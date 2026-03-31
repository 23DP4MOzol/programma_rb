from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Literal

from supabase import create_client, Client

Status = Literal[
    "RECEIVED",
    "PREPARING",
    "PREPARED",
    "SENT",
    "IN_USE",
    "RETURNED",
    "RETIRED",
]

ALLOWED_STATUSES: set[str] = {
    "RECEIVED",
    "PREPARING",
    "PREPARED",
    "SENT",
    "IN_USE",
    "RETURNED",
    "RETIRED",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class Device:
    serial: str
    device_type: str = "scanner"
    model: str | None = None
    from_store: str | None = None
    to_store: str | None = None
    status: str = "RECEIVED"
    comment: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

class InventoryDB:
    """Supabase Backend Database for multiple scanners."""

    def __init__(self, db_path: str | Path = "inventory.db") -> None:
        self.url = "https://qvlduxpdcwgmokjdsdfp.supabase.co"
        self.key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF2bGR1eHBkY3dnbW9ramRzZGZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ5Mzk5MzMsImV4cCI6MjA5MDUxNTkzM30.3HiNhJKLrMmc0I11Y7qMS73fi0b1XUaEorTAL6wJOsk"
        self.supabase: Client = create_client(self.url, self.key)

    def init_db(self) -> None:
        """With Supabase, no local init needed if table already deployed."""
        pass

    def _validate_serial(self, serial: str) -> None:
        if not serial or not serial.strip():
            raise ValueError("Serial field is required")

    def _validate_status(self, status: str) -> None:
        if status not in ALLOWED_STATUSES:
            raise ValueError(f"Invalid status: {status}")

    def add_device(self, device: Device, *, overwrite: bool = False) -> None:
        self._validate_serial(device.serial)
        self._validate_status(device.status)

        created_at = device.created_at or _utc_now_iso()
        updated_at = device.updated_at or created_at

        # Supabase API dict
        payload = {
            "serial": device.serial,
            "device_type": device.device_type,
            "model": device.model or "",
            "from_store": device.from_store or "",
            "to_store": device.to_store or "",
            "status": device.status,
            "comment": device.comment or "",
            "created_at": created_at,
            "updated_at": updated_at,
        }

        # Check existence if not overwriting
        existing = self.get_device(device.serial)
        if existing and not overwrite:
            raise ValueError(f"Device with serial '{device.serial}' already exists.")

        self.supabase.table("devices").upsert(payload).execute()

    def update_device(
        self,
        serial: str,
        *,
        device_type: str | None = None,
        model: str | None = None,
        from_store: str | None = None,
        to_store: str | None = None,
        status: str | None = None,
        comment: str | None = None,
    ) -> bool:
        self._validate_serial(serial)
        
        updates: dict[str, Any] = {"updated_at": _utc_now_iso()}
        if device_type is not None:
            updates["device_type"] = device_type
        if model is not None:
            updates["model"] = model
        if from_store is not None:
            updates["from_store"] = from_store
        if to_store is not None:
            updates["to_store"] = to_store
        if status is not None:
            self._validate_status(status)
            updates["status"] = status
        if comment is not None:
            updates["comment"] = comment

        res = self.supabase.table("devices").update(updates).eq("serial", serial).execute()
        return len(res.data) > 0

    def change_status(
        self,
        serial: str,
        status: str,
        *,
        to_store: str | None = None,
        comment: str | None = None,
    ) -> bool:
        self._validate_serial(serial)
        self._validate_status(status)

        updates: dict[str, Any] = {
            "status": status,
            "updated_at": _utc_now_iso(),
        }
        if to_store is not None:
            updates["to_store"] = to_store
        if comment is not None:
            updates["comment"] = comment

        res = self.supabase.table("devices").update(updates).eq("serial", serial).execute()
        return len(res.data) > 0

    def delete_device(self, serial: str) -> bool:
        self._validate_serial(serial)
        res = self.supabase.table("devices").delete().eq("serial", serial).execute()
        return len(res.data) > 0

    def get_device(self, serial: str) -> Device | None:
        self._validate_serial(serial)
        res = self.supabase.table("devices").select("*").eq("serial", serial).execute()
        if res.data:
            return self._row_to_device(res.data[0])
        return None

    def list_devices(
        self,
        *,
        status: str | None = None,
        device_type: str | None = None,
        serial: str | None = None,
        make: str | None = None,  # Computed offline for now if we can't reliably do SQL
        model: str | None = None,
        to_store: str | None = None,
        from_store: str | None = None,
        limit: int = 200,
    ) -> list[Device]:
        
        query = self.supabase.table("devices").select("*")
        
        if status:
            self._validate_status(status)
            query = query.eq("status", status)
        if device_type:
            query = query.eq("device_type", device_type)
        if serial:
            query = query.ilike("serial", f"%{serial}%")
        if model:
            query = query.ilike("model", f"%{model}%")
        if to_store:
            query = query.eq("to_store", to_store)
        if from_store:
            query = query.eq("from_store", from_store)

        if str(limit).isdigit() and int(limit) > 0:
            query = query.order("updated_at", desc=True).limit(int(limit))
        res = query.execute()

        all_devices = [self._row_to_device(row) for row in res.data]

        # Supabase API does not support native string manipulation in Python query.
        # Filter "Make" locally. Make is derived from the first word of the model
        if make:
            filtered = []
            for d in all_devices:
                make_val = ""
                m = d.model or ""
                m = m.strip()
                if " " in m:
                    make_val = m.split(" ", 1)[0]
                else:
                    make_val = m
                if make_val.casefold() == make.casefold():
                    filtered.append(d)
            return filtered

        return all_devices

    def list_makes(self, *, device_type: str | None = None) -> list[str]:
        # Same concept. Fetch models, compute makes.
        query = self.supabase.table("devices").select("model")
        if device_type:
            query = query.eq("device_type", device_type)
        
        res = query.execute()
        makes = set()
        for r in res.data:
            m = r.get("model", "") or ""
            m = m.strip()
            if m:
                if " " in m:
                    make = m.split(" ", 1)[0]
                else:
                    make = m
                if make:
                    makes.add(make)
        
        return sorted(list(makes), key=lambda x: x.casefold())

    def list_models(self, *, device_type: str | None = None, make: str | None = None) -> list[str]:
        query = self.supabase.table("devices").select("model")
        if device_type:
            query = query.eq("device_type", device_type)

        res = query.execute()
        models = set()
        for r in res.data:
            m = r.get("model", "") or ""
            m = m.strip()
            if not m:
                continue

            # Check if this matches the "make"
            make_val = ""
            if " " in m:
                make_val = m.split(" ", 1)[0]
            else:
                make_val = m

            if make and make_val.casefold() != make.casefold():
                continue
            
            models.add(m)
            
        return sorted(list(models), key=lambda x: x.casefold())

    def _row_to_device(self, row: dict[str, Any]) -> Device:
        return Device(
            serial=row["serial"],
            device_type=row.get("device_type") or "scanner",
            model=row.get("model") or None,
            from_store=row.get("from_store") or None,
            to_store=row.get("to_store") or None,
            status=row.get("status") or "RECEIVED",
            comment=row.get("comment") or None,
            created_at=row.get("created_at") or None,
            updated_at=row.get("updated_at") or None,
        )
