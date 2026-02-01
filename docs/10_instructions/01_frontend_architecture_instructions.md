# Frontend Architecture Instructions (DO NOT DEVIATE)

## Purpose

The frontend stack uses Tailwind CSS with a build step. Tailwind is treated as a compiler, not a static CSS file.

## Hard Rules

### 1. Frontend Build Tooling Location

* All Node / Tailwind tooling MUST live at the project root in a directory named:

  frontend/

* This directory owns:

  * package.json
  * tailwind.config.js
  * postcss.config.js
  * Tailwind source CSS (input.css)

* NO Node tooling, configs, or source CSS may exist under src/

---

### 2. Python Application Layout (Read-Only for Frontend)

The following directories are NOT to be modified or repurposed by frontend tooling:

* src/minutes_iq/
* src/minutes_iq/templates/
* src/minutes_iq/static/

These directories serve fixed roles:

* templates/ → HTML input for Tailwind scanning
* static/ → Output-only directory for compiled assets

---

### 3. Tailwind Input / Output Contract

* Tailwind input CSS lives in:

  frontend/src/input.css

* Tailwind compiled output MUST be written to:

  src/minutes_iq/static/css/tailwind.css

* No handwritten CSS is allowed in static/css/

---

### 4. Template Scanning Rules

* Tailwind must scan only Jinja templates:

  src/minutes_iq/templates/**/*.html

* No JavaScript or Python files are scanned by Tailwind.

---

### 5. Jinja Integration

Templates include Tailwind via:

<link rel="stylesheet" href="{{ url_for('static', path='css/tailwind.css') }}">

* Do not inline Tailwind CDN scripts in production templates.

---

### 6. Responsibilities Boundary

Layer responsibilities:

* FastAPI: Routing, authentication, background jobs
* Jinja: HTML rendering
* Tailwind: CSS compilation
* static/: Asset hosting only

These responsibilities must remain isolated.

---

### 7. Non-Goals (Explicitly Disallowed)

* Do NOT place node_modules under src/
* Do NOT modify Python imports to reference frontend tooling
* Do NOT use Tailwind CDN except for temporary prototyping
* Do NOT create CSS inside templates/

---

## Summary

This project follows a backend-first architecture.

Frontend tooling is isolated, deterministic, and replaceable.
The Python application must remain unaware of the build system.

Any deviation from this structure is considered a defect.
