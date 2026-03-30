from __future__ import annotations

import traceback
import tkinter as tk
from dataclasses import asdict
from pathlib import Path
from tkinter import messagebox
from tkinter import ttk

from i18n import load_translations, t
from inventory_db import ALLOWED_STATUSES, Device, InventoryDB


DEVICE_TYPES: list[str] = ["scanner", "laptop", "tablet", "phone", "other"]


def _try_load_photo_image(path: Path) -> tk.PhotoImage | None:
    try:
        if not path.exists():
            return None
        return tk.PhotoImage(file=str(path))
    except Exception:
        return None


class DeviceEditor(tk.Toplevel):
    def __init__(self, app: "DesktopApp", serial: str) -> None:
        super().__init__(app.root)
        self.app = app
        self.serial = serial

        self.app._register_editor(self)

        self.title(app.tr("desktop_editor_title", serial=serial))
        self.geometry("560x520")
        self.minsize(520, 460)
        self.transient(app.root)

        self._build_ui()
        self._load_device()

    def _build_ui(self) -> None:
        outer = ttk.Frame(self, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)
        outer.columnconfigure(0, weight=1)

        self.title_lbl = ttk.Label(outer, text="", style="Section.TLabel")
        self.title_lbl.grid(row=0, column=0, sticky="w")

        form = ttk.Frame(outer)
        form.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)

        self.serial_var = tk.StringVar(value=self.serial)
        self.type_var = tk.StringVar(value=self.app._display_value("scanner", kind="type"))
        self.model_var = tk.StringVar()
        self.from_store_var = tk.StringVar()
        self.to_store_var = tk.StringVar()
        self.status_var = tk.StringVar(value=self.app._display_value("RECEIVED", kind="status"))
        self.comment_var = tk.StringVar()

        self.serial_lbl = ttk.Label(form, text="")
        self.serial_lbl.grid(row=0, column=0, sticky="w")
        self.serial_entry = ttk.Entry(form, textvariable=self.serial_var, state="readonly")
        self.serial_entry.grid(row=1, column=0, sticky="ew")

        self.type_lbl = ttk.Label(form, text="")
        self.type_lbl.grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.type_combo = ttk.Combobox(
            form,
            textvariable=self.type_var,
            values=[self.app._display_value(tp, kind="type") for tp in DEVICE_TYPES],
            state="readonly",
        )
        self.type_combo.grid(row=1, column=1, sticky="ew", padx=(8, 0))

        self.model_lbl = ttk.Label(form, text="")
        self.model_lbl.grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.model_entry = ttk.Entry(form, textvariable=self.model_var)
        self.model_entry.grid(row=3, column=0, sticky="ew")

        self.status_lbl = ttk.Label(form, text="")
        self.status_lbl.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
        self.status_combo = ttk.Combobox(
            form,
            textvariable=self.status_var,
            values=[self.app._display_value(st, kind="status") for st in sorted(ALLOWED_STATUSES)],
            state="readonly",
        )
        self.status_combo.grid(row=3, column=1, sticky="ew", padx=(8, 0))

        self.from_lbl = ttk.Label(form, text="")
        self.from_lbl.grid(row=4, column=0, sticky="w", pady=(8, 0))
        self.from_entry = ttk.Entry(form, textvariable=self.from_store_var)
        self.from_entry.grid(row=5, column=0, sticky="ew")

        self.to_lbl = ttk.Label(form, text="")
        self.to_lbl.grid(row=4, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
        self.to_entry = ttk.Entry(form, textvariable=self.to_store_var)
        self.to_entry.grid(row=5, column=1, sticky="ew", padx=(8, 0))

        self.comment_lbl = ttk.Label(form, text="")
        self.comment_lbl.grid(row=6, column=0, sticky="w", pady=(8, 0))
        self.comment_entry = ttk.Entry(form, textvariable=self.comment_var)
        self.comment_entry.grid(row=7, column=0, columnspan=2, sticky="ew")

        btns = ttk.Frame(outer)
        btns.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        btns.columnconfigure(0, weight=1)
        btns.columnconfigure(1, weight=1)
        btns.columnconfigure(2, weight=1)

        self.save_btn = ttk.Button(btns, command=self._on_save, style="Primary.TButton")
        self.save_btn.grid(row=0, column=0, sticky="ew")

        self.delete_btn = ttk.Button(btns, command=self._on_delete, style="Danger.TButton")
        self.delete_btn.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        self.close_btn = ttk.Button(btns, command=self.destroy, style="Secondary.TButton")
        self.close_btn.grid(row=0, column=2, sticky="ew", padx=(8, 0))

        self._apply_i18n()

    def _apply_i18n(self) -> None:
        # Preserve current codes while updating localized display
        type_code = self.app._code_from_display(self.type_var.get()) or "scanner"
        status_code = self.app._code_from_display(self.status_var.get()) or "RECEIVED"

        self.title(self.app.tr("desktop_editor_title", serial=self.serial))

        self.title_lbl.config(text=self.app.tr("desktop_editor_title", serial=self.serial))
        self.serial_lbl.config(text=self.app.tr("web_serial"))
        self.type_lbl.config(text=self.app.tr("web_type"))
        self.model_lbl.config(text=self.app.tr("web_model"))
        self.status_lbl.config(text=self.app.tr("web_status"))
        self.from_lbl.config(text=self.app.tr("web_from_store"))
        self.to_lbl.config(text=self.app.tr("web_to_store"))
        self.comment_lbl.config(text=self.app.tr("web_comment"))
        self.save_btn.config(text=self.app.tr("desktop_save"))
        self.delete_btn.config(text=self.app.tr("web_delete"))
        self.close_btn.config(text=self.app.tr("desktop_close"))

        self.type_combo.configure(values=[self.app._display_value(tp, kind="type") for tp in DEVICE_TYPES])
        self.status_combo.configure(values=[self.app._display_value(st, kind="status") for st in sorted(ALLOWED_STATUSES)])

        self.type_var.set(self.app._display_value(type_code, kind="type"))
        self.status_var.set(self.app._display_value(status_code, kind="status"))

    def _load_device(self) -> None:
        d = self.app.db.get_device(self.serial)
        if not d:
            messagebox.showerror(self.app.tr("desktop_error_title"), self.app.tr("not_found"), parent=self)
            self.destroy()
            return

        self.type_var.set(self.app._display_value(d.device_type if d.device_type in DEVICE_TYPES else "other", kind="type"))
        self.model_var.set(d.model or "")
        self.from_store_var.set(d.from_store or "")
        self.to_store_var.set(d.to_store or "")
        self.status_var.set(self.app._display_value(d.status or "RECEIVED", kind="status"))
        self.comment_var.set(d.comment or "")

    def _on_save(self) -> None:
        try:
            changed = self.app.db.update_device(
                self.serial,
                device_type=self.app._code_from_display(self.type_var.get()) or "scanner",
                model=self.model_var.get().strip() or None,
                from_store=self.from_store_var.get().strip() or None,
                to_store=self.to_store_var.get().strip() or None,
                status=self.app._code_from_display(self.status_var.get()) or "RECEIVED",
                comment=self.comment_var.get().strip() or None,
            )
            if not changed:
                raise ValueError(self.app.tr("not_found_or_no_fields"))

            self.app._selected_serial = self.serial
            self.app.refresh_list(select_serial=self.serial)
            self.app._on_row_selected()
            self.destroy()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(self.app.tr("desktop_error_title"), str(exc), parent=self)

    def _on_delete(self) -> None:
        try:
            msg = self.app.tr("web_confirm_delete", serial=self.serial)
            if not messagebox.askyesno(self.app.tr("desktop_confirm_title"), msg, parent=self):
                return

            deleted = self.app.db.delete_device(self.serial)
            if not deleted:
                raise ValueError(self.app.tr("not_found"))

            if self.app._selected_serial == self.serial:
                self.app.clear_form()
            self.app.refresh_list()
            self.destroy()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(self.app.tr("desktop_error_title"), str(exc), parent=self)


class DesktopApp:
    def __init__(self, root: tk.Tk, *, db_path: str | Path = "inventory.db", lang: str = "lv") -> None:
        self.root = root
        self.db_path = str(db_path)
        self.lang = lang

        self.translations = load_translations()
        self.db = InventoryDB(self.db_path)
        self.db.init_db()

        self._selected_serial: str | None = None
        self._editors: set[DeviceEditor] = set()

        self._build_ui()
        self._apply_i18n()
        self.refresh_list()

    # ---------- i18n ----------

    def tr(self, key: str, **kwargs: object) -> str:
        return t(self.translations, key, lang=self.lang, **kwargs)

    def _status_key(self, code: str) -> str:
        return f"status_{code.lower()}"

    def _type_key(self, code: str) -> str:
        return f"type_{code.lower()}"

    def _display_value(self, code: str, *, kind: str) -> str:
        code = (code or "").strip()
        if not code:
            return ""
        if kind == "status":
            label = self.tr(self._status_key(code))
        elif kind == "type":
            label = self.tr(self._type_key(code))
        else:
            label = code
        return f"{code} — {label}" if label else code

    def _code_from_display(self, display: str) -> str:
        if not display:
            return ""
        return display.split(" — ", 1)[0].strip()

    # ---------- UI ----------

    def _build_ui(self) -> None:
        self.root.title("programma_rb")
        self.root.geometry("1200x720")
        self.root.minsize(1050, 640)

        self._style()

        self._setup_branding_assets()

        top = ttk.Frame(self.root, padding=12)
        top.pack(fill=tk.X)

        self.logo_lbl = ttk.Label(top, text="")
        self.logo_lbl.pack(side=tk.LEFT)

        self.title_lbl = ttk.Label(top, text="programma_rb", style="Title.TLabel")
        self.title_lbl.pack(side=tk.LEFT, padx=(10, 0))

        self.subtitle_lbl = ttk.Label(top, text="", style="SubTitle.TLabel")
        self.subtitle_lbl.pack(side=tk.LEFT, padx=(12, 0))

        right = ttk.Frame(top)
        right.pack(side=tk.RIGHT)

        self.lang_var = tk.StringVar(value=self.lang)
        self.lang_combo = ttk.Combobox(
            right,
            textvariable=self.lang_var,
            values=["lv", "en"],
            width=6,
            state="readonly",
        )
        self.lang_combo.pack(side=tk.RIGHT)
        self.lang_combo.bind("<<ComboboxSelected>>", lambda _e: self._on_lang_changed())

        self.refresh_btn = ttk.Button(right, command=self.refresh_list, style="Secondary.TButton")
        self.refresh_btn.pack(side=tk.RIGHT, padx=(0, 10))

        body = ttk.Frame(self.root, padding=(12, 0, 12, 12))
        body.pack(fill=tk.BOTH, expand=True)

        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        # Left: form
        self.form_card = ttk.Frame(body, padding=12, style="Card.TFrame")
        self.form_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.form_card.columnconfigure(0, weight=1)

        self.actions_title = ttk.Label(self.form_card, text="", style="Section.TLabel")
        self.actions_title.grid(row=0, column=0, sticky="w")

        form = ttk.Frame(self.form_card)
        form.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)

        self.serial_var = tk.StringVar()
        self.type_var = tk.StringVar(value="scanner")
        self.model_var = tk.StringVar()
        self.from_store_var = tk.StringVar()
        self.to_store_var = tk.StringVar()
        self.status_var = tk.StringVar(value="RECEIVED")
        self.comment_var = tk.StringVar()
        self.overwrite_var = tk.BooleanVar(value=False)

        self._field(form, 0, 0, "web_serial", self.serial_var)

        self.type_lbl = ttk.Label(form, text="")
        self.type_lbl.grid(row=0, column=1, sticky="w")
        self.type_combo = ttk.Combobox(
            form,
            textvariable=self.type_var,
            state="readonly",
        )
        self.type_combo.grid(row=1, column=1, sticky="ew", padx=(8, 0))

        self._field(form, 2, 0, "web_model", self.model_var)

        self.status_lbl = ttk.Label(form, text="")
        self.status_lbl.grid(row=2, column=1, sticky="w", padx=(8, 0))
        self.status_combo = ttk.Combobox(
            form,
            textvariable=self.status_var,
            state="readonly",
        )
        self.status_combo.grid(row=3, column=1, sticky="ew", padx=(8, 0))

        self._field(form, 4, 0, "web_from_store", self.from_store_var)
        self._field(form, 4, 1, "web_to_store", self.to_store_var, padx_left=8)

        self.comment_lbl = ttk.Label(form, text="")
        self.comment_lbl.grid(row=6, column=0, sticky="w", pady=(8, 0))
        self.comment_entry = ttk.Entry(form, textvariable=self.comment_var)
        self.comment_entry.grid(row=7, column=0, columnspan=2, sticky="ew")

        self.overwrite_chk = ttk.Checkbutton(self.form_card, variable=self.overwrite_var)
        self.overwrite_chk.grid(row=2, column=0, sticky="w", pady=(10, 0))

        btns = ttk.Frame(self.form_card)
        btns.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        btns.columnconfigure(0, weight=1)
        btns.columnconfigure(1, weight=1)
        btns.columnconfigure(2, weight=1)
        btns.columnconfigure(3, weight=1)

        self.add_btn = ttk.Button(btns, command=self.add_device, style="Primary.TButton")
        self.add_btn.grid(row=0, column=0, sticky="ew")

        self.update_btn = ttk.Button(btns, command=self.update_device, style="Secondary.TButton")
        self.update_btn.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        self.status_btn = ttk.Button(btns, command=self.change_status, style="Secondary.TButton")
        self.status_btn.grid(row=0, column=2, sticky="ew", padx=(8, 0))

        self.delete_btn = ttk.Button(btns, command=self.delete_selected, style="Danger.TButton")
        self.delete_btn.grid(row=0, column=3, sticky="ew", padx=(8, 0))

        self.clear_btn = ttk.Button(self.form_card, command=self.clear_form, style="Secondary.TButton")
        self.clear_btn.grid(row=4, column=0, sticky="ew", pady=(10, 0))

        self.result_lbl = ttk.Label(self.form_card, text="", style="Muted.TLabel")
        self.result_lbl.grid(row=5, column=0, sticky="w", pady=(10, 0))

        self.result_txt = tk.Text(
            self.form_card,
            height=8,
            wrap="word",
            bg="#ffffff",
            relief="solid",
            borderwidth=1,
        )
        self.result_txt.grid(row=6, column=0, sticky="nsew", pady=(6, 0))
        self.form_card.rowconfigure(6, weight=1)

        # Right: list + filters
        self.list_card = ttk.Frame(body, padding=12, style="Card.TFrame")
        self.list_card.grid(row=0, column=1, sticky="nsew")
        self.list_card.columnconfigure(0, weight=1)
        self.list_card.rowconfigure(2, weight=1)

        list_header = ttk.Frame(self.list_card)
        list_header.grid(row=0, column=0, sticky="ew")
        list_header.columnconfigure(0, weight=1)

        self.list_title = ttk.Label(list_header, text="", style="Section.TLabel")
        self.list_title.grid(row=0, column=0, sticky="w")

        self.double_click_hint = ttk.Label(list_header, text="", style="Muted.TLabel")
        self.double_click_hint.grid(row=0, column=1, sticky="e")

        filters = ttk.Frame(self.list_card)
        filters.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        for c in range(4):
            filters.columnconfigure(c, weight=1)

        self.filter_status_var = tk.StringVar(value="")
        self.filter_from_var = tk.StringVar(value="")
        self.filter_to_var = tk.StringVar(value="")
        self.limit_var = tk.StringVar(value="200")

        self.filter_status_lbl = ttk.Label(filters, text="")
        self.filter_status_lbl.grid(row=0, column=0, sticky="w")
        self.filter_status_combo = ttk.Combobox(
            filters,
            textvariable=self.filter_status_var,
            state="readonly",
        )
        self.filter_status_combo.grid(row=1, column=0, sticky="ew")

        self.limit_lbl = ttk.Label(filters, text="")
        self.limit_lbl.grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.limit_entry = ttk.Entry(filters, textvariable=self.limit_var)
        self.limit_entry.grid(row=1, column=1, sticky="ew", padx=(8, 0))

        self.filter_from_lbl = ttk.Label(filters, text="")
        self.filter_from_lbl.grid(row=0, column=2, sticky="w", padx=(8, 0))
        self.filter_from_entry = ttk.Entry(filters, textvariable=self.filter_from_var)
        self.filter_from_entry.grid(row=1, column=2, sticky="ew", padx=(8, 0))

        self.filter_to_lbl = ttk.Label(filters, text="")
        self.filter_to_lbl.grid(row=0, column=3, sticky="w", padx=(8, 0))
        self.filter_to_entry = ttk.Entry(filters, textvariable=self.filter_to_var)
        self.filter_to_entry.grid(row=1, column=3, sticky="ew", padx=(8, 0))

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
        self.tree.bind("<Double-1>", lambda _e: self._on_row_double_click())

        self._build_context_menu()

    def _build_context_menu(self) -> None:
        self.menu = tk.Menu(self.root, tearoff=False)
        self.menu.add_command(label=self.tr("web_edit"), command=self._on_row_double_click)

        self.status_menu = tk.Menu(self.menu, tearoff=False)
        for s in sorted(ALLOWED_STATUSES):
            disp = self._display_value(s, kind="status")
            self.status_menu.add_command(label=disp, command=lambda st=s: self._set_status_from_menu(st))

        self.menu.add_cascade(label=self.tr("web_status_inline"), menu=self.status_menu)
        self.menu.add_separator()
        self.menu.add_command(label=self.tr("web_delete_short"), command=self.delete_selected)

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
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Rimi-like red/white
        self.root.configure(bg="#ffffff")

        style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"), background="#ffffff", foreground="#d50000")
        style.configure("SubTitle.TLabel", font=("Segoe UI", 10), background="#ffffff", foreground="#666666")
        style.configure("Section.TLabel", font=("Segoe UI", 11, "bold"), background="#ffffff", foreground="#111111")
        style.configure("Muted.TLabel", font=("Segoe UI", 9), background="#ffffff", foreground="#666666")

        style.configure("Card.TFrame", background="#ffffff")

        style.configure(
            "TEntry",
            padding=(8, 6),
        )

        style.configure(
            "TCombobox",
            padding=(6, 4),
        )

        style.configure(
            "Treeview",
            font=("Segoe UI", 9),
            rowheight=28,
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground="#111111",
            borderwidth=0,
        )
        style.map(
            "Treeview",
            background=[("selected", "#fff5f5")],
            foreground=[("selected", "#111111")],
        )

        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 9, "bold"),
            background="#ffffff",
            foreground="#111111",
            relief="flat",
        )

        style.configure(
            "Primary.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(10, 8),
        )
        style.map(
            "Primary.TButton",
            background=[("!disabled", "#d50000"), ("active", "#b40000")],
            foreground=[("!disabled", "#ffffff")],
        )

        style.configure(
            "Secondary.TButton",
            font=("Segoe UI", 10),
            padding=(10, 8),
        )
        style.map(
            "Secondary.TButton",
            background=[("!disabled", "#ffffff"), ("active", "#fff5f5")],
            foreground=[("!disabled", "#d50000")],
        )

        style.configure(
            "Danger.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(10, 8),
        )
        style.map(
            "Danger.TButton",
            background=[("!disabled", "#b00020"), ("active", "#8a0019")],
            foreground=[("!disabled", "#ffffff")],
        )

    def _setup_branding_assets(self) -> None:
        """Loads user-provided logo/icon from ./assets.

        Note: We do not ship any Rimi Baltic logo assets.
        If you want an official logo, place it as ./assets/logo.png.
        """

        assets_dir = Path(__file__).resolve().parent / "assets"

        self._logo_img: tk.PhotoImage | None = None
        for name in ("logo.png", "logo.gif"):
            img = _try_load_photo_image(assets_dir / name)
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
    ) -> None:
        lbl = ttk.Label(parent, text="")
        lbl.grid(row=row, column=col, sticky="w", pady=(8, 0), padx=(padx_left, 0))
        ent = ttk.Entry(parent, textvariable=var)
        ent.grid(row=row + 1, column=col, sticky="ew", padx=(padx_left, 0))
        setattr(self, f"_lbl_{label_key}_{row}_{col}", lbl)

    def _apply_i18n(self) -> None:
        self.lang = self.lang_var.get().lower()

        self.root.title(self.tr("app_title"))

        if self._logo_img is not None:
            self.logo_lbl.config(image=self._logo_img, text="")
            self.logo_lbl.image = self._logo_img  # keep reference
        else:
            self.logo_lbl.config(text=self.tr("desktop_brand"), style="Title.TLabel")

        self.title_lbl.config(text=f"{self.tr('desktop_brand')} — {self.tr('desktop_brand_title')}")
        self.subtitle_lbl.config(text=self.tr("desktop_brand_subtitle"))
        self.refresh_btn.config(text=self.tr("web_refresh"))

        self.actions_title.config(text=self.tr("web_action"))
        self.list_title.config(text=self.tr("web_list"))

        # Form labels
        self._get_field_label("web_serial", 0, 0).config(text=self.tr("web_serial"))
        self.type_lbl.config(text=self.tr("web_type"))
        self._get_field_label("web_model", 2, 0).config(text=self.tr("web_model"))
        self.status_lbl.config(text=self.tr("web_status"))
        self._get_field_label("web_from_store", 4, 0).config(text=self.tr("web_from_store"))
        self._get_field_label("web_to_store", 4, 1).config(text=self.tr("web_to_store"))
        self.comment_lbl.config(text=self.tr("web_comment"))

        self.overwrite_chk.config(text=self.tr("web_overwrite"))

        self.add_btn.config(text=self.tr("web_add"))
        self.update_btn.config(text=self.tr("web_update"))
        self.status_btn.config(text=self.tr("web_change_status"))
        self.delete_btn.config(text=self.tr("web_delete"))
        self.clear_btn.config(text=self.tr("web_refresh"))

        self.result_lbl.config(text=self.tr("web_result"))

        # Filters
        self.filter_status_lbl.config(text=self.tr("web_status"))
        self.limit_lbl.config(text=self.tr("web_limit"))
        self.filter_from_lbl.config(text=self.tr("web_from_store"))
        self.filter_to_lbl.config(text=self.tr("web_to_store"))

        self.double_click_hint.config(text=self.tr("desktop_double_click_hint"))

        # Dropdown values (localized display, stable code prefix)
        type_code = self._code_from_display(self.type_var.get()) or "scanner"
        status_code = self._code_from_display(self.status_var.get()) or "RECEIVED"

        type_values = [self._display_value(tp, kind="type") for tp in DEVICE_TYPES]
        status_values = [self._display_value(st, kind="status") for st in sorted(ALLOWED_STATUSES)]

        self.type_combo.configure(values=type_values)
        self.status_combo.configure(values=status_values)

        self.type_var.set(self._display_value(type_code, kind="type"))
        self.status_var.set(self._display_value(status_code, kind="status"))

        # Status filter (localized display, stable code prefix; empty means no filter)
        current_filter_code = self._code_from_display(self.filter_status_var.get())
        filter_values = [""] + status_values
        self.filter_status_combo.configure(values=filter_values)
        if current_filter_code:
            self.filter_status_var.set(self._display_value(current_filter_code, kind="status"))

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

    def _get_field_label(self, label_key: str, row: int, col: int) -> ttk.Label:
        return getattr(self, f"_lbl_{label_key}_{row}_{col}")

    def _on_lang_changed(self) -> None:
        self._apply_i18n()
        self.refresh_list()
        self._refresh_open_editors_i18n()

    def _register_editor(self, editor: DeviceEditor) -> None:
        self._editors.add(editor)
        editor.bind("<Destroy>", lambda _e: self._editors.discard(editor))

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

    # ---------- Data actions ----------

    def _write_result(self, payload: object, ok: bool = True) -> None:
        self.result_txt.configure(state="normal")
        self.result_txt.delete("1.0", tk.END)
        self.result_txt.insert("1.0", str(payload))
        self.result_txt.configure(state="disabled")
        self.result_txt.tag_configure("ok", foreground="#0a7a2f")
        self.result_txt.tag_configure("err", foreground="#b00020")

        # Not perfect coloring, but keep the area usable.
        self.result_txt.configure(fg="#0a7a2f" if ok else "#b00020")

    def _current_device_from_form(self) -> Device:
        serial = self.serial_var.get().strip()
        device_type = self._code_from_display(self.type_var.get()) or "scanner"
        model = self.model_var.get().strip() or None
        from_store = self.from_store_var.get().strip() or None
        to_store = self.to_store_var.get().strip() or None
        status = self._code_from_display(self.status_var.get()) or "RECEIVED"
        comment = self.comment_var.get().strip() or None

        return Device(
            serial=serial,
            device_type=device_type,
            model=model,
            from_store=from_store,
            to_store=to_store,
            status=status,
            comment=comment,
        )

    def add_device(self) -> None:
        try:
            device = self._current_device_from_form()
            overwrite = bool(self.overwrite_var.get())
            self.db.add_device(device, overwrite=overwrite)
            self._selected_serial = device.serial
            self._write_result({"ok": True, "action": "add", "serial": device.serial})
            self.refresh_list(select_serial=device.serial)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(self.tr("desktop_error_title"), str(exc))
            self._write_result({"ok": False, "error": str(exc)}, ok=False)

    def update_device(self) -> None:
        try:
            device = self._current_device_from_form()
            if not device.serial:
                raise ValueError("serial is required")

            changed = self.db.update_device(
                device.serial,
                device_type=device.device_type,
                model=device.model,
                from_store=device.from_store,
                to_store=device.to_store,
                status=device.status,
                comment=device.comment,
            )
            if not changed:
                raise ValueError(self.tr("not_found_or_no_fields"))

            self._selected_serial = device.serial
            self._write_result({"ok": True, "action": "update", "serial": device.serial})
            self.refresh_list(select_serial=device.serial)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(self.tr("desktop_error_title"), str(exc))
            self._write_result({"ok": False, "error": str(exc)}, ok=False)

    def change_status(self) -> None:
        try:
            serial = self.serial_var.get().strip()
            if not serial:
                raise ValueError("serial is required")

            changed = self.db.change_status(
                serial,
                self._code_from_display(self.status_var.get()) or "RECEIVED",
                to_store=self.to_store_var.get().strip() or None,
                comment=self.comment_var.get().strip() or None,
            )
            if not changed:
                raise ValueError(self.tr("not_found"))

            self._selected_serial = serial
            self._write_result(
                {
                    "ok": True,
                    "action": "status",
                    "serial": serial,
                    "status": self._code_from_display(self.status_var.get()) or "RECEIVED",
                }
            )
            self.refresh_list(select_serial=serial)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(self.tr("desktop_error_title"), str(exc))
            self._write_result({"ok": False, "error": str(exc)}, ok=False)

    def delete_selected(self) -> None:
        try:
            serial = self.serial_var.get().strip()
            if not serial:
                raise ValueError("serial is required")

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
            messagebox.showerror(self.tr("desktop_error_title"), str(exc))
            self._write_result({"ok": False, "error": str(exc)}, ok=False)

    def clear_form(self) -> None:
        self._selected_serial = None
        self.serial_var.set("")
        self.type_var.set("scanner")
        self.model_var.set("")
        self.from_store_var.set("")
        self.to_store_var.set("")
        self.status_var.set("RECEIVED")
        self.comment_var.set("")

    def refresh_list(self, *, select_serial: str | None = None) -> None:
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)

            status_display = self.filter_status_var.get().strip()
            status = self._code_from_display(status_display) or None
            from_store = self.filter_from_var.get().strip() or None
            to_store = self.filter_to_var.get().strip() or None

            try:
                limit = int(self.limit_var.get().strip() or "200")
            except Exception:
                limit = 200

            devices = self.db.list_devices(status=status, from_store=from_store, to_store=to_store, limit=limit)

            selected_iid: str | None = None
            want_serial = select_serial or self._selected_serial

            for d in devices:
                updated = (d.updated_at or "").replace("T", " ")

                type_disp = self._display_value(d.device_type, kind="type")
                status_disp = self._display_value(d.status, kind="status")
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

        # Always load from DB so we can keep stable codes even if table shows localized labels.
        d = self.db.get_device(serial)
        if not d:
            return

        self.serial_var.set(serial)
        self.type_var.set(self._display_value(d.device_type or "other", kind="type"))
        self.model_var.set(d.model or "")
        self.from_store_var.set(d.from_store or "")
        self.to_store_var.set(d.to_store or "")
        self.status_var.set(self._display_value(d.status or "RECEIVED", kind="status"))
        self.comment_var.set(d.comment or "")

    def _on_row_double_click(self) -> None:
        if not self._selected_serial:
            self._on_row_selected()
        if not self._selected_serial:
            return

        try:
            DeviceEditor(self, self._selected_serial)
        except Exception:
            messagebox.showerror(self.tr("desktop_error_title"), traceback.format_exc())


def run_desktop(*, db_path: str | Path = "inventory.db", lang: str = "lv") -> None:
    root = tk.Tk()
    DesktopApp(root, db_path=db_path, lang=lang)
    root.mainloop()
