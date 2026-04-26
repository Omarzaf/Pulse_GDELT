import re
from functools import lru_cache
from typing import Optional

STATIC_COUNTRIES: dict[str, tuple[str, str]] = {
    "usa": ("USA", "United States"),
    "us": ("USA", "United States"),
    "united states": ("USA", "United States"),
    "united states of america": ("USA", "United States"),
    "america": ("USA", "United States"),
    "france": ("FRA", "France"),
    "fra": ("FRA", "France"),
    "kenya": ("KEN", "Kenya"),
    "ken": ("KEN", "Kenya"),
    "democratic republic of the congo": ("COD", "Democratic Republic of the Congo"),
    "dr congo": ("COD", "Democratic Republic of the Congo"),
    "drc": ("COD", "Democratic Republic of the Congo"),
    "congo-kinshasa": ("COD", "Democratic Republic of the Congo"),
    "united kingdom": ("GBR", "United Kingdom"),
    "uk": ("GBR", "United Kingdom"),
    "great britain": ("GBR", "United Kingdom"),
    "china": ("CHN", "China"),
    "india": ("IND", "India"),
    "brazil": ("BRA", "Brazil"),
    "canada": ("CAN", "Canada"),
    "mexico": ("MEX", "Mexico"),
    "germany": ("DEU", "Germany"),
    "italy": ("ITA", "Italy"),
    "spain": ("ESP", "Spain"),
    "japan": ("JPN", "Japan"),
    "south korea": ("KOR", "South Korea"),
    "republic of korea": ("KOR", "South Korea"),
    "nigeria": ("NGA", "Nigeria"),
    "south africa": ("ZAF", "South Africa"),
}

FREE_TEXT_SHORT_ALIASES = {"us", "usa", "uk", "drc"}


@lru_cache(maxsize=1)
def _alias_index() -> dict[str, tuple[str, str]]:
    aliases = dict(STATIC_COUNTRIES)
    try:
        import pycountry
    except Exception:
        return aliases

    for country in pycountry.countries:
        iso3 = getattr(country, "alpha_3", "").upper()
        if not iso3:
            continue
        name = getattr(country, "name", iso3)
        aliases[iso3.lower()] = (iso3, name)
        aliases[getattr(country, "alpha_2", "").lower()] = (iso3, name)
        aliases[name.lower()] = (iso3, name)
        official = getattr(country, "official_name", None)
        if official:
            aliases[official.lower()] = (iso3, name)
        common = getattr(country, "common_name", None)
        if common:
            aliases[common.lower()] = (iso3, name)
    return {key: value for key, value in aliases.items() if key}


def normalize_country(value: Optional[str]) -> Optional[tuple[str, str]]:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    normalized = re.sub(r"\s+", " ", value).lower()
    return _alias_index().get(normalized)


def extract_country(
    *,
    structured_countries: Optional[list[str]] = None,
    metadata: Optional[dict[str, object]] = None,
    headline: Optional[str] = None,
    summary: Optional[str] = None,
) -> Optional[tuple[str, str]]:
    for value in structured_countries or []:
        normalized = normalize_country(value)
        if normalized:
            return normalized

    metadata = metadata or {}
    for key in ("country_iso3", "iso3", "country", "countries", "location", "locations"):
        value = metadata.get(key)
        values = value if isinstance(value, list) else [value]
        for item in values:
            if isinstance(item, dict):
                for nested_key in ("iso3", "code", "name", "country"):
                    normalized = normalize_country(str(item.get(nested_key, "")))
                    if normalized:
                        return normalized
            elif isinstance(item, str):
                normalized = normalize_country(item)
                if normalized:
                    return normalized

    text = f"{headline or ''} {summary or ''}".lower()
    padded_text = f" {re.sub(r'[^a-z0-9]+', ' ', text)} "
    for alias, value in sorted(_alias_index().items(), key=lambda entry: len(entry[0]), reverse=True):
        if len(alias) <= 3 and alias not in FREE_TEXT_SHORT_ALIASES:
            continue
        padded_alias = f" {re.sub(r'[^a-z0-9]+', ' ', alias.lower()).strip()} "
        if padded_alias.strip() and padded_alias in padded_text:
            return value

    return None
