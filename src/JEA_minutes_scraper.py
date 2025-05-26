# src/JEA_minutes_scraper.py

"""
JEA Meeting Minutes Scraper with NLP Entity Extraction
- Streams PDFs from JEA board meeting archive
- Parses N or all pages for keyword matches
- Downloads full PDF if keywords are found
- Filters documents by date range
- Extracts named entities from matched content using spaCy
- Saves structured match data with NLP entities
"""

import os
import re
import requests
import hashlib
from bs4 import BeautifulSoup
import pdfplumber
import pandas as pd
from io import BytesIO
from datetime import datetime
import logging
from collections import defaultdict
import spacy

# === NLP SETUP ===
nlp = spacy.load("en_core_web_sm")

# === CONFIG ===
BASE_URL = "https://www.jea.com/About/Board_and_Management/Board_Meetings_Archive/"
PDF_DIR = os.path.join("..", "data", "raw_pdfs")
RESULT_DIR = os.path.join("..", "data", "processed")
KEYWORDS_FILE = os.path.join("..", "keywords.txt")
LOG_FILE = os.path.join("..", "scraper.log")
MAX_SCAN_PAGES = 15  # Set to None to scan all pages, or an integer like 5
DATE_RANGE = ("2024-06", "2025-05")  # YYYY-MM format strings

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
RESULT_CSV = os.path.join(RESULT_DIR, f"extracted_mentions_{timestamp}.csv")

# === SETUP ===
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')

# === LOAD KEYWORDS ===
def load_keywords(filepath):
    with open(filepath, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

keywords = load_keywords(KEYWORDS_FILE)

# === SCRAPE PDF LINKS ===
def get_pdf_links(include_minutes=True, include_packages=True):
    res = requests.get(BASE_URL)
    soup = BeautifulSoup(res.content, 'html.parser')
    pdf_links = []
    for row in soup.find_all("tr"):
        for a_tag in row.find_all("a", href=True):
            text = a_tag.get_text(strip=True).lower()
            href = a_tag["href"]
            if ("minutes" in text and include_minutes) or ("package" in text and include_packages):
                full_link = href if href.startswith("http") else f"https://www.jea.com{href}"
                filename = get_safe_filename(full_link)
                date_match = re.search(r'(20\d{2})[\-_](\d{2})', filename)
                if date_match:
                    y, m = date_match.groups()
                    ym_str = f"{y}-{m}"
                    if DATE_RANGE[0] <= ym_str <= DATE_RANGE[1]:
                        pdf_links.append(full_link)
    return pdf_links

# === FILENAME HELPER ===
def get_safe_filename(url):
    tail = url.rstrip('/').split('/')[-1]
    if not tail:
        hash_str = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"unknown_{hash_str}.pdf"
    else:
        tail = re.sub(r'[^a-zA-Z0-9_-]', '_', tail)
        return f"{tail}.pdf" if not tail.endswith('.pdf') else tail

# === STREAM & SCAN PDF WITH NLP ===
def stream_and_scan_pdf(url, max_pages=MAX_SCAN_PAGES):
    try:
        response = requests.get(url)
        pdf_bytes = BytesIO(response.content)
        with pdfplumber.open(pdf_bytes) as pdf:
            matches = []
            pages_to_scan = pdf.pages if max_pages is None else pdf.pages[:max_pages]
            for i, page in enumerate(pages_to_scan):
                text = page.extract_text() or ""
                for keyword in keywords:
                    if keyword.lower() in text.lower():
                        context_snippet = text[text.lower().find(keyword.lower()):][:300]
                        doc = nlp(context_snippet)
                        entities = ", ".join(f"{ent.text} ({ent.label_})" for ent in doc.ents)
                        matches.append({
                            "file": get_safe_filename(url),
                            "page": i + 1,
                            "keyword": keyword,
                            "snippet": context_snippet.strip(),
                            "entities": entities
                        })
            return matches, response.content if matches else None, len(pages_to_scan)
    except Exception as e:
        logging.error(f"Error processing {url}: {e}")
        return [], None, 0

# === MAIN ===
if __name__ == "__main__":
    print("🔍 Fetching PDF links...")
    logging.info("Started scraping JEA PDFs")
    pdf_links = get_pdf_links(include_minutes=True, include_packages=True)

    all_mentions = []
    keyword_counts = defaultdict(int)

    print("🔎 Scanning and downloading PDFs with matches...")
    for url in pdf_links:
        filename = get_safe_filename(url)
        filepath = os.path.join(PDF_DIR, filename)

        matches, pdf_content, num_pages_scanned = stream_and_scan_pdf(url)
        if matches:
            print(f"✅ Match found in {filename}, saving PDF...")
            logging.info(f"Match found in {filename}, saved to disk.")
            with open(filepath, 'wb') as f:
                f.write(pdf_content)
            all_mentions.extend(matches)
            for m in matches:
                keyword_counts[m['keyword']] += 1
        else:
            print(f"⏩ No match in first {num_pages_scanned} pages of {filename}, skipping...")
            logging.info(f"No match in {filename}, skipped.")

    print(f"💾 Saving {len(all_mentions)} matches to CSV: {RESULT_CSV}")
    pd.DataFrame(all_mentions).to_csv(RESULT_CSV, index=False)
    logging.info(f"Results saved to {RESULT_CSV}")

    print("\n📊 Keyword Match Summary:")
    print("-------------------------")
    for keyword, count in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"{keyword}: {count}")
    print("\n✅ Done.")
    logging.info("Scraper finished successfully.")

