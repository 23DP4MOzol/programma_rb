from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_DEFAULT_LANG = "lv"


def load_translations(path: str | Path | None = None) -> dict[str, dict[str, str]]:
    file_path = Path(path) if path is not None else Path(__file__).with_name("i18n.json")
    data = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("i18n.json must be an object")
    return {str(lang): {str(k): str(v) for k, v in dict(messages).items()} for lang, messages in data.items()}


def t(translations: dict[str, dict[str, str]], key: str, *, lang: str | None = None, **kwargs: Any) -> str:
    use_lang = (lang or _DEFAULT_LANG).lower()
    messages = translations.get(use_lang) or translations.get(_DEFAULT_LANG) or {}
    template = messages.get(key) or (translations.get(_DEFAULT_LANG, {}).get(key)) or key
    try:
        return template.format(**kwargs)
    except Exception:
        # If placeholders don't match, return raw template rather than crashing.
        return template
