# 📜 Architecture Decision Record (ADR)

## ADR-001: FastAPI for Web Layer

**Decision:** Use FastAPI  
**Rationale:** Async support, clear dependency injection, Python-native

---

## ADR-002: Turso (SQLite) for Database

**Decision:** Use Turso  
**Rationale:** Low cost, minimal ops, sufficient scale

---

## ADR-003: Auth-Code Gated Registration

**Decision:** Require 6-digit authorization code  
**Rationale:** Prevent unauthorized access while allowing self-service

---

## ADR-004: Admin-Only Client Management

**Decision:** Restrict client creation to admins  
**Rationale:** Scraping is brittle; data integrity is critical

---

## ADR-005: No Persistent Scraper Outputs

**Decision:** Do not store PDFs in DB  
**Rationale:** Cost control and data minimization

---

**ADR Principle:**  
> _Every decision is reversible, but not free._
