#!/usr/bin/env python3
"""Fix complete keywords table schema in Turso database."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from minutes_iq.db.client import get_db_connection

# Expected schema from migration
EXPECTED_COLUMNS = {
    "keyword_id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "keyword": "TEXT NOT NULL UNIQUE",
    "category": "TEXT",
    "description": "TEXT",
    "is_active": "INTEGER NOT NULL DEFAULT 1",
    "created_at": "INTEGER NOT NULL",
    "created_by": "INTEGER NOT NULL",
}

print("Connecting to Turso database...")
with get_db_connection() as db:
    print("Connected to Turso database")
    print("=" * 80)

    # Check current keywords table structure
    print("\n1. Checking current keywords table structure...")
    result = db.execute("PRAGMA table_info(keywords)")
    columns = result.fetchall()

    print(f"   Found {len(columns)} columns:")
    current_columns = {}
    for col in columns:
        col_name = col[1]
        col_type = col[2]
        current_columns[col_name] = col_type
        print(f"   - {col_name} ({col_type})")

    # Find missing columns
    missing_columns = []
    for expected_col, expected_type in EXPECTED_COLUMNS.items():
        if expected_col not in current_columns:
            missing_columns.append((expected_col, expected_type))

    if missing_columns:
        print(f"\n   ⚠️  Found {len(missing_columns)} missing columns!")
        for col_name, col_type in missing_columns:
            print(f"      - {col_name} ({col_type})")

        print("\n2. Adding missing columns...")
        for col_name, col_def in missing_columns:
            # Parse the column definition for ALTER TABLE
            if "NOT NULL" in col_def and "DEFAULT" not in col_def:
                if col_name == "created_at":
                    # Add with default for NOT NULL columns
                    sql = f"ALTER TABLE keywords ADD COLUMN {col_name} INTEGER NOT NULL DEFAULT 0"
                elif col_name == "created_by":
                    # Add with default for NOT NULL columns
                    sql = f"ALTER TABLE keywords ADD COLUMN {col_name} INTEGER NOT NULL DEFAULT 1"
                else:
                    sql = f"ALTER TABLE keywords ADD COLUMN {col_name} TEXT NOT NULL DEFAULT ''"
            else:
                # Extract just the type
                col_type_only = col_def.split()[0]
                sql = f"ALTER TABLE keywords ADD COLUMN {col_name} {col_type_only}"

            try:
                db.execute(sql)
                print(f"   ✅ Added: {col_name}")
            except Exception as e:
                print(f"   ❌ Error adding {col_name}: {e}")

        # Verify all columns exist now
        print("\n3. Verifying schema...")
        result = db.execute("PRAGMA table_info(keywords)")
        columns = result.fetchall()
        current_columns = {col[1]: col[2] for col in columns}

        all_present = True
        for expected_col in EXPECTED_COLUMNS.keys():
            if expected_col in current_columns:
                print(f"   ✅ {expected_col}")
            else:
                print(f"   ❌ {expected_col} - STILL MISSING")
                all_present = False

        if all_present:
            print("\n   ✅ All columns present!")
        else:
            print("\n   ❌ Some columns still missing")

    else:
        print("   ✅ All expected columns already exist")

    # Check row count
    print("\n4. Checking keyword count...")
    result = db.execute("SELECT COUNT(*) FROM keywords")
    count = result.fetchone()[0]
    print(f"   ✅ Table has {count} keywords")

    print("\n" + "=" * 80)
    print("Schema fix complete!")
