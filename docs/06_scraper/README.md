# Scraper Documentation

This directory contains comprehensive documentation for the Minutes IQ Scraper Orchestration System.

## Overview

The scraper system converts the CLI-based PDF scraper into a production-ready, database-backed service with async job execution, API endpoints, and comprehensive monitoring.

## Documentation Index

### 1. [API Reference](./01_api_reference.md)
Complete REST API documentation including:
- All scraper endpoints (11 endpoints)
- Request/response examples
- Authentication requirements
- Error codes
- Job status lifecycle
- Best practices

**Use this when:** Building clients, integrating with the API, or understanding endpoint behavior.

### 2. [Data Model](./02_data_model.md)
Database schema documentation including:
- Table definitions and relationships
- Constraints and indexes
- Status enums and transitions
- Entity relationship diagrams
- Migration scripts
- Performance considerations

**Use this when:** Understanding the database structure, writing queries, or planning schema changes.

### 3. [Operational Guide](./03_operational_guide.md)
Administrator and operations guide including:
- Job management workflows
- Monitoring strategies
- Troubleshooting failed jobs
- Performance tuning
- Storage and cleanup policies
- Common issues and solutions

**Use this when:** Operating the system, troubleshooting issues, or optimizing performance.

## Quick Start

### For Developers

1. Read the [API Reference](./01_api_reference.md) to understand available endpoints
2. Review the [Data Model](./02_data_model.md) to understand data structures
3. See the [test files](../../tests/integration_tests/scraper/) for usage examples

### For Administrators

1. Read the [Operational Guide](./03_operational_guide.md)
2. Set up monitoring using the provided queries
3. Configure cleanup policies for your environment

### For Users

1. Obtain an authentication token via `/auth/login`
2. Create a scrape job via `POST /scraper/jobs`
3. Poll job status via `GET /scraper/jobs/{job_id}/status`
4. Download results via `GET /scraper/jobs/{job_id}/results/export`

## Architecture Overview

```
┌─────────────┐
│   FastAPI   │ ← API Endpoints
│   Routes    │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  Service    │ ← Business Logic
│   Layer     │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ Repository  │ ← Data Access
│   Layer     │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  Database   │ ← SQLite/Turso
│   Tables    │
└─────────────┘
```

## Key Features

✅ **Async Background Execution** - Jobs run asynchronously using FastAPI BackgroundTasks
✅ **Job Cancellation** - Cancel pending or running jobs
✅ **Timeout Protection** - 30-minute timeout prevents runaway jobs
✅ **Progress Tracking** - Real-time status updates
✅ **Result Pagination** - Handle large result sets efficiently
✅ **CSV Export** - Download results in CSV format
✅ **NLP Integration** - Named entity extraction with spaCy
✅ **Comprehensive Testing** - 68+ tests covering unit, integration, and performance

## System Requirements

- **Python:** 3.11+
- **Database:** SQLite 3.35+ or Turso
- **Memory:** 2GB minimum, 4GB recommended
- **Disk Space:** 10GB+ for PDF storage
- **CPU:** 2+ cores for concurrent job execution

## Configuration

Key configuration files:
- `src/minutes_iq/scraper/async_runner.py` - Timeout settings
- `src/minutes_iq/scraper/routes.py` - API endpoints
- `src/minutes_iq/db/schema/005_add_scraper_orchestration.sql` - Database schema

## Support

- **Issues:** https://github.com/your-org/minutes-iq/issues
- **Documentation:** This directory
- **Tests:** `tests/integration_tests/scraper/` and `tests/unit_tests/scraper/`

## Related Documentation

- [Authentication](../04_security/) - User authentication and authorization
- [Client Management](../05_clients/) - Managing clients and keywords
- [Database](../03_db/) - Database setup and migrations

## Version History

- **v1.0** (2026-01) - Initial release of scraper orchestration system
  - Background job execution
  - REST API endpoints
  - Database-backed storage
  - Comprehensive testing

## Contributing

When updating scraper documentation:

1. Keep all three documents in sync
2. Update examples when API changes
3. Add troubleshooting entries for new issues
4. Update the data model for schema changes
5. Test all code examples before committing

## License

Copyright © 2026 Minutes IQ. All rights reserved.
