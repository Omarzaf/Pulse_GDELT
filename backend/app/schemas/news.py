from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class NewsArticleRead(BaseModel):
    id: int
    source_name: str
    source_key: str
    source_url: str
    headline_original: str
    headline_en: str
    summary: Optional[str] = None
    language: Optional[str] = None
    translation_status: str
    country_iso3: Optional[str] = None
    country_name: Optional[str] = None
    published_at: datetime
    ingested_at: datetime
    source_credibility: str
    credibility_label: str

    model_config = {"from_attributes": True}


class CountryLatestNewsResponse(BaseModel):
    iso3: str
    connected: bool = True
    hours: int
    limit: int
    articles: list[NewsArticleRead]
    empty_state: Optional[str] = None


class CountryNewsHistoryResponse(BaseModel):
    iso3: str
    connected: bool = True
    days: int
    limit: int
    articles: list[NewsArticleRead]
    empty_state: Optional[str] = None


class NewsIngestRunRead(BaseModel):
    id: int
    started_at: datetime
    finished_at: Optional[datetime] = None
    status: str
    requested_sources: list[str]
    countries: Optional[list[str]] = None
    articles_seen: int
    articles_created: int
    articles_updated: int
    articles_rejected: int
    duplicate_count: int
    failed_sources: int
    source_errors: dict[str, str]
    duration_seconds: Optional[float] = None

    model_config = {"from_attributes": True}


class NewsIngestRequest(BaseModel):
    sources: Optional[list[str]] = Field(
        default=None,
        description="Source keys to ingest. Defaults to every configured free source.",
    )
    countries: Optional[list[str]] = Field(
        default=None,
        description="Optional ISO3 or country names to narrow source queries.",
    )
    limit_per_source: int = Field(default=10, ge=1, le=50)
    translate: bool = True
    polite_delay_seconds: float = Field(default=1.0, ge=0.0, le=5.0)


class NewsListResponse(BaseModel):
    connected: bool = True
    total: int
    limit: int
    offset: int
    articles: list[NewsArticleRead]
    metadata: dict[str, Any] = Field(default_factory=dict)
