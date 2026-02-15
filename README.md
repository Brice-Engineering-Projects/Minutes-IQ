# 🧠 Minutes IQ

## Municipal Meeting Intelligence Platform

![Python](https://img.shields.io/badge/python-3.12+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-async-success)
![uv](https://img.shields.io/badge/uv-package%20manager-orange)
![Build](https://img.shields.io/badge/build-passing-brightgreen)
![License](https://img.shields.io/badge/license-private-lightgrey)
![Status](https://img.shields.io/badge/status-active%20development-yellow)

> *A secure FastAPI platform for scraping, annotating, and extracting actionable intelligence from municipal meeting records.*

**Minutes IQ** is a **private, login-protected intelligence platform** designed to extract **business development and pre-positioning signals** from publicly available municipal meeting documents.

All scraping, NLP, and PDF annotation workflows are executed as **tracked asynchronous jobs**, with results packaged into downloadable ZIP artifacts. Documents are stored **on disk only**, never in the database.

---

## 📌 Versioning

* **Current Version:** `v0.7.0`
* **Phase Status:** Phase 6 – Scraper Orchestration **COMPLETE**
* **Stability:** Backend feature-complete, UI & deployment pending

Versioning follows semantic intent:

* `0.x` → Active architecture development
* `0.6.x` → Async scraper orchestration milestone
* `0.7.x` → UI + deployment
* `1.0.0` → Production-ready release

---

## 🔐 Key Design Principles

* FastAPI backend with service-oriented architecture
* JWT authentication using HttpOnly secure cookies
* Background task execution for long-running jobs
* Database used for metadata only (users, jobs, results)
* No PDFs stored in the database
* Structured disk storage with retention policies
* ZIP-based export model for all results
* Designed for multi-municipality expansion

---

## 🚀 Core Capabilities

### 🔑 Authentication & Profiles

* Secure login using JWT (HttpOnly cookies)
* User-scoped access to jobs, results, and artifacts

### 🧠 Keyword Intelligence

* Predefined and client-specific keyword sets
* Database-driven keyword selection
* NLP entity extraction and annotation

### 📄 Scraper & NLP Pipeline

Scraping jobs run asynchronously and include:

1. PDF discovery
2. Text extraction
3. Keyword matching
4. NLP entity extraction
5. PDF highlighting
6. Result persistence
7. Artifact generation

All stages are monitored, cancellable, and auditable.

### 📦 Artifact Generation

Each completed job produces a ZIP archive containing:

* Raw PDFs
* Annotated PDFs
* CSV result exports
* Metadata JSON

Artifacts are stored temporarily with configurable retention policies.

---

## 🗂️ Project Structure

The authoritative project structure is documented in:

`docs/02_architecture/01_project_structure.md`

That document defines:

* Complete directory layout
* Module responsibilities
* Separation between web, service, scraper, NLP, and data layers
* Conventions for future expansion

The README intentionally avoids duplicating the structure here to prevent documentation drift.

---

## 🧰 Technology Stack

* Python 3.12+
* FastAPI
* Jinja2
* Bootstrap 5
* JWT (HttpOnly cookies)
* spaCy (lazy-loaded)
* pdfplumber / PyMuPDF / PyPDFium2
* SQLite / PostgreSQL
* uv (dependency & environment management)

---

## ⚙️ Local Development

### Install uv

`pip install uv`

or

`curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh`

### Install Dependencies

`uv sync`

### Run the Application

`uv run uvicorn src.minutes_iq.main:app --reload`

API documentation will be available at:

[http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🛡️ Security Summary

* Short-lived JWT tokens
* HttpOnly cookies (XSS-resistant)
* HTTPS required in production
* No document persistence in DB
* Ownership enforcement on all job and artifact resources

---

## 👔 Purpose & Ethics

Minutes IQ is intended for private, internal business development use only.

All data is sourced from publicly available municipal records and is used for ethical pre-positioning and intelligence analysis. No sensitive or personally identifiable information is collected or distributed.

---

## 🧭 Roadmap

* UI completion (dashboard, job monitoring, downloads)
* Deployment (Cloudflare Tunnel / Fly.io / Render)
* Role-based access control
* Scheduled scraping
* Artifact expiration automation
* Multi-municipality onboarding tooling

---

Minutes IQ
Turning meeting minutes into signals, not noise.
