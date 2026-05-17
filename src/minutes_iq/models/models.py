"""SQLAlchemy ORM models for the Minutes IQ PostgreSQL schema."""

from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Text,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for the Minutes IQ database models."""

    metadata = MetaData()


class Role(Base):
    __tablename__ = "roles"

    role_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)

    users: Mapped[list[User]] = relationship(back_populates="role")


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    email: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.role_id"), nullable=False)
    force_password_change: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )

    role: Mapped[Role] = relationship(back_populates="users")
    auth_credentials: Mapped[list[AuthCredential]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    created_auth_codes: Mapped[list[AuthCode]] = relationship(
        back_populates="created_by_user"
    )
    code_usage_entries: Mapped[list[CodeUsage]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    password_reset_tokens: Mapped[list[PasswordResetToken]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    clients_created: Mapped[list[Client]] = relationship(
        back_populates="created_by_user"
    )
    keywords_created: Mapped[list[Keyword]] = relationship(
        back_populates="created_by_user"
    )
    client_keywords_added: Mapped[list[ClientKeyword]] = relationship(
        back_populates="added_by_user"
    )
    favorites: Mapped[list[UserClientFavorite]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    scrape_jobs_created: Mapped[list[ScrapeJob]] = relationship(
        back_populates="created_by_user"
    )


class AuthProvider(Base):
    __tablename__ = "auth_providers"

    provider_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider_name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)

    auth_credentials: Mapped[list[AuthCredential]] = relationship(
        back_populates="provider"
    )


class AuthCredential(Base):
    __tablename__ = "auth_credentials"

    credential_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    provider_id: Mapped[int] = mapped_column(
        ForeignKey("auth_providers.provider_id"), nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    user: Mapped[User] = relationship(back_populates="auth_credentials")
    provider: Mapped[AuthProvider] = relationship(back_populates="auth_credentials")


class AuthCode(Base):
    __tablename__ = "auth_codes"

    code_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    expires_at: Mapped[int | None] = mapped_column(BigInteger)
    max_uses: Mapped[int | None] = mapped_column(Integer, server_default=text("1"))
    current_uses: Mapped[int | None] = mapped_column(Integer, server_default=text("0"))
    is_active: Mapped[bool | None] = mapped_column(Boolean, server_default=text("true"))
    notes: Mapped[str | None] = mapped_column(Text)

    created_by_user: Mapped[User] = relationship(back_populates="created_auth_codes")
    usage_entries: Mapped[list[CodeUsage]] = relationship(
        back_populates="auth_code", cascade="all, delete-orphan"
    )


class CodeUsage(Base):
    __tablename__ = "code_usage"

    usage_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code_id: Mapped[int] = mapped_column(
        ForeignKey("auth_codes.code_id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    used_at: Mapped[int] = mapped_column(BigInteger, nullable=False)

    auth_code: Mapped[AuthCode] = relationship(back_populates="usage_entries")
    user: Mapped[User] = relationship(back_populates="code_usage_entries")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    token_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    expires_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    used_at: Mapped[int | None] = mapped_column(BigInteger)
    is_valid: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    user: Mapped[User] = relationship(back_populates="password_reset_tokens")


class Client(Base):
    __tablename__ = "client"

    client_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    updated_at: Mapped[int | None] = mapped_column(BigInteger)

    created_by_user: Mapped[User] = relationship(back_populates="clients_created")
    urls: Mapped[list[ClientUrl]] = relationship(
        back_populates="client", cascade="all, delete-orphan"
    )
    keywords: Mapped[list[ClientKeyword]] = relationship(
        back_populates="client", cascade="all, delete-orphan"
    )
    favorites: Mapped[list[UserClientFavorite]] = relationship(
        back_populates="client", cascade="all, delete-orphan"
    )


class ClientUrl(Base):
    __tablename__ = "client_urls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("client.client_id", ondelete="CASCADE"), nullable=False
    )
    alias: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    last_scraped_at: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    updated_at: Mapped[int | None] = mapped_column(BigInteger)

    client: Mapped[Client] = relationship(back_populates="urls")
    scrape_jobs: Mapped[list[ScrapeJob]] = relationship(
        back_populates="client_url", cascade="all, delete-orphan"
    )


class Keyword(Base):
    __tablename__ = "keywords"

    keyword_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    category: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)

    created_by_user: Mapped[User] = relationship(back_populates="keywords_created")
    client_keywords: Mapped[list[ClientKeyword]] = relationship(
        back_populates="keyword", cascade="all, delete-orphan"
    )
    scrape_results: Mapped[list[ScrapeResult]] = relationship(back_populates="keyword")


class ClientKeyword(Base):
    __tablename__ = "client_keywords"

    client_id: Mapped[int] = mapped_column(
        ForeignKey("client.client_id", ondelete="CASCADE"), primary_key=True
    )
    keyword_id: Mapped[int] = mapped_column(
        ForeignKey("keywords.keyword_id", ondelete="CASCADE"), primary_key=True
    )
    added_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    added_by: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)

    client: Mapped[Client] = relationship(back_populates="keywords")
    keyword: Mapped[Keyword] = relationship(back_populates="client_keywords")
    added_by_user: Mapped[User] = relationship(back_populates="client_keywords_added")


class UserClientFavorite(Base):
    __tablename__ = "user_client_favorites"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey("client.client_id", ondelete="CASCADE"), primary_key=True
    )
    favorited_at: Mapped[int] = mapped_column(BigInteger, nullable=False)

    user: Mapped[User] = relationship(back_populates="favorites")
    client: Mapped[Client] = relationship(back_populates="favorites")


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'cancelled')",
            name="ck_scrape_jobs_status",
        ),
    )

    job_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_url_id: Mapped[int] = mapped_column(
        ForeignKey("client_urls.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    started_at: Mapped[int | None] = mapped_column(BigInteger)
    completed_at: Mapped[int | None] = mapped_column(BigInteger)
    error_message: Mapped[str | None] = mapped_column(Text)

    client_url: Mapped[ClientUrl] = relationship(back_populates="scrape_jobs")
    created_by_user: Mapped[User] = relationship(back_populates="scrape_jobs_created")
    config: Mapped[ScrapeJobConfig | None] = relationship(
        back_populates="job", cascade="all, delete-orphan", uselist=False
    )
    results: Mapped[list[ScrapeResult]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class ScrapeJobConfig(Base):
    __tablename__ = "scrape_job_config"

    config_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("scrape_jobs.job_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    date_range_start: Mapped[str | None] = mapped_column(Text)
    date_range_end: Mapped[str | None] = mapped_column(Text)
    max_scan_pages: Mapped[int | None] = mapped_column(Integer)
    include_minutes: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    include_packages: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    job: Mapped[ScrapeJob] = relationship(back_populates="config")


class ScrapeResult(Base):
    __tablename__ = "scrape_results"

    result_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(
        ForeignKey("scrape_jobs.job_id", ondelete="CASCADE"), nullable=False
    )
    pdf_filename: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    keyword_id: Mapped[int] = mapped_column(
        ForeignKey("keywords.keyword_id", ondelete="RESTRICT"), nullable=False
    )
    snippet: Mapped[str] = mapped_column(Text, nullable=False)
    entities_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)

    job: Mapped[ScrapeJob] = relationship(back_populates="results")
    keyword: Mapped[Keyword] = relationship(back_populates="scrape_results")


Index("idx_users_username", User.username)
Index("idx_users_email", User.email)
Index("idx_auth_credentials_user_id", AuthCredential.user_id)
Index("idx_auth_credentials_provider_id", AuthCredential.provider_id)
Index("idx_auth_credentials_is_active", AuthCredential.is_active)
Index("idx_auth_codes_code", AuthCode.code)
Index("idx_auth_codes_is_active", AuthCode.is_active)
Index("idx_auth_codes_expires_at", AuthCode.expires_at)
Index("idx_auth_codes_created_by", AuthCode.created_by)
Index("idx_code_usage_code_id", CodeUsage.code_id)
Index("idx_code_usage_user_id", CodeUsage.user_id)
Index("idx_password_reset_token_hash", PasswordResetToken.token_hash)
Index("idx_password_reset_user_id", PasswordResetToken.user_id)
Index("idx_password_reset_expires_at", PasswordResetToken.expires_at)
Index("idx_client_name", Client.name)
Index("idx_client_is_active", Client.is_active)
Index("idx_client_created_by", Client.created_by)
Index("idx_client_urls_client_id", ClientUrl.client_id)
Index("idx_client_urls_is_active", ClientUrl.is_active)
Index("idx_client_urls_alias", ClientUrl.alias)
Index("idx_keywords_keyword", Keyword.keyword)
Index("idx_keywords_category", Keyword.category)
Index("idx_keywords_is_active", Keyword.is_active)
Index("idx_client_keywords_client_id", ClientKeyword.client_id)
Index("idx_client_keywords_keyword_id", ClientKeyword.keyword_id)
Index("idx_user_favorites_user_id", UserClientFavorite.user_id)
Index("idx_user_favorites_client_id", UserClientFavorite.client_id)
Index("idx_scrape_jobs_client_url_id", ScrapeJob.client_url_id)
Index("idx_scrape_jobs_status", ScrapeJob.status)
Index("idx_scrape_jobs_created_by", ScrapeJob.created_by)
Index("idx_scrape_results_job_id", ScrapeResult.job_id)
Index("idx_scrape_results_keyword_id", ScrapeResult.keyword_id)
Index("idx_scrape_results_created_at", ScrapeResult.created_at)


__all__ = [
    "Base",
    "Role",
    "User",
    "AuthProvider",
    "AuthCredential",
    "AuthCode",
    "CodeUsage",
    "PasswordResetToken",
    "Client",
    "ClientUrl",
    "Keyword",
    "ClientKeyword",
    "UserClientFavorite",
    "ScrapeJob",
    "ScrapeJobConfig",
    "ScrapeResult",
]
