from __future__ import annotations

import traceback
from pathlib import Path


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    log_path = base_dir / "programma_rb_error.log"

    try:
        from desktop_app import run_desktop

        run_desktop(db_path=base_dir / "inventory.db", lang="lv")
    except Exception:  # noqa: BLE001
        log_path.write_text(traceback.format_exc(), encoding="utf-8")
        # Try to show a message box without relying on console.
        try:
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "programma_rb",
                "Failed to start. See programma_rb_error.log",
            )
            root.destroy()
        except Exception:
            pass


if __name__ == "__main__":
    main()
