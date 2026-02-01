# Minimal Frontend Build Setup (Tailwind – Inert by Design)

This document defines the **minimal, correct frontend build architecture**. It is intentionally low-impact and safe to add immediately.

The goal is to establish a clean boundary now, without changing UI behavior yet.

---

## Directory Placement (Project Root)

Create this directory at the **project root** (not under src/):

frontend/

This directory owns all frontend build tooling. Python must never import from here.

---

## Required Files

Create the following files exactly as named.

### frontend/package.json

Purpose: Declare the frontend toolchain. No scripts are required yet.

Contents:

{
"name": "minutes-iq-frontend",
"private": true,
"version": "0.0.0",
"devDependencies": {
"tailwindcss": "^3.4.0",
"postcss": "^8.4.0",
"autoprefixer": "^10.4.0"
}
}

---

### frontend/tailwind.config.js

Purpose: Define what Tailwind scans and where it outputs.

Contents:

module.exports = {
content: [
"../src/minutes_iq/templates/**/*.html"
],
theme: {
extend: {},
},
plugins: [],
};

---

### frontend/postcss.config.js

Purpose: Enable Tailwind processing.

Contents:

module.exports = {
plugins: {
tailwindcss: {},
autoprefixer: {},
},
};

---

### frontend/src/input.css

Purpose: Tailwind source file. Custom styles will migrate here later.

Contents:

@tailwind base;
@tailwind components;
@tailwind utilities;

/*
NOTE:
Custom styles (spinners, toasts, cards) will be migrated here later
using @layer components or @layer utilities.
*/

---

## Output Contract (Do Not Break)

Tailwind output MUST be written to:

src/minutes_iq/static/css/tailwind.css

Even if this file does not exist yet, this path is authoritative.

---

## Base Template Change (Immediate)

In base.html:

* Remove Tailwind CDN usage
* Link to the compiled stylesheet instead

The application should reference:

/static/css/tailwind.css

htmx remains loaded via CDN for now.

---

## What This Setup Does NOT Do (By Design)

* Does NOT require running a Tailwind build yet
* Does NOT break existing UI
* Does NOT migrate existing CSS
* Does NOT introduce Node into Python execution

This setup only establishes architectural boundaries.

---

## Why This Exists

This prevents future UI entropy and avoids repeating the Flask + Tailwind failure mode.

Once this boundary exists, CSS migration can happen incrementally and safely.

---

## Summary

* frontend/ exists now
* Tailwind knows where templates live
* Python knows nothing about Node
* UI continues to work
* Migration happens later, intentionally

This is a preventative architectural step.
