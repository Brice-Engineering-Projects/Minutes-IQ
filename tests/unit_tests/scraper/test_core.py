"""
Unit tests for scraper core functions.
"""

from unittest.mock import Mock, patch

from minutes_iq.scraper.core import (
    download_pdf,
    extract_entities,
    get_safe_filename,
    scrape_pdf_links,
    stream_and_scan_pdf,
)


class TestGetSafeFilename:
    """Test filename generation from URLs."""

    def test_normal_url(self):
        """Test with normal PDF URL."""
        url = "https://example.com/meeting_2024-01-15.pdf"
        filename = get_safe_filename(url)
        assert filename == "meeting_2024-01-15.pdf"

    def test_url_without_extension(self):
        """Test URL without .pdf extension."""
        url = "https://example.com/document"
        filename = get_safe_filename(url)
        assert filename.endswith(".pdf")

    def test_url_with_special_chars(self):
        """Test URL with special characters."""
        url = "https://example.com/meeting@2024!.pdf"
        filename = get_safe_filename(url)
        assert "@" not in filename
        assert "!" not in filename

    def test_url_trailing_slash(self):
        """Test URL with trailing slash."""
        url = "https://example.com/path/"
        filename = get_safe_filename(url)
        assert filename.startswith("unknown_")
        assert filename.endswith(".pdf")


class TestScrapePdfLinks:
    """Test PDF link scraping."""

    @patch("minutes_iq.scraper.core.requests.get")
    def test_scrape_minutes_pdfs(self, mock_get):
        """Test scraping minutes PDFs."""
        mock_response = Mock()
        mock_response.text = """
        <html>
            <table>
                <tr>
                    <td><a href="/docs/minutes_2024-01-15.pdf">Board Minutes</a></td>
                </tr>
            </table>
        </html>
        """
        mock_get.return_value = mock_response

        links = scrape_pdf_links(
            base_url="https://example.com/meetings",
            include_minutes=True,
            include_packages=False,
        )

        assert len(links) > 0
        assert any("minutes" in link["filename"].lower() for link in links)

    @patch("minutes_iq.scraper.core.requests.get")
    def test_scrape_with_date_filter(self, mock_get):
        """Test scraping with date range filter."""
        mock_response = Mock()
        mock_response.text = """
        <html>
            <table>
                <tr>
                    <td><a href="/docs/minutes_2024-01-15.pdf">Minutes Jan</a></td>
                    <td><a href="/docs/minutes_2024-06-20.pdf">Minutes Jun</a></td>
                    <td><a href="/docs/minutes_2025-01-10.pdf">Minutes 2025</a></td>
                </tr>
            </table>
        </html>
        """
        mock_get.return_value = mock_response

        links = scrape_pdf_links(
            base_url="https://example.com/meetings",
            date_range_start="2024-01",
            date_range_end="2024-12",
        )

        # Should only include 2024 PDFs
        for link in links:
            if link["date_str"]:
                assert link["date_str"].startswith("2024")

    @patch("minutes_iq.scraper.core.requests.get")
    def test_scrape_handles_network_error(self, mock_get):
        """Test handling of network errors."""
        mock_get.side_effect = Exception("Network error")

        links = scrape_pdf_links(base_url="https://example.com/meetings")

        assert links == []


