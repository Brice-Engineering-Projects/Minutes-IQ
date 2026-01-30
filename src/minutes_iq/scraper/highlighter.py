"""
PDF highlighting functions for Minutes IQ.
Refactored from highlight_mentions.py for database-backed operations.
"""

import logging
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


def highlight_pdf(
    pdf_path: str | Path,
    output_path: str | Path,
    matches: list[dict[str, Any]],
) -> bool:
    """
    Add highlights to a PDF based on keyword matches.

    Args:
        pdf_path: Path to the source PDF file
        output_path: Path to save the annotated PDF
        matches: List of match dicts with keys: page (1-indexed), keyword

    Returns:
        True if successful, False otherwise
    """
    pdf_path = Path(pdf_path)
    output_path = Path(output_path)

    if not pdf_path.exists():
        logger.error(f"PDF not found: {pdf_path}")
        return False

    try:
        doc = fitz.open(pdf_path)
        highlight_pages = set()

        # Process each match
        for match in matches:
            page_num = int(match["page"]) - 1  # Convert to 0-indexed
            keyword = match["keyword"]

            try:
                page = doc[page_num]
                # Search for keyword instances in the page
                text_instances = page.search_for(keyword, quads=True)

                for inst in text_instances:
                    # Add highlight annotation
                    annot = page.add_highlight_annot(inst)
                    annot.update()
                    highlight_pages.add(page_num)

            except IndexError:
                logger.warning(f"Page {page_num + 1} out of range in {pdf_path.name}")
            except Exception as e:
                logger.error(
                    f"Could not highlight '{keyword}' on page {page_num + 1} "
                    f"in {pdf_path.name}: {e}"
                )

        # Add bookmarks for highlighted pages
        if highlight_pages:
            add_bookmarks(doc, highlight_pages)

        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save annotated PDF
        doc.save(output_path)
        doc.close()

        logger.info(
            f"Highlighted {len(highlight_pages)} pages in {pdf_path.name}, "
            f"saved to {output_path}"
        )
        return True

    except Exception as e:
        logger.error(f"Error highlighting PDF {pdf_path}: {e}")
        return False


def add_bookmarks(doc: fitz.Document, highlight_pages: set[int]) -> None:
    """
    Add bookmarks/outline entries for highlighted pages.

    Args:
        doc: The PyMuPDF Document object
        highlight_pages: Set of 0-indexed page numbers that were highlighted
    """
    try:
        toc = doc.get_toc()

        # Determine bookmark level based on existing TOC
        # If TOC is empty, use level 1; otherwise use level 2
        level = 1 if not toc else 2

        # Create bookmark entries for each highlighted page
        new_entries = [
            [level, f"Highlight {idx + 1} (Page {pnum + 1})", pnum]
            for idx, pnum in enumerate(sorted(highlight_pages))
        ]

        # Add new entries to existing TOC
        doc.set_toc(toc + new_entries)
        logger.debug(f"Added {len(new_entries)} bookmarks to document")

    except Exception as e:
        logger.error(f"Error adding bookmarks: {e}")


def batch_highlight_pdfs(
    pdf_dir: str | Path,
    output_dir: str | Path,
    matches_by_file: dict[str, list[dict[str, Any]]],
) -> dict[str, bool]:
    """
    Highlight multiple PDFs in batch.

    Args:
        pdf_dir: Directory containing source PDFs
        output_dir: Directory to save annotated PDFs
        matches_by_file: Dict mapping filename to list of matches

    Returns:
        Dict mapping filename to success status (True/False)
    """
    pdf_dir = Path(pdf_dir)
    output_dir = Path(output_dir)
    results = {}

    for filename, matches in matches_by_file.items():
        pdf_path = pdf_dir / filename
        output_path = output_dir / filename.replace(".pdf", "_annotated.pdf")

        success = highlight_pdf(pdf_path, output_path, matches)
        results[filename] = success

    return results


def highlight_job_results(
    job_id: int,
    pdf_dir: str | Path,
    output_base_dir: str | Path,
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Highlight PDFs for all results from a scrape job.

    Args:
        job_id: The scrape job ID
        pdf_dir: Directory containing source PDFs
        output_base_dir: Base directory for annotated PDFs
        results: List of scrape results from database

    Returns:
        Dict with summary: files_processed, files_succeeded, files_failed
    """
    pdf_dir = Path(pdf_dir)
    output_dir = Path(output_base_dir) / str(job_id)

    # Group results by filename
    matches_by_file = {}
    for result in results:
        filename = result["pdf_filename"]
        if filename not in matches_by_file:
            matches_by_file[filename] = []

        matches_by_file[filename].append(
            {
                "page": result["page_number"],
                "keyword": result["keyword"],
            }
        )

    logger.info(
        f"Highlighting {len(matches_by_file)} PDFs for job {job_id} "
        f"with {len(results)} total matches"
    )

    # Batch highlight all PDFs
    highlight_results = batch_highlight_pdfs(pdf_dir, output_dir, matches_by_file)

    # Calculate summary
    files_succeeded = sum(1 for success in highlight_results.values() if success)
    files_failed = len(highlight_results) - files_succeeded

    summary = {
        "files_processed": len(highlight_results),
        "files_succeeded": files_succeeded,
        "files_failed": files_failed,
        "output_dir": str(output_dir),
    }

    logger.info(
        f"Highlighting complete for job {job_id}: "
        f"{files_succeeded} succeeded, {files_failed} failed"
    )

    return summary
