# 🏛️ JEA Meeting Minutes Scraper & Intelligence Dashboard

This project scrapes, analyzes, and visualizes public JEA board meeting minutes for strategic business development insights.

---

## 🚀 Features

### 🧠 Scraper: `JEA_minutes_scraper.py`
- Streams and scans JEA board meeting PDFs
- Filters by date and keyword
- Extracts text and detects keywords
- Uses **spaCy NLP** to extract named entities (e.g., organizations, locations, money, dates)
- Saves:
  - Matching PDFs to `/data/raw_pdfs/`
  - Match metadata to `/data/processed/*.csv`

### 🔎 PDF Highlighter: `highlight_mentions.py`
- Reopens saved PDFs
- Highlights matched keywords (and optionally named entities)
- Saves annotated PDFs to `/data/annotated_pdfs/`

### 📊 Dashboard: `dashboard.py`
- Filters by keyword, named entity, or date
- Displays:
  - Keyword frequency chart
  - Data table with matches and extracted context
  - Entity-level filtering (GPE, ORG, MONEY, etc.)

---

## 🛠️ Setup

```bash
conda create -n jea_scraper python=3.11
conda activate jea_scraper
conda install -c conda-forge pdfplumber pymupdf beautifulsoup4 spacy pandas
python -m spacy download en_core_web_sm
```

---

## 📁 Project Structure

```
📂 data/
├── raw_pdfs/              # PDFs saved when a keyword match is found
├── annotated_pdfs/        # Highlighted PDFs for easy reading
└── processed/             # CSV files with extracted match + NLP metadata

📂 src/
├── JEA_minutes_scraper.py   # Main scraper with NLP integration
├── highlight_mentions.py    # Highlights keywords in PDFs
└── dashboard/
    └── dashboard.py         # Streamlit-based insights dashboard

📄 keywords.txt              # One keyword per line to match against PDFs
```

---

## 🧪 How to Use

### 1. Scrape & Analyze
```bash
python src/JEA_minutes_scraper.py
```
- Finds matching PDFs based on keywords
- Extracts relevant context and NLP entities
- Saves results to CSV

### 2. Highlight PDFs
```bash
python src/highlight_mentions.py
```
- Highlights matches in the original PDFs
- Saves new annotated PDFs

### 3. Launch Dashboard
```bash
streamlit run src/dashboard/dashboard.py
```
- Filter and explore all matches interactively

---

## 🗂️ Example Output (CSV)

| file                           | page | keyword   | snippet                              | entities                       |
|--------------------------------|------|-----------|--------------------------------------|--------------------------------|
| 2024_06_25_Board_Meeting.pdf  | 3    | stormwater | "...stormwater improvements in..."  | Jacksonville (GPE), $2M (MONEY) |

---

## 📌 Notes
- You control scanning depth with `MAX_SCAN_PAGES` in the scraper
- Set date range via `DATE_RANGE` (e.g., `("2024-06", "2025-05")`)
- Add or remove keywords in `keywords.txt`

---

## 📬 Next Steps
- Add color-coded highlights for different entities
- Explore integrations with chat-based querying or alerting
- Build a summary generator for long packages

---

## 👋 About
This project is used for internal business development exploration. Scraped data is not shared publicly to respect ethical boundaries.

---

Made with 💼, 🧠, and Python.
