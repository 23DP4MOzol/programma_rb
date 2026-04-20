from __future__ import annotations

import json
import os
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="programma_rb remote warranty worker", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WarrantyLookupRequest(BaseModel):
    make: str
    serial: str
    checker_url: str | None = None


MAKE_ALIASES: dict[str, str] = {
    "hewlett packard": "hp",
    "hp inc": "hp",
    "hp": "hp",
    "lenovo": "lenovo",
    "zebra technologies": "zebra",
    "zebra": "zebra",
    "samsung electronics": "samsung",
    "samsung": "samsung",
    "apple inc": "apple",
    "apple": "apple",
    "dell inc": "dell",
    "dell": "dell",
    "acer": "acer",
    "asus": "asus",
    "asustek": "asus",
    "microsoft": "microsoft",
}

WARRANTY_WEB_CHECKER_BY_MAKE: dict[str, dict[str, str]] = {
    "hp": {"url": "https://support.hp.com/us-en/check-warranty"},
    "lenovo": {"url": "https://pcsupport.lenovo.com/us/en/warrantylookup#/"},
    "zebra": {"url": "https://support.zebra.com/warrantycheck"},
    "samsung": {"url": "https://www.samsung.com/us/support/warranty/"},
    "apple": {"url": "https://checkcoverage.apple.com/"},
    "dell": {"url": "https://www.dell.com/support/home/en-us/product-support/servicetag/"},
    "acer": {"url": "https://www.acer.com/us-en/support/warranty"},
    "asus": {"url": "https://www.asus.com/support/warranty-status-inquiry/"},
    "microsoft": {"url": "https://support.microsoft.com/devices"},
}

WARRANTY_WEB_CHECKER_SERIAL_PARAM_BY_MAKE: dict[str, str] = {
    "hp": "serialnumber",
    "lenovo": "serial",
    "zebra": "serial",
    "samsung": "serialNumber",
    "apple": "sn",
    "dell": "servicetag",
    "acer": "sn",
    "asus": "sn",
    "microsoft": "serialNumber",
}

WARRANTY_WEB_RESULT_HINTS: tuple[str, ...] = (
    "warranty",
    "coverage",
    "expires",
    "expired",
    "in warranty",
    "out of warranty",
    "valid through",
    "applecare",
    "care pack",
)

WARRANTY_WEB_AUTOMATION_RULES_BY_MAKE: dict[str, dict[str, object]] = {
    "hp": {
        "serial_selectors": (
            "input[id*='serial']",
            "input[name*='serial']",
            "input[placeholder*='Serial']",
            "input[aria-label*='Serial']",
        ),
        "submit_selectors": (
            "button[type='submit']",
            "button[id*='submit']",
            "button[aria-label*='check']",
            "button[aria-label*='search']",
        ),
        "result_selectors": (
            "[id*='warranty']",
            "[class*='warranty']",
            "[data-testid*='warranty']",
            "[id*='result']",
        ),
        "wait_tokens": ("warranty", "care pack", "expired", "active"),
    },
    "lenovo": {
        "serial_selectors": (
            "input[id*='serial']",
            "input[name*='serial']",
            "input[placeholder*='Serial']",
            "input[aria-label*='Serial']",
            "input[id*='machine']",
        ),
        "submit_selectors": (
            "button[type='submit']",
            "button[id*='search']",
            "button[aria-label*='search']",
            "button[aria-label*='submit']",
        ),
        "result_selectors": (
            "[id*='warranty']",
            "[class*='warranty']",
            "[class*='result']",
            "[data-testid*='warranty']",
        ),
        "wait_tokens": ("warranty", "start date", "end date", "expired", "active"),
    },
    "zebra": {
        "serial_selectors": (
            "input[id*='serial']",
            "input[name*='serial']",
            "input[placeholder*='Serial']",
            "input[aria-label*='Serial']",
        ),
        "submit_selectors": (
            "button[type='submit']",
            "button[id*='search']",
            "button[aria-label*='search']",
            "button[aria-label*='check']",
        ),
        "result_selectors": (
            "[id*='warranty']",
            "[class*='warranty']",
            "[class*='result']",
            "[data-testid*='warranty']",
        ),
        "wait_tokens": ("warranty", "in warranty", "out of warranty", "expired", "service"),
    },
    "samsung": {
        "serial_selectors": (
            "input[id*='serial']",
            "input[name*='serial']",
            "input[placeholder*='Serial']",
            "input[aria-label*='Serial']",
        ),
        "submit_selectors": (
            "button[type='submit']",
            "button[id*='search']",
            "button[aria-label*='search']",
            "button[aria-label*='check']",
        ),
        "result_selectors": (
            "[id*='warranty']",
            "[class*='warranty']",
            "[class*='result']",
            "[data-testid*='warranty']",
        ),
        "wait_tokens": ("warranty", "coverage", "parts", "labor", "expired", "active"),
    },
    "apple": {
        "serial_selectors": (
            "input[id*='serial']",
            "input[name*='serial']",
            "input[placeholder*='serial']",
            "input[aria-label*='serial']",
        ),
        "submit_selectors": (
            "button[type='submit']",
            "button[id*='submit']",
            "button[aria-label*='continue']",
            "button[aria-label*='check']",
        ),
        "result_selectors": (
            "[id*='coverage']",
            "[class*='coverage']",
            "[id*='warranty']",
            "[class*='warranty']",
            "[data-testid*='coverage']",
        ),
        "wait_tokens": ("coverage", "applecare", "repairs and service", "valid", "expired"),
    },
}


def _normalize_make(make: str | None) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", (make or "").strip().lower()).strip()
    if not normalized:
        return ""
    if normalized in MAKE_ALIASES:
        return MAKE_ALIASES[normalized]
    first = normalized.split(" ", 1)[0]
    return MAKE_ALIASES.get(first, first)


