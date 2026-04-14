# Rimi Baltic Inventory System

[Latviešu](#latviešu) | [English](#english)

## Latviešu

Vienota inventarizācijas sistēma ar diviem klientiem:

- PC aplikācija (Tkinter, Python)
- Web aplikācija (`docs`) + Android WebView APK (TC52 u.c.)

Abi klienti izmanto vienu Supabase backend un vienotu serial apstrādes loģiku.

### Arhitektūra

- Backend: Supabase (`devices`, `device_prefix_rules`, `device_audit_log`)
- Desktop: `desktop_app.py`
- Web: `docs/index.html` + `docs/app.js`
- Android wrapper: `android/` (WebView)

### Funkciju matrica (ko vari darīt kurā aplikācijā)

| Funkcija | PC programma | Web / WebView APK | Piezīmes |
|---|---|---|---|
| Scanner serial skenēšana | Jā | Jā | Atbalsta `S + 13/14` un plain `13/14` |
| Laptop QR (1. tokens = serial) | Jā | Jā | Piem.: `5CG...,...,...` |
| Auto ielāde no DB pēc serial | Jā | Jā | Atrod esošu ierīci un aizpilda formu |
| Prefix auto-atpazīšana | Jā | Jā | Prioritāte: DB noteikumi -> fallback |
| Learning no vēsturiskajiem serial | Jā | Jā | Mainīga prefix garuma modelis |
| Manuāla pievienošana / update | Jā | Jā | Konflikti tiek noķerti ar `updated_at` |
| Offline queue | Jā | Jā | PC: `pending_ops.json`, Web: localStorage queue |
| Manuāls Sync now | Jā | Jā | PC poga + Web poga |
| CSV eksports | Nē | Jā | Eksportē redzamos (filtrētos) ierakstus |
| Audit logs skatīšana (admin) | Jā | Jā | Pieejams tikai admin tiesībām |
| Prefix noteikumu pārvaldība (admin) | Jā | Jā | CRUD panelis prefiksu noteikumiem |
| Diagnostikas panelis | Jā | Jā | Rāda lomu, queue, API veselību, pēdējo sync |
| Rediģēt identity laukus (serial/type/model) | Ar noteikumiem | Ar noteikumiem | Esošiem ierakstiem tikai `device_admin` |

### PC programmas funkcijas

- Klasiska forma + saraksts
- Kamera skenēšana (ja pieejams `opencv/pyzbar`)
- PIN aizsardzība sensitīvām darbībām
- Admin audit viewer logs
- Admin prefiksu noteikumu panelis (CRUD)
- Diagnostikas panelis (queue, API, loma, pēdējā sync)
- Konflikta paziņojums, ja cits klients jau atjaunojis ierakstu

Palaišana (PowerShell):

```powershell
python .\main.py
# vai
python .\main.py ui
```

Ja `.bat`/CMD ir bloķēts, vari palaist `programma_rb.pyw`.

### Web / WebView APK funkcijas

- Ātra skenēšana (`serial` input + Enter)
- Queue badge (`Queued: N`)
- Sync statuss + versija footerī
- Draft atjaunošana pēc pārlādes
- Offline save queue ar automātisku sinhronizāciju
- Manuāls `Sync now`
- `Export CSV`
- Audit karte (admin pieejām)

### Android WebView APK

- Orientācija fiksēta uz portrait
- Ekrāns netiek izslēgts skenēšanas laikā (`KEEP_SCREEN_ON`)
- Debug build workflow: `.github/workflows/build_webview_apk.yml`
- Production signed workflow (stable/test tracks): `.github/workflows/build_webview_apk_production.yml`

### Supabase migrācija (obligāti)

Izpildi:

- `supabase/migrations/20260407_hardening_and_audit.sql`

Skripts pievieno:

- `devices` ierobežojumus un indeksus
- `device_prefix_rules` (vienots prefix avots PC + Web)
- `device_audit_log` + trigger auditu
- RLS politikas un `device_admin` sadalījumu

RLS pamatprincips:

- `anon/authenticated` var lasīt/pievienot/atjaunot
- esošiem ierakstiem `serial/device_type/model` drīkst mainīt tikai `device_admin`
- dzēšana tikai `device_admin`
- audit log lasīšana tikai `device_admin`

`device_admin` tiek ņemts no JWT:

- `app_metadata.device_admin=true` vai
- `device_admin=true`

### Automātiska HP garantija (attālināts serviss)

Ja šajā datorā uzņēmuma politika bloķē pārlūka automatizāciju, HP garantijas auto-nolasīšanu var darbināt caur atsevišķu servisu uz neierobežotas mašīnas.

- Servisa kods: `remote_worker/hp_warranty_worker.py`
- Ātra uzstādīšana: `remote_worker/README.md`

Desktop klientam iestati:

```powershell
$env:WARRANTY_REMOTE_API_URL = "http://<worker-host>:8787/warranty/lookup"
$env:WARRANTY_REMOTE_API_KEY = "change-me"
```

Vai pievieno šīs vērtības `app_config.json`:

- `warranty_remote_api_url`
- `warranty_remote_api_key`
- `warranty_remote_api_timeout_sec`

Cloudflare variants:

- `cloudflare_worker/` satur gatavu Worker projektu (`/health`, `/warranty/lookup`)
- konfigurācija: `cloudflare_worker/wrangler.toml`
- soļi: `cloudflare_worker/README.md`

### CLI (opcioniāli)

```powershell
python .\main.py init --lang lv
python .\main.py add --lang lv --serial SN-001 --type scanner --model Zebra-DS2208 --from-store RIMI001 --to-store RIMI123 --status RECEIVED
python .\main.py status --lang lv --serial SN-001 --new PREPARED --comment "Sapakots nosūtīšanai"
python .\main.py list --lang lv
python .\main.py get --lang lv --serial SN-001
python .\main.py delete --lang lv --serial SN-001
```

### Testi

```powershell
python -m unittest tests.test_serial_parsing
```

Backup un atjaunošanas procedūra: `BACKUP_RECOVERY_RUNBOOK.md`.

Operāciju release kontrolsaraksts: `OPERATIONS_RELEASE_CHECKLIST.md`.

## English

Unified inventory system with two clients:

- PC app (Tkinter, Python)
- Web app (`docs`) + Android WebView APK

Both clients use the same Supabase backend and aligned serial parsing behavior.

### Architecture

- Backend: Supabase (`devices`, `device_prefix_rules`, `device_audit_log`)
- Desktop: `desktop_app.py`
- Web: `docs/index.html` + `docs/app.js`
- Android wrapper: `android/` (WebView)

### Feature matrix (what you can do where)

| Feature | PC app | Web / WebView APK | Notes |
|---|---|---|---|
| Scanner serial scanning | Yes | Yes | Supports `S + 13/14` and plain `13/14` |
| Laptop QR (first token as serial) | Yes | Yes | Example: `5CG...,...,...` |
| Auto-load device by serial | Yes | Yes | Existing device fields auto-filled |
| Prefix auto-detection | Yes | Yes | Priority: DB rules -> fallback |
| Learning from serial history | Yes | Yes | Variable-length prefix learning |
| Manual add / update | Yes | Yes | Uses conflict-safe `updated_at` checks |
| Offline queue | Yes | Yes | PC: `pending_ops.json`, Web: localStorage queue |
| Manual Sync now | Yes | Yes | Dedicated action in both clients |
| CSV export | No | Yes | Exports currently visible filtered rows |
| Audit logs viewer (admin) | Yes | Yes | Admin-only visibility |
| Prefix rules management (admin) | Yes | Yes | CRUD panel for prefix rules |
| Diagnostics panel | Yes | Yes | Shows role, queue, API health, last sync |
| Edit identity fields (serial/type/model) | Restricted | Restricted | Existing rows: admin only |

### PC app features

- Form + list workflow
- Camera scanning fallback (if `opencv/pyzbar` available)
- PIN protection for sensitive operations
- Admin audit viewer dialog
- Admin prefix rules panel (CRUD)
- Diagnostics panel (queue, API, role, last sync)
- Conflict warning when record changed elsewhere

Start (PowerShell):

```powershell
python .\main.py
# or
python .\main.py ui
```

If CMD/BAT is blocked by policy, run `programma_rb.pyw`.

### Web / WebView features

- Fast serial scan input flow
- Queue badge (`Queued: N`)
- Sync status + version in footer
- Draft restore after reload
- Offline save queue with auto-sync
- Manual `Sync now`
- `Export CSV`
- Audit panel (admin permissions)

### Android WebView APK

- Orientation locked to portrait
- Keep-screen-on for uninterrupted scanning
- Debug build workflow: `.github/workflows/build_webview_apk.yml`
- Production signed workflow (stable/test tracks): `.github/workflows/build_webview_apk_production.yml`

### Supabase migration (required)

Run:

- `supabase/migrations/20260407_hardening_and_audit.sql`

This migration adds:

- `devices` constraints and indexes
- `device_prefix_rules` (shared rules source for PC + Web)
- `device_audit_log` + trigger-based auditing
- RLS policies and `device_admin` role split

RLS baseline:

- `anon/authenticated` can read/insert/update
- changing `serial/device_type/model` on existing rows requires `device_admin`
- delete requires `device_admin`
- audit log read requires `device_admin`

`device_admin` is read from JWT claims:

- `app_metadata.device_admin=true` or
- `device_admin=true`

### Automatic HP Warranty (Remote Worker)

If company policy blocks browser automation on this PC, run HP auto warranty lookup through a separate worker on an unrestricted machine.

- Worker code: `remote_worker/hp_warranty_worker.py`
- Quick setup: `remote_worker/README.md`

Set on desktop client:

```powershell
$env:WARRANTY_REMOTE_API_URL = "http://<worker-host>:8787/warranty/lookup"
$env:WARRANTY_REMOTE_API_KEY = "change-me"
```

Or set these keys in `app_config.json`:

- `warranty_remote_api_url`
- `warranty_remote_api_key`
- `warranty_remote_api_timeout_sec`

Cloudflare option:

- `cloudflare_worker/` contains a ready Worker project (`/health`, `/warranty/lookup`)
- config: `cloudflare_worker/wrangler.toml`
- setup steps: `cloudflare_worker/README.md`

### CLI (optional)

```powershell
python .\main.py init --lang en
python .\main.py add --lang en --serial SN-001 --type scanner --model Zebra-DS2208 --from-store RIMI001 --to-store RIMI123 --status RECEIVED
python .\main.py status --lang en --serial SN-001 --new PREPARED --comment "Packed for shipment"
python .\main.py list --lang en
python .\main.py get --lang en --serial SN-001
python .\main.py delete --lang en --serial SN-001
```

### Tests

```powershell
python -m unittest tests.test_serial_parsing
```

Backup and recovery procedure: `BACKUP_RECOVERY_RUNBOOK.md`.

Operations release checklist: `OPERATIONS_RELEASE_CHECKLIST.md`.
