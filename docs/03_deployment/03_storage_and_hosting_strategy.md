# Storage and Hosting Strategy

## Overview

This document outlines the storage and hosting architecture for MinutesIQ, optimized for a free/low-cost beta deployment with a clear path to scale.

---

## Architecture Components

### 1. Database: Turso (libSQL)

**Purpose:** Store structured application data

**What's stored:**
- User accounts and authentication
- Client information and URLs
- Keywords and categories
- Scrape job metadata (status, timestamps, configuration)
- Search results metadata (matched keywords, page numbers, snippets)
- File paths and references (NOT the actual PDF files)

**Free Tier Limits:**
- 500 databases
- 9 GB total storage
- Billions of row reads
- Suitable for thousands of users in beta

**Why Turso:**
- ✅ Free tier sufficient for beta
- ✅ SQLite compatibility (easy development)
- ✅ Edge deployment (low latency)
- ✅ No credit card required
- ✅ Auto-scaling reads

**Connection:** Remote HTTP API (Hrana protocol)

---

### 2. Application Hosting: Render.com

**Purpose:** Run the FastAPI application

**Free Tier:**
- 512 MB RAM
- Persistent disk storage (limited)
- Auto-deploy from GitHub
- HTTPS included
- **Limitation:** Sleeps after 15 min inactivity (30-60s wake time)

**Paid Tier ($7/month):**
- Always-on (no sleep)
- More disk space
- Better performance
- Suitable for production

**Alternative:** Railway.app (similar pricing/features)

---

### 3. PDF Storage: Server Filesystem

**Purpose:** Store extracted PDF pages with highlighted keywords

**Storage Location:**
```
/data/scraper_output/
├── {job_id}/
│   ├── matched_pdfs/
│   │   ├── document_2024-01-15_pages_2-5-7.pdf
│   │   └── document_2024-02-20_pages_3.pdf
│   └── metadata.json
```

**What's stored:**
- Only PDF pages containing keyword matches (not full documents)
- Highlighted keywords on matched pages
- Typically 2-5 pages per document vs 15-50 page originals

**Storage estimates:**
- Average matched PDF: ~200 KB (2-3 pages)
- 100 jobs × 10 matches = ~200 MB
- Free tier: Sufficient for 500+ matches

**Why server filesystem:**
- ✅ Simple implementation
- ✅ Included with hosting (no extra cost)
- ✅ Fast local access
- ✅ Works in both development and production
- ❌ Limited by server disk space
- ❌ Not automatically backed up

**Access:** Served via API endpoint `/api/scraper/jobs/{job_id}/pdfs/{filename}`

---

## Cost Breakdown (Beta Phase)

| Service | Free Tier | Estimated Usage | Monthly Cost |
|---------|-----------|-----------------|--------------|
| **Turso Database** | 9 GB storage | <500 MB | $0 |
| **Render Hosting** | 512 MB RAM | 1 web service | $0 |
| **PDF Storage** | ~1 GB disk | <500 MB | $0 (included) |
| **Domain** | N/A | render.com subdomain | $0 |
| **HTTPS/SSL** | Included | Automatic | $0 |
| **Total** | | | **$0/month** |

---

## Scaling Path

### Phase 1: Beta (Current - $0/month)
- Turso free tier
- Render free tier
- Server filesystem storage
- 5-10 beta users
- ~100 scrape jobs/month

### Phase 2: Early Production ($7-15/month)
**When:** 20+ active users or need 24/7 uptime

**Upgrades:**
- Render paid tier: $7/month (always-on, more disk)
- Still on Turso free tier (plenty of headroom)
- Server filesystem still sufficient

### Phase 3: Growth ($20-50/month)
**When:** 100+ users or PDF storage >5 GB

**Upgrades:**
- Render: $7/month
- Cloudflare R2 for PDFs: $0.015/GB stored + $0.36/million requests
- Turso still free (or $29/month for Pro if needed)
- Example: 50 GB PDFs = $0.75/month storage

### Phase 4: Scale ($100+/month)
**When:** 1000+ users, enterprise deployment

**Upgrades:**
- Render: Scale to multiple instances ($21+/month)
- Cloudflare R2: ~$10-20/month for 500+ GB
- Turso Pro: $29/month (dedicated instance)
- CDN for PDF delivery (optional)

---

## Alternative Storage Options

### Option A: Cloudflare R2 (Future Migration)

**When to switch:** PDF storage exceeds 5 GB or need geographic distribution

**Pricing:**
- FREE up to 10 GB
- $0.015/GB/month beyond 10 GB
- No egress fees (unlike S3)

**Migration process:**
```python
# Current: local filesystem
storage_manager.save_matched_pdf(job_id, filename, pdf_bytes)

# Future: R2 adapter
r2_storage.save_matched_pdf(job_id, filename, pdf_bytes)
# Same interface, different backend
```

### Option B: Store PDFs in Turso (NOT RECOMMENDED)

