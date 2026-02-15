# Project Structure

```plaintext
JEA_WEB_SCRAPING/
│
├── data/
│   ├── raw_pdfs/
│   ├── processed/
│   └── annotated_pdfs/
│
├── docs/
│   ├── 01_overview/
│   ├── 02_architecture/
│   ├── 03_deployment/
│   ├── 04_security/
│   ├── 05_future_plans/
│   ├── 06_operations/
│   ├── 07_project_diary_notes/
│   ├── 08_database/
│   └── 09_medium_blog/
│
├── scripts/
│   ├── README.md           # Documentation
│   ├── migrations/         # Database migrations
│   ├── admin/             # Admin utilities
│   └── archive/           # Deprecated scripts
│
├── src/jea_meeting_web_scraper/
│   ├── __init__.py
│   │
│   ├── main.py                   # FastAPI app entry point
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── config.yaml           # Application configuration file
│   │   └── settings.py            # Pydantic settings management
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── routes.py              # Auth route handlers
│   │   ├── schemas.py             # Pydantic models for auth
│   │   ├── security.py            # JWT and password hashing
│   │   ├── storage.py             # User data storage logic or db access
│   │   ├── service.py             # user auth orchestration (DB-facing)
│   │   └── dependencies.py        # Auth dependencies
│   │
│   ├── dashboard/
│   │   ├── __init__.py
│   │   └── dashboard.py          # can be converted into a route handler
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── client.py            # Database client module for interacting with the database
│   │   ├── user_repository.py   # Identity-only
│   │   └── auth_repository.py   # Joins & Hashes
│   │
│   ├── nlp/
│   │   ├── __init__.py
│   │   ├── JEA_minutes_scraper.py
│   │   ├── highlight_mentions.py
│   │   └── NLP_test.py
│   │
│   ├── services/
│   │   ├── scraper_service.py    # will wrap your existing scripts
│   │   └── pdf_service.py
│   │
│   └── templates/
│       ├── layouts/
│       │   ├── base.html
│       │   └── home.html
│       ├── auth/
│       │   ├── login.html
│       │   └── register.html
│       ├── dashboard/
│       │   ├── dashboard.html
│       │   └── downloads.html
│       │
│       └── static/
│           ├── css/
│           ├── js/
│           └── images/
│
├── environment.yml
├── pyproject.toml
├── pyproject_orginal.toml
├── pytest.ini
├── .pre-commit-config.yaml
├── .env
├── .env.example
├── .gitignore
├── keywords.txt
├── uv.lock
├── README.md
└── scraper.log
```
