# programma_rb (lokāls inventārs / local inventory)

LV: Vienkāršs Python + SQLite lokāls “backend” (ar CLI un opcionalu Web UI), lai reģistrētu skenerus/ierīces ar `serial`, modeli, izcelsmes/mērķa veikalu un statusu.

EN: Simple local Python + SQLite “backend” (with CLI and optional Web UI) to track scanners/devices by `serial`, model, source/target store and status.

## Prasības / Requirements

- Python 3.10+ (bez ārējām bibliotekām / no external dependencies)

## CLI lietošana / CLI usage

PowerShell no šīs mapes / from this folder:

```powershell
python .\main.py init --lang lv
python .\main.py add --lang lv --serial SN-001 --type scanner --model Zebra-DS2208 --from-store RIMI001 --to-store RIMI123 --status RECEIVED
python .\main.py status --lang lv --serial SN-001 --new PREPARED --comment "Sapakots nosūtīšanai"
python .\main.py list --lang en
python .\main.py get --lang en --serial SN-001
python .\main.py delete --lang lv --serial SN-001
```

## Desktop UI (programma / app)

LV: Galvenais variants ir Desktop logs (Tkinter) ar formu + sarakstu. Palaižot `main.py` bez argumentiem, automātiski atveras interfeiss (nevis pārlūks).

EN: Primary interface is a desktop window (Tkinter) with a form + list. Running `main.py` without arguments opens the interface (not a browser).

Start:

```powershell
python .\main.py

# or explicitly:
python .\main.py ui
```

LV: Vari arī vienkārši dubultklikšķināt start_ui.bat.
EN: You can also double-click start_ui.bat.

LV: Ja start_ui.bat neko neatver, palaid start_ui_debug.bat (tas parādīs kļūdu tekstu) un paskaties start_ui.log.
EN: If start_ui.bat opens nothing, run start_ui_debug.bat (shows error text) and check start_ui.log.

## Web UI (opcioniāli / optional)

LV: Ja vajag, var palaist arī Web UI pārlūkā.
EN: If needed, you can also run a browser-based UI.

```powershell
python .\main.py web --host 127.0.0.1 --port 8000

# do not auto-open browser / neatver pārlūku:
python .\main.py web --no-browser
```

Open / Atver:

- http://127.0.0.1:8000/

LV/EN tekstus vari mainīt failā `i18n.json`.
EN: You can change LV/EN texts in `i18n.json`.

## Statusi / Statuses

Atļautās vērtības / Allowed values:

- `RECEIVED`, `PREPARING`, `PREPARED`, `SENT`, `IN_USE`, `RETURNED`, `RETIRED`

## Piezīmes / Notes

- DB fails pēc noklusējuma ir `inventory.db` (vari mainīt ar `--db c:\path\to\file.db`).
- Default DB file is `inventory.db` (override with `--db c:\path\to\file.db`).
