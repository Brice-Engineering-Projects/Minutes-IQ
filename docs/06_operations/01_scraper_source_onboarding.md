# 🏗️ Scraper Source Onboarding Checklist (Admin Only)

## Purpose
Defines the **safe, repeatable process** for adding a new municipal client to the scraping system.

---

## Phase 1 — Intake

- [ ] Client name confirmed
- [ ] Primary website identified
- [ ] Meeting minutes location identified
- [ ] Document formats confirmed (PDF/HTML)

---

## Phase 2 — Technical Validation

- [ ] Robots.txt reviewed
- [ ] Pagination behavior understood
- [ ] File naming consistency verified
- [ ] Historical archive reachable

---

## Phase 3 — Scraper Testing

- [ ] Test scrape run locally
- [ ] PDFs downloaded correctly
- [ ] Text extraction verified
- [ ] Keyword detection validated

---

## Phase 4 — Failure Handling

- [ ] Broken link behavior tested
- [ ] Missing PDF handling verified
- [ ] Timeout behavior tested

---

## Phase 5 — Database Entry

- [ ] Client added (disabled)
- [ ] Source URLs added
- [ ] Metadata documented
- [ ] Client enabled

---

## Phase 6 — Regression Check

- [ ] Existing clients re-tested
- [ ] No shared logic broken

---

**Admin Rule:**  
> _No client is enabled without passing all phases._
