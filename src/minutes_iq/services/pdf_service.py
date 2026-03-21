"""PDF page extraction, highlighting, and ZIP artifact generation."""

from __future__ import annotations

import re
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path
from uuid import uuid4

import fitz


def normalize_snippet(snippet: str, max_length: int = 500) -> str:
    """Normalize snippet text for more resilient PDF text matching."""
    normalized = re.sub(r"\s+", " ", snippet).strip()
    if len(normalized) > max_length:
        return normalized[:max_length]
    return normalized


def _safe_filename(value: str) -> str:
    """Build a safe filename segment from arbitrary text."""
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "document"


def _find_text_instances(
    page: fitz.Page, snippets: list[str], keywords: list[str]
) -> list:
    """Search the page for snippets first, then fallback to keywords."""
    text_instances = []

    for snippet in snippets:
        normalized = normalize_snippet(snippet)
        if normalized:
            text_instances.extend(page.search_for(normalized))

    if text_instances:
        return text_instances

    for keyword in keywords:
        keyword_value = keyword.strip()
        if keyword_value:
            text_instances.extend(page.search_for(keyword_value))

    return text_instances


def _extract_single_page_pdf(
    source_doc: fitz.Document,
    source_page_index: int,
) -> tuple[fitz.Document, fitz.Page]:
    """Create a one-page PDF document from the source page."""
    single_page_doc = fitz.open()
    single_page_doc.insert_pdf(
        source_doc,
        from_page=source_page_index,
        to_page=source_page_index,
    )
    return single_page_doc, single_page_doc[0]


def _write_zip(files: list[Path], output_path: Path) -> None:
    """Write output files into a ZIP archive."""
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_path in files:
            archive.write(file_path, arcname=file_path.name)


def generate_highlighted_pages_zip(
    *,
    job_id: int,
    matches: list[dict],
    raw_pdf_base_dir: Path,
) -> str:
    """Generate a ZIP file of highlighted one-page PDFs for a scrape job.

    Grouping rules:
    - Group by (pdf_path, page_number)
    - Produce exactly one output PDF for each group
    - Apply all snippet/keyword highlights for that page in one output file

    Matching rules:
    - Try snippet matches first
    - Fallback to keyword matching
    - If both fail, include the page without highlights
    """
    if not matches:
        raise ValueError("No matches provided for ZIP generation")

    temp_dir = Path(tempfile.mkdtemp(prefix=f"minutes_iq_job_{job_id}_"))
    output_files: list[Path] = []

    grouped_matches: dict[tuple[Path, int], list[dict]] = defaultdict(list)
    for match in matches:
        pdf_path = raw_pdf_base_dir / match["pdf_filename"]
        page_number = int(match["page_number"])
        grouped_matches[(pdf_path, page_number)].append(match)

    for (pdf_path, page_number), page_matches in grouped_matches.items():
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        source_doc = fitz.open(pdf_path)
        try:
            page_index = page_number - 1
            if page_index < 0 or page_index >= source_doc.page_count:
                raise ValueError(
                    f"Invalid page number {page_number} for file {pdf_path.name}"
                )

            single_page_doc, single_page = _extract_single_page_pdf(
                source_doc, page_index
            )
            try:
                snippets = [m.get("snippet", "") for m in page_matches]
                keywords = [m.get("keyword", "") for m in page_matches]
                text_instances = _find_text_instances(single_page, snippets, keywords)

                for instance in text_instances:
                    highlight = single_page.add_highlight_annot(instance)
                    highlight.update()

                unique_suffix = uuid4().hex[:8]
                base_name = _safe_filename(pdf_path.stem)
                output_path = temp_dir / (
                    f"{base_name}_page_{page_number}_{unique_suffix}.pdf"
                )

                single_page_doc.save(str(output_path))
                output_files.append(output_path)
            finally:
                single_page_doc.close()
        finally:
            source_doc.close()

    zip_path = temp_dir / "minutes_iq_results.zip"
    _write_zip(output_files, zip_path)
    return str(zip_path)
