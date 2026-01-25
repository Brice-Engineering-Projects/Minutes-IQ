# 🗺️ High-Level Roadmap — JEA Meeting Intelligence Platform

This roadmap is a **checklist-style guide** that reflects the *actual state* of the project today and the **intentional sequencing** going forward.

It is not aspirational.  
It is designed to minimize rework, refactors, and operational risk.

---

## Phase 0 — Foundation (✅ Complete)

**Goal:** Eliminate ambiguity before implementation.

- [x] Project vision clarified (internal tool, limited users)
- [x] FastAPI transition decision documented
- [x] Turso selected for cost-controlled persistence
- [x] Documentation-first approach adopted
- [x] Architecture Decision Record (ADR) written
- [x] Build checklist defined
- [x] Database schema finalized (auth, profiles, clients)
- [x] Security model defined
- [x] Admin governance policy defined
- [x] Operational runbook created
- [x] Sequence diagrams completed
- [x] API contract finalized

**Exit Criteria:**  
Architecture decisions are locked and traceable.

---

## Phase 1 — Auth Refactor & Stabilization (✅ Complete)

**Goal:** Establish clean auth boundaries before adding features.

- [x] Split monolithic auth module into layered components
- [x] Isolated crypto logic (JWT / bcrypt)
- [x] Isolated FastAPI dependencies
- [x] Isolated auth service logic
- [x] Updated all tests to reference new structure
- [x] Deleted legacy `auth_routes.py`
- [x] Ruff / pre-commit stabilized
- [x] Auth behavior preserved and verified by tests

**Exit Criteria:**  
Auth structure is stable, test-covered, and extensible.

---

## Phase 2 — Persistence Layer

**Goal:** Give the application long-term memory by storing users in a database instead of in temporary in-memory storage.

### What This Phase Accomplishes

- User accounts persist across restarts and deployments
- Authentication becomes production-ready
- The system is safer to test and easier to extend

### Checklist

- [x] **Define DB Module**
- [x] **Create database connection layer**
  - Add a single, centralized module responsible for connecting to the database
  - Ensure all database access flows through this module
- [x] Validate schema & migrations
- [x] Seed admin user
- [x] Verify DB access programmatically

- [x] **Implement user data access (CRUD)**
  - Add functions to create, read, update, and delete users
  - Isolate database logic from authentication and route handlers

- [x] **Migrate authentication to database-backed users**
  - Replace in-memory user storage with database queries
  - Validate credentials against stored user records

- [x] **Update tests for database usage**
  - Modify tests to use test users, fixtures, or mock data
  - Ensure tests do not interact with real user data

- [x] **Verify migrations and rollback safety**
  - Confirm database schema changes apply cleanly
  - Validate rollback procedures in case of migration failure

### Completion Criteria

- Users persist after application restarts
- Authentication no longer relies on in-memory data
- All tests pass using database-backed user data
- Database changes are reversible and documented

**Exit Criteria:**  
Auth no longer depends on in-memory data structures.

---

## Phase 3 — Controlled Registration (⏳ Planned)

**Goal:** Prevent unauthorized self-registration.

- [ ] Implement authorization-code model
- [ ] Admin-only auth code rotation
- [ ] Registration blocked without valid code
- [ ] Tests for valid / invalid / expired codes
- [ ] Update docs and sequence diagrams

**Exit Criteria:**  
Only explicitly authorized users can create accounts.

---

## Phase 4 — Password Reset Flow (⏳ Planned)

**Goal:** Enable safe account recovery.

- [ ] Password reset token model
- [ ] Token expiration enforcement
- [ ] One-time token usage
- [ ] Email delivery integration
- [ ] End-to-end password reset tests

**Exit Criteria:**  
Users can recover access without admin intervention.

---

## Phase 5 — Client & Keyword Management (⏳ Planned)

**Goal:** Enable real value from the dashboard.

- [ ] Admin-managed client pool
- [ ] Client source configuration
- [ ] Keyword taxonomy defined
- [ ] User-specific favorites
- [ ] Validation of scraper sources

**Exit Criteria:**  
Users can reliably target relevant agencies.

---

## Phase 6 — Scraper Orchestration (⏳ Planned)

**Goal:** Convert scraper into a safe, async service.

- [ ] Background job execution
- [ ] Job status tracking
- [ ] Timeout and failure handling
- [ ] ZIP artifact generation
- [ ] Secure download endpoints

**Exit Criteria:**  
Scrapes run asynchronously without blocking the UI.

---

## Phase 7 — UI & UX (⏳ Planned)

**Goal:** Provide a usable internal dashboard.

- [ ] Login / logout pages
- [ ] Registration flow
- [ ] Password reset UI
- [ ] Client & keyword selection UI
- [ ] Download management

**Exit Criteria:**  
Non-technical users can use the system end-to-end.

---

## Phase 8 — Deployment & Hardening (⏳ Planned)

**Goal:** Prepare for limited internal distribution.

- [ ] Production configuration verified
- [ ] HTTPS enforced
- [ ] Environment variables audited
- [ ] Logging reviewed
- [ ] Smoke tests in prod

**Exit Criteria:**  
System is stable for internal use.

---

## Phase 9 — Optional Scale-Up (🚫 Not Committed)

**Goal:** Only if leadership approves.

- [ ] Role-based access control
- [ ] Invite-based onboarding
- [ ] Managed Postgres migration
- [ ] Background job queue
- [ ] Audit logging

**Exit Criteria:**  
Business value justifies cost.

---

## Guiding Principle

> **Stability before features.  
> Architecture before implementation.  
> Scale only when paid for.**
