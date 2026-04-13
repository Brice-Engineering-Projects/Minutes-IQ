#!/usr/bin/env python3
"""Create the Minutes IQ schema in PostgreSQL using SQLAlchemy Core."""

from __future__ import annotations

import argparse
import os
import re
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy_schema import build_metadata, seed_reference_data


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create Minutes IQ tables/indexes in PostgreSQL via SQLAlchemy."
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv("MINUTESIQ_POSTGRES_URL"),
        help="SQLAlchemy Postgres URL (or set MINUTESIQ_POSTGRES_URL).",
    )
    parser.add_argument(
        "--schema",
        default=os.getenv("MINUTESIQ_POSTGRES_SCHEMA", "public"),
        help="Target PostgreSQL schema. Default: public.",
    )
    parser.add_argument(
        "--drop-existing",
        action="store_true",
        help="Drop existing tables before creating them.",
    )
    parser.add_argument(
        "--skip-seed",
        action="store_true",
        help="Skip seeding required role/provider reference rows.",
    )
    parser.add_argument(
        "--echo-sql",
        action="store_true",
        help="Echo SQL statements while running.",
    )
    parser.add_argument(
        "--create-db-if-missing",
        action="store_true",
        help="Create the database first using --admin-url and --db-name.",
    )
    parser.add_argument(
        "--admin-url",
        default=os.getenv("MINUTESIQ_POSTGRES_ADMIN_URL"),
        help="Admin Postgres URL to create database (usually postgres DB).",
    )
    parser.add_argument(
        "--db-name",
        default=os.getenv("MINUTESIQ_POSTGRES_DB_NAME"),
        help="Database name to create when using --create-db-if-missing.",
    )
    return parser.parse_args()


def _validate_db_name(db_name: str) -> None:
    if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", db_name):
        raise ValueError(
            "Invalid db name. Use only letters, numbers, and underscores, "
            "starting with a letter/underscore."
        )


def _database_url_with_name(url_str: str, db_name: str) -> str:
    parsed = make_url(url_str)
    if parsed:
        return str(parsed.set(database=db_name))

    # Fallback: treat as full URL and replace trailing path segment.
    if "/" not in url_str:
        raise ValueError("Invalid --database-url format.")
    base, _, _ = url_str.rpartition("/")
    return f"{base}/{quote_plus(db_name)}"


def create_database_if_missing(
    admin_url: str, db_name: str, echo_sql: bool = False
) -> None:
    """Create the target database if it does not already exist."""
    _validate_db_name(db_name)

    admin_engine = create_engine(
        admin_url,
        isolation_level="AUTOCOMMIT",
        future=True,
        pool_pre_ping=True,
        echo=echo_sql,
    )

    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
            {"db_name": db_name},
        ).scalar_one_or_none()

        if exists:
            print(f"Database '{db_name}' already exists.")
            return

        conn.execute(text(f'CREATE DATABASE "{db_name}"'))
        print(f"Created database '{db_name}'.")


def create_schema(
    database_url: str,
    schema: str,
    drop_existing: bool,
    seed_data: bool,
    echo_sql: bool,
) -> None:
    """Create all canonical Minutes IQ objects in PostgreSQL."""
    target_schema = None if schema == "public" else schema

    engine = create_engine(database_url, future=True, pool_pre_ping=True, echo=echo_sql)
    metadata = build_metadata(schema=target_schema)

    with engine.begin() as conn:
        conn.execute(text("SELECT 1"))
        if target_schema:
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{target_schema}"'))

    if drop_existing:
        print("Dropping existing schema objects...")
        metadata.drop_all(engine, checkfirst=True)

    print("Creating schema objects...")
    metadata.create_all(engine, checkfirst=True)

    if seed_data:
        print("Seeding reference data...")
        seed_reference_data(engine, schema=target_schema)


def main() -> int:
    args = _parse_args()

    if not args.database_url:
        print("Missing --database-url (or MINUTESIQ_POSTGRES_URL).")
        return 1

    if args.create_db_if_missing:
        if not args.admin_url or not args.db_name:
            print(
                "--create-db-if-missing requires both --admin-url "
                "(or MINUTESIQ_POSTGRES_ADMIN_URL) and --db-name "
                "(or MINUTESIQ_POSTGRES_DB_NAME)."
            )
            return 1

        create_database_if_missing(
            admin_url=args.admin_url,
            db_name=args.db_name,
            echo_sql=args.echo_sql,
        )

        # Allow passing an admin URL plus db name to construct final URL quickly.
        if args.database_url == args.admin_url:
            args.database_url = _database_url_with_name(args.database_url, args.db_name)

    create_schema(
        database_url=args.database_url,
        schema=args.schema,
        drop_existing=args.drop_existing,
        seed_data=not args.skip_seed,
        echo_sql=args.echo_sql,
    )

    print("PostgreSQL setup complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
