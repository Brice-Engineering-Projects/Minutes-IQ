# src/JEA_minutes_scraper.py

"""
JEA Meeting Minutes Scraper (Filename-Safe Version with Logging)
- Streams PDFs from JEA board meeting archive
- Parses first N pages for keyword matches
- Downloads full PDF only if keywords are found
- Saves matches with context in a timestamped CSV in data/processed
- Logs activity to ../scraper.log and prints summary statistics
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

# === CONFIG ===
BASE_URL = "https://www.jea.com/About/Board_and_Management/Board_Meetings_Archive/"
PDF_DIR = os.path.join("..", "data", "raw_pdfs")
RESULT_DIR = os.path.join("..", "data", "processed")
KEYWORDS_FILE = os.path.join("..", "keywords.txt")
LOG_FILE = os.path.join("..", "scraper.log")
MAX_SCAN_PAGES = 3

# Timestamped output file
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
def get_pdf_links(include_minutes=True, include_packages=False):
    res = requests.get(BASE_URL)
    soup = BeautifulSoup(res.content, 'html.parser')
    pdf_links = []
    for row in soup.find_all("tr"):
        for a_tag in row.find_all("a", href=True):
            text = a_tag.get_text(strip=True).lower()
            href = a_tag["href"]
            if ("minutes" in text and include_minutes) or ("package" in text and include_packages):
                full_link = href if href.startswith("http") else f"https://www.jea.com{href}"
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

# === STREAM & SCAN PDF ===
def stream_and_scan_pdf(url, max_pages=MAX_SCAN_PAGES):
    try:
        response = requests.get(url)
        pdf_bytes = BytesIO(response.content)
        with pdfplumber.open(pdf_bytes) as pdf:
            matches = []
            for i, page in enumerate(pdf.pages[:max_pages]):
                text = page.extract_text() or ""
                for keyword in keywords:
                    if keyword.lower() in text.lower():
                        context_snippet = text[text.lower().find(keyword.lower()):][:300]
                        matches.append({
                            "file": get_safe_filename(url),
                            "page": i + 1,
                            "keyword": keyword,
                            "snippet": context_snippet.strip()
                        })
            return matches, response.content if matches else None
    except Exception as e:
        logging.error(f"Error processing {url}: {e}")
        return [], None

# === MAIN ===
if __name__ == "__main__":
    print("🔍 Fetching PDF links...")
    logging.info("Started scraping JEA PDFs")
    pdf_links = get_pdf_links(include_minutes=True, include_packages=False)

    all_mentions = []
    keyword_counts = defaultdict(int)

    print("🔎 Scanning and downloading PDFs with matches...")
    for url in pdf_links:
        filename = get_safe_filename(url)
        filepath = os.path.join(PDF_DIR, filename)

        matches, pdf_content = stream_and_scan_pdf(url)
        if matches:
            print(f"✅ Match found in {filename}, saving PDF...")
            logging.info(f"Match found in {filename}, saved to disk.")
            with open(filepath, 'wb') as f:
                f.write(pdf_content)
            all_mentions.extend(matches)
            for m in matches:
                keyword_counts[m['keyword']] += 1
        else:
            print(f"⏩ No match in first {MAX_SCAN_PAGES} pages of {filename}, skipping...")
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