"""
NPTEL course search tool.
Uses a local dataset of NPTEL courses.
Replace with a real API or scraped dataset later.
"""

_NPTEL_COURSES = [
    # ── Python / Programming ─────────────────────────────
    {
        "title": "Programming, Data Structures and Algorithms Using Python",
        "institution": "IIT Madras",
        "instructor": "Prof. Madhavan Mukund",
        "duration": "8 weeks",
        "url": "https://nptel.ac.in/courses/106106145",
        "tags": ["python", "programming", "data structures", "algorithms"],
    },
    {
        "title": "Python for Data Science",
        "institution": "IIT Madras",
        "instructor": "Prof. Ragunathan Rengasamy",
        "duration": "4 weeks",
        "url": "https://nptel.ac.in/courses/106106212",
        "tags": ["python", "data science", "data analytics"],
    },
    {
        "title": "Joy of Computing using Python",
        "institution": "IIT Ropar",
        "instructor": "Prof. Sudarshan Iyengar",
        "duration": "12 weeks",
        "url": "https://nptel.ac.in/courses/106106182",
        "tags": ["python", "programming", "computing", "beginner"],
    },
    # ── Data Analytics / Data Science ────────────────────
    {
        "title": "Data Science for Engineers",
        "institution": "IIT Madras",
        "instructor": "Prof. Ragunathan Rengasamy",
        "duration": "8 weeks",
        "url": "https://nptel.ac.in/courses/106106179",
        "tags": ["data science", "data analytics", "statistics", "python"],
    },
    {
        "title": "Introduction to Data Analytics",
        "institution": "IIT Madras",
        "instructor": "Prof. Nandan Sudarsanam",
        "duration": "8 weeks",
        "url": "https://nptel.ac.in/courses/110106064",
        "tags": ["data analytics", "statistics", "business analytics"],
    },
    {
        "title": "Business Analytics and Data Mining Modeling using R",
        "institution": "IIT Kharagpur",
        "instructor": "Prof. Ganapati Panda",
        "duration": "8 weeks",
        "url": "https://nptel.ac.in/courses/110105089",
        "tags": ["data analytics", "data mining", "r programming", "business analytics"],
    },
    # ── Machine Learning / AI ────────────────────────────
    {
        "title": "Introduction to Machine Learning",
        "institution": "IIT Kharagpur",
        "instructor": "Prof. Sudeshna Sarkar",
        "duration": "8 weeks",
        "url": "https://nptel.ac.in/courses/106105152",
        "tags": ["machine learning", "ai", "artificial intelligence", "data science"],
    },
    {
        "title": "Deep Learning",
        "institution": "IIT Madras",
        "instructor": "Prof. Mitesh Khapra",
        "duration": "12 weeks",
        "url": "https://nptel.ac.in/courses/106106184",
        "tags": ["deep learning", "machine learning", "ai", "neural networks"],
    },
    {
        "title": "Artificial Intelligence: Search Methods for Problem Solving",
        "institution": "IIT Madras",
        "instructor": "Prof. Deepak Khemani",
        "duration": "12 weeks",
        "url": "https://nptel.ac.in/courses/106106126",
        "tags": ["artificial intelligence", "ai", "ai literacy", "search methods"],
    },
    # ── SQL / Databases ──────────────────────────────────
    {
        "title": "Database Management System",
        "institution": "IIT Kharagpur",
        "instructor": "Prof. Partha Pratim Das",
        "duration": "8 weeks",
        "url": "https://nptel.ac.in/courses/106105175",
        "tags": ["sql", "database", "dbms", "relational databases"],
    },
    {
        "title": "Introduction to Database Systems",
        "institution": "IIT Madras",
        "instructor": "Prof. S. Sudarshan",
        "duration": "12 weeks",
        "url": "https://nptel.ac.in/courses/106106220",
        "tags": ["sql", "database", "data management"],
    },
    # ── Cloud Computing ──────────────────────────────────
    {
        "title": "Cloud Computing",
        "institution": "IIT Kharagpur",
        "instructor": "Prof. Soumya K Ghosh",
        "duration": "8 weeks",
        "url": "https://nptel.ac.in/courses/106105167",
        "tags": ["cloud computing", "cloud", "aws", "devops"],
    },
    {
        "title": "Cloud Computing and Distributed Systems",
        "institution": "IIT Patna",
        "instructor": "Prof. Rajiv Misra",
        "duration": "12 weeks",
        "url": "https://nptel.ac.in/courses/106104182",
        "tags": ["cloud computing", "distributed systems", "cloud"],
    },
    # ── Cybersecurity ────────────────────────────────────
    {
        "title": "Introduction to Cyber Security",
        "institution": "IIT Kanpur",
        "instructor": "Prof. Sandeep Shukla",
        "duration": "8 weeks",
        "url": "https://nptel.ac.in/courses/106104220",
        "tags": ["cybersecurity", "security", "network security"],
    },
    {
        "title": "Cryptography and Network Security",
        "institution": "IIT Kharagpur",
        "instructor": "Prof. Debdeep Mukhopadhyay",
        "duration": "8 weeks",
        "url": "https://nptel.ac.in/courses/106105031",
        "tags": ["cybersecurity", "cryptography", "network security"],
    },
    # ── Finance / Accounting ─────────────────────────────
    {
        "title": "Financial Accounting",
        "institution": "IIT Roorkee",
        "instructor": "Prof. Varadraj Bapat",
        "duration": "8 weeks",
        "url": "https://nptel.ac.in/courses/110107073",
        "tags": ["accounting", "financial accounting", "finance", "tally"],
    },
    {
        "title": "Financial Management",
        "institution": "IIT Kanpur",
        "instructor": "Prof. Anil K. Makhija",
        "duration": "12 weeks",
        "url": "https://nptel.ac.in/courses/110104073",
        "tags": ["financial modelling", "finance", "financial management", "power bi"],
    },
    # ── Product Management / UX ──────────────────────────
    {
        "title": "Product Design and Development",
        "institution": "IIT Delhi",
        "instructor": "Prof. Sumitesh Das",
        "duration": "8 weeks",
        "url": "https://nptel.ac.in/courses/112102101",
        "tags": ["product management", "product design", "product thinking"],
    },
    {
        "title": "User Interface Design",
        "institution": "IIT Guwahati",
        "instructor": "Prof. Samit Bhattacharya",
        "duration": "8 weeks",
        "url": "https://nptel.ac.in/courses/106103115",
        "tags": ["ux", "user research", "ui design", "wireframing", "user interface"],
    },
    # ── Statistics ────────────────────────────────────────
    {
        "title": "Probability and Statistics",
        "institution": "IIT Kanpur",
        "instructor": "Prof. Neeraj Misra",
        "duration": "12 weeks",
        "url": "https://nptel.ac.in/courses/111104079",
        "tags": ["statistics", "probability", "data analytics", "data science"],
    },
    {
        "title": "Statistical Inference",
        "institution": "IIT Kharagpur",
        "instructor": "Prof. Somesh Kumar",
        "duration": "8 weeks",
        "url": "https://nptel.ac.in/courses/111105035",
        "tags": ["statistics", "inference", "data science"],
    },
    # ── Communication / Soft Skills ──────────────────────
    {
        "title": "Effective Business Communication",
        "institution": "IIT Roorkee",
        "instructor": "Prof. Rajlakshmi Guha",
        "duration": "4 weeks",
        "url": "https://nptel.ac.in/courses/109107121",
        "tags": ["communication", "business communication", "soft skills"],
    },
    # ── Supply Chain / Logistics ─────────────────────────
    {
        "title": "Supply Chain Management",
        "institution": "IIT Bombay",
        "instructor": "Prof. Sanjog Misra",
        "duration": "12 weeks",
        "url": "https://nptel.ac.in/courses/110101132",
        "tags": ["supply chain", "logistics", "inventory management", "warehouse"],
    },
    # ── SEO / Content / Marketing ────────────────────────
    {
        "title": "Introduction to Digital Marketing",
        "institution": "IIT Roorkee",
        "instructor": "Prof. Rashmi Tiwari",
        "duration": "4 weeks",
        "url": "https://nptel.ac.in/courses/110107142",
        "tags": ["digital marketing", "seo", "content marketing", "seo writing", "copywriting"],
    },
    # ── Prompt Engineering / Generative AI ───────────────
    {
        "title": "Generative AI and Large Language Models",
        "institution": "IIT Bombay",
        "instructor": "Prof. Pushpak Bhattacharyya",
        "duration": "8 weeks",
        "url": "https://nptel.ac.in/courses/106101250",
        "tags": ["prompt engineering", "generative ai", "llm", "ai literacy", "ai"],
    },
    {
        "title": "Natural Language Processing",
        "institution": "IIT Kharagpur",
        "instructor": "Prof. Pawan Goyal",
        "duration": "8 weeks",
        "url": "https://nptel.ac.in/courses/106105158",
        "tags": ["nlp", "natural language processing", "ai", "prompt engineering", "llm"],
    },
]


def search_nptel_courses(query: str, max_results: int = 5) -> list[dict]:
    """
    Search the NPTEL dataset for courses matching a skill/topic query.
    Returns a list of matching courses sorted by relevance.
    """
    query_lower = query.lower()
    query_words = set(query_lower.split())

    scored = []
    for course in _NPTEL_COURSES:
        score = 0
        # Tag matching (highest weight)
        for tag in course["tags"]:
            if query_lower in tag or tag in query_lower:
                score += 3
            elif any(w in tag for w in query_words):
                score += 1

        # Title matching
        title_lower = course["title"].lower()
        if query_lower in title_lower:
            score += 4
        elif any(w in title_lower for w in query_words):
            score += 1

        if score > 0:
            scored.append((score, course))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for _score, course in scored[:max_results]:
        results.append({
            "title": course["title"],
            "institution": course["institution"],
            "instructor": course["instructor"],
            "duration": course["duration"],
            "url": course["url"],
        })
    return results
