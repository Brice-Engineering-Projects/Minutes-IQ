# 📄 MinutesIQ – User-Scoped Scrape Jobs Refactor

## 1. Objective

Refactor scraper job data access and permissions so that:

- Users can ONLY see their own scrape jobs
- Users can access details of jobs they created
- Admins can access ALL jobs
- Eliminate mismatch between listing and detail authorization

---

## 2. Root Problem

Current behavior:

- Scrape jobs are queried globally (no user filtering)
- Authorization is enforced at the detail level
- This causes:
  - Users seeing all jobs in list view ❌
  - Users receiving 403 on job detail ❌

---

## 3. Required Data Model Change

### Ensure scraper_jobs table includes:

- `user_id` (FOREIGN KEY → users.id)

If not present:

ALTER TABLE scraper_jobs ADD COLUMN user_id INTEGER NOT NULL;

---

## 4. Ownership Rules

- Each job must be associated with the user who created it
- On job creation:
  - scraper_jobs.user_id = current_user.id

---

## 5. Repository Layer Changes

### 5.1 List Jobs (User Scope)

Replace global queries with:

def get_jobs_for_user(user):
    if user.is_admin:
        return get_all_jobs()
    return get_jobs_by_user_id(user.id)

---

### 5.2 Get Job By ID (Authorization Safe)

def get_job_for_user(job_id, user):
    job = get_job_by_id(job_id)

    if not job:
        raise Exception("Job not found")

    if user.is_admin:
        return job

    if job.user_id != user.id:
        raise Exception("Access denied")

    return job

---

## 6. Service Layer Changes

All job-related services must use scoped repository methods:

- list_jobs() → get_jobs_for_user(user)
- get_job_details() → get_job_for_user(job_id, user)

---

## 7. Route Layer Changes

### 7.1 List Jobs Route

@router.get("/scraper/jobs")
def list_jobs(current_user=Depends(get_current_user)):
    return job_service.get_jobs_for_user(current_user)

---

### 7.2 Job Detail Route

@router.get("/scraper/jobs/{job_id}")
def get_job(job_id: int, current_user=Depends(get_current_user)):
    return job_service.get_job_for_user(job_id, current_user)

---

## 8. Fix for PDF Download Endpoint

Update GET /download-results/{job_id}

Ensure:

job = job_service.get_job_for_user(job_id, current_user)

NOT:

job = get_job_by_id(job_id)

---

## 9. Job Creation Update

Ensure:

new_job.user_id = current_user.id

---

## 10. Migration (if needed)

If existing jobs do not have user_id:

Option A:
- Assign all existing jobs to admin user

Option B:
- Assign based on historical ownership if available

---

## 11. Testing Requirements

### Add tests for:

User Isolation:
- User A cannot see User B jobs
- User A cannot access User B job detail

Admin Access:
- Admin can see all jobs
- Admin can access all job details

PDF Endpoint:
- User can download their own job results
- User receives 403 for others’ jobs

---

## 12. Definition of Done

- Job list is user-scoped
- Job detail access matches list visibility
- No 403 errors for user-owned jobs
- Admin retains full access
- PDF download endpoint respects ownership

---

## 13. Clients and Keywords

- Both Clients and Keywords are currently global and can be accessed by all users. This refactor does NOT change their behavior. They remain shared resources across the application.

---

## 14. Summary

This refactor enforces proper multi-user data isolation:

- Eliminates global job visibility
- Aligns listing and authorization behavior
- Ensures secure and scalable job access model
