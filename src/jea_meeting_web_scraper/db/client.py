# src/jea_meeting_web_scraper/db/client.py

from libsql_experimental import connect

from jea_meeting_web_scraper.config.settings import settings


def get_db_client():
    return connect(
        settings.database.db_url,
        auth_token=settings.database.auth_token,
    )


def healthcheck() -> bool:
    conn = get_db_client()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        row = cur.fetchone()
        return row == (1,)
    finally:
        conn.close()
