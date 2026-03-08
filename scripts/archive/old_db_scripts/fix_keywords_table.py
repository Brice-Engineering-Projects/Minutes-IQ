#!/usr/bin/env python3
"""Fix keywords table schema in Turso database."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from minutes_iq.db.client import get_db_connection

# Connect to Turso
print("Connecting to Turso database...")
with get_db_connection() as db:
    print("Connected to Turso database")
    print("=" * 60)

    # Check current keywords table structure
    print("\n1. Checking current keywords table structure...")
    try:
        result = db.execute("PRAGMA table_info(keywords)")
        columns = result.fetchall()

        print(f"   Found {len(columns)} columns:")
        for col in columns:
            print(f"   - {col[1]} ({col[2]})")

        column_names = [col[1] for col in columns]

        # Check if category column exists
        if "category" not in column_names:
            print("\n   ⚠️  'category' column is MISSING!")
            print("\n2. Adding 'category' column...")

            # Add category column
            db.execute("ALTER TABLE keywords ADD COLUMN category TEXT")
            print("   ✅ 'category' column added successfully")

            # Verify
            result = db.execute("PRAGMA table_info(keywords)")
            columns = result.fetchall()
            column_names = [col[1] for col in columns]

            if "category" in column_names:
                print("   ✅ Verified: 'category' column now exists")
            else:
                print("   ❌ Error: 'category' column still missing!")
        else:
            print("   ✅ 'category' column already exists")

    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Check if table exists at all
    print("\n3. Verifying keywords table exists...")
    try:
        result = db.execute("SELECT COUNT(*) FROM keywords")
        count = result.fetchone()[0]
        print(f"   ✅ Table exists with {count} keywords")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print("\n   The keywords table may not exist. Run the migration:")
        print(
            "   See migration: migrations/20260125_170000_add_client_keyword_management.sql"
        )

    print("\n" + "=" * 60)
    print("Schema check complete!")
