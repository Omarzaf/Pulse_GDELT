import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.news import router as news_router
from app.api.sentiment import router as sentiment_router
from app.db import init_db
from app.settings import cors_settings, startup_jobs_enabled

logger = logging.getLogger(__name__)

allow_origins, allow_credentials = cors_settings()
_executor = ThreadPoolExecutor(max_workers=2)


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
    if startup_jobs_enabled():
        loop = asyncio.get_event_loop()
        loop.run_in_executor(_executor, _run_startup_ingest)
        loop.run_in_executor(_executor, _run_sentiment_for_all)

        try:
            from apscheduler.schedulers.background import BackgroundScheduler

            scheduler = BackgroundScheduler()
            scheduler.add_job(_run_startup_ingest, "interval", hours=1, id="news_ingest")
            scheduler.add_job(
                _run_sentiment_for_all, "interval", hours=1, minutes=5, id="sentiment_compute"
            )
            scheduler.start()
            logger.info("APScheduler started for hourly news and sentiment refresh")
        except ImportError:
            logger.warning("apscheduler not installed; hourly refresh disabled")
    yield
    if scheduler:
        scheduler.shutdown(wait=False)
    _executor.shutdown(wait=False)


app = FastAPI(
    title="Sentinel Atlas Social Pulse API",
    description="Aggregate public-news and public-signal research module for Sentinel Atlas.",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Accept", "Authorization", "Content-Type"],
)

app.include_router(news_router, prefix="/api", tags=["news"])
app.include_router(sentiment_router, prefix="/api", tags=["sentiment"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
