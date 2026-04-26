import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.sentiment import SentimentSnapshot


def seed_snapshot(
    db: Session,
    *,
    iso3: str = "COD",
    score: float = 72.8,
    signals_elevated: int = 4,
    computed_at: Optional[datetime] = None,
) -> SentimentSnapshot:
    snapshot = SentimentSnapshot(
        country_iso3=iso3,
        computed_at=computed_at or datetime.now(timezone.utc),
        social_pulse_score=score,
        pulse_level="elevated",
        reddit_score=70,
        wikipedia_score=74,
        trends_fear_score=75,
        news_sentiment_score=72,
        signals_elevated=signals_elevated,
        evidence_json=json.dumps(
            [
                {
                    "title": "Wikipedia: Mpox page views spiking above baseline",
                    "url": "https://en.wikipedia.org/wiki/Mpox",
                    "source": "Wikipedia Pageviews",
                    "sentiment_score": 0.78,
                }
            ]
        ),
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def test_social_pulse_endpoint_returns_latest_snapshot(client, db_session):
    older = datetime.now(timezone.utc) - timedelta(days=2)
    seed_snapshot(db_session, score=40, signals_elevated=1, computed_at=older)
    latest = seed_snapshot(db_session)

    response = client.get("/api/countries/COD/social-pulse?days=30")

    assert response.status_code == 200
    payload = response.json()
    assert payload["iso3"] == "COD"
    assert payload["latest"]["social_pulse_score"] == latest.social_pulse_score
    assert payload["latest"]["signals_elevated"] == 4
    assert payload["evidence"][0]["source"] == "Wikipedia Pageviews"
    assert len(payload["history"]) == 2


def test_elevated_countries_requires_threshold_and_signal_convergence(client, db_session):
    seed_snapshot(db_session, iso3="COD", score=72.8, signals_elevated=4)
    seed_snapshot(db_session, iso3="USA", score=70, signals_elevated=1)

    response = client.get("/api/countries/elevated?threshold=55")

    assert response.status_code == 200
    assert response.json()["elevated"] == [
        {"iso3": "COD", "score": 72.8, "level": "elevated", "signals_elevated": 4}
    ]
