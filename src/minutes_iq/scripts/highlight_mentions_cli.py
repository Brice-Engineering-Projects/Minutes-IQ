#!/usr/bin/env python3
"""
Legacy CLI script for highlighting PDFs from CSV files.

This script provides backward compatibility with the old CSV-based workflow.
For new workflows, use the database-backed scraper service instead.

Usage:
    python -m minutes_iq.scripts.highlight_mentions_cli
"""

import glob
import os
from pathlib import Path

import pandas as pd

from minutes_iq.scraper.highlighter import batch_highlight_pdfs

# === Root path ===
BASE_DIR = Path(__file__).resolve().parents[3]  # Go up to project root
RAW_PDF_DIR = BASE_DIR / "data" / "raw_pdfs"
ANNOTATED_PDF_DIR = BASE_DIR / "data" / "annotated_pdfs"
MENTIONS_DIR = BASE_DIR / "data" / "processed"


def get_latest_csv() -> Path | None:
    """Find the most recent extracted_mentions CSV file."""
    files = sorted(
        glob.glob(str(MENTIONS_DIR / "extracted_mentions_*.csv")),
        key=os.path.getmtime,
        reverse=True,
    )
    return Path(files[0]) if files else None


def main():
    """Main CLI entry point."""
    # Ensure output directory exists
    ANNOTATED_PDF_DIR.mkdir(parents=True, exist_ok=True)

    # Find latest CSV file
    csv_path = get_latest_csv()
    if not csv_path:
        print("❌ No extracted_mentions_*.csv file found.")
        print("   Run the scraper first to generate match data.")
        return 1

    print(f"📄 Using mentions from: {csv_path.relative_to(BASE_DIR)}")

    # Load CSV
    try:
        df = pd.read_csv(csv_path)
    except pd.errors.EmptyDataError:
        print("⚠️  CSV file is empty - no matches were found by the scraper.")
        print(
            "   Try adjusting the DATE_RANGE or keywords, or increasing MAX_SCAN_PAGES."
        )
        return 1

    if df.empty:
        print("⚠️  No mentions found in CSV file.")
        return 1

    # Convert CSV data to matches format expected by highlighter
    df["file"] = df["file"].astype(str)
    matches_by_file = {}

    for pdf_name in df["file"].unique():
        pdf_matches = df[df["file"] == pdf_name]
        matches_by_file[pdf_name] = [
            {
                "page": int(row["page"]),
                "keyword": row["keyword"],
            }
            for _, row in pdf_matches.iterrows()
        ]

    # Batch highlight PDFs using new highlighter module
    print(f"\n🖍️  Highlighting {len(matches_by_file)} PDFs...")
    results = batch_highlight_pdfs(
        pdf_dir=RAW_PDF_DIR,
        output_dir=ANNOTATED_PDF_DIR,
        matches_by_file=matches_by_file,
    )

    # Print summary
    succeeded = sum(1 for success in results.values() if success)
    failed = len(results) - succeeded

    print("\n✅ Highlighting complete:")
    print(f"   - {succeeded} PDFs highlighted successfully")
    if failed > 0:
        print(f"   - {failed} PDFs failed (check logs for details)")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
