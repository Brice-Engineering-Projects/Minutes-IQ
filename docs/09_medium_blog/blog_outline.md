# AI-Powered Municipal Signals: From Meeting Minutes to Market Moves

## ✪ Introduction

* Most firms wait for RFPs. We built a system that sees the signals *before* the RFP drops.
* Scraping public meeting minutes to detect civil project opportunities early.
* Using AI and NLP to turn municipal noise into actionable business intelligence.

---

## 🏛️ The Problem: Lagging Behind in BD

* Municipal firms often react *after* RFQs go public.
* Key project clues are often buried in meeting minutes months in advance.
* Traditional methods are manual, inconsistent, and often ignored.

---

## 🤖 The Solution: AI-Powered Signal Extraction

* Python-based scraper monitors board meeting PDFs (JEA case study).
* Uses NLP (spaCy) to extract:

  * Project-related keywords
  * Named entities: contractors, funding, locations
* Adds PDF highlighting + bookmark navigation for fast review.

---

## 🧐 How It Works (Visually Engaging)

* Scraper runs periodically to collect meeting minutes
* Keywords editable via `keywords.txt`
* NLP extracts:

  * 💰 Budgets (e.g. "\$2 million")
  * 🏩 Locations (e.g. "Jacksonville")
  * 🏗️ Org Names (e.g. "Black & Veatch")
* Matching PDFs saved and **highlighted**
* Streamlit dashboard displays:

  * Top keywords
  * Filterable matches
  * Date/snippet preview

> Insert dashboard + PDF highlight screenshot

---

## 📈 What We Found

* Matches cluster around specific committees (Finance, Capital Improvements)
* Consent agenda items often contain valuable leads hidden in attachments
* Identified early mentions of utility improvements before RFQ was posted

---

## 💡 Real-World Impact

* Pre-position before competitors
* Build relationship pipelines *before* procurement
* Expandable to other municipalities

---

## 🛠️ Tech Stack

* Python, pdfplumber, spaCy, PyMuPDF
* Streamlit for dashboard
* Conda environment
* (Optional: Private GitHub repo)

---

## 🧱 What’s Next

* Summarize full PDF packages
* ML classification of urgency/relevance
* CRM or Slack integration for alerts

---

## 🧠 Final Thoughts

> "In a world where public data is free but underused, the real competitive edge isn’t access — it’s interpretation."

If your BD team isn’t using AI to read between the lines, you’re already behind.
