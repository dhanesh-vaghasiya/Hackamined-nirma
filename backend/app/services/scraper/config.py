"""Scraper configuration."""

# Default search keywords
SEARCH_KEYWORDS = [
    "developer",
    "analyst",
    "engineer",
    "designer",
    "manager",
]

# Location filter (empty = all India)
LOCATION = ""

# Default max rows to collect per scrape run
MAX_ROWS = 50

# Max pages to crawl per keyword
MAX_PAGES_PER_KEYWORD = 5

# Selenium wait timeout (seconds)
REQUEST_TIMEOUT = 15

# Delay between page requests (seconds)
REQUEST_DELAY = 2
