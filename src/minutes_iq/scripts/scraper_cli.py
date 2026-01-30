#!/usr/bin/env python3
"""
Legacy CLI script for scraping JEA meeting minutes.

This script provides backward compatibility with the old file-based workflow.
For new workflows, use the database-backed scraper service instead.

Usage:
    python -m minutes_iq.scripts.scraper_cli

Configuration:
    Edit the constants below to adjust scraping behavior.
"""

import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd

from minutes_iq.scraper.core import scrape_pdf_links, stream_and_scan_pdf

# === CONFIG ===
ARCHIVE_URL = "https://www.jea.com/About/Board_and_Management/Board_Meetings_Archive/"
CURRENT_MEETINGS_URL = (
    "https://www.jea.com/about/board_and_management/jea_board_meetings/"
)

# Get absolute paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
PDF_DIR = PROJECT_ROOT / "data" / "raw_pdfs"
RESULT_DIR = PROJECT_ROOT / "data" / "processed"
KEYWORDS_FILE = PROJECT_ROOT / "keywords.txt"
LOG_FILE = PROJECT_ROOT / "scraper.log"

# Scraping parameters
MAX_SCAN_PAGES = None  # Set to None to scan all pages, or an integer like 5
DATE_RANGE = ("2024-01", "2025-12")  # YYYY-MM format strings
INCLUDE_MINUTES = True
INCLUDE_PACKAGES = True

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
RESULT_CSV = RESULT_DIR / f"extracted_mentions_{timestamp}.csv"


def load_keywords(filepath: Path) -> list[str]:
    """Load keywords from a text file."""
    if not filepath.exists():
        print(f"⚠️  Keywords file not found: {filepath}")
        print("   Creating empty keywords file. Please add keywords and run again.")
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text("# Add keywords here, one per line\n")
        return []

    with open(filepath) as f:
        keywords = [
            line.strip() for line in f if line.strip() and not line.startswith("#")
        ]
    return keywords


def main():
    """Main CLI entry point."""
    # Setup
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(message)s"
    )

    # Load keywords
    keywords = load_keywords(KEYWORDS_FILE)
    if not keywords:
        print("❌ No keywords found. Exiting.")
        return 1

    print(f"🔑 Loaded {len(keywords)} keywords from {KEYWORDS_FILE}")

    # Scrape PDF links
    print("🔍 Fetching PDF links...")
    logging.info("Started scraping JEA PDFs")

    all_pdf_links = []
    for source_url in [ARCHIVE_URL, CURRENT_MEETINGS_URL]:
        print(f"  → Scraping {source_url.split('/')[-2]}...")
        pdf_links = scrape_pdf_links(
            base_url=source_url,
            date_range_start=DATE_RANGE[0],
            date_range_end=DATE_RANGE[1],
            include_minutes=INCLUDE_MINUTES,
            include_packages=INCLUDE_PACKAGES,
        )
        all_pdf_links.extend(pdf_links)

    # Remove duplicates
    seen = set()
    unique_links = []
    for link_info in all_pdf_links:
        if link_info["url"] not in seen:
            seen.add(link_info["url"])
            unique_links.append(link_info)

    print(
        f"📋 Found {len(unique_links)} PDFs in date range {DATE_RANGE[0]} to {DATE_RANGE[1]}"
    )

    if len(unique_links) == 0:
        print("⚠️  No PDFs found in the specified date range.")
        print("   Check the JEA website or adjust DATE_RANGE.")
        logging.warning("No PDFs found in date range.")
        return 1

    # Show sample of available PDFs
    if len(unique_links) > 0:
        print("\n🔍 Sample of available PDFs:")
        for link_info in unique_links[:10]:
            date_str = link_info["date_str"] or "[no date]"
            print(f"  - {link_info['filename']} → {date_str}")

    # Scan PDFs for keywords
    all_mentions = []
    keyword_counts: dict[str, int] = defaultdict(int)

    print("\n🔎 Scanning and downloading PDFs with matches...")
    for link_info in unique_links:
        url = link_info["url"]
        filename = link_info["filename"]
        filepath = PDF_DIR / filename

        # Scan PDF
        matches, pdf_content, num_pages_scanned = stream_and_scan_pdf(
            url=url,
            keywords=keywords,
            max_pages=MAX_SCAN_PAGES,
        )

        if matches and pdf_content is not None:
            print(f"✅ Match found in {filename}, saving PDF...")
            logging.info(f"Match found in {filename}, saved to disk.")

            # Save PDF
            with open(filepath, "wb") as f:
                f.write(pdf_content)

            # Collect matches
            all_mentions.extend(matches)
            for match in matches:
                keyword_counts[match["keyword"]] += 1
        else:
            print(
                f"⏩ No match in {num_pages_scanned} pages of {filename}, skipping..."
            )
            logging.info(f"No match in {filename}, skipped.")

    # Save results to CSV
    if all_mentions:
        print(f"\n💾 Saving {len(all_mentions)} matches to CSV: {RESULT_CSV}")
        pd.DataFrame(all_mentions).to_csv(RESULT_CSV, index=False)
        logging.info(f"Results saved to {RESULT_CSV}")

        print("\n📊 Keyword Match Summary:")
        print("-------------------------")
        for keyword, count in sorted(
            keyword_counts.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"{keyword}: {count}")
    else:
        print("\n⚠️  No matches found across all PDFs.")
        print("   Consider adjusting keywords or DATE_RANGE.")

    print("\n✅ Done.")
    logging.info("Scraper finished successfully.")
    return 0


if __name__ == "__main__":
    exit(main())