**Why not:**
- ❌ Inflates database size (binary blobs are inefficient)
- ❌ Expensive queries (fetching large blobs)
- ❌ Hits 9 GB limit quickly (~45 PDFs at 200 KB each = 9 GB)
- ❌ Poor performance
- ✅ Only advantage: Single storage backend

**Verdict:** Only viable for proof-of-concept with <50 PDFs

---

## Deployment Checklist

### Initial Deployment (Free Tier)

1. **Setup Turso Database**
   - [x] Create Turso account
   - [x] Create database
   - [x] Add `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN` to `.env`
   - [x] Run migrations

2. **Deploy to Render**
   - [ ] Create Render account
   - [ ] Connect GitHub repository
   - [ ] Configure build command: `pip install -r requirements.txt`
   - [ ] Configure start command: `uvicorn minutes_iq.main:app --host 0.0.0.0 --port $PORT`
   - [ ] Add environment variables (Turso credentials, secrets)
   - [ ] Enable persistent disk for `/data` directory

3. **Configure Storage**
   - [x] `StorageManager` configured with `base_dir="data"`
   - [ ] Verify `/data` directory is on persistent disk (not ephemeral)
   - [ ] Test PDF upload/download via API

4. **Test End-to-End**
   - [ ] Create scrape job
   - [ ] Verify PDFs stored in `/data/scraper_output/`
   - [ ] Download matched PDF via UI
   - [ ] Confirm persistence after app restart

---

## Storage Best Practices

### 1. Store Minimal Data
- ❌ Don't store full PDF documents
- ✅ Extract and store only matched pages
- ✅ Store PDF URL for reference (can re-download if needed)

### 2. Implement Cleanup
```python
# Delete old job data after 90 days
if job.completed_at < 90_days_ago:
    storage_manager.cleanup_job(job_id)
```

### 3. Monitor Usage
```python
# Track storage metrics
storage_stats = storage_manager.get_storage_stats()
# {'total_size_mb': 245, 'file_count': 1234, 'jobs_count': 156}
```

### 4. Plan for Migration
- Keep storage logic abstracted (`StorageManager` interface)
- Easy to swap backend (filesystem → R2 → S3)
- No application code changes needed

---

## FAQ

### Q: What happens if Render free tier goes away?
**A:** Switch to Railway (similar free tier) or upgrade to Render paid ($7/month)

### Q: What if we exceed free disk space?
**A:**
1. Implement cleanup (delete old jobs)
2. Upgrade to Render paid (more disk)
3. Migrate to Cloudflare R2 (unlimited, cheap)

### Q: Can we use AWS Lambda instead?
**A:** Possible but complex:
- ✅ Cheaper at low scale (free tier)
- ❌ Limited to 15 min execution (scrape jobs may timeout)
- ❌ Ephemeral storage (need S3)
- **Verdict:** Not recommended for this use case

### Q: Should we add Redis for caching?
**A:** Not yet:
- Wait until performance issues arise
- Render Redis: $10/month
- Free alternative: Upstash Redis (10K requests/day free)

### Q: How do we backup PDFs?
**A:**
- Render persistent disk is backed up automatically
- For critical data: sync to R2/S3 nightly
- Or store PDF source URLs and re-scrape if needed

---

## Monitoring and Alerts

### Key Metrics to Track

1. **Disk Usage**
   ```python
   # Alert if disk usage > 80%
   storage_stats = storage_manager.get_storage_stats()
   if storage_stats['total_size_mb'] > 800:  # 80% of 1GB
       send_alert("Disk usage critical")
   ```

2. **Database Size**
   ```sql
   -- Check Turso dashboard for storage usage
   -- Alert if approaching 8 GB (90% of 9 GB limit)
   ```

3. **Job Success Rate**
   ```python
   # Track failed jobs
   failed_jobs = count_jobs_by_status('failed')
   if failed_jobs > 10:  # More than 10 failures
       send_alert("High failure rate")
   ```

---

## Security Considerations

### 1. PDF Access Control
- ✅ Verify user owns job before serving PDF
- ✅ Use signed URLs for temporary access (future enhancement)
- ❌ Don't expose filesystem paths in API responses

### 2. Storage Limits
- ✅ Implement per-user storage quotas
- ✅ Validate file sizes before storage
- ✅ Prevent disk fill attacks

### 3. Data Retention
- ✅ Auto-delete jobs after retention period
- ✅ Allow users to manually delete jobs
- ✅ GDPR compliance (user data deletion)

---

## Conclusion

**Current state:** Ready for beta deployment at $0/month

**Strengths:**
- Free tier supports 5-20 users
- Simple architecture (easy to maintain)
- Clear scaling path
- No vendor lock-in (can migrate storage backends)

**Limitations:**
- App sleeps on free tier (acceptable for beta)
- Limited disk space (5-10 GB)
- Manual scaling required

**Next steps:**
1. Deploy to Render
2. Test with beta users
3. Monitor usage metrics
4. Upgrade or migrate based on actual usage patterns

**Boss approval threshold:** If usage exceeds 50 jobs/week or 10+ active users, upgrade to paid tier ($7/month)
