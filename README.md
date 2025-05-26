# 🕵️‍♂️ JEA Meeting Minutes Scraper & Dashboard

This project scrapes and analyzes **JEA commission meeting PDFs** to detect early signs of potential civil engineering projects. It includes a keyword-based PDF scanner and a Streamlit dashboard for visualizing results.

---

## 📁 Project Structure

```
project_root/
├── data/
│   ├── raw_pdfs/              # Downloaded PDFs with matches
│   └── processed/             # Extracted keyword match CSVs
├── src/
│   ├── dashboard/             # Streamlit dashboard app
│   │   └── dashboard.py
│   └── JEA_minutes_scraper.py  # Main scraper logic
├── keywords.txt              # List of keywords to scan for
├── scraper.log               # Logging output
└── README.md
```

---

## ⚙️ Requirements

Use a **Conda environment**. Install dependencies via:

```bash
conda install -c conda-forge streamlit beautifulsoup4 requests pandas pdfplumber
```

---

## 🚀 How to Use

### 1. 📥 Scrape the PDFs

Edit the `DATE_RANGE` and `MAX_SCAN_PAGES` values in `src/JEA_minutes_scraper.py` to suit your target window.

Then run:

```bash
cd src
python JEA_minutes_scraper.py
```

This will:
- Download PDFs with keyword hits
- Save snippets and matches in `/data/processed/`
- Log activity in `scraper.log`

---

### 2. 📊 Launch the Dashboard

After scraping, you can visualize the results:

```bash
streamlit run src/dashboard/dashboard.py
```

This launches a local web app showing:
- Keyword frequency charts
- Searchable mentions
- Filters by keyword and meeting date

---

## 📝 Keywords

The `keywords.txt` file controls what you’re looking for in PDFs. Format:

```
rehab
stormwater
consent agenda
...
```
Lines beginning with `#` are ignored.

---

## ⏰ (Optional) Automation with Cron

You can automate scraping with a cron job. Example:

```cron
0 6 * * 1 /path/to/env/bin/python /full/path/to/src/JEA_minutes_scraper.py >> /full/path/to/scraper_cron.log 2>&1
```

This runs the scraper **every Monday at 6 AM**.

---

## 🧠 Author Notes

Built as a civil-engineering-focused business intelligence tool. The dashboard is designed for internal use to identify upcoming infrastructure projects.

⚠️ PDF matches and results are not publicly shared due to ethical considerations.

---

## ✅ Future Ideas

- 🧠 NLP summary extraction
- 📧 Email alerts for high-interest hits
- 🗂️ Tagging PDFs by committee/topic
- 📅 Dashboard time series charts

---

Let me know if you'd like to turn this into a deployable Streamlit Cloud app or wire up nightly scrapes with caching!
