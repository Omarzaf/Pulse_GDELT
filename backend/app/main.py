import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.news import router as news_router
from app.api.sentiment import router as sentiment_router
from app.db import init_db

logger = logging.getLogger(__name__)

raw_origins = os.getenv("ALLOWED_ORIGINS", "")
allow_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()] if raw_origins else ["*"]
_executor = ThreadPoolExecutor(max_workers=2)


def _startup_jobs_enabled() -> bool:
    return os.getenv("SENTINEL_DISABLE_STARTUP_JOBS") != "1" and "PYTEST_CURRENT_TEST" not in os.environ


def _run_startup_ingest() -> None:
    from app.db import SessionLocal
    from app.schemas.news import NewsIngestRequest
    from app.services.news_ingest import ingest_news

    db = SessionLocal()
    try:
        ingest_news(db, NewsIngestRequest(polite_delay_seconds=1.0, translate=True))
    except Exception:
        logger.exception("Startup news ingest failed")
    finally:
        db.close()


def _run_sentiment_for_all() -> None:
    from app.data.countries import ATLAS_ISO3_LIST
    from app.db import SessionLocal
    from app.services.sentiment.aggregator import compute_social_pulse

    db = SessionLocal()
    try:
        for iso3 in ATLAS_ISO3_LIST:
            try:
                compute_social_pulse(iso3, db)
                logger.info("Social Pulse computed for %s", iso3)
            except Exception:
                logger.exception("Social Pulse failed for %s", iso3)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler = None
    if _startup_jobs_enabled():
        loop = asyncio.get_event_loop()
        loop.run_in_executor(_executor, _run_startup_ingest)
        loop.run_in_executor(_executor, _run_sentiment_for_all)

        try:
            from apscheduler.schedulers.background import BackgroundScheduler

            scheduler = BackgroundScheduler()
            scheduler.add_job(_run_startup_ingest, "interval", hours=1, id="news_ingest")
            scheduler.add_job(_run_sentiment_for_all, "interval", hours=1, minutes=5, id="sentiment_compute")
            scheduler.start()
            logger.info("APScheduler started for hourly news and sentiment refresh")
        except ImportError:
            logger.warning("apscheduler not installed; hourly refresh disabled")
    yield
    if scheduler:
        scheduler.shutdown(wait=False)
    _executor.shutdown(wait=False)


app = FastAPI(
    title="Sentinel Atlas API",
    description="Aggregate-only public news intelligence and social pulse for pandemic early warning.",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(news_router, prefix="/api", tags=["news"])
app.include_router(sentiment_router, prefix="/api", tags=["sentiment"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
