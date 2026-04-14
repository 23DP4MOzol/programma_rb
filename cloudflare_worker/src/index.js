import puppeteer from "@cloudflare/puppeteer";

function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    },
  });
}

function normalizeMake(make) {
  const normalized = String(make || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
  if (!normalized) return "";
  return normalized.split(" ", 1)[0];
}

function safeHpCheckerUrl(checkerUrl, serial) {
  let base = String(checkerUrl || "").trim() || "https://support.hp.com/us-en/check-warranty";

  if (!base.startsWith("https://support.hp.com/")) {
    base = "https://support.hp.com/us-en/check-warranty";
  }

  const serialToken = String(serial || "").replace(/[^A-Za-z0-9\-]/g, "");
  if (!serialToken) {
    return base;
  }

  if (/serialnumber=/i.test(base)) {
    return base;
  }

  const sep = base.includes("?") ? "&" : "?";
  return `${base}${sep}serialnumber=${encodeURIComponent(serialToken)}`;
}

function deriveStatus(text) {
  const lower = String(text || "").toLowerCase();
  if (!lower) return "UNKNOWN";

  const expiredTerms = ["out of warranty", "expired", "not covered", "no warranty"];
  const activeTerms = ["in warranty", "active", "covered", "valid", "care pack", "applecare"];

  if (expiredTerms.some((t) => lower.includes(t))) return "EXPIRED";
  if (activeTerms.some((t) => lower.includes(t))) return "ACTIVE";
  return "UNKNOWN";
}

function normalizeDateToken(rawValue) {
  const token = String(rawValue || "").replace(/\s+/g, " ").trim();
  if (!token) return "";

  let cleaned = token.replace(/^[\s.,:;()\[\]{}]+|[\s.,:;()\[\]{}]+$/g, "");
  if (/^\d{4}\.\d{2}\.\d{2}$/.test(cleaned)) {
    cleaned = cleaned.replace(/\./g, "-");
  }

  const parsed = Date.parse(cleaned);
  if (!Number.isNaN(parsed)) {
    return new Date(parsed).toISOString().slice(0, 10);
  }
  return "";
}

function extractEndDate(text) {
  const pattern = /\b(\d{4}-\d{2}-\d{2}|\d{1,2}\/\d{1,2}\/\d{2,4}|\d{4}\.\d{2}\.\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b/i;
  const match = String(text || "").match(pattern);
  if (!match) return "";
  return normalizeDateToken(match[1]);
}

function summaryFromText(text) {
  const hints = ["coverage status", "warranty", "care pack", "expired", "active", "access denied"];
  const lines = String(text || "")
    .split("\n")
    .map((x) => x.trim())
    .filter(Boolean);

  for (const line of lines) {
    const lower = line.toLowerCase();
    if (hints.some((h) => lower.includes(h))) {
      return line.slice(0, 220);
    }
  }

  return String(text || "").replace(/\s+/g, " ").trim().slice(0, 220);
}

async function dismissCookieButtons(page) {
  const labels = ["accept all", "accept", "reject all"];
  await page.evaluate((buttonLabels) => {
    const all = Array.from(document.querySelectorAll("button"));
    for (const btn of all) {
      const text = (btn.textContent || "").toLowerCase().trim();
      if (buttonLabels.some((label) => text.includes(label))) {
        btn.click();
        break;
      }
    }
  }, labels);
}

async function lookupHpWarranty({ serial, checkerUrl, env }) {
  const serialToken = String(serial || "").replace(/[^A-Za-z0-9\-]/g, "");
  if (!serialToken) {
    return {
      ok: false,
      reason: "missing_serial",
      details: "Serial is empty",
    };
  }

  const targetUrl = safeHpCheckerUrl(checkerUrl, serialToken);
  const timeoutMs = Number.parseInt(String(env.WARRANTY_REMOTE_TIMEOUT_MS || "45000"), 10) || 45000;

  let browser;
  try {
    browser = await puppeteer.launch(env.BROWSER);
    const page = await browser.newPage();

    await page.goto(targetUrl, { waitUntil: "domcontentloaded", timeout: timeoutMs });
    await dismissCookieButtons(page);
    await new Promise((resolve) => setTimeout(resolve, 2200));

    const bodyText = await page.evaluate(() => (document.body ? document.body.innerText || "" : ""));
    const normalized = String(bodyText || "").replace(/\s+/g, " ").trim();
    const lower = normalized.toLowerCase();

    if (lower.includes("access denied")) {
      return {
        ok: false,
        reason: "remote_access_denied",
        details: "HP returned Access Denied from Cloudflare worker network",
        checker_url: targetUrl,
        summary: summaryFromText(normalized),
      };
    }

    if (lower.includes("captcha") || lower.includes("verify you are human") || lower.includes("recaptcha")) {
      return {
        ok: false,
        reason: "remote_blocked_by_captcha",
        details: "HP page requires captcha/human verification in Cloudflare worker context",
        checker_url: targetUrl,
        summary: summaryFromText(normalized),
      };
    }

    const status = deriveStatus(normalized);
    const endDate = extractEndDate(normalized);
    const summary = summaryFromText(normalized);

    if (status === "UNKNOWN" && !endDate) {
      return {
        ok: false,
        reason: "remote_no_warranty_text_found",
        details: "Cloudflare worker could not detect warranty fields",
        checker_url: targetUrl,
        summary,
      };
    }

    return {
      ok: true,
      status,
      end_date: endDate,
      summary,
      checker_url: targetUrl,
    };
  } catch (err) {
    return {
      ok: false,
      reason: "remote_worker_error",
      details: String(err && err.message ? err.message : err),
      checker_url: targetUrl,
    };
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

function isAuthorized(request, env) {
  const configuredKey = String(env.WARRANTY_REMOTE_API_KEY || "").trim();
  if (!configuredKey) return true;

  const headerKey = String(request.headers.get("X-API-Key") || "").trim();
  const auth = String(request.headers.get("Authorization") || "").trim();
  const bearer = auth.toLowerCase().startsWith("bearer ") ? auth.slice(7).trim() : "";

  return headerKey === configuredKey || bearer === configuredKey;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "GET" && url.pathname === "/health") {
      return jsonResponse({ ok: true, service: "warranty-worker-cf" });
    }

    if (request.method === "POST" && url.pathname === "/warranty/lookup") {
      if (!isAuthorized(request, env)) {
        return jsonResponse({ ok: false, reason: "unauthorized", details: "Invalid API key" }, 401);
      }

      let payload;
      try {
        payload = await request.json();
      } catch {
        return jsonResponse({ ok: false, reason: "bad_request", details: "Invalid JSON body" }, 400);
      }

      const make = normalizeMake(payload && payload.make);
      const serial = String((payload && payload.serial) || "").trim();
      const checkerUrl = payload && payload.checker_url ? String(payload.checker_url) : "";

      if (make !== "hp") {
        return jsonResponse({
          ok: false,
          reason: "remote_make_not_supported",
          details: `Cloudflare worker currently supports HP only (got: ${String((payload && payload.make) || "")})`,
          checker_url: checkerUrl,
        });
      }

      const result = await lookupHpWarranty({ serial, checkerUrl, env });
      return jsonResponse(result, result.ok ? 200 : 200);
    }

    return jsonResponse({ ok: false, reason: "not_found" }, 404);
  },
};
