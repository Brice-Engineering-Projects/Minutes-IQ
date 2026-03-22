# 📄 MinutesIQ – SQLAlchemy Refactor Checklist

## Phase 1 – Foundation Setup

- [ ] Add SQLAlchemy and driver dependencies to project config
- [ ] Pin versions for SQLAlchemy and related DB drivers
- [ ] Document dependency rationale in project docs/changelog
- [ ] Create central DB config module (single source of truth)
- [ ] Add environment-based DB URL resolution (dev/test/prod)
- [ ] Add explicit configuration flags for echo/logging and pool options
- [ ] Implement engine factory with per-environment settings
- [ ] Implement SessionLocal/sessionmaker factory
- [ ] Implement request-scoped get_db() dependency for FastAPI
- [ ] Add startup validation for required DB configuration
- [ ] Add defensive error messaging for invalid DB URL/driver config
- [ ] Verify application boots with DB layer initialized

---

## Phase 2 – Model Definition

- [ ] Define Base = declarative_base() in dedicated models base module
- [ ] Establish model package structure and import strategy
- [ ] Implement User model with schema-compatible fields and constraints
- [ ] Implement ScraperJob model with schema-compatible fields and constraints
- [ ] Implement Client model with schema-compatible fields and constraints
- [ ] Implement additional high-use models needed by current endpoints
- [ ] Map primary keys and foreign keys to existing schema conventions
- [ ] Add ORM relationships for user ↔ jobs and client ↔ jobs
- [ ] Define nullable/default semantics to mirror current schema behavior
- [ ] Confirm table names exactly match existing DB tables
- [ ] Add model-level indexes/unique constraints where schema expects them
- [ ] Validate generated metadata against current schema design

---

## Phase 3 – Repository Layer

- [ ] Create repository package and base repository utilities
- [ ] Define repository interfaces/contracts for key domains
- [ ] Implement UserRepository with SQLAlchemy session usage only
- [ ] Implement JobRepository with SQLAlchemy session usage only
- [ ] Implement ClientRepository with SQLAlchemy session usage only
- [ ] Add pagination/filter/sort support consistent with current behavior
- [ ] Add owner/admin-scoped query helpers where needed
- [ ] Replace raw SQL read paths with ORM/query-builder equivalents
- [ ] Replace raw SQL write/update/delete paths with ORM equivalents
- [ ] Standardize transaction boundaries and commit/rollback patterns
- [ ] Add repository-level error translation (not found/conflict/etc.)
- [ ] Add lightweight repository unit tests for each migrated method

---

## Phase 4 – Service Layer Integration

- [ ] Update service constructors to receive SQLAlchemy-backed repositories
- [ ] Remove all direct DB connection usage from services
- [ ] Ensure service APIs remain backward compatible for route handlers
- [ ] Preserve existing authorization and ownership checks
- [ ] Preserve existing validation/error behavior contracts
- [ ] Confirm no business logic drift during repository swap
- [ ] Add service tests for key workflows with mocked repositories
- [ ] Run regression checks for scraper and auth-related service flows

---

## Phase 5 – Testing Setup

- [ ] Configure dedicated SQLite test DB URL and engine options
- [ ] Create test engine/session fixtures for pytest
- [ ] Implement FastAPI dependency override for get_db in tests
- [ ] Add schema create/drop lifecycle fixture strategy
- [ ] Add per-test transaction rollback isolation fixture
- [ ] Seed required baseline test data (roles/users/minimum refs)
- [ ] Update existing DB fixtures to use SQLAlchemy session
- [ ] Update integration tests that rely on raw connection helpers
- [ ] Verify deterministic test ordering independence
- [ ] Validate parallel/local test runs are stable

---

## Phase 6 – Migration Strategy

- [ ] Define migration plan by domain (auth, users, scraper, clients, keywords)
- [ ] Identify and track all remaining direct connect()/raw SQL call sites
- [ ] Migrate one domain at a time with feature-parity verification
- [ ] Maintain temporary compatibility shim where dual access is required
- [ ] Validate data integrity after each domain migration
- [ ] Add rollback strategy for each migration increment
- [ ] Remove migrated legacy code paths incrementally
- [ ] Keep changelog entries for each migration batch
- [ ] Confirm no new raw SQL introduced outside repositories

---

## Phase 7 – Production Integration

- [ ] Configure production SQLAlchemy engine for Turso/libSQL target
- [ ] Validate TLS/connection parameters for production environment
- [ ] Remove dependency on libsql_experimental in production paths
- [ ] Add connection health checks and startup diagnostics
- [ ] Add query timeout/retry/pool tuning settings
- [ ] Validate write/read behavior in staging environment
- [ ] Run end-to-end smoke tests on deployed environment
- [ ] Verify auth, scraper jobs, clients, and keyword flows in production-like setup
- [ ] Capture performance baseline before/after migration

---

## Phase 8 – Cleanup

- [ ] Remove obsolete DB helper modules and dead code
- [ ] Remove unused raw SQL query utilities
- [ ] Remove deprecated connection wrappers and compatibility shims
- [ ] Remove experimental DB dependencies from project config
- [ ] Refactor imports/usages to final SQLAlchemy module layout
- [ ] Update architecture docs with final DB access pattern
- [ ] Update contributor docs for repository and session usage conventions
- [ ] Update runbooks for debugging DB/session issues

---

## Phase 9 – Validation

- [ ] Full unit test suite passes
- [ ] Full integration test suite passes
- [ ] Targeted end-to-end tests pass for critical user journeys
- [ ] Static scan confirms no direct DB calls outside repositories
- [ ] Verify production deployment completed successfully
- [ ] Validate performance is within acceptable regression threshold
- [ ] Validate error rates and DB connectivity are stable post-deploy
- [ ] Obtain final sign-off for SQLAlchemy migration completion

---

## Phase 10 – Post-Refactor Enhancements (Optional)

- [ ] Introduce Alembic for schema migration lifecycle management
- [ ] Add automated migration checks in CI
- [ ] Profile and optimize high-volume query paths
- [ ] Add/adjust database indexes based on observed workloads
- [ ] Introduce selective caching for expensive read-heavy endpoints
- [ ] Add query observability/metrics for long-term tuning
- [ ] Establish DB performance SLOs and monitoring dashboards

---

## Cross-Phase Tracking (Recommended)

- [ ] Create an issue/board epic for SQLAlchemy migration
- [ ] Track each phase as a milestone with owner and target date
- [ ] Define "phase done" criteria before implementation begins
- [ ] Record decisions and trade-offs in ADR/project docs
- [ ] Schedule checkpoint reviews after each phase
