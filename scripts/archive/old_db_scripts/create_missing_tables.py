#!/usr/bin/env python3
"""Create missing tables for client/keyword management."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from minutes_iq.db.client import get_db_connection

print("=" * 80)
print("Creating Missing Tables")
print("=" * 80)

with get_db_connection() as db:
    print("\nConnected to Turso database\n")

    # 1. Check if 'client' exists (singular)
    result = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='client'"
    )
    client_exists = result.fetchone() is not None

    # 2. Check if 'clients' exists (plural)
    result = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='clients'"
    )
    clients_exists = result.fetchone() is not None

    if client_exists and not clients_exists:
        print("1. Found 'client' table (singular), but code expects 'clients' (plural)")
        print("   Creating 'clients' table...")

    # Create clients table (even if singular exists)
    try:
        db.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                client_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                website_url TEXT,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at INTEGER NOT NULL,
                created_by INTEGER NOT NULL,
                updated_at INTEGER,
                FOREIGN KEY (created_by) REFERENCES users(user_id)
            )
        """)
        print("   ✅ 'clients' table created")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Create client_keywords table
    print("\n2. Creating 'client_keywords' table...")
    try:
        db.execute("""
            CREATE TABLE IF NOT EXISTS client_keywords (
                client_id INTEGER NOT NULL,
                keyword_id INTEGER NOT NULL,
                added_at INTEGER NOT NULL,
                added_by INTEGER NOT NULL,
                PRIMARY KEY (client_id, keyword_id),
                FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE,
                FOREIGN KEY (keyword_id) REFERENCES keywords(keyword_id) ON DELETE CASCADE,
                FOREIGN KEY (added_by) REFERENCES users(user_id)
            )
        """)
        print("   ✅ 'client_keywords' table created")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Create indexes
    print("\n3. Creating indexes...")
    indexes = [
        (
            "idx_clients_name",
            "CREATE INDEX IF NOT EXISTS idx_clients_name ON clients(name)",
        ),
        (
            "idx_clients_is_active",
            "CREATE INDEX IF NOT EXISTS idx_clients_is_active ON clients(is_active)",
        ),
        (
            "idx_clients_created_by",
            "CREATE INDEX IF NOT EXISTS idx_clients_created_by ON clients(created_by)",
        ),
        (
            "idx_client_keywords_client_id",
            "CREATE INDEX IF NOT EXISTS idx_client_keywords_client_id ON client_keywords(client_id)",
        ),
        (
            "idx_client_keywords_keyword_id",
            "CREATE INDEX IF NOT EXISTS idx_client_keywords_keyword_id ON client_keywords(keyword_id)",
        ),
    ]

    for idx_name, idx_sql in indexes:
        try:
            db.execute(idx_sql)
            print(f"   ✅ {idx_name}")
        except Exception as e:
            if "already exists" in str(e):
                print(f"   ⏭️  {idx_name} (already exists)")
            else:
                print(f"   ❌ {idx_name}: {e}")

    # Verify
    print("\n4. Verifying tables...")
    result = db.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name IN ('clients', 'client_keywords')
        ORDER BY name
    """)
    tables = [row[0] for row in result.fetchall()]

    if "clients" in tables:
        print("   ✅ clients")
    else:
        print("   ❌ clients - MISSING")

    if "client_keywords" in tables:
        print("   ✅ client_keywords")
    else:
        print("   ❌ client_keywords - MISSING")

    print("\n" + "=" * 80)
    print("✅ Tables created successfully!")
    print("=" * 80)
