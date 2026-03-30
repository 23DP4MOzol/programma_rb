# Rimi Baltic Inventory Prototype

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

- `assets/logo_white.png` (ieteicams) vai `assets/logo.png` — parādīsies augšā galvenē
- (ja izmanto tikai vienu failu) `assets/logo_red.png` — ieteicamais variants jaunajai baltajai galvenei
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

Šajā versijā Web UI ir izņemts (programma ir paredzēta kā Desktop aplikācija).

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

- `assets/logo_white.png` (recommended) or `assets/logo.png` — shown in the header
- (if you only use one file) `assets/logo_red.png` — recommended for the new white header
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

In this version the Web UI is removed (the program is intended as a Desktop app).

### Statuses

Allowed values:

- `RECEIVED`, `PREPARING`, `PREPARED`, `SENT`, `IN_USE`, `RETURNED`, `RETIRED`

### Notes

- Default DB file is `inventory.db` (override with `--db c:\path\to\file.db`).
- You can edit LV/EN texts in `i18n.json`.
