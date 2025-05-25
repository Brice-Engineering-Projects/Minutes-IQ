# 🧠 JEA Meeting Minutes Scraper: Civil Engineering BD Intelligence

## 📌 Project Overview

This project extracts infrastructure-related insights from **JEA Commission Meeting Minutes** using web scraping and PDF parsing. The goal is to identify potential **early-phase projects**, **capital planning discussions**, or **pre-RFP activities** to assist in business development and pre-positioning for engineering services.

---

## 🚀 Objectives

- Scrape publicly available **PDF meeting minutes** from the [JEA Board Meetings page](https://www.jea.com/About/Leadership/Board_Meetings/)
- Extract **relevant project keywords** (e.g., “stormwater,” “lift station,” “RFP,” etc.)
- Provide **contextual snippets** for manual review
- (Optional) Apply **basic NLP** techniques for deeper insight

---

## 🧱 Project Structure

jea_scraper/
├── data/
│ ├── raw_pdfs/
│ └── extracted_mentions.csv
├── notebooks/
│ └── 01_extract_and_parse_jea_minutes.ipynb
├── src/
│ ├── fetch_pdfs.py
│ ├── parse_pdfs.py
│ └── keyword_search.py
├── keywords.txt
├── README.md
└── requirements.txt


---

## 📚 Phase 1: Basic Web Scraping & Parsing

### ✅ Tasks

- [ ] Scrape all PDF links from the JEA Board Meetings page
- [ ] Download PDFs to `data/raw_pdfs/`
- [ ] Extract full text using `pdfplumber`
- [ ] Search for predefined **keywords**
- [ ] Save results to CSV:
  - Meeting date
  - PDF URL
  - Matched keyword
  - Snippet of surrounding context

---

## 🤖 Phase 2 (Optional): NLP & Smart Filtering

### 🔍 Enhancements

- Use **Named Entity Recognition (NER)** to detect locations, consultants, or funding amounts
- Classify project mentions as:
  - Idea / Discussion
  - Study / Planning
  - Approved / Funded
- Rank topics by frequency to flag **recurring needs**

---

## ⚖️ Ethics & Usage

- All data is sourced from **public domain meeting minutes**
- This tool is intended for **internal business development**
- **No raw insights or names will be published publicly**
- Any future blog posts will abstract findings to ensure ethical integrity

---

## 🧪 Example Keywords (editable in `keywords.txt`)

- stormwater
- sanitary sewer
- lift station
- force main
- RFP
- capital improvement
- infrastructure
- design study
- grant
- rehabilitation


---

## 🛠 Tools & Libraries

- `requests` + `BeautifulSoup` → for scraping PDF links
- `pdfplumber` → for text extraction
- `pandas` → for organizing results
- `spaCy`, `scikit-learn` (optional) → for NLP analysis

---

## 📈 Future Enhancements

- GUI dashboard using Streamlit or Flask
- Schedule daily/weekly scraping via cron or GitHub Actions
- Add keyword weightings or fuzzy matching for variations
- Scrape related municipal data (e.g., Jacksonville City Council)

---

## ✍️ Author Notes

This project is built for private use by a civil engineering professional leveraging data science to gain ethical business intelligence from publicly available sources. No data or names will be made public.

