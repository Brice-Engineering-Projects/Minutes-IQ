# Phase 7.11 — E2E Testing Clarifications (Authoritative Decisions)

This document answers the clarification questions for **Phase 7.11: End-to-End (E2E) Testing**.  
These decisions are **authoritative** and should be followed exactly when implementing the test suite.

---

## 1. Testing Framework

**Decision:** ✅ **Playwright**

**Rationale:**
- First-class multi-browser support (Chromium, Firefox, WebKit)
- Faster and more deterministic than Cypress
- Excellent support for modern auth flows and file downloads
- Works well with server-rendered apps (Jinja2 + htmx)
- Clean separation from frontend tooling (no SPA assumptions)

**Language:** TypeScript  
**Location:** `tests/e2e/`

---

## 2. Test Coverage Expectations

**Decision:**  
- The checklist numbers (5+, 8+, etc.) are **minimums**, not ceilings.
- Meet the minimums first.
- Add coverage where it provides **meaningful regression protection**, not vanity tests.

**Priority Order:**
1. Authentication & access control
2. Scrape job lifecycle (highest business risk)
3. Client & keyword management
4. Admin panel
5. Mobile responsiveness

---

## 3. Test Data Strategy

**Decision:** ✅ **Dedicated E2E Test Database**

**Rules:**
- Use a **separate database** (e.g. `minutes_iq_test`)
- Never run E2E tests against dev or prod data
- Tests must be **self-contained and repeatable**

**Data Handling:**
- Seed baseline data once at test startup:
  - Admin user
  - Regular user
  - Sample auth code
  - Minimal clients / keywords
- Create and clean up additional data **within each test**
- No reliance on existing integration test fixtures

**Goal:** Tests must pass when run:
- Locally
- In CI
- On a clean machine

---

## 4. CI Integration

**Decision:**  
- ❌ Do **not** run E2E tests on every PR
- ✅ Run E2E tests on:
  - Merge to `dev`
  - Merge to `main`
- ✅ Allow **manual triggering** (CI workflow dispatch)

**Rationale:**
- E2E tests are slower and more brittle
- Unit + integration tests protect PRs
- E2E tests protect release branches

---

## 5. Browser Coverage

**Initial Phase (Required):**
- ✅ Chromium only

**Expansion Phase (Planned):**
- Firefox
- WebKit (Safari equivalent)

**Rule:**  
Design tests to be **browser-agnostic**, even if initially executed on Chromium only.

---

## Additional Constraints

- No new frontend tooling decisions
- No DOM selectors tied to styling
- Prefer `data-testid` attributes where needed
- Avoid brittle timing-based waits
- Prefer Playwright’s auto-waiting and assertions
- Auth must be tested as a real user (no token injection)

---

## Expected Outcomes

At completion of Phase 7.11:
- Critical user journeys are covered end-to-end
- Auth gating regressions are caught automatically
- Scrape job lifecycle is protected against breakage
- Admin-only paths are verified
- Mobile navigation is validated
- Tests are stable, repeatable, and CI-ready

---

**This closes all open questions for Phase 7.11.  
Proceed with Playwright setup and implementation using these decisions.**
