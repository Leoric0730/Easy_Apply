# Job Search Multi-Agent System — Design Spec

## Problem

Manually searching for relevant positions across multiple job platforms (LinkedIn, Handshake, Chinese platforms) and filling repetitive application forms is time-consuming and error-prone. Candidates miss relevant roles and waste hours on mechanical data entry.

## Solution

A multi-agent system with memory that automates job discovery and application filling, with human-in-the-loop batch review before submission.

---

## Architecture

### Agents

| Agent | Responsibility | LLM |
|-------|---------------|-----|
| **Scraper Agent** | Collects job listings from selected platforms via Playwright | None (browser automation only) |
| **Matcher Agent** | Ranks jobs by resume-JD similarity + learned preferences | Cheap model (GPT-4o-mini / Qwen) |
| **Filler Agent** | Opens application pages, fills forms, pauses before submit | Strong model (GPT-4o / Claude) |
| **Memory Agent** | Manages user profile, preferences, application history in MySQL | None (CRUD operations) |

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React (JavaScript) |
| Backend | FastAPI (Python) |
| Database | MySQL |
| Vector Search | FAISS (local, sentence-transformers/all-MiniLM-L6-v2) |
| Browser Automation | Playwright |
| Notifications | Email (SMTP) |
| Deployment | Docker Compose on GCP VM |

### System Flow

```
1. User opens dashboard → configures search (platforms, resume profile, filters)
2. User clicks "Search Now" OR auto-search triggers on daily schedule
3. Scraper Agent launches Playwright → scrapes selected platforms → stores raw listings in MySQL
4. Dedup: skip jobs matching existing (company + title + location)
5. Matcher Agent embeds new JDs → FAISS similarity against resume profile → scores with preference signals → ranks batch
6. Email notification sent: "X new jobs matched"
7. User opens dashboard → reviews ranked batch → selects jobs to apply
8. Filler Agent opens Playwright session per selected job → fills application form → pauses on final page
9. Dashboard shows "Ready to Review" list with live browser links
10. User clicks link → reviews filled form in live browser → submits manually
11. Filler Agent detects submission → records to MySQL → closes browser session
12. Dashboard moves application to "History" view
```

---

## Data Model (MySQL)

### users
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK AUTO_INCREMENT | |
| name | VARCHAR(100) | |
| email | VARCHAR(255) | For notifications |
| contact_info | JSON | Phone, address, etc. |
| created_at | DATETIME | |

### resume_profiles
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK AUTO_INCREMENT | |
| user_id | INT FK → users | |
| label | VARCHAR(50) | "MLE", "Agentic AI" |
| resume_file_path | VARCHAR(500) | Path to uploaded PDF |
| parsed_content | JSON | Structured resume data (education, skills, experience) |
| target_keywords | JSON | Role-specific search terms |
| preferences | JSON | Profile-specific preferences |
| embedding | BLOB | Resume embedding vector for FAISS |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### jobs
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK AUTO_INCREMENT | |
| platform | VARCHAR(50) | "linkedin", "handshake", "boss_zhipin" |
| external_url | VARCHAR(1000) | Link to job posting |
| title | VARCHAR(255) | |
| company | VARCHAR(255) | |
| location | VARCHAR(255) | |
| description | TEXT | Full JD text |
| salary_range | VARCHAR(100) | If available |
| embedding | BLOB | JD embedding vector for FAISS |
| match_score | FLOAT | Similarity score from Matcher |
| status | ENUM('new','selected','rejected','applied','expired') | |
| scraped_at | DATETIME | |

### applications
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK AUTO_INCREMENT | |
| job_id | INT FK → jobs | |
| resume_profile_id | INT FK → resume_profiles | |
| filled_data | JSON | What was filled into the form |
| browser_session_id | VARCHAR(100) | Playwright session reference |
| status | ENUM('filling','ready_to_review','submitted') | |
| applied_at | DATETIME | NULL until submitted |
| created_at | DATETIME | |

### preference_signals
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK AUTO_INCREMENT | |
| resume_profile_id | INT FK → resume_profiles | |
| job_id | INT FK → jobs | |
| action | ENUM('selected','rejected','bookmarked') | |
| created_at | DATETIME | |

### search_configs
| Column | Type | Notes |
|--------|------|-------|
| id | INT PK AUTO_INCREMENT | |
| user_id | INT FK → users | |
| resume_profile_id | INT FK → resume_profiles | Active profile for search |
| platforms | JSON | ["linkedin", "handshake"] |
| filters | JSON | {location, keywords, salary_min, ...} |
| auto_search_enabled | BOOLEAN | Toggle for daily schedule |
| auto_search_time | TIME | e.g. "09:00" |
| updated_at | DATETIME | |

---

## Dashboard Views

### 1. Search Config (Top Bar / Sidebar)
- Platform selector (multi-select checkboxes)
- Resume profile dropdown
- Filter inputs (keywords, location, salary range)
- "Search Now" button
- Auto-search toggle with time picker

### 2. New Batch
- Table of ranked job matches: title, company, platform, location, match score
- Checkboxes to select/reject each job
- "Apply Selected" button → triggers Filler Agent

### 3. Ready to Review
- Table of filled applications: title, company, status
- "Open Browser" link per application → connects to live Playwright session
- Status auto-updates when submission detected

### 4. History
- All past applications with search/filter
- Columns: title, company, platform, resume profile used, date applied, status
- Sortable and filterable

---

## Deployment Architecture (GCP)

```
GCP VM (n1-standard-4, 1x T4 optional)
├── Docker Compose
│   ├── frontend (React, nginx, port 80)
│   ├── backend (FastAPI, port 8000)
│   ├── mysql (port 3306)
│   ├── playwright-service (browser sessions)
│   └── scheduler (cron for auto-search)
```

- All services in one VM via Docker Compose
- Nginx reverse proxy serves React and proxies `/api/*` to FastAPI
- MySQL data persisted via Docker volume
- FAISS index stored as file on disk, loaded into memory by backend

---

## Embedding & Matching Pipeline

1. **Resume upload** → parse PDF to structured JSON → embed with sentence-transformers → store in resume_profiles + FAISS index
2. **Job scraped** → embed JD text → store in jobs + FAISS index
3. **Matching** → query FAISS with resume embedding → get top-K similar JDs → re-rank using preference_signals (boost categories user tends to select, penalize rejected patterns) → return sorted batch

---

## Key Design Decisions

- **Single-user**: No auth system. Simplifies everything.
- **Playwright everywhere**: One browser automation tool for both scraping and form filling.
- **Live browser review**: Filler Agent keeps Playwright sessions alive for manual submission. No auto-submit.
- **Cost-aware LLM routing**: Cheap model for bulk JD parsing/matching, strong model for form filling reasoning.
- **Local embeddings**: sentence-transformers runs on VM, no API cost for embeddings.
- **Simple dedup**: Company + title + location exact match. No embedding-based dedup.
- **Unified search config**: Dashboard config drives both manual and scheduled searches.

---

## Scope Boundaries (Out of Scope for v1)

- Multi-user / authentication
- Resume tailoring per job
- Interview tracking / full ATS features
- Cover letter generation
- Mobile app
- Auto-submit (user always submits manually)
