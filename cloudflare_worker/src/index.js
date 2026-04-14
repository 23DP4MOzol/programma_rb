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

function parseHpLocale(checkerUrl) {
  const fallback = "us-en";
  const source = String(checkerUrl || "").trim();
  if (!source) return fallback;

  try {
    const parsed = new URL(source);
    if (parsed.hostname !== "support.hp.com") return fallback;
    const firstSegment = parsed.pathname.split("/").filter(Boolean)[0] || "";
    if (/^[a-z]{2}-[a-z]{2}$/i.test(firstSegment)) {
      return firstSegment.toLowerCase();
    }
  } catch {
    return fallback;
  }

  return fallback;
}

function normalizeSku(productNumber) {
  const token = String(productNumber || "").trim();
  if (!token) return "";
  return token.split("#", 1)[0].trim();
}

function htmlToText(html) {
  return String(html || "")
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<!--[\s\S]*?-->/g, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&quot;/gi, '"')
    .replace(/&#39;/gi, "'")
    .replace(/\s+/g, " ")
    .trim();
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

function extractAllEndDates(text) {
  const source = String(text || "");
  const dates = [];
  const pattern = /end\s*date\s*(?:[:\-])?\s*(\d{4}-\d{2}-\d{2}|\d{1,2}\/\d{1,2}\/\d{2,4}|\d{4}\.\d{2}\.\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})/gi;
  let match;
  while ((match = pattern.exec(source)) !== null) {
    const normalized = normalizeDateToken(match[1]);
    if (normalized) dates.push(normalized);
  }
  return [...new Set(dates)];
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

async function lookupHpWarranty({ serial, checkerUrl, env }) {
  const serialToken = String(serial || "").replace(/[^A-Za-z0-9\-]/g, "");
  if (!serialToken) {
    return {
      ok: false,
      reason: "missing_serial",
      details: "Serial is empty",
    };
  }

  const locale = parseHpLocale(checkerUrl);
  const checkerEntryUrl = `https://support.hp.com/${locale}/check-warranty`;
  const timeoutMs = Number.parseInt(String(env.WARRANTY_REMOTE_TIMEOUT_MS || "45000"), 10) || 45000;

  const commonHeaders = {
    "user-agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "accept-language": "en-US,en;q=0.9",
  };

  try {
    const searchUrl = new URL(`https://support.hp.com/wcc-services/searchresult/${locale}`);
    searchUrl.searchParams.set("q", serialToken);
    searchUrl.searchParams.set("context", "pdp");
    searchUrl.searchParams.set("navigation", "true");

    const searchResponse = await fetch(searchUrl.toString(), {
      method: "GET",
      headers: {
        ...commonHeaders,
        accept: "application/json, text/plain, */*",
        referer: checkerEntryUrl,
      },
      cf: { cacheTtl: 0, cacheEverything: false },
      redirect: "follow",
      signal: AbortSignal.timeout(timeoutMs),
    });

    if (!searchResponse.ok) {
      return {
        ok: false,
        reason: "remote_search_http_error",
        details: `HP searchresult HTTP ${searchResponse.status}`,
        checker_url: checkerEntryUrl,
      };
    }

    let searchJson;
    try {
      searchJson = await searchResponse.json();
    } catch {
      return {
        ok: false,
        reason: "remote_search_invalid_json",
        details: "HP searchresult did not return JSON",
        checker_url: checkerEntryUrl,
      };
    }

    const verifyNode = searchJson?.data?.verifyResponse;
    const verifyCode = Number(verifyNode?.code || 0);
    const verifyData = verifyNode?.data;
    if (verifyCode !== 200 || !verifyData) {
      return {
        ok: false,
        reason: "remote_search_no_device",
        details: String(verifyNode?.message || searchJson?.message || "Device not found from HP search"),
        checker_url: checkerEntryUrl,
      };
    }

    const seoName = String(verifyData.SEOFriendlyName || "").trim();
    const seriesOid = String(verifyData.productSeriesOID || "").trim();
    const modelOid = String(verifyData.productNameOID || "").trim();
    const sku = normalizeSku(verifyData.altProductNumber || verifyData.productNumber || "");
    const serialOut = String(verifyData.serialNumber || serialToken).trim() || serialToken;

    if (!seoName || !seriesOid || !modelOid) {
      return {
        ok: false,
        reason: "remote_search_incomplete_metadata",
        details: "HP searchresult missing required route metadata",
        checker_url: checkerEntryUrl,
      };
    }

    const warrantyUrl = new URL(`https://support.hp.com/${locale}/warrantyresult/${seoName}/${seriesOid}/model/${modelOid}`);
    if (sku) warrantyUrl.searchParams.set("sku", sku);
    warrantyUrl.searchParams.set("serialnumber", serialOut);

    const warrantyResponse = await fetch(warrantyUrl.toString(), {
      method: "GET",
      headers: {
        ...commonHeaders,
        accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        referer: checkerEntryUrl,
      },
      cf: { cacheTtl: 0, cacheEverything: false },
      redirect: "follow",
      signal: AbortSignal.timeout(timeoutMs),
    });

    if (!warrantyResponse.ok) {
      return {
        ok: false,
        reason: "remote_warranty_http_error",
        details: `HP warranty page HTTP ${warrantyResponse.status}`,
        checker_url: warrantyUrl.toString(),
      };
    }

    const html = await warrantyResponse.text();
    const normalized = htmlToText(html);
    const lower = normalized.toLowerCase();

    if (lower.includes("access denied")) {
      return {
        ok: false,
        reason: "remote_access_denied",
        details: "HP returned Access Denied from Cloudflare worker network",
        checker_url: warrantyUrl.toString(),
        summary: summaryFromText(normalized),
      };
    }

    if (lower.includes("captcha") || lower.includes("verify you are human") || lower.includes("recaptcha")) {
      return {
        ok: false,
        reason: "remote_blocked_by_captcha",
        details: "HP page requires captcha/human verification in Cloudflare worker context",
        checker_url: warrantyUrl.toString(),
        summary: summaryFromText(normalized),
      };
    }

    let status = deriveStatus(normalized);
    const endDates = extractAllEndDates(normalized);
    const endDate = endDates.length ? [...endDates].sort().reverse()[0] : "";
    const summary = summaryFromText(normalized);

    if (status === "UNKNOWN" && endDate) {
      const today = new Date().toISOString().slice(0, 10);
      status = endDate >= today ? "ACTIVE" : "EXPIRED";
    }

    if (status === "UNKNOWN" && !endDate) {
      return {
        ok: false,
        reason: "remote_no_warranty_text_found",
        details: "Cloudflare worker could not detect warranty fields from HP result page",
        checker_url: warrantyUrl.toString(),
        summary,
      };
    }

    return {
      ok: true,
      status,
      end_date: endDate,
      summary,
      checker_url: warrantyUrl.toString(),
    };
  } catch (err) {
    return {
      ok: false,
      reason: "remote_worker_error",
      details: String(err && err.message ? err.message : err),
      checker_url: checkerEntryUrl,
    };
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
