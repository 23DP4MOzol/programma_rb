from __future__ import annotations

import base64
import calendar
import html
import io
import json
import os
import shutil
import subprocess
import threading
import traceback
import tkinter as tk
import webbrowser
from datetime import date, datetime, timezone
from tkinter import font as tkfont
from tkinter import simpledialog
import re
import socket
import ssl
from dataclasses import asdict
from pathlib import Path
from tkinter import messagebox
from tkinter import ttk
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest
import zipfile

from i18n import load_translations, t
from serial_parsing import extract_preferred_serial, normalize_for_store
from supabase_db import ALLOWED_STATUSES, Device, InventoryDB, SyncConflictError


DEVICE_TYPES: list[str] = ["scanner", "laptop", "tablet", "phone", "printer", "other"]

SERIAL_PREFIX_MAP: dict[str, tuple[str, str, str]] = {
    # Prefix: ("device_type", "Make", "Make Model")
    # Zebra scanners often start with these (example patterns, edit these to match your actual fleet!)
    "19": ("scanner", "Zebra", "Zebra TC52"),    # e.g., 19055...
    "20": ("scanner", "Zebra", "Zebra TC52"),    # e.g., 20334...
    "24": ("scanner", "Zebra", "Zebra TC52"),
    "17": ("scanner", "Zebra", "Zebra TC51"),    # e.g., 17094...
    "18": ("scanner", "Zebra", "Zebra TC51"),
    "21": ("scanner", "Zebra", "Zebra TC52"),
    "40": ("scanner", "Zebra", "Zebra MC3300"),
    "5CG21": ("laptop", "HP", "HP EliteBook 830 G8"),
    "5CG32": ("laptop", "HP", "HP EliteBook 840 G10"),
    "5CG": ("laptop", "HP", "HP EliteBook"),
}

