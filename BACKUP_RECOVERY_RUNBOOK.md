# Backup and Recovery Runbook

## Latviesu

### 1. Mērķis
Šis runbook nosaka, kā droši veikt dublējumus un atjaunošanu Rimi Inventory sistēmai (Desktop + WebView + Supabase).

### 2. Ko obligāti dublēt
- Supabase tabulas:
  - `public.devices`
  - `public.device_prefix_rules`
  - `public.device_audit_log`
- Desktop lokālie faili (katrai darba stacijai):
  - `inventory.db` (ja tiek lietots)
  - `app_config.json`
  - `pending_ops.json`
- Android release artefakti:
  - keystore fails
  - release APK artefakti no CI
- Repo saturs (`main` zars + release tagi)

### 3. Dublēšanas grafiks
- Katru dienu (automātiski): Supabase datu dump.
- Pirms katra release: manuāls pilns dublējums + keystore verifikācija.
- Katru nedēļu: atjaunošanas tests uz test vidi.

### 4. Atjaunošana pēc incidenta
1. Apturi rakstīšanas operācijas (izslēdz klientus vai read-only režīms).
2. Atjauno Supabase no pēdējā derīgā dump.
3. Atjauno Desktop lokālos failus (ja nepieciešams).
4. Palaid `Sync now` klientos, lai izlīdzinātu rindas.
5. Verificē datus:
   - ierakstu skaits `devices`
   - pēdējie `device_audit_log` notikumi
   - `device_prefix_rules` pieejamība

### 5. Pēcatjaunošanas pārbaudes
- Web diagnostics panel rāda `Health: healthy`.
- Queue ir 0 vai zināms izskaidrojams atlikums.
- Testi izpildās:

```powershell
python -m unittest tests.test_serial_parsing tests.test_release_smoke
```

## English

### 1. Purpose
This runbook defines backup and recovery steps for the full Rimi Inventory stack (Desktop + WebView + Supabase).

### 2. Required backup scope
- Supabase tables:
  - `public.devices`
  - `public.device_prefix_rules`
  - `public.device_audit_log`
- Desktop local files (per workstation):
  - `inventory.db` (if used)
  - `app_config.json`
  - `pending_ops.json`
- Android release assets:
  - release keystore file
  - release APK artifacts from CI
- Repository state (`main` branch + release tags)

### 3. Backup cadence
- Daily (automated): Supabase data dump.
- Before each release: full manual backup + keystore integrity check.
- Weekly: recovery drill in test environment.

### 4. Incident recovery steps
1. Stop write traffic (pause clients or enable read-only mode).
2. Restore Supabase from the latest valid dump.
3. Restore Desktop local files where needed.
4. Run `Sync now` in clients to reconcile pending queues.
5. Validate data:
   - row counts in `devices`
   - recent events in `device_audit_log`
   - availability of `device_prefix_rules`

### 5. Post-recovery validation
- Web diagnostics panel shows `Health: healthy`.
- Queue is 0 or has a known explainable remainder.
- Execute verification tests:

```powershell
python -m unittest tests.test_serial_parsing tests.test_release_smoke
```
