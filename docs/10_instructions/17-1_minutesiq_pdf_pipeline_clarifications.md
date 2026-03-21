# 📄 MinutesIQ – PDF Page Highlight & Download Pipeline (MVP) - Clarifications

This document provides clarifications and additional details for the implementation of the PDF page highlight and download pipeline as outlined in the main instructions.

## 1. Source of matches

- Matches must be retrieved server-side from an existing job/result record.
- The frontend will pass a job_id or result_id, not raw match data.

## 2. Page numbering convention

- Stored page numbers are 1-based.
- Convert to 0-based when calling PyMuPDF:
- page_index = stored_page - 1

## 3. Multiple matches on the same page

- If multiple matches occur on the same page, generate a single PDF page and apply all highlights.
- Do not generate duplicate PDFs for the same page.

## 4. Snippet matching behavior

- Attempt full snippet match first.
- If no matches are found, fallback to keyword-based highlighting.
- If both fail, still include the page without highlights (optional but recommended).

## 5. Authorization scope

- Users may only download artifacts for jobs they own.
- Admins may access all jobs.
- Authorization must be enforced before generating the ZIP.

## 6. Temporary file cleanup

- Temporary files do not need to be explicitly deleted during request handling and may remain in /tmp.
- Cleanup can be handled by the OS or container lifecycle.
- Optional: implement periodic cleanup later.

## 7. Actual Module Location

Place implementation in:
src/minutes_iq/services/pdf_service.py

The path in this document is conceptual and must be adapted to the existing package structure.

## 8. Match grouping requirement

- Matches must be grouped by (pdf_path, page_number) before processing.
- Each (pdf_path, page_number) combination should produce exactly one output PDF.
- All snippets/keywords for that page must be applied to the same output page.

## 9. Snippet normalization

- Snippet matching may fail due to PDF text inconsistencies.
- Implement basic normalization if needed:
  - strip extra whitespace
  - collapse line breaks
  - trim long snippets

## 10. File naming

- Output filenames must be unique to prevent overwriting.
- Include at least:
  - PDF name
  - page number
  - unique identifier (e.g., UUID suffix)

## 11. Endpoint contract

- Endpoint: GET /download-results/{job_id}
- Backend must:
  1. Validate user access to job_id
  2. Retrieve matches from database
  3. Generate ZIP artifact
  4. Return ZIP as FileResponse
