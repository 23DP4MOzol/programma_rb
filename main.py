from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path

from i18n import load_translations, t
from inventory_db import Device, InventoryDB, format_device_table


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="programma_rb",
        description="Vienkāršs lokāls inventāra backend (SQLite) skeneriem u.c. iekārtām.",
    )
    p.add_argument(
        "--db",
        default="inventory.db",
        help="SQLite datubāzes fails (default: inventory.db)",
    )
    p.add_argument(
        "--lang",
        default="lv",
        choices=["lv", "en"],
        help="UI valoda / language (lv|en)",
    )
    p.add_argument("--host", default="127.0.0.1", help="Web UI host (for UI mode)")
    p.add_argument("--port", type=int, default=8000, help="Web UI port (for UI mode)")
    p.add_argument(
        "--no-browser",
        action="store_true",
        help="Neatver pārlūku automātiski (for UI mode)",
    )

    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("ui", help="Palaiž Desktop UI (Tkinter)")
    sub.add_parser("web", help="Palaiž Web UI (lokāli pārlūkā)")

    sub.add_parser("init", help="Izveido datubāzes tabulas (ja nav)")

    add = sub.add_parser("add", help="Pievieno jaunu ierīci")
    add.add_argument("--serial", required=True)
    add.add_argument("--type", dest="device_type", default="scanner")
    add.add_argument("--model")
    add.add_argument("--from-store", dest="from_store")
    add.add_argument("--to-store", dest="to_store")
    add.add_argument("--status", default="RECEIVED")
    add.add_argument("--comment")
    add.add_argument(
        "--overwrite",
        action="store_true",
        help="Ja serial jau eksistē, pārraksta ierakstu",
    )

    upd = sub.add_parser("update", help="Maina laukus pēc serial (daļēji)")
    upd.add_argument("--serial", required=True)
    upd.add_argument("--type", dest="device_type")
    upd.add_argument("--model")
    upd.add_argument("--from-store", dest="from_store")
    upd.add_argument("--to-store", dest="to_store")
    upd.add_argument("--status")
    upd.add_argument("--comment")

    st = sub.add_parser("status", help="Maina tikai statusu (un pēc izvēles to-store/comment)")
    st.add_argument("--serial", required=True)
    st.add_argument("--new", dest="new_status", required=True)
    st.add_argument("--to-store", dest="to_store")
    st.add_argument("--comment")

    dele = sub.add_parser("delete", help="Dzēš ierīci pēc serial")
    dele.add_argument("--serial", required=True)

    get = sub.add_parser("get", help="Parāda vienu ierīci")
    get.add_argument("--serial", required=True)

    ls = sub.add_parser("list", help="Saraksts (ar izvēles filtriem)")
    ls.add_argument("--status")
    ls.add_argument("--to-store", dest="to_store")
    ls.add_argument("--from-store", dest="from_store")
    ls.add_argument("--limit", type=int, default=200)

    return p


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    db = InventoryDB(Path(args.db))
    translations = load_translations()

    # If started without CLI command (e.g. double-click main.py), launch Desktop UI.
    if args.cmd is None:
        args.cmd = "ui"

    if args.cmd == "ui":
        from desktop_app import run_desktop  # noqa: WPS433

        print("LV: Palaižu Desktop UI... / EN: Starting Desktop UI...")
        run_desktop(db_path=str(args.db), lang=str(args.lang))
        return 0

    if args.cmd == "web":
        # Lazy import so CLI-only usage doesn't pull in HTTP server.
        from web_app import run  # noqa: WPS433

        url = f"http://{args.host}:{args.port}/"
        print("LV: Palaižu Web UI... / EN: Starting Web UI...")
        print(url)
        if not args.no_browser:
            try:
                webbrowser.open(url)
            except Exception:
                pass
        run(args.host, int(args.port), str(args.db))
        return 0

    if args.cmd == "init":
        db.init_db()
        print(t(translations, "db_initialized", lang=args.lang, path=args.db))
        return 0

    # Ensure schema exists for all other commands
    db.init_db()

    if args.cmd == "add":
        device = Device(
            serial=args.serial,
            device_type=args.device_type,
            model=args.model,
            from_store=args.from_store,
            to_store=args.to_store,
            status=args.status,
            comment=args.comment,
        )
        db.add_device(device, overwrite=bool(args.overwrite))
        print(t(translations, "ok_added", lang=args.lang))
        return 0

    if args.cmd == "update":
        changed = db.update_device(
            args.serial,
            device_type=args.device_type,
            model=args.model,
            from_store=args.from_store,
            to_store=args.to_store,
            status=args.status,
            comment=args.comment,
        )
        if not changed:
            print(t(translations, "not_found_or_no_fields", lang=args.lang))
            return 2
        print(t(translations, "ok_updated", lang=args.lang))
        return 0

    if args.cmd == "status":
        changed = db.change_status(
            args.serial,
            args.new_status,
            to_store=args.to_store,
            comment=args.comment,
        )
        if not changed:
            print(t(translations, "not_found", lang=args.lang))
            return 2
        print(t(translations, "ok_status_changed", lang=args.lang))
        return 0

    if args.cmd == "delete":
        deleted = db.delete_device(args.serial)
        if not deleted:
            print(t(translations, "not_found", lang=args.lang))
            return 2
        print(t(translations, "ok_deleted", lang=args.lang))
        return 0

    if args.cmd == "get":
        d = db.get_device(args.serial)
        if not d:
            print(t(translations, "not_found", lang=args.lang))
            return 2
        print(format_device_table([d]))
        return 0

    if args.cmd == "list":
        devices = db.list_devices(
            status=args.status,
            to_store=args.to_store,
            from_store=args.from_store,
            limit=args.limit,
        )
        print(format_device_table(devices))
        print("\n" + t(translations, "count", lang=args.lang, n=len(devices)))
        return 0

    raise AssertionError(f"Unhandled cmd: {args.cmd}")


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as exc:  # noqa: BLE001
        try:
            translations = load_translations()
            print(t(translations, "error", lang="lv", msg=str(exc)), file=sys.stderr)
            print(t(translations, "error", lang="en", msg=str(exc)), file=sys.stderr)
        except Exception:
            print(f"ERROR: {exc}", file=sys.stderr)
        raise
