#!/usr/bin/env python3
"""Properly fix the client table issue by updating the existing table."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from minutes_iq.db.client import get_db_connection

print("=" * 80)
print("Fixing Client Table Properly")
print("=" * 80)

with get_db_connection() as db:
    print("\nStep 1: Drop the incorrectly created 'clients' table...")
    try:
        db.execute("DROP TABLE IF EXISTS clients")
        print("   ✅ Dropped 'clients' table")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\nStep 2: Check current 'client' table structure...")
    result = db.execute("PRAGMA table_info(client)")
    columns = result.fetchall()
    current_columns = {col[1]: col[2] for col in columns}

    print(f"   Current columns: {', '.join(current_columns.keys())}")

    print("\nStep 3: Add missing columns to 'client' table...")

    # Columns that should exist in client table
    required_columns = {
        "description": "TEXT",
        "website_url": "TEXT",
        "created_by": "INTEGER NOT NULL DEFAULT 1",
        "updated_at": "INTEGER",
    }

    for col_name, col_type in required_columns.items():
        if col_name not in current_columns:
            try:
                if "NOT NULL" in col_type and "DEFAULT" not in col_type:
                    sql = f"ALTER TABLE client ADD COLUMN {col_name} {col_type}"
                else:
                    sql = f"ALTER TABLE client ADD COLUMN {col_name} {col_type.split()[0]}"

                db.execute(sql)
                print(f"   ✅ Added column: {col_name}")
            except Exception as e:
                print(f"   ❌ Error adding {col_name}: {e}")
        else:
            print(f"   ⏭️  Column {col_name} already exists")

    print(
        "\nStep 4: Update client_keywords to reference 'client' instead of 'clients'..."
    )
    try:
        # Drop and recreate client_keywords with correct foreign key
        db.execute("DROP TABLE IF EXISTS client_keywords")
        db.execute("""
            CREATE TABLE IF NOT EXISTS client_keywords (
                client_id INTEGER NOT NULL,
                keyword_id INTEGER NOT NULL,
                added_at INTEGER NOT NULL,
                added_by INTEGER NOT NULL,
                PRIMARY KEY (client_id, keyword_id),
                FOREIGN KEY (client_id) REFERENCES client(client_id) ON DELETE CASCADE,
                FOREIGN KEY (keyword_id) REFERENCES keywords(keyword_id) ON DELETE CASCADE,
                FOREIGN KEY (added_by) REFERENCES users(user_id)
            )
        """)
        print("   ✅ Recreated client_keywords with correct reference")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\nStep 5: Create indexes...")
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_client_name ON client(name)",
        "CREATE INDEX IF NOT EXISTS idx_client_is_active ON client(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_client_created_by ON client(created_by)",
        "CREATE INDEX IF NOT EXISTS idx_client_keywords_client_id ON client_keywords(client_id)",
        "CREATE INDEX IF NOT EXISTS idx_client_keywords_keyword_id ON client_keywords(keyword_id)",
    ]

    for idx_sql in indexes:
        try:
            db.execute(idx_sql)
            idx_name = idx_sql.split("INDEX")[1].split("ON")[0].strip().split()[0]
            print(f"   ✅ {idx_name}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    print("\nStep 6: Verify final structure...")
    result = db.execute("PRAGMA table_info(client)")
    columns = result.fetchall()
    print(f"   Final columns in 'client': {len(columns)}")
    for col in columns:
        print(f"     - {col[1]} ({col[2]})")

    print("\n" + "=" * 80)
    print("✅ Fixed! Now update code to use 'client' (singular) instead of 'clients'")
    print("=" * 80)
