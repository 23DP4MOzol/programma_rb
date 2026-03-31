import json
import flet as ft
from supabase_db import InventoryDB, Device

SERIAL_PREFIX_MAP: dict[str, tuple[str, str, str]] = {
    # Prefix: ("device_type", "Make", "Make Model")
    # Zebra scanners often start with these (edit to match your actual fleet)
    "19": ("scanner", "Zebra", "Zebra TC52"),
    "20": ("scanner", "Zebra", "Zebra TC52"),
    "17": ("scanner", "Zebra", "Zebra TC51"),
    "18": ("scanner", "Zebra", "Zebra TC51"),
    "21": ("scanner", "Zebra", "Zebra TC57"),
    "40": ("scanner", "Zebra", "Zebra MC3300"),
    "PF": ("laptop", "Lenovo", "Lenovo ThinkPad"),
    "PC": ("laptop", "Lenovo", "Lenovo ThinkPad"),
}

def main(page: ft.Page):
    page.title = "Rimi Scanner App"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 12

    pending_key = "pending_devices"
    config_key = "app_config"

    config_defaults = {
        "supabase_url": "https://qvlduxpdcwgmokjdsdfp.supabase.co",
        "supabase_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF2bGR1eHBkY3dnbW9ramRzZGZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ5Mzk5MzMsImV4cCI6MjA5MDUxNTkzM30.3HiNhJKLrMmc0I11Y7qMS73fi0b1XUaEorTAL6wJOsk",
        "lang": "lv",
        "pin": "",
        "prefix_rules": "",
    }

    def _load_config() -> dict:
        try:
            stored = page.client_storage.get(config_key)
        except Exception:
            stored = None

        if isinstance(stored, dict):
            cfg = {**config_defaults, **stored}
        else:
            cfg = dict(config_defaults)
        return cfg

    def _save_config(cfg: dict) -> None:
        try:
            page.client_storage.set(config_key, cfg)
        except Exception:
            pass

    config = _load_config()
    lang = config.get("lang", "lv")
    pin_code = ""
    pin_verified = False

    db = InventoryDB(url=config.get("supabase_url"), key=config.get("supabase_key"))
    
    STRINGS = {
        "lv": {
            "title": "Rimi Iekartu Skeneris",
            "serial": "Skenet / Ievadit Serial (Scan Here)",
            "type": "Tips",
            "make": "Razotajs (Make)",
            "model": "Modelis",
            "status": "Statuss",
            "from": "No veikala (From)",
            "to": "Uz veikalu (To)",
            "comment": "Komentars",
            "overwrite": "Overwrite existing device",
            "bulk_scan": "Bulk scan mode",
            "register": "Registrer jaunu ierici",
            "save": "Saglabat / Atjaunot",
            "sync": "Sync now",
            "config": "Iestatijumi",
            "supabase_url": "Supabase URL",
            "supabase_key": "Supabase Key",
            "language": "Valoda",
            "pin": "Admin PIN",
            "save_config": "Saglabat iestatijumus",
            "camera_scan": "Camera scan",
            "prefix_rules": "Prefix noteikumi (JSON)",
            "section_actions": "Darbibas",
            "section_controls": "Kontrole",
            "section_settings": "Iestatijumi",
        },
        "en": {
            "title": "Rimi Device Scanner",
            "serial": "Scan / Enter Serial (Scan Here)",
            "type": "Type",
            "make": "Make",
            "model": "Model",
            "status": "Status",
            "from": "From store",
            "to": "To store",
            "comment": "Comment",
            "overwrite": "Overwrite existing device",
            "bulk_scan": "Bulk scan mode",
            "register": "Register new device",
            "save": "Save / Update",
            "sync": "Sync now",
            "config": "Settings",
            "supabase_url": "Supabase URL",
            "supabase_key": "Supabase Key",
            "language": "Language",
            "pin": "Admin PIN",
            "save_config": "Save settings",
            "camera_scan": "Camera scan",
            "prefix_rules": "Prefix rules (JSON)",
            "section_actions": "Actions",
            "section_controls": "Controls",
            "section_settings": "Settings",
        },
    }

    def tr(key: str) -> str:
        return STRINGS.get(lang, STRINGS["en"]).get(key, key)

    def _get_prefix_rules() -> dict[str, tuple[str, str, str]]:
        merged = dict(SERIAL_PREFIX_MAP)
        raw = (config or {}).get("prefix_rules")
        if not raw:
            return merged
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, (list, tuple)) and len(v) == 3:
                        merged[str(k)] = (str(v[0]), str(v[1]), str(v[2]))
        except Exception:
            pass
        return merged

    # UI Elements
    result_text = ft.Text("", color=ft.colors.GREEN, size=12)
    new_device_text = ft.Text("", color=ft.colors.AMBER, size=12)
    header_text = ft.Text(tr("title"), size=20, weight=ft.FontWeight.BOLD)

    serial_input = ft.TextField(label=tr("serial"), autofocus=True, text_size=16)
    type_dropdown = ft.Dropdown(
        label=tr("type"),
        options=[
            ft.dropdown.Option("scanner"),
            ft.dropdown.Option("laptop"),
            ft.dropdown.Option("tablet"),
            ft.dropdown.Option("phone"),
            ft.dropdown.Option("other"),
        ],
        value="scanner"
    )
    make_input = ft.TextField(label=tr("make"))
    model_input = ft.TextField(label=tr("model"))
    status_dropdown = ft.Dropdown(
        label=tr("status"),
        options=[
            ft.dropdown.Option("RECEIVED"),
            ft.dropdown.Option("PREPARING"),
            ft.dropdown.Option("PREPARED"),
            ft.dropdown.Option("SENT"),
            ft.dropdown.Option("IN_USE"),
            ft.dropdown.Option("RETURNED"),
            ft.dropdown.Option("RETIRED"),
        ],
        value="RECEIVED"
    )
    from_store_input = ft.TextField(label=tr("from"))
    to_store_input = ft.TextField(label=tr("to"))
    comment_input = ft.TextField(label=tr("comment"))
    overwrite_checkbox = ft.Checkbox(label=tr("overwrite"), value=False)
    bulk_scan_checkbox = ft.Checkbox(label=tr("bulk_scan"), value=False)

    def _split_make_model(model_text: str) -> tuple[str, str]:
        text = model_text.strip()
        if not text:
            return "", ""
        if " " in text:
            parts = text.split(" ", 1)
            return parts[0], parts[1]
        return text, ""

    def _apply_prefill(device_type: str, make: str, model: str) -> None:
        type_dropdown.value = device_type
        make_input.value = make
        model_input.value = model

    def _set_new_device_state(active: bool, message: str | None = None) -> None:
        register_btn.visible = active
        register_btn.disabled = not active
        new_device_text.value = message or ""

    def _after_save() -> None:
        serial_input.value = ""
        serial_input.focus()
        if not bulk_scan_checkbox.value:
            return
        # Keep the rest of the fields for rapid consecutive scans

    def _apply_language() -> None:
        nonlocal lang
        page.title = tr("title")
        header_text.value = tr("title")
        actions_title.value = tr("section_actions")
        controls_title.value = tr("section_controls")
        serial_input.label = tr("serial")
        type_dropdown.label = tr("type")
        make_input.label = tr("make")
        model_input.label = tr("model")
        status_dropdown.label = tr("status")
        from_store_input.label = tr("from")
        to_store_input.label = tr("to")
        comment_input.label = tr("comment")
        overwrite_checkbox.label = tr("overwrite")
        bulk_scan_checkbox.label = tr("bulk_scan")
        register_btn.text = tr("register")
        btn_save.text = tr("save")
        sync_btn.text = tr("sync")
        scan_btn.text = tr("camera_scan")
        config_title.value = tr("config")
        config_url_input.label = tr("supabase_url")
        config_key_input.label = tr("supabase_key")
        config_lang_dropdown.label = tr("language")
        config_pin_input.label = tr("pin")
        prefix_rules_input.label = tr("prefix_rules")
        config_save_btn.text = tr("save_config")

    def _get_pending() -> list[dict]:
        try:
            pending = page.client_storage.get(pending_key)
        except Exception:
            return []
        if isinstance(pending, list):
            return pending
        return []

    def _save_pending(items: list[dict]) -> None:
        try:
            page.client_storage.set(pending_key, items)
        except Exception:
            pass

    def _device_to_payload(device: Device) -> dict:
        return {
            "serial": device.serial,
            "device_type": device.device_type,
            "model": device.model or "",
            "from_store": device.from_store or "",
            "to_store": device.to_store or "",
            "status": device.status,
            "comment": device.comment or "",
        }

    def _enqueue_pending(payload: dict) -> None:
        pending = _get_pending()
        pending.append(payload)
        _save_pending(pending)

    def _flush_pending() -> tuple[int, int]:
        pending = _get_pending()
        if not pending:
            return 0, 0

        remaining: list[dict] = []
        synced = 0
        for item in pending:
            try:
                db.add_device(Device(**item), overwrite=True)
                synced += 1
            except Exception:
                remaining.append(item)

        _save_pending(remaining)
        return synced, len(remaining)

    def load_device(e):
        serial = serial_input.value.strip()
        if not serial:
            return
            
        try:
            device = db.get_device(serial)
        except Exception as exc:
            pending = _get_pending()
            pending_match = next((p for p in pending if p.get("serial") == serial), None)
            if pending_match:
                overwrite_checkbox.value = True
                type_dropdown.value = pending_match.get("device_type") or "scanner"
                status_dropdown.value = pending_match.get("status") or "RECEIVED"
                from_store_input.value = pending_match.get("from_store") or ""
                to_store_input.value = pending_match.get("to_store") or ""
                comment_input.value = pending_match.get("comment") or ""
                make_val, model_val = _split_make_model(pending_match.get("model") or "")
                make_input.value = make_val
                model_input.value = model_val
                _set_new_device_state(False)
                result_text.value = f"Offline: loaded local device ({serial})"
                result_text.color = ft.colors.ORANGE
                page.update()
                return

            result_text.value = f"Offline: {exc}"
            result_text.color = ft.colors.RED
            page.update()
            return
            
        if device:
            overwrite_checkbox.value = True
            type_dropdown.value = device.device_type
            status_dropdown.value = device.status
            from_store_input.value = device.from_store or ""
            to_store_input.value = device.to_store or ""
            comment_input.value = device.comment or ""

            make_val, model_val = _split_make_model(device.model or "")
            make_input.value = make_val
            model_input.value = model_val
                
            _set_new_device_state(False)
            result_text.value = f"Iekārta atrasta! ({serial})"
            result_text.color = ft.colors.BLUE
        else:
            overwrite_checkbox.value = False
            # Try prefix rules for new devices
            upper_scan = serial.upper()
            for prefix, (guess_type, guess_make, guess_model) in _get_prefix_rules().items():
                if upper_scan.startswith(prefix.upper()):
                    make_val, model_val = _split_make_model(guess_model)
                    _apply_prefill(guess_type, make_val, model_val)
                    _set_new_device_state(True, "New device detected. Tap 'Register' to add.")
                    result_text.value = f"Auto-detected: {guess_make} {guess_model} (Rule: '{prefix}')"
                    result_text.color = ft.colors.GREEN
                    page.update()
                    return

            # Smart learning: guess by similar serial prefix from database
            try:
                all_devs = db.list_devices()
                if len(serial) >= 4:
                    prefix3 = upper_scan[:3]
                    matches = [d for d in all_devs if (d.serial or "").upper().startswith(prefix3)]
                    if matches:
                        from collections import Counter

                        common = Counter([d.model for d in matches if d.model]).most_common(1)
                        if common:
                            guessed_model = common[0][0]
                            make_val, model_val = _split_make_model(guessed_model)
                            _apply_prefill(matches[0].device_type, make_val, model_val)
                            _set_new_device_state(True, "New device detected. Tap 'Register' to add.")
                            result_text.value = f"Auto-guessed from '{prefix3}'"
                            result_text.color = ft.colors.GREEN
                            page.update()
                            return
            except Exception:
                pass

            result_text.value = "New device. Please fill in details."
            _set_new_device_state(True, "New device detected. Tap 'Register' to add.")
            result_text.color = ft.colors.YELLOW
            
        page.update()

    def save_device(e):
        serial = serial_input.value.strip()
        if not serial:
            result_text.value = "Kļūda: Serial ir obligāts"
            result_text.color = ft.colors.RED
            page.update()
            return

        # PIN disabled for stability on older devices.

        if not overwrite_checkbox.value:
            try:
                existing = db.get_device(serial)
            except Exception as exc:
                result_text.value = f"Kļūda: {exc}"
                result_text.color = ft.colors.RED
                page.update()
                return
            if existing:
                result_text.value = "Iekārta jau eksistē. Ieslēdziet Overwrite."
                result_text.color = ft.colors.ORANGE
                page.update()
                return
            
        make = make_input.value.strip()
        model_text = model_input.value.strip()
        
        full_model = model_text
        if make and model_text:
            full_model = f"{make} {model_text}"
        elif make:
            full_model = make
            
        dev = Device(
            serial=serial,
            device_type=type_dropdown.value,
            model=full_model,
            from_store=from_store_input.value.strip(),
            to_store=to_store_input.value.strip(),
            status=status_dropdown.value,
            comment=comment_input.value.strip()
        )
        
        try:
            db.add_device(dev, overwrite=bool(overwrite_checkbox.value))
            synced, remaining = _flush_pending()
            _set_new_device_state(False)
            if synced:
                result_text.value = f"Saved. Synced {synced}, pending {remaining}."
            else:
                result_text.value = "Saglabāts veiksmīgi!"
            result_text.color = ft.colors.GREEN

            _after_save()

        except Exception as exc:
            _enqueue_pending(_device_to_payload(dev))
            result_text.value = f"Offline: saved locally ({exc})"
            result_text.color = ft.colors.ORANGE
            _after_save()
            
        page.update()

    # When scanner presses 'Enter' (on_submit), load device details
    serial_input.on_submit = load_device

    def start_camera_scan(_e):
        result_text.value = "Camera scanner not available"
        result_text.color = ft.colors.ORANGE
        page.update()

    def sync_now(_e):
        synced, remaining = _flush_pending()
        if synced or remaining:
            result_text.value = f"Sync done: {synced} sent, {remaining} pending."
            result_text.color = ft.colors.GREEN if remaining == 0 else ft.colors.ORANGE
        else:
            result_text.value = "No pending offline items."
            result_text.color = ft.colors.GREEN
        page.update()

    actions_title = ft.Text(tr("section_actions"), size=14, weight=ft.FontWeight.BOLD)
    controls_title = ft.Text(tr("section_controls"), size=14, weight=ft.FontWeight.BOLD)
    config_url_input = ft.TextField(label=tr("supabase_url"), value=config.get("supabase_url", ""))
    config_key_input = ft.TextField(
        label=tr("supabase_key"),
        value=config.get("supabase_key", ""),
        password=True,
        can_reveal_password=True,
    )
    config_lang_dropdown = ft.Dropdown(
        label=tr("language"),
        options=[ft.dropdown.Option("lv"), ft.dropdown.Option("en")],
        value=lang,
    )
    config_pin_input = ft.TextField(
        label=tr("pin"),
        value=pin_code,
        password=True,
        can_reveal_password=True,
    )
    prefix_rules_input = ft.TextField(
        label=tr("prefix_rules"),
        value=config.get("prefix_rules", ""),
        multiline=True,
        min_lines=3,
        max_lines=6,
    )

    def save_config(_e):
        nonlocal config, db, lang, pin_code, pin_verified
        config = {
            "supabase_url": config_url_input.value.strip(),
            "supabase_key": config_key_input.value.strip(),
            "lang": config_lang_dropdown.value or "lv",
            "pin": "",
            "prefix_rules": prefix_rules_input.value.strip(),
        }
        _save_config(config)
        lang = config["lang"]
        pin_code = ""
        pin_verified = False
        db = InventoryDB(url=config.get("supabase_url"), key=config.get("supabase_key"))
        _apply_language()
        result_text.value = "Settings saved"
        result_text.color = ft.colors.GREEN
        page.update()

    config_save_btn = ft.ElevatedButton(tr("save_config"), on_click=save_config, width=float('inf'))

    settings_panel = ft.Column(
        [
            config_title,
            config_url_input,
            config_key_input,
            config_lang_dropdown,
            config_pin_input,
            prefix_rules_input,
            config_save_btn,
        ],
        spacing=8,
        visible=False,
    )

    def toggle_settings(_e):
        settings_panel.visible = not settings_panel.visible
        page.update()

    settings_toggle_btn = ft.ElevatedButton(
        tr("section_settings"),
        on_click=toggle_settings,
        width=float('inf'),
    )

    # PIN dialog removed for stability on older devices.

    button_height = 44

    scan_btn = ft.ElevatedButton(
        tr("camera_scan"),
        on_click=start_camera_scan,
        expand=True,
        height=button_height,
        bgcolor=ft.colors.BLUE_700,
        color=ft.colors.WHITE,
    )
    scan_btn.disabled = True

    register_btn = ft.ElevatedButton(
        tr("register"),
        on_click=save_device,
        width=float('inf'),
        height=button_height,
        bgcolor=ft.colors.GREEN_700,
        color=ft.colors.WHITE,
        visible=False,
        disabled=True,
    )
    sync_btn = ft.ElevatedButton(
        tr("sync"),
        on_click=sync_now,
        expand=True,
        height=button_height,
        bgcolor=ft.colors.BLUE_700,
        color=ft.colors.WHITE,
    )
    btn_save = ft.ElevatedButton(
        tr("save"),
        on_click=save_device,
        width=float('inf'),
        height=button_height,
        bgcolor=ft.colors.RED_700,
        color=ft.colors.WHITE,
    )

    # Scrollable column for smaller screens
    content = ft.Column(
        [
            header_text,
            serial_input,
            ft.Row([scan_btn, sync_btn], spacing=8),
            result_text,
            new_device_text,
            actions_title,
            type_dropdown,
            make_input,
            model_input,
            status_dropdown,
            from_store_input,
            to_store_input,
            comment_input,
            controls_title,
            overwrite_checkbox,
            bulk_scan_checkbox,
            register_btn,
            btn_save,
            settings_toggle_btn,
            settings_panel,
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        spacing=8,
    )
    
    _apply_language()
    page.add(content)

    initial_synced, remaining = _flush_pending()
    if initial_synced or remaining:
        result_text.value = f"Startup sync: {initial_synced} sent, {remaining} pending."
        result_text.color = ft.colors.GREEN if remaining == 0 else ft.colors.ORANGE
        page.update()

if __name__ == "__main__":
    ft.app(target=main)
