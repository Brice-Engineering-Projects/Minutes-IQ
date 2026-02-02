#!/usr/bin/env python3
"""Check all tables and their relationships."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from minutes_iq.db.client import get_db_connection

print("=" * 80)
print("Database Schema Analysis")
print("=" * 80)

with get_db_connection() as db:
    # Get all tables
    result = db.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        ORDER BY name
    """)
    tables = [row[0] for row in result.fetchall()]

    print(f"\nFound {len(tables)} tables\n")

    # Check each table for foreign keys
    for table in tables:
        if table.startswith("sqlite_"):
            continue

        print(f"Table: {table}")

        # Get columns
        result = db.execute(f"PRAGMA table_info({table})")
        columns = result.fetchall()
        col_names = [col[1] for col in columns]
        print(f"  Columns: {', '.join(col_names)}")

        # Get foreign keys
        result = db.execute(f"PRAGMA foreign_key_list({table})")
        foreign_keys = result.fetchall()

        if foreign_keys:
            print("  Foreign Keys:")
            for fk in foreign_keys:
                print(f"    - {fk[3]} → {fk[2]}({fk[4]})")

        # Check for references to 'client' (singular)
        for fk in foreign_keys:
            if fk[2] == "client":
                print("  ⚠️  REFERENCES OLD 'client' TABLE!")

        # Get row count
        result = db.execute(f"SELECT COUNT(*) FROM {table}")
        count = result.fetchone()[0]
        print(f"  Rows: {count}")
        print()

print("=" * 80)
print("Issue Summary:")
print("=" * 80)
print("""
The database has existing tables that reference 'client' (singular).
These foreign keys are now broken because the code was changed to use
'clients' (plural) but a new table was created instead of updating the code.

Solution: Rename 'client' → 'clients' and add missing columns.
""")
