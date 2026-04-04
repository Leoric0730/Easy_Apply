# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Job Search Multi-Agent System — Columbia ECE ML on Cloud final project (Spring 2026).
Multi-agent system that scrapes job listings, ranks them against user resumes, and auto-fills applications with human-in-the-loop review.

Design spec: `docs/specs/2026-04-03-job-search-agent-design.md`

## Tech Stack

- **Frontend:** React (JavaScript), served via nginx
- **Backend:** FastAPI (Python)
- **Database:** MySQL (structured data) + FAISS (vector search)
- **Embeddings:** sentence-transformers/all-MiniLM-L6-v2 (local)
- **Browser automation:** Playwright (scraping + form filling)
- **LLM:** GPT-4o-mini/Qwen for JD parsing, GPT-4o/Claude for form filling
- **Deployment:** Docker Compose on GCP VM

## Project Structure

```
frontend/          # React app (JavaScript)
backend/           # FastAPI app (Python)
  agents/          # Scraper, Matcher, Filler, Memory agents
  models/          # SQLAlchemy models
  api/             # FastAPI route handlers
docker/            # Dockerfiles
docs/specs/        # Design documents
docker-compose.yml
```

## Commands

```bash
# Local development
docker-compose up              # Start all services
docker-compose up backend      # Backend only
docker-compose up frontend     # Frontend only

# Backend
cd backend && pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend && npm install
npm start                      # Dev server on port 3000

# Database
docker-compose exec mysql mysql -u root -p  # Connect to MySQL

# Cloud deployment
bash deploy/cloud_setup.sh     # GCP VM provisioning
```

## Architecture

4 agents orchestrated by FastAPI backend:
1. **Scraper Agent** — Playwright browser automation, one scraper per platform
2. **Matcher Agent** — FAISS similarity + preference signals → ranked batch
3. **Filler Agent** — Playwright form filling, keeps sessions alive for user review
4. **Memory Agent** — MySQL CRUD for profiles, jobs, applications, preferences

Single-user system. No authentication.

## Key Patterns

- Unified search config drives both manual and scheduled searches
- Playwright used for both scraping and form filling
- Cost-aware LLM routing: cheap model for bulk tasks, strong model for reasoning
- User always submits applications manually via live browser session
- Preference learning from accept/reject signals per resume profile
