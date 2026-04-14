from __future__ import annotations

import json
import os
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(title="programma_rb remote warranty worker", version="1.0.0")


class WarrantyLookupRequest(BaseModel):
    make: str
    serial: str
    checker_url: str | None = None


def _normalize_make(make: str | None) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", (make or "").strip().lower()).strip()
    if not normalized:
        return ""
    return normalized.split(" ", 1)[0]


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
    return ""


def _extract_all_end_dates(text: str) -> list[str]:
    source = str(text or "")
    pattern = re.compile(
        r"end\s*date\s*(?:[:\-])?\s*"
        r"(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}|\d{4}\.\d{2}\.\d{2}|"
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})",
        flags=re.IGNORECASE,
    )
    found: list[str] = []
    for match in pattern.finditer(source):
        normalized = _normalize_date(match.group(1))
        if normalized:
            found.append(normalized)
    return sorted(set(found))


def _summary_from_text(text: str) -> str:
    hints = ("coverage status", "warranty", "care pack", "expired", "active", "access denied")
    for line in (text or "").splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        if any(h in candidate.lower() for h in hints):
            return candidate[:220]
    return (text or "").strip().replace("\n", " ")[:220]


def _allow_insecure_tls() -> bool:
    raw = str(os.environ.get("WARRANTY_REMOTE_ALLOW_INSECURE_TLS", "")).strip().lower()
    return raw in {"1", "true", "yes", "on"}


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
    timeout_ms = int(str(os.environ.get("WARRANTY_REMOTE_TIMEOUT_MS", "45000")))
    timeout_sec = max(1.0, float(timeout_ms) / 1000.0)
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
        return {
            "ok": False,
            "reason": "remote_blocked_by_captcha",
            "details": "HP page requires captcha or human verification",
            "checker_url": warranty_url,
            "summary": summary,
        }

    status = _derive_status(normalized)
    end_dates = _extract_all_end_dates(normalized)
    end_date = end_dates[-1] if end_dates else ""
    if status == "UNKNOWN" and end_date:
        today = datetime.utcnow().date().isoformat()
        status = "ACTIVE" if end_date >= today else "EXPIRED"

    if status == "UNKNOWN" and not end_date:
        return {
            "ok": False,
            "reason": "remote_no_warranty_text_found",
            "details": "Remote worker could not detect warranty fields",
            "checker_url": warranty_url,
            "summary": summary,
        }

    return {
        "ok": True,
        "status": status,
        "end_date": end_date,
        "summary": summary,
        "checker_url": warranty_url,
    }


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "service": "warranty-worker"}


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
    if make_key != "hp":
        return {
            "ok": False,
            "reason": "remote_make_not_supported",
            "details": f"Remote worker currently supports HP only (got: {payload.make})",
            "checker_url": payload.checker_url or "",
        }

    return _lookup_hp_warranty(payload.serial, payload.checker_url)