DEVICE_CATALOG: dict[str, dict[str, list[str]]] = {
    "scanner": {
        "Zebra": ["DS2208", "DS2278", "DS3608", "DS3678", "DS4608", "DS4678", "DS8108", "DS8178", "DS9308", "LI2208", "LS2208", "RS5100", "RS6100", "SE4710", "TC20", "TC21", "TC22", "TC25", "TC26", "TC51", "TC52", "TC53", "TC53-HC", "TC56", "TC57", "TC58", "TC58-HC", "TC70", "TC70x", "TC72", "TC75", "TC75x", "TC77", "MC40", "MC55", "MC67", "MC92N0", "MC93", "MC2200", "MC2700", "MC3300", "MC3300x", "MC3390x", "WS50"],
        "Datalogic": ["Gryphon GD4500", "Gryphon GBT4500", "Gryphon GM4500", "QuickScan QD2430", "QuickScan QD2500", "PowerScan PD9630", "PowerScan PM9600", "PowerScan PBT9600", "Memor 10", "Memor 11", "Skorpio X4", "Skorpio X5", "Falcon X4", "Joya Touch"],
        "Apple": ["MacBook Air M1", "MacBook Air M2", "MacBook Air M3", "MacBook Pro 13", "MacBook Pro 14", "MacBook Pro 16", "Mac Mini", "Mac Studio", "iMac", "Mac Pro"],
        "Asus": ["ZenBook 14", "ZenBook Duo", "ZenBook Pro", "VivoBook 15", "VivoBook Pro", "ROG Zephyrus", "ROG Strix", "TUF Gaming", "ExpertBook"],
        "Dell": ["Latitude 3420", "Latitude 5430", "Latitude 5440", "Latitude 7330", "Latitude 7430", "Latitude 7440", "XPS 13", "XPS 15", "Precision 3570", "Precision 3580", "Vostro 3520", "Inspiron 15", "Alienware m15", "Alienware x14"]
    },
    "laptop": {
        "Dell": ["Latitude 3420", "Latitude 5430", "Latitude 5440", "Latitude 7330", "Latitude 7430", "Latitude 7440", "XPS 13", "XPS 15", "Precision 3570", "Precision 3580", "Vostro 3520", "Inspiron 15", "Alienware m15", "Alienware x14"],
        "Asus": ["ZenBook 14", "ZenBook Duo", "ZenBook Pro", "VivoBook 15", "VivoBook Pro", "ROG Zephyrus", "ROG Strix", "TUF Gaming", "ExpertBook"],
        "HP": ["EliteBook 830 G8", "EliteBook 830 G9", "EliteBook 840 G8", "EliteBook 840 G9", "EliteBook 840 G10", "EliteBook 850 G8", "ProBook 440 G8", "ProBook 450 G8", "ProBook 440 G9", "ProBook 450 G9", "ZBook Firefly 14", "ZBook Power 15"],
        "Apple": ["MacBook Air 13 M1", "MacBook Air 13 M2", "MacBook Air 15 M2", "MacBook Pro 13", "MacBook Pro 14", "MacBook Pro 16"]
    },
    "tablet": {
        "Samsung": ["Galaxy Tab A7", "Galaxy Tab A8", "Galaxy Tab S6 Lite", "Galaxy Tab S7", "Galaxy Tab S8", "Galaxy Tab S9", "Galaxy Tab Active3", "Galaxy Tab Active4 Pro", "Galaxy Tab Active5"],
        "Apple": ["iPad 9th Gen", "iPad 10th Gen", "iPad Air 5", "iPad Mini 6", "iPad Pro 11", "iPad Pro 12.9"],
        "Zebra": ["ET40", "ET45", "L10", "XSLATE L10"]
    },
    "phone": {
        "Samsung": ["Galaxy S21", "Galaxy S22", "Galaxy S23", "Galaxy S24", "Galaxy A54", "Galaxy A55", "Galaxy XCover 5", "Galaxy XCover 6 Pro", "Galaxy XCover 7"],
        "Apple": ["iPhone 11", "iPhone 12", "iPhone 13", "iPhone 14", "iPhone 15", "iPhone 16", "iPhone SE"]
    },
    "printer": {
        "Zebra": ["ZD220", "ZD230", "ZD421", "ZD621", "ZT111", "ZT231", "ZT411", "ZT421", "GK420d", "GX430t", "QLn220", "QLn320", "ZQ310", "ZQ320", "ZQ511", "ZQ521", "ZR138"]
    },
    "other": {
        "HP": ["Engage One", "Engage Flex Pro", "RP9"],
        "Datalogic": ["Magellan 1500i", "Magellan 3410VSi", "Joya Touch A6"],
        "Zebra": ["CC600", "CC6000", "DS9308 Scale", "MP7000"]
    }
}
WARRANTY_MARKER)
        if idx < 0:
            return text, None

        base = text[:idx].rstrip(" |")
        warranty = text[idx:].strip() or None
        return base, warranty

    def _prepare_comment_for_persist(
        self,
        comment: str | None,
        *,
        serial: str,
        device_type: str,
        created_at: str | None,
        allow_admin_override: bool,
    ) -> str | None:
        raw = (comment or "").strip()
        if allow_admin_override:
            return raw or None

        base_comment, old_warranty = self._split_comment_and_warranty(raw)
        trusted_warranty = (old_warranty or "").strip() if self._is_trusted_warranty_segment(old_warranty) else ""
        if trusted_warranty:
            if base_comment:
                return f"{base_comment} | {trusted_warranty}"
            return trusted_warranty

        marker = self._build_warranty_marker(serial=serial, device_type=device_type, created_at=created_at)
        if not marker:
            return base_comment or None
        if base_comment:
            return f"{base_comment} | {marker}"
        return marker

    def _comment_with_warranty_preview(
        self,
        comment: str | None,
        *,
        serial: str,
        device_type: str,
        created_at: str | None,
    ) -> str:
        return (
            self._prepare_comment_for_persist(
                comment,
                serial=serial,
                device_type=device_type,
                created_at=created_at,
                allow_admin_override=False,
            )
            or ""
        )

    def _resolve_created_at_for_serial(self, serial: str | None) -> str | None:
        if self._selected_created_at:
            return self._selected_created_at

        key = (serial or "").strip()
        if not key:
            return None

        try:
            existing = self.db.get_device(key)
            return existing.created_at if existing else None
        except Exception:
            return None

    def _refresh_warranty_comment_preview(
        self,
        *,
        serial: str | None = None,
        device_type: str | None = None,
        created_at: str | None = None,
    ) -> None:
        resolved_serial = (serial if serial is not None else self.serial_var.get()).strip()
        resolved_type = device_type or (self._code_from_display(self.type_var.get(), kind="type") or "scanner")
        resolved_created = created_at if created_at is not None else self._selected_created_at
        self.comment_var.set(
            self._comment_with_warranty_preview(
                self.comment_var.get(),
                serial=resolved_serial,
                device_type=resolved_type,
                created_at=resolved_created,
            )
        )

    def check_warranty_from_web_checker(self) -> None:
        if self._warranty_lookup_in_progress:
            return

        serial = (self.serial_var.get() or "").strip()
        if not serial:
            messagebox.showerror(self.tr("desktop_error_title"), self.tr("desktop_warranty_missing_serial"), parent=self.root)
            return

        make = (self.make_var.get() or "").strip()
        if not make:
            messagebox.showerror(self.tr("desktop_error_title"), self.tr("desktop_warranty_missing_make"), parent=self.root)
            return

        self._warranty_lookup_in_progress = True
        try:
            self.warranty_btn.configure(state="disabled")
        except Exception:
            pass
        self._write_result(
            {
                "ok": True,
                "info": self.tr("desktop_warranty_checking"),
                "serial": serial,
                "make": make,
            }
        )

        def _worker() -> None:
            result = self._lookup_warranty_via_web_checker(make=make, serial=serial)

            def _done() -> None:
                self._warranty_lookup_in_progress = False
                try:
                    self.warranty_btn.configure(state="normal")
                except Exception:
                    pass

                checker_url = str(result.get("checker_url") or (self._warranty_checker_config_for_make(make) or {}).get("url") or "")
                config_url = str((self._warranty_checker_config_for_make(make) or {}).get("url") or "").strip()
                make_key = self._normalize_make_for_warranty_checker(make)
                manual_checker_url = ""
                if config_url:
                    manual_checker_url = self._build_checker_url_with_serial(
                        make=make,
                        serial=serial,
                        checker_url=config_url,
                    ) or config_url
                if make_key == "hp":
                    manual_checker_url = config_url or manual_checker_url or checker_url
                if not manual_checker_url:
                    manual_checker_url = checker_url

                base_comment, _ = self._split_comment_and_warranty(self.comment_var.get())

                if bool(result.get("ok")):
                    status = str(result.get("status") or "UNKNOWN")
                    start_date = str(result.get("start_date") or "").strip() or None
                    end_date = str(result.get("end_date") or "").strip() or None
                    remaining_text = str(result.get("remaining_text") or "").strip()
                    remaining_days_raw = result.get("remaining_days")
                    remaining_days: int | None = None
                    if isinstance(remaining_days_raw, int):
                        remaining_days = remaining_days_raw
                    elif isinstance(remaining_days_raw, str):
                        try:
                            remaining_days = int(remaining_days_raw.strip())
                        except Exception:
                            remaining_days = None

                    if not remaining_text:
                        _, remaining_text = self._build_time_remaining_from_end_date(end_date)

                    marker = self._build_web_warranty_verified_marker(
                        make=make,
                        serial=serial,
                        status=status,
                        start_date=start_date,
                        end_date=end_date,
                        time_remaining=remaining_text,
                        checker_url=checker_url,
                    )
                    self.comment_var.set(f"{base_comment} | {marker}" if base_comment else marker)
                    self._write_result(
                        {
                            "ok": True,
                            "info": self.tr("desktop_warranty_found", status=status),
                            "serial": serial,
                            "make": make,
                            "start_date": start_date,
                            "end_date": end_date,
                            "remaining_days": remaining_days,
                            "time_remaining": remaining_text,
                            "summary": str(result.get("summary") or ""),
                            "source": checker_url,
                        }
                    )
                    return

                reason = str(result.get("reason") or "not_found")
                marker = self._build_web_warranty_not_found_marker(make=make, serial=serial, checker_url=manual_checker_url)
                self.comment_var.set(f"{base_comment} | {marker}" if base_comment else marker)
                opened_manual_checker = False
                copied_checker_url = False
                if manual_checker_url and reason not in {
                    "make_not_supported",
                    "checker_not_configured",
                    "remote_worker_unavailable",
                    "remote_worker_route_not_found",
                    "remote_worker_unauthorized",
                    "remote_worker_http_error",
                }:
                    # Change: Copy SERIAL instead of URL to clipboard since the URL auto-opens
                    copied_checker_url = self._copy_to_clipboard(serial)
                    opened_manual_checker = self._open_checker_in_system_browser(manual_checker_url)

                if reason == "make_not_supported":
                    info = self.tr("desktop_warranty_unsupported_make", make=make)
                elif reason == "remote_make_not_supported":
                    info = self.tr("desktop_warranty_unsupported_make", make=make)
                elif reason == "remote_checker_not_configured":
                    info = self.tr("desktop_warranty_unsupported_make", make=make)
                elif reason == "selenium_missing":
                    info = self.tr("desktop_warranty_selenium_missing")
                elif reason == "browser_launch_failed":
                    info = self.tr("desktop_warranty_driver_missing")
                elif reason == "browser_policy_blocked":
                    info = self.tr("desktop_warranty_opened_checker_manual", url=manual_checker_url) if opened_manual_checker else self.tr("desktop_warranty_browser_policy_blocked")
                elif reason == "dynamic_page_requires_browser":
                    info = self.tr("desktop_warranty_opened_checker_manual", url=manual_checker_url) if opened_manual_checker else self.tr("desktop_warranty_dynamic_page")
                elif reason == "remote_worker_route_not_found":
                    info = self.tr("desktop_warranty_remote_worker_route_not_found")
                elif reason == "remote_worker_unauthorized":
                    info = self.tr("desktop_warranty_remote_worker_unauthorized")
                elif reason == "remote_worker_http_error":
                    info = self.tr("desktop_warranty_remote_worker_http_error")
                elif reason == "remote_worker_unavailable":
                    info = self.tr("desktop_warranty_remote_worker_unavailable")
                elif reason == "remote_browser_policy_blocked":
                    info = self.tr("desktop_warranty_browser_policy_blocked")
                else:
                    info = self.tr("desktop_warranty_not_found")

                if copied_checker_url and manual_checker_url:
                    info = f"Opened HP site natively. SERIAL COPIED TO CLIPBOARD! Press Ctrl+V."
                elif opened_manual_checker and manual_checker_url:
                    info = self.tr("desktop_warranty_opened_checker_manual", url=manual_checker_url)

                self._write_result(
                    {
                        "ok": False,
                        "info": info,
                        "reason": reason,
                        "serial": serial,
                        "make": make,
                        "source": manual_checker_url,
                        "details": str(result.get("details") or ""),
                    },
                    ok=False,
                )

            self.root.after(0, _done)

        threading.Thread(target=_worker, daemon=True).start()

    # ---------- Config / Prefix Rules ----------

    def _load_config(self) -> dict:
        cfg = dict(self._config_defaults)
        try:
            if self._config_path.exists():
                data = json.loads(self._config_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    cfg.update(data)
        except Exception:
            pass
        return cfg

    def _save_config(self) -> None:
        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            self._config_path.write_text(json.dumps(self.config, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _load_prefix_rules(self) -> dict[str, tuple[str, str, str]]:
        rules: dict[str, tuple[str, str, str]] = {}
        raw = (self.config or {}).get("prefix_rules")
        if not raw:
            return rules
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, (list, tuple)) and len(v) == 3:
                        rules[str(k)] = (str(v[0]), str(v[1]), str(v[2]))
        except Exception:
            pass
        return rules

    def _get_prefix_rules(self) -> dict[str, tuple[str, str, str]]:
        merged = dict(SERIAL_PREFIX_MAP)

        try:
            merged.update(self.db.list_prefix_rules())
        except Exception:
            pass

        merged.update(self._custom_prefix_rules or {})
        return merged

    # ---------- Offline Queue ----------

    def _load_pending_ops(self) -> list[dict]:
        try:
            if self._pending_ops_path.exists():
                data = json.loads(self._pending_ops_path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return data
        except Exception:
            pass
        return []

    def _save_pending_ops(self, ops: list[dict]) -> None:
        try:
            self._pending_ops_path.parent.mkdir(parents=True, exist_ok=True)
            self._pending_ops_path.write_text(json.dumps(ops, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _enqueue_op(self, op: dict) -> None:
        ops = self._load_pending_ops()
        ops.append(op)
        self._save_pending_ops(ops)

    def _flush_pending_ops(self) -> tuple[int, int]:
        ops = self._load_pending_ops()
        if not ops:
            return 0, 0
        remaining: list[dict] = []
        synced = 0
        for op in ops:
            try:
                action = op.get("action")
                if action == "add":
                    dev = Device(**op.get("device", {}))
                    self.db.add_device(dev, overwrite=bool(op.get("overwrite")))
                elif action == "update":
                    self.db.update_device(op.get("serial", ""), **op.get("fields", {}))
                elif action == "status":
                    self.db.change_status(op.get("serial", ""), op.get("status", "RECEIVED"), to_store=op.get("to_store"), comment=op.get("comment"))
                elif action == "delete":
                    self.db.delete_device(op.get("serial", ""))
                else:
                    raise ValueError("Unknown op")
                synced += 1
            except Exception:
                remaining.append(op)

        self._save_pending_ops(remaining)
        return synced, len(remaining)

    # ---------- Action (form) dependent dropdowns ----------

    def _refresh_action_make_model_values(self, *, preserve_typed_model: bool) -> None:
        device_type = self._code_from_display(self.type_var.get(), kind="type") or "scanner"
        current_make = self.make_var.get().strip() or None

        catalog_data = DEVICE_CATALOG.get(device_type, {})
        catalog_makes = list(catalog_data.keys())

        try:
            db_makes = self.db.list_makes(device_type=device_type)
        except Exception:
            db_makes = []

        all_makes_dict = {m.casefold(): m for m in catalog_makes + db_makes if m.strip()}
        all_makes = sorted(all_makes_dict.values(), key=lambda x: x.casefold())

        self._action_makes_all = all_makes
        self.make_combo.configure(values=[""] + all_makes)

        if current_make and current_make.casefold() not in all_makes_dict:
            # allow custom makes by not strictly clearing, just keep what they typed
            pass

        if (not current_make) and len(all_makes) == 1:
            current_make = all_makes[0]
            self.make_var.set(current_make)

        try:
            # We pass current_make to db.list_models to only get models for that exact Make from DB
            db_models = self.db.list_models(device_type=device_type, make=current_make)
        except Exception:
            db_models = []

        catalog_models = []
        if current_make:
            for cat_make, models in catalog_data.items():
                if cat_make.casefold() == current_make.casefold():
                    catalog_models.extend(models)
        else:
            for models in catalog_data.values():
                catalog_models.extend(models)

        all_models_dict = {m.casefold(): m for m in catalog_models + db_models if m.strip()}
        all_models = sorted(all_models_dict.values(), key=lambda x: x.casefold())

        self._action_models_all = all_models
        self.model_combo.configure(values=[""] + all_models)
        if not preserve_typed_model:
            self.model_var.set("")

    def _on_serial_scanned(self, _event: tk.Event | None = None) -> None:
        """Called automatically when the barcode scanner presses 'Enter' in the Serial field."""
        raw_scan = self.serial_var.get().strip()
        if not raw_scan:
            return

        # Parse scanner and laptop QR payloads into one canonical serial token.
        serial_token = extract_preferred_serial(raw_scan, mode="scanner")

        if not serial_token:
            self._write_result({"ok": False, "error": "Invalid serial barcode format"}, ok=False)
            return

        normalized_serial = normalize_for_store(serial_token)
        self.serial_var.set(normalized_serial)

        # 1. Check if device exists in DB (support both with and without S prefix)
        existing: Device | None = None
        lookup_candidates = [normalized_serial]
        if serial_token != normalized_serial:
            lookup_candidates.append(serial_token)

        for cand in lookup_candidates:
            try:
                existing = self.db.get_device(cand)
            except Exception:
                existing = None
            if existing:
                break

        if existing:
            self._fill_action_form(existing)
            self.serial_var.set(existing.serial)
            self._selected_serial = existing.serial
            self._selected_updated_at = existing.updated_at
            self._selected_created_at = existing.created_at
            self._write_result({"ok": True, "info": self.tr("desktop_scan_info_loaded")})
            self._show_scan_result_popup(self.tr("desktop_scan_found_db"))
            return

        upper_scan = normalized_serial.upper()

        # 2. Smart learning from existing serial prefixes (variable length)
        try:
            all_devs = self.db.list_devices()

            def _serial_family_and_comparable(value: str | None) -> tuple[str, str] | None:
                token = (value or "").strip().upper()
                if re.fullmatch(r"S\d{13,14}", token):
                    return ("scanner", token[1:])
                if re.fullmatch(r"\d{13,14}", token):
                    return ("scanner", token)
                if re.fullmatch(r"[A-Z0-9]{8,20}", token):
                    return ("generic", token)
                return None

            scan_info = _serial_family_and_comparable(normalized_serial)
            if scan_info:
                scan_family, scan_cmp = scan_info
                min_len = 2 if scan_family == "scanner" else 3
                max_len = min(len(scan_cmp), 6 if scan_family == "scanner" else 7)

                learned_rows: list[tuple[str, Device]] = []
                for dev in all_devs:
                    if not dev.model:
                        continue
                    dev_info = _serial_family_and_comparable(dev.serial)
                    if not dev_info or dev_info[0] != scan_family:
                        continue
                    learned_rows.append((dev_info[1], dev))

                from collections import Counter

                for p_len in range(max_len, min_len - 1, -1):
                    prefix = scan_cmp[:p_len]
                    matches = [dev for cmp_value, dev in learned_rows if cmp_value.startswith(prefix)]
                    if not matches:
                        continue

                    model_counts = Counter(
                        [f"{(m.device_type or 'scanner')}||{m.model}" for m in matches if m.model]
                    )
                    if not model_counts:
                        continue

                    top_two = model_counts.most_common(2)
                    best_key, best_count = top_two[0]
                    second_count = top_two[1][1] if len(top_two) > 1 else 0
                    total = sum(model_counts.values())
                    confidence = (best_count / total) if total else 0
                    clear_winner = (
                        len(model_counts) == 1
                        or confidence >= 0.7
                        or (best_count >= 3 and (best_count - second_count) >= 2)
                    )
                    if not clear_winner:
                        continue

                    guessed_device = next(
                        (
                            m
                            for m in matches
                            if f"{(m.device_type or 'scanner')}||{m.model}" == best_key
                        ),
                        None,
                    )
                    if guessed_device:
                        self._fill_action_form(guessed_device)
                        self.serial_var.set(normalized_serial)
                        self._selected_serial = normalized_serial
                        self._selected_updated_at = None
                        self._selected_created_at = None
                        self._refresh_warranty_comment_preview(
                            serial=normalized_serial,
                            device_type=guessed_device.device_type or "scanner",
                            created_at=None,
                        )
                        self.overwrite_var.set(False)
                        self._write_result(
                            {
                                "ok": True,
                                "info": self.tr("desktop_scan_info_history", prefix=prefix),
                            }
                        )
                        self._show_scan_result_popup(
                            self.tr("desktop_scan_not_found_history"),
                            allow_register=True,
                            serial=normalized_serial,
                        )
                        return
        except Exception:
            pass

        # 3. Prefix rules fallback
        # Longest prefix wins so specific rules (e.g. 5CG21) beat generic ones (e.g. 5CG).
        for prefix, (guess_type, guess_make, guess_model) in sorted(
            self._get_prefix_rules().items(),
            key=lambda item: len(item[0]),
            reverse=True,
        ):
            if upper_scan.startswith(prefix.upper()):
                self.type_var.set(self._display_from_code(guess_type, "type"))
                self._on_action_type_changed()
                self.make_var.set(guess_make)
                self._on_action_make_changed()
                self.model_var.set(guess_model.replace(guess_make + " ", "", 1))
                self._selected_created_at = None
                self._refresh_warranty_comment_preview(
                    serial=normalized_serial,
                    device_type=guess_type,
                    created_at=None,
                )
                self.overwrite_var.set(False)
                self._write_result(
                    {
                        "ok": True,
                        "info": self.tr(
                            "desktop_scan_info_prefix",
                            model_desc=f"{guess_make} {guess_model}",
                            prefix=prefix,
                        ),
                    }
                )
                self._show_scan_result_popup(
                    self.tr("desktop_scan_not_found_prefix"),
                    allow_register=True,
                    serial=normalized_serial,
                )
                return

        # Keep serial ready for manual entry when no rule matched.
        self._selected_serial = normalized_serial
        self._selected_updated_at = None
        self._selected_created_at = None
        self._refresh_warranty_comment_preview(serial=normalized_serial, created_at=None)
        self.overwrite_var.set(False)
        self._write_result({"ok": True, "info": self.tr("desktop_scan_info_not_found")})
        self._show_scan_result_popup(
            self.tr("desktop_scan_not_found"),
            allow_register=True,
            serial=normalized_serial,
        )

    def _prepare_manual_registration(self, serial: str | None = None) -> None:
        normalized = (serial or self.serial_var.get() or "").strip()
        if normalized:
            self.serial_var.set(normalized)
        self._selected_serial = normalized or None
        self._selected_updated_at = None
        self._selected_created_at = None
        self._refresh_warranty_comment_preview(serial=normalized, created_at=None)
        self.overwrite_var.set(False)
        self._write_result({"ok": True, "info": self.tr("desktop_scan_register_status")})
        try:
            self.make_combo.focus_set()
        except Exception:
            try:
                self.model_combo.focus_set()
            except Exception:
                pass

    def _show_scan_result_popup(self, message: str, *, allow_register: bool = False, serial: str | None = None) -> None:
        win = tk.Toplevel(self.root)
        win.title(self.tr("desktop_scan_popup_title"))
        win.geometry("520x220")
        win.minsize(460, 190)
        win.transient(self.root)
        win.grab_set()

        frm = ttk.Frame(win, padding=14)
        frm.pack(fill=tk.BOTH, expand=True)
        frm.columnconfigure(0, weight=1)

        ttk.Label(frm, text=self.tr("desktop_scan_popup_title"), style="Section.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(frm, text=message, wraplength=470, justify="left").grid(row=1, column=0, sticky="w", pady=(10, 0))

        btns = ttk.Frame(frm)
        btns.grid(row=2, column=0, sticky="e", pady=(14, 0))

        if allow_register:
            ttk.Button(
                btns,
                text=self.tr("desktop_register_new_device"),
                style="Primary.TButton",
                command=lambda: (self._prepare_manual_registration(serial), win.destroy()),
            ).grid(row=0, column=0, padx=(0, 8))

        ttk.Button(btns, text=self.tr("desktop_close"), style="Secondary.TButton", command=win.destroy).grid(row=0, column=1)

    def _fill_action_form(self, device: Device) -> None:
        """Helper to fill the Action section fields nicely from a DB record."""
        # Type
        disp_type = self._display_from_code(device.device_type, "type")
        self.type_var.set(disp_type)
        self._on_action_type_changed()

        # Try to guess 'Make' from the stored Model
        make = ""
        model_text = device.model or ""
        # The database code gets Make by splitting at the first space
        if model_text and " " in model_text:
            parts = model_text.split(" ", 1)
            make = parts[0]
            model_text = parts[1]
            # Verify if it makes sense based on catalog
            if make in getattr(self, "DEVICE_CATALOG", {}).get(device.device_type, {}):
                pass
            else:
                # Fallback slightly:
                make = parts[0]
        elif model_text:
            make = model_text 

        self.make_var.set(make)
        self._on_action_make_changed()
        
        # We need to set the remainder into Model
        self.model_var.set(model_text)

        self.from_store_var.set(device.from_store or "")
        self.to_store_var.set(device.to_store or "")
        self.status_var.set(self._display_from_code(device.status, "status"))
        self.comment_var.set(
            self._comment_with_warranty_preview(
                device.comment,
                serial=device.serial,
                device_type=device.device_type or "other",
                created_at=device.created_at,
            )
        )
        self._selected_serial = device.serial
        self._selected_updated_at = device.updated_at
        self._selected_created_at = device.created_at
        self.overwrite_var.set(True) # Ready for update

    def _on_action_type_changed(self, _event: tk.Event | None = None) -> None:  # type: ignore[override]
        self.make_var.set("")
        self.model_var.set("")
        self._refresh_action_make_model_values(preserve_typed_model=True)
        self._refresh_warranty_comment_preview()

    def _on_action_make_changed(self, _event: tk.Event | None = None) -> None:  # type: ignore[override]
        self.model_var.set("")
        self._refresh_action_make_model_values(preserve_typed_model=True)

    def _on_action_make_typed(self, _event: tk.Event | None = None) -> None:  # type: ignore[override]
        typed = self.make_var.get().strip()
        if not getattr(self, "_action_makes_all", None):
            self._refresh_action_make_model_values(preserve_typed_model=True)
            
        if not typed:
            self.make_combo.configure(values=[""] + getattr(self, "_action_makes_all", []))
            self.model_var.set("")
            self._refresh_action_make_model_values(preserve_typed_model=True)
            return

        t_low = typed.casefold()
        filtered = [m for m in getattr(self, "_action_makes_all", []) if t_low in m.casefold()]
        self.make_combo.configure(values=[""] + filtered)
        # We also refresh models to reflect the partial or completed Make type
        self._refresh_action_make_model_values(preserve_typed_model=True)

    def _on_action_model_typed(self, _event: tk.Event | None = None) -> None:  # type: ignore[override]
        typed = self.model_var.get().strip()
        if not self._action_models_all:
            self._refresh_action_make_model_values(preserve_typed_model=True)

        if not typed:
            self.model_combo.configure(values=[""] + (self._action_models_all or []))
            return

        t_low = typed.casefold()
        filtered = [m for m in (self._action_models_all or []) if t_low in m.casefold()]
        self.model_combo.configure(values=[""] + filtered)

    def _normalize_code(self, value: str | None, *, kind: str) -> str:
        raw = (value or "").strip()
        if not raw:
            return ""

        code = (self._code_from_display(raw, kind=kind) or "").strip()

        if kind == "status":
            up = code.upper()
            return up if up in ALLOWED_STATUSES else code
        if kind == "type":
            low = code.lower()
            return low if low in DEVICE_TYPES else code
        return code

    # ---------- UI ----------

    def _build_ui(self) -> None:
        self.root.title("programma_rb")
        self.root.geometry("1200x720")
        self.root.minsize(1050, 640)

        self._style()

        self._setup_branding_assets()

        # --- Top header (red bar like reference) ---
        # Darker base red so the red logo stays visible without any white box.
        self._header_bg = "#8a0000"
        self._header_bg_hi = "#d50000"
        self._header_shadow = "#5a0000"

        self.header_outer = tk.Frame(self.root, bg=self._header_bg)
        self.header_outer.pack(fill=tk.X, side=tk.TOP)

        self.header_highlight = tk.Frame(self.header_outer, bg=self._header_bg_hi, height=3)
        self.header_highlight.pack(fill=tk.X, side=tk.TOP)

        self.header_main = tk.Frame(self.header_outer, bg=self._header_bg)
        self.header_main.pack(fill=tk.X, side=tk.TOP)

        self.header_shadow_line = tk.Frame(self.header_outer, bg=self._header_shadow, height=2)
        self.header_shadow_line.pack(fill=tk.X, side=tk.TOP)

        left = tk.Frame(self.header_main, bg=self._header_bg)
        left.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=16, pady=10)

        # Logo directly on the header (no white border/frame)
        self.logo_lbl = tk.Label(left, text="", bg=self._header_bg, fg="#ffffff")
        self.logo_lbl.pack(side=tk.LEFT)

        title_wrap = tk.Frame(left, bg=self._header_bg)
        title_wrap.pack(side=tk.LEFT, padx=(14, 0), anchor="w")

        self.title_lbl = tk.Label(
            title_wrap,
            text="programma_rb",
            bg=self._header_bg,
            fg="#ffffff",
            font=("Segoe UI", 14, "bold"),
        )
        self.title_lbl.pack(anchor="w")

        self.subtitle_lbl = tk.Label(
            title_wrap,
            text="",
            bg=self._header_bg,
            fg="#ffecec",
            font=("Segoe UI", 9),
        )
        self.subtitle_lbl.pack(anchor="w", pady=(2, 0))

        right = tk.Frame(self.header_main, bg=self._header_bg)
        right.pack(side=tk.RIGHT, padx=16, pady=10)

        self.lang_var = tk.StringVar(value=self.lang)
        self.lang_combo = ttk.Combobox(
            right,
            textvariable=self.lang_var,
            values=["lv", "en"],
            width=6,
            state="readonly",
            style="Top.TCombobox",
        )
        self.lang_combo.pack(side=tk.RIGHT)
        self.lang_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_lang_changed())

        self.theme_btn = ttk.Button(right, command=self.toggle_theme, style="Top.TButton")
        self.theme_btn.pack(side=tk.RIGHT, padx=(0, 10))

        self.admin_btn = ttk.Button(right, command=self._toggle_admin_session, style="Top.TButton")
        self.admin_btn.pack(side=tk.RIGHT, padx=(0, 10))

        self.settings_btn = ttk.Button(right, command=self._open_settings_dialog, style="Top.TButton")
        self.settings_btn.pack(side=tk.RIGHT, padx=(0, 10))

        body = ttk.Frame(self.root, padding=14, style="Body.TFrame")
        body.pack(fill=tk.BOTH, expand=True)

        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        # Left: form
        self.form_card = ttk.Frame(body, padding=14, style="Card.TFrame", relief="solid", borderwidth=1)
        self.form_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.form_card.columnconfigure(0, weight=1)

        self.actions_title = ttk.Label(self.form_card, text="", style="Section.TLabel")
        self.actions_title.grid(row=0, column=0, sticky="w")

        form = ttk.Frame(self.form_card, style="Card.TFrame")
        form.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)

        self.serial_var = tk.StringVar()
        self.type_var = tk.StringVar(value="scanner")
        self.make_var = tk.StringVar()
        self.model_var = tk.StringVar()
        self.from_store_var = tk.StringVar()
        self.to_store_var = tk.StringVar()
        self.status_var = tk.StringVar(value="RECEIVED")
        self.comment_var = tk.StringVar()
        self.overwrite_var = tk.BooleanVar(value=False)
        self.bulk_scan_var = tk.BooleanVar(value=False)

        self.serial_entry = self._field(form, 0, 0, "web_serial", self.serial_var)
        self.serial_entry.bind("<Return>", self._on_serial_scanned)

        self.type_lbl = ttk.Label(form, text="", style="Label.TLabel")
        self.type_lbl.grid(row=0, column=1, sticky="w")
        self.type_combo = ttk.Combobox(
            form,
            textvariable=self.type_var,
            state="readonly",
            style="App.TCombobox",
        )
        self.type_combo.grid(row=1, column=1, sticky="ew", padx=(8, 0))

        self.make_lbl = ttk.Label(form, text="", style="Label.TLabel")
        self.make_lbl.grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.make_combo = ttk.Combobox(
            form,
            textvariable=self.make_var,
            state="normal",
            style="App.TCombobox",
        )
        self.make_combo.grid(row=3, column=0, sticky="ew")

        self.model_lbl = ttk.Label(form, text="", style="Label.TLabel")
        self.model_lbl.grid(row=4, column=0, sticky="w", pady=(8, 0))
        self.model_combo = ttk.Combobox(
            form,
            textvariable=self.model_var,
            state="normal",
            style="App.TCombobox",
        )
        self.model_combo.grid(row=5, column=0, sticky="ew")

        self.status_lbl = ttk.Label(form, text="", style="Label.TLabel")
        self.status_lbl.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
        self.status_combo = ttk.Combobox(
            form,
            textvariable=self.status_var,
            state="readonly",
            style="App.TCombobox",
        )
        self.status_combo.grid(row=3, column=1, sticky="ew", padx=(8, 0))

        self._field(form, 6, 0, "web_from_store", self.from_store_var)
        self._field(form, 6, 1, "web_to_store", self.to_store_var, padx_left=8)

        self.comment_lbl = ttk.Label(form, text="", style="Label.TLabel")
        self.comment_lbl.grid(row=8, column=0, sticky="w", pady=(8, 0))
        self.comment_entry = ttk.Entry(form, textvariable=self.comment_var, style="App.TEntry")
        self.comment_entry.grid(row=9, column=0, columnspan=2, sticky="ew")

        self._action_models_all: list[str] = []

        try:
            self.type_combo.bind("<<ComboboxSelected>>", self._on_action_type_changed)
        except Exception:
            pass

        try:
            self.make_combo.bind("<<ComboboxSelected>>", self._on_action_make_changed)
            self.make_combo.bind("<KeyRelease>", self._on_action_make_typed)
        except Exception:
            pass

        try:
            self.model_combo.bind("<KeyRelease>", self._on_action_model_typed)
        except Exception:
            pass

        self.overwrite_chk = ttk.Checkbutton(self.form_card, variable=self.overwrite_var, style="App.TCheckbutton")
        self.overwrite_chk.grid(row=2, column=0, sticky="w", pady=(10, 0))

        self.bulk_scan_chk = ttk.Checkbutton(
            self.form_card,
            variable=self.bulk_scan_var,
            command=self._on_bulk_scan_toggle,
            style="App.TCheckbutton",
        )
        self.bulk_scan_chk.grid(row=2, column=0, sticky="e", pady=(10, 0))

        btns = ttk.Frame(self.form_card, style="Card.TFrame")
        btns.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        btns.columnconfigure(0, weight=1)
        btns.columnconfigure(1, weight=1)

        self.add_btn = ttk.Button(btns, command=self.add_device, style="Primary.TButton")
        self.add_btn.grid(row=0, column=0, sticky="ew")

        self.clear_form_btn = ttk.Button(btns, command=self.clear_form, style="Secondary.TButton")
        self.clear_form_btn.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        self.sync_btn = ttk.Button(btns, command=self._sync_now, style="Secondary.TButton")
        self.sync_btn.grid(row=1, column=0, sticky="ew", pady=(8, 0))

        self.camera_btn = ttk.Button(btns, command=self._camera_scan, style="Secondary.TButton")
        self.camera_btn.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        self.warranty_btn = ttk.Button(btns, command=self.check_warranty_from_web_checker, style="Secondary.TButton")
        self.warranty_btn.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        self.audit_btn = ttk.Button(btns, command=self._open_audit_viewer, style="Secondary.TButton")
        self.audit_btn.grid(row=3, column=0, sticky="ew", pady=(8, 0))

        self.diag_btn = ttk.Button(btns, command=self._open_diagnostics_panel, style="Secondary.TButton")
        self.diag_btn.grid(row=3, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))

        self.prefix_btn = ttk.Button(btns, command=self._open_prefix_rules_admin, style="Secondary.TButton")
        self.prefix_btn.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(8, 0))


        self.result_lbl = ttk.Label(self.form_card, text="", style="Muted.TLabel")
        self.result_lbl.grid(row=5, column=0, sticky="w", pady=(10, 0))

        self.result_txt = tk.Text(
            self.form_card,
            height=8,
            wrap="word",
            relief="solid",
            borderwidth=1,
        )
        self.result_txt.grid(row=6, column=0, sticky="nsew", pady=(6, 0))
        self.form_card.rowconfigure(6, weight=1)

        # Right: list + filters
        self.list_card = ttk.Frame(body, padding=14, style="Card.TFrame", relief="solid", borderwidth=1)
        self.list_card.grid(row=0, column=1, sticky="nsew")
        self.list_card.columnconfigure(0, weight=1)
        self.list_card.rowconfigure(2, weight=1)

        list_header = ttk.Frame(self.list_card, style="Card.TFrame")
        list_header.grid(row=0, column=0, sticky="ew")
        list_header.columnconfigure(0, weight=1)

        self.list_title = ttk.Label(list_header, text="", style="Section.TLabel")
        self.list_title.grid(row=0, column=0, sticky="w")

        self.double_click_hint = ttk.Label(list_header, text="", style="Muted.TLabel")
        self.double_click_hint.grid(row=0, column=1, sticky="e")

        self.clear_filters_btn = ttk.Button(list_header, command=self.clear_filters, style="Secondary.TButton")
        self.clear_filters_btn.grid(row=0, column=2, sticky="e", padx=(10, 0))

        filters = ttk.Frame(self.list_card, style="Card.TFrame")
        filters.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        for c in range(8):
            filters.columnconfigure(c, weight=1)

        self.filter_status_var = tk.StringVar(value="")
        self.filter_type_var = tk.StringVar(value="")
        self.filter_make_var = tk.StringVar(value="")
        self.filter_serial_var = tk.StringVar(value="")
        self.filter_model_var = tk.StringVar(value="")
        self.filter_from_var = tk.StringVar(value="")
        self.filter_to_var = tk.StringVar(value="")
        self.limit_var = tk.StringVar(value="200")

        self.filter_status_lbl = ttk.Label(filters, text="", style="Label.TLabel")
        self.filter_status_lbl.grid(row=0, column=0, sticky="w")
        self.filter_status_combo = ttk.Combobox(
            filters,
            textvariable=self.filter_status_var,
            state="readonly",
            style="App.TCombobox",
        )
        self.filter_status_combo.grid(row=1, column=0, sticky="ew")

        self.filter_type_lbl = ttk.Label(filters, text="", style="Label.TLabel")
        self.filter_type_lbl.grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.filter_type_combo = ttk.Combobox(
            filters,
            textvariable=self.filter_type_var,
            state="readonly",
            style="App.TCombobox",
        )
        self.filter_type_combo.grid(row=1, column=1, sticky="ew", padx=(8, 0))

        self.filter_make_lbl = ttk.Label(filters, text="", style="Label.TLabel")
        self.filter_make_lbl.grid(row=0, column=2, sticky="w", padx=(8, 0))
        self.filter_make_combo = ttk.Combobox(
            filters,
            textvariable=self.filter_make_var,
            state="normal",
            style="App.TCombobox",
        )
        self.filter_make_combo.grid(row=1, column=2, sticky="ew", padx=(8, 0))

        self.filter_model_lbl = ttk.Label(filters, text="", style="Label.TLabel")
        self.filter_model_lbl.grid(row=0, column=3, sticky="w", padx=(8, 0))
        self.filter_model_combo = ttk.Combobox(
            filters,
            textvariable=self.filter_model_var,
            state="normal",
            style="App.TCombobox",
        )
        self.filter_model_combo.grid(row=1, column=3, sticky="ew", padx=(8, 0))

        self.filter_serial_lbl = ttk.Label(filters, text="", style="Label.TLabel")
        self.filter_serial_lbl.grid(row=0, column=4, sticky="w", padx=(8, 0))
        self.filter_serial_entry = ttk.Entry(filters, textvariable=self.filter_serial_var, style="App.TEntry")
        self.filter_serial_entry.grid(row=1, column=4, sticky="ew", padx=(8, 0))

        self.filter_from_lbl = ttk.Label(filters, text="", style="Label.TLabel")
        self.filter_from_lbl.grid(row=0, column=5, sticky="w", padx=(8, 0))
        self.filter_from_entry = ttk.Entry(filters, textvariable=self.filter_from_var, style="App.TEntry")
        self.filter_from_entry.grid(row=1, column=5, sticky="ew", padx=(8, 0))

        self.filter_to_lbl = ttk.Label(filters, text="", style="Label.TLabel")
        self.filter_to_lbl.grid(row=0, column=6, sticky="w", padx=(8, 0))
        self.filter_to_entry = ttk.Entry(filters, textvariable=self.filter_to_var, style="App.TEntry")
        self.filter_to_entry.grid(row=1, column=6, sticky="ew", padx=(8, 0))

        self.limit_lbl = ttk.Label(filters, text="", style="Label.TLabel")
        self.limit_lbl.grid(row=0, column=7, sticky="w", padx=(8, 0))
        self.limit_entry = ttk.Entry(filters, textvariable=self.limit_var, style="App.TEntry")
        self.limit_entry.grid(row=1, column=7, sticky="ew", padx=(8, 0))

        # Dependent dropdown values for Make/Model suggestions
        self._filter_models_all: list[str] = []

        # Treeview
        cols = ("serial", "type", "model", "from", "to", "status", "updated")
        self.tree = ttk.Treeview(self.list_card, columns=cols, show="headings", selectmode="browse")
        self.tree.grid(row=2, column=0, sticky="nsew", pady=(10, 0))

        self.tree.heading("serial", text="serial")
        self.tree.heading("type", text="type")
        self.tree.heading("model", text="model")
        self.tree.heading("from", text="from")
        self.tree.heading("to", text="to")
        self.tree.heading("status", text="status")
        self.tree.heading("updated", text="updated")

        # Click headings to sort
        for col in ("serial", "type", "model", "from", "to", "status", "updated"):
            self.tree.heading(col, command=lambda c=col: self._on_sort_column(c))

        self.tree.column("serial", width=140, anchor="w")
        self.tree.column("type", width=120, anchor="w")
        self.tree.column("model", width=180, anchor="w")
        self.tree.column("from", width=100, anchor="w")
        self.tree.column("to", width=100, anchor="w")
        self.tree.column("status", width=110, anchor="w")
        self.tree.column("updated", width=170, anchor="w")

        vsb = ttk.Scrollbar(self.list_card, orient="vertical", command=self.tree.yview)
        vsb.grid(row=2, column=1, sticky="ns", pady=(10, 0))
        self.tree.configure(yscrollcommand=vsb.set)

        self.count_lbl = ttk.Label(self.list_card, text="", style="Muted.TLabel")
        self.count_lbl.grid(row=3, column=0, sticky="w", pady=(8, 0))

        # Events
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._on_row_selected())
        self.tree.bind("<Double-1>", self._on_tree_double_click)

        self._build_context_menu()

        # Auto-refresh on filter changes
        self._bind_filter_auto_refresh()

        # Ensure non-ttk widgets match current theme (Result background etc.)
        self._apply_non_ttk_theme()

    def _build_context_menu(self) -> None:
        self.menu = tk.Menu(self.root, tearoff=False)
        self.menu.add_command(label=self.tr("web_edit"), command=self._on_row_double_click)

        self.status_menu = tk.Menu(self.menu, tearoff=False)
        for s in sorted(ALLOWED_STATUSES):
            disp = self._display_value(s, kind="status")
            self.status_menu.add_command(label=disp, command=lambda st=s: self._set_status_from_menu(st))

        self.menu.add_cascade(label=self.tr("web_status_inline"), menu=self.status_menu)
        self.menu.add_separator()
        self.menu.add_command(
            label=self.tr("web_delete_short"),
            command=self.delete_selected,
            state="normal" if self._admin_login_active else "disabled",
        )

        self.tree.bind("<Button-3>", self._on_right_click)

    def _on_right_click(self, event: tk.Event) -> None:  # type: ignore[override]
        row_id = self.tree.identify_row(event.y)
        if row_id:
            self.tree.selection_set(row_id)
            self._on_row_selected()
            try:
                self.menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.menu.grab_release()

    def _set_status_from_menu(self, new_status: str) -> None:
        if not self._selected_serial:
            return
        self.status_var.set(self._display_value(new_status, kind="status"))
        self.change_status()

    def _style(self) -> None:
        style = ttk.Style(self.root)
        self._apply_theme(style)

    def _apply_theme(self, style: ttk.Style) -> None:
        """Apply light/dark theme with high contrast (readable buttons)."""

        theme = (self.theme or "light").lower()
        brand_red = "#d50000"

        # Use a fully-styleable ttk theme for BOTH modes.
        # Native Windows themes often ignore custom colors -> unreadable buttons.
        try:
            style.theme_use("clam")
        except Exception:
            pass

        if theme == "dark":
            bg = "#0f1216"
            card_bg = "#171b21"
            text = "#e8eaed"
            muted = "#a5aab3"
            border = "#2a2f39"
            entry_bg = "#11151a"
            tree_sel = "#232a35"
            header_btn_bg = "#202632"
            header_btn_hover = "#2a3342"
            header_btn_fg = "#ffffff"
            secondary_bg = "#202632"
            secondary_hover = "#2a3342"
            secondary_fg = "#ffffff"
        else:
            bg = "#f5f6f8"
            card_bg = "#ffffff"
            text = "#111111"
            muted = "#6b7280"
            border = "#e5e7eb"
            entry_bg = "#ffffff"
            tree_sel = "#fff5f5"
            header_btn_bg = "#ffffff"
            header_btn_hover = "#fff5f5"
            header_btn_fg = brand_red
            secondary_bg = "#ffffff"
            secondary_hover = "#fff5f5"
            secondary_fg = text

        self.root.configure(bg=bg)

        # Defaults for any widget not using our explicit styles
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=card_bg, foreground=text)

        style.configure("Header.TFrame", background=card_bg)
        style.configure("HeaderTitle.TLabel", font=("Segoe UI", 16, "bold"), background=card_bg, foreground=brand_red)
        style.configure("HeaderSub.TLabel", font=("Segoe UI", 10), background=card_bg, foreground=muted)
        style.configure("HeaderLogo.TLabel", background=card_bg)

        # Top red header widgets (always readable)
        top_btn_bg = "#8a0000"
        top_btn_hover = "#a10000"
        style.configure("Top.TButton", font=("Segoe UI", 9, "bold"), padding=(10, 7))
        style.map(
            "Top.TButton",
            background=[("pressed", top_btn_hover), ("active", top_btn_hover), ("!disabled", top_btn_bg)],
            foreground=[("pressed", "#ffffff"), ("active", "#ffffff"), ("!disabled", "#ffffff")],
        )
        style.configure(
            "Top.TCombobox",
            padding=(8, 6),
            font=("Segoe UI", 10),
            fieldbackground=top_btn_bg,
            background=top_btn_bg,
            foreground="#ffffff",
            arrowcolor="#ffffff",
        )
        style.map(
            "Top.TCombobox",
            fieldbackground=[("readonly", top_btn_bg), ("!readonly", top_btn_bg), ("disabled", top_btn_bg)],
            foreground=[("readonly", "#ffffff"), ("!readonly", "#ffffff"), ("disabled", "#ffffff")],
            background=[("readonly", top_btn_bg), ("!readonly", top_btn_bg)],
            selectbackground=[("readonly", top_btn_bg), ("!readonly", top_btn_bg)],
            selectforeground=[("readonly", "#ffffff"), ("!readonly", "#ffffff")],
        )

        style.configure("Body.TFrame", background=bg)

        style.configure("Section.TLabel", font=("Segoe UI", 11, "bold"), background=card_bg, foreground=text)
        style.configure("Muted.TLabel", font=("Segoe UI", 9), background=card_bg, foreground=muted)
        style.configure("Label.TLabel", font=("Segoe UI", 9), background=card_bg, foreground=text)

        style.configure("Card.TFrame", background=card_bg)

        style.configure("TCheckbutton", background=card_bg, foreground=text)
        style.map(
            "TCheckbutton",
            background=[("pressed", card_bg), ("active", card_bg), ("!disabled", card_bg)],
            foreground=[("pressed", text), ("active", text), ("!disabled", text), ("disabled", muted)],
        )

        style.configure("App.TCheckbutton", background=card_bg, foreground=text)
        style.map(
            "App.TCheckbutton",
            background=[("pressed", card_bg), ("active", card_bg), ("!disabled", card_bg)],
            foreground=[("pressed", text), ("active", text), ("!disabled", text), ("disabled", muted)],
        )

        # Inputs
        style.configure("App.TEntry", padding=(10, 8), font=("Segoe UI", 10), fieldbackground=entry_bg, foreground=text)
        style.map(
            "App.TEntry",
            fieldbackground=[("!disabled", entry_bg), ("disabled", card_bg)],
            foreground=[("!disabled", text), ("disabled", muted)],
        )

        style.configure(
            "App.TCombobox",
            padding=(8, 6),
            font=("Segoe UI", 10),
            fieldbackground=entry_bg,
            background=entry_bg,
            foreground=text,
            arrowcolor=text,
        )
        # Readonly combobox uses a special state; map colors explicitly.
        style.map(
            "App.TCombobox",
            fieldbackground=[
                ("readonly", entry_bg),
                ("!readonly", entry_bg),
                ("active", entry_bg),
                ("focus", entry_bg),
                ("disabled", card_bg),
            ],
            foreground=[
                ("readonly", text),
                ("!readonly", text),
                ("active", text),
                ("focus", text),
                ("disabled", muted),
            ],
            background=[("readonly", entry_bg), ("!readonly", entry_bg), ("active", entry_bg), ("focus", entry_bg)],
            selectbackground=[("readonly", entry_bg), ("!readonly", entry_bg), ("active", entry_bg), ("focus", entry_bg)],
            selectforeground=[("readonly", text), ("!readonly", text), ("active", text), ("focus", text)],
            arrowcolor=[("readonly", text), ("!readonly", text), ("active", text), ("focus", text), ("disabled", muted)],
        )

        # Keep default class styles aligned too (some widgets might not be updated)
        style.configure("TEntry", padding=(10, 8), font=("Segoe UI", 10), fieldbackground=entry_bg, foreground=text)
        style.map(
            "TEntry",
            fieldbackground=[("!disabled", entry_bg), ("disabled", card_bg)],
            foreground=[("!disabled", text), ("disabled", muted)],
        )
        style.configure(
            "TCombobox",
            padding=(8, 6),
            font=("Segoe UI", 10),
            fieldbackground=entry_bg,
            background=entry_bg,
            foreground=text,
            arrowcolor=text,
        )
        style.map(
            "TCombobox",
            fieldbackground=[
                ("readonly", entry_bg),
                ("!readonly", entry_bg),
                ("active", entry_bg),
                ("focus", entry_bg),
                ("disabled", card_bg),
            ],
            foreground=[
                ("readonly", text),
                ("!readonly", text),
                ("active", text),
                ("focus", text),
                ("disabled", muted),
            ],
            background=[("readonly", entry_bg), ("!readonly", entry_bg), ("active", entry_bg), ("focus", entry_bg)],
            selectbackground=[("readonly", entry_bg), ("!readonly", entry_bg), ("active", entry_bg), ("focus", entry_bg)],
            selectforeground=[("readonly", text), ("!readonly", text), ("active", text), ("focus", text)],
            arrowcolor=[("readonly", text), ("!readonly", text), ("active", text), ("focus", text), ("disabled", muted)],
        )

        # Combobox dropdown list colors (Listbox is a tk widget)
        try:
            # Use high priority so switching themes updates existing option patterns.
            prio = 80
            self.root.option_add("*TCombobox*Listbox.background", entry_bg, prio)
            self.root.option_add("*TCombobox*Listbox.foreground", text, prio)
            self.root.option_add("*TCombobox*Listbox.selectBackground", tree_sel, prio)
            self.root.option_add("*TCombobox*Listbox.selectForeground", text, prio)
            # Hover (active) item in dropdown
            self.root.option_add("*TCombobox*Listbox.activeBackground", tree_sel, prio)
            self.root.option_add("*TCombobox*Listbox.activeForeground", text, prio)
        except Exception:
            pass

        # Table
        style.configure(
            "Treeview",
            font=("Segoe UI", 9),
            rowheight=30,
            background=card_bg,
            fieldbackground=card_bg,
            foreground=text,
            borderwidth=0,
        )
        style.map(
            "Treeview",
            background=[("selected", tree_sel)],
            foreground=[("selected", text)],
        )
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 9, "bold"),
            background=card_bg,
            foreground=text,
            relief="flat",
        )
        style.map(
            "Treeview.Heading",
            background=[("pressed", card_bg), ("active", card_bg)],
            foreground=[("pressed", text), ("active", text)],
        )

        # Header buttons (refresh/theme)
        style.configure("Header.TButton", font=("Segoe UI", 9, "bold"), padding=(10, 7))
        style.map(
            "Header.TButton",
            background=[("pressed", header_btn_hover), ("active", header_btn_hover), ("!disabled", header_btn_bg)],
            foreground=[("pressed", header_btn_fg), ("active", header_btn_fg), ("!disabled", header_btn_fg)],
        )

        # Default buttons (fallback) - keep readable on hover
        style.configure("TButton", font=("Segoe UI", 10), padding=(10, 8))
        style.map(
            "TButton",
            background=[("pressed", secondary_hover), ("active", secondary_hover), ("!disabled", secondary_bg)],
            foreground=[("pressed", secondary_fg), ("active", secondary_fg), ("!disabled", secondary_fg)],
        )

        # Main buttons
        style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), padding=(10, 8))
        style.map(
            "Primary.TButton",
            background=[("pressed", "#b40000"), ("active", "#b40000"), ("!disabled", brand_red)],
            foreground=[("pressed", "#ffffff"), ("active", "#ffffff"), ("!disabled", "#ffffff")],
        )

        style.configure("Secondary.TButton", font=("Segoe UI", 10), padding=(10, 8))
        style.map(
            "Secondary.TButton",
            background=[("pressed", secondary_hover), ("active", secondary_hover), ("!disabled", secondary_bg)],
            foreground=[("pressed", secondary_fg), ("active", secondary_fg), ("!disabled", secondary_fg)],
        )

        style.configure("Danger.TButton", font=("Segoe UI", 10, "bold"), padding=(10, 8))
        style.map(
            "Danger.TButton",
            background=[("pressed", "#8a0019"), ("active", "#8a0019"), ("!disabled", "#b00020")],
            foreground=[("pressed", "#ffffff"), ("active", "#ffffff"), ("!disabled", "#ffffff")],
        )

        # Non-ttk widgets
        self._apply_non_ttk_theme()

    def _apply_non_ttk_theme(self) -> None:
        """Apply theme colors to tk.* widgets (Text / header frames)."""

        theme = (self.theme or "light").lower()
        if theme == "dark":
            entry_bg = "#0b0f14"  # black-ish
            text = "#e8eaed"
            tree_sel = "#232a35"
            border = "#2a2f39"
        else:
            entry_bg = "#ffffff"
            text = "#111111"
            tree_sel = "#fff5f5"
            border = "#e5e7eb"

        # Header stays red in both modes, but keep label background aligned
        try:
            self.header_outer.configure(bg=self._header_bg)
            self.header_main.configure(bg=self._header_bg)
            self.header_highlight.configure(bg=self._header_bg_hi)
            self.header_shadow_line.configure(bg=self._header_shadow)
        except Exception:
            pass
        try:
            self.logo_lbl.configure(bg=getattr(self, "_header_bg", "#b40000"))
        except Exception:
            pass

        try:
            state = str(self.result_txt.cget("state"))
            self.result_txt.configure(state="normal")
            # Configure only options supported by tk.Text across Tk versions.
            self.result_txt.configure(
                bg=entry_bg,
                fg=text,
                insertbackground=text,
                selectbackground=tree_sel,
                selectforeground=text,
                highlightbackground=border,
                highlightcolor=border,
            )
            self.result_txt.configure(state=state)
        except Exception:
            pass

    def toggle_theme(self) -> None:
        self.theme = "dark" if (self.theme or "light") == "light" else "light"
        self._style()
        self._apply_i18n()
        self.refresh_list()
        self._refresh_open_editors_i18n()

    def _setup_branding_assets(self) -> None:
        """Loads user-provided logo/icon from ./assets.

        Note: We do not ship any Rimi Baltic logo assets.
        If you want an official logo, place it as ./assets/logo.png.
        """

        assets_dir = Path(__file__).resolve().parent / "assets"

        self._logo_img: tk.PhotoImage | None = None

        # Use red logo on white header.
        for name in (
            "logo_red.png",
            "logo_red.gif",
            "logo.png",
            "logo.gif",
            "logo_white.png",
            "logo_white.gif",
        ):
            img = _try_load_logo_image(assets_dir / name, max_w=260, max_h=64)
            if img is not None:
                self._logo_img = img
                break

        ico = assets_dir / "icon.ico"
        try:
            if ico.exists():
                self.root.iconbitmap(str(ico))
        except Exception:
            pass

    def _field(
        self,
        parent: ttk.Frame,
        row: int,
        col: int,
        label_key: str,
        var: tk.StringVar,
        *,
        padx_left: int = 0,
    ) -> ttk.Entry:
        lbl = ttk.Label(parent, text="", style="Label.TLabel")
        lbl.grid(row=row, column=col, sticky="w", pady=(8, 0), padx=(padx_left, 0))
        ent = ttk.Entry(parent, textvariable=var, style="App.TEntry")
        ent.grid(row=row + 1, column=col, sticky="ew", padx=(padx_left, 0))
        setattr(self, f"_lbl_{label_key}_{row}_{col}", lbl)
        return ent

    def _apply_i18n(self) -> None:
        self.lang = self.lang_var.get().lower()

        self._rebuild_display_maps()

        self.root.title(self.tr("app_title"))

        if self._logo_img is not None:
            self.logo_lbl.config(image=self._logo_img, text="")
            self.logo_lbl.image = self._logo_img  # keep reference
        else:
            self.logo_lbl.config(text=self.tr("desktop_brand"))

        # Header text (reference-like)
        self.title_lbl.config(text=f"{self.tr('desktop_brand')} {self.tr('desktop_brand_title')}")
        self.subtitle_lbl.config(text=self.tr("desktop_brand_subtitle"))

        self.theme_btn.config(
            text=self.tr("desktop_theme_dark") if (self.theme or "light") == "light" else self.tr("desktop_theme_bright")
        )
        if self._admin_login_active:
            self.admin_btn.config(text=self.tr("desktop_admin_logout", email=self._admin_email or "admin"))
        else:
            self.admin_btn.config(text=self.tr("desktop_admin_login"))
        self.settings_btn.config(text=self.tr("desktop_settings"))

        self.actions_title.config(text=self.tr("web_action"))
        self.list_title.config(text=self.tr("web_list"))

        # Form labels
        self._get_field_label("web_serial", 0, 0).config(text=self.tr("web_serial"))
        self.type_lbl.config(text=self.tr("web_type"))
        self.make_lbl.config(text=self.tr("web_make"))
        self.model_lbl.config(text=self.tr("web_model"))
        self.status_lbl.config(text=self.tr("web_status"))
        self._get_field_label("web_from_store", 6, 0).config(text=self.tr("web_from_store"))
        self._get_field_label("web_to_store", 6, 1).config(text=self.tr("web_to_store"))
        self.comment_lbl.config(text=self.tr("web_comment"))

        self.overwrite_chk.config(text=self.tr("web_overwrite"))
        self.bulk_scan_chk.config(text=self.tr("desktop_bulk_scan"))

        self.add_btn.config(text=self.tr("web_add"))
        self.clear_form_btn.config(text=self.tr("desktop_clear_form"))
        self.sync_btn.config(text=self.tr("desktop_sync"))
        self.camera_btn.config(text=self.tr("desktop_camera_scan"))
        self.warranty_btn.config(text=self.tr("desktop_warranty_check"))
        self.audit_btn.config(text=self.tr("desktop_audit_viewer"))
        self.diag_btn.config(text=self.tr("desktop_diagnostics"))
        self.prefix_btn.config(text=self.tr("desktop_prefix_admin"))
        # Update / Status / Delete buttons removed from Action section (use editor/context menu)

        self.result_lbl.config(text=self.tr("web_result"))

        # Filters
        self.filter_status_lbl.config(text=self.tr("web_status"))
        self.filter_type_lbl.config(text=self.tr("web_type"))
        self.filter_make_lbl.config(text=self.tr("web_make"))
        self.filter_serial_lbl.config(text=self.tr("web_serial"))
        self.filter_model_lbl.config(text=self.tr("web_model"))
        self.limit_lbl.config(text=self.tr("web_limit"))
        self.filter_from_lbl.config(text=self.tr("web_from_store"))
        self.filter_to_lbl.config(text=self.tr("web_to_store"))

        self.clear_filters_btn.config(text=self.tr("desktop_clear_filters"))

        self.double_click_hint.config(text=self.tr("desktop_double_click_hint"))

        # Dropdown values (localized display, stable code prefix)
        type_code = self._code_from_display(self.type_var.get(), kind="type") or "scanner"
        status_code = self._code_from_display(self.status_var.get(), kind="status") or "RECEIVED"

        type_values = [self._display_value(tp, kind="type") for tp in DEVICE_TYPES]
        status_values = [self._display_value(st, kind="status") for st in sorted(ALLOWED_STATUSES)]

        self.type_combo.configure(values=type_values)
        self.status_combo.configure(values=status_values)

        self.type_var.set(self._display_value(type_code, kind="type"))
        self.status_var.set(self._display_value(status_code, kind="status"))

        # Refresh action Make/Model lists (depends on selected type)
        self._refresh_action_make_model_values(preserve_typed_model=True)

        # Status filter (localized display, stable code prefix; empty means no filter)
        current_filter_code = self._code_from_display(self.filter_status_var.get(), kind="status")
        filter_values = [""] + status_values
        self.filter_status_combo.configure(values=filter_values)
        if current_filter_code:
            self.filter_status_var.set(self._display_value(current_filter_code, kind="status"))

        # Type filter (localized display; empty means no filter)
        current_type_code = self._code_from_display(self.filter_type_var.get(), kind="type")
        type_filter_values = [""] + type_values
        self.filter_type_combo.configure(values=type_filter_values)
        if current_type_code:
            self.filter_type_var.set(self._display_value(current_type_code, kind="type"))

        # Make/Model filter values depend on selected Type/Make.
        self._refresh_make_model_filter_values(preserve_typed_model=True)

        # Tree headings
        self.tree.heading("serial", text=self.tr("web_serial"))
        self.tree.heading("type", text=self.tr("web_type"))
        self.tree.heading("model", text=self.tr("web_model"))
        self.tree.heading("from", text=self.tr("web_from_store"))
        self.tree.heading("to", text=self.tr("web_to_store"))
        self.tree.heading("status", text=self.tr("web_status"))
        self.tree.heading("updated", text=self.tr("web_updated"))

        # Rebuild context menu so status labels change with language
        try:
            self.menu.destroy()
        except Exception:
            pass
        self._build_context_menu()

        self._write_result({"ok": True, "lang": self.lang})

        # Result widget colors can be wrong on first paint; re-apply.
        self._apply_non_ttk_theme()

    def _bind_filter_auto_refresh(self) -> None:
        def _trace(_a: str = "", _b: str = "", _c: str = "") -> None:
            self._schedule_filter_refresh()

        for var in (
            self.filter_from_var,
            self.filter_to_var,
            self.filter_model_var,
            self.filter_serial_var,
            self.filter_make_var,
            self.limit_var,
            self.filter_type_var,
        ):
            try:
                var.trace_add("write", _trace)
            except Exception:
                pass

        # Combobox selection event
        try:
            self.filter_status_combo.bind("<<ComboboxSelected>>", lambda _e: self._schedule_filter_refresh())
        except Exception:
            pass

        try:
            self.filter_make_combo.bind("<<ComboboxSelected>>", self._on_filter_make_changed)
            self.filter_make_combo.bind("<KeyRelease>", self._on_filter_make_typed)
        except Exception:
            pass

        try:
            self.filter_type_combo.bind("<<ComboboxSelected>>", self._on_filter_type_changed)
        except Exception:
            pass

        try:
            self.filter_model_combo.bind("<<ComboboxSelected>>", lambda _e: self._schedule_filter_refresh())
        except Exception:
            pass

        try:
            self.filter_model_combo.bind("<KeyRelease>", self._on_filter_model_typed)
        except Exception:
            pass

        # Also refresh when status filter variable changes (covers keyboard navigation)
        try:
            self.filter_status_var.trace_add("write", _trace)
        except Exception:
            pass

    def _schedule_filter_refresh(self) -> None:
        if self._filter_refresh_job is not None:
            try:
                self.root.after_cancel(self._filter_refresh_job)
            except Exception:
                pass
            self._filter_refresh_job = None

        self._filter_refresh_job = self.root.after(250, self._run_filter_refresh)

    def _run_filter_refresh(self) -> None:
        self._filter_refresh_job = None
        self.refresh_list()

    def clear_filters(self) -> None:
        # Reset table to default (no extra sorting) when clearing filters
        self._sort_col = None
        self._sort_desc = False
        self.filter_status_var.set("")
        self.filter_type_var.set("")
        self.filter_make_var.set("")
        self.filter_serial_var.set("")
        self.filter_model_var.set("")
        self.filter_from_var.set("")
        self.filter_to_var.set("")
        self.limit_var.set("200")
        self._refresh_make_model_filter_values(preserve_typed_model=True)
        self.refresh_list()

    def _current_filter_type_code(self) -> str | None:
        type_display = self.filter_type_var.get().strip()
        type_code = self._code_from_display(type_display, kind="type")
        return type_code or None

    def _current_filter_make(self) -> str | None:
        make = self.filter_make_var.get().strip()
        return make or None

    def _refresh_make_model_filter_values(self, *, preserve_typed_model: bool) -> None:
        """Refresh Make/Model dropdown values based on current Type/Make filters."""

        device_type = self._current_filter_type_code()
        current_make = self._current_filter_make()

        catalog_data = DEVICE_CATALOG.get(device_type, {}) if device_type else {}
        catalog_makes = list(catalog_data.keys())

        try:
            db_makes = self.db.list_makes(device_type=device_type)
        except Exception:
            db_makes = []

        all_makes_dict = {m.casefold(): m for m in catalog_makes + db_makes if m.strip()}
        all_makes = sorted(all_makes_dict.values(), key=lambda x: x.casefold())

        self._filter_makes_all = all_makes
        self.filter_make_combo.configure(values=[""] + all_makes)

        if current_make and current_make.casefold() not in all_makes_dict:
            pass

        if (not current_make) and len(all_makes) == 1 and device_type:
            current_make = all_makes[0]
            self.filter_make_var.set(current_make)

        try:
            db_models = self.db.list_models(device_type=device_type, make=current_make)
        except Exception:
            db_models = []

        catalog_models = []
        if current_make:
            for cat_make, models in catalog_data.items():
                if cat_make.casefold() == current_make.casefold():
                    catalog_models.extend(models)
        elif device_type:
            for models in catalog_data.values():
                catalog_models.extend(models)

        all_models_dict = {m.casefold(): m for m in catalog_models + db_models if m.strip()}
        all_models = sorted(all_models_dict.values(), key=lambda x: x.casefold())

        self._filter_models_all = all_models
        self.filter_model_combo.configure(values=[""] + all_models)

        if not preserve_typed_model:
            self.filter_model_var.set("")

    def _on_filter_type_changed(self, _event: tk.Event | None = None) -> None:  # type: ignore[override]
        # Changing type changes available makes/models.
        self.filter_make_var.set("")
        self.filter_model_var.set("")
        self._refresh_make_model_filter_values(preserve_typed_model=True)
        self._schedule_filter_refresh()

    def _on_filter_make_changed(self, _event: tk.Event | None = None) -> None:  # type: ignore[override]
        # Changing make changes available models.
        self.filter_model_var.set("")
        self._refresh_make_model_filter_values(preserve_typed_model=True)
        self._schedule_filter_refresh()

    def _on_filter_make_typed(self, _event: tk.Event | None = None) -> None:  # type: ignore[override]
        typed = self.filter_make_var.get().strip()
        if not getattr(self, "_filter_makes_all", None):
            self._refresh_make_model_filter_values(preserve_typed_model=True)

        if not typed:
            self.filter_make_combo.configure(values=[""] + getattr(self, "_filter_makes_all", []))
            self.filter_model_var.set("")
            self._refresh_make_model_filter_values(preserve_typed_model=True)
            self._schedule_filter_refresh()
            return

        t_low = typed.casefold()
        filtered = [m for m in getattr(self, "_filter_makes_all", []) if t_low in m.casefold()]
        self.filter_make_combo.configure(values=[""] + filtered)
        self._refresh_make_model_filter_values(preserve_typed_model=True)
        self._schedule_filter_refresh()

    def _on_filter_model_typed(self, _event: tk.Event | None = None) -> None:  # type: ignore[override]
        typed = self.filter_model_var.get().strip()
        if not self._filter_models_all:
            self._refresh_make_model_filter_values(preserve_typed_model=True)

        if not typed:
            self.filter_model_combo.configure(values=[""] + (self._filter_models_all or []))
            return

        t_low = typed.casefold()
        filtered = [m for m in (self._filter_models_all or []) if t_low in m.casefold()]
        self.filter_model_combo.configure(values=[""] + filtered)

    def _natural_key(self, value: str) -> list[object]:
        parts = re.split(r"(\d+)", (value or "").lower())
        out: list[object] = []
        for p in parts:
            if p.isdigit():
                out.append(int(p))
            else:
                out.append(p)
        return out

    def _on_sort_column(self, col: str) -> None:
        if self._sort_col == col:
            self._sort_desc = not self._sort_desc
        else:
            self._sort_col = col
            self._sort_desc = False
        self.refresh_list()

    def _get_field_label(self, label_key: str, row: int, col: int) -> ttk.Label:
        return getattr(self, f"_lbl_{label_key}_{row}_{col}")

    def _on_lang_changed(self) -> None:
        self._apply_i18n()
        self.config["lang"] = self.lang
        self._save_config()
        self.refresh_list()
        self._refresh_open_editors_i18n()

    def _register_editor(self, editor: DeviceEditor) -> None:
        self._editors.add(editor)
        editor.bind("<Destroy>", lambda _e: self._editors.discard(editor))

    def _get_open_editor(self) -> DeviceEditor | None:
        for ed in list(self._editors):
            try:
                if ed.winfo_exists():
                    return ed
            except Exception:
                pass
            self._editors.discard(ed)
        return None

    def _refresh_open_editors_i18n(self) -> None:
        for ed in list(self._editors):
            try:
                if not ed.winfo_exists():
                    self._editors.discard(ed)
                    continue
                ed._apply_i18n()
            except Exception:
                # Best-effort; don't break language switching
                pass

    def _refresh_auth_claims(self) -> None:
        token_for_claims = self._auth_access_token or (self.config.get("supabase_key") or "")
        claims = _decode_jwt_claims(token_for_claims)
        role = str(claims.get("role") or "anon").strip() or "anon"

        app_metadata = claims.get("app_metadata")
        app_metadata_dict = app_metadata if isinstance(app_metadata, dict) else {}

        self._auth_role = role
        self._is_device_admin = (
            role.lower() == "service_role"
            or _claim_to_bool(claims.get("device_admin"))
            or _claim_to_bool(app_metadata_dict.get("device_admin"))
        )

    def _apply_admin_session_to_client(self) -> None:
        if not self._auth_access_token:
            return
        try:
            if self._auth_refresh_token and hasattr(self.db.supabase.auth, "set_session"):
                self.db.supabase.auth.set_session(self._auth_access_token, self._auth_refresh_token)
        except Exception:
            pass

    def _restore_admin_session_from_config(self) -> None:
        if not self._remember_admin_device:
            return
        if not self._auth_access_token:
            return

        self._apply_admin_session_to_client()
        self._refresh_auth_claims()
        self._admin_login_active = bool(self._auth_access_token)

    def _extract_auth_session_data(self, response: object) -> tuple[str, str, str]:
        session = None
        user = None

        if isinstance(response, dict):
            session = response.get("session")
            user = response.get("user")
        else:
            session = getattr(response, "session", None)
            user = getattr(response, "user", None)

        access_token = ""
        refresh_token = ""
        email = ""

        if isinstance(session, dict):
            access_token = str(session.get("access_token") or "").strip()
            refresh_token = str(session.get("refresh_token") or "").strip()
        elif session is not None:
            access_token = str(getattr(session, "access_token", "") or "").strip()
            refresh_token = str(getattr(session, "refresh_token", "") or "").strip()

        if isinstance(user, dict):
            email = str(user.get("email") or "").strip()
        elif user is not None:
            email = str(getattr(user, "email", "") or "").strip()

        if (not email) and access_token:
            claims = _decode_jwt_claims(access_token)
            email = str(claims.get("email") or "").strip()

        return access_token, refresh_token, email

    def _clear_saved_admin_session(self, *, refresh_ui: bool = True) -> None:
        self._admin_email = ""
        self._auth_access_token = ""
        self._auth_refresh_token = ""
        self._remember_admin_device = False
        self._admin_login_active = False

        self.config["admin_email"] = ""
        self.config["admin_access_token"] = ""
        self.config["admin_refresh_token"] = ""
        self.config["admin_remember_device"] = False
        self._save_config()

        self._refresh_auth_claims()
        if refresh_ui and hasattr(self, "admin_btn"):
            self._apply_role_controls()
            self._apply_i18n()

    def _toggle_admin_session(self) -> None:
        if self._admin_login_active:
            if messagebox.askyesno(self.tr("desktop_confirm_title"), self.tr("desktop_admin_logout_confirm"), parent=self.root):
                self._logout_admin()
            return
        self._open_admin_login_dialog()

    def _logout_admin(self) -> None:
        try:
            self.db.supabase.auth.sign_out()
        except Exception:
            pass
        self._clear_saved_admin_session()

    def _open_admin_login_dialog(self) -> None:
        win = tk.Toplevel(self.root)
        win.title(self.tr("desktop_admin_login_title"))
        win.geometry("420x250")
        win.minsize(380, 230)
        win.transient(self.root)
        win.grab_set()

        frm = ttk.Frame(win, padding=14)
        frm.pack(fill=tk.BOTH, expand=True)
        frm.columnconfigure(1, weight=1)

        email_var = tk.StringVar(value=self._admin_email)
        password_var = tk.StringVar(value="")
        remember_var = tk.BooleanVar(value=self._remember_admin_device)
        status_var = tk.StringVar(value="")

        ttk.Label(frm, text=self.tr("desktop_admin_email")).grid(row=0, column=0, sticky="w")
        email_entry = ttk.Entry(frm, textvariable=email_var)
        email_entry.grid(row=0, column=1, sticky="ew")

        ttk.Label(frm, text=self.tr("desktop_admin_password")).grid(row=1, column=0, sticky="w", pady=(8, 0))
        password_entry = ttk.Entry(frm, textvariable=password_var, show="*")
        password_entry.grid(row=1, column=1, sticky="ew", pady=(8, 0))

        ttk.Checkbutton(frm, text=self.tr("desktop_admin_remember_device"), variable=remember_var).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(10, 0)
        )

        ttk.Label(frm, textvariable=status_var, style="Muted.TLabel").grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

        def _submit() -> None:
            email = email_var.get().strip()
            password = password_var.get().strip()
            if not email or not password:
                status_var.set(self.tr("desktop_admin_login_failed"))
                return

            try:
                response = self.db.supabase.auth.sign_in_with_password({"email": email, "password": password})
                access_token, refresh_token, resolved_email = self._extract_auth_session_data(response)
                if not access_token:
                    raise ValueError(self.tr("desktop_admin_login_failed"))

                self._auth_access_token = access_token
                self._auth_refresh_token = refresh_token
                self._admin_email = resolved_email or email
                self._remember_admin_device = bool(remember_var.get())
                self._admin_login_active = True

                self._refresh_auth_claims()

                if self._remember_admin_device:
                    self.config["admin_email"] = self._admin_email
                    self.config["admin_access_token"] = self._auth_access_token
                    self.config["admin_refresh_token"] = self._auth_refresh_token
                    self.config["admin_remember_device"] = True
                else:
                    self.config["admin_email"] = ""
                    self.config["admin_access_token"] = ""
                    self.config["admin_refresh_token"] = ""
                    self.config["admin_remember_device"] = False
                self._save_config()

                self._apply_role_controls()
                self._apply_i18n()
                win.destroy()
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror(self.tr("desktop_error_title"), f"{self.tr('desktop_admin_login_failed')}: {exc}", parent=win)

        btns = ttk.Frame(frm)
        btns.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        btns.columnconfigure(0, weight=1)
        btns.columnconfigure(1, weight=1)
        ttk.Button(btns, text=self.tr("desktop_admin_login"), command=_submit).grid(row=0, column=0, sticky="ew")
        ttk.Button(btns, text=self.tr("desktop_close"), command=win.destroy).grid(row=0, column=1, sticky="ew", padx=(8, 0))

        email_entry.focus_set()
        password_entry.bind("<Return>", lambda _e: _submit())

    def _apply_role_controls(self) -> None:
        try:
            if self._admin_login_active:
                self.audit_btn.grid()
                self.diag_btn.grid()
                self.prefix_btn.grid()
            else:
                self.audit_btn.grid_remove()
                self.diag_btn.grid_remove()
                self.prefix_btn.grid_remove()
        except Exception:
            pass

    def _authorize_admin_panel(self) -> bool:
        if self._admin_login_active:
            return True
        messagebox.showerror(self.tr("desktop_error_title"), self.tr("desktop_admin_required"), parent=self.root)
        return False

    def _require_admin_delete(self) -> bool:
        if self._admin_login_active:
            return True
        messagebox.showerror(self.tr("desktop_error_title"), self.tr("desktop_admin_required"), parent=self.root)
        return False

    def _is_offline_error(self, exc: Exception) -> bool:
        msg = str(exc).lower()
        return any(
            token in msg
            for token in (
                "timeout",
                "connection",
                "network",
                "failed to establish",
                "name or service",
                "temporary failure",
                "host",
                "dns",
                "ssl",
            )
        )

    def _normalize_prefix_key(self, value: str | None) -> str:
        raw = (value or "").upper().strip()
        if not raw:
            return ""
        cleaned = re.sub(r"[^A-Z0-9:]", "", raw)
        if ":" in cleaned:
            left, right = cleaned.split(":", 1)
            return f"{left}:{right}"
        return cleaned

    def _mark_sync_success(self) -> None:
        self._last_sync_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    def _pending_ops_count(self) -> int:
        return len(self._load_pending_ops())

    def _require_pin(self) -> bool:
        return True

    def _after_save(self) -> None:
        if self.bulk_scan_var.get():
            self.serial_var.set("")
            self.serial_entry.focus_set()
            self.overwrite_var.set(False)
            return
        self.clear_form()

    def _on_bulk_scan_toggle(self) -> None:
        if self.bulk_scan_var.get():
            try:
                self.serial_entry.focus_set()
                self.serial_entry.icursor(tk.END)
            except Exception:
                pass

    def _schedule_scanner_focus_lock(self) -> None:
        if self._focus_lock_job:
            try:
                self.root.after_cancel(self._focus_lock_job)
            except Exception:
                pass
        self._focus_lock_job = self.root.after(350, self._scanner_focus_lock_tick)

    def _scanner_focus_lock_tick(self) -> None:
        self._focus_lock_job = None
        try:
            if self.bulk_scan_var.get():
                current_focus = self.root.focus_get()
                top = current_focus.winfo_toplevel() if current_focus is not None else None
                if top is self.root and current_focus is not self.serial_entry:
                    self.serial_entry.focus_set()
                    self.serial_entry.icursor(tk.END)
        except Exception:
            pass
        self._schedule_scanner_focus_lock()

    def _sync_now(self) -> None:
        synced, remaining = self._flush_pending_ops()
        self._mark_sync_success()
        self._write_result({"ok": True, "sync": synced, "pending": remaining})
        self.refresh_list()

    def _open_diagnostics_panel(self) -> None:
        if not self._authorize_admin_panel():
            return

        win = tk.Toplevel(self.root)
        win.title(self.tr("desktop_diagnostics_title"))
        win.geometry("700x450")
        win.minsize(640, 420)
        win.transient(self.root)

        theme = (self.theme or "light").lower()
        if theme == "dark":
            panel_bg = "#0f1216"
            card_bg = "#171b21"
            card_border = "#2a2f39"
            text = "#e8eaed"
            muted = "#a5aab3"
        else:
            panel_bg = "#f4f6f8"
            card_bg = "#ffffff"
            card_border = "#d8dee6"
            text = "#111111"
            muted = "#5f6775"

        outer = tk.Frame(win, bg=panel_bg, padx=16, pady=14)
        outer.pack(fill=tk.BOTH, expand=True)
        outer.columnconfigure(0, weight=1)

        title_row = tk.Frame(outer, bg=panel_bg)
        title_row.grid(row=0, column=0, sticky="ew")
        title_row.columnconfigure(1, weight=1)

        tk.Label(
            title_row,
            text=self.tr("desktop_diagnostics_title"),
            bg=panel_bg,
            fg=text,
            font=("Segoe UI", 13, "bold"),
        ).grid(row=0, column=0, sticky="w")

        health_badge = tk.Label(
            title_row,
            text="",
            bg="#5f6775",
            fg="#ffffff",
            padx=12,
            pady=5,
            font=("Segoe UI", 9, "bold"),
        )
        health_badge.grid(row=0, column=1, sticky="e")

        tk.Label(
            outer,
            text=self.tr("desktop_diag_subtitle"),
            bg=panel_bg,
            fg=muted,
            font=("Segoe UI", 9),
        ).grid(row=1, column=0, sticky="w", pady=(4, 10))

        cards = tk.Frame(outer, bg=panel_bg)
        cards.grid(row=2, column=0, sticky="ew")
        cards.columnconfigure(0, weight=1)
        cards.columnconfigure(1, weight=1)
        cards.columnconfigure(2, weight=1)

        api_var = tk.StringVar(value="")
        queue_var = tk.StringVar(value="")
        role_var = tk.StringVar(value="")
        sync_var = tk.StringVar(value="")
        url_var = tk.StringVar(value=self.config.get("supabase_url", ""))
        status_var = tk.StringVar(value="")

        def _metric_card(parent: tk.Frame, col: int, title: str, value_var: tk.StringVar) -> tk.Label:
            card = tk.Frame(parent, bg=card_bg, highlightbackground=card_border, highlightthickness=1, bd=0)
            pad_left = 0 if col == 0 else 8
            pad_right = 0 if col == 2 else 8
            card.grid(row=0, column=col, sticky="nsew", padx=(pad_left, pad_right))
            tk.Label(card, text=title, bg=card_bg, fg=muted, font=("Segoe UI", 9)).pack(anchor="w", padx=12, pady=(10, 2))
            value_lbl = tk.Label(card, textvariable=value_var, bg=card_bg, fg=text, font=("Segoe UI", 12, "bold"))
            value_lbl.pack(anchor="w", padx=12, pady=(0, 10))
            return value_lbl

        api_value_lbl = _metric_card(cards, 0, self.tr("desktop_diag_api"), api_var)
        queue_value_lbl = _metric_card(cards, 1, self.tr("desktop_diag_queue"), queue_var)
        _metric_card(cards, 2, self.tr("desktop_diag_role"), role_var)

        details_card = tk.Frame(outer, bg=card_bg, highlightbackground=card_border, highlightthickness=1, bd=0)
        details_card.grid(row=3, column=0, sticky="nsew", pady=(10, 0))
        details_card.columnconfigure(1, weight=1)

        tk.Label(details_card, text=self.tr("desktop_diag_last_sync"), bg=card_bg, fg=muted, font=("Segoe UI", 9)).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 4)
        )
        tk.Label(details_card, textvariable=sync_var, bg=card_bg, fg=text, font=("Segoe UI", 10, "bold")).grid(
            row=0, column=1, sticky="w", padx=(0, 12), pady=(10, 4)
        )

        tk.Label(details_card, text=self.tr("desktop_diag_url"), bg=card_bg, fg=muted, font=("Segoe UI", 9)).grid(
            row=1, column=0, sticky="nw", padx=12, pady=(0, 10)
        )
        tk.Label(
            details_card,
            textvariable=url_var,
            bg=card_bg,
            fg=text,
            font=("Segoe UI", 9),
            justify="left",
            wraplength=440,
        ).grid(row=1, column=1, sticky="w", padx=(0, 12), pady=(0, 10))

        status_lbl = tk.Label(
            outer,
            textvariable=status_var,
            bg=panel_bg,
            fg=muted,
            font=("Segoe UI", 9),
            justify="left",
            wraplength=640,
        )
        status_lbl.grid(row=4, column=0, sticky="w", pady=(10, 0))

        def _copy_url() -> None:
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(url_var.get())
                status_var.set(self.tr("desktop_diag_url_copied"))
            except Exception:
                pass

        def _refresh() -> None:
            queue_count = self._pending_ops_count()
            queue_var.set(str(queue_count))
            role_var.set(f"{self._auth_role} ({'admin' if self._admin_login_active else 'operator'})")
            sync_var.set(self._last_sync_at or self.tr("desktop_diag_na"))

            api_ok = False
            api_error = ""
            try:
                self.db.list_devices(limit=1)
                api_ok = True
            except Exception as exc:
                api_error = str(exc)

            api_var.set(self.tr("desktop_diag_api_ok") if api_ok else self.tr("desktop_diag_api_error"))
            api_value_lbl.configure(fg="#0a7a2f" if api_ok else "#b00020")
            queue_value_lbl.configure(fg="#ad6a00" if queue_count > 0 else "#0a7a2f")

            if not api_ok:
                health_text = self.tr("desktop_diag_health_offline")
                badge_bg = "#b00020"
                status_lbl.configure(fg="#b00020")
                status_var.set(api_error)
            elif queue_count > 0:
                health_text = self.tr("desktop_diag_health_queue")
                badge_bg = "#ad6a00"
                status_lbl.configure(fg="#ad6a00")
                status_var.set(self.tr("desktop_diag_queue_pending", n=queue_count))
            else:
                health_text = self.tr("desktop_diag_health_ok")
                badge_bg = "#0a7a2f"
                status_lbl.configure(fg="#0a7a2f")
                status_var.set(self.tr("desktop_diag_ready"))

            health_badge.configure(text=f"{self.tr('desktop_diag_health')}: {health_text}", bg=badge_bg)

        btns = ttk.Frame(outer)
        btns.grid(row=5, column=0, sticky="ew", pady=(14, 0))
        btns.columnconfigure(0, weight=1)
        btns.columnconfigure(1, weight=1)
        btns.columnconfigure(2, weight=1)
        btns.columnconfigure(3, weight=1)

        ttk.Button(btns, text=self.tr("desktop_sync"), command=lambda: (self._sync_now(), _refresh())).grid(
            row=0, column=0, sticky="ew"
        )
        ttk.Button(btns, text=self.tr("web_refresh"), command=_refresh).grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ttk.Button(btns, text=self.tr("desktop_diag_copy_url"), command=_copy_url).grid(row=0, column=2, sticky="ew", padx=(8, 0))
        ttk.Button(btns, text=self.tr("desktop_close"), command=win.destroy).grid(row=0, column=3, sticky="ew", padx=(8, 0))

        _refresh()

    def _open_prefix_rules_admin(self) -> None:
        if not self._authorize_admin_panel():
            return

        win = tk.Toplevel(self.root)
        win.title(self.tr("desktop_prefix_admin_title"))
        win.geometry("1120x620")
        win.minsize(980, 560)
        win.transient(self.root)

        frame = ttk.Frame(win, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)

        form = ttk.Frame(frame)
        form.grid(row=0, column=0, sticky="ew")
        for i in range(6):
            form.columnconfigure(i, weight=1)

        rule_id_var = tk.StringVar(value="")
        key_var = tk.StringVar(value="")
        type_var = tk.StringVar(value="scanner")
        make_var = tk.StringVar(value="")
        model_var = tk.StringVar(value="")
        priority_var = tk.StringVar(value="100")
        active_var = tk.BooleanVar(value=True)
        status_var = tk.StringVar(value="")
        counts_var = tk.StringVar(value="")

        ttk.Label(form, text=self.tr("desktop_prefix_key")).grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=key_var).grid(row=1, column=0, sticky="ew", padx=(0, 8))

        ttk.Label(form, text=self.tr("web_type")).grid(row=0, column=1, sticky="w")
        ttk.Combobox(form, textvariable=type_var, values=DEVICE_TYPES, state="readonly").grid(
            row=1, column=1, sticky="ew", padx=(0, 8)
        )

        ttk.Label(form, text=self.tr("web_make")).grid(row=0, column=2, sticky="w")
        ttk.Entry(form, textvariable=make_var).grid(row=1, column=2, sticky="ew", padx=(0, 8))

        ttk.Label(form, text=self.tr("web_model")).grid(row=0, column=3, sticky="w")
        ttk.Entry(form, textvariable=model_var).grid(row=1, column=3, sticky="ew", padx=(0, 8))

        ttk.Label(form, text=self.tr("desktop_prefix_priority")).grid(row=0, column=4, sticky="w")
        ttk.Entry(form, textvariable=priority_var).grid(row=1, column=4, sticky="ew", padx=(0, 8))

        ttk.Checkbutton(form, text=self.tr("desktop_prefix_active"), variable=active_var).grid(row=1, column=5, sticky="w")

        tree = ttk.Treeview(
            frame,
            columns=("key", "type", "make", "model", "priority", "active", "source", "updated", "id"),
            show="headings",
            selectmode="browse",
        )
        tree.grid(row=2, column=0, sticky="nsew", pady=(10, 0))

        tree.heading("key", text=self.tr("desktop_prefix_key"))
        tree.heading("type", text=self.tr("web_type"))
        tree.heading("make", text=self.tr("web_make"))
        tree.heading("model", text=self.tr("web_model"))
        tree.heading("priority", text=self.tr("desktop_prefix_priority"))
        tree.heading("active", text=self.tr("desktop_prefix_active"))
        tree.heading("source", text="source")
        tree.heading("updated", text=self.tr("web_updated"))
        tree.heading("id", text="id")

        tree.column("key", width=130, anchor="w")
        tree.column("type", width=100, anchor="w")
        tree.column("make", width=130, anchor="w")
        tree.column("model", width=180, anchor="w")
        tree.column("priority", width=80, anchor="w")
        tree.column("active", width=70, anchor="w")
        tree.column("source", width=120, anchor="w")
        tree.column("updated", width=180, anchor="w")
        tree.column("id", width=190, anchor="w")

        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        vsb.grid(row=2, column=1, sticky="ns", pady=(10, 0))
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        hsb.grid(row=3, column=0, sticky="ew", pady=(4, 0))
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        def _clear_form() -> None:
            rule_id_var.set("")
            key_var.set("")
            type_var.set("scanner")
            make_var.set("")
            model_var.set("")
            priority_var.set("100")
            active_var.set(True)

        def _load_rules() -> None:
            tree.delete(*tree.get_children())
            try:
                db_rows = self.db.list_prefix_rules_admin(include_inactive=True)
            except Exception as exc:
                status_var.set(f"{self.tr('desktop_prefix_load_failed')}: {exc}")
                counts_var.set("")
                return

            normalized_db_keys: set[str] = set()

            for row in db_rows:
                raw_key = str(row.get("prefix_key") or "").strip()
                normalized = raw_key.split(":", 1)[1] if ":" in raw_key else raw_key
                if normalized:
                    normalized_db_keys.add(normalized.upper())

                updated = str(row.get("updated_at") or "").replace("T", " ")
                tree.insert(
                    "",
                    tk.END,
                    values=(
                        normalized or raw_key,
                        row.get("device_type") or "",
                        row.get("make") or "",
                        row.get("model") or "",
                        row.get("priority") if row.get("priority") is not None else "",
                        "yes" if row.get("active", True) else "no",
                        "db",
                        updated,
                        row.get("id") or "",
                    ),
                )

            # Show built-in defaults that are not overridden by DB keys.
            for prefix_key, (device_type, make, full_model) in sorted(SERIAL_PREFIX_MAP.items(), key=lambda item: item[0]):
                key_u = str(prefix_key).upper()
                if key_u in normalized_db_keys:
                    continue

                model_value = str(full_model or "").strip()
                if make and model_value.upper().startswith(f"{make} ".upper()):
                    model_value = model_value[len(make) + 1 :]

                tree.insert(
                    "",
                    tk.END,
                    values=(
                        prefix_key,
                        device_type,
                        make,
                        model_value,
                        "base",
                        "yes",
                        "built-in",
                        "",
                        f"builtin:{prefix_key}",
                    ),
                )

            # Show local config rules that are not overridden by DB keys.
            for prefix_key, (device_type, make, full_model) in sorted((self._custom_prefix_rules or {}).items(), key=lambda item: item[0]):
                key_u = str(prefix_key).upper()
                if key_u in normalized_db_keys:
                    continue

                model_value = str(full_model or "").strip()
                if make and model_value.upper().startswith(f"{make} ".upper()):
                    model_value = model_value[len(make) + 1 :]

                tree.insert(
                    "",
                    tk.END,
                    values=(
                        prefix_key,
                        device_type,
                        make,
                        model_value,
                        "local",
                        "yes",
                        "config",
                        "",
                        f"config:{prefix_key}",
                    ),
                )

            status_var.set(self.tr("desktop_prefix_loaded", n=len(db_rows)))

            try:
                active_db_rules = self.db.list_prefix_rules()
                effective_rules = self._get_prefix_rules()

                device_count_text = ""
                try:
                    # This is inventory row count (devices), not prefix rule count.
                    devices = self.db.list_devices(limit=5000)
                    device_count_text = f" | Inventory devices: {len(devices)}"
                except Exception:
                    device_count_text = ""

                counts_var.set(
                    f"Prefix rules -> DB rows: {len(db_rows)} | Active DB prefixes: {len(active_db_rules)} | Effective scanner prefixes: {len(effective_rules)}{device_count_text}"
                )
            except Exception:
                counts_var.set(f"DB rows: {len(db_rows)}")

        def _on_select(_event: tk.Event | None = None) -> None:
            sel = tree.selection()
            if not sel:
                return
            vals = tree.item(sel[0], "values")
            if not vals:
                return

            key_var.set(str(vals[0] or ""))
            type_var.set(str(vals[1] or "scanner"))
            make_var.set(str(vals[2] or ""))
            model_var.set(str(vals[3] or ""))
            source = str(vals[6] or "")
            priority_var.set(str(vals[4] or "100"))
            active_var.set(str(vals[5] or "").lower() == "yes")
            selected_id = str(vals[8] or "")
            if source != "db" or selected_id.startswith("builtin:") or selected_id.startswith("config:"):
                rule_id_var.set("")
                status_var.set("Read-only source rule selected. Save to create/override DB rule.")
            else:
                rule_id_var.set(selected_id)
                status_var.set("")

        def _save_rule() -> None:
            key = self._normalize_prefix_key(key_var.get())
            if not key:
                status_var.set(self.tr("desktop_prefix_key_required"))
                return

            try:
                priority = int(priority_var.get().strip() or "100")
            except Exception:
                priority = 100

            try:
                self.db.save_prefix_rule(
                    rule_id=rule_id_var.get().strip() or None,
                    prefix_key=key,
                    device_type=(type_var.get().strip() or "scanner").lower(),
                    make=make_var.get().strip(),
                    model=model_var.get().strip(),
                    priority=priority,
                    active=bool(active_var.get()),
                )
                status_var.set(self.tr("desktop_prefix_saved"))
                _load_rules()
                _clear_form()
            except Exception as exc:
                status_var.set(f"{self.tr('desktop_prefix_save_failed')}: {exc}")

        def _delete_rule() -> None:
            rid = rule_id_var.get().strip()
            if not rid:
                status_var.set(self.tr("desktop_prefix_select_delete"))
                return

            if not messagebox.askyesno(self.tr("desktop_confirm_title"), self.tr("desktop_prefix_confirm_delete"), parent=win):
                return

            try:
                self.db.delete_prefix_rule(rule_id=rid)
                status_var.set(self.tr("desktop_prefix_deleted"))
                _load_rules()
                _clear_form()
            except Exception as exc:
                status_var.set(f"{self.tr('desktop_prefix_delete_failed')}: {exc}")

        btns = ttk.Frame(frame)
        btns.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        btns.columnconfigure(0, weight=1)
        btns.columnconfigure(1, weight=1)
        btns.columnconfigure(2, weight=1)
        btns.columnconfigure(3, weight=1)
        btns.columnconfigure(4, weight=1)

        ttk.Button(btns, text=self.tr("web_refresh"), command=_load_rules).grid(row=0, column=0, sticky="ew")
        ttk.Button(btns, text=self.tr("desktop_save"), command=_save_rule).grid(row=0, column=1, sticky="ew", padx=(8, 0))
        ttk.Button(btns, text=self.tr("web_delete"), command=_delete_rule).grid(row=0, column=2, sticky="ew", padx=(8, 0))
        ttk.Button(btns, text=self.tr("desktop_clear_form"), command=_clear_form).grid(row=0, column=3, sticky="ew", padx=(8, 0))
        ttk.Button(btns, text=self.tr("desktop_close"), command=win.destroy).grid(row=0, column=4, sticky="ew", padx=(8, 0))

        ttk.Label(frame, textvariable=counts_var, style="Muted.TLabel").grid(row=5, column=0, sticky="w", pady=(8, 0))
        ttk.Label(frame, textvariable=status_var, style="Muted.TLabel").grid(row=6, column=0, sticky="w", pady=(2, 0))

        tree.bind("<<TreeviewSelect>>", _on_select)
        _load_rules()

    def _camera_scan(self) -> None:
        try:
            import cv2  # type: ignore
            from pyzbar import pyzbar  # type: ignore
        except Exception:
            manual = simpledialog.askstring(self.tr("desktop_camera_scan"), "Paste serial to scan:")
            if manual:
                self.serial_var.set(manual.strip())
                self._on_serial_scanned()
            return

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror(self.tr("desktop_error_title"), "Camera not available")
            return

        serial = None
        for _ in range(60):
            ret, frame = cap.read()
            if not ret:
                continue
            codes = pyzbar.decode(frame)
            if codes:
                try:
                    serial = codes[0].data.decode("utf-8")
                except Exception:
                    serial = None
                break
        cap.release()

        if serial:
            self.serial_var.set(serial)
            self._on_serial_scanned()
        else:
            messagebox.showinfo(self.tr("desktop_camera_scan"), "No barcode detected")

    def _open_settings_dialog(self) -> None:
        win = tk.Toplevel(self.root)
        win.title(self.tr("desktop_config_title"))
        win.geometry("520x520")
        win.transient(self.root)

        frm = ttk.Frame(win, padding=14)
        frm.pack(fill=tk.BOTH, expand=True)
        frm.columnconfigure(1, weight=1)

        url_var = tk.StringVar(value=self.config.get("supabase_url", ""))
        key_var = tk.StringVar(value=self.config.get("supabase_key", ""))
        lang_var = tk.StringVar(value=self.lang)

        ttk.Label(frm, text=self.tr("desktop_config_supabase_url")).grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=url_var).grid(row=0, column=1, sticky="ew")

        ttk.Label(frm, text=self.tr("desktop_config_supabase_key")).grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(frm, textvariable=key_var, show="*").grid(row=1, column=1, sticky="ew", pady=(8, 0))

        ttk.Label(frm, text=self.tr("web_language")).grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Combobox(frm, textvariable=lang_var, values=["lv", "en"], state="readonly").grid(row=2, column=1, sticky="ew", pady=(8, 0))

        ttk.Label(frm, text=self.tr("desktop_config_prefix_rules")).grid(row=3, column=0, sticky="w", pady=(8, 0))
        prefix_txt = tk.Text(frm, height=8, wrap="word")
        prefix_txt.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(4, 0))
        frm.rowconfigure(4, weight=1)
        prefix_txt.insert("1.0", self.config.get("prefix_rules", ""))

        def _save() -> None:
            self.config["supabase_url"] = url_var.get().strip()
            self.config["supabase_key"] = key_var.get().strip()
            self.config["lang"] = lang_var.get().strip() or "lv"
            self.config["prefix_rules"] = prefix_txt.get("1.0", tk.END).strip()
            self._save_config()

            self.lang = self.config["lang"]
            self._custom_prefix_rules = self._load_prefix_rules()
            self.db = InventoryDB(
                self.db_path,
                url=self.config.get("supabase_url"),
                key=self.config.get("supabase_key"),
            )
            self._apply_admin_session_to_client()
            self._refresh_auth_claims()
            self._apply_i18n()
            self._apply_role_controls()
            self.refresh_list()
            messagebox.showinfo(self.tr("desktop_config_title"), self.tr("desktop_config_saved"))
            win.destroy()

        ttk.Button(frm, text=self.tr("desktop_config_save"), command=_save).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 0))

    # ---------- Data actions ----------

    def _write_result(self, payload: object, ok: bool = True) -> None:
        # Force background in case Tk ignored earlier theme updates.
        self._apply_non_ttk_theme()
        self.result_txt.configure(state="normal")
        self.result_txt.delete("1.0", tk.END)
        if isinstance(payload, (dict, list)):
            try:
                pretty = json.dumps(payload, indent=2, ensure_ascii=False)
            except Exception:
                pretty = str(payload)
        else:
            pretty = str(payload)

        self.result_txt.insert("1.0", pretty)
        self.result_txt.configure(state="disabled")
        if (self.theme or "light") == "dark":
            ok_fg = "#7ee787"
            err_fg = "#ff7b72"
        else:
            ok_fg = "#0a7a2f"
            err_fg = "#b00020"

        self.result_txt.tag_configure("ok", foreground=ok_fg)
        self.result_txt.tag_configure("err", foreground=err_fg)

        # Not perfect coloring, but keep the area usable.
        self.result_txt.configure(fg=ok_fg if ok else err_fg)

    def _current_device_from_form(self) -> Device:
        raw_serial = self.serial_var.get().strip()
        serial = raw_serial
        device_type = self._code_from_display(self.type_var.get(), kind="type") or "scanner"

        if raw_serial:
            serial_token = extract_preferred_serial(raw_serial, mode=device_type)
            if serial_token:
                serial = normalize_for_store(serial_token)

        make = self.make_var.get().strip() or None
        model_text = self.model_var.get().strip() or None
        from_store = self.from_store_var.get().strip() or None
        to_store = self.to_store_var.get().strip() or None
        status = self._code_from_display(self.status_var.get(), kind="status") or "RECEIVED"
        created_at = self._resolve_created_at_for_serial(serial)
        comment = self._prepare_comment_for_persist(
            self.comment_var.get(),
            serial=serial,
            device_type=device_type,
            created_at=created_at,
            allow_admin_override=self._admin_login_active,
        )

        model: str | None
        if model_text and make:
            if model_text.casefold().startswith(make.casefold()):
                model = model_text
            else:
                model = f"{make} {model_text}".strip()
        else:
            model = model_text

        return Device(
            serial=serial,
            device_type=device_type,
            model=model,
            from_store=from_store,
            to_store=to_store,
            status=status,
            comment=comment,
            created_at=created_at,
        )

    def add_device(self) -> None:
        device: Device | None = None
        overwrite = bool(self.overwrite_var.get())
        try:
            device = self._current_device_from_form()
            if overwrite or device.status != "RECEIVED":
                if not self._require_pin():
                    return
            self.db.add_device(device, overwrite=overwrite)
            self._selected_serial = device.serial
            refreshed = self.db.get_device(device.serial)
            self._selected_updated_at = refreshed.updated_at if refreshed else None
            self._selected_created_at = refreshed.created_at if refreshed else device.created_at
            self._write_result({"ok": True, "action": "add", "serial": device.serial})
            self.refresh_list(select_serial=device.serial)
            self._after_save()
        except Exception as exc:  # noqa: BLE001
            if self._is_offline_error(exc) and device and device.serial:
                self._enqueue_op({"action": "add", "device": asdict(device), "overwrite": overwrite})
                self._write_result({"ok": True, "offline": True, "action": "add", "serial": device.serial})
                self._after_save()
                return
            messagebox.showerror(self.tr("desktop_error_title"), str(exc))
            self._write_result({"ok": False, "error": str(exc)}, ok=False)

    def update_device(self) -> None:
        device: Device | None = None
        try:
            device = self._current_device_from_form()
            if not device.serial:
                raise ValueError("serial is required")
            if not self._require_pin():
                return

            changed = self.db.update_device(
                device.serial,
                device_type=device.device_type,
                model=device.model,
                from_store=device.from_store,
                to_store=device.to_store,
                status=device.status,
                comment=device.comment,
                expected_updated_at=self._selected_updated_at,
            )
            if not changed:
                raise ValueError(self.tr("not_found_or_no_fields"))

            self._selected_serial = device.serial
            refreshed = self.db.get_device(device.serial)
            self._selected_updated_at = refreshed.updated_at if refreshed else None
            self._selected_created_at = refreshed.created_at if refreshed else device.created_at
            self._write_result({"ok": True, "action": "update", "serial": device.serial})
            self.refresh_list(select_serial=device.serial)
            self._after_save()
        except SyncConflictError as exc:
            choice = messagebox.askyesnocancel(
                self.tr("desktop_error_title"),
                f"{exc}\n\nYes = overwrite with current values\nNo = reload latest from database\nCancel = keep current form",
            )

            if choice is True and device and device.serial:
                try:
                    changed = self.db.update_device(
                        device.serial,
                        device_type=device.device_type,
                        model=device.model,
                        from_store=device.from_store,
                        to_store=device.to_store,
                        status=device.status,
                        comment=device.comment,
                        expected_updated_at=None,
                    )
                    if not changed:
                        raise ValueError(self.tr("not_found_or_no_fields"))

                    refreshed = self.db.get_device(device.serial)
                    self._selected_serial = device.serial
                    self._selected_updated_at = refreshed.updated_at if refreshed else None
                    self._selected_created_at = refreshed.created_at if refreshed else device.created_at
                    self._write_result(
                        {"ok": True, "action": "update", "serial": device.serial, "conflict": "overwrite"}
                    )
                    self.refresh_list(select_serial=device.serial)
                    self._after_save()
                    return
                except Exception as overwrite_exc:  # noqa: BLE001
                    messagebox.showerror(self.tr("desktop_error_title"), str(overwrite_exc))
                    self._write_result({"ok": False, "error": str(overwrite_exc)}, ok=False)
                    return

            if choice is False and device and device.serial:
                try:
                    latest = self.db.get_device(device.serial)
                    if latest:
                        self._fill_action_form(latest)
                        self.serial_var.set(latest.serial)
                    self._write_result(
                        {"ok": False, "serial": device.serial, "conflict": "reloaded_latest"},
                        ok=False,
                    )
                    self.refresh_list(select_serial=device.serial)
                    return
                except Exception:
                    self.refresh_list(select_serial=device.serial)
                    return

            self._write_result({"ok": False, "error": str(exc), "conflict": "cancelled"}, ok=False)
            return
        except Exception as exc:  # noqa: BLE001
            if self._is_offline_error(exc) and device and device.serial:
                self._enqueue_op(
                    {
                        "action": "update",
                        "serial": device.serial,
                        "fields": {
                            "device_type": device.device_type,
                            "model": device.model,
                            "from_store": device.from_store,
                            "to_store": device.to_store,
                            "status": device.status,
                            "comment": device.comment,
                        },
                    }
                )
                self._write_result({"ok": True, "offline": True, "action": "update", "serial": device.serial})
                self._after_save()
                return
            messagebox.showerror(self.tr("desktop_error_title"), str(exc))
            self._write_result({"ok": False, "error": str(exc)}, ok=False)

    def change_status(self) -> None:
        serial = ""
        status_code = "RECEIVED"
        comment: str | None = None
        try:
            serial = self.serial_var.get().strip() or (self._selected_serial or "")
            if not serial:
                raise ValueError("serial is required")
            if not self._require_pin():
                return

            status_code = self._code_from_display(self.status_var.get(), kind="status") or "RECEIVED"
            created_at = self._resolve_created_at_for_serial(serial)
            device_type = self._code_from_display(self.type_var.get(), kind="type") or "scanner"
            comment = self._prepare_comment_for_persist(
                self.comment_var.get(),
                serial=serial,
                device_type=device_type,
                created_at=created_at,
                allow_admin_override=self._admin_login_active,
            )
            changed = self.db.change_status(
                serial,
                status_code,
                to_store=self.to_store_var.get().strip() or None,
                comment=comment,
            )
            if not changed:
                raise ValueError(self.tr("not_found"))

            self._selected_serial = serial
            self.comment_var.set(comment or "")
            self._write_result(
                {
                    "ok": True,
                    "action": "status",
                    "serial": serial,
                    "status": status_code,
                }
            )
            self.refresh_list(select_serial=serial)
            self._after_save()
        except Exception as exc:  # noqa: BLE001
            if self._is_offline_error(exc) and serial:
                self._enqueue_op(
                    {
                        "action": "status",
                        "serial": serial,
                        "status": status_code,
                        "to_store": self.to_store_var.get().strip() or None,
                        "comment": comment,
                    }
                )
                self._write_result({"ok": True, "offline": True, "action": "status", "serial": serial})
                self._after_save()
                return
            messagebox.showerror(self.tr("desktop_error_title"), str(exc))
            self._write_result({"ok": False, "error": str(exc)}, ok=False)

    def delete_selected(self) -> None:
        serial = ""
        try:
            if not self._require_admin_delete():
                return
            serial = self.serial_var.get().strip() or (self._selected_serial or "")
            if not serial:
                raise ValueError("serial is required")
            if not self._require_pin():
                return

            msg = self.tr("web_confirm_delete", serial=serial)
            if not messagebox.askyesno(self.tr("desktop_confirm_title"), msg):
                return

            deleted = self.db.delete_device(serial)
            if not deleted:
                raise ValueError(self.tr("not_found"))

            self._write_result({"ok": True, "action": "delete", "serial": serial})
            self.clear_form()
            self.refresh_list()
        except Exception as exc:  # noqa: BLE001
            if self._is_offline_error(exc) and serial:
                self._enqueue_op({"action": "delete", "serial": serial})
                self._write_result({"ok": True, "offline": True, "action": "delete", "serial": serial})
                self.clear_form()
                return
            messagebox.showerror(self.tr("desktop_error_title"), str(exc))
            self._write_result({"ok": False, "error": str(exc)}, ok=False)

    def clear_form(self) -> None:
        self._selected_serial = None
        self._selected_updated_at = None
        self._selected_created_at = None
        self.serial_var.set("")
        self.type_var.set(self._display_value("scanner", kind="type"))
        self.make_var.set("")
        self.model_var.set("")
        self.from_store_var.set("")
        self.to_store_var.set("")
        self.status_var.set(self._display_value("RECEIVED", kind="status"))
        self.comment_var.set("")
        self.overwrite_var.set(False)

        try:
            self._refresh_action_make_model_values(preserve_typed_model=True)
        except Exception:
            pass

    def refresh_list(self, *, select_serial: str | None = None) -> None:
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)

            status_display = self.filter_status_var.get().strip()
            status = self._code_from_display(status_display, kind="status") or None
            type_display = self.filter_type_var.get().strip()
            device_type = self._code_from_display(type_display, kind="type") or None
            make = self.filter_make_var.get().strip() or None
            serial_filter = self.filter_serial_var.get().strip() or None
            model = self.filter_model_var.get().strip() or None
            from_store = self.filter_from_var.get().strip() or None
            to_store = self.filter_to_var.get().strip() or None

            try:
                limit = int(self.limit_var.get().strip() or "200")
            except Exception:
                limit = 200

            devices = self.db.list_devices(
                status=status,
                device_type=device_type,
                serial=serial_filter,
                make=make,
                model=model,
                from_store=from_store,
                to_store=to_store,
                limit=limit,
            )

            # Apply in-memory sorting when user clicked a heading.
            if self._sort_col:
                col = self._sort_col

                def key_for(d: Device) -> list[object]:
                    if col == "serial":
                        return self._natural_key(d.serial)
                    if col == "type":
                        type_code = self._normalize_code(d.device_type, kind="type")
                        disp = self._display_value(type_code, kind="type") if type_code in DEVICE_TYPES else (d.device_type or "")
                        return self._natural_key(disp)
                    if col == "model":
                        return self._natural_key(d.model or "")
                    if col == "from":
                        return self._natural_key(d.from_store or "")
                    if col == "to":
                        return self._natural_key(d.to_store or "")
                    if col == "status":
                        status_code = self._normalize_code(d.status, kind="status")
                        disp = (
                            self._display_value(status_code, kind="status")
                            if status_code in ALLOWED_STATUSES
                            else (d.status or "")
                        )
                        return self._natural_key(disp)
                    if col == "updated":
                        # ISO timestamps sort lexicographically.
                        return [d.updated_at or ""]
                    return [""]

                devices = sorted(devices, key=key_for, reverse=self._sort_desc)

            selected_iid: str | None = None
            want_serial = select_serial or self._selected_serial

            for d in devices:
                updated = (d.updated_at or "").replace("T", " ")

                # Normalize stored values (can be legacy "CODE — label" or LV/EN labels)
                type_code = self._normalize_code(d.device_type, kind="type")
                status_code = self._normalize_code(d.status, kind="status")

                type_disp = self._display_value(type_code, kind="type") if type_code in DEVICE_TYPES else (d.device_type or "")
                status_disp = (
                    self._display_value(status_code, kind="status") if status_code in ALLOWED_STATUSES else (d.status or "")
                )
                values = (
                    d.serial,
                    type_disp,
                    d.model or "",
                    d.from_store or "",
                    d.to_store or "",
                    status_disp,
                    updated,
                )
                iid = self.tree.insert("", tk.END, values=values)
                if want_serial and d.serial == want_serial:
                    selected_iid = iid

            if selected_iid:
                self.tree.selection_set(selected_iid)
                self.tree.see(selected_iid)

            self.count_lbl.config(text=self.tr("count", n=len(devices)))
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(self.tr("desktop_error_title"), str(exc))

    def _on_row_selected(self) -> None:
        sel = self.tree.selection()
        if not sel:
            return

        values = self.tree.item(sel[0], "values")
        if not values:
            return

        serial = str(values[0])
        self._selected_serial = serial
        try:
            device = self.db.get_device(serial)
            self._selected_updated_at = device.updated_at if device else None
            self._selected_created_at = device.created_at if device else None
        except Exception:
            self._selected_updated_at = None
            self._selected_created_at = None

    def _open_audit_viewer(self) -> None:
        if not self._authorize_admin_panel():
            return

        win = tk.Toplevel(self.root)
        win.title("Audit Viewer (Admin)")
        win.geometry("980x520")
        win.transient(self.root)

        frame = ttk.Frame(win, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)

        top = ttk.Frame(frame)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)

        ttk.Label(top, text="Serial filter").grid(row=0, column=0, sticky="w")
        serial_var = tk.StringVar(value=self._selected_serial or "")
        serial_entry = ttk.Entry(top, textvariable=serial_var)
        serial_entry.grid(row=0, column=1, sticky="ew", padx=(8, 8))

        limit_var = tk.StringVar(value="120")
        ttk.Entry(top, textvariable=limit_var, width=8).grid(row=0, column=2, sticky="e")

        tree = ttk.Treeview(
            frame,
            columns=("time", "op", "serial", "actor", "source"),
            show="headings",
            selectmode="browse",
        )
        tree.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
        tree.heading("time", text="Event time")
        tree.heading("op", text="Operation")
        tree.heading("serial", text="Serial")
        tree.heading("actor", text="Actor")
        tree.heading("source", text="Source")
        tree.column("time", width=190, anchor="w")
        tree.column("op", width=90, anchor="w")
        tree.column("serial", width=180, anchor="w")
        tree.column("actor", width=230, anchor="w")
        tree.column("source", width=120, anchor="w")

        details = tk.Text(frame, height=9, wrap="word", relief="solid", borderwidth=1)
        details.grid(row=3, column=0, sticky="ew", pady=(8, 0))

        status_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=status_var).grid(row=1, column=0, sticky="w", pady=(6, 0))
        status_var.set("")

        logs_cache: list[dict] = []

        def _render_details(_event: tk.Event | None = None) -> None:
            sel = tree.selection()
            if not sel:
                return
            iid = sel[0]
            try:
                idx = int(iid)
            except Exception:
                return
            if idx < 0 or idx >= len(logs_cache):
                return

            row = logs_cache[idx]
            details.configure(state="normal")
            details.delete("1.0", tk.END)
            payload = {
                "before_data": row.get("before_data"),
                "after_data": row.get("after_data"),
                "txid": row.get("txid"),
            }
            details.insert("1.0", json.dumps(payload, indent=2, ensure_ascii=False))
            details.configure(state="disabled")

        def _load() -> None:
            tree.delete(*tree.get_children())
            details.configure(state="normal")
            details.delete("1.0", tk.END)
            details.configure(state="disabled")

            serial = serial_var.get().strip() or None
            try:
                limit = int(limit_var.get().strip() or "120")
            except Exception:
                limit = 120

            try:
                rows = self.db.list_audit_logs(serial=serial, limit=limit)
            except Exception as exc:
                status_var.set(f"Audit load failed: {exc}")
                return

            logs_cache.clear()
            logs_cache.extend(rows)
            for idx, row in enumerate(rows):
                iid = str(idx)
                tree.insert(
                    "",
                    tk.END,
                    iid=iid,
                    values=(
                        str(row.get("event_time") or "").replace("T", " "),
                        row.get("operation") or "",
                        row.get("serial") or "",
                        row.get("actor") or "",
                        row.get("source") or "",
                    ),
                )
            status_var.set(f"Loaded {len(rows)} audit row(s)")

        btns = ttk.Frame(frame)
        btns.grid(row=0, column=0, sticky="e")
        ttk.Button(btns, text="Load", command=_load).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(btns, text="Close", command=win.destroy).grid(row=0, column=1)

        tree.bind("<<TreeviewSelect>>", _render_details)
        serial_entry.bind("<Return>", lambda _e: _load())
        _load()

    def _on_row_double_click(self) -> None:
        if not self._selected_serial:
            self._on_row_selected()
        if not self._selected_serial:
            return

        open_editor = self._get_open_editor()
        if open_editor is not None:
            try:
                open_editor.deiconify()
                open_editor.lift()
                open_editor.focus_force()
            except Exception:
                pass

            if getattr(open_editor, "serial", None) != self._selected_serial:
                self._write_result(
                    {"ok": False, "info": "Close current editor window before opening a different listing."},
                    ok=False,
                )
            return

        try:
            DeviceEditor(self, self._selected_serial)
        except Exception:
            messagebox.showerror(self.tr("desktop_error_title"), traceback.format_exc())

    def _on_tree_double_click(self, event: tk.Event) -> None:  # type: ignore[override]
        # Ignore double-clicks on headers (used for sorting) or empty space.
        try:
            region = self.tree.identify("region", event.x, event.y)
        except Exception:
            region = ""

        if region != "cell":
            return

        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return

        self.tree.selection_set(row_id)
        self._on_row_selected()
        self._on_row_double_click()


def run_desktop(*, db_path: str | Path = "inventory.db", lang: str = "lv") -> None:
    root = tk.Tk()
    _configure_windows_dpi(root)
    try:
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(family="Segoe UI", size=10)
        root.option_add("*Font", default_font)
    except Exception:
        pass
    DesktopApp(root, db_path=db_path, lang=lang)
    root.mainloop()
