# 🚀 FastAPI Web Application Plan  

>*A Secure Private Web Interface for the JEA Scraper Project*

## 1. Overview  

This document outlines the implementation plan for building a secure web application layer on top of the existing JEA scraping and PDF-annotation pipeline. The web interface will provide:

- A login-protected dashboard  
- A button to trigger the scraping workflow  
- A page to view and download annotated PDFs  
- An intuitive UI styled using Bootstrap  
- Secure access enforced through JWT-based authentication  

The application will not publicly expose code or sensitive endpoints and will be deployed privately.

---

## 2. Project Goals  

- Add a lightweight, secure web interface without disrupting the existing Python file structure.  
- Ensure only authenticated users can trigger the scraper or download PDF results.  
- Maintain the current domain separation between NLP logic, data storage, and docs.  
- Create a structure that can easily deploy locally or through Cloudflare Tunnel.  
- Add no unnecessary complexity—small, clean, and purpose-built.

---

## 3. High-Level Architecture  

### Core Components  

| Component | Purpose |
|----------|---------|
| **FastAPI application** | Hosts the web interface, routing, and API endpoints |
| **Jinja templates** | Render HTML pages (login, dashboard, downloads) |
| **Bootstrap** | Provides styling and layout with no build step required |
| **JWT Auth** | Secures protected routes and manages user sessions |
| **Background Task Layer** | Ensures scraper runs without blocking the UI |
| **Service Layer** | Wraps existing scraper and PDF logic for clean interfacing |

### Interaction Flow  

1. User navigates to `/login`  
2. User enters username/password  
3. FastAPI validates credentials and issues a JWT access token  
4. Token is stored in a secure, HttpOnly cookie  
5. User is redirected to the dashboard  
6. Dashboard provides actions to run the scraper or download results  
7. Protected routes verify JWT token on every request  
8. Scraper + PDF generator run in the background  
9. New annotated PDFs appear on the “Downloads” page  

---

## 4. Proposed Directory Structure  

The new web layer will be added without modifying existing scraper logic:

```plaintext
src/
│
├── NLP/                  
├── dashboard/            
├── services/              
│   ├── scraper_service.py
│   └── pdf_service.py
│
└── webapp/                
    ├── main.py
    ├── auth.py
    ├── routes.py
    ├── dependencies.py
    │
    ├── templates/
    │   ├── base.html
    │   ├── login.html
    │   ├── dashboard.html
    │   └── downloads.html
    │
    └── static/
        ├── css/
        └── js/
```

---

## 5. Authentication Strategy (JWT)  

The app will use JWT tokens stored in **HttpOnly cookies** to secure user sessions.

### Key Requirements  

- Password-based login with credentials stored securely  
- Short-lived access tokens for security  
- Logout clears cookie  
- Protected routes require token validation  

### Protected Routes  

| Route | Purpose |
|-------|---------|
| `/dashboard` | Main interface for interacting with app |
| `/run-scraper` | Triggers scraping pipeline |
| `/downloads` | Lists available annotated PDFs |
| `/download/<filename>` | Secure direct download |

---

## 6. UI Layer Plan (Jinja + Bootstrap)  

### Pages  

- **Login Page**  
- **Dashboard Page**  
- **Downloads Page**  

### Styling  

- Bootstrap loaded via CDN  
- Consistent layout managed by `base.html`

---

## 7. Background Task Workflow  

When the user runs the scraper:

1. FastAPI accepts the request  
2. The scraper pipeline runs asynchronously  
3. User returns immediately to dashboard  
4. Output files appear automatically on the downloads page  

---

## 8. Integration With Existing Scraper Code  

A service layer will wrap existing functionality:

- **`scraper_service.py`**  
- **`pdf_service.py`**  

This avoids restructuring core logic.

---

## 9. Deployment Plan  

### Recommended Deployment Options  

- **Cloudflare Tunnel**  
- **Render.com**  
- **Fly.io**  

### Security Considerations  

- Use HTTPS  
- Keep JWT secret in environment variables  
- Do not expose scraper endpoints publicly  

---

## 10. Future Enhancements  

- Role-based access  
- Scheduled scraping  
- PDF previews  
- Keyword management in UI  

---

## 11. Summary  

This FastAPI + Jinja + Bootstrap plan will convert the existing JEA scraper into a secure, intuitive web application.
