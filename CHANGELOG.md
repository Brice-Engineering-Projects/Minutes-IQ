# Changelog

All notable changes to MinutesIQ will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Multi-URL Client Architecture**: Clients can now have multiple URLs for scraping
  - Each URL has a descriptive alias (e.g., "current", "archive")
  - URLs can be individually activated/deactivated
  - Last scraped timestamp tracked per URL
  - Dynamic URL management UI in client forms (add/edit/delete)
  - Client detail page displays all URLs with metadata
- New `client_urls` table with full URL metadata
- New `ClientUrlRepository` for URL management
- Comprehensive test suite for URL management (16 tests)
- API documentation for `ClientUrl` model

### Changed
- **BREAKING**: Removed `website_url` field from `client` table
- **BREAKING**: `scrape_jobs` now references `client_url_id` instead of `client_id`
- Client API responses now include `urls` array with `ClientUrl` objects
- Updated all client endpoints to populate URL data
- Improved form UI with dynamic URL row management
- Updated test database schema to match production

### Deprecated
- `website_url` parameter in client creation/update (use URL management instead)

### Removed
- `website_url` field from client creation/update API requests
- `website_url` parameter from `ClientRepository` methods
- `client_sources` table (replaced by `client_urls`)

### Fixed
- Type checking errors in form data handling
- Favorites endpoint now works correctly
- Client edit button visibility for admins
- All integration tests updated and passing

### Technical Details
- Database Migration: `20260212_120000_refactor_client_urls.sql`
- Phase 3 (Multi-URL Architecture) completed across:
  - Phase 3A: Critical admin fixes
  - Phase 3B: User-facing API updates
  - Phase 3C: Test updates (30+ tests)
  - Phase 3D: UI updates
  - Phase 3E: Documentation and cleanup

## [0.1.0] - Previous Release

### Added
- Initial FastAPI application with Jinja2 templates
- User authentication system with auth codes
- Client and keyword management
- Favorites functionality
- Basic scraper integration
- Admin and user role separation
