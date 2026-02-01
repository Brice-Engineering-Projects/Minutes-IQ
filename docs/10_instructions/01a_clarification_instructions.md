# UI Architecture Clarifications and Instructions

## Context

The UI stack uses FastAPI with Jinja2 templates and htmx for interactivity. Tailwind CSS is used for styling. The system is backend-first and must remain architecturally clean and reversible.

These instructions clarify how to handle custom styles, JavaScript, htmx, and when to enforce the frontend build architecture.

---

## 1. Custom Styles (Spinners, Toasts, Cards, etc.)

### Current State

Custom styles currently exist as handwritten CSS (loading spinners, toast notifications, card helpers).

### Approved Short-Term Approach

* Custom styles may temporarily live in static CSS for rapid UI iteration.
* This is acceptable during early UI development.

### Required Medium-Term Direction

* All reusable custom styles must eventually be migrated into Tailwind using:

  * Tailwind layers (`@layer components` or `@layer utilities`)
  * Defined in the Tailwind source file (`frontend/src/input.css`)
* These styles are design primitives and must not grow indefinitely as ad-hoc CSS.

### Explicit Non-Goals

* Do not keep expanding standalone CSS files long-term.
* Do not inline complex animations or reusable patterns directly in templates.
* Do not force all styles into raw utility class soup when components are clearer.

---

## 2. JavaScript Usage and Placement

### Scope of JavaScript

JavaScript is intentionally minimal and limited to:

* Toast notifications
* Global error handling
* htmx lifecycle hooks
* Loading indicators and UX helpers

JavaScript must remain behavioral and must not compete with htmx for DOM control.

### File Location

JavaScript should remain in:

src/minutes_iq/static/js/

The current `main.js` file is acceptable and correctly scoped.

### Explicit Non-Goals

* Do not introduce a JS framework.
* Do not move JS into a frontend build pipeline unless a real frontend app exists.
* Do not allow JavaScript to manage application state owned by the server.

---

## 3. htmx Dependency Handling

### Current Decision

* htmx may be loaded via CDN during UI development.

### Rationale

* Fast iteration
* No deployment target yet
* No security or determinism requirements enforced at this phase

### Future Decision Point

* During deployment hardening, htmx may either:

  * Remain CDN-based with integrity hashes, or
  * Be vendored into `static/js/`

This decision is deferred to the deployment phase.

---

## 4. Tailwind and Frontend Architecture Enforcement

### Immediate Requirement

The frontend build architecture must be aligned now to prevent future entropy.

### Enforced Structure

* All Tailwind and Node tooling must live in a root-level `frontend/` directory.
* The Python application must remain unaware of build tooling.
* `static/` is output-only.
* `templates/` are input-only.

### Migration Strategy

* Do not immediately refactor working UI code.
* Add the `frontend/` directory and document the contract.
* Migrate custom styles into Tailwind layers when the build step is activated.

---

## Summary Directives

* Custom CSS is acceptable short-term but must be migrated into Tailwind layers.
* JavaScript should remain minimal and stay in `static/js/`.
* htmx may stay CDN-based for now.
* Frontend build tooling must be isolated at the project root.
* No frontend build logic belongs under `src/`.

Any deviation from these rules is considered an architectural defect.
