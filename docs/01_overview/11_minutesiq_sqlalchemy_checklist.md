# 📄 MinutesIQ – SQLAlchemy Refactor Checklist

## Phase 1 – Foundation Setup

- [ ] Install SQLAlchemy
- [ ] Create database configuration module
- [ ] Define engine creation logic (env-based)
- [ ] Create SessionLocal factory
- [ ] Implement get_db() dependency

---

## Phase 2 – Model Definition

- [ ] Define Base = declarative_base()
- [ ] Create User model
- [ ] Create ScraperJob model
- [ ] Create Client model
- [ ] Define relationships (FKs)

---

## Phase 3 – Repository Layer

- [ ] Create repository structure
- [ ] Implement UserRepository
- [ ] Implement JobRepository
- [ ] Implement ClientRepository
- [ ] Replace raw SQL with ORM queries

---

## Phase 4 – Service Layer Integration

- [ ] Update services to use repositories
- [ ] Remove direct DB calls from services
- [ ] Validate business logic unchanged

---

## Phase 5 – Testing Setup

- [ ] Configure SQLite test database
- [ ] Create test engine
- [ ] Implement dependency override
- [ ] Add DB setup/teardown fixtures
- [ ] Ensure test isolation

---

## Phase 6 – Migration Strategy

- [ ] Maintain compatibility with existing schema
- [ ] Validate existing data integrity
- [ ] Gradually replace legacy DB calls
- [ ] Remove old connect-based logic

---

## Phase 7 – Production Integration

- [ ] Configure Turso connection via SQLAlchemy
- [ ] Replace experimental client
- [ ] Validate connection stability
- [ ] Run end-to-end tests

---

## Phase 8 – Cleanup

- [ ] Remove unused DB code
- [ ] Remove experimental dependencies
- [ ] Refactor imports
- [ ] Update documentation

---

## Phase 9 – Validation

- [ ] All tests passing
- [ ] No direct SQL outside repositories
- [ ] Production deployment verified
- [ ] Performance acceptable

---

## Phase 10 – Post-Refactor Enhancements (Optional)

- [ ] Add migrations (Alembic)
- [ ] Optimize queries
- [ ] Add indexing strategy
- [ ] Add caching if needed
