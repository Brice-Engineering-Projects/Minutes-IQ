# E2E Test Suite - Minutes IQ Platform

This directory contains End-to-End (E2E) tests for the Minutes IQ platform using Playwright.

## Overview

**Framework:** Playwright (TypeScript)
**Browser Coverage:** Chromium (Desktop & Mobile)
**Test Database:** Dedicated E2E test database (`test_e2e.db`)

## Test Coverage

### Authentication Flow Tests (8 tests)
- ✅ Login with valid credentials
- ✅ Login with invalid credentials
- ✅ Registration with valid auth code
- ✅ Registration with invalid auth code
- ✅ Password reset flow
- ✅ Logout functionality
- ✅ Auth gating on protected routes
- ✅ Remember me functionality

### Client Management Tests (7 tests)
- ✅ View client list
- ✅ View client details
- ✅ Add/remove favorites
- ✅ Create new client (admin)
- ✅ Edit client (admin)
- ✅ Restrict creation to admin only
- ✅ Search and filter clients

### Scrape Job Tests (10 tests)
- ✅ Create new scrape job
- ✅ View job list with filtering
- ✅ View job details
- ✅ Poll job status in real-time
- ✅ Download CSV export
- ✅ Generate ZIP artifact
- ✅ Download ZIP artifact
- ✅ Cancel pending/running job
- ✅ Validation errors for invalid config
- ✅ Paginate results

### Admin Panel Tests (8 tests)
- ✅ Access admin dashboard (admin only)
- ✅ Restrict admin access by role
- ✅ View user list
- ✅ Generate authorization code
- ✅ View and revoke auth codes
- ✅ Storage cleanup information
- ✅ Admin-only navigation items
- ✅ Update user role

### Mobile Responsiveness Tests (5 tests)
- ✅ Mobile navigation with hamburger menu
- ✅ Forms properly sized on mobile
- ✅ Tables with horizontal scroll or cards
- ✅ Readable text and proper spacing
- ✅ Modals and dialogs on mobile

**Total: 38 E2E tests**

## Setup

### Prerequisites

1. **Node.js** (v20+) - For Playwright
2. **Python** (3.12+) - For application server
3. **Application dependencies** installed

### Installation

```bash
# Install Node dependencies
npm install

# Install Playwright browsers
npx playwright install chromium
```

## Running Tests

### Local Testing

```bash
# Run all tests
npm test

# Run tests with UI mode (interactive)
npm run test:ui

# Run tests in headed mode (see browser)
npm run test:headed

# Debug a specific test
npm run test:debug

# View last test report
npm run test:report
```

### Specific Test Suites

```bash
# Run only authentication tests
npx playwright test auth.spec.ts

# Run only admin tests
npx playwright test admin.spec.ts

# Run only mobile tests (uses mobile viewport)
npx playwright test mobile.spec.ts --project=mobile-chromium
```

### Before Running Tests

**Important:** The application server must be running before executing E2E tests.

```bash
# Terminal 1: Start the application
source .venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Run E2E tests
npm test
```

Alternatively, uncomment the `webServer` section in `playwright.config.ts` to have Playwright automatically start the server.

## Test Database

Per Phase 7.11 instructions, E2E tests use a **dedicated test database** (`test_e2e.db`).

### Baseline Test Data

The following baseline data is seeded once at test startup:

- **Admin User:** `admin@test.local` / `Admin123!`
- **Regular User:** `user@test.local` / `User123!`
- **Auth Code:** `E2E-TEST-CODE-2026`
- **Sample Client:** Test Agency
- **Sample Keywords:** infrastructure, budget, sustainability

### Data Cleanup

Tests are designed to be self-contained and repeatable. Each test:
- Uses baseline data where possible
- Creates additional data with unique identifiers
- Cleans up created data after completion

To reset the test database:

```bash
rm test_e2e.db
python -m src.db.migrate
python tests/e2e/setup/seed_data.py
```

## CI Integration

Per Phase 7.11 instructions, E2E tests run:

- ✅ On merge to `dev` branch
- ✅ On merge to `main` branch
- ✅ Manual trigger via GitHub Actions workflow dispatch
- ❌ NOT on every PR (too slow)

See `.github/workflows/e2e-tests.yml` for CI configuration.

## Writing New Tests

### Guidelines

1. **Use helpers:** Import auth and cleanup helpers from `./helpers/`
2. **Use data-testid:** Prefer `data-testid` attributes over brittle CSS selectors
3. **Auto-waiting:** Use Playwright's built-in auto-waiting (avoid `waitForTimeout` except for polling)
4. **Clean up:** Delete test data created during the test
5. **Browser-agnostic:** Design tests to work on any browser (even though we start with Chromium)

### Example Test

```typescript
import { test, expect } from '@playwright/test';
import { loginAsUser } from './helpers/auth';
import { generateTestId } from './helpers/cleanup';

test('should do something', async ({ page }) => {
  await loginAsUser(page);

  const testId = generateTestId();
  const testData = `test-${testId}`;

  // Create test data
  await page.goto('/some-page');
  await page.fill('input[name="field"]', testData);
  await page.click('button[type="submit"]');

  // Assert
  await expect(page.locator(`text=${testData}`)).toBeVisible();

  // Cleanup (if needed)
  await page.click(`button[data-testid="delete-${testData}"]`);
});
```

## Troubleshooting

### Tests Failing Locally

1. **Server not running:** Ensure `uvicorn` is running on port 8000
2. **Database not seeded:** Run `python tests/e2e/setup/seed_data.py`
3. **Port conflict:** Change port in `playwright.config.ts` and restart server
4. **Stale browser:** Run `npx playwright install --force chromium`

### Timeouts

If tests timeout frequently:
- Increase timeouts in `playwright.config.ts`
- Check server logs for errors
- Run tests in headed mode to see what's happening

### Flaky Tests

If tests are flaky:
- Avoid `waitForTimeout()` - use `waitForSelector()` instead
- Use `toBeVisible()` instead of checking for existence
- Ensure unique test data with `generateTestId()`

## References

- [Playwright Documentation](https://playwright.dev/)
- [Phase 7.11 Instructions](../../docs/10_instructions/07_e2e_testing_instructions.md)
- [High-Level Roadmap](../../docs/01_overview/07_high_level_roadmap.md)