def _parse_hp_locale(checker_url: str | None) -> str:
    fallback = "us-en"
    source = str(checker_url or "").strip()
    if not source:
        return fallback

    try:
        parsed = urllib.parse.urlparse(source)
        if (parsed.netloc or "").lower() != "support.hp.com":
            return fallback
        first_segment = (parsed.path or "").strip("/").split("/", 1)[0]
        if re.fullmatch(r"[a-z]{2}-[a-z]{2}", first_segment, flags=re.IGNORECASE):
            return first_segment.lower()
    except Exception:
        return fallback

    return fallback


def _remote_timeout_sec() -> float:
    try:
        timeout_ms = int(str(os.environ.get("WARRANTY_REMOTE_TIMEOUT_MS", "20000")))
    except Exception:
        timeout_ms = 20000
    return max(5.0, min(float(timeout_ms) / 1000.0, 30.0))


def _warranty_checker_config_for_make(make_key: str) -> dict[str, str] | None:
    config = WARRANTY_WEB_CHECKER_BY_MAKE.get(make_key)
    return config if isinstance(config, dict) else None


def _warranty_serial_param_for_make(make_key: str) -> str:
    return str(WARRANTY_WEB_CHECKER_SERIAL_PARAM_BY_MAKE.get(make_key) or "").strip()


def _warranty_automation_rules_for_make(make_key: str) -> dict[str, object]:
    rules = WARRANTY_WEB_AUTOMATION_RULES_BY_MAKE.get(make_key)
    return rules if isinstance(rules, dict) else {}


def _build_checker_url_with_serial(*, make_key: str, serial: str, checker_url: str) -> str:
    base = (checker_url or "").strip()
    if not base:
        return ""

    token = re.sub(r"[^A-Za-z0-9\-]", "", (serial or "").strip())
    if not token:
        return base

    serial_param = _warranty_serial_param_for_make(make_key)
    if not serial_param:
        return base

    try:
        parsed = urllib.parse.urlparse(base)
        pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        query: dict[str, str] = {k: v for k, v in pairs}
        if serial_param not in query:
            query[serial_param] = token
        new_query = urllib.parse.urlencode(query)
        return urllib.parse.urlunparse(parsed._replace(query=new_query))
    except Exception:
        return base


def _normalize_sku(product_number: str | None) -> str:
    token = str(product_number or "").strip()
    if not token:
        return ""
    return token.split("#", 1)[0].strip()


def _html_to_text(html: str | None) -> str:
    text = str(html or "")
    text = re.sub(r"(?is)<script\b[^>]*>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style\b[^>]*>.*?</style>", " ", text)
    text = re.sub(r"(?is)<!--.*?-->", " ", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = (
        text.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
    )
    return re.sub(r"\s+", " ", text).strip()


def _derive_status(text: str) -> str:
    lower_text = (text or "").lower()
    if not lower_text:
        return "UNKNOWN"

    expired_terms = ("out of warranty", "expired", "not covered", "no warranty")
    active_terms = ("in warranty", "active", "covered", "valid", "care pack", "applecare")

    if any(term in lower_text for term in expired_terms):
        return "EXPIRED"
    if any(term in lower_text for term in active_terms):
        return "ACTIVE"
    return "UNKNOWN"


def _normalize_date(raw_value: str | None) -> str:
    token = re.sub(r"\s+", " ", str(raw_value or "").strip())
    if not token:
        return ""

    cleaned = token.strip(" .,:;()[]{}")
    if re.fullmatch(r"\d{4}\.\d{2}\.\d{2}", cleaned):
        cleaned = cleaned.replace(".", "-")

    formats = (
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%d/%m/%Y",
        "%d/%m/%y",
        "%b %d %Y",
        "%B %d %Y",
        "%b %d, %Y",
        "%B %d, %Y",
    )
    for fmt in formats:
        try:
            parsed = datetime.strptime(cleaned, fmt)
            return parsed.date().isoformat()
        except Exception:
            continue

    try:
        parsed_iso = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
        return parsed_iso.date().isoformat()
    except Exception:
        pass

    return ""


def _extract_dates_near_keywords(text: str, keywords: tuple[str, ...]) -> list[str]:
    if not text or not keywords:
        return []

    source = str(text or "")
    date_pattern = r"(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}|\d{4}\.\d{2}\.\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})"
    found: list[str] = []

    for keyword in keywords:
        key = re.escape(str(keyword or ""))
        if not key:
            continue

        patterns = (
            rf"{key}.{{0,56}}?{date_pattern}",
            rf"{date_pattern}.{{0,56}}?{key}",
        )
        for pattern in patterns:
            for match in re.finditer(pattern, source, flags=re.IGNORECASE):
                for group in match.groups():
                    normalized = _normalize_date(group)
                    if normalized:
                        found.append(normalized)

    return sorted(set(found))


def _parse_iso_date(token: str | None):
    raw = str(token or "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except Exception:
        return None


def _build_remaining_from_end_date(end_date: str | None) -> tuple[int | None, str]:
    end_obj = _parse_iso_date(end_date)
    if end_obj is None:
        return None, ""

    today = datetime.now(timezone.utc).date()
    days = int((end_obj - today).days)

    if days > 0:
        return days, f"{days} day(s) remaining"
    if days == 0:
        return days, "expires today"
    return days, f"expired {-days} day(s) ago"


def _summary_from_text(text: str) -> str:
    hints = ("coverage status", "warranty", "care pack", "expired", "active", "access denied")
    for line in (text or "").splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        if any(h in candidate.lower() for h in hints):
            return candidate[:220]
    return (text or "").strip().replace("\n", " ")[:220]


def _extract_first_normalized_date(text: str) -> str:
    match = re.search(
        r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}|\d{4}\.\d{2}\.\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b",
        text or "",
        flags=re.IGNORECASE,
    )
    if not match:
        return ""
    return _normalize_date(match.group(1))


def _derive_status_for_make(text: str, make_key: str) -> str:
    lower_text = (text or "").lower()
    if not lower_text:
        return "UNKNOWN"

    expired_terms = ["out of warranty", "not covered", "no warranty", "coverage expired", "warranty expired"]
    active_terms = ["in warranty", "covered", "valid through", "coverage active", "warranty active", "applecare", "care pack"]

    make_terms: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
        "hp": (("out of warranty", "no active care pack", "care pack expired"), ("in warranty", "active care pack", "care pack active")),
        "lenovo": (("out of warranty", "warranty expired"), ("in warranty", "warranty valid")),
        "zebra": (("out of warranty", "not in warranty", "warranty expired"), ("in warranty", "under warranty", "warranty valid")),
        "samsung": (("out of warranty", "warranty expired"), ("warranty valid through", "parts valid", "labor valid")),
        "apple": (("coverage expired",), ("coverage active", "applecare", "repairs and service coverage")),
    }

    extra = make_terms.get(make_key)
    if extra:
        expired_terms.extend(extra[0])
        active_terms.extend(extra[1])

    if any(term in lower_text for term in expired_terms):
        return "EXPIRED"
    if any(term in lower_text for term in active_terms):
        return "ACTIVE"
    return "UNKNOWN"


