#!/usr/bin/env python3
"""Apply users.force_password_change migration safely (idempotent)."""

from __future__ import annotations

import sys
from pathlib import Path

# Add project src to import path.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from minutes_iq.db.client import get_db_connection  # noqa: E402


def main() -> int:
    print("=" * 72)
    print("Force Password Change Migration - v20260307_120000")
    print("=" * 72)

    with get_db_connection() as db:
        print("\nConnected to database")

        columns = [row[1] for row in db.execute("PRAGMA table_info(users)").fetchall()]

        if "force_password_change" in columns:
            print("\nMigration already applied: users.force_password_change exists")
            return 0

        print("\nApplying migration: adding users.force_password_change...")
        db.execute(
            """
            ALTER TABLE users
            ADD COLUMN force_password_change INTEGER NOT NULL DEFAULT 0;
            """.strip()
        )
        db.commit()

        updated_columns = [
            row[1] for row in db.execute("PRAGMA table_info(users)").fetchall()
        ]

        if "force_password_change" not in updated_columns:
            print("\nMigration failed: column not found after ALTER TABLE")
            return 1

        print("\nMigration applied successfully")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
