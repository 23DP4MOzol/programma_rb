from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

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


def _extract_end_date(text: str) -> str:
    date_pattern = (
        r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4}|\d{4}\.\d{2}\.\d{2}|"
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b"
    )
    match = re.search(date_pattern, text or "", flags=re.IGNORECASE)
    if not match:
        return ""
    return _normalize_date(match.group(1))


def _summary_from_text(text: str) -> str:
    hints = ("coverage status", "warranty", "care pack", "expired", "active", "access denied")
    for line in (text or "").splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        if any(h in candidate.lower() for h in hints):
            return candidate[:220]
    return (text or "").strip().replace("\n", " ")[:220]


def _safe_hp_checker_url(checker_url: str | None, serial: str) -> str:
    base = (checker_url or "").strip() or "https://support.hp.com/us-en/check-warranty"
    if not base.startswith("https://support.hp.com/"):
        base = "https://support.hp.com/us-en/check-warranty"

    serial_token = re.sub(r"[^A-Za-z0-9\-]", "", (serial or "").strip())
    if not serial_token:
        return base

    if "serialnumber=" in base.lower():
        return base

    sep = "&" if "?" in base else "?"
    return f"{base}{sep}serialnumber={serial_token}"


async def _lookup_hp_warranty(serial: str, checker_url: str | None) -> dict[str, Any]:
    serial_token = re.sub(r"[^A-Za-z0-9\-]", "", (serial or "").strip())
    if not serial_token:
        return {
            "ok": False,
            "reason": "missing_serial",
            "details": "Serial is empty",
        }

    target_url = _safe_hp_checker_url(checker_url, serial_token)

    timeout_ms = int(str(os.environ.get("WARRANTY_REMOTE_TIMEOUT_MS", "45000")))
    headless = str(os.environ.get("WARRANTY_REMOTE_HEADLESS", "1")).strip().lower() not in {"0", "false", "no"}
    browser_channel = str(os.environ.get("WARRANTY_REMOTE_BROWSER_CHANNEL", "")).strip()

    async with async_playwright() as p:
        browser = None
        try:
            launch_args = {
                "headless": headless,
                "args": ["--disable-blink-features=AutomationControlled"],
            }
            if browser_channel:
                try:
                    browser = await p.chromium.launch(channel=browser_channel, **launch_args)
                except Exception:
                    browser = await p.chromium.launch(**launch_args)
            else:
                browser = await p.chromium.launch(**launch_args)

            context = await browser.new_context(locale="en-US")
            page = await context.new_page()
            await page.goto(target_url, wait_until="domcontentloaded", timeout=timeout_ms)

            # Best effort cookie dismiss.
            for selector in (
                "button:has-text('Accept All')",
                "button:has-text('Accept all')",
                "button:has-text('Reject All')",
            ):
                try:
                    btn = page.locator(selector).first
                    if await btn.is_visible(timeout=800):
                        await btn.click(timeout=1200)
                        break
                except Exception:
                    continue

            await page.wait_for_timeout(2200)
            body_text = (await page.locator("body").inner_text()) or ""
            normalized = re.sub(r"\s+", " ", body_text).strip()
            lower_text = normalized.lower()

            if "access denied" in lower_text:
                return {
                    "ok": False,
                    "reason": "remote_access_denied",
                    "details": "HP returned Access Denied from remote worker network",
                    "checker_url": target_url,
                    "summary": _summary_from_text(normalized),
                }

            if "captcha" in lower_text or "verify you are human" in lower_text:
                return {
                    "ok": False,
                    "reason": "remote_blocked_by_captcha",
                    "details": "HP page requires captcha or human verification",
                    "checker_url": target_url,
                    "summary": _summary_from_text(normalized),
                }

            status = _derive_status(normalized)
            end_date = _extract_end_date(normalized)
            summary = _summary_from_text(normalized)

            if status == "UNKNOWN" and not end_date:
                return {
                    "ok": False,
                    "reason": "remote_no_warranty_text_found",
                    "details": "Remote worker could not detect warranty fields",
                    "checker_url": target_url,
                    "summary": summary,
                }

            return {
                "ok": True,
                "status": status,
                "end_date": end_date,
                "summary": summary,
                "checker_url": target_url,
            }
        except PlaywrightTimeoutError:
            return {
                "ok": False,
                "reason": "remote_timeout",
                "details": f"Remote browser timed out after {timeout_ms}ms",
                "checker_url": target_url,
            }
        except Exception as exc:
            return {
                "ok": False,
                "reason": "remote_worker_error",
                "details": str(exc),
                "checker_url": target_url,
            }
        finally:
            if browser is not None:
                await browser.close()


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"ok": True, "service": "warranty-worker"}


@app.post("/warranty/lookup")
async def warranty_lookup(
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

    return await _lookup_hp_warranty(payload.serial, payload.checker_url)
