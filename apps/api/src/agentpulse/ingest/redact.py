"""PII redaction engine applied before trace persistence."""

import re
from typing import cast

# Regex patterns for common sensitive PII
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
PHONE_REGEX = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
CREDIT_CARD_REGEX = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")
SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def redact_text(text: str) -> str:
    """Redact identifiable personal data from string."""
    if not text:
        return text
    text = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
    text = CREDIT_CARD_REGEX.sub("[REDACTED_CARD]", text)
    text = SSN_REGEX.sub("[REDACTED_SSN]", text)
    text = PHONE_REGEX.sub("[REDACTED_PHONE]", text)
    return text


def redact_data(data: object) -> object:
    """Recursively redact PII from strings, lists, and dictionaries."""
    if isinstance(data, str):
        return redact_text(data)
    if isinstance(data, dict):
        d = cast(dict[object, object], data)
        result: dict[str, object] = {}
        for k, v in d.items():
            result[str(k)] = redact_data(v)
        return result
    if isinstance(data, list):
        lst = cast(list[object], data)
        return [redact_data(item) for item in lst]
    return data
