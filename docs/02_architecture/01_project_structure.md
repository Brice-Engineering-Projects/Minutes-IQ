# Project Structure

```plaintext
JEA_WEB_SCRAPING/
│
├── data/
│   ├── raw_pdfs/
│   ├── processed/
│   └── annotated_pdfs/
│
├── docs/
│   ├── 01_overview/
│   ├── 02_architecture/
│   └── 03_medium_blog/
│
├── src/
│   ├── dashboard/
│   │   ├── __init__.py
│   │   └── dashboard.py          # can be converted into a route handler
│   │
│   ├── NLP/
│   │   ├── __init__.py
│   │   ├── JEA_minutes_scraper.py
│   │   ├── highlight_mentions.py
│   │   └── NLP_test.py
│   │
│   ├── services/
│   │   ├── scraper_service.py    # will wrap your existing scripts
│   │   └── pdf_service.py
│   │
│   └── webapp/
│       ├── main.py               # FASTAPI ENTRYPOINT
│       ├── auth.py               # login logic
│       ├── routes.py             # dashboard routes
│       ├── dependencies.py
│       │
│       ├── templates/
│       │   ├── base.html
│       │   ├── login.html
│       │   ├── dashboard.html
│       │   └── downloads.html
│       │
│       └── static/
│           ├── css/
│           ├── js/
│           └── images/
│
├── environment.yml
├── README.md
└── scraper.log
```
