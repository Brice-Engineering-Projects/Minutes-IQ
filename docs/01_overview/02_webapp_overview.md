# Web Application Overview

## 1. Purpose

This document provides a high-level overview of the FastAPI-based web interface developed to support a secure, private workflow for the JEA meeting‑minutes scraper and PDF annotation pipeline.

The application provides:

- A fully private web dashboard
- Login‑protected access
- A trigger mechanism for running the scraper
- A downloads page for accessing annotated PDFs
- A Bootstrap‑styled interface for usability

---

## 2. Objectives

- Create a web-accessible layer without exposing core scraper logic.
- Introduce authentication (JWT + HttpOnly cookies).
- Maintain code separation between UI, business logic, and NLP components.
- Improve the usability and professionalism of the scraper.

---

## 3. Key

Features

- Modern FastAPI backend
- Jinja2 server-side templates
- Bootstrap 5 front-end styling
- Secure login flow
- Background task execution
- Downloadable PDF results

---

## 4. Intended Users

This application is designed **exclusively** for private, internal use by the project owner.  
It is not intended for public access or external distribution.
All data handling and processing comply with ethical standards for publicly available information.
