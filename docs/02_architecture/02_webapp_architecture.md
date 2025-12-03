# Web Application Architecture

## 1. System Overview
The web application consists of a FastAPI backend paired with Jinja-rendered HTML templates and Bootstrap styling.

It is built on a modular structure:
- Web layer (`webapp`)
- Service layer (`services`)
- NLP & scraper logic (`NLP`)
- Data storage (`data`)

---

## 2. Architecture Diagram (ASCII)

```
                 ┌─────────────────────────────┐
                 │         Web Browser         │
                 │ (User Interface, Bootstrap) │
                 └──────────────┬──────────────┘
                                │
                                ▼
                     ┌────────────────────┐
                     │      FastAPI       │
                     │   (main.py app)    │
                     └────────┬───────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐     ┌────────────────┐     ┌──────────────────────┐
│  Templates   │     │ Authentication │     │     Route Handlers   │
│  (Jinja2)    │     │  (JWT Cookies) │     │  (dashboard, runs)   │
└──────┬───────┘     └───────┬────────┘     └──────────┬──────────┘
       │                     │                          │
       ▼                     ▼                          ▼
┌────────────────┐  ┌──────────────────┐      ┌────────────────────┐
│ Static Assets  │  │  Service Layer   │      │   Background Tasks  │
│  (Bootstrap)   │  │ (scraper, PDFs)  │      │  (run pipeline)     │
└────────────────┘  └────────┬─────────┘      └─────────┬──────────┘
                              │                         │
                              ▼                         ▼
                      ┌──────────────┐        ┌────────────────────┐
                      │   NLP Code   │        │  Annotated PDFs     │
                      │  (scraping)  │        │  output directory   │
                      └──────────────┘        └────────────────────┘
```

---

## 3. Components

### 3.1 Web Layer (`webapp/`)
- Routes
- JWT authentication
- Jinja templates
- Static assets
- User login flow

### 3.2 Service Layer (`services/`)
- Wraps scraper logic
- Runs PDF annotation
- Ensures clean separation between UI and backend logic

### 3.3 NLP Layer (`NLP/`)
- Existing scraper logic
- Keyword detection
- Highlighting logic

### 3.4 Data Layer
Folders for:
- Raw PDFs
- Processed text
- Annotated PDFs

---

## 4. Route Overview

| Route | Purpose | Auth Required |
|-------|---------|---------------|
| `/login` | Login form | ❌ |
| `/auth/login` | Validate credentials | ❌ |
| `/dashboard` | Main UI | ✔ |
| `/run-scraper` | Trigger scraper | ✔ |
| `/downloads` | View files | ✔ |
| `/download/<file>` | File download | ✔ |

---

## 5. Authentication Model
JWT tokens stored in secure, HttpOnly cookies.

---

## 6. UI Architecture
- Template inheritance via `base.html`
- Bootstrap components
- Flash messages / status banners

