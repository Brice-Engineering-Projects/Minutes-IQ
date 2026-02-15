"""
Core scraper functions for Minutes IQ.
Refactored from jea_minutes_scraper.py for database-backed orchestration.
"""

import hashlib
import logging
import re
from io import BytesIO
from typing import Any

import pdfplumber
import requests
import spacy
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# === NLP SETUP ===
# Lazy load spaCy model to avoid loading during import
_nlp: Any = None


def _get_nlp() -> Any:
    """Lazy load spaCy model."""
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning(
                "spaCy model 'en_core_web_sm' not found. "
                "Entity extraction will be disabled. "
                "Install with: python -m spacy download en_core_web_sm"
            )
            _nlp = False  # Mark as unavailable
    return _nlp if _nlp is not False else None


def get_safe_filename(url: str) -> str:
    """
    Generate a safe filename from a PDF URL.

    Args:
        url: The PDF URL

    Returns:
        A safe filename string
    """
    tail = url.rstrip("/").split("/")[-1]
    if not tail:
        hash_str = hashlib.md5(url.encode()).hexdigest()[:8]
        return f"unknown_{hash_str}.pdf"
    else:
        tail = re.sub(r"[^a-zA-Z0-9_.-]", "_", tail)
        return f"{tail}.pdf" if not tail.endswith(".pdf") else tail


def scrape_pdf_links(
    base_url: str,
    date_range_start: str | None = None,
    date_range_end: str | None = None,
    include_minutes: bool = True,
    include_packages: bool = True,
    timeout: int = 30,
) -> list[dict[str, Any]]:
    """
    Scrape PDF links from a given URL.

    Args:
        base_url: The URL to scrape for PDF links
        date_range_start: Start date in YYYY-MM format (optional)
        date_range_end: End date in YYYY-MM format (optional)
        include_minutes: Whether to include 'minutes' PDFs
        include_packages: Whether to include 'package' PDFs
        timeout: Request timeout in seconds

    Returns:
        List of dicts with keys: url, filename, date_str (YYYY-MM or None)
    """
    try:
        response = requests.get(base_url, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {base_url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    pdf_links = []

    for row in soup.find_all("tr"):
        for a_tag in row.find_all("a", href=True):
            text = a_tag.get_text(strip=True).lower()
            href = str(a_tag["href"])

            # Filter by document type
            if not (
                (include_minutes and "minutes" in text)
                or (include_packages and "package" in text)
            ):
                continue

            # Build full URL
            full_link = (
                href if href.startswith("http") else f"https://www.jea.com{href}"
            )
            filename = get_safe_filename(full_link)

            # Extract date from filename
            date_match = re.search(r"(20\d{2})[\-_](\d{2})[\-_](\d{2})", filename)
            date_str = None
            if date_match:
                y, m = date_match.groups()[0], date_match.groups()[1]
                date_str = f"{y}-{m}"

            # Apply date range filter if specified
            if date_range_start and date_range_end:
                # Skip if we couldn't extract a date
                if not date_str:
                    continue
                # Skip if date is outside range
                if not (date_range_start <= date_str <= date_range_end):
                    continue

            pdf_links.append(
                {
                    "url": full_link,
                    "filename": filename,
                    "date_str": date_str,
                }
            )

    return pdf_links


def stream_and_scan_pdf(
    url: str,
    keywords: list[str],
    max_pages: int | None = None,
    timeout: int = 60,
) -> tuple[list[dict[str, Any]], bytes | None, int]:
    """
    Stream a PDF and search for keyword matches.

    Args:
        url: The PDF URL to stream
        keywords: List of keywords to search for
        max_pages: Maximum number of pages to scan (None = all pages)
        timeout: Request timeout in seconds

    Returns:
        Tuple of (matches, pdf_content, pages_scanned)
        - matches: List of dicts with keys: filename, page, keyword, snippet, entities
        - pdf_content: PDF bytes if matches found, else None
        - pages_scanned: Number of pages scanned
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        pdf_bytes = BytesIO(response.content)

        with pdfplumber.open(pdf_bytes) as pdf:
            matches = []
            pages_to_scan = pdf.pages if max_pages is None else pdf.pages[:max_pages]

            for i, page in enumerate(pages_to_scan):
                text = page.extract_text() or ""

                for keyword in keywords:
                    if keyword.lower() in text.lower():
                        # Extract context snippet
                        start_idx = text.lower().find(keyword.lower())
                        context_snippet = text[start_idx:][:300]

                        # Extract entities using NLP
                        entities = extract_entities(context_snippet)

                        matches.append(
                            {
                                "filename": get_safe_filename(url),
                                "page": i + 1,
                                "keyword": keyword,
                                "snippet": context_snippet.strip(),
                                "entities": entities,
                            }
                        )

            # Return PDF bytes only if matches were found
            pdf_content = response.content if matches else None
            return matches, pdf_content, len(pages_to_scan)

    except requests.RequestException as e:
        logger.error(f"Failed to fetch PDF {url}: {e}")
        return [], None, 0
    except Exception as e:
        logger.error(f"Error processing PDF {url}: {e}")
        return [], None, 0


def extract_entities(text: str) -> str:
    """
    Extract named entities from text using spaCy NLP.

    Args:
        text: The text to extract entities from

    Returns:
        Comma-separated string of entities with labels (e.g., "John (PERSON), NASA (ORG)")
    """
    nlp = _get_nlp()
    if nlp is None:
        # spaCy model not available
        return ""

    try:
        doc = nlp(text)
        entities = ", ".join(f"{ent.text} ({ent.label_})" for ent in doc.ents)
        return entities
    except Exception as e:
        logger.error(f"Error extracting entities: {e}")
        return ""


def download_pdf(url: str, filepath: str, timeout: int = 60) -> bool:
    """
    Download a PDF from a URL and save to disk.

    Args:
        url: The PDF URL
        filepath: The local file path to save to
        timeout: Request timeout in seconds

    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            f.write(response.content)

        logger.info(f"Downloaded PDF to {filepath}")
        return True

    except requests.RequestException as e:
        logger.error(f"Failed to download PDF {url}: {e}")
        return False
    except OSError as e:
        logger.error(f"Failed to save PDF to {filepath}: {e}")
        return False