def _derive_end_date_from_text(text: str, make_key: str) -> str:
    keyword_map: dict[str, tuple[str, ...]] = {
        "hp": ("warranty end", "service end", "coverage end", "end date", "care pack end"),
        "lenovo": ("warranty end", "end date", "expires", "expiration date", "warranty expires"),
        "zebra": ("warranty end", "warranty expires", "expiration", "service end"),
        "samsung": ("parts valid through", "labor valid through", "warranty valid through", "warranty end"),
        "apple": ("estimated expiration date", "coverage end", "applecare", "repairs and service coverage"),
    }

    end_dates = _extract_dates_near_keywords(text, keyword_map.get(make_key, ()))
    if end_dates:
        return end_dates[-1]
    return _extract_first_normalized_date(text)


def _derive_start_date_from_text(text: str, make_key: str) -> str:
    keyword_map: dict[str, tuple[str, ...]] = {
        "hp": ("warranty start", "service start", "coverage start", "start date"),
        "lenovo": ("warranty start", "start date", "coverage start"),
        "zebra": ("warranty start", "start date", "service start"),
        "samsung": ("warranty start", "start date", "coverage start"),
        "apple": ("purchase date", "coverage start", "start date"),
    }

    start_dates = _extract_dates_near_keywords(text, keyword_map.get(make_key, ()))
    return start_dates[0] if start_dates else ""


def _extract_warranty_from_page_text(page_text: str, *, make_key: str, checker_url: str) -> dict[str, Any]:
    normalized_text = re.sub(r"\s+", " ", page_text or "").strip()
    lower_text = normalized_text.lower()
    if not normalized_text:
        return {"ok": False, "reason": "empty_page", "checker_url": checker_url}

    rules = _warranty_automation_rules_for_make(make_key)
    rule_wait_tokens = tuple(str(x).lower() for x in tuple(rules.get("wait_tokens", ())) if str(x).strip())
    hint_tokens = tuple(dict.fromkeys((*WARRANTY_WEB_RESULT_HINTS, *rule_wait_tokens)))

    if any(token in lower_text for token in ("captcha", "verify you are human", "i am not a robot", "recaptcha")):
        return {"ok": False, "reason": "blocked_by_captcha", "checker_url": checker_url}

    lines = [line.strip() for line in (page_text or "").splitlines() if line.strip()]
    interesting_lines = [line for line in lines if any(hint in line.lower() for hint in hint_tokens)]
    summary = interesting_lines[0][:220] if interesting_lines else _summary_from_text(page_text)

    status = _derive_status_for_make(normalized_text, make_key)
    start_date = _derive_start_date_from_text(normalized_text, make_key)
    end_date = _derive_end_date_from_text(normalized_text, make_key)

    has_strong_warranty_context = bool(
        re.search(
            r"(warranty|coverage|care\s*pack|applecare).{0,40}(active|expired|valid|in warranty|out of warranty|end|expires|through|status)",
            lower_text,
            flags=re.IGNORECASE,
        )
        or re.search(
            r"(active|expired|valid|in warranty|out of warranty|end|expires|through|status).{0,40}(warranty|coverage|care\s*pack|applecare)",
            lower_text,
            flags=re.IGNORECASE,
        )
    )

    if status == "UNKNOWN" and end_date:
        today_iso = datetime.now(timezone.utc).date().isoformat()
        status = "ACTIVE" if end_date >= today_iso else "EXPIRED"
    remaining_days, remaining_text = _build_remaining_from_end_date(end_date)

    if status != "UNKNOWN" and not end_date and not has_strong_warranty_context:
        return {
            "ok": False,
            "reason": "ambiguous_result",
            "summary": summary,
            "checker_url": checker_url,
        }

    if not interesting_lines and status == "UNKNOWN" and not end_date:
        return {
            "ok": False,
            "reason": "no_warranty_text_found",
            "summary": summary,
            "checker_url": checker_url,
        }
    if status == "UNKNOWN" and not end_date:
        return {
            "ok": False,
            "reason": "ambiguous_result",
            "summary": summary,
            "checker_url": checker_url,
        }

    return {
        "ok": True,
        "status": status,
        "start_date": start_date,
        "end_date": end_date,
        "remaining_days": remaining_days,
        "remaining_text": remaining_text,
        "summary": summary,
        "checker_url": checker_url,
    }


def _normalize_status_from_specs(raw_status: str | None, fallback_text: str = "") -> str:
    token = str(raw_status or "").strip().lower()
    if token:
        if token in {"active", "inwarranty", "in_warranty", "valid", "current"}:
            return "ACTIVE"
        if token in {"expired", "outofwarranty", "out_of_warranty", "ended"}:
            return "EXPIRED"
    return _derive_status(fallback_text)


