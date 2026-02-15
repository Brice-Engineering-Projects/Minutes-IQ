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

### Changed
- Basic scraper integration
- Admin and user role separation



### `CHANGELOG.md`
**Why important**: Project change history
**Changes**: Created new file documenting Phase 3 implementation
```markdown
## [Unreleased]

### Added
- **Multi-URL Client Architecture**: Clients can now have multiple URLs for scraping
  - Each URL has a descriptive alias (e.g., "current", "archive")
  - URLs can be individually activated/deactivated
  - Last scraped timestamp tracked per URL

### Changed
- **BREAKING**: Removed `website_url` field from `client` table
- **BREAKING**: `scrape_jobs` now references `client_url_id` instead of `client_id`
```

### `src/minutes_iq/api/scraper_jobs_ui.py`
**Why important**: Scraper job creation endpoint
**Changes**: Updated to use client_url_id instead of client_id
```python
class JobCreate(BaseModel):
    """Schema for creating a scrape job."""
    client_url_id: int  # Changed from client_id
    start_date: str
    end_date: str
    max_scan_pages: int = 15
    include_board_minutes: bool = True
    include_packages: bool = False

@router.post("", response_class=HTMLResponse)
async def create_job(job_data: JobCreate, scraper_repo: Annotated[ScraperRepository, Depends(get_scraper_repository)]):
    job_id = scraper_repo.create_job(
        client_url_id=job_data.client_url_id,  # Changed from client_id
        created_by=created_by,
        status="pending",
    )
```

### `src/minutes_iq/db/scraper_repository.py`
**Why important**: Database operations for scraper jobs
**Changes**: Updated create_job method signature
```python
def create_job(
    self,
    client_url_id: int,  # Changed from client_id
    created_by: int,
    status: str = "pending",
) -> int:
    """Create a new scrape job."""
    cursor = self.conn.execute(
        """
        INSERT INTO scrape_jobs (client_url_id, status, created_by, created_at)
        VALUES (?, ?, ?, ?)
        RETURNING job_id
        """,
        (client_url_id, status, created_by, int(datetime.now().timestamp())),
    )
```

### `src/minutes_iq/templates/scraper/job_create.html`
**Why important**: Scraper job creation form
**Changes**: Updated to show client URL dropdown instead of client dropdown
```html
<label for="client_url_id">Client URL <span class="text-red-500">*</span></label>
<select id="client_url_id" name="client_url_id" required>
    <option value="">Select a client URL...</option>
    <optgroup label="Favorites">
        <!-- Favorite client URLs loaded via script -->
    </optgroup>
    <optgroup label="All Client URLs">
        <!-- All client URLs loaded via script -->
    </optgroup>
</select>

<script>
Promise.all([
    fetch('/api/clients/all-urls').then(r => r.json()),
    fetch('/api/clients/favorites').then(r => r.json()).catch(() => [])
])
.then(([allClientUrls, favorites]) => {
    const favoriteClientIds = new Set(favorites.map(f => f.client_id));
    const favoriteUrls = allClientUrls.filter(url => favoriteClientIds.has(url.client_id));
    const otherUrls = allClientUrls.filter(url => !favoriteClientIds.has(url.client_id));
    
    favoriteUrls.forEach(clientUrl => {
        const option = document.createElement('option');
        option.value = clientUrl.client_url_id;
        option.textContent = clientUrl.display_name; // "ClientName - alias"
        option.title = clientUrl.url;
        favoritesOptgroup.appendChild(option);
    });
    // ... similar for otherUrls
});
</script>
```

## 4. Errors and Fixes

### Error 1: 7 Failing URL Management Tests
**Description**: Tests failed due to incorrect method signatures and return types
**Fix Applied**:
- `list_all_urls()` returns tuple `(list, total)` - unpacked with `all_urls, total = url_repo.list_all_urls()`
- `update_url()` returns `bool` not updated object - added `url_repo.get_url()` calls after updates to verify
- `update_last_scraped()` only takes url_id (auto-generates timestamp) - removed manual timestamp parameter
- Missing `test_user` fixture in cascade delete test - added fixture to function signature
- `update_nonexistent_url` expected False not None - changed assertion
**User Feedback**: "If it is an easy fix, can you fix them?" - User confirmed they wanted the fixes

### Error 2: Linting Error - Unused Variable
**Description**: `E402 Local variable 'url' is assigned to but never used` in cascade delete test
**Fix Applied**: Removed the variable assignment, just called `create_url()` without storing result
**User Feedback**: User provided linting error output directly

### Error 3: Mypy Type Checking Errors
**Description**: Multiple type errors in `client_url_repository.py` and `clients_ui.py`
- `params` list inferred as `list[str]` but needed `list[str | int]`
- Form data `getlist()` returns `UploadFile | str` but methods expect `str`
**Fix Applied**:
- Added explicit type hints: `params: list[str | int] = []`
- Added `str()` conversions: `alias=str(alias), url=str(url_value)`
**User Feedback**: User provided mypy error output showing exact line numbers

