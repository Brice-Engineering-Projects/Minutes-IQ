#!/usr/bin/env python3
"""Run the client/keyword management migration on Turso database."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from minutes_iq.db.client import get_db_connection

print("=" * 80)
print("Running Client & Keyword Management Migration")
print("=" * 80)

# Read the migration SQL file
migration_file = Path("migrations/20260125_170000_add_client_keyword_management.sql")
migration_sql = migration_file.read_text()

print(f"\nReading migration from: {migration_file}")

with get_db_connection() as db:
    print("Connected to Turso database\n")

    # Check what tables currently exist
    print("1. Checking existing tables...")
    result = db.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        ORDER BY name
    """)
    existing_tables = [row[0] for row in result.fetchall()]
    print(f"   Found {len(existing_tables)} tables:")
    for table in existing_tables:
        print(f"   - {table}")

    # Split migration into statements
    statements = []
    current_statement = []

    for line in migration_sql.split("\n"):
        line = line.strip()

        # Skip comments and empty lines
        if not line or line.startswith("--"):
            continue

        current_statement.append(line)

        # If line ends with semicolon, we have a complete statement
        if line.endswith(";"):
            statement = " ".join(current_statement)
            if statement and not statement.startswith("--"):
                statements.append(statement)
            current_statement = []

    print(f"\n2. Found {len(statements)} SQL statements in migration")

    # Execute each statement
    print("\n3. Executing migration statements...")
    success_count = 0
    skip_count = 0

    for i, statement in enumerate(statements, 1):
        # Get statement type
        stmt_type = statement.split()[0].upper()

        # Get table/index name if applicable
        name = "unknown"
        if "TABLE" in statement:
            try:
                name = statement.split("TABLE")[1].split("(")[0].strip().split()[0]
            except (IndexError, AttributeError):
                pass
        elif "INDEX" in statement:
            try:
                name = statement.split("INDEX")[1].split("ON")[0].strip().split()[0]
            except (IndexError, AttributeError):
                pass

        try:
            db.execute(statement)
            print(f"   ✅ [{i}/{len(statements)}] {stmt_type} {name}")
            success_count += 1
        except Exception as e:
            error_msg = str(e)
            if "already exists" in error_msg:
                print(
                    f"   ⏭️  [{i}/{len(statements)}] {stmt_type} {name} (already exists)"
                )
                skip_count += 1
            else:
                print(f"   ❌ [{i}/{len(statements)}] {stmt_type} {name}")
                print(f"      Error: {error_msg}")

    # Verify tables were created
    print("\n4. Verifying tables...")
    result = db.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        ORDER BY name
    """)
    final_tables = [row[0] for row in result.fetchall()]

    expected_new_tables = [
        "clients",
        "keywords",
        "client_keywords",
        "user_client_favorites",
        "client_sources",
    ]

    all_present = True
    for table in expected_new_tables:
        if table in final_tables:
            print(f"   ✅ {table}")
        else:
            print(f"   ❌ {table} - MISSING")
            all_present = False

    print("\n" + "=" * 80)
    print("Migration complete!")
    print(f"  Success: {success_count}")
    print(f"  Skipped: {skip_count}")
    print(f"  Total tables: {len(final_tables)}")

    if all_present:
        print("\n✅ All expected tables are present!")
    else:
        print("\n⚠️  Some tables are missing. Check errors above.")

    print("=" * 80)