def _extract_from_specs_payload(payload: dict[str, Any], checker_url: str) -> dict[str, Any] | None:
    devices = ((payload.get("data") or {}).get("devices") or [])
    if not isinstance(devices, list) or not devices:
        return None

    first_device = devices[0] if isinstance(devices[0], dict) else {}
    warranty_node = first_device.get("warranty") or {}
    warranty_data = (warranty_node.get("data") if isinstance(warranty_node, dict) else {}) or {}
    if not isinstance(warranty_data, dict):
        return None

    start_date = _normalize_date(warranty_data.get("warrantyStartDate") or warranty_data.get("startDate") or "")
    end_date = _normalize_date(
        warranty_data.get("warrantyEndDate")
        or warranty_data.get("hardwareCarePackEndDate")
        or warranty_data.get("endDate")
        or ""
    )
    status = _normalize_status_from_specs(
        warranty_data.get("status") or warranty_data.get("state") or "",
        " ".join(
            str(v or "")
            for v in (
                warranty_data.get("caption"),
                warranty_data.get("tooltip"),
                warranty_data.get("statusDetail"),
            )
        ),
    )
    if status == "UNKNOWN" and end_date:
        today_iso = datetime.now(timezone.utc).date().isoformat()
        status = "ACTIVE" if end_date >= today_iso else "EXPIRED"

    remaining_days, remaining_text = _build_remaining_from_end_date(end_date)
    summary = _summary_from_text(
        " ".join(
            str(v or "")
            for v in (
                warranty_data.get("caption"),
                warranty_data.get("tooltip"),
                warranty_data.get("serviceType"),
                warranty_data.get("statusDetail"),
            )
        )
    )

    if status == "UNKNOWN" and not end_date:
        return None

    return {
        "ok": True,
        "status": status,
        "start_date": start_date,
        "end_date": end_date,
        "remaining_days": remaining_days,
        "remaining_text": remaining_text,
        "summary": summary,
        "checker_url": checker_url,
    }


def _lookup_hp_warranty_via_browser(*, warranty_url: str, timeout_sec: float) -> dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return {
            "ok": False,
            "reason": "browser_fallback_unavailable",
            "details": "Playwright is not installed",
            "checker_url": warranty_url,
        }

    browser_name = str(os.environ.get("WARRANTY_REMOTE_BROWSER", "chromium")).strip().lower() or "chromium"
    channel = str(os.environ.get("WARRANTY_REMOTE_BROWSER_CHANNEL", "")).strip()
    if channel.lower() == "msedge" and not _allow_edge_channel():
        channel = ""

    # Keep total Playwright work bounded so desktop caller timeouts are not exceeded.
    budget_sec = max(8.0, min(float(timeout_sec), 20.0))
    deadline = time.monotonic() + budget_sec

    def _remaining_ms(minimum_ms: int = 2000) -> int:
        remaining = int((deadline - time.monotonic()) * 1000)
        return max(minimum_ms, remaining)

    try:
        with sync_playwright() as p:
            if browser_name == "firefox":
                browser_type = p.firefox
            elif browser_name == "webkit":
                browser_type = p.webkit
            else:
                browser_type = p.chromium

            launch_kwargs: dict[str, Any] = {
                "headless": False,
                "timeout": _remaining_ms(3000),
            }
            exe_path = str(os.environ.get("WARRANTY_REMOTE_BROWSER_EXECUTABLE_PATH") or "").strip()
            if exe_path:
                launch_kwargs["executable_path"] = exe_path
            elif channel and browser_name == "chromium":
                launch_kwargs["channel"] = channel
            if browser_name == "chromium":
                launch_kwargs["args"] = [
                    "--disable-gpu",
                    "--no-first-run",
                    "--no-default-browser-check",
                ]

            try:
                base_dir = os.path.join(os.environ.get("LOCALAPPDATA", ""), f"WARRANTY_REMOTE_PROFILE_{browser_name.upper()}")
                browser_context = browser_type.launch_persistent_context(
                    user_data_dir=base_dir,
                    **launch_kwargs,
                    ignore_https_errors=True,
                    locale="en-US",
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    )
                )
                page = browser_context.pages[0] if browser_context.pages else browser_context.new_page()

                nav_timeout_ms = _remaining_ms(3000)
                page.goto(warranty_url, wait_until="domcontentloaded", timeout=nav_timeout_ms)

                # Try to extract the serial number from the URL
                serial = ""
                try:
                    parsed = urllib.parse.urlparse(warranty_url)
                    query = urllib.parse.parse_qs(parsed.query)
                    if "serialnumber" in query:
                        serial = query["serialnumber"][0]
                except Exception:
                    pass

                # If HP didn't auto-fetch, try filling the inputs and clicking Check
                if serial:
                    try:
                        # Wait for the form element to appear
                        input_box = page.locator("input[id*='Wgt-input'], input[id*='serial'], input[name*='serial'], input[placeholder*='Serial']").first
                        if input_box:
                            input_box.wait_for(state="visible", timeout=10000) # Increased timeout to wait for React to render
                            
                            # Sometimes inputs need a click before filling works, or a clear
                            input_box.click(timeout=2000)
                            input_box.fill(serial)

                            # Handle potential cookie banners that might block the submit button
                            try:
                                cookie_btn = page.locator("button[id*='accept-cookies'], button.banner-close-button, button:has-text('Accept')").first
                                if cookie_btn and cookie_btn.is_visible():
                                    cookie_btn.click(timeout=2000)
                            except Exception:
                                pass

                            # Click the Check / Submit button and await the response 
                            submit_btn = page.locator("button[id*='Wgt-Submit'], button[type='submit'], button[id*='check'], button:has-text('Check warranty')").first
                            if submit_btn:
                                with page.expect_response(
                                    lambda r: "/wcc-services/profile/devices/warranty/specs" in (r.url or "")
                                    and (r.request.method or "").upper() == "POST",
                                    timeout=_remaining_ms(6000)
                                ) as response_info:
                                    submit_btn.click(timeout=3000)
                                response = response_info.value
                    except Exception as loop_e:
                        print("Worker UI filling error:", loop_e)
                        pass # Ignore and continue if form filling fails, maybe it already fired
                
                # If we haven't successfully obtained the response yet (meaning the form click failed or wasn't tried)
                if 'response' not in locals() or not response:
                    response = page.wait_for_response(
                        lambda r: "/wcc-services/profile/devices/warranty/specs" in (r.url or "")
                        and (r.request.method or "").upper() == "POST",
                        timeout=_remaining_ms(3000),
                    )

                status_code = int(response.status or 0)
                body_text = ""
                try:
                    body_text = response.text() or ""
                except Exception:
                    body_text = ""
            finally:
                if 'browser_context' in locals():
                    browser_context.close()
    except Exception as exc:
        return {
            "ok": False,
            "reason": "browser_fallback_error",
            "details": str(exc),
            "checker_url": warranty_url,
        }

    if not body_text:
        return {
            "ok": False,
            "reason": "browser_fallback_no_specs_response",
            "details": "No warranty specs response captured",
            "checker_url": warranty_url,
        }

    if status_code != 200:
        return {
            "ok": False,
            "reason": "browser_fallback_specs_http_error",
            "details": f"Warranty specs request returned HTTP {status_code}",
            "checker_url": warranty_url,
        }

    try:
        parsed = json.loads(body_text)
    except Exception:
        parsed = {}
    extracted = _extract_from_specs_payload(parsed, warranty_url)
    if extracted:
        return extracted

    return {
        "ok": False,
        "reason": "browser_fallback_specs_not_parseable",
        "details": "Warranty specs response was captured but not parseable",
        "checker_url": warranty_url,
    }


