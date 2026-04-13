#!/usr/bin/env python3
"""PostgreSQL schema definition for Minutes IQ using SQLAlchemy Core."""

from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    text,
)
from sqlalchemy.engine import Engine


def _qualified_table(schema: str | None, table_name: str) -> str:
    """Return a schema-qualified table reference for foreign keys."""
    return f"{schema}.{table_name}" if schema else table_name


def build_metadata(schema: str | None = None) -> MetaData:
    """Build the canonical Minutes IQ schema for PostgreSQL."""
    metadata = MetaData()

    Table(
        "roles",
        metadata,
        Column("role_id", Integer, primary_key=True),
        Column("role_name", Text, nullable=False, unique=True),
        schema=schema,
    )

    users = Table(
        "users",
        metadata,
        Column("user_id", Integer, primary_key=True),
        Column("username", Text, nullable=False, unique=True),
        Column("email", Text, nullable=False, unique=True),
        Column(
            "role_id",
            Integer,
            ForeignKey(f"{_qualified_table(schema, 'roles')}.role_id"),
            nullable=False,
        ),
        Column(
            "force_password_change",
            Boolean,
            nullable=False,
            server_default=text("false"),
        ),
        schema=schema,
    )

    Table(
        "auth_providers",
        metadata,
        Column("provider_id", Integer, primary_key=True),
        Column("provider_name", Text, nullable=False, unique=True),
        schema=schema,
    )

    auth_credentials = Table(
        "auth_credentials",
        metadata,
        Column("credential_id", Integer, primary_key=True),
        Column(
            "user_id",
            Integer,
            ForeignKey(f"{_qualified_table(schema, 'users')}.user_id"),
            nullable=False,
        ),
        Column(
            "provider_id",
            Integer,
            ForeignKey(f"{_qualified_table(schema, 'auth_providers')}.provider_id"),
            nullable=False,
        ),
        Column("hashed_password", Text, nullable=False),
        Column("is_active", Boolean, nullable=False, server_default=text("true")),
        schema=schema,
    )

    auth_codes = Table(
        "auth_codes",
        metadata,
        Column("code_id", Integer, primary_key=True),
        Column("code", Text, nullable=False, unique=True),
        Column(
            "created_by",
            Integer,
            ForeignKey(f"{_qualified_table(schema, 'users')}.user_id"),
            nullable=False,
        ),
        Column("created_at", BigInteger, nullable=False),
        Column("expires_at", BigInteger),
        Column("max_uses", Integer, server_default=text("1")),
        Column("current_uses", Integer, server_default=text("0")),
        Column("is_active", Boolean, server_default=text("true")),
        Column("notes", Text),
        schema=schema,
    )

    code_usage = Table(
        "code_usage",
        metadata,
        Column("usage_id", Integer, primary_key=True),
        Column(
            "code_id",
            Integer,
            ForeignKey(f"{_qualified_table(schema, 'auth_codes')}.code_id"),
            nullable=False,
        ),
        Column(
            "user_id",
            Integer,
            ForeignKey(f"{_qualified_table(schema, 'users')}.user_id"),
            nullable=False,
        ),
        Column("used_at", BigInteger, nullable=False),
        schema=schema,
    )

    password_reset_tokens = Table(
        "password_reset_tokens",
        metadata,
        Column("token_id", Integer, primary_key=True),
        Column(
            "user_id",
            Integer,
            ForeignKey(
                f"{_qualified_table(schema, 'users')}.user_id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        Column("token_hash", Text, nullable=False, unique=True),
        Column("created_at", BigInteger, nullable=False),
        Column("expires_at", BigInteger, nullable=False),
        Column("used_at", BigInteger),
        Column("is_valid", Boolean, nullable=False, server_default=text("true")),
        schema=schema,
    )

    client = Table(
        "client",
        metadata,
        Column("client_id", Integer, primary_key=True),
        Column("name", Text, nullable=False, unique=True),
        Column("description", Text),
        Column("is_active", Boolean, nullable=False, server_default=text("true")),
        Column("created_at", BigInteger, nullable=False),
        Column(
            "created_by",
            Integer,
            ForeignKey(f"{_qualified_table(schema, 'users')}.user_id"),
            nullable=False,
        ),
        Column("updated_at", BigInteger),
        schema=schema,
    )

    client_urls = Table(
        "client_urls",
        metadata,
        Column("id", Integer, primary_key=True),
        Column(
            "client_id",
            Integer,
            ForeignKey(
                f"{_qualified_table(schema, 'client')}.client_id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        Column("alias", Text, nullable=False),
        Column("url", Text, nullable=False),
        Column("is_active", Boolean, nullable=False, server_default=text("true")),
        Column("last_scraped_at", BigInteger),
        Column("created_at", BigInteger, nullable=False),
        Column("updated_at", BigInteger),
        schema=schema,
    )

    keywords = Table(
        "keywords",
        metadata,
        Column("keyword_id", Integer, primary_key=True),
        Column("keyword", Text, nullable=False, unique=True),
        Column("category", Text),
        Column("description", Text),
        Column("is_active", Boolean, nullable=False, server_default=text("true")),
        Column("created_at", BigInteger, nullable=False),
        Column(
            "created_by",
            Integer,
            ForeignKey(f"{_qualified_table(schema, 'users')}.user_id"),
            nullable=False,
        ),
        schema=schema,
    )

    client_keywords = Table(
        "client_keywords",
        metadata,
        Column(
            "client_id",
            Integer,
            ForeignKey(
                f"{_qualified_table(schema, 'client')}.client_id", ondelete="CASCADE"
            ),
            primary_key=True,
            nullable=False,
        ),
        Column(
            "keyword_id",
            Integer,
            ForeignKey(
                f"{_qualified_table(schema, 'keywords')}.keyword_id", ondelete="CASCADE"
            ),
            primary_key=True,
            nullable=False,
        ),
        Column("added_at", BigInteger, nullable=False),
        Column(
            "added_by",
            Integer,
            ForeignKey(f"{_qualified_table(schema, 'users')}.user_id"),
            nullable=False,
        ),
        schema=schema,
    )

    user_client_favorites = Table(
        "user_client_favorites",
        metadata,
        Column(
            "user_id",
            Integer,
            ForeignKey(
                f"{_qualified_table(schema, 'users')}.user_id", ondelete="CASCADE"
            ),
            primary_key=True,
            nullable=False,
        ),
        Column(
            "client_id",
            Integer,
            ForeignKey(
                f"{_qualified_table(schema, 'client')}.client_id", ondelete="CASCADE"
            ),
            primary_key=True,
            nullable=False,
        ),
        Column("favorited_at", BigInteger, nullable=False),
        schema=schema,
    )

    scrape_jobs = Table(
        "scrape_jobs",
        metadata,
        Column("job_id", Integer, primary_key=True),
        Column(
            "client_url_id",
            Integer,
            ForeignKey(
                f"{_qualified_table(schema, 'client_urls')}.id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        Column("status", Text, nullable=False),
        Column(
            "created_by",
            Integer,
            ForeignKey(f"{_qualified_table(schema, 'users')}.user_id"),
            nullable=False,
        ),
        Column("created_at", BigInteger, nullable=False),
        Column("started_at", BigInteger),
        Column("completed_at", BigInteger),
        Column("error_message", Text),
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'cancelled')",
            name="ck_scrape_jobs_status",
        ),
        schema=schema,
    )

    Table(
        "scrape_job_config",
        metadata,
        Column("config_id", Integer, primary_key=True),
        Column(
            "job_id",
            Integer,
            ForeignKey(
                f"{_qualified_table(schema, 'scrape_jobs')}.job_id", ondelete="CASCADE"
            ),
            nullable=False,
            unique=True,
        ),
        Column("date_range_start", Text),
        Column("date_range_end", Text),
        Column("max_scan_pages", Integer),
        Column("include_minutes", Boolean, nullable=False, server_default=text("true")),
        Column(
            "include_packages", Boolean, nullable=False, server_default=text("true")
        ),
        schema=schema,
    )

    scrape_results = Table(
        "scrape_results",
        metadata,
        Column("result_id", Integer, primary_key=True),
        Column(
            "job_id",
            Integer,
            ForeignKey(
                f"{_qualified_table(schema, 'scrape_jobs')}.job_id", ondelete="CASCADE"
            ),
            nullable=False,
        ),
        Column("pdf_filename", Text, nullable=False),
        Column("page_number", Integer, nullable=False),
        Column(
            "keyword_id",
            Integer,
            ForeignKey(
                f"{_qualified_table(schema, 'keywords')}.keyword_id",
                ondelete="RESTRICT",
            ),
            nullable=False,
        ),
        Column("snippet", Text, nullable=False),
        Column("entities_json", Text),
        Column("created_at", BigInteger, nullable=False),
        schema=schema,
    )

    Index("idx_users_username", users.c.username)
    Index("idx_users_email", users.c.email)
    Index("idx_auth_credentials_user_id", auth_credentials.c.user_id)
    Index("idx_auth_credentials_provider_id", auth_credentials.c.provider_id)
    Index("idx_auth_credentials_is_active", auth_credentials.c.is_active)

    Index("idx_auth_codes_code", auth_codes.c.code)
    Index("idx_auth_codes_is_active", auth_codes.c.is_active)
    Index("idx_auth_codes_expires_at", auth_codes.c.expires_at)
    Index("idx_auth_codes_created_by", auth_codes.c.created_by)
    Index("idx_code_usage_code_id", code_usage.c.code_id)
    Index("idx_code_usage_user_id", code_usage.c.user_id)

    Index("idx_password_reset_token_hash", password_reset_tokens.c.token_hash)
    Index("idx_password_reset_user_id", password_reset_tokens.c.user_id)
    Index("idx_password_reset_expires_at", password_reset_tokens.c.expires_at)

    Index("idx_client_name", client.c.name)
    Index("idx_client_is_active", client.c.is_active)
    Index("idx_client_created_by", client.c.created_by)
    Index("idx_client_urls_client_id", client_urls.c.client_id)
    Index("idx_client_urls_is_active", client_urls.c.is_active)
    Index("idx_client_urls_alias", client_urls.c.alias)
    Index("idx_keywords_keyword", keywords.c.keyword)
    Index("idx_keywords_category", keywords.c.category)
    Index("idx_keywords_is_active", keywords.c.is_active)
    Index("idx_client_keywords_client_id", client_keywords.c.client_id)
    Index("idx_client_keywords_keyword_id", client_keywords.c.keyword_id)
    Index("idx_user_favorites_user_id", user_client_favorites.c.user_id)
    Index("idx_user_favorites_client_id", user_client_favorites.c.client_id)

    Index("idx_scrape_jobs_client_url_id", scrape_jobs.c.client_url_id)
    Index("idx_scrape_jobs_status", scrape_jobs.c.status)
    Index("idx_scrape_jobs_created_by", scrape_jobs.c.created_by)
    Index("idx_scrape_results_job_id", scrape_results.c.job_id)
    Index("idx_scrape_results_keyword_id", scrape_results.c.keyword_id)
    Index("idx_scrape_results_created_at", scrape_results.c.created_at)

    return metadata


def seed_reference_data(engine: Engine, schema: str | None = None) -> None:
    """Seed required lookup rows expected by Minutes IQ services."""
    table_prefix = f"{schema}." if schema else ""

    with engine.begin() as conn:
        conn.execute(
            text(
                f"INSERT INTO {table_prefix}roles (role_id, role_name) VALUES (1, 'admin') "
                "ON CONFLICT (role_id) DO NOTHING"
            )
        )
        conn.execute(
            text(
                f"INSERT INTO {table_prefix}roles (role_id, role_name) VALUES (2, 'user') "
                "ON CONFLICT (role_id) DO NOTHING"
            )
        )
        conn.execute(
            text(
                f"INSERT INTO {table_prefix}auth_providers (provider_id, provider_name) "
                "VALUES (1, 'password') ON CONFLICT (provider_id) DO NOTHING"
            )
        )
