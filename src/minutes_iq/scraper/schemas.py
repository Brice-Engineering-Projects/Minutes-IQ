"""
Pydantic schemas for scraper API endpoints.
"""

from pydantic import BaseModel, Field

# === Job Management Schemas ===


class CreateJobRequest(BaseModel):
    """Request schema for creating a scrape job."""

    client_id: int = Field(..., description="Client ID to scrape for")
    date_range_start: str | None = Field(
        None, description="Start date in YYYY-MM format"
    )
    date_range_end: str | None = Field(None, description="End date in YYYY-MM format")
    max_scan_pages: int | None = Field(
        None, description="Maximum pages to scan per PDF (None = all)"
    )
    include_minutes: bool = Field(True, description="Include meeting minutes PDFs")
    include_packages: bool = Field(True, description="Include meeting package PDFs")
    source_urls: list[str] = Field(
        ..., description="List of URLs to scrape for PDF links"
    )


class CreateJobResponse(BaseModel):
    """Response schema for job creation."""

    job_id: int
    status: str
    message: str


class JobSummary(BaseModel):
    """Summary of a scrape job."""

    job_id: int
    client_id: int
    client_name: str
    status: str
    created_by: int
    created_at: int
    started_at: int | None
    completed_at: int | None
    error_message: str | None


class JobListResponse(BaseModel):
    """Response schema for listing jobs."""

    jobs: list[JobSummary]
    total: int
    limit: int
    offset: int


class JobConfig(BaseModel):
    """Job configuration details."""

    config_id: int
    job_id: int
    date_range_start: str | None
    date_range_end: str | None
    max_scan_pages: int | None
    include_minutes: bool
    include_packages: bool


class JobStatistics(BaseModel):
    """Job execution statistics."""

    total_matches: int
    unique_pdfs: int
    unique_keywords: int
    execution_time_seconds: int | None


class JobDetails(BaseModel):
    """Full job details."""

    job_id: int
    client_id: int
    status: str
    created_by: int
    created_at: int
    started_at: int | None
    completed_at: int | None
    error_message: str | None
    config: JobConfig
    statistics: JobStatistics


class JobStatusResponse(BaseModel):
    """Job status polling response."""

    job_id: int
    status: str
    progress: dict | None
    error_message: str | None


# === Results Schemas ===


class ResultMatch(BaseModel):
    """Individual match result."""

    result_id: int
    job_id: int
    pdf_filename: str
    page_number: int
    keyword_id: int
    keyword: str
    snippet: str
    entities_json: str | None
    created_at: int


class ResultsListResponse(BaseModel):
    """Response schema for listing results."""

    results: list[ResultMatch]
    total: int
    limit: int
    offset: int


class KeywordStatistic(BaseModel):
    """Keyword match statistics."""

    keyword: str
    match_count: int


class ResultsSummaryResponse(BaseModel):
    """Results summary statistics."""

    job_id: int
    status: str
    total_matches: int
    unique_pdfs: int
    unique_keywords: int
    keyword_breakdown: list[KeywordStatistic]
    execution_time_seconds: int | None
    created_at: int
    started_at: int | None
    completed_at: int | None


# === Artifact Schemas ===


class CreateArtifactRequest(BaseModel):
    """Request schema for creating an artifact."""

    include_raw_pdfs: bool = Field(True, description="Include original PDFs")
    include_annotated_pdfs: bool = Field(True, description="Include highlighted PDFs")
    include_csv: bool = Field(True, description="Include results CSV")
    include_metadata: bool = Field(True, description="Include metadata JSON")


class CreateArtifactResponse(BaseModel):
    """Response schema for artifact creation."""

    artifact_id: str
    job_id: int
    status: str
    download_url: str | None
    expires_at: int | None


class ArtifactDetails(BaseModel):
    """Artifact details."""

    artifact_id: str
    job_id: int
    created_at: int
    size_bytes: int | None
    download_url: str | None
    expires_at: int | None


# === Storage Management Schemas ===


class CleanupResponse(BaseModel):
    """Response schema for cleanup operations."""

    job_id: int
    files_deleted: dict[str, int] = Field(
        ..., description="Count of files deleted by type"
    )
    message: str


class StorageCategory(BaseModel):
    """Storage statistics for a category."""

    size_bytes: int
    file_count: int
    job_count: int


class StorageStatsResponse(BaseModel):
    """Response schema for storage statistics."""

    raw_pdfs: StorageCategory
    annotated_pdfs: StorageCategory
    artifacts: StorageCategory
    total_size_bytes: int
