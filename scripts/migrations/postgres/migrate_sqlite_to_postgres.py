#!/usr/bin/env python3
"""Migrate data from SQLite/libSQL export into PostgreSQL.

This script migrates data only. It assumes target schema objects already exist
and were created by scripts/migrations/postgres/create_postgres_db.py.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
from pathlib import Path

from sqlalchemy import Boolean, create_engine, inspect, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.sql.sqltypes import TypeEngine
from sqlalchemy_schema import build_metadata


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate Minutes IQ data from SQLite/libSQL export to PostgreSQL."
    )
    parser.add_argument(
        "--source-sqlite-path",
        default=os.getenv("MINUTESIQ_SOURCE_SQLITE_PATH"),
        help="Path to source SQLite database file (or MINUTESIQ_SOURCE_SQLITE_PATH).",
    )
    parser.add_argument(
        "--target-url",
        default=os.getenv("MINUTESIQ_POSTGRES_URL"),
        help="Target PostgreSQL SQLAlchemy URL (or MINUTESIQ_POSTGRES_URL).",
    )
    parser.add_argument(
        "--schema",
        default=os.getenv("MINUTESIQ_POSTGRES_SCHEMA", "public"),
        help="Target PostgreSQL schema. Default: public.",
    )
    parser.add_argument(
        "--truncate-target",
        action="store_true",
        help="Truncate target tables before inserting migrated rows.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Insert batch size. Default: 1000.",
    )
    return parser.parse_args()


def _coerce_value(value: object, col_type: TypeEngine) -> object:
    if value is None:
        return None

    if isinstance(col_type, Boolean):
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value != 0
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"1", "true", "t", "yes", "y"}:
                return True
            if lowered in {"0", "false", "f", "no", "n"}:
                return False

    return value


def _qualified_name(schema: str | None, table_name: str) -> str:
    if not schema:
        return f'"{table_name}"'
    return f'"{schema}"."{table_name}"'


def _ensure_target_tables_exist(
    engine: Engine, schema: str | None, table_names: list[str]
) -> None:
    inspector = inspect(engine)
    missing = [
        name for name in table_names if not inspector.has_table(name, schema=schema)
    ]
    if missing:
        formatted = ", ".join(missing)
        raise RuntimeError(
            "Target schema is missing tables: "
            f"{formatted}. Run create_postgres_db.py first."
        )


def _truncate_target(
    conn: Connection, schema: str | None, table_names: list[str]
) -> None:
    if not table_names:
        return

    qualified = ", ".join(_qualified_name(schema, name) for name in table_names)
    conn.execute(text(f"TRUNCATE TABLE {qualified} RESTART IDENTITY CASCADE"))


def _chunked(rows: list[dict[str, object]], size: int):
    for i in range(0, len(rows), size):
        yield rows[i : i + size]


def _reset_sequence_for_integer_pk(conn: Connection, schema: str | None, table) -> None:
    pk_cols = list(table.primary_key.columns)
    if len(pk_cols) != 1:
        return

    pk_col = pk_cols[0]
    try:
        if pk_col.type.python_type is not int:
            return
    except NotImplementedError:
        return

    qualified_table_for_fn = f"{schema}.{table.name}" if schema else table.name
    max_value = conn.execute(
        text(
            f"SELECT COALESCE(MAX({pk_col.name}), 0) FROM {_qualified_name(schema, table.name)}"
        )
    ).scalar_one()

    conn.execute(
        text(
            "SELECT setval(pg_get_serial_sequence(:table_name, :column_name), :value, true)"
        ),
        {
            "table_name": qualified_table_for_fn,
            "column_name": pk_col.name,
            "value": max_value,
        },
    )


def migrate_data(
    source_sqlite_path: str,
    target_url: str,
    schema: str,
    truncate_target: bool,
    batch_size: int,
) -> None:
    source_path = Path(source_sqlite_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Source SQLite file not found: {source_path}")

    target_schema = None if schema == "public" else schema

    metadata = build_metadata(schema=target_schema)
    table_order = [table.name for table in metadata.sorted_tables]

    sqlite_conn = sqlite3.connect(source_path)
    sqlite_conn.row_factory = sqlite3.Row
    source_tables = {
        row[0]
        for row in sqlite_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }

    pg_engine = create_engine(target_url, future=True, pool_pre_ping=True)
    _ensure_target_tables_exist(pg_engine, target_schema, table_order)

    with pg_engine.begin() as pg_conn:
        if truncate_target:
            print("Truncating target tables...")
            _truncate_target(pg_conn, target_schema, table_order)

        row_counts: list[tuple[str, int, int]] = []

        for table in metadata.sorted_tables:
            table_name = table.name
            if table_name not in source_tables:
                target_count = pg_conn.execute(
                    text(
                        f"SELECT COUNT(*) FROM {_qualified_name(target_schema, table_name)}"
                    )
                ).scalar_one()
                row_counts.append((table_name, 0, int(target_count)))
                print(f"{table_name}: source table not found (skipped)")
                continue

            sqlite_rows = sqlite_conn.execute(f"SELECT * FROM {table_name}").fetchall()
            source_count = len(sqlite_rows)

            if source_count == 0:
                target_count = pg_conn.execute(
                    text(
                        f"SELECT COUNT(*) FROM {_qualified_name(target_schema, table_name)}"
                    )
                ).scalar_one()
                row_counts.append((table_name, 0, int(target_count)))
                print(f"{table_name}: 0 rows (skipped)")
                continue

            insert_rows: list[dict[str, object]] = []
            for row in sqlite_rows:
                row_dict = dict(row)
                transformed: dict[str, object] = {}

                for column in table.columns:
                    if column.name in row_dict:
                        transformed[column.name] = _coerce_value(
                            row_dict[column.name], column.type
                        )

                insert_rows.append(transformed)

            for chunk in _chunked(insert_rows, max(1, batch_size)):
                pg_conn.execute(table.insert(), chunk)

            _reset_sequence_for_integer_pk(pg_conn, target_schema, table)

            target_count = pg_conn.execute(
                text(
                    f"SELECT COUNT(*) FROM {_qualified_name(target_schema, table_name)}"
                )
            ).scalar_one()
            row_counts.append((table_name, source_count, int(target_count)))
            print(f"{table_name}: migrated {source_count} rows")

    sqlite_conn.close()

    print("\nRow count validation:")
    mismatch_found = False
    for table_name, source_count, target_count in row_counts:
        status = "OK" if source_count == target_count else "MISMATCH"
        print(
            f"  - {table_name}: source={source_count} target={target_count} [{status}]"
        )
        if source_count != target_count:
            mismatch_found = True

    if mismatch_found:
        raise RuntimeError("Data migration completed with row-count mismatches.")


def main() -> int:
    args = _parse_args()

    if not args.source_sqlite_path:
        print("Missing --source-sqlite-path (or MINUTESIQ_SOURCE_SQLITE_PATH).")
        return 1

    if not args.target_url:
        print("Missing --target-url (or MINUTESIQ_POSTGRES_URL).")
        return 1

    if args.batch_size < 1:
        print("--batch-size must be >= 1.")
        return 1

    migrate_data(
        source_sqlite_path=args.source_sqlite_path,
        target_url=args.target_url,
        schema=args.schema,
        truncate_target=args.truncate_target,
        batch_size=args.batch_size,
    )

    print("Data migration complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
