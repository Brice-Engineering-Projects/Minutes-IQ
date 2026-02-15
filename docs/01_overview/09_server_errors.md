# Server Errors

This section provides guidance on handling server errors in your application.

**Date:** 2026-02-13

**Logged Errors:**

```http 
INFO:     127.0.0.1:39318 - "GET /api/scraper/jobs/list?status=pending&client_id= HTTP/1.1" 422 Unprocessable Entity
INFO:     127.0.0.1:39318 - "GET /api/scraper/jobs/list?status=running&client_id= HTTP/1.1" 422 Unprocessable Entity
INFO:     127.0.0.1:39318 - "GET /api/scraper/jobs/1/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:39318 - "GET /api/scraper/jobs/list?status=completed&client_id= HTTP/1.1" 422 Unprocessable Entity
INFO:     127.0.0.1:39318 - "GET /api/scraper/jobs/list?status=failed&client_id= HTTP/1.1" 422 Unprocessable Entity
INFO:     127.0.0.1:39318 - "GET /api/scraper/jobs/1/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:46968 - "GET /api/scraper/jobs/1/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:42652 - "GET /api/scraper/jobs/1/status HTTP/1.1" 200 OK
INFO:     127.0.0.1:49996 - "GET /api/scraper/jobs/1/status HTTP/1.1" 200 OK
```

**Analysis:**
- The server encountered 422 Unprocessable Entity errors for invalid query parameters.
- Successful status checks for job 1 were logged.
