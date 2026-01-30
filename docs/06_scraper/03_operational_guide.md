# Scraper Operational Guide

This guide provides administrators with the information needed to monitor, troubleshoot, and optimize the scraper system.

## Table of Contents

1. [Job Management Workflows](#job-management-workflows)
2. [Monitoring](#monitoring)
3. [Troubleshooting Failed Jobs](#troubleshooting-failed-jobs)
4. [Performance Tuning](#performance-tuning)
5. [Storage and Cleanup Policies](#storage-and-cleanup-policies)
6. [Common Issues](#common-issues)

---

## Job Management Workflows

### Creating a Scrape Job

**Via API:**

```bash
curl -X POST https://api.example.com/scraper/jobs \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": 1,
    "date_range_start": "2024-01",
    "date_range_end": "2024-12",
    "max_scan_pages": 10,
    "source_urls": ["https://www.jea.com/meetings"]
  }'
```

**Best Practices:**
- Set appropriate `date_range` to avoid scanning too many PDFs
- Use `max_scan_pages` for faster scanning (10-20 pages recommended)
- Verify client has keywords configured before creating job

### Monitoring Job Progress

**Check Job Status:**

```bash
curl -X GET https://api.example.com/scraper/jobs/42/status \
  -H "Authorization: Bearer <token>"
```

**Poll every 5-10 seconds** during job execution.

**Status Indicators:**
- `pending`: Job is queued
- `running`: Job is executing
- `completed`: Job finished successfully
- `failed`: Job encountered an error
- `cancelled`: Job was cancelled

### Cancelling a Job

```bash
curl -X DELETE https://api.example.com/scraper/jobs/42 \
  -H "Authorization: Bearer <token>"
```

**Note:** Only `pending` and `running` jobs can be cancelled.

---

## Monitoring

### Database Queries

**Get job statistics by status:**

```sql
SELECT status, COUNT(*) as count
FROM scrape_jobs
GROUP BY status;
```

**Find long-running jobs:**

```sql
SELECT job_id, client_id,
       (CAST(strftime('%s', 'now') AS INTEGER) - started_at) / 60 as runtime_minutes
FROM scrape_jobs
WHERE status = 'running'
  AND started_at IS NOT NULL
ORDER BY runtime_minutes DESC;
```

**Find jobs with high match counts:**

```sql
SELECT j.job_id, j.client_id, COUNT(r.result_id) as match_count
FROM scrape_jobs j
LEFT JOIN scrape_results r ON j.job_id = r.job_id
WHERE j.status = 'completed'
GROUP BY j.job_id, j.client_id
HAVING match_count > 100
ORDER BY match_count DESC;
```

### Log Monitoring

**Application logs location:** `/var/log/minutes_iq/app.log`

**Key log patterns to watch:**

```bash
# Job creation
grep "Created scrape job" /var/log/minutes_iq/app.log

# Job failures
grep "Job.*failed with error" /var/log/minutes_iq/app.log

# Timeout warnings
grep "exceeded timeout" /var/log/minutes_iq/app.log

# Cancellation events
grep "Cancellation flag set" /var/log/minutes_iq/app.log
```

### Metrics to Track

1. **Job Completion Rate**
   - Target: >95% of jobs should complete successfully
   - Alert if <90% over 24 hours

2. **Average Execution Time**
   - Typical: 2-5 minutes for 10-20 PDFs
   - Alert if >30 minutes

3. **Failed Job Count**
   - Monitor daily failed job count
   - Investigate if >5% of total jobs

4. **Queue Depth**
   - Monitor number of pending jobs
   - Alert if >50 jobs pending for >1 hour

---

## Troubleshooting Failed Jobs

### Common Failure Scenarios

#### 1. Network Timeout

**Symptom:**
```
Error processing PDF https://example.com/doc.pdf: ReadTimeout
```

**Cause:** PDF download or parsing took too long

**Solution:**
- Increase timeout in `scraper/core.py` (default: 60s)
- Check network connectivity to source website
- Verify source URL is accessible

#### 2. No Keywords Configured

**Symptom:**
```
No keywords configured for client
```

**Cause:** Client has no active keywords

**Solution:**
```sql
-- Check client keywords
SELECT k.keyword_id, k.keyword
FROM keywords k
JOIN client_keywords ck ON k.keyword_id = ck.keyword_id
WHERE ck.client_id = 1 AND k.is_active = 1;

-- Add keyword to client
INSERT INTO client_keywords (client_id, keyword_id, added_at, added_by)
VALUES (1, 5, strftime('%s', 'now'), 1);
```

#### 3. Job Timeout

**Symptom:**
```
Job 42 exceeded timeout of 1800s (elapsed: 1850.3s)
```

**Cause:** Job took longer than 30 minutes

**Solution:**
- Reduce `max_scan_pages` in job config
- Narrow `date_range` to scan fewer PDFs
- Increase `JOB_TIMEOUT` constant if legitimate need (not recommended)

#### 4. PDF Parsing Error

**Symptom:**
```
Error processing PDF: Invalid PDF structure
```

**Cause:** Corrupted or malformed PDF

**Solution:**
- Note problematic PDF URL in logs
- Exclude URL from future scrapes
- Contact source website about corrupted file

### Investigating Failed Jobs

**Step 1: Get job details**

```sql
SELECT * FROM scrape_jobs WHERE job_id = 42;
```

**Step 2: Check error message**

```sql
SELECT error_message FROM scrape_jobs WHERE job_id = 42;
```

**Step 3: Review application logs**

```bash
grep "Job 42" /var/log/minutes_iq/app.log | tail -50
```

**Step 4: Check job configuration**

```sql
SELECT * FROM scrape_job_config WHERE job_id = 42;
```

**Step 5: Verify keywords**

```sql
SELECT k.keyword
FROM keywords k
JOIN client_keywords ck ON k.keyword_id = ck.keyword_id
JOIN scrape_jobs j ON ck.client_id = j.client_id
WHERE j.job_id = 42;
```

### Retrying Failed Jobs

Failed jobs can be retried by creating a new job with the same configuration:

```bash
# Get original job config
curl -X GET https://api.example.com/scraper/jobs/42

# Create new job with same config
curl -X POST https://api.example.com/scraper/jobs \
  -H "Authorization: Bearer <token>" \
  -d '<same config as original>'
```

---

## Performance Tuning

### Configuration Parameters

#### max_scan_pages

Controls how many pages to scan per PDF.

**Impact:**
- Lower value = faster execution, may miss matches
- Higher value = slower execution, more complete results
- `null` = scan all pages (slowest)

**Recommendations:**
| Document Type | Recommended Value |
|---------------|-------------------|
| Meeting Minutes | 10-20 pages |
| Meeting Packages | 50 pages |
| Full Documents | null (all pages) |

**Example:**
```json
{
  "max_scan_pages": 20
}
```

#### date_range

Filters PDFs by date to reduce the number of documents scanned.

**Impact:**
- Narrower range = fewer PDFs = faster execution
- Wider range = more PDFs = slower execution

**Recommendations:**
- Use 3-6 month ranges for routine searches
- Use full year for comprehensive analysis
- Use specific month for targeted searches

**Example:**
```json
{
  "date_range_start": "2024-10",
  "date_range_end": "2024-12"
}
```

#### include_minutes / include_packages

Controls which PDF types to include.

**Impact:**
- Both enabled = more documents, slower
- One disabled = fewer documents, faster

**Recommendations:**
- Enable `minutes` only for quick searches
- Enable both for comprehensive searches

### Timeout Configuration

**Current timeout:** 30 minutes per job

**Location:** `src/minutes_iq/scraper/async_runner.py`

```python
JOB_TIMEOUT = 30 * 60  # 30 minutes
```

**To adjust:**

```python
JOB_TIMEOUT = 45 * 60  # 45 minutes (if needed)
```

**Warning:** Longer timeouts can tie up resources. Consider reducing scope instead.

### Concurrent Job Execution

**Current limit:** Determined by FastAPI worker configuration

**To increase:**

```bash
# Start FastAPI with more workers
uvicorn main:app --workers 4
```

**Recommendation:** 1 worker per CPU core

### Database Performance

**Indexing:**

Ensure indexes exist on commonly queried columns:

```sql
CREATE INDEX IF NOT EXISTS idx_jobs_status ON scrape_jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_user ON scrape_jobs(created_by);
CREATE INDEX IF NOT EXISTS idx_results_job ON scrape_results(job_id);
```

**Query Optimization:**

Use `EXPLAIN QUERY PLAN` to verify index usage:

```sql
EXPLAIN QUERY PLAN
SELECT * FROM scrape_jobs WHERE status = 'running';
```

---

## Storage and Cleanup Policies

### Storage Organization

The scraper uses a structured directory layout managed by `StorageManager`:

```
data/
├── raw_pdfs/{job_id}/           # Original PDFs downloaded during scrape
├── annotated_pdfs/{job_id}/     # PDFs with keyword highlights
└── artifacts/{job_id}/          # ZIP archives for download
```

**Benefits:**
- Job isolation: Each job has its own directory
- Easy cleanup: Delete entire job directory at once
- Traceable: File organization matches database records

### Retention Policies

**Default Retention Periods:**

| File Type | Retention | Rationale |
|-----------|-----------|-----------|
| Raw PDFs | 30 days | Temporary storage for processing |
| Annotated PDFs | 90 days | Primary output for users |
| Artifacts | 30 days | One-time downloads or until downloaded |

**Configuration:**

```python
from minutes_iq.scraper.storage import StorageManager

storage = StorageManager(
    base_dir="data",
    raw_pdf_retention_days=30,
    annotated_pdf_retention_days=90,
    artifact_retention_days=30
)
```

### Manual File Cleanup

**Cleanup Specific Job (Admin API):**

```bash
# Delete all files for job 123
curl -X DELETE "http://localhost:8000/scraper/jobs/123/cleanup" \
  -H "Authorization: Bearer <admin_token>"

# Preserve artifacts (only delete PDFs)
curl -X DELETE "http://localhost:8000/scraper/jobs/123/cleanup?include_artifacts=false" \
  -H "Authorization: Bearer <admin_token>"
```

**Response:**

```json
{
  "job_id": 123,
  "files_deleted": {
    "raw_pdfs": 15,
    "annotated_pdfs": 12,
    "artifacts": 2
  },
  "message": "Cleaned up 29 files for job 123"
}
```

### Automated Cleanup

**Python Script (Age-Based):**

```python
#!/usr/bin/env python3
"""
Automated cleanup script for scraper storage.
Run as cron job daily: 0 2 * * * /usr/local/bin/cleanup_scraper_storage.py
"""

from minutes_iq.scraper.storage import StorageManager

def main():
    storage = StorageManager(
        base_dir="/var/lib/minutes_iq/data",
        raw_pdf_retention_days=30,
        annotated_pdf_retention_days=90,
        artifact_retention_days=30
    )

    # Cleanup files older than retention periods
    summary = storage.cleanup_old_files()

    print(f"Cleanup Summary:")
    print(f"  Raw PDFs deleted: {summary['raw_pdfs_deleted']}")
    print(f"  Annotated PDFs deleted: {summary['annotated_pdfs_deleted']}")
    print(f"  Artifacts deleted: {summary['artifacts_deleted']}")
    print(f"  Jobs cleaned: {len(summary['jobs_cleaned'])}")

if __name__ == "__main__":
    main()
```

**Cron Configuration:**

```bash
# /etc/cron.daily/cleanup_scraper_storage.sh
#!/bin/bash
cd /opt/minutes_iq
source venv/bin/activate
python -m minutes_iq.scripts.cleanup_storage
```

### Storage Monitoring

**Get Storage Statistics (Admin API):**

```bash
curl "http://localhost:8000/scraper/storage/stats" \
  -H "Authorization: Bearer <admin_token>"
```

**Response:**

```json
{
  "raw_pdfs": {
    "size_bytes": 157286400,
    "file_count": 350,
    "job_count": 45
  },
  "annotated_pdfs": {
    "size_bytes": 210534400,
    "file_count": 280,
    "job_count": 38
  },
  "artifacts": {
    "size_bytes": 52428800,
    "file_count": 12,
    "job_count": 12
  },
  "total_size_bytes": 420249600
}
```

**Python Script for Monitoring:**

```python
from minutes_iq.scraper.storage import StorageManager

def check_storage():
    storage = StorageManager(base_dir="data")
    stats = storage.get_storage_stats()

    total_gb = stats["total_size_bytes"] / (1024**3)

    print(f"Total Storage: {total_gb:.2f} GB")
    print(f"Raw PDFs: {stats['raw_pdfs']['file_count']} files ({stats['raw_pdfs']['job_count']} jobs)")
    print(f"Annotated PDFs: {stats['annotated_pdfs']['file_count']} files")
    print(f"Artifacts: {stats['artifacts']['file_count']} files")

    # Alert if storage exceeds threshold
    if total_gb > 50:
        print("WARNING: Storage exceeds 50GB threshold!")

check_storage()
```

### Database Cleanup

**Job Records:**

```sql
-- Archive completed jobs older than 1 year
-- (Move to archive table or export to file)
CREATE TABLE scrape_jobs_archive AS
SELECT * FROM scrape_jobs
WHERE status = 'completed'
  AND completed_at < strftime('%s', 'now', '-1 year');

-- Delete old failed/cancelled jobs (older than 90 days)
DELETE FROM scrape_jobs
WHERE status IN ('failed', 'cancelled')
  AND completed_at < strftime('%s', 'now', '-90 days');
```

**Automated Cleanup (cron):**

```bash
# /etc/cron.daily/cleanup_scraper_jobs.sh
#!/bin/bash

sqlite3 /var/lib/minutes_iq/db.sqlite3 <<EOF
DELETE FROM scrape_jobs
WHERE status IN ('failed', 'cancelled')
  AND completed_at < strftime('%s', 'now', '-90 days');
EOF
```

### Disk Space Monitoring

**Check disk usage:**

```bash
# PDF storage
du -sh /var/lib/minutes_iq/pdfs

# Database size
du -h /var/lib/minutes_iq/db.sqlite3
```

**Set up alerts:**

```bash
# Alert if disk usage >80%
df -h /var/lib/minutes_iq | awk '{ if (int($5) > 80) print "ALERT: Disk usage " $5 }'
```

---

## Common Issues

### Issue: Jobs Stuck in "pending" Status

**Cause:** Background worker not running or overloaded

**Diagnosis:**

```sql
SELECT COUNT(*) FROM scrape_jobs WHERE status = 'pending';
```

**Solution:**
1. Check if FastAPI server is running
2. Restart workers: `systemctl restart minutes_iq`
3. Reduce concurrent job creation

---

### Issue: Jobs Timing Out Frequently

**Cause:** Too many PDFs or pages to scan

**Diagnosis:**

```sql
SELECT j.job_id, c.max_scan_pages, COUNT(r.result_id) as results
FROM scrape_jobs j
LEFT JOIN scrape_job_config c ON j.job_id = c.job_id
LEFT JOIN scrape_results r ON j.job_id = r.job_id
WHERE j.status = 'failed'
  AND j.error_message LIKE '%timeout%'
GROUP BY j.job_id, c.max_scan_pages;
```

**Solution:**
- Set `max_scan_pages` to 10-20
- Narrow `date_range`
- Split into multiple smaller jobs

---

### Issue: High Memory Usage

**Cause:** Processing large PDFs or many concurrent jobs

**Diagnosis:**

```bash
# Check memory usage
free -h

# Check process memory
ps aux | grep uvicorn
```

**Solution:**
- Reduce concurrent workers
- Set `max_scan_pages` limit
- Increase server memory

---

### Issue: No Results Found

**Cause:** Keywords not in PDFs or wrong date range

**Diagnosis:**

```sql
-- Check if any results exist for client
SELECT j.job_id, COUNT(r.result_id) as results
FROM scrape_jobs j
LEFT JOIN scrape_results r ON j.job_id = r.job_id
WHERE j.client_id = 1
GROUP BY j.job_id;

-- Check keywords
SELECT k.keyword FROM keywords k
JOIN client_keywords ck ON k.keyword_id = ck.keyword_id
WHERE ck.client_id = 1 AND k.is_active = 1;
```

**Solution:**
- Verify keywords are correct and active
- Expand `date_range`
- Increase or remove `max_scan_pages` limit
- Test keywords manually on known PDFs

---

## Maintenance Checklist

### Daily Tasks
- [ ] Check failed job count
- [ ] Monitor disk space
- [ ] Review error logs

### Weekly Tasks
- [ ] Review job completion rates
- [ ] Check for stuck jobs
- [ ] Verify backup completion
- [ ] Clean up old failed/cancelled jobs

### Monthly Tasks
- [ ] Archive old completed jobs
- [ ] Review performance metrics
- [ ] Optimize database indexes
- [ ] Update documentation

---

## Support Contacts

- **Development Team:** dev@example.com
- **On-Call:** +1-555-123-4567
- **Issue Tracker:** https://github.com/your-org/minutes-iq/issues

---

## Additional Resources

- [API Reference](./01_api_reference.md)
- [Data Model](./02_data_model.md)
- [User Guide](../user_guide.md)