def _lookup_generic_warranty_via_browser(*, make_key: str, serial: str, checker_url: str, timeout_sec: float) -> dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return {
            "ok": False,
            "reason": "browser_fallback_unavailable",
            "details": "Playwright is not installed",
            "checker_url": checker_url,
        }

    token = re.sub(r"[^A-Za-z0-9\-]", "", (serial or "").strip())
    if not token:
        return {
            "ok": False,
            "reason": "missing_serial",
            "details": "Serial is empty",
            "checker_url": checker_url,
        }

    rules = _warranty_automation_rules_for_make(make_key)
    serial_selectors = tuple(str(x) for x in tuple(rules.get("serial_selectors", ())) if str(x).strip())
    submit_selectors = tuple(str(x) for x in tuple(rules.get("submit_selectors", ())) if str(x).strip())
    result_selectors = tuple(str(x) for x in tuple(rules.get("result_selectors", ())) if str(x).strip())
    wait_tokens = tuple(
        dict.fromkeys(
            [
                *(str(x).lower() for x in WARRANTY_WEB_RESULT_HINTS),
                *(str(x).lower() for x in tuple(rules.get("wait_tokens", ())) if str(x).strip()),
            ]
        )
    )

    browser_name = str(os.environ.get("WARRANTY_REMOTE_BROWSER", "chromium")).strip().lower() or "chromium"
    configured_channel = str(os.environ.get("WARRANTY_REMOTE_BROWSER_CHANNEL", "")).strip()
    if configured_channel.lower() == "msedge" and not _allow_edge_channel():
        configured_channel = ""
    budget_sec = max(8.0, min(float(timeout_sec), 20.0))
    deadline = time.monotonic() + budget_sec

    def _remaining_ms(minimum_ms: int = 2000) -> int:
        remaining = int((deadline - time.monotonic()) * 1000)
        return max(minimum_ms, remaining)

    launch_errors: list[str] = []
    body_text = ""
    captured_sections: list[str] = []

    def _try_fill_serial(page: Any) -> bool:
        candidates = [
            *serial_selectors,
            "input[id*='serial']",
            "input[name*='serial']",
            "input[placeholder*='Serial']",
            "input[aria-label*='Serial']",
            "input[id*='imei']",
            "input[name*='imei']",
            "input[type='text']",
        ]
        for selector in candidates:
            try:
                elements = page.query_selector_all(selector)
            except Exception:
                elements = []
            for element in elements:
                try:
                    if not element.is_visible():
                        continue
                    element.click(timeout=_remaining_ms(1000))
                    try:
                        element.fill("")
                    except Exception:
                        pass
                    element.type(token, timeout=_remaining_ms(1000))
                    try:
                        element.press("Enter", timeout=_remaining_ms(1000))
                    except Exception:
                        pass
                    return True
                except Exception:
                    continue
        return False

    def _try_submit(page: Any) -> None:
        candidates = [
            *submit_selectors,
            "button[type='submit']",
            "button[id*='submit']",
            "button[id*='search']",
            "button[aria-label*='search']",
            "button[aria-label*='check']",
            "input[type='submit']",
        ]
        for selector in candidates:
            try:
                elements = page.query_selector_all(selector)
            except Exception:
                elements = []
            for element in elements:
                try:
                    if not element.is_visible():
                        continue
                    element.click(timeout=_remaining_ms(1000))
                    return
                except Exception:
                    continue

    try:
        with sync_playwright() as p:
            if browser_name == "firefox":
                browser_type = p.firefox
            elif browser_name == "webkit":
                browser_type = p.webkit
            else:
                browser_type = p.chromium

            launch_variants: list[dict[str, Any]] = []
            if browser_name == "chromium":
                if configured_channel:
                    launch_variants.append({"headless": True, "channel": configured_channel})
                launch_variants.append({"headless": True})
                launch_variants.append({"headless": False})
                if os.name == "nt" and _allow_edge_channel() and configured_channel.lower() != "msedge":
                    launch_variants.append({"headless": True, "channel": "msedge"})
            else:
                launch_variants.append({"headless": True})
                launch_variants.append({"headless": False})

            browser = None
            last_launch_error = ""
            for variant in launch_variants:
                launch_kwargs: dict[str, Any] = {
                    "headless": bool(variant.get("headless", True)),
                    "timeout": _remaining_ms(3000),
                }
                exe_path = str(os.environ.get("WARRANTY_REMOTE_BROWSER_EXECUTABLE_PATH") or "").strip()
                if exe_path:
                    launch_kwargs["executable_path"] = exe_path
                elif variant.get("channel"):
                    launch_kwargs["channel"] = str(variant.get("channel"))
                if browser_name == "chromium":
                    launch_kwargs["args"] = [
                        "--disable-gpu",
                        "--no-default-browser-check",
                    ]
                
                try:
                    base_dir = os.path.join(os.environ.get("LOCALAPPDATA", ""), f"WARRANTY_REMOTE_PROFILE_{browser_name.upper()}")
                    browser_context = browser_type.launch_persistent_context(
                        user_data_dir=base_dir,
                        **launch_kwargs,
                        ignore_https_errors=True,
                        locale="en-US",
                        user_agent=(
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/124.0.0.0 Safari/537.36"
                        )
                    )
                    page = browser_context.pages[0] if browser_context.pages else browser_context.new_page()
                except Exception as launch_exc:
                    last_launch_error = str(launch_exc)
                    launch_errors.append(last_launch_error)
                    continue

                target_url = _build_checker_url_with_serial(make_key=make_key, serial=token, checker_url=checker_url) or checker_url
                page.goto(target_url, wait_until="domcontentloaded", timeout=_remaining_ms(4000))

                before_text = ""
                try:
                    before_text = (page.inner_text("body", timeout=_remaining_ms(1000)) or "").strip()
                except Exception:
                    before_text = ""

                filled = _try_fill_serial(page)
                if filled:
                    _try_submit(page)

                try:
                    page.wait_for_function(
                        """
                        ([tokens, previous]) => {
                            const body = (document.body && document.body.innerText ? document.body.innerText : "").toLowerCase();
                            if (!body) return false;
                            if (previous && body === String(previous).toLowerCase()) return false;
                            return tokens.some(token => body.includes(String(token || "").toLowerCase()));
                        }
                        """,
                        arg=[list(wait_tokens), before_text],
                        timeout=_remaining_ms(3000),
                    )
                except Exception:
                    pass

                for selector in result_selectors:
                    try:
                        for element in page.query_selector_all(selector):
                            try:
                                text = (element.inner_text(timeout=_remaining_ms(1000)) or "").strip()
                            except Exception:
                                text = ""
                            if text:
                                captured_sections.append(text)
                    except Exception:
                        continue

                try:
                    body_text = (page.inner_text("body", timeout=_remaining_ms(1000)) or "").strip()
                except Exception:
                    body_text = ""

                if 'browser_context' in locals():
                    try:
                        browser_context.close()
                    except Exception:
                        pass
                
                if body_text:
                    break

    except Exception as exc:
        return {
            "ok": False,
            "reason": "browser_fallback_error",
            "details": str(exc),
            "checker_url": checker_url,
        }

    joined_text = "\n".join(x for x in (*captured_sections, body_text) if x).strip()
    parsed = _extract_warranty_from_page_text(joined_text, make_key=make_key, checker_url=checker_url)
    if parsed.get("ok"):
        return parsed

    if launch_errors and not str(parsed.get("details") or "").strip():
        parsed["details"] = " | ".join(launch_errors[-2:])
    return parsed


