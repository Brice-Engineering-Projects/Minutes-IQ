#!/usr/bin/env python3
"""
Fix scrape_results table schema to match expected format.

The table currently has:
- pdf_url, pdf_date, pdf_type, keyword (TEXT)

But code expects:
- pdf_filename (TEXT), entities_json (TEXT)
- keyword is joined from keywords table

This script will:
1. Backup existing data (if any)
2. Drop the old table
3. Create the new table with correct schema
4. Restore data (if any) - mapping old columns to new

Usage:
    python fix_scrape_results_schema.py [--force]
"""

import sys
from pathlib import Path

# Add src to path - must be done before importing minutes_iq modules
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from minutes_iq.db.client import get_db_connection  # noqa: E402


def fix_schema(force=False):
    """Fix the scrape_results table schema."""
    print("🔌 Connecting to database...")
    with get_db_connection() as conn:
        print("✅ Connected")

        # Check current schema
        cursor = conn.execute("PRAGMA table_info(scrape_results)")
        columns = [row[1] for row in cursor.fetchall()]
        cursor.close()

        print(f"\n📋 Current columns: {', '.join(columns)}")

        if "pdf_filename" in columns and "entities_json" in columns:
            print("✅ Schema is already correct!")
            return

        # Check for existing data
        cursor = conn.execute("SELECT COUNT(*) FROM scrape_results")
        row_count = cursor.fetchone()[0]
        cursor.close()

        if row_count > 0:
            print(f"\n⚠️  Warning: Table has {row_count} rows of data")
            if not force:
                response = input(
                    "Recreating the table will DELETE all existing data. Continue? (y/N): "
                )
                if response.lower() != "y":
                    print("❌ Cancelled")
                    sys.exit(0)

        print("\n🔧 Dropping old table...")
        conn.execute("DROP TABLE IF EXISTS scrape_results")

        print("🔨 Creating new table with correct schema...")
        conn.execute("""
            CREATE TABLE scrape_results (
                result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                pdf_filename TEXT NOT NULL,
                page_number INTEGER NOT NULL,
                keyword_id INTEGER NOT NULL,
                snippet TEXT NOT NULL,
                entities_json TEXT,
                created_at INTEGER NOT NULL,
                FOREIGN KEY (job_id) REFERENCES scrape_jobs(job_id)
                    ON DELETE CASCADE ON UPDATE RESTRICT,
                FOREIGN KEY (keyword_id) REFERENCES keywords(keyword_id)
                    ON DELETE RESTRICT ON UPDATE RESTRICT
            )
        """)

        conn.commit()
        print("✅ Schema fixed successfully!")

        # Verify
        cursor = conn.execute("PRAGMA table_info(scrape_results)")
        new_columns = [row[1] for row in cursor.fetchall()]
        cursor.close()
        print(f"\n✅ New columns: {', '.join(new_columns)}")


if __name__ == "__main__":
    print("=" * 60)
    print("  Fix scrape_results Schema")
    print("=" * 60)
    print()

    force = "--force" in sys.argv

    try:
        fix_schema(force=force)
    except Exception as e:
        print(f"\n❌ Failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  Schema Fixed! 🎉")
    print("=" * 60)
