from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)

USER_AGENT = "SentinelAtlas/0.1 sentiment scraper (aggregate public data)"

COUNTRY_SUBREDDITS: dict[str, list[str]] = {
    "USA": ["Health", "Coronavirus", "worldnews", "news", "unitedstates"],
    "BRA": ["brasil", "worldnews", "Coronavirus"],
    "FRA": ["france", "worldnews", "Coronavirus"],
    "GBR": ["unitedkingdom", "worldnews", "Coronavirus"],
    "COD": ["AfricaNews", "worldnews", "Coronavirus"],
    "KEN": ["Kenya", "Africa", "worldnews"],
    "IND": ["india", "worldnews", "Coronavirus"],
    "CHN": ["China", "worldnews", "Coronavirus"],
    "JPN": ["japan", "worldnews", "Coronavirus"],
    "AUS": ["australia", "worldnews", "Coronavirus"],
}

HEALTH_KEYWORDS = [
    "outbreak",
    "epidemic",
    "disease",
    "virus",
    "sick",
    "ill",
    "fever",
    "hospital",
    "health",
    "infection",
    "quarantine",
    "symptoms",
    "cases",
    "deaths",
    "spread",
    "contagious",
    "pathogen",
    "vaccine",
    "pandemic",
]

COUNTRY_NAME_MAP = {
    "USA": ["united states", "america", "us health"],
    "BRA": ["brazil", "brasil"],
    "FRA": ["france", "french"],
    "GBR": ["uk", "britain", "england"],
    "COD": ["congo", "drc", "democratic republic"],
    "KEN": ["kenya"],
    "IND": ["india"],
    "CHN": ["china", "chinese"],
    "JPN": ["japan"],
    "AUS": ["australia"],
}


def fetch_reddit_posts(iso3: str, limit: int = 25) -> list[dict]:
    """
    Fetch recent health-related posts from Reddit public JSON endpoints.

    Returns aggregate post metadata only; no usernames or comments are ingested.
    """
    country_iso3 = iso3.upper()
    subreddits = COUNTRY_SUBREDDITS.get(country_iso3, ["worldnews", "Health"])
    country_terms = COUNTRY_NAME_MAP.get(country_iso3, [])
    posts: list[dict] = []
    headers = {"User-Agent": USER_AGENT}

    for subreddit in subreddits[:3]:
        url = f"https://www.reddit.com/r/{subreddit}/new.json?limit=50"
        try:
            response = requests.get(url, headers=headers, timeout=12)
            response.raise_for_status()
            children = response.json().get("data", {}).get("children", [])
        except Exception as exc:
            logger.warning("Reddit fetch failed for r/%s: %s", subreddit, exc)
            continue

        for child in children:
            post = child.get("data", {})
            title = post.get("title", "").strip()
            if not title:
                continue

            title_lower = title.lower()
            if not any(keyword in title_lower for keyword in HEALTH_KEYWORDS):
                continue

            if subreddit in ("worldnews", "news", "Coronavirus") and country_terms:
                if not any(term in title_lower for term in country_terms):
                    continue

            posts.append(
                {
                    "title": title,
                    "url": f"https://www.reddit.com{post.get('permalink', '')}",
                    "subreddit": subreddit,
                    "upvotes": post.get("score", 0),
                }
            )

        if len(posts) >= limit:
            break

    return posts[:limit]
