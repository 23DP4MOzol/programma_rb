from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Literal


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
    """Vienkāršs lokāls 'backend' SQLite datubāzei.

    Galvenais identifikators ir `serial` (unikāls).
    """

    def __init__(self, db_path: str | Path = "inventory.db") -> None:
        self.db_path = str(db_path)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    serial TEXT NOT NULL UNIQUE,
                    device_type TEXT NOT NULL,
                    model TEXT,
                    from_store TEXT,
                    to_store TEXT,
                    status TEXT NOT NULL,
                    comment TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_devices_to_store ON devices(to_store)")

    def add_device(self, device: Device, *, overwrite: bool = False) -> None:
        """Pievieno jaunu iekārtu. Ja `overwrite=True`, tad pārraksta pēc serial."""
        self._validate_serial(device.serial)
        self._validate_status(device.status)

        created_at = device.created_at or _utc_now_iso()
        updated_at = device.updated_at or created_at

        payload = {
            **asdict(device),
            "created_at": created_at,
            "updated_at": updated_at,
        }

        columns = [
            "serial",
            "device_type",
            "model",
            "from_store",
            "to_store",
            "status",
            "comment",
            "created_at",
            "updated_at",
        ]
        values = [payload[c] for c in columns]

        with self.connect() as conn:
            if overwrite:
                conn.execute(
                    """
                    INSERT INTO devices (serial, device_type, model, from_store, to_store, status, comment, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(serial) DO UPDATE SET
                        device_type=excluded.device_type,
                        model=excluded.model,
                        from_store=excluded.from_store,
                        to_store=excluded.to_store,
                        status=excluded.status,
                        comment=excluded.comment,
                        updated_at=excluded.updated_at
                    """,
                    values,
                )
            else:
                conn.execute(
                    """
                    INSERT INTO devices (serial, device_type, model, from_store, to_store, status, comment, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    values,
                )

    def delete_device(self, serial: str) -> bool:
        """Dzēš pēc serial. Atgriež True, ja kaut kas tika izdzēsts."""
        self._validate_serial(serial)
        with self.connect() as conn:
            cur = conn.execute("DELETE FROM devices WHERE serial = ?", (serial.strip(),))
            return cur.rowcount > 0

    def get_device(self, serial: str) -> Device | None:
        self._validate_serial(serial)
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM devices WHERE serial = ?", (serial.strip(),)).fetchone()
        return self._row_to_device(row) if row else None

    def list_devices(
        self,
        *,
        status: str | None = None,
        device_type: str | None = None,
        serial: str | None = None,
        make: str | None = None,
        model: str | None = None,
        to_store: str | None = None,
        from_store: str | None = None,
        limit: int = 200,
    ) -> list[Device]:
        make_expr = (
            "CASE "
            "WHEN model IS NULL THEN '' "
            "WHEN TRIM(model) = '' THEN '' "
            "WHEN INSTR(TRIM(model), ' ') = 0 THEN TRIM(model) "
            "ELSE SUBSTR(TRIM(model), 1, INSTR(TRIM(model), ' ') - 1) "
            "END"
        )

        where = []
        params: list[Any] = []

        if status is not None:
            self._validate_status(status)
            where.append("status = ?")
            params.append(status)

        if serial is not None:
            where.append("serial LIKE ?")
            params.append(f"%{serial}%")

        if device_type is not None:
            where.append("device_type = ?")
            params.append(device_type)

        if make is not None:
            where.append(f"LOWER({make_expr}) = LOWER(?)")
            params.append(make)

        if model is not None:
            # Partial match; SQLite LIKE is case-insensitive for ASCII by default.
            where.append("model LIKE ?")
            params.append(f"%{model}%")

        if to_store is not None:
            where.append("to_store = ?")
            params.append(to_store)

        if from_store is not None:
            where.append("from_store = ?")
            params.append(from_store)

        where_sql = (" WHERE " + " AND ".join(where)) if where else ""
        limit = max(1, min(int(limit), 2000))

        with self.connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM devices{where_sql} ORDER BY updated_at DESC LIMIT ?",
                (*params, limit),
            ).fetchall()

        return [self._row_to_device(r) for r in rows]

    def list_makes(self, *, device_type: str | None = None) -> list[str]:
        """Returns distinct 'make' values derived from `model`.

        We don't store make separately; it's derived as the first token of `model`.
        """

        make_expr = (
            "CASE "
            "WHEN model IS NULL THEN '' "
            "WHEN TRIM(model) = '' THEN '' "
            "WHEN INSTR(TRIM(model), ' ') = 0 THEN TRIM(model) "
            "ELSE SUBSTR(TRIM(model), 1, INSTR(TRIM(model), ' ') - 1) "
            "END"
        )

        where = ["model IS NOT NULL", "TRIM(model) <> ''"]
        params: list[Any] = []
        if device_type is not None:
            where.append("device_type = ?")
            params.append(device_type)

        where_sql = " WHERE " + " AND ".join(where)

        with self.connect() as conn:
            rows = conn.execute(
                f"SELECT DISTINCT {make_expr} AS make FROM devices{where_sql}",
                tuple(params),
            ).fetchall()

        raw = [str(r["make"]).strip() for r in rows if str(r["make"]).strip()]

        # Case-insensitive de-duplication (keep first-seen original casing).
        seen: dict[str, str] = {}
        for item in raw:
            key = item.casefold()
            if key not in seen:
                seen[key] = item

        makes = sorted(seen.values(), key=lambda s: s.casefold())
        return makes

    def list_models(self, *, device_type: str | None = None, make: str | None = None) -> list[str]:
        """Returns distinct full `model` strings, optionally filtered by type and derived make."""

        make_expr = (
            "CASE "
            "WHEN model IS NULL THEN '' "
            "WHEN TRIM(model) = '' THEN '' "
            "WHEN INSTR(TRIM(model), ' ') = 0 THEN TRIM(model) "
            "ELSE SUBSTR(TRIM(model), 1, INSTR(TRIM(model), ' ') - 1) "
            "END"
        )

        where = ["model IS NOT NULL", "TRIM(model) <> ''"]
        params: list[Any] = []
        if device_type is not None:
            where.append("device_type = ?")
            params.append(device_type)
        if make is not None:
            where.append(f"LOWER({make_expr}) = LOWER(?)")
            params.append(make)

        where_sql = " WHERE " + " AND ".join(where)
        with self.connect() as conn:
            rows = conn.execute(
                f"SELECT DISTINCT TRIM(model) AS model FROM devices{where_sql}",
                tuple(params),
            ).fetchall()

        raw = [str(r["model"]).strip() for r in rows if str(r["model"]).strip()]

        # Case-insensitive de-duplication (keep first-seen original casing).
        seen: dict[str, str] = {}
        for item in raw:
            key = item.casefold()
            if key not in seen:
                seen[key] = item

        models = sorted(seen.values(), key=lambda s: s.casefold())
        return models

    def update_device(self, serial: str, **fields: Any) -> bool:
        """Maina jebkurus laukus pēc serial (daļējs update).

        Atļautie lauki: device_type, model, from_store, to_store, status, comment.
        Atgriež True, ja atrada un atjaunoja ierakstu.
        """
        self._validate_serial(serial)

        allowed = {"device_type", "model", "from_store", "to_store", "status", "comment"}
        unknown = set(fields) - allowed
        if unknown:
            raise ValueError(f"Unknown fields: {sorted(unknown)}")

        if "status" in fields and fields["status"] is not None:
            self._validate_status(str(fields["status"]))

        updates = []
        params: list[Any] = []
        for key, value in fields.items():
            if value is None:
                continue
            updates.append(f"{key} = ?")
            params.append(value)

        if not updates:
            return False

        updates.append("updated_at = ?")
        params.append(_utc_now_iso())

        params.append(serial.strip())
        sql = f"UPDATE devices SET {', '.join(updates)} WHERE serial = ?"

        with self.connect() as conn:
            cur = conn.execute(sql, tuple(params))
            return cur.rowcount > 0

    def change_status(
        self,
        serial: str,
        new_status: Status | str,
        *,
        to_store: str | None = None,
        comment: str | None = None,
    ) -> bool:
        """Maina statusu (un pēc vajadzības mērķa veikalu / komentāru)."""
        self._validate_serial(serial)
        self._validate_status(str(new_status))

        payload: dict[str, Any] = {"status": str(new_status)}
        if to_store is not None:
            payload["to_store"] = to_store
        if comment is not None:
            payload["comment"] = comment

        return self.update_device(serial, **payload)

    def _validate_serial(self, serial: str) -> None:
        if not isinstance(serial, str) or not serial.strip():
            raise ValueError("serial must be a non-empty string")

    def _validate_status(self, status: str) -> None:
        if status not in ALLOWED_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Allowed: {sorted(ALLOWED_STATUSES)}")

    def _row_to_device(self, row: sqlite3.Row) -> Device:
        return Device(
            serial=row["serial"],
            device_type=row["device_type"],
            model=row["model"],
            from_store=row["from_store"],
            to_store=row["to_store"],
            status=row["status"],
            comment=row["comment"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


def format_device_table(devices: Iterable[Device]) -> str:
    """Vienkārša teksta tabula (bez ārējām bibliotekām)."""
    rows = [
        [
            d.serial,
            d.device_type,
            d.model or "",
            d.from_store or "",
            d.to_store or "",
            d.status,
            (d.updated_at or ""),
        ]
        for d in devices
    ]
    headers = ["serial", "type", "model", "from", "to", "status", "updated_at"]

    all_rows = [headers, *rows]
    widths = [max(len(str(r[i])) for r in all_rows) for i in range(len(headers))]

    def fmt(r: list[str]) -> str:
        return " | ".join(str(r[i]).ljust(widths[i]) for i in range(len(headers)))

    sep = "-+-".join("-" * w for w in widths)

    if not rows:
        return fmt(headers) + "\n" + sep

    return "\n".join([fmt(headers), sep, *[fmt(r) for r in rows]])
