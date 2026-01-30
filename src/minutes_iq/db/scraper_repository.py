"""
Repository layer for scraper job database operations.
"""

import json
import logging
from datetime import datetime
from typing import Any

from libsql_experimental import Connection

logger = logging.getLogger(__name__)


class ScraperRepository:
    """Repository for scraper job data access."""

    def __init__(self, conn: Connection):
        self.conn = conn

    def create_job(
        self,
        client_id: int,
        created_by: int,
        status: str = "pending",
    ) -> int:
        """
        Create a new scrape job.

        Args:
            client_id: The client ID to scrape for
            created_by: The user ID who created the job
            status: Initial job status (default: pending)

        Returns:
            The job_id of the created job
        """
        cursor = self.conn.execute(
            """
            INSERT INTO scrape_jobs (client_id, status, created_by, created_at)
            VALUES (?, ?, ?, ?)
            RETURNING job_id
            """,
            (client_id, status, created_by, int(datetime.now().timestamp())),
        )
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else 0

    def create_job_config(
        self,
        job_id: int,
        date_range_start: str | None = None,
        date_range_end: str | None = None,
        max_scan_pages: int | None = None,
        include_minutes: bool = True,
        include_packages: bool = True,
    ) -> int:
        """
        Create configuration for a scrape job.

        Args:
            job_id: The job ID
            date_range_start: Start date in YYYY-MM format
            date_range_end: End date in YYYY-MM format
            max_scan_pages: Maximum pages to scan per PDF
            include_minutes: Whether to include minutes PDFs
            include_packages: Whether to include package PDFs

        Returns:
            The config_id of the created config
        """
        cursor = self.conn.execute(
            """
            INSERT INTO scrape_job_config (
                job_id, date_range_start, date_range_end,
                max_scan_pages, include_minutes, include_packages
            )
            VALUES (?, ?, ?, ?, ?, ?)
            RETURNING config_id
            """,
            (
                job_id,
                date_range_start,
                date_range_end,
                max_scan_pages,
                1 if include_minutes else 0,
                1 if include_packages else 0,
            ),
        )
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else 0

    def update_job_status(
        self,
        job_id: int,
        status: str,
        error_message: str | None = None,
    ) -> None:
        """
        Update the status of a scrape job.

        Args:
            job_id: The job ID
            status: The new status (pending, running, completed, failed, cancelled)
            error_message: Optional error message if status is failed
        """
        timestamp = int(datetime.now().timestamp())

        if status == "running":
            self.conn.execute(
                """
                UPDATE scrape_jobs
                SET status = ?, started_at = ?
                WHERE job_id = ?
                """,
                (status, timestamp, job_id),
            )
        elif status in ("completed", "failed", "cancelled"):
            self.conn.execute(
                """
                UPDATE scrape_jobs
                SET status = ?, completed_at = ?, error_message = ?
                WHERE job_id = ?
                """,
                (status, timestamp, error_message, job_id),
            )
        else:
            self.conn.execute(
                """
                UPDATE scrape_jobs
                SET status = ?
                WHERE job_id = ?
                """,
                (status, job_id),
            )

        self.conn.commit()

    def save_result(
        self,
        job_id: int,
        pdf_filename: str,
        page_number: int,
        keyword_id: int,
        snippet: str,
        entities: dict[str, Any] | str | None = None,
    ) -> int:
        """
        Save a scrape result to the database.

        Args:
            job_id: The job ID
            pdf_filename: The PDF filename
            page_number: The page number where match was found
            keyword_id: The keyword ID that matched
            snippet: The text snippet containing the match
            entities: NLP entities extracted from the snippet (dict or string)

        Returns:
            The result_id of the created result
        """
        # Convert entities to JSON string if it's a dict
        entities_json = None
        if entities:
            if isinstance(entities, dict):
                entities_json = json.dumps(entities)
            else:
                entities_json = str(entities)

        cursor = self.conn.execute(
            """
            INSERT INTO scrape_results (
                job_id, pdf_filename, page_number,
                keyword_id, snippet, entities_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            RETURNING result_id
            """,
            (
                job_id,
                pdf_filename,
                page_number,
                keyword_id,
                snippet,
                entities_json,
                int(datetime.now().timestamp()),
            ),
        )
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else 0

    def get_job(self, job_id: int) -> dict[str, Any] | None:
        """
        Get a scrape job by ID.

        Args:
            job_id: The job ID

        Returns:
            Dict with job details or None if not found
        """
        cursor = self.conn.execute(
            """
            SELECT job_id, client_id, status, created_by,
                   created_at, started_at, completed_at, error_message
            FROM scrape_jobs
            WHERE job_id = ?
            """,
            (job_id,),
        )
        row = cursor.fetchone()
        cursor.close()

        if not row:
            return None

        return {
            "job_id": row[0],
            "client_id": row[1],
            "status": row[2],
            "created_by": row[3],
            "created_at": row[4],
            "started_at": row[5],
            "completed_at": row[6],
            "error_message": row[7],
        }

    def get_job_config(self, job_id: int) -> dict[str, Any] | None:
        """
        Get configuration for a scrape job.

        Args:
            job_id: The job ID

        Returns:
            Dict with config details or None if not found
        """
        cursor = self.conn.execute(
            """
            SELECT config_id, job_id, date_range_start, date_range_end,
                   max_scan_pages, include_minutes, include_packages
            FROM scrape_job_config
            WHERE job_id = ?
            """,
            (job_id,),
        )
        row = cursor.fetchone()
        cursor.close()

        if not row:
            return None

        return {
            "config_id": row[0],
            "job_id": row[1],
            "date_range_start": row[2],
            "date_range_end": row[3],
            "max_scan_pages": row[4],
            "include_minutes": bool(row[5]),
            "include_packages": bool(row[6]),
        }

    def get_job_results(self, job_id: int) -> list[dict[str, Any]]:
        """
        Get all results for a scrape job.

        Args:
            job_id: The job ID

        Returns:
            List of result dicts
        """
        cursor = self.conn.execute(
            """
            SELECT r.result_id, r.job_id, r.pdf_filename, r.page_number,
                   r.keyword_id, k.keyword, r.snippet, r.entities_json, r.created_at
            FROM scrape_results r
            JOIN keywords k ON r.keyword_id = k.keyword_id
            WHERE r.job_id = ?
            ORDER BY r.created_at DESC
            """,
            (job_id,),
        )
        rows = cursor.fetchall()
        cursor.close()

        results = []
        for row in rows:
            results.append(
                {
                    "result_id": row[0],
                    "job_id": row[1],
                    "pdf_filename": row[2],
                    "page_number": row[3],
                    "keyword_id": row[4],
                    "keyword": row[5],
                    "snippet": row[6],
                    "entities_json": row[7],
                    "created_at": row[8],
                }
            )

        return results

    def get_client_keywords(self, client_id: int) -> list[dict[str, Any]]:
        """
        Get all active keywords for a client.

        Args:
            client_id: The client ID

        Returns:
            List of keyword dicts with keyword_id and keyword text
        """
        cursor = self.conn.execute(
            """
            SELECT k.keyword_id, k.keyword
            FROM keywords k
            JOIN client_keywords ck ON k.keyword_id = ck.keyword_id
            WHERE ck.client_id = ? AND k.is_active = 1
            ORDER BY k.keyword
            """,
            (client_id,),
        )
        rows = cursor.fetchall()
        cursor.close()

        return [{"keyword_id": row[0], "keyword": row[1]} for row in rows]

    def list_jobs(
        self,
        user_id: int | None = None,
        client_id: int | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        List scrape jobs with optional filtering.

        Args:
            user_id: Filter by user who created the job
            client_id: Filter by client
            status: Filter by job status
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip

        Returns:
            List of job dicts
        """
        query = """
            SELECT j.job_id, j.client_id, c.name as client_name,
                   j.status, j.created_by, j.created_at,
                   j.started_at, j.completed_at, j.error_message
            FROM scrape_jobs j
            JOIN clients c ON j.client_id = c.client_id
            WHERE 1=1
        """
        params = []

        if user_id is not None:
            query += " AND j.created_by = ?"
            params.append(user_id)

        if client_id is not None:
            query += " AND j.client_id = ?"
            params.append(client_id)

        if status is not None:
            query += " AND j.status = ?"
            params.append(status)

        query += " ORDER BY j.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = self.conn.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close()

        jobs = []
        for row in rows:
            jobs.append(
                {
                    "job_id": row[0],
                    "client_id": row[1],
                    "client_name": row[2],
                    "status": row[3],
                    "created_by": row[4],
                    "created_at": row[5],
                    "started_at": row[6],
                    "completed_at": row[7],
                    "error_message": row[8],
                }
            )

        return jobs

    def add_error_message(self, job_id: int, error_message: str) -> None:
        """
        Add or update error message for a job.

        Args:
            job_id: The job ID
            error_message: The error message to record
        """
        self.conn.execute(
            """
            UPDATE scrape_jobs
            SET error_message = ?
            WHERE job_id = ?
            """,
            (error_message, job_id),
        )
        self.conn.commit()

    def get_job_statistics(self) -> dict[str, int]:
        """
        Get job statistics by status for dashboard.

        Returns:
            Dict with counts by status: {pending: N, running: N, completed: N, failed: N, cancelled: N}
        """
        cursor = self.conn.execute(
            """
            SELECT status, COUNT(*) as count
            FROM scrape_jobs
            GROUP BY status
            """
        )
        rows = cursor.fetchall()
        cursor.close()

        stats = {
            "pending": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
        }

        for row in rows:
            status = row[0]
            count = row[1]
            if status in stats:
                stats[status] = count

        return stats

    def get_result_count(self, job_id: int) -> int:
        """
        Get the number of results for a job.

        Args:
            job_id: The job ID

        Returns:
            Number of matches found
        """
        cursor = self.conn.execute(
            """
            SELECT COUNT(*) FROM scrape_results WHERE job_id = ?
            """,
            (job_id,),
        )
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else 0

    def get_keyword_statistics(self, job_id: int) -> list[dict[str, Any]]:
        """
        Get aggregated match counts by keyword for a job.

        Args:
            job_id: The job ID

        Returns:
            List of dicts with keyword and match count, sorted by count descending
        """
        cursor = self.conn.execute(
            """
            SELECT k.keyword, COUNT(*) as match_count
            FROM scrape_results r
            JOIN keywords k ON r.keyword_id = k.keyword_id
            WHERE r.job_id = ?
            GROUP BY k.keyword_id, k.keyword
            ORDER BY match_count DESC
            """,
            (job_id,),
        )
        rows = cursor.fetchall()
        cursor.close()

        return [{"keyword": row[0], "match_count": row[1]} for row in rows]
