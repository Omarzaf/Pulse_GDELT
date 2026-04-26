from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.news import NewsArticle, NewsIngestRun
from app.schemas.news import (
    CountryLatestNewsResponse,
    CountryNewsHistoryResponse,
    NewsArticleRead,
    NewsIngestRequest,
    NewsIngestRunRead,
    NewsListResponse,
)
from app.services.news_ingest import ingest_news, serialize_ingest_run

router = APIRouter()

LATEST_EMPTY_STATE = "No public news reports found in the last 48 hours."
HISTORY_EMPTY_STATE = "No historical public news reports found for this country."


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_articles_statement():
    return select(NewsArticle).where(NewsArticle.safety_status == "safe")


@router.get("/countries/{iso3}/news/latest", response_model=CountryLatestNewsResponse)
def get_country_latest_news(
    iso3: str,
    hours: int = Query(default=48, ge=1, le=24 * 14),
    limit: int = Query(default=5, ge=1, le=50),
    db: Session = Depends(get_db),
) -> CountryLatestNewsResponse:
    country_iso3 = iso3.upper()
    cutoff = _utc_now() - timedelta(hours=hours)
    statement = (
        _safe_articles_statement()
        .where(NewsArticle.country_iso3 == country_iso3)
        .where(NewsArticle.published_at >= cutoff)
        .order_by(NewsArticle.published_at.desc())
        .limit(limit)
    )
    articles = list(db.scalars(statement))
    return CountryLatestNewsResponse(
        iso3=country_iso3,
        connected=True,
        hours=hours,
        limit=limit,
        articles=[NewsArticleRead.model_validate(article) for article in articles],
        empty_state=None if articles else LATEST_EMPTY_STATE,
    )


@router.get("/countries/{iso3}/news/history", response_model=CountryNewsHistoryResponse)
def get_country_news_history(
    iso3: str,
    days: int = Query(default=30, ge=1, le=366),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> CountryNewsHistoryResponse:
    country_iso3 = iso3.upper()
    now = _utc_now()
    start = now - timedelta(days=days)
    latest_boundary = now - timedelta(hours=48)
    statement = (
        _safe_articles_statement()
        .where(NewsArticle.country_iso3 == country_iso3)
        .where(NewsArticle.published_at >= start)
        .where(NewsArticle.published_at < latest_boundary)
        .order_by(NewsArticle.published_at.desc())
        .limit(limit)
    )
    articles = list(db.scalars(statement))
    return CountryNewsHistoryResponse(
        iso3=country_iso3,
        connected=True,
        days=days,
        limit=limit,
        articles=[NewsArticleRead.model_validate(article) for article in articles],
        empty_state=None if articles else HISTORY_EMPTY_STATE,
    )


@router.get("/news", response_model=NewsListResponse)
def list_news(
    iso3: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=250),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> NewsListResponse:
    statement = _safe_articles_statement()
    count_statement = select(func.count(NewsArticle.id)).where(NewsArticle.safety_status == "safe")
    if iso3:
        country_iso3 = iso3.upper()
        statement = statement.where(NewsArticle.country_iso3 == country_iso3)
        count_statement = count_statement.where(NewsArticle.country_iso3 == country_iso3)
    statement = statement.order_by(NewsArticle.published_at.desc()).offset(offset).limit(limit)
    articles = list(db.scalars(statement))
    total = int(db.scalar(count_statement) or 0)
    return NewsListResponse(
        connected=True,
        total=total,
        limit=limit,
        offset=offset,
        articles=[NewsArticleRead.model_validate(article) for article in articles],
        metadata={"credibility_basis": "source confidence only"},
    )


@router.post("/ingest/news", response_model=NewsIngestRunRead)
def create_news_ingest_run(
    request: Optional[NewsIngestRequest] = None,
    db: Session = Depends(get_db),
) -> NewsIngestRunRead:
    return ingest_news(db, request or NewsIngestRequest())


@router.get("/ingest/news/runs", response_model=list[NewsIngestRunRead])
def list_news_ingest_runs(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[NewsIngestRunRead]:
    statement = select(NewsIngestRun).order_by(NewsIngestRun.started_at.desc()).limit(limit)
    return [serialize_ingest_run(run) for run in db.scalars(statement)]
