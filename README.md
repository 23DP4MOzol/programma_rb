# programma_rb

[Latviešu](#latviešu) | [English](#english)

## Latviešu

Vienkārša lokāla ierīču uzskaites programma (Python + SQLite) ar Desktop UI (Tkinter). Ierīces tiek identificētas pēc `serial` un var mainīt tipu/modeli/veikalu/statusu.

### Prasības

- Python 3.10+ (bez ārējām bibliotekām)

### Desktop UI (programma)

Palaišana (PowerShell no šīs mapes):

```powershell
python .\main.py

# vai explicit:
python .\main.py ui
```

Ja datorā ir aizliegts CMD/BAT (Group Policy), tad dubultklikšķini `programma_rb.pyw` (drošākais “launcheris”).

Ja programma nepalaižas, paskaties `programma_rb_error.log`.

#### Logo / ikona (opcioniāli)

Lai logs izskatās “oficiālāk”, vari ielikt savu logo failu mapē `assets`:

- `assets/logo.png` (vai `assets/logo.gif`) — parādīsies augšā galvenē
- `assets/icon.ico` — loga ikona

### CLI lietošana

```powershell
python .\main.py init --lang lv
python .\main.py add --lang lv --serial SN-001 --type scanner --model Zebra-DS2208 --from-store RIMI001 --to-store RIMI123 --status RECEIVED
python .\main.py status --lang lv --serial SN-001 --new PREPARED --comment "Sapakots nosūtīšanai"
python .\main.py list --lang lv
python .\main.py get --lang lv --serial SN-001
python .\main.py delete --lang lv --serial SN-001
```

### Web UI (opcioniāli)

Ja vajag, var palaist arī Web UI pārlūkā:

```powershell
python .\main.py web --host 127.0.0.1 --port 8000

# neatver pārlūku automātiski:
python .\main.py web --no-browser
```

Atver: http://127.0.0.1:8000/

### Statusi

Atļautās vērtības:

- `RECEIVED`, `PREPARING`, `PREPARED`, `SENT`, `IN_USE`, `RETURNED`, `RETIRED`

### Piezīmes

- DB fails pēc noklusējuma ir `inventory.db` (vari mainīt ar `--db c:\path\to\file.db`).
- LV/EN tekstus vari mainīt failā `i18n.json`.

## English

Simple local device inventory app (Python + SQLite) with a desktop UI (Tkinter). Devices are identified by `serial` and you can edit type/model/store/status.

### Requirements

- Python 3.10+ (no external dependencies)

### Desktop UI (app)

Start (PowerShell in this folder):

```powershell
python .\main.py

# or explicitly:
python .\main.py ui
```

If CMD/BAT is blocked by policy, double-click `programma_rb.pyw` (safest launcher).

If it fails to start, check `programma_rb_error.log`.

#### Logo / icon (optional)

To make the window look more “official”, put your own branding into `assets`:

- `assets/logo.png` (or `assets/logo.gif`) — shown in the header
- `assets/icon.ico` — window icon

### CLI usage

```powershell
python .\main.py init --lang en
python .\main.py add --lang en --serial SN-001 --type scanner --model Zebra-DS2208 --from-store RIMI001 --to-store RIMI123 --status RECEIVED
python .\main.py status --lang en --serial SN-001 --new PREPARED --comment "Packed for shipment"
python .\main.py list --lang en
python .\main.py get --lang en --serial SN-001
python .\main.py delete --lang en --serial SN-001
```

### Web UI (optional)

If needed, you can also run a browser-based UI:

```powershell
python .\main.py web --host 127.0.0.1 --port 8000

# do not auto-open browser:
python .\main.py web --no-browser
```

Open: http://127.0.0.1:8000/

### Statuses

Allowed values:

- `RECEIVED`, `PREPARING`, `PREPARED`, `SENT`, `IN_USE`, `RETURNED`, `RETIRED`

### Notes

- Default DB file is `inventory.db` (override with `--db c:\path\to\file.db`).
- You can edit LV/EN texts in `i18n.json`.
