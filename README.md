# 🏛️ JEA Meeting Minutes Intelligence Platform  

>*A Secure FastAPI Web Application for Scraping, Annotating, and Extracting Signals From Municipal Meeting Records*

This application provides a **private, login-protected FastAPI dashboard** for scraping meeting minutes from municipal agencies (starting with **JEA**, but extendable to **City of Jacksonville Beach**, **Atlantic Beach**, **Palm Coast**, etc.).  

Authenticated users can manage their profile, select clients to scrape, select or define keywords, run the scraper pipeline, and download annotated PDFs in a ZIP bundle.

This system is explicitly designed for **internal business development** and **pre-positioning intelligence**—no documents or annotations are stored long-term in the database.

---

## 🔐 Key Design Principles

- **FastAPI backend + Jinja2 UI**  
- **JWT authentication** (HttpOnly secure cookies)  
- **Database stores users + profiles only**  
- **No PDF storage in DB** → All PDFs stay on disk to keep costs low  
- **Scraper + NLP pipeline stays separate from web layer** (service layer architecture)  
- **Zip-based export** for easy downloads  
- **Extendable** to multiple municipalities

---

## 🚀 Core Features

### 🔑 1. Authentication & User Profiles

Once a user logs in, they can create and manage:

- Full Name  
- Email  
- Business Unit / Group  
- Assigned Clients (JEA, COJ Beach, Atlantic Beach, etc.)

Auth model uses **JWT tokens stored in HttpOnly cookies** for maximum safety.

---

### 🧠 2. Keyword Management

Users can:

- Select from **predefined keyword categories**  
- Add new custom keywords  
- Save keyword lists associated with their profile  

---

### 🏙️ 3. Client Selection

The dashboard provides a dropdown of supported municipalities:

- JEA  
- City of Jacksonville Beach  
- Atlantic Beach  
- Palm Coast  
- (Expandable list via admin UI in future versions)

---

### 📄 4. Scraper Pipeline

The FastAPI UI triggers the scraper as a **background task** so the user doesn't have to wait.

Pipeline includes:

- Web scraping  
- PDF text extraction  
- Keyword matching  
- NLP annotation (spaCy)  
- PDF highlighting  
- Bookmark generation  
- Organized output into `/data/raw_pdfs/`, `/data/processed/`, `/data/annotated_pdfs/`

---

### 📦 5. Result Packaging  

After the run completes, the dashboard presents a **Download ZIP** button containing:

- Raw PDFs  
- Annotated PDFs  
- CSV of extracted metadata  
- Optional NLP summaries (future feature)

No results are stored in the database.

---

## 🗂️ Project Structure

The project structure below illustrates the simplified version.  For full project structure, see the [detailed plan](docs/02_architecture/01_project_structure.md).

```plaintext
src/
├── webapp/                # FastAPI, auth, templates, dashboard UI
│   ├── main.py
│   ├── auth.py
│   ├── routes.py
│   ├── templates/
│   └── static/
│
├── services/              # Service layer wrapping scraper + PDF annotation
│   ├── scraper_service.py
│   └── pdf_service.py
│
├── NLP/                   # Original scraper & NLP pipeline
│   ├── JEA_minutes_scraper.py
│   ├── highlight_mentions.py
│   └── NLP_test.py
│
└── data/
    ├── raw_pdfs/
    ├── processed/
    └── annotated_pdfs/
```

---

## 🧰 Technology Stack

- **FastAPI** (backend & routing)  
- **Jinja2** (HTML templates)  
- **Bootstrap 5** (UI styling)  
- **JWT + HttpOnly cookies** (secure session auth)  
- **Background Tasks** for long scraper runs  
- **spaCy** for NLP  
- **pdfplumber / PyPDFium2** for PDF parsing & highlighting  
- **SQLite** (or PostgreSQL in production) for user auth + profile data  
- **Cloudflare Tunnel, Render, Fly.io** supported for deployment  

---

## 🥽 User Dashboard Flow

1. **Login → `/login`**  
2. **Create or update profile**  
3. **Choose keywords** (or add custom)  
4. **Select municipality/client**  
5. **Run scraper** (background task)  
6. **View results in dashboard**  
7. **Download ZIP** of all outputs  

Protected routes require JWT validation.

---

## ⚙️ Running Locally

```bash
uvicorn src.jea_meeting_web_scraper.main:app --reload
```

If using Conda:

```bash
conda activate your_env
pip install -r requirements.txt
```

---

## 🛡️ Security Summary

- JWT tokens are **short-lived**  
- Stored in **HttpOnly cookies**  
- All interactive routes use `Depends(get_current_user)`  
- Recommended deployment: **Cloudflare Tunnel + HTTPS**  
- No PDFs or extracted text stored in DB—only user profile + auth  

---

## 🔭 Future Enhancements

- Keyword customization via UI  
- Admin panel for managing municipalities  
- PDF previews in-browser  
- Scheduled scraping  
- Email or Slack alerts  
- Docker deployment  
- Full CI/CD pipeline  

---

## 👔 Purpose & Ethics

This platform is intended **solely for internal business development**. All scraped data is **publicly available** and used responsibly. No distribution of annotated content occurs outside your organization.
