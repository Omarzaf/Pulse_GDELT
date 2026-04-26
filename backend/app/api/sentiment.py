from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.sentiment import SentimentSnapshot
from app.services.sentiment.aggregator import compute_social_pulse, get_pulse_history

router = APIRouter()


@router.get("/countries/{iso3}/social-pulse")
def get_social_pulse(
    iso3: str,
    days: int = Query(default=30, ge=7, le=90),
    db: Session = Depends(get_db),
) -> dict:
    country_iso3 = iso3.upper()
    latest = db.scalar(
        select(SentimentSnapshot)
        .where(SentimentSnapshot.country_iso3 == country_iso3)
        .order_by(desc(SentimentSnapshot.computed_at))
    )

    if not latest:
        latest = compute_social_pulse(country_iso3, db)

    evidence = []
    if latest.evidence_json:
        try:
            evidence = json.loads(latest.evidence_json)
        except Exception:
            evidence = []

    return {
        "iso3": country_iso3,
        "latest": {
            "social_pulse_score": latest.social_pulse_score,
            "pulse_level": latest.pulse_level,
            "signals_elevated": latest.signals_elevated,
            "reddit_score": latest.reddit_score,
            "wikipedia_score": latest.wikipedia_score,
            "trends_fear_score": latest.trends_fear_score,
            "news_sentiment_score": latest.news_sentiment_score,
            "computed_at": latest.computed_at.isoformat(),
        },
        "evidence": evidence,
        "history": get_pulse_history(country_iso3, db, days=days),
        "days": days,
    }


@router.post("/social-pulse/compute-all")
def compute_all_pulses(db: Session = Depends(get_db)) -> dict:
    from app.data.countries import ATLAS_ISO3_LIST

    results = {}
    for iso3 in ATLAS_ISO3_LIST:
        try:
            snapshot = compute_social_pulse(iso3, db)
            results[iso3] = {"score": snapshot.social_pulse_score, "level": snapshot.pulse_level}
        except Exception as exc:
            results[iso3] = {"error": str(exc)}
    return results


@router.get("/countries/elevated")
def get_elevated_countries(
    threshold: int = Query(default=55, ge=0, le=100),
    db: Session = Depends(get_db),
) -> dict:
    subquery = (
        select(SentimentSnapshot.country_iso3, func.max(SentimentSnapshot.computed_at).label("max_at"))
        .group_by(SentimentSnapshot.country_iso3)
        .subquery()
    )
    rows = list(
        db.execute(
            select(SentimentSnapshot)
            .join(
                subquery,
                (SentimentSnapshot.country_iso3 == subquery.c.country_iso3)
                & (SentimentSnapshot.computed_at == subquery.c.max_at),
            )
            .where(
                SentimentSnapshot.social_pulse_score >= threshold,
                SentimentSnapshot.signals_elevated >= 2,
            )
        ).scalars()
    )
    return {
        "elevated": [
            {
                "iso3": row.country_iso3,
                "score": row.social_pulse_score,
                "level": row.pulse_level,
                "signals_elevated": row.signals_elevated,
            }
            for row in rows
        ]
    }
