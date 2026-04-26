from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class SentimentSnapshot(Base):
    __tablename__ = "sentiment_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    country_iso3: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    social_pulse_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pulse_level: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)

    reddit_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wikipedia_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    trends_fear_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    news_sentiment_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    signals_elevated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    evidence_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    errors_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
