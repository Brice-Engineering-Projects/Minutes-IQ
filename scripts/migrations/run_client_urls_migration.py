#!/usr/bin/env python3
"""
Migration: Refactor Client URLs Architecture

This migration:
1. Creates client_urls table with simplified schema (alias + url)
2. Migrates existing website_url from client table to client_urls
3. Drops old client_sources table
4. Removes website_url column from client table
5. Updates scrape_jobs to reference client_url_id instead of client_id

Usage:
    From project root: uv run python scripts/migrations/run_client_urls_migration.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project src to path (must be before local imports)
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from minutes_iq.db.client import get_db_connection  # noqa: E402


def main():
    """Execute the client URLs migration."""
    print("=" * 80)
    print("Client URLs Migration - v20260212_120000")
    print("=" * 80)
    print("\nThis migration will:")
    print("  • Create client_urls table")
    print("  • Migrate website_url → client_urls (alias='default')")
    print("  • Drop client_sources table")
    print("  • Remove website_url from client table")
    print("  • Update scrape_jobs.client_id → client_url_id")
    print("\n" + "=" * 80)

    with get_db_connection() as db:
        print("\n✓ Connected to Turso database\n")

        # Step 1: Check current state
        print("Step 1: Checking current database state...")

        result = db.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='client_urls'
        """)
        if result.fetchone():
            print("   ⚠️  client_urls table already exists!")
            print("   Migration already applied. Exiting.")
            return 0

        result = db.execute("""
            SELECT COUNT(*) FROM client WHERE website_url IS NOT NULL AND website_url != ''
        """)
        url_count = result.fetchone()[0]
        print(f"   • Found {url_count} client(s) with website_url to migrate")

        result = db.execute("SELECT COUNT(*) FROM client_sources")
        sources_count = result.fetchone()[0]
        print(f"   • Found {sources_count} row(s) in client_sources (will be dropped)")

        # Step 2: Execute migration
        print("\nStep 2: Executing migration...")

        try:
            # Create client_urls table
            print("   • Creating client_urls table...")
            db.execute("""
                CREATE TABLE IF NOT EXISTS client_urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id INTEGER NOT NULL,
                    alias TEXT NOT NULL,
                    url TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    last_scraped_at INTEGER,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER,
                    FOREIGN KEY (client_id) REFERENCES client(client_id) ON DELETE CASCADE
                )
            """)
            print("     ✓ client_urls table created")

            # Migrate website_url data
            print("   • Migrating website_url data...")
            db.execute("""
                INSERT INTO client_urls (client_id, alias, url, is_active, created_at)
                SELECT
                    client_id,
                    'default' as alias,
                    website_url as url,
                    1 as is_active,
                    CAST(strftime('%s', 'now') AS INTEGER) as created_at
                FROM client
                WHERE website_url IS NOT NULL AND website_url != ''
            """)
            result = db.execute("SELECT changes()")
            rows_migrated = result.fetchone()[0]
            print(f"     ✓ Migrated {rows_migrated} URL(s) to client_urls")

            # Create indexes
            print("   • Creating indexes...")
            db.execute(
                "CREATE INDEX IF NOT EXISTS idx_client_urls_client_id ON client_urls(client_id)"
            )
            db.execute(
                "CREATE INDEX IF NOT EXISTS idx_client_urls_is_active ON client_urls(is_active)"
            )
            db.execute(
                "CREATE INDEX IF NOT EXISTS idx_client_urls_alias ON client_urls(alias)"
            )
            print("     ✓ Indexes created")

            # Drop client_sources
            print("   • Dropping old client_sources table...")
            db.execute("DROP TABLE IF EXISTS client_sources")
            print("     ✓ client_sources dropped")

            # Recreate client table without website_url
            print("   • Recreating client table without website_url...")
            db.execute("""
                CREATE TABLE client_new (
                    client_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    created_by INTEGER NOT NULL,
                    updated_at INTEGER,
                    FOREIGN KEY (created_by) REFERENCES users(user_id)
                )
            """)
            db.execute("""
                INSERT INTO client_new (client_id, name, description, is_active, created_at, created_by, updated_at)
                SELECT client_id, name, description, is_active, created_at, created_by, updated_at
                FROM client
            """)
            db.execute("DROP TABLE client")
            db.execute("ALTER TABLE client_new RENAME TO client")
            print("     ✓ client table recreated")

            # Recreate client indexes
            print("   • Recreating client indexes...")
            db.execute("CREATE INDEX IF NOT EXISTS idx_client_name ON client(name)")
            db.execute(
                "CREATE INDEX IF NOT EXISTS idx_client_is_active ON client(is_active)"
            )
            db.execute(
                "CREATE INDEX IF NOT EXISTS idx_client_created_by ON client(created_by)"
            )
            print("     ✓ Indexes recreated")

            # Update scrape_jobs
            print("   • Updating scrape_jobs table...")
            result = db.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='scrape_jobs'
            """)
            if result.fetchone():
                db.execute("""
                    CREATE TABLE scrape_jobs_new (
                        job_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        client_url_id INTEGER NOT NULL,
                        status TEXT NOT NULL,
                        created_by INTEGER NOT NULL,
                        created_at INTEGER NOT NULL,
                        started_at INTEGER,
                        completed_at INTEGER,
                        error_message TEXT,
                        FOREIGN KEY (client_url_id) REFERENCES client_urls(id) ON DELETE CASCADE,
                        FOREIGN KEY (created_by) REFERENCES users(user_id)
                    )
                """)
                db.execute("""
                    INSERT INTO scrape_jobs_new (
                        job_id, client_url_id, status, created_by, created_at,
                        started_at, completed_at, error_message
                    )
                    SELECT
                        sj.job_id,
                        cu.id as client_url_id,
                        sj.status,
                        sj.created_by,
                        sj.created_at,
                        sj.started_at,
                        sj.completed_at,
                        sj.error_message
                    FROM scrape_jobs sj
                    LEFT JOIN client_urls cu ON cu.client_id = sj.client_id AND cu.alias = 'default'
                    WHERE cu.id IS NOT NULL
                """)
                db.execute("DROP TABLE scrape_jobs")
                db.execute("ALTER TABLE scrape_jobs_new RENAME TO scrape_jobs")
                db.execute(
                    "CREATE INDEX IF NOT EXISTS idx_scrape_jobs_client_url_id ON scrape_jobs(client_url_id)"
                )
                db.execute(
                    "CREATE INDEX IF NOT EXISTS idx_scrape_jobs_status ON scrape_jobs(status)"
                )
                db.execute(
                    "CREATE INDEX IF NOT EXISTS idx_scrape_jobs_created_by ON scrape_jobs(created_by)"
                )
                print("     ✓ scrape_jobs updated")
            else:
                print("     ⏭️  scrape_jobs table not found, skipping")

            # Commit
            db.commit()
            print("\n✅ Migration completed successfully!")

            # Step 3: Verify
            print("\nStep 3: Verifying migration...")
            result = db.execute("SELECT COUNT(*) FROM client_urls")
            final_count = result.fetchone()[0]
            print(f"   • Total URLs in client_urls: {final_count}")

            result = db.execute("""
                SELECT c.name, cu.alias, cu.url, cu.is_active
                FROM client_urls cu
                JOIN client c ON c.client_id = cu.client_id
            """)
            print("\n   Client URLs:")
            for row in result.fetchall():
                print(f"     • {row[0]}: [{row[1]}] {row[2]} (active={row[3]})")

        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            db.rollback()
            return 1

    print("\n" + "=" * 80)
    print("Migration Complete!")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
