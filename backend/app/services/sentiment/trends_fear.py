from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

COUNTRY_DISEASES: dict[str, list[str]] = {
    "USA": ["flu", "mpox", "bird flu"],
    "BRA": ["dengue", "zika", "yellow fever"],
    "FRA": ["mpox", "flu"],
    "GBR": ["mpox", "flu", "norovirus"],
    "COD": ["ebola", "mpox", "cholera"],
    "KEN": ["cholera", "dengue"],
    "IND": ["dengue", "bird flu", "cholera"],
    "CHN": ["bird flu", "H5N1", "flu"],
    "JPN": ["flu", "bird flu"],
    "AUS": ["flu", "hendra"],
}

COUNTRY_GEO: dict[str, str] = {
    "USA": "US",
    "BRA": "BR",
    "FRA": "FR",
    "GBR": "GB",
    "COD": "CD",
    "KEN": "KE",
    "IND": "IN",
    "CHN": "CN",
    "JPN": "JP",
    "AUS": "AU",
}


def compute_trends_fear_score(iso3: str) -> dict:
    try:
        from pytrends.request import TrendReq
    except ImportError:
        return {"score": 0, "keyword": None, "error": "pytrends not installed"}

    country_iso3 = iso3.upper()
    geo = COUNTRY_GEO.get(country_iso3)
    diseases = COUNTRY_DISEASES.get(country_iso3, ["flu"])
    if not geo:
        return {"score": 0, "keyword": None, "error": "country not configured"}

    top_disease = diseases[0]
    queries = [
        f"how to avoid {top_disease}",
        f"is {top_disease} dangerous",
        f"{top_disease} outbreak",
        "hospital near me",
        "symptoms fever",
    ]

    try:
        trend_request = TrendReq(hl="en-US", tz=0, timeout=(10, 25), retries=2, backoff_factor=0.5)
        trend_request.build_payload(queries[:5], cat=0, timeframe="today 30-d", geo=geo, gprop="")
        frame = trend_request.interest_over_time()
    except Exception as exc:
        logger.warning("Google Trends fear fetch failed for %s: %s", country_iso3, exc)
        return {"score": 0, "keyword": None, "error": str(exc)}

    if frame is None or frame.empty:
        return {"score": 0, "keyword": None, "error": "no data"}

    if "isPartial" in frame.columns:
        frame = frame.drop(columns=["isPartial"])

    recent_scores: dict[str, float] = {}
    for query in frame.columns:
        recent_scores[query] = float(frame[query].iloc[-7:].mean())

    if not recent_scores:
        return {"score": 0, "keyword": None, "error": "no columns"}

    average_score = sum(recent_scores.values()) / len(recent_scores)
    top_query = max(recent_scores, key=lambda query: recent_scores[query])

    return {
        "score": min(100.0, average_score),
        "keyword": top_query,
        "series": {key: [float(value) for value in frame[key].tolist()] for key in frame.columns},
        "dates": [date.strftime("%Y-%m-%d") for date in frame.index.tolist()],
        "error": None,
    }
