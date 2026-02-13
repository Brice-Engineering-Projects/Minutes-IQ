#!/usr/bin/env python3
"""Check both client tables to see what needs to be done."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from minutes_iq.db.client import get_db_connection

print("=" * 80)
print("Checking Client Tables")
print("=" * 80)

with get_db_connection() as db:
    # 1. Check structure of 'client' (singular)
    print("\n1. Structure of 'client' (singular):")
    try:
        result = db.execute("PRAGMA table_info(client)")
        columns = result.fetchall()
        print(f"   Columns: {len(columns)}")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")

        # Check data
        result = db.execute("SELECT COUNT(*) FROM client")
        count = result.fetchone()[0]
        print(f"\n   Rows: {count}")

        if count > 0:
            result = db.execute("SELECT * FROM client LIMIT 5")
            rows = result.fetchall()
            print(f"\n   Sample data (first {len(rows)} rows):")
            for i, row in enumerate(rows, 1):
                print(f"   {i}. {row}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # 2. Check structure of 'clients' (plural)
    print("\n2. Structure of 'clients' (plural):")
    try:
        result = db.execute("PRAGMA table_info(clients)")
        columns = result.fetchall()
        print(f"   Columns: {len(columns)}")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")

        # Check data
        result = db.execute("SELECT COUNT(*) FROM clients")
        count = result.fetchone()[0]
        print(f"\n   Rows: {count}")

        if count > 0:
            result = db.execute("SELECT * FROM clients LIMIT 5")
            rows = result.fetchall()
            print(f"\n   Sample data (first {len(rows)} rows):")
            for i, row in enumerate(rows, 1):
                print(f"   {i}. {row}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n" + "=" * 80)
    print("Analysis:")
    print("=" * 80)
    print("""
Your database has TWO client tables:
  - 'client' (singular) - old table
  - 'clients' (plural) - new table (created by fix script)

The application code uses 'clients' (plural), so:
  - If 'client' has important data → migrate it to 'clients'
  - If 'client' is empty/old → can safely drop it

See the data counts above to decide.
""")
