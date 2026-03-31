import flet as ft
from supabase_db import InventoryDB, Device

def main(page: ft.Page):
    page.title = "Rimi Scanner App"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.window_width = 400
    page.window_height = 800
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20

    db = InventoryDB()
    
    # UI Elements
    result_text = ft.Text("", color=ft.colors.GREEN)
    
    serial_input = ft.TextField(label="Skenēt / Ievadīt Serial (Scan Here)", autofocus=True)
    type_dropdown = ft.Dropdown(
        label="Tips",
        options=[
            ft.dropdown.Option("scanner"),
            ft.dropdown.Option("laptop"),
            ft.dropdown.Option("tablet"),
            ft.dropdown.Option("phone"),
            ft.dropdown.Option("other"),
        ],
        value="scanner"
    )
    make_input = ft.TextField(label="Ražotājs (Make)")
    model_input = ft.TextField(label="Modelis")
    status_dropdown = ft.Dropdown(
        label="Statuss",
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
    from_store_input = ft.TextField(label="No veikala (From)")
    to_store_input = ft.TextField(label="Uz veikalu (To)")
    comment_input = ft.TextField(label="Komentārs")

    def load_device(e):
        serial = serial_input.value.strip()
        if not serial:
            return
            
        try:
            device = db.get_device(serial)
        except Exception as exc:
            result_text.value = f"Error: {exc}"
            result_text.color = ft.colors.RED
            page.update()
            return
            
        if device:
            type_dropdown.value = device.device_type
            status_dropdown.value = device.status
            from_store_input.value = device.from_store or ""
            to_store_input.value = device.to_store or ""
            comment_input.value = device.comment or ""
            
            model_text = device.model or ""
            if " " in model_text:
                parts = model_text.split(" ", 1)
                make_input.value = parts[0]
                model_input.value = parts[1]
            else:
                make_input.value = model_text
                model_input.value = ""
                
            result_text.value = f"Iekārta atrasta! ({serial})"
            result_text.color = ft.colors.BLUE
        else:
            result_text.value = "Jauna iekārta. Lūdzu, ievadiet datus."
            result_text.color = ft.colors.YELLOW
            
        page.update()

    def save_device(e):
        serial = serial_input.value.strip()
        if not serial:
            result_text.value = "Kļūda: Serial ir obligāts"
            result_text.color = ft.colors.RED
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
            db.add_device(dev, overwrite=True)
            result_text.value = "Saglabāts veiksmīgi!"
            result_text.color = ft.colors.GREEN
            
            # Clear form for next scan
            serial_input.value = ""
            serial_input.focus()
            
        except Exception as exc:
            result_text.value = f"Kļūda saglabājot: {exc}"
            result_text.color = ft.colors.RED
            
        page.update()

    # When scanner presses 'Enter' (on_submit), load device details
    serial_input.on_submit = load_device

    btn_save = ft.ElevatedButton("Saglabāt / Atjaunot", on_click=save_device, width=float('inf'), bgcolor=ft.colors.RED_700, color=ft.colors.WHITE)

    # Scrollable column for smaller screens
    content = ft.Column(
        [
            ft.Text("Rimi Iekārtu Skeneris", size=24, weight=ft.FontWeight.BOLD),
            serial_input,
            result_text,
            type_dropdown,
            make_input,
            model_input,
            status_dropdown,
            from_store_input,
            to_store_input,
            comment_input,
            btn_save
        ],
        scroll=ft.ScrollMode.AUTO,
        expand=True
    )
    
    page.add(content)

if __name__ == "__main__":
    ft.app(target=main)
