import flet as ft
from supabase_db import InventoryDB, Device

SERIAL_PREFIX_MAP: dict[str, tuple[str, str, str]] = {
    # Prefix: ("device_type", "Make", "Make Model")
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
    page.title = "Rimi Inventory"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 12

    db = InventoryDB()

    # UI Elements
    result_text = ft.Text("", color=ft.colors.GREEN, size=12)
    new_device_text = ft.Text("", color=ft.colors.AMBER, size=12)
    header_text = ft.Text("Rimi Inventory", size=20, weight=ft.FontWeight.BOLD)

    serial_input = ft.TextField(label="Serial (scan here)", autofocus=True, text_size=16)
    type_dropdown = ft.Dropdown(
        label="Type",
        options=[
            ft.dropdown.Option("scanner"),
            ft.dropdown.Option("laptop"),
            ft.dropdown.Option("tablet"),
            ft.dropdown.Option("phone"),
            ft.dropdown.Option("other"),
        ],
        value="scanner",
    )
    make_input = ft.TextField(label="Make")
    model_input = ft.TextField(label="Model")
    status_dropdown = ft.Dropdown(
        label="Status",
        options=[
            ft.dropdown.Option("RECEIVED"),
            ft.dropdown.Option("PREPARING"),
            ft.dropdown.Option("PREPARED"),
            ft.dropdown.Option("SENT"),
            ft.dropdown.Option("IN_USE"),
            ft.dropdown.Option("RETURNED"),
            ft.dropdown.Option("RETIRED"),
        ],
        value="RECEIVED",
    )
    from_store_input = ft.TextField(label="From store")
    to_store_input = ft.TextField(label="To store")
    comment_input = ft.TextField(label="Comment")
    overwrite_checkbox = ft.Checkbox(label="Overwrite existing device", value=False)
    bulk_scan_checkbox = ft.Checkbox(label="Bulk scan mode", value=False)

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

    def _clear_form() -> None:
        type_dropdown.value = "scanner"
        make_input.value = ""
        model_input.value = ""
        status_dropdown.value = "RECEIVED"
        from_store_input.value = ""
        to_store_input.value = ""
        comment_input.value = ""
        overwrite_checkbox.value = False
        _set_new_device_state(False, "")

    def _after_save() -> None:
        serial_input.value = ""
        serial_input.focus()
        if bulk_scan_checkbox.value:
            return
        _clear_form()

    def load_device(_e):
        serial = serial_input.value.strip()
        if not serial:
            return

        try:
            device = db.get_device(serial)
        except Exception as exc:
            result_text.value = f"Database error: {exc}"
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
            result_text.value = f"Device found ({serial})"
            result_text.color = ft.colors.BLUE
        else:
            overwrite_checkbox.value = False
            upper_scan = serial.upper()
            for prefix, (guess_type, guess_make, guess_model) in SERIAL_PREFIX_MAP.items():
                if upper_scan.startswith(prefix.upper()):
                    make_val, model_val = _split_make_model(guess_model)
                    _apply_prefill(guess_type, make_val, model_val)
                    _set_new_device_state(True, "New device detected. Tap 'Register' to add.")
                    result_text.value = f"Auto-detected: {guess_make} {guess_model}"
                    result_text.color = ft.colors.GREEN
                    page.update()
                    return

            result_text.value = "New device. Please fill in details."
            _set_new_device_state(True, "New device detected. Tap 'Register' to add.")
            result_text.color = ft.colors.YELLOW

        page.update()

    def save_device(_e):
        serial = serial_input.value.strip()
        if not serial:
            result_text.value = "Serial is required"
            result_text.color = ft.colors.RED
            page.update()
            return

        if not overwrite_checkbox.value:
            try:
                existing = db.get_device(serial)
            except Exception as exc:
                result_text.value = f"Database error: {exc}"
                result_text.color = ft.colors.RED
                page.update()
                return
            if existing:
                result_text.value = "Device already exists. Enable overwrite."
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
            comment=comment_input.value.strip(),
        )

        try:
            db.add_device(dev, overwrite=bool(overwrite_checkbox.value))
            _set_new_device_state(False)
            result_text.value = "Saved"
            result_text.color = ft.colors.GREEN
            _after_save()
        except Exception as exc:
            result_text.value = f"Save failed: {exc}"
            result_text.color = ft.colors.RED
            _after_save()

        page.update()

    # When scanner presses 'Enter' (on_submit), load device details
    serial_input.on_submit = load_device

    button_height = 44
    register_btn = ft.ElevatedButton(
        "Register new device",
        on_click=save_device,
        width=float("inf"),
        height=button_height,
        bgcolor=ft.colors.GREEN_700,
        color=ft.colors.WHITE,
        visible=False,
        disabled=True,
    )
    btn_save = ft.ElevatedButton(
        "Save / Update",
        on_click=save_device,
        width=float("inf"),
        height=button_height,
        bgcolor=ft.colors.RED_700,
        color=ft.colors.WHITE,
    )

    content = ft.Column(
        [
            header_text,
            serial_input,
            result_text,
            new_device_text,
            ft.Text("Actions", size=14, weight=ft.FontWeight.BOLD),
            type_dropdown,
            make_input,
            model_input,
            status_dropdown,
            from_store_input,
            to_store_input,
            comment_input,
            ft.Text("Controls", size=14, weight=ft.FontWeight.BOLD),
            overwrite_checkbox,
            bulk_scan_checkbox,
            register_btn,
            btn_save,
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        spacing=8,
    )

    page.add(content)


if __name__ == "__main__":
    ft.app(target=main)
