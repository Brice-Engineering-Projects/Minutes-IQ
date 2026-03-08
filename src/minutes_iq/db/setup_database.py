#!/usr/bin/env python3
"""Initialize the Minutes IQ database from canonical schema SQL files."""

from __future__ import annotations

from pathlib import Path

from minutes_iq.db.client import get_db_connection

SCHEMA_DIR = Path(__file__).parent / "schema"
SCHEMA_FILES = [
    "001_create_tables.sql",
    "002_add_indexes.sql",
    "003_seed_auth_providers.sql",
]


def _parse_sql_statements(sql_text: str) -> list[str]:
    """Split SQL text into statements while skipping line comments."""
    statements: list[str] = []
    current: list[str] = []

    for raw_line in sql_text.splitlines():
        line = raw_line.strip()

        if not line or line.startswith("--"):
            continue

        current.append(raw_line)

        if line.endswith(";"):
            statement = "\n".join(current).strip()
            if statement:
                statements.append(statement)
            current = []

    trailing = "\n".join(current).strip()
    if trailing:
        statements.append(trailing)

    return statements


def apply_schema() -> None:
    """Apply canonical schema files in deterministic order."""
    with get_db_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")

        for filename in SCHEMA_FILES:
            file_path = SCHEMA_DIR / filename
            if not file_path.exists():
                raise FileNotFoundError(f"Missing schema file: {file_path}")

            sql_text = file_path.read_text(encoding="utf-8")
            statements = _parse_sql_statements(sql_text)

            print(f"Applying {filename} ({len(statements)} statements)...")
            for statement in statements:
                conn.execute(statement)

        conn.commit()

    print("Database schema setup complete.")


if __name__ == "__main__":
    apply_schema()
