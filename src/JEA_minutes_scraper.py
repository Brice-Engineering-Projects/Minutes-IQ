# src/jea_minutes_scraper.py

"""
JEA Meeting Minutes Scraper
- Downloads PDFs from JEA board meeting archive
- Extracts text from each PDF
- Searches for project-related keywords
- Stores results with context in a CSV
"""

import os
import requests
from bs4 import BeautifulSoup
import pdfplumber
import pandas as pd
from datetime import datetime

# === CONFIG ===
BASE_URL = "https://www.jea.com/About/Board_and_Management/Board_Meetings_Archive/"
PDF_DIR = "data/raw_pdfs"
RESULT_CSV = "data/extracted_mentions.csv"
KEYWORDS_FILE = "keywords.txt"

# === SETUP ===
os.makedirs(PDF_DIR, exist_ok=True)

# === LOAD KEYWORDS ===
def load_keywords(filepath):
    with open(filepath, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

keywords = load_keywords(KEYWORDS_FILE)

# === SCRAPE PDF LINKS (Minutes and/or Packages) ===
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
                pdf_links.append(full_link)

    return pdf_links

# === DOWNLOAD PDFS ===
def download_pdfs(pdf_links):
    for url in pdf_links:
        filename = url.split("/")[-1]
        filepath = os.path.join(PDF_DIR, filename)
        if not os.path.exists(filepath):
            print(f"Downloading {filename}...")
            response = requests.get(url)
            with open(filepath, 'wb') as f:
                f.write(response.content)

# === PARSE AND SEARCH PDFs ===
def extract_mentions_from_pdf(filepath):
    mentions = []
    filename = os.path.basename(filepath)
    try:
        with pdfplumber.open(filepath) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                for keyword in keywords:
                    if keyword.lower() in text.lower():
                        context_snippet = text[text.lower().find(keyword.lower()):][:300]
                        mentions.append({
                            "file": filename,
                            "page": i + 1,
                            "keyword": keyword,
                            "snippet": context_snippet.strip()
                        })
    except Exception as e:
        print(f"Error reading {filename}: {e}")
    return mentions

# === MAIN ===
if __name__ == "__main__":
    print("🔍 Fetching PDF links...")
    pdf_links = get_pdf_links(include_minutes=True, include_packages=False)

    print("📥 Downloading PDFs...")
    download_pdfs(pdf_links)

    print("🔎 Extracting keyword mentions...")
    all_mentions = []
    for file in os.listdir(PDF_DIR):
        path = os.path.join(PDF_DIR, file)
        mentions = extract_mentions_from_pdf(path)
        all_mentions.extend(mentions)

    print(f"✅ Found {len(all_mentions)} total mentions. Saving to CSV...")
    pd.DataFrame(all_mentions).to_csv(RESULT_CSV, index=False)
    print(f"💾 Results saved to {RESULT_CSV}")
