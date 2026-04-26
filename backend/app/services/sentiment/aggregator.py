from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sentiment import SentimentSnapshot
from app.services.sentiment.hf_client import negative_ratio, score_texts
from app.services.sentiment.news_sentiment import compute_news_sentiment_score
from app.services.sentiment.reddit_scraper import fetch_reddit_posts
from app.services.sentiment.trends_fear import compute_trends_fear_score
from app.services.sentiment.wikipedia_trends import compute_wikipedia_spike_score

logger = logging.getLogger(__name__)

WEIGHTS = {
    "reddit": 0.25,
    "wikipedia": 0.20,
    "trends": 0.30,
    "news": 0.25,
}

ELEVATED_THRESHOLD = 50.0
DAMPEN_FACTOR = 0.70


def _level(score: float) -> str:
    if score >= 75:
        return "high"
    if score >= 55:
        return "elevated"
    if score >= 35:
        return "moderate"
    return "low"


def compute_social_pulse(iso3: str, db: Session) -> SentimentSnapshot:
    country_iso3 = iso3.upper()
    now = datetime.now(timezone.utc)
    errors: dict[str, str] = {}
    evidence: list[dict] = []

    reddit_score = 0.0
    try:
        posts = fetch_reddit_posts(country_iso3, limit=25)
        if posts:
            results = score_texts([post["title"] for post in posts])
            reddit_score = negative_ratio(results) * 100
            scored_posts = list(zip(posts, results))
            scored_posts.sort(
                key=lambda item: item[1]["score"] if item[1]["label"] == "negative" else 0,
                reverse=True,
            )
            for post, result in scored_posts[:2]:
                if result["label"] == "negative":
                    evidence.append(
                        {
                            "title": post["title"],
                            "url": post["url"],
                            "source": f"Reddit r/{post['subreddit']}",
                            "sentiment_score": round(result["score"], 3),
                        }
                    )
    except Exception as exc:
        logger.warning("Reddit signal failed for %s: %s", country_iso3, exc)
        errors["reddit"] = str(exc)

    wikipedia_score = 0.0
    try:
        wiki_result = compute_wikipedia_spike_score(country_iso3)
        wikipedia_score = wiki_result["score"]
        if wiki_result.get("article") and wikipedia_score > 30:
            evidence.append(
                {
                    "title": (
                        f"Wikipedia spike: {wiki_result['article']} "
                        f"({wiki_result['spike_ratio']}x normal traffic)"
                    ),
                    "url": wiki_result.get("url", "https://en.wikipedia.org"),
                    "source": "Wikipedia Pageviews",
                    "sentiment_score": round(wikipedia_score / 100, 3),
                }
            )
        if wiki_result.get("error"):
            errors["wikipedia"] = wiki_result["error"]
    except Exception as exc:
        logger.warning("Wikipedia signal failed for %s: %s", country_iso3, exc)
        errors["wikipedia"] = str(exc)

    trends_score = 0.0
    try:
        trends_result = compute_trends_fear_score(country_iso3)
        trends_score = trends_result["score"]
        if trends_result.get("keyword") and trends_score > 30:
            evidence.append(
                {
                    "title": f"Search spike: \"{trends_result['keyword']}\" trending in {country_iso3}",
                    "url": "https://trends.google.com/trends/explore",
                    "source": "Google Trends",
                    "sentiment_score": round(trends_score / 100, 3),
                }
            )
        if trends_result.get("error"):
            errors["trends"] = trends_result["error"]
    except Exception as exc:
        logger.warning("Trends fear signal failed for %s: %s", country_iso3, exc)
        errors["trends"] = str(exc)

    news_score = 0.0
    try:
        news_result = compute_news_sentiment_score(country_iso3, db)
        news_score = news_result["score"]
        evidence.extend(news_result.get("evidence", [])[:1])
        if news_result.get("error"):
            errors["news"] = news_result["error"]
    except Exception as exc:
        logger.warning("News sentiment signal failed for %s: %s", country_iso3, exc)
        errors["news"] = str(exc)

    scores = {
        "reddit": reddit_score,
        "wikipedia": wikipedia_score,
        "trends": trends_score,
        "news": news_score,
    }
    signals_elevated = sum(1 for score in scores.values() if score > ELEVATED_THRESHOLD)
    raw_composite = sum(scores[key] * WEIGHTS[key] for key in WEIGHTS)
    composite = raw_composite if signals_elevated >= 2 else raw_composite * DAMPEN_FACTOR

    snapshot = SentimentSnapshot(
        country_iso3=country_iso3,
        computed_at=now,
        social_pulse_score=round(composite, 1),
        pulse_level=_level(composite),
        reddit_score=round(reddit_score, 1),
        wikipedia_score=round(wikipedia_score, 1),
        trends_fear_score=round(trends_score, 1),
        news_sentiment_score=round(news_score, 1),
        signals_elevated=signals_elevated,
        evidence_json=json.dumps(evidence[:5], ensure_ascii=False),
        errors_json=json.dumps(errors) if errors else None,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def get_pulse_history(iso3: str, db: Session, days: int = 30) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rows = list(
        db.scalars(
            select(SentimentSnapshot)
            .where(
                SentimentSnapshot.country_iso3 == iso3.upper(),
                SentimentSnapshot.computed_at >= cutoff,
            )
            .order_by(SentimentSnapshot.computed_at.asc())
        )
    )
    return [
        {
            "date": row.computed_at.strftime("%Y-%m-%d"),
            "social_pulse": row.social_pulse_score,
            "reddit": row.reddit_score,
            "wikipedia": row.wikipedia_score,
            "trends": row.trends_fear_score,
            "news": row.news_sentiment_score,
            "level": row.pulse_level,
            "signals_elevated": row.signals_elevated,
        }
        for row in rows
    ]
