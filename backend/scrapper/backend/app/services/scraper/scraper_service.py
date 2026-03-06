"""
Scraper service – real-time Naukri.com job scraper.
Uses Selenium (headless Chrome) + BeautifulSoup to scrape live data.
Scraped jobs are stored in the in-memory store (DB placeholder).
"""

import re
import time
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from app.services.scraper import config as scraper_config
from app.services.scraper.store import save_jobs


# ── helpers ────────────────────────────────────────────────

def _parse_posted_date(raw_text: str) -> str:
    """Convert relative date strings into YYYY-MM-DD."""
    if not raw_text:
        return "N/A"
    raw = raw_text.strip().lower()
    today = datetime.now()

    if any(w in raw for w in ("just now", "few hours", "today", "hour ago", "hours ago")):
        return today.strftime("%Y-%m-%d")
    if "yesterday" in raw or "1 day ago" in raw:
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")

    match = re.search(r"(\d+)\s*day", raw)
    if match:
        return (today - timedelta(days=int(match.group(1)))).strftime("%Y-%m-%d")

    match = re.search(r"(\d+)\s*month", raw)
    if match:
        return (today - timedelta(days=int(match.group(1)) * 30)).strftime("%Y-%m-%d")

    for fmt in ("%Y-%m-%d", "%d %b %Y", "%b %d, %Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    return raw_text.strip()


def _create_driver() -> webdriver.Chrome:
    """Create a headless Chrome WebDriver."""
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=opts)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )
    return driver


def _build_search_url(keyword: str, location: str, page: int) -> str:
    """Build Naukri search URL."""
    slug = keyword.strip().lower().replace(" ", "-")
    url = f"https://www.naukri.com/{slug}-jobs"
    if location:
        url += f"-in-{location.strip().lower().replace(' ', '-')}"
    if page > 1:
        url += f"?pageNo={page}"
    return url


def _parse_job_cards(soup: BeautifulSoup) -> list[dict]:
    """Extract job data from a parsed Naukri search page."""
    jobs: list[dict] = []

    cards = soup.select("div.srp-jobtuple-wrapper")
    if not cards:
        cards = soup.select("article.jobTuple")
    if not cards:
        cards = soup.select("div.cust-job-tuple")
    if not cards:
        cards = soup.find_all("div", class_=re.compile(r"jobTuple|job-tuple", re.I))
    if not cards:
        cards = soup.find_all("div", attrs={"data-job-id": True})

    for card in cards:
        title_el = (
            card.select_one("a.title")
            or card.select_one("a.jobTitle")
            or card.select_one("a[class*='title']")
            or card.select_one("h2 a")
            or card.find("a", class_=re.compile(r"title", re.I))
        )
        job_title = title_el.get_text(strip=True) if title_el else "N/A"

        loc_el = (
            card.select_one("span.locWrap span")
            or card.select_one("span.loc-wrap span")
            or card.select_one("span.location")
            or card.select_one("li.location span")
            or card.find("span", class_=re.compile(r"loc", re.I))
            or card.select_one("span[class*='ellipsis']")
        )
        location = loc_el.get_text(strip=True) if loc_el else "N/A"

        desc_el = (
            card.select_one("div.job-description")
            or card.select_one("div.jobDesc")
            or card.select_one("span.job-desc")
            or card.find("div", class_=re.compile(r"desc", re.I))
            or card.select_one("div[class*='job-desc']")
        )
        description = desc_el.get_text(" ", strip=True)[:500] if desc_el else "N/A"

        date_el = (
            card.select_one("span.date")
            or card.select_one("span.job-post-day")
            or card.select_one("span.freshness")
            or card.find("span", class_=re.compile(r"date|day|fresh", re.I))
        )
        raw_date = date_el.get_text(strip=True) if date_el else ""
        date_posted = _parse_posted_date(raw_date) if raw_date else "N/A"

        jobs.append({
            "job_title": job_title,
            "location": location,
            "job_description": description,
            "date_posted": date_posted,
        })

    return jobs


# ── public API ─────────────────────────────────────────────

def run_scrape(
    keywords: list[str] | None = None,
    location: str | None = None,
    max_rows: int | None = None,
) -> dict:
    """
    Execute a real-time scrape of Naukri.com.

    Launches headless Chrome, cycles through keywords, collects job
    listings, deduplicates, and stores them in the in-memory store.

    Returns a run summary dict with the scraped jobs.
    """
    keywords = keywords or scraper_config.SEARCH_KEYWORDS
    location = location or scraper_config.LOCATION
    max_rows = max_rows or scraper_config.MAX_ROWS
    max_pages = scraper_config.MAX_PAGES_PER_KEYWORD

    keyword_label = ", ".join(keywords)
    all_jobs: list[dict] = []
    seen: set[str] = set()

    driver = _create_driver()
    try:
        for keyword in keywords:
            if len(all_jobs) >= max_rows:
                break

            page = 1
            consecutive_empty = 0

            while len(all_jobs) < max_rows and page <= max_pages:
                url = _build_search_url(keyword, location, page)
                driver.get(url)

                try:
                    WebDriverWait(driver, scraper_config.REQUEST_TIMEOUT).until(
                        EC.presence_of_element_located((
                            By.CSS_SELECTOR,
                            "div.srp-jobtuple-wrapper, article.jobTuple, "
                            "div[class*='jobTuple'], div[data-job-id]",
                        ))
                    )
                    time.sleep(1.5)
                except Exception:
                    consecutive_empty += 1
                    if consecutive_empty >= 2:
                        break
                    page += 1
                    time.sleep(scraper_config.REQUEST_DELAY)
                    continue

                consecutive_empty = 0
                soup = BeautifulSoup(driver.page_source, "lxml")
                page_jobs = _parse_job_cards(soup)

                if not page_jobs:
                    consecutive_empty += 1
                    if consecutive_empty >= 2:
                        break
                    page += 1
                    time.sleep(scraper_config.REQUEST_DELAY)
                    continue

                for job in page_jobs:
                    if len(all_jobs) >= max_rows:
                        break
                    dedup_key = f"{job['job_title']}|{job['location']}|{job['date_posted']}"
                    if dedup_key in seen:
                        continue
                    seen.add(dedup_key)
                    all_jobs.append(job)

                page += 1
                time.sleep(scraper_config.REQUEST_DELAY)
    finally:
        driver.quit()

    # Store in the in-memory store (will be swapped for real DB later)
    run_summary = save_jobs(all_jobs, keyword=keyword_label)
    run_summary["jobs"] = all_jobs

    return run_summary