def _lookup_generic_warranty(make_key: str, serial: str, checker_url: str | None) -> dict[str, Any]:
    serial_token = re.sub(r"[^A-Za-z0-9\-]", "", (serial or "").strip())
    if not serial_token:
        return {
            "ok": False,
            "reason": "missing_serial",
            "details": "Serial is empty",
            "checker_url": str(checker_url or ""),
        }

    configured_url = str((checker_url or "").strip() or ((_warranty_checker_config_for_make(make_key) or {}).get("url") or "")).strip()
    if not configured_url:
        return {
            "ok": False,
            "reason": "remote_checker_not_configured",
            "details": f"No checker URL configured for make '{make_key}'",
            "checker_url": "",
        }

    timeout_sec = _remote_timeout_sec()
    insecure_tls = _allow_insecure_tls()
    target_url = _build_checker_url_with_serial(make_key=make_key, serial=serial_token, checker_url=configured_url) or configured_url
    common_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    http_parsed: dict[str, Any] | None = None
    http_error_details = ""
    try:
        html = _http_get_text(
            url=target_url,
            timeout_sec=timeout_sec,
            headers=common_headers,
            insecure_tls=insecure_tls,
        )
        page_text = _html_to_text(html)
        http_parsed = _extract_warranty_from_page_text(page_text, make_key=make_key, checker_url=target_url)
        if http_parsed.get("ok"):
            return http_parsed
    except urllib.error.HTTPError as exc:
        http_error_details = f"Checker HTTP {int(getattr(exc, 'code', 0) or 0)}"
    except Exception as exc:
        http_error_details = str(exc)

    browser_result = _lookup_generic_warranty_via_browser(
        make_key=make_key,
        serial=serial_token,
        checker_url=configured_url,
        timeout_sec=timeout_sec,
    )
    if browser_result.get("ok"):
        return browser_result

    browser_details_raw = str(browser_result.get("details") or "").strip()
    browser_details_concise, browser_policy_blocked = _summarize_browser_failure(browser_details_raw)

    failure_reason = "remote_no_warranty_text_found"
    if isinstance(http_parsed, dict) and str(http_parsed.get("reason") or "").strip():
        parsed_reason = str(http_parsed.get("reason") or "").strip()
        reason_map = {
            "empty_page": "remote_no_warranty_text_found",
            "no_warranty_text_found": "remote_no_warranty_text_found",
            "ambiguous_result": "remote_ambiguous_result",
            "blocked_by_captcha": "remote_blocked_by_captcha",
        }
        failure_reason = reason_map.get(parsed_reason, f"remote_{parsed_reason}")
    elif http_error_details:
        failure_reason = "remote_warranty_http_error"

    if browser_policy_blocked:
        failure_reason = "remote_browser_policy_blocked"

    details_parts = [
        str(http_parsed.get("details") or "").strip() if isinstance(http_parsed, dict) else "",
        http_error_details,
        browser_details_concise,
    ]
    details = " | ".join(x for x in details_parts if x)

    return {
        "ok": False,
        "reason": failure_reason,
        "details": details or "Remote worker could not detect warranty fields",
        "checker_url": target_url,
        "summary": str((http_parsed or {}).get("summary") or ""),
        "browser_fallback": browser_result,
    }


