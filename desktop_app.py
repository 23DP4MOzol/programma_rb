from __future__ import annotations

import traceback
import tkinter as tk
from tkinter import font as tkfont
import re
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


def _fit_photo_image(img: tk.PhotoImage, *, max_w: int, max_h: int) -> tk.PhotoImage:
    try:
        w = int(img.width())
        h = int(img.height())
        if w <= 0 or h <= 0:
            return img

        factor_w = (w + max_w - 1) // max_w
        factor_h = (h + max_h - 1) // max_h
        factor = max(1, factor_w, factor_h)
        if factor <= 1:
            return img
        return img.subsample(factor, factor)
    except Exception:
        return img


def _try_load_logo_image(path: Path, *, max_w: int, max_h: int) -> tk.PhotoImage | None:
    """Load logo with high-quality resize (Pillow if available).

    Tk's native subsample can look jagged; Pillow resize looks much cleaner.
    """

    if not path.exists():
        return None

    try:
        from PIL import Image, ImageTk  # type: ignore

        img = Image.open(path).convert("RGBA")

        # If the logo is a banner with a solid-ish background (like a red rectangle),
        # remove that background so it looks clean on the header.
        try:
            alpha = img.getchannel("A")
            mins, maxs = alpha.getextrema()
            has_transparency = mins < 255

            if not has_transparency:
                w, h = img.size
                # Sample corners to estimate background color.
                corners = [
                    img.getpixel((0, 0)),
                    img.getpixel((w - 1, 0)),
                    img.getpixel((0, h - 1)),
                    img.getpixel((w - 1, h - 1)),
                ]
                bg_r = sum(p[0] for p in corners) // 4
                bg_g = sum(p[1] for p in corners) // 4
                bg_b = sum(p[2] for p in corners) // 4

                def near_bg(r: int, g: int, b: int) -> bool:
                    # Tuned for typical "red header" banners with slight gradients.
                    return abs(r - bg_r) + abs(g - bg_g) + abs(b - bg_b) <= 80

                pixels = list(img.getdata())
                new: list[tuple[int, int, int, int]] = []
                for r, g, b, a in pixels:
                    if a > 240 and near_bg(r, g, b):
                        new.append((r, g, b, 0))
                    else:
                        new.append((r, g, b, a))
                img.putdata(new)

                bbox = img.getchannel("A").getbbox()
                if bbox:
                    img = img.crop(bbox)
        except Exception:
            pass
        w, h = img.size
        if w <= 0 or h <= 0:
            return None

        scale = min(max_w / w, max_h / h, 1.0)
        if scale < 1.0:
            img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)

        return ImageTk.PhotoImage(img)
    except Exception:
        img = _try_load_photo_image(path)
        if img is None:
            return None
        return _fit_photo_image(img, max_w=max_w, max_h=max_h)


