from __future__ import annotations

import re

SCANNER_SERIAL_RE = re.compile(r"^S\d{13,14}$", re.IGNORECASE)
PLAIN_SCANNER_RE = re.compile(r"^\d{13,14}$")
GENERIC_SERIAL_RE = re.compile(r"^[A-Z0-9]{8,20}$")


def clean_token(value: str | None) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


def tokenize_scan(raw_value: str | None) -> list[str]:
    return [
        clean_token(t)
        for t in re.split(r"[\s,;|]+", str(raw_value or "").upper())
        if t and clean_token(t)
    ]


def is_scanner_token(token: str | None) -> bool:
    return bool(SCANNER_SERIAL_RE.fullmatch(str(token or "")))


def is_plain_scanner_token(token: str | None) -> bool:
    return bool(PLAIN_SCANNER_RE.fullmatch(str(token or "")))


def is_generic_token(token: str | None) -> bool:
    return bool(GENERIC_SERIAL_RE.fullmatch(str(token or "")))


def extract_preferred_serial(raw_value: str | None, *, mode: str = "scanner") -> str | None:
    tokens = tokenize_scan(raw_value)
    if not tokens:
        return None

    mode_lower = str(mode or "scanner").lower()
    raw_text = str(raw_value or "")
    has_delimited_payload = any(sep in raw_text for sep in [",", ";", "|"])

    scanner = next((t for t in tokens if is_scanner_token(t)), None)
    if scanner:
        return scanner

    plain_scanner = next((t for t in tokens if is_plain_scanner_token(t)), None)
    if plain_scanner:
        return plain_scanner

    if len(tokens) > 1:
        first = tokens[0]
        if (mode_lower in {"laptop", "other"} or has_delimited_payload) and is_generic_token(first):
            return first
        return None

    only = tokens[0]
    if is_scanner_token(only) or is_plain_scanner_token(only):
        return only
    if mode_lower in {"laptop", "other"} and is_generic_token(only):
        return only
    return None


def normalize_for_store(token: str | None) -> str:
    cleaned = clean_token(token)
    if is_scanner_token(cleaned):
        return cleaned[1:]
    return cleaned
