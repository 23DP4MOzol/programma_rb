import flet as ft


def main(page: ft.Page) -> None:
    page.title = "Rimi Inventory Diagnostic"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.padding = 16

    status = ft.Text("UI loaded", size=18, color=ft.colors.GREEN)
    info = ft.Text("If you can see this, the Flet runtime works.", size=14)

    def init_db(_e) -> None:
        try:
            from supabase_db import InventoryDB

            InventoryDB()
            status.value = "Supabase import OK"
            status.color = ft.colors.GREEN
        except Exception as exc:
            status.value = f"DB init failed: {exc}"
            status.color = ft.colors.RED
        page.update()

    btn = ft.ElevatedButton("Init DB", on_click=init_db, width=200)

    page.add(
        ft.Column(
            [
                ft.Text("Rimi Inventory", size=24, weight=ft.FontWeight.BOLD),
                status,
                info,
                btn,
            ],
            spacing=12,
        )
    )


if __name__ == "__main__":
    ft.app(target=main)
