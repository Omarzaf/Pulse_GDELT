from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.news import NewsArticle
from app.services import news_ingest
from app.services.news_sources import RawNewsItem


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def seed_article(
    db: Session,
    *,
    source_url: str,
    iso3: str = "USA",
    headline: str = "Public health report from United States",
    published_at: Optional[datetime] = None,
    source_key: str = "reliefweb",
    source_name: str = "ReliefWeb",
    credibility_label: str = "Highly Reliable",
    source_credibility: str = "high",
    safety_status: str = "safe",
) -> NewsArticle:
    article = NewsArticle(
        source_name=source_name,
        source_key=source_key,
        source_url=source_url,
        headline_original=headline,
        headline_en=headline,
        summary=None,
        language="en",
        translation_status="not_needed",
        country_iso3=iso3,
        country_name="United States" if iso3 == "USA" else "France",
        published_at=published_at or utc_now(),
        ingested_at=utc_now(),
        source_credibility=source_credibility,
        credibility_label=credibility_label,
        safety_status=safety_status,
        safety_reasons=None,
        source_metadata="{}",
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def test_latest_endpoint_returns_only_last_48_hour_items(client, db_session):
    recent = seed_article(db_session, source_url="https://example.org/recent", published_at=utc_now() - timedelta(hours=2))
    seed_article(db_session, source_url="https://example.org/old", published_at=utc_now() - timedelta(days=4))

    response = client.get("/api/countries/USA/news/latest")

    assert response.status_code == 200
    payload = response.json()
    assert [article["id"] for article in payload["articles"]] == [recent.id]
    assert payload["empty_state"] is None


def test_latest_endpoint_returns_empty_state_when_connected_but_no_recent_reports(client, db_session):
    seed_article(db_session, source_url="https://example.org/old", published_at=utc_now() - timedelta(days=4))

    response = client.get("/api/countries/USA/news/latest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["connected"] is True
    assert payload["articles"] == []
    assert payload["empty_state"] == "No public news reports found in the last 48 hours."


def test_history_endpoint_returns_older_reports(client, db_session):
    older = seed_article(db_session, source_url="https://example.org/history", published_at=utc_now() - timedelta(days=7))
    seed_article(db_session, source_url="https://example.org/recent", published_at=utc_now() - timedelta(hours=3))

    response = client.get("/api/countries/USA/news/history")

    assert response.status_code == 200
    payload = response.json()
    assert [article["id"] for article in payload["articles"]] == [older.id]


def test_ingest_deduplicates_by_source_url(client, monkeypatch):
    raw = RawNewsItem(
        source_name="ReliefWeb",
        source_key="reliefweb",
        source_url="https://reliefweb.int/report/example",
        headline_original="United States public health update",
        published_at=utc_now(),
        structured_countries=["United States"],
    )
    monkeypatch.setitem(news_ingest.NEWS_SOURCE_FETCHERS, "mock", lambda countries, limit: [raw, raw])
    monkeypatch.setattr(news_ingest, "translate_headline", lambda headline, enabled=True: (headline, "not_needed"))

    response = client.post(
        "/api/ingest/news",
        json={"sources": ["mock"], "limit_per_source": 2, "polite_delay_seconds": 0},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["articles_seen"] == 2
    assert payload["articles_created"] == 1
    assert payload["duplicate_count"] == 1


def test_unsafe_individual_level_content_is_rejected(client, monkeypatch):
    raw = RawNewsItem(
        source_name="Google News",
        source_key="google_news",
        source_url="https://news.example/unsafe",
        headline_original="Patient named Jane Doe has MRN 123 and a confirmed infection",
        summary="Contact jane@example.com for test result for Jane Doe.",
        published_at=utc_now(),
        structured_countries=["United States"],
    )
    monkeypatch.setitem(news_ingest.NEWS_SOURCE_FETCHERS, "mock_unsafe", lambda countries, limit: [raw])

    response = client.post(
        "/api/ingest/news",
        json={"sources": ["mock_unsafe"], "limit_per_source": 1, "polite_delay_seconds": 0},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["articles_created"] == 0
    assert payload["articles_rejected"] == 1
    assert client.get("/api/news").json()["articles"] == []


def test_translation_failure_falls_back_safely(client, monkeypatch):
    raw = RawNewsItem(
        source_name="Google News",
        source_key="google_news",
        source_url="https://news.example/translation",
        headline_original="France public health bulletin",
        published_at=utc_now(),
        structured_countries=["France"],
    )
    monkeypatch.setitem(news_ingest.NEWS_SOURCE_FETCHERS, "mock_translation", lambda countries, limit: [raw])
    monkeypatch.setattr(news_ingest, "translate_headline", lambda headline, enabled=True: (headline, "failed"))

    response = client.post(
        "/api/ingest/news",
        json={"sources": ["mock_translation"], "limit_per_source": 1, "polite_delay_seconds": 0},
    )

    assert response.status_code == 200
    article = client.get("/api/countries/FRA/news/latest").json()["articles"][0]
    assert article["headline_en"] == "France public health bulletin"
    assert article["translation_status"] == "failed"


def test_credibility_labels_are_source_confidence_only(client, monkeypatch):
    raw = RawNewsItem(
        source_name="ReliefWeb",
        source_key="reliefweb",
        source_url="https://reliefweb.int/report/confidence",
        headline_original="Kenya public health update",
        published_at=utc_now(),
        structured_countries=["Kenya"],
    )
    monkeypatch.setitem(news_ingest.NEWS_SOURCE_FETCHERS, "reliefweb", lambda countries, limit: [raw])
    monkeypatch.setattr(news_ingest, "translate_headline", lambda headline, enabled=True: (headline, "not_needed"))

    response = client.post(
        "/api/ingest/news",
        json={"sources": ["reliefweb"], "limit_per_source": 1, "polite_delay_seconds": 0},
    )

    assert response.status_code == 200
    article = client.get("/api/countries/KEN/news/latest").json()["articles"][0]
    assert article["credibility_label"] == "Highly Reliable"
    assert article["source_credibility"] == "high"
    assert "risk_score" not in article
    assert "country_risk" not in article


def test_country_isolation(client, db_session):
    usa = seed_article(db_session, source_url="https://example.org/usa", iso3="USA", published_at=utc_now())
    seed_article(
        db_session,
        source_url="https://example.org/fra",
        iso3="FRA",
        headline="France public health report",
        published_at=utc_now(),
    )

    response = client.get("/api/countries/USA/news/latest")

    assert response.status_code == 200
    payload = response.json()
    assert [article["id"] for article in payload["articles"]] == [usa.id]