class TestStreamAndScanPdf:
    """Test PDF streaming and keyword matching."""

    @patch("minutes_iq.scraper.core.requests.get")
    @patch("minutes_iq.scraper.core.pdfplumber.open")
    def test_scan_pdf_with_matches(self, mock_pdf_open, mock_get):
        """Test scanning PDF with keyword matches."""
        # Mock PDF response
        mock_response = Mock()
        mock_response.content = b"fake pdf content"
        mock_get.return_value = mock_response

        # Mock PDF pages
        mock_page = Mock()
        mock_page.extract_text.return_value = (
            "This is a test document with important keyword here."
        )

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)

        mock_pdf_open.return_value = mock_pdf

        keywords = ["important", "test"]
        matches, pdf_content, pages_scanned = stream_and_scan_pdf(
            url="https://example.com/test.pdf",
            keywords=keywords,
        )

        assert len(matches) >= 2  # Should match both keywords
        assert pdf_content is not None
        assert pages_scanned == 1

    @patch("minutes_iq.scraper.core.requests.get")
    @patch("minutes_iq.scraper.core.pdfplumber.open")
    def test_scan_pdf_no_matches(self, mock_pdf_open, mock_get):
        """Test scanning PDF with no keyword matches."""
        mock_response = Mock()
        mock_response.content = b"fake pdf content"
        mock_get.return_value = mock_response

        mock_page = Mock()
        mock_page.extract_text.return_value = "This is a test document."

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)

        mock_pdf_open.return_value = mock_pdf

        keywords = ["nonexistent"]
        matches, pdf_content, pages_scanned = stream_and_scan_pdf(
            url="https://example.com/test.pdf",
            keywords=keywords,
        )

        assert len(matches) == 0
        assert pdf_content is None  # Should not return content if no matches
        assert pages_scanned == 1

    @patch("minutes_iq.scraper.core.requests.get")
    @patch("minutes_iq.scraper.core.pdfplumber.open")
    def test_scan_pdf_with_max_pages(self, mock_pdf_open, mock_get):
        """Test scanning PDF with max_pages limit."""
        mock_response = Mock()
        mock_response.content = b"fake pdf content"
        mock_get.return_value = mock_response

        # Create 10 pages
        mock_pages = [Mock() for _ in range(10)]
        for page in mock_pages:
            page.extract_text.return_value = "Test content with keyword."

        mock_pdf = Mock()
        mock_pdf.pages = mock_pages
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)

        mock_pdf_open.return_value = mock_pdf

        keywords = ["keyword"]
        matches, pdf_content, pages_scanned = stream_and_scan_pdf(
            url="https://example.com/test.pdf",
            keywords=keywords,
            max_pages=3,
        )

        assert pages_scanned == 3  # Should only scan first 3 pages

    @patch("minutes_iq.scraper.core.requests.get")
    def test_scan_pdf_handles_error(self, mock_get):
        """Test error handling during PDF scan."""
        mock_get.side_effect = Exception("Download failed")

        keywords = ["test"]
        matches, pdf_content, pages_scanned = stream_and_scan_pdf(
            url="https://example.com/test.pdf",
            keywords=keywords,
        )

        assert matches == []
        assert pdf_content is None
        assert pages_scanned == 0


class TestExtractEntities:
    """Test NLP entity extraction."""

    def test_extract_entities_with_names(self):
        """Test extracting entities from text with person names."""
        text = "John Smith met with NASA officials in Washington."
        entities = extract_entities(text)

        assert isinstance(entities, str)
        # spaCy should detect PERSON and ORG entities
        assert len(entities) > 0

    def test_extract_entities_empty_text(self):
        """Test with empty text."""
        entities = extract_entities("")
        assert entities == ""

    def test_extract_entities_no_entities(self):
        """Test with text containing no entities."""
        text = "This is a simple sentence."
        entities = extract_entities(text)
        # May be empty or contain minimal entities
        assert isinstance(entities, str)


class TestDownloadPdf:
    """Test PDF download functionality."""

    @patch("minutes_iq.scraper.core.requests.get")
    @patch("builtins.open", create=True)
    def test_download_pdf_success(self, mock_open, mock_get):
        """Test successful PDF download."""
        mock_response = Mock()
        mock_response.content = b"fake pdf content"
        mock_get.return_value = mock_response

        mock_file = Mock()
        mock_open.return_value.__enter__ = Mock(return_value=mock_file)
        mock_open.return_value.__exit__ = Mock(return_value=False)

        success = download_pdf(
            url="https://example.com/test.pdf",
            filepath="/tmp/test.pdf",
        )

        assert success is True
        mock_file.write.assert_called_once_with(b"fake pdf content")

    @patch("minutes_iq.scraper.core.requests.get")
    def test_download_pdf_network_error(self, mock_get):
        """Test download with network error."""
        mock_get.side_effect = Exception("Network error")

        success = download_pdf(
            url="https://example.com/test.pdf",
            filepath="/tmp/test.pdf",
        )

        assert success is False

    @patch("minutes_iq.scraper.core.requests.get")
    @patch("builtins.open", create=True)
    def test_download_pdf_file_error(self, mock_open, mock_get):
        """Test download with file write error."""
        mock_response = Mock()
        mock_response.content = b"fake pdf content"
        mock_get.return_value = mock_response

        mock_open.side_effect = OSError("Permission denied")

        success = download_pdf(
            url="https://example.com/test.pdf",
            filepath="/tmp/test.pdf",
        )

        assert success is False
