import flet as ft

def main(page: ft.Page):
    page.title = "Rimi Inventory"
    page.padding = 12
    page.vertical_alignment = ft.MainAxisAlignment.START

    status_text = ft.Text("Ready", color=ft.colors.GREEN)
    serial_input = ft.TextField(label="Serial", autofocus=True, text_size=16)
    model_input = ft.TextField(label="Model")
    from_store_input = ft.TextField(label="From store")
    to_store_input = ft.TextField(label="To store")
    comment_input = ft.TextField(label="Comment")

    db_state = {"db": None}

    def init_db(_e):
        try:
            from supabase_db import InventoryDB, Device  # lazy import

            db_state["db"] = InventoryDB()
            status_text.value = "DB ready"
            status_text.color = ft.colors.GREEN
        except Exception as exc:
            status_text.value = f"DB init failed: {exc}"
            status_text.color = ft.colors.RED
        page.update()

    def save_device(_e):
        if db_state["db"] is None:
            status_text.value = "DB not ready. Tap 'Init DB' first."
            status_text.color = ft.colors.ORANGE
            page.update()
            return

        serial = serial_input.value.strip()
        if not serial:
            status_text.value = "Serial is required"
            status_text.color = ft.colors.RED
            page.update()
            return

        try:
            from supabase_db import Device  # lazy import

            dev = Device(
                serial=serial,
                device_type="scanner",
                model=model_input.value.strip() or None,
                from_store=from_store_input.value.strip() or None,
                to_store=to_store_input.value.strip() or None,
                status="RECEIVED",
                comment=comment_input.value.strip() or None,
            )
            db_state["db"].add_device(dev, overwrite=True)
            status_text.value = "Saved"
            status_text.color = ft.colors.GREEN
            serial_input.value = ""
            serial_input.focus()
        except Exception as exc:
            status_text.value = f"Save failed: {exc}"
            status_text.color = ft.colors.RED
        page.update()

    init_btn = ft.ElevatedButton("Init DB", on_click=init_db, width=float("inf"))
    save_btn = ft.ElevatedButton("Save", on_click=save_device, width=float("inf"))

    content = ft.Column(
        [
            ft.Text("Rimi Inventory (Safe Mode)", size=20, weight=ft.FontWeight.BOLD),
            status_text,
            serial_input,
            model_input,
            from_store_input,
            to_store_input,
            comment_input,
            init_btn,
            save_btn,
        ],
        spacing=8,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    page.add(content)

if __name__ == "__main__":
    ft.app(target=main)
