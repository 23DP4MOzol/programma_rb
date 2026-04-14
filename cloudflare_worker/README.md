# Cloudflare Worker Setup (Automatic HP Warranty)

This worker exposes the same API contract as the desktop app expects:

- `GET /health`
- `POST /warranty/lookup`

## 1. Prerequisites

- Cloudflare account
- Browser Rendering enabled in your Cloudflare account
- Node.js 18+

## 2. Install and Login

```powershell
cd .\cloudflare_worker
npm install
npx wrangler login
```

## Cloudflare Dashboard Form Values (Git Deploy)

Use these values in the "Set up your application" form.

- Project name: `programma_rb`
- Build command: leave empty
- Deploy command: `npx wrangler deploy`
- Non-production branch deploy command: `npx wrangler versions upload`
- Path: `/cloudflare_worker`
- API token: create new (automatic is fine)

If the dashboard requires a non-empty build command, use:

- `npm install`

Required API token permissions should include:

- Account Workers Scripts Edit
- Account Workers Tail Read
- Zone Workers Routes Edit (only if you later attach custom routes)

Environment/variables to add in Cloudflare:

- `WARRANTY_REMOTE_API_KEY` = `<your-strong-secret>` (required)
- `WARRANTY_REMOTE_TIMEOUT_MS` = `45000` (optional)

## 3. Set Secret API Key

```powershell
npx wrangler secret put WARRANTY_REMOTE_API_KEY
```

Enter a strong key when prompted.

## 4. Deploy

```powershell
npm run deploy
```

After deploy, you get a URL like:

- `https://programma-rb-warranty-worker.<your-subdomain>.workers.dev`

## 5. Verify

```powershell
Invoke-WebRequest -UseBasicParsing -Uri "https://<your-worker>.workers.dev/health"
```

## 6. Connect Desktop App

On your desktop machine, set:

```powershell
$env:WARRANTY_REMOTE_API_URL = "https://<your-worker>.workers.dev/warranty/lookup"
$env:WARRANTY_REMOTE_API_KEY = "<same-secret-you-set>"
```

Then restart desktop app.

## 7. API Request/Response Shape

Request JSON:

```json
{
  "make": "hp",
  "serial": "5CG3387KZJ",
  "checker_url": "https://support.hp.com/us-en/check-warranty"
}
```

Success response example:

```json
{
  "ok": true,
  "status": "ACTIVE",
  "end_date": "2027-10-31",
  "summary": "Coverage status ...",
  "checker_url": "https://support.hp.com/us-en/check-warranty?serialnumber=5CG3387KZJ"
}
```

Failure response example:

```json
{
  "ok": false,
  "reason": "remote_access_denied",
  "details": "HP returned Access Denied from Cloudflare worker network",
  "checker_url": "https://support.hp.com/us-en/check-warranty?serialnumber=..."
}
```

## Important Limitations

- Cloudflare Browser Rendering uses cloud IPs; HP may still block with `Access Denied` or captcha.
- If that happens, the worker is deployed correctly, but HP anti-bot policy blocked the source network.
