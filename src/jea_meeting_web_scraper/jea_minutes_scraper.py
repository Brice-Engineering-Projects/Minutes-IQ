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

import hashlib
import logging
import os
import re
from collections import defaultdict
from datetime import datetime
from io import BytesIO

import pandas as pd
import pdfplumber
import requests
import spacy
from bs4 import BeautifulSoup

# === NLP SETUP ===
nlp = spacy.load("en_core_web_sm")

# === CONFIG ===
ARCHIVE_URL = "https://www.jea.com/About/Board_and_Management/Board_Meetings_Archive/"
CURRENT_MEETINGS_URL = (
    "https://www.jea.com/about/board_and_management/jea_board_meetings/"
)
# Get absolute paths relative to this script's location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
PDF_DIR = os.path.join(PROJECT_ROOT, "data", "raw_pdfs")
RESULT_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
KEYWORDS_FILE = os.path.join(PROJECT_ROOT, "keywords.txt")
LOG_FILE = os.path.join(PROJECT_ROOT, "scraper.log")
MAX_SCAN_PAGES = None  # Set to None to scan all pages, or an integer like 5
DATE_RANGE = ("2024-01", "2025-12")  # YYYY-MM format strings

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
RESULT_CSV = os.path.join(RESULT_DIR, f"extracted_mentions_{timestamp}.csv")

# === SETUP ===
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(message)s"
)


# === LOAD KEYWORDS ===
def load_keywords(filepath):
    with open(filepath) as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]


keywords = load_keywords(KEYWORDS_FILE)


# === SCRAPE PDF LINKS ===
def get_pdf_links_from_url(
    url, include_minutes=True, include_packages=True, debug=False
):
    """Scrape PDF links from a single URL"""
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    pdf_links = []
    all_pdfs_found = []

    for row in soup.find_all("tr"):
        for a_tag in row.find_all("a", href=True):
            text = a_tag.get_text(strip=True).lower()
            href = str(a_tag["href"])
            if ("minutes" in text and include_minutes) or (
                "package" in text and include_packages
            ):
                full_link = (
                    href if href.startswith("http") else f"https://www.jea.com{href}"
                )
                filename = get_safe_filename(full_link)

                # Try multiple date patterns
                date_match = re.search(
                    r"(20\d{2})[\-_](\d{2})[\-_](\d{2})", filename
                )  # YYYY-MM-DD or YYYY_MM_DD

                if debug:
                    all_pdfs_found.append((filename, full_link, date_match))

                if date_match:
                    y, m = date_match.groups()[0], date_match.groups()[1]
                    ym_str = f"{y}-{m}"
                    if DATE_RANGE[0] <= ym_str <= DATE_RANGE[1]:
                        pdf_links.append(full_link)

    return pdf_links, all_pdfs_found


def get_pdf_links(include_minutes=True, include_packages=True, debug=False):
    """Scrape PDF links from both archive and current meetings pages"""
    all_links = []
    all_pdfs = []

    print("  → Scraping archive page...")
    archive_links, archive_pdfs = get_pdf_links_from_url(
        ARCHIVE_URL, include_minutes, include_packages, debug
    )
    all_links.extend(archive_links)
    all_pdfs.extend(archive_pdfs)

    print("  → Scraping current meetings page...")
    current_links, current_pdfs = get_pdf_links_from_url(
        CURRENT_MEETINGS_URL, include_minutes, include_packages, debug
    )
    all_links.extend(current_links)
    all_pdfs.extend(current_pdfs)

    # Remove duplicates while preserving order
    seen = set()
    unique_links = []
    for link in all_links:
        if link not in seen:
            seen.add(link)
            unique_links.append(link)

    if debug:
        return unique_links, all_pdfs
    return unique_links


# === FILENAME HELPER ===
def get_safe_filename(url):
    tail = url.rstrip("/").split("/")[-1]
    if not tail:
        hash_str = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"unknown_{hash_str}.pdf"
    else:
        tail = re.sub(r"[^a-zA-Z0-9_-]", "_", tail)
        return f"{tail}.pdf" if not tail.endswith(".pdf") else tail


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
                        context_snippet = text[text.lower().find(keyword.lower()) :][
                            :300
                        ]
                        doc = nlp(context_snippet)
                        entities = ", ".join(
                            f"{ent.text} ({ent.label_})" for ent in doc.ents
                        )
                        matches.append(
                            {
                                "file": get_safe_filename(url),
                                "page": i + 1,
                                "keyword": keyword,
                                "snippet": context_snippet.strip(),
                                "entities": entities,
                            }
                        )
            return matches, response.content if matches else None, len(pages_to_scan)
    except Exception as e:
        logging.error(f"Error processing {url}: {e}")
        return [], None, 0


# === MAIN ===
if __name__ == "__main__":
    print("🔍 Fetching PDF links...")
    logging.info("Started scraping JEA PDFs")
    pdf_links, all_pdfs = get_pdf_links(
        include_minutes=True, include_packages=True, debug=True
    )

    print(
        f"📋 Found {len(pdf_links)} PDFs in date range {DATE_RANGE[0]} to {DATE_RANGE[1]}"
    )
    print(f"📊 Total PDFs on website: {len(all_pdfs)}")

    if len(all_pdfs) > 0:
        print("\n🔍 Sample of ALL available PDFs with full URLs:")
        for filename, url, date_match in all_pdfs[:20]:  # Show first 20
            if date_match:
                y, m = date_match.groups()[0], date_match.groups()[1]
                print(f"  - {filename} → {y}-{m}")
            else:
                print(f"  - {filename} → [no date parsed]")
                print(f"    URL: {url[:80]}...")

    if len(pdf_links) == 0:
        print(
            "⚠️ No PDFs found in the specified date range. Check the JEA website or adjust DATE_RANGE."
        )
        logging.warning("No PDFs found in date range.")

    print(f"🔑 Loaded {len(keywords)} keywords from {KEYWORDS_FILE}")

    all_mentions = []
    keyword_counts: dict[str, int] = defaultdict(int)

    print("🔎 Scanning and downloading PDFs with matches...")
    for url in pdf_links:
        filename = get_safe_filename(url)
        filepath = os.path.join(PDF_DIR, filename)

        matches, pdf_content, num_pages_scanned = stream_and_scan_pdf(url)
        if matches and pdf_content is not None:
            print(f"✅ Match found in {filename}, saving PDF...")
            logging.info(f"Match found in {filename}, saved to disk.")
            with open(filepath, "wb") as f:
                f.write(pdf_content)
            all_mentions.extend(matches)
            for m in matches:
                keyword_counts[m["keyword"]] += 1
        else:
            print(
                f"⏩ No match in {num_pages_scanned} pages of {filename}, skipping..."
            )
            logging.info(f"No match in {filename}, skipped.")

    print(f"💾 Saving {len(all_mentions)} matches to CSV: {RESULT_CSV}")
    pd.DataFrame(all_mentions).to_csv(RESULT_CSV, index=False)
    logging.info(f"Results saved to {RESULT_CSV}")

    print("\n📊 Keyword Match Summary:")
    print("-------------------------")
    for keyword, count in sorted(
        keyword_counts.items(), key=lambda x: x[1], reverse=True
    ):
        print(f"{keyword}: {count}")
    print("\n✅ Done.")
    logging.info("Scraper finished successfully.")
