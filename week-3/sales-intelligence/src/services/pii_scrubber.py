import re

from collections import Counter
from src.models.schemas import GuardResult

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(\+1[-\s]?)?(\(?\d{3}\)?[-\s]?)\d{3}[-\s]?\d{4}")
CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
AMOUNT_RE = re.compile(r"\$\d{1,3}(?:,\d{3})*(?:\.\d+)?|\$\d+(?:\.\d+)?[MK]?")
NAME_RE = re.compile(r"(?<!^)(?:\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b)")

INJECTION_PATTERNS = [
    "ignore previous instructions",
    "disregard your system prompt",
    "you are now",
    "new instruction:",
    "forget everything",
]

def scrub_pii(transcript: str) -> str:
    transcript = EMAIL_RE.sub("[EMAIL]", transcript)
    transcript = PHONE_RE.sub("[PHONE]", transcript)
    transcript = CARD_RE.sub("[CARD]", transcript)
    transcript = AMOUNT_RE.sub("[AMOUNT]", transcript)
    transcript = NAME_RE.sub("[NAME]", transcript)
    return transcript

def scrubbed_entities(scrubbed: str) -> dict[str, int]:
    return {
        "EMAIL": scrubbed.count("[EMAIL]"),
        "PHONE": scrubbed.count("[PHONE]"),
        "CARD": scrubbed.count("[CARD]"),
        "AMOUNT": scrubbed.count("[AMOUNT]"),
        "NAME": scrubbed.count("[NAME]"),
    }

def check_injection(text: str, max_length: int = 8192) -> GuardResult:
    if len(text) > max_length:
        return GuardResult(is_safe=False, reason="Input exceeds maximum length",)
    lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if pattern in lower:
            return GuardResult(is_safe=False, reason="Potential prompt injection detected",)
    return GuardResult(is_safe=True, reason=None,)