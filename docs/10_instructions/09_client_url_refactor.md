# Minutes IQ – Client URL Refactor Execution Plan

## 📌 Context

The schema has been refactored to remove `clients.website_url` and introduce a proper 1-to-many relationship:

- `clients`
- `client_urls`

Core structural changes have been completed.

Now the remaining work must be executed in the correct order to avoid instability.

---

# 🎯 Refactor Execution Strategy

The work must be completed in the following order:

## Phase 1 – Stabilize Critical API Endpoints (PRIORITY)

Goal: Get the application running without 500 errors.

Focus only on endpoints and repositories that directly impact application startup and core functionality.

### Update the Following:

- `clients.py`
- `clients_ui.py`
- `admin/client_routes.py`
- `favorites_repository.py` (if blocking UI load)

### Required Changes:

- Remove all references to `website_url`
- Replace logic to use `client_urls`
- Update queries to join on `client_urls`
- Ensure API responses return URLs as a list per client
- Update scrape job creation to use `client_url_id`

### Success Criteria:

- App boots successfully
- Client list endpoint works
- Client detail endpoint works
- Scrape job creation works
- No runtime errors referencing `website_url`

Do not refactor templates or non-critical features during this phase.

---

## Phase 2 – Create a Refactor Audit Checklist

Goal: Prevent hidden regressions.

After the app runs successfully:

Create a structured audit document that includes:

- All files previously referencing `website_url`
- All Pydantic models that included `website_url`
- All SQL queries that referenced `website_url`
- All templates expecting `client.website_url`
- Any test cases asserting `website_url`

This checklist ensures no residual schema dependencies remain.

---

## Phase 3 – Complete Remaining Refactor

Once the system is stable and the audit checklist is complete:

Proceed with:

- Updating HTML templates to support multiple URLs
- Updating client creation/edit forms to manage multiple URLs
- Updating detail views to display URL aliases
- Updating tests to reflect new schema
- Cleaning up any deprecated logic

---

# 🧠 Why This Order Matters

Do NOT:

- Refactor everything at once
- Update UI before endpoints are stable
- Write documentation before verifying runtime behavior

Correct order:

1. Stabilize runtime
2. Audit remaining references
3. Complete refactor

This prevents:
- Runtime instability
- Hidden broken queries
- Regression bugs
- UI inconsistencies

---

# 🚀 Design Outcome

After completion:

- Clients support multiple URLs
- Scrape jobs track specific `client_url_id`
- System supports future URL-level scheduling
- Schema is normalized and scalable
- No legacy `website_url` field remains

Minutes IQ transitions from a flat CRUD model to a properly normalized intelligence platform.
