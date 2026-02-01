# Scrape Job Management UI – Authoritative Decisions

This document defines the **final, authoritative decisions** for implementing the Scrape Job Management UI (Checklist 7.6). These decisions are **intentional**, align with the existing backend architecture, and remove ambiguity for implementation.

These are not placeholders.
These are not provisional.
These decisions are locked unless explicitly changed later.

---

## 1. Date Range Picker

**Decision:**
Use **native HTML5 date inputs**.

**Rationale:**

* Zero new frontend tooling
* Fully compatible with FastAPI + Jinja + htmx
* Accessible by default
* Easy to replace later without breaking contracts

**Implementation Example:**

```html
<input type="date" name="start_date">
<input type="date" name="end_date">
```

No JavaScript date libraries.
No Flatpickr.
No custom widgets.

---

## 2. Job Status Auto-Refresh / Polling

**Decision:**
Use **htmx polling**.

**Implementation Rules:**

* Poll every 5 seconds
* Use a lightweight status endpoint
* Stop polling when job reaches a terminal state

**Example:**

```html
<div hx-get="/api/scraper/jobs/{{ job_id }}/status"
     hx-trigger="every 5s"
     hx-swap="outerHTML">
</div>
```

**Notifications:**

* ❌ No browser notifications
* ✅ In-page feedback only

  * Status badge updates
  * Toast message on completion or failure

This avoids permission prompts and keeps UX deterministic.

---

## 3. CSV Export vs ZIP Artifact Generation

### CSV Export

**Decision:**
Synchronous download.

**Behavior:**

* Direct file response
* Immediate browser download
* No background job

---

### ZIP Artifact Generation

**Decision:**
Asynchronous generation.

**Behavior:**

* Trigger backend artifact creation
* Show "Generating…" UI state
* Poll until ready
* Provide download link when complete

This matches the existing backend orchestration model exactly.

---

## 4. Progress Tracking Granularity

**Decision:**
UI must be **defensive and data-driven**.

**Rules:**

* Display progress fields **only if backend data exists**
* Hide fields when data is unavailable
* Never display simulated or placeholder values

**Fields:**

* Pages scanned – show if available
* Matches found – show if available
* Current PDF – show only if backend provides it

If data does not exist yet, render explicit empty states.

---

## 5. Results Table Pagination

**Decision:**
Server-side pagination via **htmx**.

**Rules:**

* 20 results per page
* Same pattern as Clients and Keywords
* Reuse existing pagination components

No client-side pagination logic.

---

## 6. Job Filtering (Status / Client)

**Decision:**
Use **htmx-powered filters**.

**Behavior:**

* Dropdown filters for status and client
* Filter changes update table only
* No full page reloads
* Query params reflect current filters

This keeps UI behavior consistent across the application.

---

## Final Instruction to Implementer

Proceed with implementation using the decisions above.

* Do **not** introduce new frontend tooling
* Do **not** simulate data
* Use htmx for polling, filtering, and pagination
* Follow established UI patterns from Clients and Keywords
* If backend data does not exist, render explicit empty states with CTAs

---

## Why These Decisions Matter

* Prevents future UI rewrites
* Keeps backend as the single source of truth
* Avoids fragile frontend state
* Allows immediate production deployment
* Preserves clean architectural boundaries

This document exists to remove ambiguity.
Implement accordingly.
