# Cloudflare Worker Setup (Automatic HP Warranty) EN

This worker exposes the same API contract as the desktop app expects:

- `GET /health`
- `POST /warranty/lookup`

## 1. Prerequisites

- Cloudflare account
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

- Worker is browserless, but requests still originate from Cloudflare network IP ranges.
- HP may still block requests with `Access Denied` or captcha depending on anti-bot policy.

## Troubleshooting (404 / "There is nothing here yet")

If you open your `*.workers.dev` URL and see:

- `There is nothing here yet`
- or `/health` returns 404
- or desktop app shows `remote_worker_unavailable` with `retry_insecure_tls_failed: HTTP Error 404: Not Found`

then the Worker script is not deployed on that hostname yet (or wrong project/route is being used).

This message is also common when a **Pages** project URL is used instead of a **Worker** production URL.

### Fix from Cloudflare Dashboard

1. Open **Workers & Pages**.
2. Open Worker named exactly: `programma-rb-warranty-worker`.
3. Ensure latest version is deployed to **production**.
4. In **Settings -> Variables and Secrets**, set:
  - `WARRANTY_REMOTE_API_KEY` (secret)
  - `WARRANTY_REMOTE_TIMEOUT_MS=45000` (optional variable)
5. Re-deploy and wait until deploy status is successful.

### Expected Verification

The following must return HTTP 200 with JSON:

- `https://programma-rb-warranty-worker.<your-subdomain>.workers.dev/health`

Depending on your Cloudflare setup, the deployed Worker may instead use an account-assigned workers.dev domain such as:

- `https://<worker-assigned-subdomain>.<account-subdomain>.workers.dev/health`

Desktop config should use:

- `warranty_remote_api_url = https://programma-rb-warranty-worker.<your-subdomain>.workers.dev/warranty/lookup`
- `warranty_remote_api_key = <same secret as Cloudflare WARRANTY_REMOTE_API_KEY>`

If `/health` is still 404 after successful deploy, you are likely opening a different hostname than the one shown in the Worker's production deployment details.

## Implementation Notes (Browserless)

Worker lookup is now fully browserless:

1. Call HP search endpoint:
  - `/wcc-services/searchresult/<cc-lc>?q=<serial>&context=pdp&navigation=true`
2. Build warranty URL from `verifyResponse.data` metadata:
  - `/<cc-lc>/warrantyresult/<SEOFriendlyName>/<productSeriesOID>/model/<productNameOID>?sku=<sku>&serialnumber=<serial>`
3. Fetch warranty page HTML and parse `End date` + status.

This removes Cloudflare Browser Rendering/Chromium dependency and keeps the worker fully automatic for HP serials.
