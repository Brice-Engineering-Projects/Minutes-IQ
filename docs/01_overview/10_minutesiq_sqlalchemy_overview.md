# 📄 MinutesIQ – SQLAlchemy Refactor (Scope & Overview)

## 1. Purpose

This document outlines the planned refactor of the MinutesIQ database layer from raw connection-based access (libsql / sqlite-style `connect`) to a structured SQLAlchemy-based architecture compatible with Turso.

---

## 2. Current State

- Database access uses direct `connect()` calls
- Queries are written as raw SQL
- Tight coupling between application logic and database client
- Test instability due to lack of isolation and schema control
- Use of experimental client (`libsql_experimental`)

---

## 3. Goals of Refactor

- Introduce SQLAlchemy as the database abstraction layer
- Decouple application logic from database implementation
- Enable stable and isolated test environment using SQLite
- Replace experimental DB client with stable solution
- Prepare system for long-term scalability and maintainability

---

## 4. Target Architecture

### Components

- SQLAlchemy Engine
- SQLAlchemy ORM Models
- Session-based database access
- Repository layer for DB interactions
- Service layer remains unchanged

---

## 5. Database Strategy

### Production Strategy
- Turso connection will be used as database client
- SQLAlchemy will be used as ORM layer
- Underlying driver MUST use HTTP-based transport
- Hrana/WebSocket transport is explicitly avoided
- If no stable SQLAlchemy-compatible HTTP driver exists:
    - Continue using libsql_experimental under repository layer
    - Or migrate to PostgreSQL

### Development & Testing
- SQLite via SQLAlchemy

---

## 6. Key Design Principles

- Single source of truth for DB access (Session)
- No direct DB calls outside repository layer
- Environment-based DB configuration
- Backwards-compatible migration strategy

---

## 7. Risks & Mitigation

### Risk
- Large refactor scope

### Mitigation
- Incremental migration
- Parallel support for old + new during transition

---

## 8. Success Criteria

- All DB access routed through SQLAlchemy
- Tests run fully on SQLite
- No dependency on experimental DB client
- Production runs on stable Turso connection

---

## 9. Timeline (Flexible)

- Phase-based implementation (see checklist document)
- No hard deadline — prioritize correctness over speed

---

## 10. Summary

This refactor moves MinutesIQ from a tightly coupled DB implementation to a scalable, testable, and maintainable architecture using SQLAlchemy.
