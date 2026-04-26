from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Callable, Optional
from urllib.parse import quote_plus

from app.services.country_extraction import extract_country, normalize_country

USER_AGENT = "SentinelAtlas/0.1 (+https://localhost; aggregate public news intelligence)"


@dataclass(frozen=True)
class RawNewsItem:
    source_name: str
    source_key: str
    source_url: str
    headline_original: str
    summary: Optional[str] = None
    published_at: Optional[datetime] = None
    language: Optional[str] = None
    structured_countries: list[str] = field(default_factory=list)
    source_metadata: dict[str, object] = field(default_factory=dict)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            parsed = parsedate_to_datetime(value)
    else:
        parsed = _utc_now()
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _country_query(countries: Optional[list[str]]) -> list[Optional[str]]:
    if not countries:
        return [None]
    return countries


def fetch_google_news(countries: Optional[list[str]] = None, limit: int = 10) -> list[RawNewsItem]:
    import feedparser
    import requests

    items: list[RawNewsItem] = []
    for country in _country_query(countries):
        country_part = f" {country}" if country else ""
        query = quote_plus(f"(outbreak OR epidemic OR disease OR public health){country_part}")
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        response = requests.get(url, timeout=15, headers={"User-Agent": USER_AGENT})
        response.raise_for_status()
        feed = feedparser.parse(response.text)
        for entry in feed.entries[:limit]:
            published_at = None
            if getattr(entry, "published_parsed", None):
                published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            headline = getattr(entry, "title", "").strip()
            source_url = getattr(entry, "link", "").strip()
            if not headline or not source_url:
                continue
            structured = [country] if country else []
            items.append(
                RawNewsItem(
                    source_name="Google News",
                    source_key="google_news",
                    source_url=source_url,
                    headline_original=headline,
                    summary=getattr(entry, "summary", None),
                    published_at=published_at,
                    language="auto",
                    structured_countries=structured,
                    source_metadata={"feed_url": url},
                )
            )
    return items[:limit]


def fetch_reliefweb(countries: Optional[list[str]] = None, limit: int = 10) -> list[RawNewsItem]:
    import requests

    params: dict[str, object] = {
        "appname": "sentinel-atlas",
        "profile": "list",
        "limit": limit,
        "sort[]": "date.created:desc",
        "fields[include][]": ["title", "url", "date", "country", "source", "body"],
    }
    if countries:
        params["query[value]"] = " OR ".join(countries)
        params["query[operator]"] = "OR"
    else:
        params["query[value]"] = "outbreak epidemic disease public health"
        params["query[operator]"] = "OR"

    response = requests.get(
        "https://api.reliefweb.int/v1/reports",
        timeout=20,
        params=params,
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()
    payload = response.json()
    items: list[RawNewsItem] = []
    for result in payload.get("data", [])[:limit]:
        fields = result.get("fields", {})
        headline = fields.get("title", "").strip()
        source_url = fields.get("url") or result.get("href")
        if not headline or not source_url:
            continue
        country_names = [country.get("name", "") for country in fields.get("country", []) if isinstance(country, dict)]
        source_names = [source.get("name", "") for source in fields.get("source", []) if isinstance(source, dict)]
        published_at = fields.get("date", {}).get("created") if isinstance(fields.get("date"), dict) else None
        items.append(
            RawNewsItem(
                source_name="ReliefWeb",
                source_key="reliefweb",
                source_url=source_url,
                headline_original=headline,
                summary=fields.get("body"),
                published_at=_ensure_datetime(published_at),
                structured_countries=country_names,
                source_metadata={"reliefweb_id": result.get("id"), "source_names": source_names},
            )
        )
    return items


def fetch_who_don(countries: Optional[list[str]] = None, limit: int = 10) -> list[RawNewsItem]:
    import requests
    from bs4 import BeautifulSoup

    response = requests.get(
        "https://www.who.int/emergencies/disease-outbreak-news",
        timeout=20,
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    items: list[RawNewsItem] = []
    for link in soup.select("a[href*='disease-outbreak-news']"):
        headline = " ".join(link.get_text(" ", strip=True).split())
        href = link.get("href")
        if not headline or not href or len(headline) < 8:
            continue
        source_url = href if href.startswith("http") else f"https://www.who.int{href}"
        country = extract_country(headline=headline, summary=None)
        if countries and country:
            requested = {normalize_country(value)[0] for value in countries if normalize_country(value)}
            if country[0] not in requested:
                continue
        items.append(
            RawNewsItem(
                source_name="WHO Disease Outbreak News",
                source_key="who_don",
                source_url=source_url,
                headline_original=headline,
                published_at=_utc_now(),
                structured_countries=[country[1]] if country else [],
                source_metadata={"scraper": "best_effort"},
            )
        )
        if len(items) >= limit:
            break
    return items


def fetch_promed(countries: Optional[list[str]] = None, limit: int = 10) -> list[RawNewsItem]:
    import requests
    from bs4 import BeautifulSoup

    response = requests.get(
        "https://promedmail.org/promed-posts/",
        timeout=20,
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    items: list[RawNewsItem] = []
    for link in soup.select("a[href]"):
        headline = " ".join(link.get_text(" ", strip=True).split())
        href = link.get("href")
        if not href or not headline or len(headline) < 12:
            continue
        if "promed-post" not in href and "promedmail.org" not in href:
            continue
        source_url = href if href.startswith("http") else f"https://promedmail.org{href}"
        country = extract_country(headline=headline, summary=None)
        if countries and country:
            requested = {normalize_country(value)[0] for value in countries if normalize_country(value)}
            if country[0] not in requested:
                continue
        items.append(
            RawNewsItem(
                source_name="ProMED",
                source_key="promed",
                source_url=source_url,
                headline_original=headline,
                published_at=_utc_now(),
                structured_countries=[country[1]] if country else [],
                source_metadata={"scraper": "best_effort"},
            )
        )
        if len(items) >= limit:
            break
    return items


NewsFetcher = Callable[[Optional[list[str]], int], list[RawNewsItem]]

NEWS_SOURCE_FETCHERS: dict[str, NewsFetcher] = {
    "google_news": fetch_google_news,
    "reliefweb": fetch_reliefweb,
    "who_don": fetch_who_don,
    "promed": fetch_promed,
}
