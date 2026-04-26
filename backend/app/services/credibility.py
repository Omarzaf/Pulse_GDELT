SOURCE_CREDIBILITY = {
    "reliefweb": ("high", "Highly Reliable"),
    "who_don": ("high", "Highly Reliable"),
    "promed": ("reliable", "Reliable"),
    "google_news": ("moderate", "Moderate"),
}

DEFAULT_CREDIBILITY = ("unverified", "Unverified")


def credibility_for_source(source_key: str) -> tuple[str, str]:
    """Return source confidence only; this is never country or outbreak risk."""
    return SOURCE_CREDIBILITY.get(source_key, DEFAULT_CREDIBILITY)
