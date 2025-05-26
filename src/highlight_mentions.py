# src/highlight_mentions.py

"""
Highlight Matched Keywords in PDFs
- Loads the latest extracted_mentions CSV
- Reopens the original PDF
- Highlights matched keywords on the indicated page
- Saves a new copy in data/annotated_pdfs/
"""

import os
import glob
import pandas as pd
import fitz  # PyMuPDF
from pathlib import Path

# === Root path ===
BASE_DIR = Path(__file__).resolve().parents[1]
RAW_PDF_DIR = BASE_DIR / "data" / "raw_pdfs"
ANNOTATED_PDF_DIR = BASE_DIR / "data" / "annotated_pdfs"
MENTIONS_DIR = BASE_DIR / "data" / "processed"
ANNOTATED_PDF_DIR.mkdir(parents=True, exist_ok=True)

# === Load the latest extracted_mentions CSV ===
def get_latest_csv():
    files = sorted(glob.glob(str(MENTIONS_DIR / "extracted_mentions_*.csv")), key=os.path.getmtime, reverse=True)
    return Path(files[0]) if files else None

# === Highlight Matches in PDFs ===
def highlight_pdf(file_path, mentions):
    pdf_path = RAW_PDF_DIR / file_path
    annotated_path = ANNOTATED_PDF_DIR / file_path.replace(".pdf", "_annotated.pdf")

    if not pdf_path.exists():
        print(f"⚠️ PDF not found: {pdf_path}")
        return

    doc = fitz.open(pdf_path)

    for _, row in mentions.iterrows():
        page_num = int(row['page']) - 1
        keyword = row['keyword']
        try:
            page = doc[page_num]
            text_instances = page.search_for(keyword, quads=True)
            for inst in text_instances:
                annot = page.add_highlight_annot(inst)
                annot.update()
        except Exception as e:
            print(f"❌ Could not highlight '{keyword}' on page {page_num+1} in {file_path}: {e}")

    doc.save(annotated_path)
    doc.close()
    print(f"✅ Highlighted and saved: {annotated_path.relative_to(BASE_DIR)}")

# === Main ===
def main():
    csv_path = get_latest_csv()
    if not csv_path:
        print("❌ No extracted_mentions_*.csv file found.")
        return

    print(f"📄 Using mentions from: {csv_path.relative_to(BASE_DIR)}")
    df = pd.read_csv(csv_path)
    df['file'] = df['file'].astype(str)

    for pdf_name in df['file'].unique():
        mentions = df[df['file'] == pdf_name]
        highlight_pdf(pdf_name, mentions)

if __name__ == "__main__":
    main()
