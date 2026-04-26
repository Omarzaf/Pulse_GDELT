from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"
    __table_args__ = (UniqueConstraint("source_url", name="uq_news_articles_source_url"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    source_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    headline_original: Mapped[str] = mapped_column(Text, nullable=False)
    headline_en: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(24), nullable=True)
    translation_status: Mapped[str] = mapped_column(String(32), nullable=False, default="not_needed")
    country_iso3: Mapped[Optional[str]] = mapped_column(String(3), nullable=True, index=True)
    country_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    source_credibility: Mapped[str] = mapped_column(String(32), nullable=False, default="moderate")
    credibility_label: Mapped[str] = mapped_column(String(32), nullable=False, default="Moderate")
    safety_status: Mapped[str] = mapped_column(String(32), nullable=False, default="safe", index=True)
    safety_reasons: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class NewsIngestRun(Base):
    __tablename__ = "news_ingest_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="running", index=True)
    requested_sources: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    countries: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    articles_seen: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    articles_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    articles_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    articles_rejected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_sources: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_errors: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
