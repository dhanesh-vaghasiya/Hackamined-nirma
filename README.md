<p align="center">
  <img src="https://img.shields.io/badge/OASIS-Workforce%20Intelligence-97A87A?style=for-the-badge&labelColor=121412" />
</p>

<h1 align="center">🌿 OASIS — Workforce Intelligence Platform</h1>

<p align="center">
  <b>AI-powered career displacement risk analysis, real-time labor market intelligence, and personalized reskilling roadmaps for the Indian workforce.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Flask-3.1-000000?logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/Groq-Llama%203.3%20%7C%204-F55036?logo=meta&logoColor=white" />
  <img src="https://img.shields.io/badge/Vite-7-646CFF?logo=vite&logoColor=white" />
  <img src="https://img.shields.io/badge/TailwindCSS-4-06B6D4?logo=tailwindcss&logoColor=white" />
</p>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Database Schema](#-database-schema)
- [API Reference](#-api-reference)
- [AI/ML Pipeline](#-aiml-pipeline)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [Screenshots](#-screenshots)
- [Team](#-team)

---

## 🌍 Overview

**OASIS** (Occupational Analysis & Strategic Intelligence System) is a full-stack workforce intelligence platform built for the Indian labor market. It combines **real-time job scraping**, **machine learning risk prediction**, and **agentic AI** to help workers understand how AI automation threatens their current role — and provides actionable, week-by-week reskilling plans to transition into safer careers.

The platform serves **two perspectives**:

| 👷 Worker View | 🏢 Employer View |
|---|---|
| Analyze your career profile against live market data | City-wise skill demand heatmap across India |
| Get AI vulnerability scores (automation + takeover risk) | Sector-level hiring trend analysis |
| Receive ML-powered job transition suggestions | Real-time scraping dashboard with analytics |
| Generate personalized reskilling roadmaps with NPTEL courses | Skill gap intelligence for workforce planning |

---

## ✨ Key Features

### 🔬 Career Risk Analysis
- **Multi-signal risk scoring** — Combines skill trend analysis (45%), hiring scarcity (35%), and experience buffer (20%) from live database data
- **AI Vulnerability Assessment** — Groq LLM evaluates automation risk and AI takeover risk for every job role
- **SHAP Explainability** — Transparent feature-importance breakdowns for risk predictions

### 🤖 Agentic AI Chatbot
- Powered by **Groq Llama 4 Scout 17B** with autonomous tool-calling
- LLM decides which database tools to invoke (job counts, skill trends, AI vulnerability, courses, related skills) — up to 5 tool iterations per query
- Auto-generates structured **Insight Deck** cards from every conversation
- Multi-language support with auto-detection
- Persistent conversation history

### 🗺️ Personalized Reskilling Roadmaps
- **Dual source** — roadmap.sh API for structured roadmaps + Groq LLM fallback for custom generation
- Week-by-week learning plans mapped to real **NPTEL / SWAYAM / PMKVY** courses
- Sub-concept drill-down graphs for deep learning paths
- ML-based job transition suggestions with skill overlap scoring

### 📊 Real-time Market Intelligence
- **Naukri.com scraper** (Selenium + BeautifulSoup) with full pipeline: scrape → normalize → update skill trends → compute AI vulnerability
- Hiring trend visualization by role, city, and timeframe
- Skill demand intelligence with growth rates
- Interactive India map with city-level skill demand markers

### 🔒 Secure Auth
- **httpOnly cookie-based JWT** (not localStorage) with SameSite protection
- bcrypt password hashing
- Protected and guest route guards

---

## 🏗 Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + Vite)                 │
│  ┌──────────┐ ┌──────────────┐ ┌────────────┐ ┌────────────┐  │
│  │ Landing  │ │  Dashboard   │ │  Chatbot   │ │  Roadmap   │  │
│  │  Page    │ │  (4 views)   │ │   Page     │ │   Page     │  │
│  └──────────┘ └──────┬───────┘ └─────┬──────┘ └────────────┘  │
│                      │               │                         │
│  ┌───────────────────┼───────────────┼───────────────────────┐ │
│  │  Market Intel │ Worker Portal │ AI Assistant │ Employers  │ │
│  └───────────────────┼───────────────┼───────────────────────┘ │
│                      │               │                         │
│            Axios (withCredentials) + httpOnly JWT Cookies       │
└──────────────────────┼───────────────┼─────────────────────────┘
                       │  Vite Proxy   │
                       │  /api → :5000 │
┌──────────────────────┼───────────────┼─────────────────────────┐
│                     BACKEND (Flask)                             │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌─────────────┐  │
│  │ Auth   │ │ Career │ │ Market │ │Chatbot │ │  Scraper    │  │
│  │ Routes │ │ Routes │ │ Routes │ │ Routes │ │  Routes     │  │
│  └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └──────┬──────┘  │
│      │          │          │          │             │           │
│  ┌───┴──────────┴──────────┴──────────┴─────────────┴────────┐ │
│  │                    SERVICE LAYER                           │ │
│  │  Groq Career │ Roadmap.sh │ Agent │ Scraper │ User Input  │ │
│  └───────────────────────┬───────────────────────────────────┘ │
│                          │                                     │
│  ┌───────────────────────┴───────────────────────────────────┐ │
│  │              CAREER RISK AI PIPELINE                      │ │
│  │  Data Prep → Feature Gen → Train → Predict → Explain     │ │
│  │  Skill Extraction → Market Analysis → AI Vulnerability    │ │
│  └───────────────────────┬───────────────────────────────────┘ │
└──────────────────────────┼─────────────────────────────────────┘
                           │
                  ┌────────┴────────┐
                  │   PostgreSQL    │
                  │   (12 tables)   │
                  └────────┬────────┘
                           │
              ┌────────────┴────────────┐
              │     External APIs       │
              │  Groq │ roadmap.sh │    │
              │  Naukri.com (Selenium)  │
              └─────────────────────────┘
```

---

## 🛠 Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 18, Vite 7, TailwindCSS 4, Framer Motion, Three.js / React Three Fiber, Recharts, Radix UI, react-simple-maps, Lucide Icons, Rive Animations |
| **Backend** | Flask 3.1, SQLAlchemy 2.0, Flask-JWT-Extended, Flask-Migrate (Alembic), Flask-CORS |
| **Database** | PostgreSQL with psycopg2 |
| **AI / LLM** | Groq API (Llama 3.3 70B Versatile, Llama 4 Scout 17B 16E), sentence-transformers |
| **ML** | scikit-learn (joblib models), pandas, NumPy, SHAP |
| **Scraping** | Selenium WebDriver, BeautifulSoup4, lxml, webdriver-manager |
| **Auth** | bcrypt, JWT (httpOnly cookies, SameSite=Lax) |

---

## 📁 Project Structure

```
oasis/
├── backend/
│   ├── app/
│   │   ├── __init__.py              # Flask app factory + blueprint registration
│   │   ├── config.py                # App configuration (DB, JWT, CORS)
│   │   ├── models.py                # SQLAlchemy models (12 tables)
│   │   ├── data_paths.py            # Centralized data file paths
│   │   ├── routes/
│   │   │   ├── auth.py              # Registration, login, logout, profile
│   │   │   ├── career.py            # Career analysis, roadmap generation
│   │   │   ├── chatbot.py           # Agentic AI chatbot with tool-calling
│   │   │   ├── market.py            # Market intelligence + employer views
│   │   │   ├── roadmap.py           # AI roadmap agent pipeline
│   │   │   ├── scraper.py           # Naukri.com scrape triggers
│   │   │   └── user_input.py        # Profile NLP extraction + storage
│   │   ├── services/
│   │   │   ├── groq_career.py       # Groq LLM career intelligence
│   │   │   ├── roadmap_sh.py        # roadmap.sh API integration
│   │   │   ├── agent/               # Agentic AI pipeline (tool-calling)
│   │   │   ├── career_risk/         # Risk scoring logic
│   │   │   ├── scraper/             # Selenium scraper + normalizer
│   │   │   └── user_input/          # Profile NLP extraction
│   │   └── utils/
│   │       ├── auth.py              # JWT decorators
│   │       └── responses.py         # Standardized API responses
│   ├── career_risk_ai/
│   │   ├── pipeline/                # 12-stage ML pipeline
│   │   │   ├── prepare_jobs_dataset.py
│   │   │   ├── preflight_analysis.py
│   │   │   ├── demand_dataset.py
│   │   │   ├── trend_model.py
│   │   │   ├── feature_generator.py
│   │   │   ├── train_risk_model.py
│   │   │   ├── predict_risk.py
│   │   │   ├── explainability.py
│   │   │   ├── skill_extractor.py
│   │   │   ├── skill_market_analysis.py
│   │   │   ├── ai_vulnerability_index.py
│   │   │   └── job_trends_export.py
│   │   ├── job_suggestion/          # ML job recommendation engine
│   │   │   ├── train.py
│   │   │   ├── recommend.py
│   │   │   └── data_utils.py
│   │   └── models/                  # Trained ML model artifacts
│   ├── data/
│   │   ├── csv/                     # Scraped & processed datasets
│   │   └── json/                    # Analysis outputs
│   ├── migrations/                  # Alembic DB migrations
│   ├── scripts/                     # DB seeding & import utilities
│   ├── requirements.txt
│   ├── run.py                       # Flask entry point
│   └── schema.sql                   # PostgreSQL schema definition
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                  # Root app with particle background
│   │   ├── main.jsx                 # React entry point
│   │   ├── pages/
│   │   │   ├── Landing.jsx          # Hero page with live stats
│   │   │   ├── Login.jsx            # Login form
│   │   │   ├── Register.jsx         # Registration form
│   │   │   ├── Dashboard.jsx        # Multi-layer dashboard host
│   │   │   ├── ChatbotPage.jsx      # Full-page AI assistant
│   │   │   └── Roadmap.jsx          # Roadmap visualization
│   │   ├── components/
│   │   │   ├── Navbar.jsx           # Layer-switcher navigation
│   │   │   ├── dashboard/
│   │   │   │   ├── EmployersView.jsx
│   │   │   │   ├── IndiaMap.jsx     # Interactive India map
│   │   │   │   ├── IntelligenceChatbot.jsx
│   │   │   │   ├── QuickInsightDeck.jsx
│   │   │   │   └── MarketIntelligence.jsx
│   │   │   ├── worker/
│   │   │   │   └── WorkerPortal.jsx # Full worker analysis flow
│   │   │   └── landing/
│   │   │       ├── ParticleBackground.jsx  # Three.js 3D particles
│   │   │       └── GlassCard.jsx
│   │   ├── context/
│   │   │   └── AuthContext.jsx      # Auth state management
│   │   ├── routes/
│   │   │   ├── AppRouter.jsx
│   │   │   ├── ProtectedRoute.jsx
│   │   │   └── GuestRoute.jsx
│   │   ├── services/
│   │   │   ├── api.js               # Axios instance (cookie auth)
│   │   │   ├── market.js            # Market API calls
│   │   │   ├── career.js            # Career analysis API calls
│   │   │   └── chatbot.js           # Chatbot API calls
│   │   └── styles/
│   ├── package.json
│   └── vite.config.js               # Proxy /api → localhost:5000
│
└── package.json                     # Root scripts (concurrent dev)
```

---

## 🗄 Database Schema

The platform uses **12 interconnected PostgreSQL tables**:

```
┌─────────┐       ┌──────────────┐       ┌───────────┐
│  users  │──1:N──│worker_profiles│──1:N──│risk_assess│
└─────────┘       └──────┬───────┘       └───────────┘
                         │
                    ┌────┴─────┐
                    │  cities  │
                    └────┬─────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────┴───┐    ┌──────┴──────┐   ┌─────┴──────┐
   │  jobs  │    │ skill_trends│   │ai_vuln_score│
   └────┬───┘    └─────────────┘   └────────────┘
        │
   ┌────┴──────┐
   │ job_skills │
   └───────────┘

┌───────────────┐    ┌──────────────┐    ┌──────────────┐
│reskilling_paths│───│reskilling_   │    │ chat_messages │
│               │   │  path_steps  │    └──────────────┘
└───────────────┘    └──────────────┘
                                         ┌──────────────┐
┌───────────┐                            │ insight_decks│
│  courses  │                            └──────────────┘
└───────────┘
```

### Key Models

| Model | Description |
|-------|-------------|
| **User** | Authentication accounts (bcrypt hashed passwords) |
| **City** | Indian cities with tier classification (1–3) |
| **Job** | Scraped job postings from Naukri.com |
| **JobSkill** | Extracted skills per job posting |
| **WorkerProfile** | NLP-extracted career profiles (skills, tasks, aspirations, domain) |
| **RiskAssessment** | Computed career displacement risk (LOW / MEDIUM / HIGH / CRITICAL) |
| **AiVulnerabilityScore** | AI automation risk per role + city (0–100) |
| **SkillTrend** | Aggregated skill demand over time periods |
| **Course** | NPTEL / SWAYAM / PMKVY courses for reskilling |
| **ReskillingPath** | Week-by-week reskilling plans with mapped courses |
| **ChatMessage** | Persistent chatbot conversation history |
| **InsightDeck** | AI-generated structured insight cards |

---

## 📡 API Reference

### Authentication (`/api/auth`)

| Method | Endpoint | Auth | Description |
|--------|----------|:----:|-------------|
| `POST` | `/register` | — | Create account |
| `POST` | `/login` | — | Login (sets httpOnly JWT cookie) |
| `POST` | `/logout` | — | Clear JWT cookie |
| `GET` | `/me` | 🔒 | Get current user |
| `PUT` | `/me` | 🔒 | Update profile |

### Career Analysis (`/api/career`)

| Method | Endpoint | Auth | Description |
|--------|----------|:----:|-------------|
| `POST` | `/analyze` | 🔒 | Full career analysis pipeline |
| `POST` | `/roadmap` | — | Generate reskilling roadmap for a target role |
| `POST` | `/detailed-roadmap` | — | Fetch topic-tree roadmap (roadmap.sh + Groq fallback) |
| `POST` | `/topic-graph` | — | Sub-concept learning graph for a topic |

### Market Intelligence (`/api/market`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/summary` | Dashboard summary (total jobs, roles, cities, vuln scores) |
| `GET` | `/hiring-trends` | Hiring trends by role, city, timeframe |
| `GET` | `/skills-intel` | Top skills demand with growth rates |
| `GET` | `/ai-vulnerability` | AI automation vulnerability by role |
| `GET` | `/job-roles` | Searchable normalized job roles |
| `GET` | `/job-role-skills` | Skills for a specific role |
| `GET` | `/available-skills` | All tracked skills |
| `POST` | `/skill-gap` | Skill gap analysis for given skills vs. market |
| `GET` | `/records` | Paginated job records with filtering |
| `GET` | `/skill-trend` | Individual skill trend over time |
| `GET` | `/cities` | Available cities |
| `GET` | `/job-count` | Job count by filters |
| `GET` | `/employer/city-skills` | City-wise skill demand for employers |
| `GET` | `/employer/sector-hiring` | Sector-level hiring analysis |

### AI Chatbot (`/api/chatbot`)

| Method | Endpoint | Auth | Description |
|--------|----------|:----:|-------------|
| `POST` | `/chat` | opt. | Agentic chat (LLM with DB tool-calling, up to 5 iterations) |
| `GET` | `/history` | 🔒 | Retrieve persisted chat history |
| `GET` | `/insight-deck/latest` | 🔒 | Latest AI-generated insight card |
| `GET` | `/insight-deck/all` | 🔒 | All insight decks (paginated) |

### Scraper (`/api/scraper`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/scrape` | Trigger Naukri.com scrape |
| `POST` | `/scrape-and-update` | Full pipeline: scrape → normalize → update trends → AI vulnerability |
| `GET` | `/jobs` | List stored jobs (paginated) |
| `GET` | `/jobs/:id` | Single job details |
| `DELETE` | `/jobs` | Clear all stored jobs |
| `GET` | `/runs` | Past scrape run history |
| `GET` | `/stats` | Quick scraper statistics |

---

## 🧠 AI/ML Pipeline

### Career Risk ML Pipeline (12 stages)

```
Raw Scraped Data
       │
       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ 1. Prepare Jobs │───▶│ 2. Preflight     │───▶│ 3. Demand       │
│    Dataset      │    │    Analysis      │    │    Dataset      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
       │
       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ 4. Trend Model  │───▶│ 5. Feature       │───▶│ 6. Train Risk   │
│                 │    │    Generator     │    │    Model        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
       │
       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ 7. Predict Risk │───▶│ 8. Explainability│───▶│ 9. Skill        │
│                 │    │    (SHAP)        │    │    Extraction   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
       │
       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│10. Skill Market │───▶│11. AI Vuln Index │───▶│12. Job Trends   │
│   Analysis      │    │   (Groq LLM)    │    │    Export       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Agentic AI Architecture

```
User Query
    │
    ▼
┌──────────────────────────────┐
│   Groq LLM (Llama 4 Scout)  │
│                              │
│  System Prompt + Tools Spec  │◄──── Tool Results
│         │                    │         ▲
│         ▼                    │         │
│   Tool Call Decision         │    ┌────┴─────────────┐
│   (up to 5 iterations)      │───▶│  DB Tool Router   │
│         │                    │    │                   │
│         ▼                    │    │ • get_job_count   │
│   Final Response             │    │ • get_skill_trend │
│         +                    │    │ • get_ai_vuln     │
│   InsightDeck Generation     │    │ • search_courses  │
└──────────────────────────────┘    │ • related_skills  │
                                    └───────────────────┘
```

### Risk Score Formula

```
Risk Score = (skill_trend_weight × 0.45) + (hiring_scarcity × 0.35) + (experience_buffer × 0.20)
```

Where:
- **Skill trend weight** — Declining demand signals for the worker's current skills
- **Hiring scarcity** — Low hiring volume in the worker's role + city
- **Experience buffer** — Higher experience provides a marginal safety buffer

Risk levels: **LOW** (0–30) · **MEDIUM** (31–55) · **HIGH** (56–75) · **CRITICAL** (76–100)

---

## 🚀 Getting Started

### Prerequisites

- **Python** 3.10+
- **Node.js** 18+
- **PostgreSQL** 14+
- **Chrome/Chromium** (for Selenium scraper)
- **Groq API key** ([console.groq.com](https://console.groq.com))

### 1. Clone the repository

```bash
git clone https://github.com/dhanesh-vaghasiya/Hackamined-nirma.git
cd Hackamined-nirma
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Setup

```bash
# Create PostgreSQL database
createdb oasis_db

# Apply schema
psql -d oasis_db -f schema.sql

# Or use Alembic migrations
flask db upgrade
```

### 4. Frontend Setup

```bash
cd frontend
npm install
```

### 5. Configure Environment

Create `backend/.env`:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/oasis_db
GROQ_API_KEY=gsk_your_groq_api_key_here
JWT_SECRET_KEY=your-secret-key-here
FLASK_ENV=development
```

### 6. Run the Application

**Option A — Concurrent (from root):**
```bash
npm run dev
```

**Option B — Separate terminals:**
```bash
# Terminal 1: Backend
cd backend
source .venv/bin/activate
python run.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

The app will be available at:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:5000

---

## 🔐 Environment Variables

| Variable | Required | Description |
|----------|:--------:|-------------|
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `GROQ_API_KEY` | ✅ | Groq API key for LLM access |
| `JWT_SECRET_KEY` | ✅ | Secret for JWT token signing |
| `FLASK_ENV` | — | `development` or `production` |

---

## 📸 Screenshots

> _Screenshots can be added here showcasing the Landing Page, Market Intelligence Dashboard, Worker Portal analysis flow, AI Chatbot, India Map, and Employer View._

---

## 🏆 Built For

**HackMind @ Nirma University** — A hackathon project addressing AI-driven workforce displacement in the Indian labor market.

---

## 👥 Team

| Name | Role |
|------|------|
| **Dhanesh Vaghasiya** | Full-Stack Development |
| **Rohit** | Full-Stack Development |

---

<p align="center">
  <sub>Built with 🌿 at HackMind Nirma · 2026</sub>
</p>
