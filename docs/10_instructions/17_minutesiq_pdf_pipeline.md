# 📄 MinutesIQ – PDF Page Highlight & Download Pipeline (MVP)

## 1. Objective

Implement a backend feature that:

- Extracts **only relevant pages** from PDFs where keyword matches occur
- Applies **highlight annotations** to matched snippets
- Generates **individual page PDFs**
- Bundles results into a **downloadable ZIP file**
- Returns the ZIP file via a FastAPI endpoint

This complements the current CSV-only output with a **usable, actionable artifact**.

---

## 2. Key Design Principle

This feature is **ephemeral and request-based**.

- Files are generated **on demand**
- Stored temporarily in `/tmp` (or system temp directory)
- Returned immediately to the user
- No long-term storage required

---

## 3. Architecture Placement

This logic belongs in the **Service Layer**:

src/services/pdf_service.py

---

## 4. Processing Pipeline

### Input

- PDF file path
- List of matches:
  - page number
  - snippet text
  - keyword

### Output

- ZIP file containing highlighted PDF pages
- This is meant to be used with the current `Generate ZIP Artifact` UI component for download in the scraper/jobs/results page.

---

## 5. Temporary File Handling

Use Python's `tempfile` module:

import tempfile

temp_dir = tempfile.mkdtemp()

---

## 6. Example Implementation (Simplified)

```python
import os
import tempfile
import zipfile
from collections import defaultdict
from uuid import uuid4

import fitz  # PyMuPDF


# -----------------------------
# ZIP CREATION
# -----------------------------
def create_zip(file_paths: list[str], output_path: str) -> None:
    with zipfile.ZipFile(output_path, "w") as z:
        for file in file_paths:
            z.write(file, os.path.basename(file))


# -----------------------------
# PAGE EXTRACTION + HIGHLIGHT
# -----------------------------
def extract_and_highlight_page(
    doc: fitz.Document,
    pdf_name: str,
    page_number: int,
    snippet: str,
    keyword: str,
    output_dir: str,
) -> str:
    """
    Extract a single page, apply highlight, and save as new PDF.
    """

    # Create new PDF with just this page
    new_doc = fitz.open()
    new_doc.insert_pdf(doc, from_page=page_number, to_page=page_number)
    page = new_doc[0]

    # Try snippet match first
    text_instances = page.search_for(snippet)

    # Fallback to keyword if snippet fails
    if not text_instances and keyword:
        text_instances = page.search_for(keyword)

    # Apply highlights
    for inst in text_instances:
        highlight = page.add_highlight_annot(inst)
        highlight.update()

    # Unique filename to avoid collisions
    file_id = uuid4().hex[:8]
    output_path = os.path.join(
        output_dir,
        f"{pdf_name}_page_{page_number}_{file_id}.pdf",
    )

    new_doc.save(output_path)
    new_doc.close()

    return output_path


# -----------------------------
# MAIN ORCHESTRATOR
# -----------------------------
def generate_highlighted_pages(matches: list[dict]) -> str:
    """
    Main pipeline:
    - Groups matches by PDF
    - Extracts + highlights pages
    - Bundles into ZIP
    """

    temp_dir = tempfile.mkdtemp()
    output_files: list[str] = []

    # Group matches by PDF path
    pdf_groups: dict[str, list[dict]] = defaultdict(list)

    for match in matches:
        pdf_groups[match["pdf_path"]].append(match)

    # Process each PDF once
    for pdf_path, pdf_matches in pdf_groups.items():
        doc = fitz.open(pdf_path)
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]

        for match in pdf_matches:
            output_path = extract_and_highlight_page(
                doc=doc,
                pdf_name=pdf_name,
                page_number=match["page"],
                snippet=match.get("snippet", ""),
                keyword=match.get("keyword", ""),
                output_dir=temp_dir,
            )
            output_files.append(output_path)

        doc.close()

    # Create ZIP archive
    zip_path = os.path.join(temp_dir, "minutes_iq_results.zip")
    create_zip(output_files, zip_path)

    return zip_path
```

---

## 7. FastAPI Endpoint

GET /download-results

from fastapi.responses import FileResponse

def download_results():
    zip_path = generate_highlighted_pages(...)
    return FileResponse(path=zip_path, filename="minutes_iq_results.zip")

---

### Example Endpoint Usage

```python
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from src.services import pdf_service
from src.webapp.dependencies import get_current_user  # adjust if needed

router = APIRouter()


@router.get("/download-results")
def download_results(current_user=Depends(get_current_user)):
    """
    Generate and return ZIP of highlighted PDF pages.
    """

    # TODO: Replace this with real match retrieval logic
    matches = [
        {
            "pdf_path": "/path/to/file1.pdf",
            "page": 2,
            "snippet": "stormwater improvements",
            "keyword": "stormwater",
        },
        {
            "pdf_path": "/path/to/file1.pdf",
            "page": 5,
            "snippet": "lift station upgrade",
            "keyword": "lift station",
        },
    ]

    zip_path = pdf_service.generate_highlighted_pages(matches)

    return FileResponse(
        path=zip_path,
        filename="minutes_iq_results.zip",
        media_type="application/zip",
    )
```

---

## 8. Definition of Done

- User downloads ZIP
- ZIP contains highlighted relevant pages
- No server file access required

---

## 9. Summary

This feature transforms MinutesIQ into an actionable intelligence tool.
