# 📄 JEA Meeting Minutes Scraper (PRIVATE REPO)

## 🚧 Status: In Development | ⚖️ Intended for Internal Use Only

---

## 📌 Overview

This project scrapes public meeting minutes from the **JEA Board of Directors** website to identify potential **upcoming infrastructure projects** for business development use.

⚠️ **This repository is private and not intended for public disclosure.**  
Data is collected ethically from publicly available records but is used exclusively for internal pre-positioning purposes. No personally identifiable or sensitive data is being disclosed or distributed.

---

## 🎯 Objectives

- Automatically collect all available PDF meeting minutes from [JEA.com](https://www.jea.com/About/Leadership/Board_Meetings/)
- Parse PDF content for engineering-related keywords (e.g., *“stormwater,” “lift station,” “RFP”*)
- Capture and store snippets around those keywords to enable manual review
- Organize results into a CSV for internal use

---

## 🧱 Folder Structure

jea_scraper/
├── data/
│ ├── raw_pdfs/ # Downloaded PDF meeting minutes
│ └── extracted_mentions.csv # Final output: date, keyword, snippet
├── notebooks/
│ └── 01_extract_and_parse.ipynb
├── src/
│ ├── fetch_pdfs.py # Scrape & download PDFs
│ ├── parse_pdfs.py # Extract text & match keywords
│ └── utils.py # Helper functions
├── keywords.txt # Editable keyword list
├── README.md # You're here
└── requirements.txt # Python environment


---

## 🛠️ Stack / Dependencies

- `requests`
- `beautifulsoup4`
- `pdfplumber`
- `pandas`
- *(Optional NLP)*: `spaCy`, `scikit-learn`, `nltk`

Install with:

```bash
pip install -r requirements.txt

