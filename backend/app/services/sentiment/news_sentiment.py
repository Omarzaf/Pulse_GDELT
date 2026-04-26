from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.news import NewsArticle
from app.services.sentiment.hf_client import negative_ratio, score_texts


def compute_news_sentiment_score(iso3: str, db: Session, days: int = 14) -> dict:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    articles = list(
        db.scalars(
            select(NewsArticle)
            .where(
                NewsArticle.country_iso3 == iso3.upper(),
                NewsArticle.safety_status == "safe",
                NewsArticle.published_at >= cutoff,
            )
            .order_by(NewsArticle.published_at.desc())
            .limit(30)
        )
    )

    if not articles:
        return {"score": 0, "article_count": 0, "evidence": [], "error": "no articles"}

    results = score_texts([article.headline_en for article in articles])
    if not results:
        return {"score": 0, "article_count": len(articles), "evidence": [], "error": "scoring failed"}

    ratio = negative_ratio(results)
    scored_articles = list(zip(articles, results))
    scored_articles.sort(
        key=lambda item: item[1]["score"] if item[1]["label"] == "negative" else 0,
        reverse=True,
    )

    evidence = []
    for article, result in scored_articles[:3]:
        if result["label"] == "negative":
            evidence.append(
                {
                    "title": article.headline_en,
                    "url": article.source_url,
                    "source": article.source_name,
                    "sentiment_score": round(result["score"], 3),
                }
            )

    return {
        "score": round(ratio * 100, 1),
        "article_count": len(articles),
        "negative_ratio": round(ratio, 3),
        "evidence": evidence,
        "error": None,
    }
