# ✅ JEA / Municipal Meeting Intelligence Dashboard  
## Build Checklist (CLI → FastAPI Web App)

> **Purpose**  
> This checklist guides the development of a FastAPI-based web application for scraping, analyzing, and distributing municipal meeting intelligence.  
> The application is designed for **small internal use**, with controlled access, minimal infrastructure cost, and a clean upgrade path if organizational adoption expands.

---

## 🧭 Phase 0 — Project Alignment & Guardrails

- [ ] Confirm core goal: internal intelligence tool (not public SaaS)
- [ ] Confirm initial users (you + limited coworkers)
- [ ] Confirm deployment model (single web instance)
- [ ] Confirm DB strategy: Turso (SQLite + edge replication)
- [ ] Confirm data policy:
  - [ ] Do not store scraped PDFs long-term
  - [ ] Generate downloadable ZIPs on demand
  - [ ] Clean temporary files after job completion
- [ ] Confirm non-goals (for now):
  - [ ] No billing
  - [ ] No org-level RBAC
  - [ ] No heavy analytics dashboards

---

## 🏗️ Phase 1 — Backend Foundation (FastAPI)

- [ ] FastAPI scaffold finalized
- [ ] Environment-based settings (dev/prod)
- [ ] Health check endpoint
- [ ] Logging configured
- [ ] CORS configured conservatively
- [ ] Routers split by domain (auth, users, agencies, jobs, downloads)

---

## 🗄️ Phase 2 — Database Design (Turso)

- [ ] Users table
- [ ] Profiles table
- [ ] Agencies table
- [ ] Keywords table
- [ ] User preferences table
- [ ] Foreign keys enforced
- [ ] Migration strategy documented

---

## 🔐 Phase 3 — Authentication & Controlled Access

- [ ] Authorization code required for registration
- [ ] Code stored securely (env or DB)
- [ ] Ability to rotate authorization code
- [ ] Password hashing (bcrypt/argon2)
- [ ] Login / logout flow
- [ ] JWT or session expiration defined

### Password Reset
- [ ] Forgot-password endpoint
- [ ] One-time reset token
- [ ] Token expiration enforced
- [ ] Email delivery configured

---

## 👤 Phase 4 — User Profiles & Preferences

- [ ] Profile creation on first login
- [ ] Editable user profile
- [ ] Agency selection UI
- [ ] Keyword selection UI
- [ ] Custom keyword support
- [ ] Preferences persisted per user

---

## 🧠 Phase 5 — Scraping & Intelligence Pipeline

- [ ] Scraper logic moved to service layer
- [ ] Async-safe execution
- [ ] Timeouts & error handling
- [ ] Job status tracking (basic)

---

## 📦 Phase 6 — Output & Downloads

- [ ] Annotated results generated
- [ ] ZIP packaging
- [ ] Secure download endpoint
- [ ] Automatic cleanup policy

---

## 🌐 Phase 7 — Frontend (Lightweight)

- [ ] Login page
- [ ] Registration page
- [ ] Password reset pages
- [ ] Dashboard UI
- [ ] Job submission UX
- [ ] Download links

---

## 🚀 Phase 8 — Deployment

- [ ] Environment variables set
- [ ] HTTPS enforced
- [ ] Turso connected in prod
- [ ] Smoke tests passed

---

## 🔒 Phase 9 — Security Review

- [ ] Auth code never logged
- [ ] Password reset tokens expire
- [ ] Rate limiting on auth routes
- [ ] Dependency versions pinned

---

## 📈 Phase 10 — Future Scale (Optional)

- [ ] Invite-based access
- [ ] Role-based permissions
- [ ] Managed Postgres migration
- [ ] Background job queue
- [ ] Audit logging

---

**Design Philosophy:**  
Build small. Ship value. Let success justify scale.
