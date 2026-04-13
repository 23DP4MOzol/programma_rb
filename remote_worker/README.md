# Remote Warranty Worker (HP Auto Mode)

This service lets the desktop app run warranty checks automatically through an unrestricted machine.

## What It Does

- Exposes `POST /warranty/lookup`.
- Supports HP automatic lookup with Playwright browser automation.
- Returns JSON that `desktop_app.py` can consume directly.

## 1. Install

```powershell
cd .\remote_worker
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install
```

## 2. Run Worker

```powershell
$env:WARRANTY_REMOTE_API_KEY = "change-me"
$env:WARRANTY_REMOTE_HEADLESS = "1"
$env:WARRANTY_REMOTE_TIMEOUT_MS = "45000"
uvicorn hp_warranty_worker:app --host 0.0.0.0 --port 8787
```

Optional:

- `WARRANTY_REMOTE_BROWSER_CHANNEL=msedge` to force Edge channel.

## 3. Point Desktop App to Worker

Set on desktop machine:

```powershell
$env:WARRANTY_REMOTE_API_URL = "http://<worker-host>:8787/warranty/lookup"
$env:WARRANTY_REMOTE_API_KEY = "change-me"
```

Or place the same values in `app_config.json` keys:

- `warranty_remote_api_url`
- `warranty_remote_api_key`
- `warranty_remote_api_timeout_sec`

## 4. Quick Health Check

```powershell
Invoke-WebRequest -UseBasicParsing -Uri "http://<worker-host>:8787/health"
```

## Notes

- If worker returns `remote_access_denied`, your worker machine/network is also blocked by HP/Akamai.
- If worker returns `remote_blocked_by_captcha`, run it on a cleaner network/IP or with a browser profile that passes HP checks.