def _allow_insecure_tls() -> bool:
    raw = str(os.environ.get("WARRANTY_REMOTE_ALLOW_INSECURE_TLS", "")).strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _allow_edge_channel() -> bool:
    raw = str(os.environ.get("WARRANTY_REMOTE_ALLOW_EDGE_CHANNEL", "")).strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _summarize_browser_failure(details: str) -> tuple[str, bool]:
    text = str(details or "").strip()
    lowered = text.lower()
    policy_signals = (
        "devtools remote debugging is disallowed",
        "group policy",
        "session not created",
        "spawn unknown",
    )
    if any(signal in lowered for signal in policy_signals):
        return "Browser automation is blocked by local system policy", True
    return (text[:280] if text else "Browser automation failed"), False


def _http_get_text(*, url: str, timeout_sec: float, headers: dict[str, str], insecure_tls: bool) -> str:
    request = urllib.request.Request(url, headers=headers, method="GET")
    open_kwargs: dict[str, Any] = {"timeout": timeout_sec}
    if insecure_tls:
        open_kwargs["context"] = ssl._create_unverified_context()
    with urllib.request.urlopen(request, **open_kwargs) as response:
        content_type = str(response.headers.get("Content-Type") or "")
        charset = "utf-8"
        match = re.search(r"charset=([A-Za-z0-9_\-]+)", content_type, flags=re.IGNORECASE)
        if match:
            charset = match.group(1)
        raw = response.read() or b""
    return raw.decode(charset, errors="ignore")


def _http_get_json(*, url: str, timeout_sec: float, headers: dict[str, str], insecure_tls: bool) -> dict[str, Any]:
    payload = _http_get_text(url=url, timeout_sec=timeout_sec, headers=headers, insecure_tls=insecure_tls)
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise ValueError("JSON response is not an object")
    return parsed


