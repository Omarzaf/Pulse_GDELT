from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.news import NewsArticle, NewsIngestRun
from app.schemas.news import NewsIngestRequest, NewsIngestRunRead
from app.services.country_extraction import extract_country
from app.services.credibility import credibility_for_source
from app.services.news_safety import evaluate_news_safety
from app.services.news_sources import NEWS_SOURCE_FETCHERS, RawNewsItem
from app.services.translation import translate_headline

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _json_dumps(value: object) -> str:
    return json.dumps(value, sort_keys=True, default=str)


def _json_loads(value: Optional[str], fallback: object) -> object:
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def serialize_ingest_run(run: NewsIngestRun) -> NewsIngestRunRead:
    return NewsIngestRunRead(
        id=run.id,
        started_at=run.started_at,
        finished_at=run.finished_at,
        status=run.status,
        requested_sources=list(_json_loads(run.requested_sources, [])),
        countries=list(_json_loads(run.countries, [])) if run.countries else None,
        articles_seen=run.articles_seen,
        articles_created=run.articles_created,
        articles_updated=run.articles_updated,
        articles_rejected=run.articles_rejected,
        duplicate_count=run.duplicate_count,
        failed_sources=run.failed_sources,
        source_errors=dict(_json_loads(run.source_errors, {})),
        duration_seconds=run.duration_seconds,
    )


def _build_article(raw: RawNewsItem, *, translate: bool) -> tuple[Optional[NewsArticle], list[str]]:
    safety = evaluate_news_safety(raw.headline_original, raw.summary)
    if not safety.is_safe:
        return None, safety.reasons

    headline_en, translation_status = translate_headline(raw.headline_original, enabled=translate)
    country = extract_country(
        structured_countries=raw.structured_countries,
        metadata=raw.source_metadata,
        headline=headline_en,
        summary=raw.summary,
    )
    credibility, label = credibility_for_source(raw.source_key)
    published_at = raw.published_at or _utc_now()
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    article = NewsArticle(
        source_name=raw.source_name,
        source_key=raw.source_key,
        source_url=raw.source_url,
        headline_original=raw.headline_original,
        headline_en=headline_en,
        summary=raw.summary,
        language=raw.language,
        translation_status=translation_status,
        country_iso3=country[0] if country else None,
        country_name=country[1] if country else None,
        published_at=published_at,
        ingested_at=_utc_now(),
        source_credibility=credibility,
        credibility_label=label,
        safety_status="safe",
        safety_reasons=None,
        source_metadata=_json_dumps(raw.source_metadata),
    )
    return article, []


def ingest_news(db: Session, request: NewsIngestRequest) -> NewsIngestRunRead:
    sources = request.sources or list(NEWS_SOURCE_FETCHERS.keys())
    run = NewsIngestRun(
        started_at=_utc_now(),
        status="running",
        requested_sources=_json_dumps(sources),
        countries=_json_dumps(request.countries) if request.countries else None,
        source_errors="{}",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    errors: dict[str, str] = {}
    seen_urls: set[str] = set()
    try:
        for index, source_key in enumerate(sources):
            fetcher = NEWS_SOURCE_FETCHERS.get(source_key)
            if fetcher is None:
                errors[source_key] = "Unknown source"
                run.failed_sources += 1
                continue
            try:
                raw_items = fetcher(request.countries, request.limit_per_source)
            except Exception as exc:
                logger.exception("News source failed during ingest: %s", source_key)
                errors[source_key] = str(exc)
                run.failed_sources += 1
                raw_items = []

            for raw in raw_items:
                run.articles_seen += 1
                if not raw.source_url or raw.source_url in seen_urls:
                    run.duplicate_count += 1
                    continue
                seen_urls.add(raw.source_url)
                existing = db.scalar(select(NewsArticle).where(NewsArticle.source_url == raw.source_url))
                if existing:
                    run.duplicate_count += 1
                    continue
                article, rejection_reasons = _build_article(raw, translate=request.translate)
                if article is None:
                    run.articles_rejected += 1
                    logger.info("Rejected unsafe news item from %s: %s", raw.source_key, ", ".join(rejection_reasons))
                    continue
                db.add(article)
                run.articles_created += 1

            db.commit()
            if request.polite_delay_seconds and index < len(sources) - 1:
                time.sleep(request.polite_delay_seconds)

        run.status = "completed_with_errors" if errors else "completed"
    except Exception:
        logger.exception("Unexpected news ingest failure")
        run.status = "failed"
        raise
    finally:
        started_at = _as_utc(run.started_at)
        run.finished_at = _utc_now()
        run.source_errors = _json_dumps(errors)
        run.duration_seconds = max(0.0, (run.finished_at - started_at).total_seconds())
        db.add(run)
        db.commit()
        db.refresh(run)

    return serialize_ingest_run(run)
