# Results & Downloads UI – Authoritative Clarifications (Section 7.7)

This document defines the **final, authoritative decisions** for implementing the Results & Downloads UI.

These decisions remove ambiguity, prevent UI duplication, and ensure the system remains safe for immediate production use.

Unless explicitly changed later, these decisions are **locked**.

---

## 1. Results List Page vs Job Detail Results

**Decision:**
❌ Do **not** create a separate standalone page at `/scraper/jobs/{id}/results`.

✅ **Enhance the existing results section on the Job Detail page** (`/scraper/jobs/{id}`).

**Rationale:**

* Results are intrinsically tied to a single job
* Avoids duplicating pagination, filters, exports, and permissions
* Keeps the user workflow linear: Job → Results → Downloads
* Reduces routing and template complexity

**Instruction:**
All checklist items for the “Results List Page” are implemented **inside the Job Detail page** as a dedicated results section.

---

## 2. Snippet Highlighting

**Decision:**
Use **server-side highlighting** with semantic HTML.

**Implementation Rules:**

* Wrap matched keywords using `<mark>` tags
* Perform highlighting when constructing the HTML response
* Do **not** use client-side JavaScript regex replacement

**Example:**

```html
… discussion included <mark>force main</mark> replacement near …
```

**Rationale:**

* Accessible and semantic
* Easy to style with Tailwind
* Deterministic and testable
* No client-side complexity

---

## 3. “View PDF” Button

**Decision:**
Create a **new backend endpoint** to securely serve PDFs.

**Endpoint Pattern:**

```
GET /api/scraper/jobs/{job_id}/pdfs/{filename}
```

**Behavior:**

* Opens PDF in a new browser tab
* Validates that the current user owns the job
* Verifies the file exists on disk
* Uses `FileResponse`
* No public/static exposure of PDFs

**Rationale:**

* PDFs are stored on disk, not static assets
* Must respect authentication and job ownership
* Keeps the storage model explicit and secure

---

## 4. Download History

**Decision:**
Display **download / artifact history on the Job Detail page only**.

**Placement:**

* Sidebar or secondary card on the job detail page

**Rules:**

* Show **only real artifact records**
* If no history exists, render an explicit empty state
* ❌ Do not simulate history
* ❌ Do not introduce new persistence in this phase

---

## 5. Entities in CSV Export

**Decision:**
Include the `entities` column **only if real data exists**.

**Rules:**

* Export whatever is stored in `scrape_results.entities_json`
* If entities are empty or null:

  * Export an empty string
  * Do not fabricate placeholders
* Do not add new extraction logic in this phase

**Rationale:**

* CSV schema remains forward-compatible
* Backend remains the single source of truth
* No fake data

---

## 6. Results Table Sorting

**Decision:**
Sorting is **server-side only**, powered by htmx.

**Sortable Columns:**

* PDF filename
* Page number
* Keyword

**Implementation Rules:**

* Sorting triggers table reload via htmx
* Sorting parameters passed as query params
* No client-side JavaScript sorting

**Rationale:**

* Consistent with pagination and filtering
* Scales to large result sets
* Keeps UI thin and predictable

---

## 7. ZIP Artifact Generation Status

**Decision:**
ZIP generation remains **asynchronous** and **defensive**.

**UI Rules:**

* Show “Generate ZIP” if no artifact exists
* Show “Generating…” while in progress
* Show “Download ZIP” only when backend confirms readiness
* Display file size and expiration only if known

No speculative polling loops beyond existing job-status polling.

---

## Final Instruction to Implementer

Proceed with implementation using these decisions:

* Enhance **Job Detail page only**
* No new frontend tooling
* No simulated or placeholder data
* Server-side rendering + htmx only
* Defensive UI: render data **only if it exists**
* Explicit empty states with actionable CTAs

If backend data does not exist yet, render an empty state rather than guessing.

---

## Why These Decisions Matter

These choices:

* Prevent duplicate UI paths
* Preserve authentication and storage boundaries
* Keep the system safe for immediate deployment
* Ensure future backend features drop in cleanly

This document exists to eliminate ambiguity.
Implement accordingly.
