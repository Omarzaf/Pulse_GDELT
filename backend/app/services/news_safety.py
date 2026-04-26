import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SafetyEvaluation:
    status: str
    reasons: list[str]

    @property
    def is_safe(self) -> bool:
        return self.status == "safe"


EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
COORDINATE_RE = re.compile(r"\b-?\d{1,2}\.\d{4,}\s*,\s*-?\d{1,3}\.\d{4,}\b")

DISALLOWED_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("direct identifier", re.compile(r"\b(patient|case)\s+(named|name|identified as)\b", re.I)),
    ("medical record detail", re.compile(r"\b(MRN|medical record|date of birth|DOB|lab result for|test result for)\b", re.I)),
    ("home address", re.compile(r"\b(home address|resides at|street address|apartment)\b", re.I)),
    ("precise personal mobility trace", re.compile(r"\b(seat\s+\d+[A-Z]?|flight\s+[A-Z]{1,3}\d{2,4}|license plate|GPS trace|cell-phone location)\b", re.I)),
    ("operational public-alert instruction", re.compile(r"\b(public alert|shelter in place|evacuate via|avoid all hospitals|report to checkpoint|use route)\b", re.I)),
    ("wet-lab guidance", re.compile(r"\b(reverse genetics|culture protocol|serial passage|viral vector protocol|synthesize the genome|plasmid map|transfection protocol)\b", re.I)),
    ("pathogen engineering", re.compile(r"\b(engineer(?:ed|ing)? pathogen|gain[- ]of[- ]function|increase transmissibility|immune escape mutation)\b", re.I)),
    ("evasion or dissemination", re.compile(r"\b(evade detection|bypass screening|aerosolize|disseminate pathogen|release pathogen|spread undetected)\b", re.I)),
]


def evaluate_news_safety(*parts: Optional[str]) -> SafetyEvaluation:
    text = " ".join(part for part in parts if part).strip()
    reasons: list[str] = []

    if EMAIL_RE.search(text):
        reasons.append("email address")
    if PHONE_RE.search(text):
        reasons.append("phone number")
    if SSN_RE.search(text):
        reasons.append("government identifier")
    if COORDINATE_RE.search(text):
        reasons.append("precise coordinate")

    for label, pattern in DISALLOWED_PATTERNS:
        if pattern.search(text):
            reasons.append(label)

    if reasons:
        return SafetyEvaluation(status="rejected", reasons=sorted(set(reasons)))
    return SafetyEvaluation(status="safe", reasons=[])