def _lookup_hp_warranty(serial: str, checker_url: str | None) -> dict[str, Any]:
    serial_token = re.sub(r"[^A-Za-z0-9\-]", "", (serial or "").strip())
    if not serial_token:
        return {
            "ok": False,
            "reason": "missing_serial",
            "details": "Serial is empty",
        }

    locale = _parse_hp_locale(checker_url)
    checker_entry_url = f"https://support.hp.com/{locale}/check-warranty"
    timeout_sec = _remote_timeout_sec()
    insecure_tls = _allow_insecure_tls()

    common_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    search_url = f"https://support.hp.com/wcc-services/searchresult/{locale}"
    query = urllib.parse.urlencode({"q": serial_token, "context": "pdp", "navigation": "true"})
    search_url = f"{search_url}?{query}"

    try:
        search_json = _http_get_json(
            url=search_url,
            timeout_sec=timeout_sec,
            headers={
                **common_headers,
                "Accept": "application/json, text/plain, */*",
                "Referer": checker_entry_url,
            },
            insecure_tls=insecure_tls,
        )
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "reason": "remote_search_http_error",
            "details": f"HP searchresult HTTP {int(getattr(exc, 'code', 0) or 0)}",
            "checker_url": checker_entry_url,
        }
    except Exception as exc:
        return {
            "ok": False,
            "reason": "remote_worker_error",
            "details": str(exc),
            "checker_url": checker_entry_url,
        }

    verify_node = ((search_json.get("data") or {}).get("verifyResponse") or {})
    verify_code = int(verify_node.get("code") or 0)
    verify_data = verify_node.get("data") or {}
    if verify_code != 200 or not isinstance(verify_data, dict):
        return {
            "ok": False,
            "reason": "remote_search_no_device",
            "details": str(verify_node.get("message") or search_json.get("message") or "Device not found from HP search"),
            "checker_url": checker_entry_url,
        }

    seo_name = str(verify_data.get("SEOFriendlyName") or "").strip()
    series_oid = str(verify_data.get("productSeriesOID") or "").strip()
    model_oid = str(verify_data.get("productNameOID") or verify_data.get("productNamOID") or "").strip()
    sku = _normalize_sku(str(verify_data.get("altProductNumber") or verify_data.get("productNumber") or ""))
    serial_out = str(verify_data.get("serialNumber") or serial_token).strip() or serial_token
    start_date_hint = _normalize_date(verify_data.get("warrantyStartDate") or verify_data.get("startDate") or "")
    end_date_hint = _normalize_date(verify_data.get("warrantyEndDate") or verify_data.get("endDate") or "")

    if not (seo_name and series_oid and model_oid):
        return {
            "ok": False,
            "reason": "remote_search_incomplete_metadata",
            "details": "HP searchresult missing required route metadata",
            "checker_url": checker_entry_url,
        }

    warranty_path = (
        f"/{locale}/warrantyresult/{urllib.parse.quote(seo_name)}/{urllib.parse.quote(series_oid)}"
        f"/model/{urllib.parse.quote(model_oid)}"
    )
    params = {"serialnumber": serial_out}
    if sku:
        params["sku"] = sku
    warranty_url = f"https://support.hp.com{warranty_path}?{urllib.parse.urlencode(params)}"

    try:
        html = _http_get_text(
            url=warranty_url,
            timeout_sec=timeout_sec,
            headers={
                **common_headers,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": checker_entry_url,
            },
            insecure_tls=insecure_tls,
        )
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "reason": "remote_warranty_http_error",
            "details": f"HP warranty page HTTP {int(getattr(exc, 'code', 0) or 0)}",
            "checker_url": warranty_url,
        }
    except Exception as exc:
        return {
            "ok": False,
            "reason": "remote_worker_error",
            "details": str(exc),
            "checker_url": warranty_url,
        }

    normalized = _html_to_text(html)
    lower_text = normalized.lower()
    summary = _summary_from_text(normalized)

    if "access denied" in lower_text:
        return {
            "ok": False,
            "reason": "remote_access_denied",
            "details": "HP returned Access Denied from worker network",
            "checker_url": warranty_url,
            "summary": summary,
        }
    if "captcha" in lower_text or "verify you are human" in lower_text or "recaptcha" in lower_text:
        browser_result = _lookup_hp_warranty_via_browser(warranty_url=warranty_url, timeout_sec=timeout_sec)
        if browser_result.get("ok"):
            return browser_result
        browser_details = str(browser_result.get("details") or "")
        concise_details, is_policy_blocked = _summarize_browser_failure(browser_details)
        if is_policy_blocked:
            return {
                "ok": False,
                "reason": "remote_browser_policy_blocked",
                "details": concise_details,
                "checker_url": warranty_url,
                "summary": summary,
                "browser_fallback": browser_result,
            }
        return {
            "ok": False,
            "reason": "remote_blocked_by_captcha",
            "details": "HP page requires captcha or human verification",
            "checker_url": warranty_url,
            "summary": summary,
            "browser_fallback": browser_result,
        }

    status = _derive_status(normalized)
    start_dates = _extract_dates_near_keywords(
        normalized,
        (
            "start date",
            "warranty start",
            "coverage start",
            "service start",
            "warranty begins",
        ),
    )
    end_dates = _extract_dates_near_keywords(
        normalized,
        (
            "end date",
            "warranty end",
            "coverage end",
            "service end",
            "expiration date",
            "expires",
            "valid through",
            "care pack end",
        ),
    )

    start_date = start_dates[0] if start_dates else start_date_hint
    end_date = end_dates[-1] if end_dates else end_date_hint
    if status == "UNKNOWN" and end_date:
        today = datetime.now(timezone.utc).date().isoformat()
        status = "ACTIVE" if end_date >= today else "EXPIRED"

    remaining_days, remaining_text = _build_remaining_from_end_date(end_date)

    if status == "UNKNOWN" and not end_date:
        browser_result = _lookup_hp_warranty_via_browser(warranty_url=warranty_url, timeout_sec=timeout_sec)
        if browser_result.get("ok"):
            return browser_result
        browser_details = str(browser_result.get("details") or "")
        concise_details, is_policy_blocked = _summarize_browser_failure(browser_details)
        if is_policy_blocked:
            return {
                "ok": False,
                "reason": "remote_browser_policy_blocked",
                "details": concise_details,
                "checker_url": warranty_url,
                "summary": summary,
                "browser_fallback": browser_result,
            }
        return {
            "ok": False,
            "reason": "remote_no_warranty_text_found",
            "details": concise_details or "Remote worker could not detect warranty fields",
            "checker_url": warranty_url,
            "summary": summary,
            "browser_fallback": browser_result,
        }

    return {
        "ok": True,
        "status": status,
        "start_date": start_date,
        "end_date": end_date,
        "remaining_days": remaining_days,
        "remaining_text": remaining_text,
        "summary": summary,
        "checker_url": warranty_url,
    }


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "service": "warranty-worker"}


@app.get("/warranty/lookup")
def warranty_lookup_get(
    make: str,
    serial: str,
    checker_url: str | None = None,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    payload = WarrantyLookupRequest(make=make, serial=serial, checker_url=checker_url)
    return warranty_lookup(payload, x_api_key, authorization)

@app.post("/warranty/lookup")
def warranty_lookup(
    payload: WarrantyLookupRequest,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    configured_key = str(os.environ.get("WARRANTY_REMOTE_API_KEY", "")).strip()
    if configured_key:
        bearer = ""
        if authorization and authorization.lower().startswith("bearer "):
            bearer = authorization.split(" ", 1)[1].strip()
        candidate_keys = {str(x_api_key or "").strip(), bearer}
        if configured_key not in candidate_keys:
            raise HTTPException(status_code=401, detail="Invalid API key")

    make_key = _normalize_make(payload.make)
    if not make_key:
        return {
            "ok": False,
            "reason": "remote_make_not_supported",
            "details": f"Unrecognized make: {payload.make}",
            "checker_url": payload.checker_url or "",
        }

    checker_url = str(payload.checker_url or "").strip()
    if make_key == "hp":
        hp_result = _lookup_hp_warranty(payload.serial, checker_url)
        if hp_result.get("ok"):
            return hp_result

        hp_reason = str(hp_result.get("reason") or "").strip()
        if hp_reason in {
            "remote_no_warranty_text_found",
            "remote_blocked_by_captcha",
            "remote_warranty_http_error",
            "remote_worker_error",
        }:
            generic_result = _lookup_generic_warranty(make_key, payload.serial, checker_url)
            if generic_result.get("ok"):
                return generic_result
            generic_result.setdefault("hp_specialized", hp_result)
            return generic_result
        return hp_result

    if not checker_url:
        checker_url = str((_warranty_checker_config_for_make(make_key) or {}).get("url") or "").strip()

    if not checker_url:
        return {
            "ok": False,
            "reason": "remote_checker_not_configured",
            "details": f"No checker URL configured for make '{make_key}'",
            "checker_url": "",
        }

    return _lookup_generic_warranty(make_key, payload.serial, checker_url)
