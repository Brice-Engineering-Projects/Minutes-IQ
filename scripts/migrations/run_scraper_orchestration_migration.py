#!/usr/bin/env python3
"""
Migration script to apply scraper orchestration schema (005).

This script applies the scraper orchestration tables to the database:
- scrape_jobs
- scrape_job_config
- scrape_results

Usage:
    python run_scraper_orchestration_migration.py [--force]

Options:
    --force    Skip confirmation prompt if tables already exist
"""

import sys
from pathlib import Path

# Add src to path so we can import minutes_iq modules
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from minutes_iq.db.client import get_db_connection  # noqa: E402


def apply_migration(force=False):
    """Apply the scraper orchestration migration."""
    # Read the migration SQL file
    schema_file = (
        project_root
        / "src"
        / "minutes_iq"
        / "db"
        / "schema"
        / "005_add_scraper_orchestration.sql"
    )

    if not schema_file.exists():
        print(f"❌ Migration file not found: {schema_file}")
        sys.exit(1)

    print(f"📄 Reading migration from: {schema_file}")
    with open(schema_file) as f:
        migration_sql = f.read()

    # Connect to database
    print("🔌 Connecting to database...")
    with get_db_connection() as conn:
        print("✅ Connected to database")

        # Check if tables already exist
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN ('scrape_jobs', 'scrape_job_config', 'scrape_results')
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        cursor.close()

        if existing_tables:
            print(f"⚠️  Warning: Some tables already exist: {existing_tables}")
            if not force:
                response = input(
                    "Do you want to continue? This may fail or skip existing tables. (y/N): "
                )
                if response.lower() != "y":
                    print("❌ Migration cancelled")
                    sys.exit(0)
            else:
                print("⚡ --force flag set, continuing...")

        # Split SQL by semicolons and execute each statement
        # This handles the multiple CREATE TABLE statements
        statements = [
            s.strip()
            for s in migration_sql.split(";")
            if s.strip() and not s.strip().startswith("--")
        ]

        print(f"📝 Executing {len(statements)} SQL statements...")

        for i, statement in enumerate(statements, 1):
            # Skip comment-only statements
            if all(
                line.startswith("--") or not line.strip()
                for line in statement.split("\n")
            ):
                continue

            try:
                print(f"  [{i}/{len(statements)}] Executing statement...")
                conn.execute(statement)
                print(f"  ✅ Statement {i} executed successfully")
            except Exception as e:
                # Check if it's a "table already exists" error
                if "already exists" in str(e).lower():
                    print(f"  ⚠️  Statement {i} skipped: Table already exists")
                else:
                    print(f"  ❌ Statement {i} failed: {e}")
                    raise

        # Commit all changes
        conn.commit()
        print("\n✅ Migration completed successfully!")

        # Verify tables were created
        print("\n🔍 Verifying tables...")
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN ('scrape_jobs', 'scrape_job_config', 'scrape_results')
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()

        print(f"✅ Found {len(tables)} scraper tables:")
        for table in tables:
            # Get row count
            cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            cursor.close()
            print(f"   - {table}: {count} rows")


if __name__ == "__main__":
    print("=" * 60)
    print("  Scraper Orchestration Migration (005)")
    print("=" * 60)
    print()

    # Check for --force flag
    force = "--force" in sys.argv

    try:
        apply_migration(force=force)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 60)
    print("  Migration Complete! 🎉")
    print("=" * 60)
