# Database Migrations

**Audience:** Developers, operations
**Purpose:** Document how database schema changes are managed and applied

---

## Migration Strategy

This project uses **manual SQL migrations** tracked in version control rather than an automated migration tool like Alembic. This approach is appropriate for:

- Small projects with limited schema complexity
- Turso (libSQL) which has some limitations with traditional migration tools
- Projects with few developers and infrequent schema changes

---

## Migration Files Location

All migration files are stored in: `migrations/`

Each migration file is named with the format:
```
YYYYMMDD_HHMMSS_description.sql
```

Example:
```
20260125_120000_initial_schema.sql
20260125_130000_add_user_status.sql
```

---

## Current Schema (v1)

The current schema is documented in `docs/08_database/01_database_schema_plain_english.md` and consists of:

- **roles** - User roles (admin, user)
- **users** - User accounts
- **auth_providers** - Authentication provider types
- **auth_credentials** - User authentication credentials

---

## Applying Migrations

### For Development (Local/Test Database)

```bash
# Using Turso CLI
turso db shell jea-meeting-scraper-dev < migrations/20260125_120000_initial_schema.sql
```

### For Production (Turso Hosted Database)

```bash
# 1. Review the migration file
cat migrations/YYYYMMDD_HHMMSS_description.sql

# 2. Test on development database first
turso db shell jea-meeting-scraper-dev < migrations/YYYYMMDD_HHMMSS_description.sql

# 3. Apply to production (after testing)
turso db shell jea-meeting-scraper-prod < migrations/YYYYMMDD_HHMMSS_description.sql
```

---

## Rolling Back Migrations

Each migration file should include:
1. **UP section** - The forward migration (commented with `-- UP`)
2. **DOWN section** - The rollback steps (commented with `-- DOWN`)

Example migration file:
```sql
-- Migration: Add user status column
-- Created: 2026-01-25 13:00:00

-- UP
ALTER TABLE users ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1;
CREATE INDEX idx_users_is_active ON users(is_active);

-- DOWN (Rollback instructions)
-- To roll back, run:
-- DROP INDEX idx_users_is_active;
-- ALTER TABLE users DROP COLUMN is_active;
```

###  Rollback Procedure

1. Copy the DOWN section from the migration file
2. Save to a new file: `migrations/rollback_YYYYMMDD_HHMMSS.sql`
3. Test on development database
4. Apply to production if needed

---

## Creating a New Migration

### 1. Create the Migration File

```bash
# Create new migration file
touch migrations/$(date +%Y%m%d_%H%M%S)_your_description.sql
```

### 2. Write the Migration

```sql
-- Migration: Your description here
-- Created: YYYY-MM-DD HH:MM:SS

-- UP
-- Your forward migration SQL here
CREATE TABLE new_table (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL
);

-- DOWN (Rollback instructions)
-- To roll back, run:
-- DROP TABLE new_table;
```

### 3. Test the Migration

```bash
# Test on development database
turso db shell jea-meeting-scraper-dev < migrations/YYYYMMDD_HHMMSS_your_description.sql

# Verify schema
turso db shell jea-meeting-scraper-dev ".schema"
```

### 4. Document the Change

Update `docs/08_database/01_database_schema_plain_english.md` with the schema changes.

---

## Migration Checklist

Before applying any migration to production:

- [ ] Migration file follows naming convention
- [ ] Migration includes both UP and DOWN sections
- [ ] Migration tested on development database
- [ ] Rollback procedure tested
- [ ] Schema documentation updated
- [ ] Code changes that depend on migration are ready
- [ ] Backup of production database taken (if applicable)

---

## Emergency Rollback

If a migration causes issues in production:

1. **Immediately assess impact** - Can the app continue running?
2. **Execute rollback** - Apply the DOWN section
3. **Verify rollback** - Check that schema is reverted
4. **Deploy previous code version** - If new code depends on migration
5. **Document incident** - What went wrong and how to prevent it

---

## Migration History

| Date | Migration | Description | Status |
|------|-----------|-------------|--------|
| 2026-01-25 | initial_schema | Created roles, users, auth_providers, auth_credentials tables | Applied |

---

## Best Practices

1. **Always test migrations on development first**
2. **Keep migrations small and focused** - One logical change per migration
3. **Never modify existing migrations** - Once applied, create a new migration
4. **Always include rollback instructions** - Even if rollback is destructive
5. **Document breaking changes** - Note any data loss or incompatibilities
6. **Coordinate with deployments** - Deploy code and migrations together

---

## Future Considerations

If the project grows and migrations become more complex, consider:

- **Alembic integration** - Automated migration management
- **Migration versioning table** - Track which migrations have been applied
- **Automated testing** - CI/CD pipeline tests for migrations
- **Blue-green deployments** - Zero-downtime schema changes
