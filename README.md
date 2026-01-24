# 🏛️ JEA Meeting Minutes Intelligence Platform

> *A Secure FastAPI Web Application for Scraping, Annotating, and Extracting Signals From Municipal Meeting Records*

This application is a **private, login-protected FastAPI web platform** designed to extract **business development and pre-positioning intelligence** from publicly available municipal meeting records.

While the system initially targets **JEA (Jacksonville Electric Authority)**, it is architected to support additional municipalities such as **City of Jacksonville Beach**, **Atlantic Beach**, **Palm Coast**, and others.

Authenticated users can manage profiles, select municipalities, define keyword sets, execute scraping and NLP pipelines, and download **annotated meeting records** bundled as ZIP archives. No scraped documents are stored long-term.

---

## 🔐 Key Design Principles

- FastAPI backend with Jinja2-rendered UI
- JWT-based authentication using HttpOnly secure cookies
- Database stores users and profiles only
- No PDFs stored in the database (disk-only to minimize cost and risk)
- Service-layer architecture separating web, scraping, and NLP concerns
- Background task execution for long-running scraper jobs
- ZIP-based export model for all results
- Expandable to additional municipalities

---

## 🚀 Core Features

### 🔑 Authentication & User Profiles

Authenticated users can manage personal and organizational profile data.
Authentication uses JWT tokens stored in HttpOnly cookies.

---

### 🧠 Keyword Management

Users can select predefined keyword categories or define custom keyword sets
used for text extraction and PDF annotation.

---

### 🏙️ Municipality / Client Selection

Supported municipalities include:

- JEA
- City of Jacksonville Beach
- Atlantic Beach
- Palm Coast

---

### 📄 Scraper & NLP Pipeline

Scraping jobs are launched from the UI and executed as background tasks.

Pipeline stages include web scraping, PDF text extraction, keyword matching,
NLP annotation, and PDF highlighting.

Outputs are written to disk only.

---

### 📦 Result Packaging

Completed runs generate a ZIP bundle containing raw PDFs, annotated PDFs,
and extracted metadata.

---

## 🗂️ Project Structure

```text
src/
├── webapp/
├── services/
├── NLP/
└── data/
```

---

## 🧰 Technology Stack

- FastAPI
- Jinja2
- Bootstrap 5
- JWT (HttpOnly cookies)
- spaCy
- pdfplumber / PyPDFium2
- SQLite / PostgreSQL
- uv

---

## ⚙️ Running Locally (uv + FastAPI)

### Install uv

```bash
pip install uv
```

or

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

### Install Dependencies

```bash
uv sync
```

---

### Run the Application

```bash
uv run uvicorn src.jea_meeting_web_scraper.main:app --reload
```

---

## 🛡️ Security Summary

- Short-lived JWT tokens
- HttpOnly cookies
- HTTPS recommended
- No document storage in DB

---

## 👔 Purpose & Ethics

This platform is intended solely for internal business development use.
All materials are publicly available records.
