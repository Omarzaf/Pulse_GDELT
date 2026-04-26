"""
Run from the repository root with:
python -m backend.scripts.seed_demo_data

Seeds 35 days of Social Pulse history for DRC to demonstrate convergence.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)

from sqlalchemy import delete

from app.db import SessionLocal, init_db
from app.models.sentiment import SentimentSnapshot
from app.services.sentiment.aggregator import DAMPEN_FACTOR, ELEVATED_THRESHOLD, WEIGHTS, _level

init_db()
db = SessionLocal()

try:
    db.execute(delete(SentimentSnapshot).where(SentimentSnapshot.country_iso3 == "COD"))
    db.commit()

    base = datetime.now(timezone.utc) - timedelta(days=35)
    schedule = [
        (12, 8, 10, 18),
        (14, 9, 11, 16),
        (13, 8, 12, 19),
        (15, 10, 11, 20),
        (14, 11, 13, 18),
        (16, 12, 12, 22),
        (15, 13, 14, 21),
        (17, 14, 15, 24),
        (18, 16, 14, 23),
        (20, 18, 16, 25),
        (22, 22, 17, 26),
        (24, 28, 18, 28),
        (28, 35, 20, 30),
        (32, 42, 22, 32),
        (38, 50, 25, 34),
        (45, 58, 30, 36),
        (48, 62, 38, 38),
        (50, 65, 48, 40),
        (55, 68, 58, 42),
        (60, 70, 65, 48),
        (64, 72, 70, 52),
        (68, 74, 74, 58),
        (70, 75, 76, 62),
        (72, 76, 78, 66),
        (74, 77, 79, 70),
        (75, 78, 80, 72),
        (76, 79, 80, 74),
        (74, 78, 79, 76),
        (73, 77, 78, 75),
        (72, 76, 77, 74),
        (71, 75, 76, 73),
        (70, 74, 75, 72),
        (70, 74, 75, 72),
        (70, 74, 75, 72),
        (70, 74, 75, 72),
    ]

    for day, (reddit, wiki, trends, news) in enumerate(schedule):
        scores = {"reddit": reddit, "wikipedia": wiki, "trends": trends, "news": news}
        signals_elevated = sum(1 for score in scores.values() if score > ELEVATED_THRESHOLD)
        raw = sum(scores[key] * WEIGHTS[key] for key in WEIGHTS)
        composite = raw if signals_elevated >= 2 else raw * DAMPEN_FACTOR

        snapshot = SentimentSnapshot(
            country_iso3="COD",
            computed_at=base + timedelta(days=day, hours=12),
            social_pulse_score=round(composite, 1),
            pulse_level=_level(composite),
            reddit_score=reddit,
            wikipedia_score=wiki,
            trends_fear_score=trends,
            news_sentiment_score=news,
            signals_elevated=signals_elevated,
            evidence_json=json.dumps(
                [
                    {
                        "title": "Mpox cases rising in DRC provinces - health officials on alert",
                        "url": "https://www.who.int/emergencies/disease-outbreak-news",
                        "source": "WHO Disease Outbreak News",
                        "sentiment_score": 0.86,
                    },
                    {
                        "title": "Wikipedia: Mpox page views spiking above 30-day average by 3.2x",
                        "url": "https://en.wikipedia.org/wiki/Mpox",
                        "source": "Wikipedia Pageviews",
                        "sentiment_score": 0.78,
                    },
                    {
                        "title": "Local posts ask how to avoid mpox exposure as symptoms searches rise",
                        "url": "https://www.reddit.com/r/AfricaNews/",
                        "source": "Reddit r/AfricaNews",
                        "sentiment_score": 0.74,
                    },
                ]
            ),
            errors_json=None,
        )
        db.add(snapshot)

    db.commit()
finally:
    db.close()

print("Demo data seeded for DRC (COD): 35 days of Social Pulse convergence")