def _configure_windows_dpi(root: tk.Tk) -> None:
    """Best-effort DPI awareness for crisp rendering on Windows."""

    try:
        import ctypes

        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)  # per-monitor DPI aware
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

        dpi = 96
        try:
            dpi = int(ctypes.windll.user32.GetDpiForSystem())
        except Exception:
            pass

        # Tk scaling uses pixels per point (1 point = 1/72 inch)
        root.tk.call("tk", "scaling", dpi / 72)
    except Exception:
        pass


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
        outer = ttk.Frame(self, padding=14, style="Body.TFrame")
        outer.pack(fill=tk.BOTH, expand=True)
        outer.columnconfigure(0, weight=1)

        self.title_lbl = ttk.Label(outer, text="", style="Section.TLabel")
        self.title_lbl.grid(row=0, column=0, sticky="w")

        form = ttk.Frame(outer, padding=14, style="Card.TFrame", relief="solid", borderwidth=1)
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

        self.serial_lbl = ttk.Label(form, text="", style="Label.TLabel")
        self.serial_lbl.grid(row=0, column=0, sticky="w")
        self.serial_entry = ttk.Entry(form, textvariable=self.serial_var, state="readonly", style="App.TEntry")
        self.serial_entry.grid(row=1, column=0, sticky="ew")

        self.type_lbl = ttk.Label(form, text="", style="Label.TLabel")
        self.type_lbl.grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.type_combo = ttk.Combobox(
            form,
            textvariable=self.type_var,
            values=[self.app._display_value(tp, kind="type") for tp in DEVICE_TYPES],
            state="readonly",
            style="App.TCombobox",
        )
        self.type_combo.grid(row=1, column=1, sticky="ew", padx=(8, 0))

        self.model_lbl = ttk.Label(form, text="", style="Label.TLabel")
        self.model_lbl.grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.model_entry = ttk.Entry(form, textvariable=self.model_var, style="App.TEntry")
        self.model_entry.grid(row=3, column=0, sticky="ew")

        self.status_lbl = ttk.Label(form, text="", style="Label.TLabel")
        self.status_lbl.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
        self.status_combo = ttk.Combobox(
            form,
            textvariable=self.status_var,
            values=[self.app._display_value(st, kind="status") for st in sorted(ALLOWED_STATUSES)],
            state="readonly",
            style="App.TCombobox",
        )
        self.status_combo.grid(row=3, column=1, sticky="ew", padx=(8, 0))

        self.from_lbl = ttk.Label(form, text="", style="Label.TLabel")
        self.from_lbl.grid(row=4, column=0, sticky="w", pady=(8, 0))
        self.from_entry = ttk.Entry(form, textvariable=self.from_store_var, style="App.TEntry")
        self.from_entry.grid(row=5, column=0, sticky="ew")

        self.to_lbl = ttk.Label(form, text="", style="Label.TLabel")
        self.to_lbl.grid(row=4, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
        self.to_entry = ttk.Entry(form, textvariable=self.to_store_var, style="App.TEntry")
        self.to_entry.grid(row=5, column=1, sticky="ew", padx=(8, 0))

        self.comment_lbl = ttk.Label(form, text="", style="Label.TLabel")
        self.comment_lbl.grid(row=6, column=0, sticky="w", pady=(8, 0))
        self.comment_entry = ttk.Entry(form, textvariable=self.comment_var, style="App.TEntry")
        self.comment_entry.grid(row=7, column=0, columnspan=2, sticky="ew")

        btns = ttk.Frame(outer, style="Body.TFrame")
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
        type_code = self.app._code_from_display(self.type_var.get(), kind="type") or "scanner"
        status_code = self.app._code_from_display(self.status_var.get(), kind="status") or "RECEIVED"

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
                device_type=self.app._code_from_display(self.type_var.get(), kind="type") or "scanner",
                model=self.model_var.get().strip() or None,
                from_store=self.from_store_var.get().strip() or None,
                to_store=self.to_store_var.get().strip() or None,
                status=self.app._code_from_display(self.status_var.get(), kind="status") or "RECEIVED",
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
        self._rebuild_display_maps()
        self.db = InventoryDB(self.db_path)
        self.db.init_db()

        self._selected_serial: str | None = None
        self._editors: set[DeviceEditor] = set()
        self.theme: str = "light"  # "light" | "dark"
        self._filter_refresh_job: str | None = None
        self._sort_col: str | None = None
        self._sort_desc: bool = False

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

    def _rebuild_display_maps(self) -> None:
        # Code -> display should be in current language.
        self._status_code_to_display = {}
        for code in sorted(ALLOWED_STATUSES):
            disp = self.tr(self._status_key(code)) or code
            self._status_code_to_display[code] = disp

        self._type_code_to_display = {}
        for code in DEVICE_TYPES:
            disp = self.tr(self._type_key(code)) or code
            self._type_code_to_display[code] = disp

        # Display -> code must accept BOTH LV/EN labels (and legacy "CODE — label")
        # so switching language never breaks filtering/validation.
        self._status_display_to_code = {}
        for code in sorted(ALLOWED_STATUSES):
            self._status_display_to_code[code] = code
            self._status_display_to_code[code.upper()] = code
            # Current language
            cur_disp = self._status_code_to_display.get(code, code)
            self._status_display_to_code[cur_disp] = code
            self._status_display_to_code[f"{code} — {cur_disp}"] = code
            # Other languages
            for _lang, table in (self.translations or {}).items():
                disp = (table or {}).get(self._status_key(code))
                if disp:
                    self._status_display_to_code[disp] = code
                    self._status_display_to_code[f"{code} — {disp}"] = code

        self._type_display_to_code = {}
        for code in DEVICE_TYPES:
            self._type_display_to_code[code] = code
            self._type_display_to_code[code.lower()] = code
            self._type_display_to_code[code.upper()] = code
            cur_disp = self._type_code_to_display.get(code, code)
            self._type_display_to_code[cur_disp] = code
            self._type_display_to_code[f"{code} — {cur_disp}"] = code
            for _lang, table in (self.translations or {}).items():
                disp = (table or {}).get(self._type_key(code))
                if disp:
                    self._type_display_to_code[disp] = code
                    self._type_display_to_code[f"{code} — {disp}"] = code

    def _display_value(self, code: str, *, kind: str) -> str:
        code = (code or "").strip()
        if not code:
            return ""
        if kind == "status":
            return self._status_code_to_display.get(code, code)
        if kind == "type":
            return self._type_code_to_display.get(code, code)
        return code

    def _code_from_display(self, display: str, *, kind: str) -> str:
        if not display:
            return ""
        display = display.strip()

        # Backward-compatible: previously UI used "CODE — label".
        if " — " in display:
            return display.split(" — ", 1)[0].strip()

        if kind == "status":
            return self._status_display_to_code.get(display, display)
        if kind == "type":
            return self._type_display_to_code.get(display, display)
        return display

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
        self.model_var = tk.StringVar()
        self.from_store_var = tk.StringVar()
        self.to_store_var = tk.StringVar()
        self.status_var = tk.StringVar(value="RECEIVED")
        self.comment_var = tk.StringVar()
        self.overwrite_var = tk.BooleanVar(value=False)

        self._field(form, 0, 0, "web_serial", self.serial_var)

        self.type_lbl = ttk.Label(form, text="", style="Label.TLabel")
        self.type_lbl.grid(row=0, column=1, sticky="w")
        self.type_combo = ttk.Combobox(
            form,
            textvariable=self.type_var,
            state="readonly",
            style="App.TCombobox",
        )
        self.type_combo.grid(row=1, column=1, sticky="ew", padx=(8, 0))

        self._field(form, 2, 0, "web_model", self.model_var)

        self.status_lbl = ttk.Label(form, text="", style="Label.TLabel")
        self.status_lbl.grid(row=2, column=1, sticky="w", padx=(8, 0))
        self.status_combo = ttk.Combobox(
            form,
            textvariable=self.status_var,
            state="readonly",
            style="App.TCombobox",
        )
        self.status_combo.grid(row=3, column=1, sticky="ew", padx=(8, 0))

        self._field(form, 4, 0, "web_from_store", self.from_store_var)
        self._field(form, 4, 1, "web_to_store", self.to_store_var, padx_left=8)

        self.comment_lbl = ttk.Label(form, text="", style="Label.TLabel")
        self.comment_lbl.grid(row=6, column=0, sticky="w", pady=(8, 0))
        self.comment_entry = ttk.Entry(form, textvariable=self.comment_var, style="App.TEntry")
        self.comment_entry.grid(row=7, column=0, columnspan=2, sticky="ew")

        self.overwrite_chk = ttk.Checkbutton(self.form_card, variable=self.overwrite_var)
        self.overwrite_chk.grid(row=2, column=0, sticky="w", pady=(10, 0))

        btns = ttk.Frame(self.form_card, style="Card.TFrame")
        btns.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        btns.columnconfigure(0, weight=1)
        btns.columnconfigure(1, weight=1)

        self.add_btn = ttk.Button(btns, command=self.add_device, style="Primary.TButton")
        self.add_btn.grid(row=0, column=0, sticky="ew")

        self.clear_form_btn = ttk.Button(btns, command=self.clear_form, style="Secondary.TButton")
        self.clear_form_btn.grid(row=0, column=1, sticky="ew", padx=(8, 0))


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
        for c in range(7):
            filters.columnconfigure(c, weight=1)

        self.filter_status_var = tk.StringVar(value="")
        self.filter_type_var = tk.StringVar(value="")
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

        self.filter_serial_lbl = ttk.Label(filters, text="", style="Label.TLabel")
        self.filter_serial_lbl.grid(row=0, column=2, sticky="w", padx=(8, 0))
        self.filter_serial_entry = ttk.Entry(filters, textvariable=self.filter_serial_var, style="App.TEntry")
        self.filter_serial_entry.grid(row=1, column=2, sticky="ew", padx=(8, 0))

        self.filter_model_lbl = ttk.Label(filters, text="", style="Label.TLabel")
        self.filter_model_lbl.grid(row=0, column=3, sticky="w", padx=(8, 0))
        self.filter_model_entry = ttk.Entry(filters, textvariable=self.filter_model_var, style="App.TEntry")
        self.filter_model_entry.grid(row=1, column=3, sticky="ew", padx=(8, 0))

        self.limit_lbl = ttk.Label(filters, text="", style="Label.TLabel")
        self.limit_lbl.grid(row=0, column=6, sticky="w", padx=(8, 0))
        self.limit_entry = ttk.Entry(filters, textvariable=self.limit_var, style="App.TEntry")
        self.limit_entry.grid(row=1, column=6, sticky="ew", padx=(8, 0))

        self.filter_from_lbl = ttk.Label(filters, text="", style="Label.TLabel")
        self.filter_from_lbl.grid(row=0, column=4, sticky="w", padx=(8, 0))
        self.filter_from_entry = ttk.Entry(filters, textvariable=self.filter_from_var, style="App.TEntry")
        self.filter_from_entry.grid(row=1, column=4, sticky="ew", padx=(8, 0))

        self.filter_to_lbl = ttk.Label(filters, text="", style="Label.TLabel")
        self.filter_to_lbl.grid(row=0, column=5, sticky="w", padx=(8, 0))
        self.filter_to_entry = ttk.Entry(filters, textvariable=self.filter_to_var, style="App.TEntry")
        self.filter_to_entry.grid(row=1, column=5, sticky="ew", padx=(8, 0))

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
        self.tree.bind("<Double-1>", lambda _e: self._on_row_double_click())

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
            self.root.option_add("*TCombobox*Listbox.background", entry_bg)
            self.root.option_add("*TCombobox*Listbox.foreground", text)
            self.root.option_add("*TCombobox*Listbox.selectBackground", tree_sel)
            self.root.option_add("*TCombobox*Listbox.selectForeground", text)
            # Hover (active) item in dropdown
            self.root.option_add("*TCombobox*Listbox.activeBackground", tree_sel)
            self.root.option_add("*TCombobox*Listbox.activeForeground", text)
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
    ) -> None:
        lbl = ttk.Label(parent, text="", style="Label.TLabel")
        lbl.grid(row=row, column=col, sticky="w", pady=(8, 0), padx=(padx_left, 0))
        ent = ttk.Entry(parent, textvariable=var, style="App.TEntry")
        ent.grid(row=row + 1, column=col, sticky="ew", padx=(padx_left, 0))
        setattr(self, f"_lbl_{label_key}_{row}_{col}", lbl)

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
        self.clear_form_btn.config(text=self.tr("desktop_clear_form"))
        # Update / Status / Delete buttons removed from Action section (use editor/context menu)

        self.result_lbl.config(text=self.tr("web_result"))

        # Filters
        self.filter_status_lbl.config(text=self.tr("web_status"))
        self.filter_type_lbl.config(text=self.tr("web_type"))
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
            self.filter_type_combo.bind("<<ComboboxSelected>>", lambda _e: self._schedule_filter_refresh())
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
        self.filter_serial_var.set("")
        self.filter_model_var.set("")
        self.filter_from_var.set("")
        self.filter_to_var.set("")
        self.limit_var.set("200")
        self.refresh_list()

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
        # Force background in case Tk ignored earlier theme updates.
        self._apply_non_ttk_theme()
        self.result_txt.configure(state="normal")
        self.result_txt.delete("1.0", tk.END)
        self.result_txt.insert("1.0", str(payload))
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
        serial = self.serial_var.get().strip()
        device_type = self._code_from_display(self.type_var.get(), kind="type") or "scanner"
        model = self.model_var.get().strip() or None
        from_store = self.from_store_var.get().strip() or None
        to_store = self.to_store_var.get().strip() or None
        status = self._code_from_display(self.status_var.get(), kind="status") or "RECEIVED"
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
            serial = self.serial_var.get().strip() or (self._selected_serial or "")
            if not serial:
                raise ValueError("serial is required")

            changed = self.db.change_status(
                serial,
                self._code_from_display(self.status_var.get(), kind="status") or "RECEIVED",
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
                    "status": self._code_from_display(self.status_var.get(), kind="status") or "RECEIVED",
                }
            )
            self.refresh_list(select_serial=serial)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(self.tr("desktop_error_title"), str(exc))
            self._write_result({"ok": False, "error": str(exc)}, ok=False)

    def delete_selected(self) -> None:
        try:
            serial = self.serial_var.get().strip() or (self._selected_serial or "")
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
        self.type_var.set(self._display_value("scanner", kind="type"))
        self.model_var.set("")
        self.from_store_var.set("")
        self.to_store_var.set("")
        self.status_var.set(self._display_value("RECEIVED", kind="status"))
        self.comment_var.set("")

    def refresh_list(self, *, select_serial: str | None = None) -> None:
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)

            status_display = self.filter_status_var.get().strip()
            status = self._code_from_display(status_display, kind="status") or None
            type_display = self.filter_type_var.get().strip()
            device_type = self._code_from_display(type_display, kind="type") or None
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
    _configure_windows_dpi(root)
    try:
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(family="Segoe UI", size=10)
        root.option_add("*Font", default_font)
    except Exception:
        pass
    DesktopApp(root, db_path=db_path, lang=lang)
    root.mainloop()
