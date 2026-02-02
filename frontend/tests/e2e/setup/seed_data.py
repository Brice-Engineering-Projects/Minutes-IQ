#!/usr/bin/env python3
"""
E2E Test Data Seeder

Creates baseline test data for E2E tests:
- Admin user
- Regular user
- Sample auth code
- Minimal clients / keywords

Per Phase 7.11: Run once at test startup, not per-test.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
# ruff: noqa: E402
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.minutes_iq.auth.crypto import hash_password  # noqa: E402
from src.minutes_iq.db.dependencies import get_db_connection  # noqa: E402


async def seed_baseline_data():
    """Seed baseline test data for E2E tests."""
    print("🌱 Seeding E2E test data...")

    conn = get_db_connection()

    try:
        # 1. Create admin user
        admin_email = "admin@test.local"
        admin_password = hash_password("Admin123!")

        conn.execute(
            """
            INSERT OR IGNORE INTO users (email, username, password_hash, role, is_active)
            VALUES (?, ?, ?, ?, ?)
            """,
            (admin_email, "Test Admin", admin_password, "admin", True),
        )
        print(f"  ✓ Admin user: {admin_email} / Admin123!")

        # 2. Create regular user
        user_email = "user@test.local"
        user_password = hash_password("User123!")

        conn.execute(
            """
            INSERT OR IGNORE INTO users (email, username, password_hash, role, is_active)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_email, "Test User", user_password, "user", True),
        )
        print(f"  ✓ Regular user: {user_email} / User123!")

        # 3. Create sample auth code
        auth_code = "E2E-TEST-CODE-2026"

        conn.execute(
            """
            INSERT OR IGNORE INTO auth_codes (code, created_by, max_uses, expires_at, is_active)
            VALUES (?, 1, 10, datetime('now', '+30 days'), 1)
            """,
            (auth_code,),
        )
        print(f"  ✓ Auth code: {auth_code}")

        # 4. Create sample client
        conn.execute(
            """
            INSERT OR IGNORE INTO clients (name, description, website_url, is_active)
            VALUES (?, ?, ?, ?)
            """,
            (
                "Test Agency",
                "Sample agency for E2E testing",
                "https://test-agency.example.com",
                True,
            ),
        )
        print("  ✓ Sample client: Test Agency")

        # 5. Create sample keywords
        keywords = [
            (
                "infrastructure",
                "Infrastructure & Development",
                "Infrastructure projects",
            ),
            ("budget", "Financial & Budget", "Budget and financial planning"),
            (
                "sustainability",
                "Environment & Sustainability",
                "Environmental initiatives",
            ),
        ]

        for keyword, category, description in keywords:
            conn.execute(
                """
                INSERT OR IGNORE INTO keywords (keyword, category, description, is_active)
                VALUES (?, ?, ?, ?)
                """,
                (keyword, category, description, True),
            )

        print(f"  ✓ Sample keywords: {len(keywords)} keywords created")

        # 6. Associate keywords with client
        conn.execute(
            """
            INSERT OR IGNORE INTO client_keywords (client_id, keyword_id)
            SELECT 1, id FROM keywords WHERE keyword IN ('infrastructure', 'budget')
            """,
        )
        print("  ✓ Associated keywords with Test Agency")

        conn.commit()
        print("✅ E2E test data seeding complete\n")

    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(seed_baseline_data())