### Error 4: 422 Unprocessable Entity on Scraper Job Creation
**Description**: POST /api/scraper/jobs returned 422 error
**Root Cause**: 
1. First fix: `JobCreate` model and `create_job()` method still used `client_id` instead of `client_url_id`
2. Second occurrence: Form HTML still sending `client_id` field name
**Fix Applied**:
1. Updated `JobCreate` model to use `client_url_id`
2. Updated `ScraperRepository.create_job()` method signature
3. Updated form field name from `client_id` to `client_url_id`
4. Created `/api/clients/all-urls` endpoint to provide client URLs for dropdown
5. Updated JavaScript to populate dropdown with client URLs showing "ClientName - alias" format
**User Feedback**: User provided server log showing "INFO: 127.0.0.1:41468 - 'POST /api/scraper/jobs HTTP/1.1' 422 Unprocessable Entity" - same error occurred twice, indicating form also needed updating

## 5. Problem Solving

### Problem 1: Multi-URL Form Management
**Challenge**: Replace single website_url input with dynamic multi-URL management
**Solution**: 
- Created repeatable URL row template with alias, URL, active checkbox
- Implemented JavaScript functions `addUrlRow()` and `removeUrlRow()`
- Used array inputs `url_alias[]`, `url_value[]`, `url_is_active[]`, `url_id[]`
- Backend parses arrays and creates/updates/deletes URLs accordingly
**Status**: ✅ Complete

### Problem 2: Test Database Schema Mismatch
**Challenge**: Production uses `client` (singular) but tests used `clients` (plural)
**Solution**: Updated test schema to match production exactly
**User Feedback**: "Do not change the code, change the test. the db has many tables and changing one table name in the code will break many things"
**Status**: ✅ Complete

### Problem 3: Scraper Job Integration with Multi-URL
**Challenge**: Scraper jobs need to reference specific client URL, not just client
**Solution**:
- Changed `scrape_jobs.client_id` to `scrape_jobs.client_url_id` in schema
- Updated all scraper-related code to use `client_url_id`
- Created endpoint to list all client URLs for dropdown
- Updated form to show "ClientName - alias" format in dropdown
**Status**: ✅ Complete (most recent work)

## 6. All User Messages

1. "Please continue the conversation from where we left it off without asking the user any further questions. Continue with the last task that you were asked to work on."

2. "The ui is still only showing one website to add in the form"

3. "If it is an easy fix, can you fix them?" (referring to 7 failing URL tests)

4. Linting error: "tests/integration_tests/clients/test_client_url_management.py:283:9: F841 Local variable `url` is assigned to but never used"

5. Mypy errors: "src/minutes_iq/db/client_url_repository.py:194: error: Argument 1 to 'append' of 'list' has incompatible type 'int'; expected 'str'" [and 10 more errors]

6. "Some of this may have been addressed, please address items that still need to be addressed" + Phase 3D checklist attachment

7. "please provide a gc message"

8. "Let's work on phase 3E" + Phase 3E checklist attachment

9. "INFO: 127.0.0.1:41064 - 'POST /api/scraper/jobs HTTP/1.1' 422 Unprocessable Entity"

10. "Do not change the code, change the test. the db has many tables and changing one table name in the code will break many things"

11. "INFO: 127.0.0.1:41468 - 'POST /api/scraper/jobs HTTP/1.1' 422 Unprocessable Entity" (same error after first fix)

12. "Your task is to create a detailed summary..." (current request)

## 7. Pending Tasks

- None explicitly stated. Phase 3 (Multi-URL Architecture) is complete including all sub-phases (3A-3E).

## 8. Current Work

Immediately before this summary request, I was fixing the scraper job creation 422 error for the second time. The error persisted after fixing the backend because the frontend form was still using `client_id`.

**Work completed in the most recent exchange:**

1. **Updated `/api/clients/all-urls` endpoint** in `src/minutes_iq/api/clients_ui.py`:
   - Returns list of all active client URLs with display names
   - Format: `{"client_url_id": 1, "client_name": "JEA", "alias": "current", "display_name": "JEA - current"}`

2. **Updated `templates/scraper/job_create.html`**:
   - Changed form field from `<select id="client_id" name="client_id">` to `<select id="client_url_id" name="client_url_id">`
   - Updated JavaScript to fetch `/api/clients/all-urls` instead of `/api/clients/all`
   - Modified dropdown population to show client URLs with format "ClientName - alias"
   - URLs from favorited clients appear in Favorites optgroup

3. **Previously updated** (in response to first 422 error):
   - `JobCreate` Pydantic model: `client_id: int` → `client_url_id: int`
   - `create_job()` API endpoint: passes `client_url_id` to repository
   - `ScraperRepository.create_job()`: method signature updated to accept `client_url_id`

**Status**: The 422 error should now be resolved. The form now submits `client_url_id` which matches what the backend expects.

## 9. Optional Next Step

**Next Step**: Test the scraper job creation form to verify the 422 error is resolved and that the dropdown correctly displays client URLs in the format "ClientName - alias".

**Supporting Quote**: 
From the user: "INFO: 127.0.0.1:41468 - 'POST /api/scraper/jobs HTTP/1.1' 422 Unprocessable Entity"

This was the task being worked on - fixing the scraper job creation error. The fix has been completed by:
1. Updating the form field name to `client_url_id`
2. Creating the `/api/clients/all-urls` endpoint
3. Updating the JavaScript to populate the dropdown with client URLs

The next logical step would be to verify this fix works, but since the user has requested a summary, no further action should be taken without explicit user confirmation..
Please continue the conversation from where we left it off without asking the user any further questions. Continue with the last task that you were asked to work on.I'll test the scraper job creation to verify the 422 error is resolved.<llm-progress-log-group>
