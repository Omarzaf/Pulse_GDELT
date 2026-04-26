from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

COUNTRY_WIKI_ARTICLES: dict[str, list[str]] = {
    "USA": ["Influenza", "West_Nile_virus", "Mpox", "COVID-19", "Dengue_fever"],
    "BRA": ["Dengue_fever", "Yellow_fever", "Zika_virus", "Chikungunya", "COVID-19"],
    "FRA": ["COVID-19", "Mpox", "Influenza"],
    "GBR": ["COVID-19", "Mpox", "Influenza", "Norovirus"],
    "COD": ["Ebola_virus_disease", "Mpox", "Cholera", "Marburg_virus_disease"],
    "KEN": ["Cholera", "Rift_Valley_fever", "Dengue_fever", "COVID-19"],
    "IND": ["Dengue_fever", "Nipah_virus", "Cholera", "COVID-19", "H5N1"],
    "CHN": ["H5N1", "COVID-19", "SARS", "Influenza_A_virus_subtype_H7N9", "Mpox"],
    "JPN": ["COVID-19", "Influenza", "H5N1", "Japanese_encephalitis"],
    "AUS": ["COVID-19", "Hendra_virus", "Murray_Valley_encephalitis_virus", "Ross_River_fever"],
}

SYMPTOM_ARTICLES = ["Fever", "Diarrhea", "Hemorrhagic_fever", "Pneumonia", "Encephalitis"]

WIKI_PAGEVIEWS_API = (
    "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
    "en.wikipedia/all-access/all-agents"
)


def _fetch_article_views(article: str, days: int = 37) -> list[int]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    article_slug = quote(article, safe="")
    url = f"{WIKI_PAGEVIEWS_API}/{article_slug}/daily/{start:%Y%m%d}/{end:%Y%m%d}"
    try:
        response = requests.get(url, timeout=12, headers={"User-Agent": "SentinelAtlas/0.1"})
        response.raise_for_status()
        return [item.get("views", 0) for item in response.json().get("items", [])]
    except Exception as exc:
        logger.debug("Wikipedia pageviews fetch failed for %s: %s", article, exc)
        return []


def compute_wikipedia_spike_score(iso3: str) -> dict:
    articles = COUNTRY_WIKI_ARTICLES.get(iso3.upper(), []) + SYMPTOM_ARTICLES[:3]
    best_spike_ratio = 0.0
    best_article = None
    best_url = None
    article_scores: list[float] = []

    for article in articles[:8]:
        views = _fetch_article_views(article, days=37)
        if len(views) < 10:
            continue

        recent = views[-7:]
        baseline_window = views[:-7]
        if not baseline_window:
            continue

        baseline_avg = sum(baseline_window) / len(baseline_window)
        recent_avg = sum(recent) / len(recent) if recent else 0
        if baseline_avg < 100:
            continue

        spike_ratio = recent_avg / baseline_avg if baseline_avg > 0 else 1.0
        article_scores.append(min(100.0, (spike_ratio - 1.0) * 50))

        if spike_ratio > best_spike_ratio:
            best_spike_ratio = spike_ratio
            best_article = article.replace("_", " ")
            best_url = f"https://en.wikipedia.org/wiki/{article}"

    if not article_scores:
        return {"score": 0, "spike_ratio": 1.0, "article": None, "url": None, "error": "no data"}

    return {
        "score": min(100.0, sum(article_scores) / len(article_scores)),
        "spike_ratio": round(best_spike_ratio, 2),
        "article": best_article,
        "url": best_url,
        "error": None,
    }
