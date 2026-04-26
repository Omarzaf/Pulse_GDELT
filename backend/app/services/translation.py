import logging

logger = logging.getLogger(__name__)


def translate_headline(headline: str, *, enabled: bool = True) -> tuple[str, str]:
    if not enabled:
        return headline, "not_requested"
    try:
        from deep_translator import GoogleTranslator

        translated = GoogleTranslator(source="auto", target="en").translate(headline)
        if not translated:
            return headline, "not_needed"
        if translated.strip() == headline.strip():
            return headline, "not_needed"
        return translated, "translated"
    except Exception as exc:
        logger.warning("Headline translation failed; using original headline: %s", exc)
        return headline, "failed"
