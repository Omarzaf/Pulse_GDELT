from __future__ import annotations

import logging
import os
import time

import requests

logger = logging.getLogger(__name__)

HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
MODEL_ID = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
HF_API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"


def score_texts(texts: list[str], retries: int = 3) -> list[dict]:
    """
    Score texts with HuggingFace Inference API.

    Returns one dict per text: {"label": "negative"|"neutral"|"positive", "score": float}.
    Falls back to keyword scoring when the hosted model is unavailable.
    """
    if not texts:
        return []

    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"} if HF_API_TOKEN else {}

    for attempt in range(retries):
        try:
            response = requests.post(
                HF_API_URL,
                headers=headers,
                json={"inputs": texts, "options": {"wait_for_model": True}},
                timeout=30,
            )
            if response.status_code == 503:
                time.sleep(10)
                continue
            response.raise_for_status()
            raw = response.json()
            results = []
            for item in raw:
                if isinstance(item, list):
                    best = max(item, key=lambda value: value["score"])
                    results.append({"label": best["label"].lower(), "score": best["score"]})
                elif isinstance(item, dict):
                    results.append(
                        {
                            "label": item.get("label", "neutral").lower(),
                            "score": item.get("score", 0.5),
                        }
                    )
            return results
        except Exception as exc:
            logger.warning("HF Inference API attempt %d failed: %s", attempt + 1, exc)
            if attempt < retries - 1:
                time.sleep(3)

    logger.warning("HF API unavailable; using keyword fallback for %d texts", len(texts))
    return [_keyword_fallback(text) for text in texts]


FEAR_KEYWORDS = {
    "high": [
        "panic",
        "outbreak",
        "epidemic",
        "death",
        "fatal",
        "killed",
        "spreading",
        "explosion",
        "emergency",
        "crisis",
    ],
    "medium": [
        "sick",
        "ill",
        "infected",
        "disease",
        "virus",
        "symptoms",
        "hospital",
        "quarantine",
        "warning",
        "alert",
    ],
    "low": ["concern", "risk", "potential", "possible", "may", "could", "health"],
}


def _keyword_fallback(text: str) -> dict:
    text_lower = text.lower()
    for level, keywords in FEAR_KEYWORDS.items():
        if any(keyword in text_lower for keyword in keywords):
            score = {"high": 0.85, "medium": 0.65, "low": 0.52}[level]
            return {"label": "negative", "score": score}
    return {"label": "neutral", "score": 0.6}


def negative_ratio(results: list[dict]) -> float:
    if not results:
        return 0.0
    negative_count = sum(1 for result in results if result["label"] == "negative")
    return negative_count / len(results)
