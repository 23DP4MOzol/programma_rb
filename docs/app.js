const SUPABASE_URL = "https://qvlduxpdcwgmokjdsdfp.supabase.co";
const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF2bGR1eHBkY3dnbW9ramRzZGZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ5Mzk5MzMsImV4cCI6MjA5MDUxNTkzM30.3HiNhJKLrMmc0I11Y7qMS73fi0b1XUaEorTAL6wJOsk";

const SCANNER_SERIAL_RE = /^S\d{13,14}$/i;
const PLAIN_SCANNER_RE = /^\d{13,14}$/;
const GENERIC_SERIAL_RE = /^[A-Z0-9]{8,20}$/;

const PREFIX_HINTS = {
  "D2:18": { device_type: "scanner", make: "Zebra", model: "TC51" },
  "D2:19": { device_type: "scanner", make: "Zebra", model: "TC52" },
  "D2:20": { device_type: "scanner", make: "Zebra", model: "TC52" },
  "D2:21": { device_type: "scanner", make: "Zebra", model: "TC52" },
  "D2:24": { device_type: "scanner", make: "Zebra", model: "TC52" },
  "A3:5CG": { device_type: "laptop", make: "HP", model: "EliteBook 840 G10" },
};

const els = {
  serial: document.getElementById("serial"),
  statusText: document.getElementById("status"),
  type: document.getElementById("type"),
  statusSelect: document.getElementById("statusSelect"),
  make: document.getElementById("make"),
  model: document.getElementById("model"),
  fromStore: document.getElementById("fromStore"),
  toStore: document.getElementById("toStore"),
  comment: document.getElementById("comment"),
  save: document.getElementById("save"),
  clear: document.getElementById("clear"),
  devicesList: document.getElementById("devicesList"),
  listStatus: document.getElementById("listStatus"),
  listFilter: document.getElementById("listFilter"),
  refreshList: document.getElementById("refreshList"),
  lookupSerial: document.getElementById("lookupSerial"),
  lookupLoad: document.getElementById("lookupLoad"),
};

let devicesCache = [];
let scanTimer = null;

function setStatus(message, tone = "info") {
  els.statusText.textContent = message;
  if (tone === "error") {
    els.statusText.style.color = "#b00020";
  } else if (tone === "ok") {
    els.statusText.style.color = "#0a7a2f";
  } else {
    els.statusText.style.color = "#6b6b6b";
  }
}

function setIdentityEditable(enabled) {
  els.type.disabled = !enabled;
  els.make.readOnly = !enabled;
  els.model.readOnly = !enabled;
}

function cleanToken(value) {
  return String(value || "")
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, "");
}

function tokenizeScan(rawValue) {
  return String(rawValue || "")
    .toUpperCase()
    .split(/[\s,;|]+/)
    .map((x) => cleanToken(x))
    .filter(Boolean);
}

function isScannerToken(token) {
  return SCANNER_SERIAL_RE.test(token || "");
}

function isPlainScannerToken(token) {
  return PLAIN_SCANNER_RE.test(token || "");
}

function isGenericToken(token) {
  return GENERIC_SERIAL_RE.test(token || "");
}

function extractPreferredSerial(rawValue) {
  const tokens = tokenizeScan(rawValue);
  if (!tokens.length) return null;

  const mode = String(els.type?.value || "scanner").toLowerCase();
  const hasDelimitedPayload = /[,;|]/.test(String(rawValue || ""));

  const scanner = tokens.find((t) => isScannerToken(t));
  if (scanner) return scanner;

  const plainScanner = tokens.find((t) => isPlainScannerToken(t));
  if (plainScanner) return plainScanner;

  if (tokens.length > 1) {
    const first = tokens[0];
    if ((mode === "laptop" || hasDelimitedPayload) && isGenericToken(first)) return first;
    return null;
  }

  const only = tokens[0];
  if (isScannerToken(only) || isPlainScannerToken(only)) {
    return only;
  }
  if ((mode === "laptop" || mode === "other") && isGenericToken(only)) return only;
  return null;
}

function normalizeForStore(token) {
  const t = cleanToken(token);
  if (isScannerToken(t)) return t.slice(1);
  return t;
}

function serialVariants(token) {
  const t = cleanToken(token);
  if (!t) return [];

  const out = new Set([t]);
  if (isScannerToken(t)) out.add(t.slice(1));
  if (isPlainScannerToken(t)) out.add(`S${t}`);

  const normalized = normalizeForStore(t);
  if (normalized) out.add(normalized);

  return Array.from(out);
}

function sanitizeSerialField(value) {
  const raw = String(value || "").toUpperCase();
  if (!raw) return "";

  // Keep delimiters while typing so multi-token QR payloads can be parsed.
  return raw.replace(/[^A-Z0-9,;|\s]/g, "").slice(0, 20);
}

function sanitizeLookupField(value) {
  const raw = String(value || "").toUpperCase();
  if (!raw) return "";

  // Same behavior for lookup/paste workflows.
  return raw.replace(/[^A-Z0-9,;|\s]/g, "").slice(0, 20);
}

function splitModel(modelText) {
  const text = String(modelText || "").trim();
  if (!text) return ["", ""];
  const parts = text.split(" ", 2);
  return parts.length === 1 ? [parts[0], ""] : [parts[0], parts[1]];
}

function composeModel(make, model) {
  const mk = String(make || "").trim();
  const md = String(model || "").trim();
  if (!mk && !md) return "";
  if (!mk) return md;
  if (!md) return mk;
  if (md.toLowerCase().startsWith(mk.toLowerCase())) return md;
  return `${mk} ${md}`;
}

function getPrefixKey(token) {
  const t = cleanToken(token);
  if (isScannerToken(t)) {
    return `D2:${t.slice(1, 3)}`;
  }
  if (isPlainScannerToken(t)) {
    return `D2:${t.slice(0, 2)}`;
  }
  if (isGenericToken(t)) {
    return `A3:${t.slice(0, 3)}`;
  }
  return "";
}

function getTokenFamilyAndComparable(token) {
  const t = cleanToken(token);
  if (!t) return null;
  if (isScannerToken(t)) {
    return { family: "scanner", comparable: t.slice(1) };
  }
  if (isPlainScannerToken(t)) {
    return { family: "scanner", comparable: t };
  }
  if (isGenericToken(t)) {
    return { family: "generic", comparable: t };
  }
  return null;
}

function getLearningPrefixCandidates(token) {
  const info = getTokenFamilyAndComparable(token);
  if (!info || !info.comparable) return [];

  const minLen = info.family === "scanner" ? 2 : 3;
  const maxLen = Math.min(info.comparable.length, info.family === "scanner" ? 6 : 7);
  const out = [];

  for (let len = maxLen; len >= minLen; len -= 1) {
    out.push({ family: info.family, prefix: info.comparable.slice(0, len), len });
  }
  return out;
}

function resetMutableFields() {
  els.statusSelect.value = "RECEIVED";
  els.fromStore.value = "";
  els.toStore.value = "";
  els.comment.value = "";
}

function resetIdentityFields() {
  els.type.value = "scanner";
  els.make.value = "";
  els.model.value = "";
}

function resetForm() {
  els.serial.value = "";
  resetIdentityFields();
  resetMutableFields();
  setIdentityEditable(true);
}

function fillFormFromDevice(device) {
  els.type.value = device.device_type || "scanner";
  const [make, model] = splitModel(device.model || "");
  els.make.value = make;
  els.model.value = model;
  els.statusSelect.value = device.status || "RECEIVED";
  els.fromStore.value = device.from_store || "";
  els.toStore.value = device.to_store || "";
  els.comment.value = device.comment || "";
  setIdentityEditable(false);
}

function applyGuess(guess) {
  setIdentityEditable(true);
  els.type.value = guess.device_type || "scanner";
  if (guess.make) {
    els.make.value = guess.make;
  }
  if (guess.model) {
    els.model.value = guess.model;
  }
}

function guessFromCache(token) {
  const scanInfo = getTokenFamilyAndComparable(token);
  if (!scanInfo) return null;

  const learnedRows = [];
  for (const row of devicesCache) {
    if (!row.model) continue;
    const rowToken = extractPreferredSerial(row.serial || "");
    if (!rowToken) continue;
    const rowInfo = getTokenFamilyAndComparable(rowToken);
    if (!rowInfo || rowInfo.family !== scanInfo.family) continue;

    learnedRows.push({
      comparable: rowInfo.comparable,
      device_type: row.device_type || "scanner",
      model: row.model,
    });
  }

  if (!learnedRows.length) return null;

  const candidates = getLearningPrefixCandidates(token);
  for (const candidate of candidates) {
    const counts = new Map();
    let total = 0;

    for (const row of learnedRows) {
      if (!row.comparable.startsWith(candidate.prefix)) continue;
      total += 1;
      const k = `${row.device_type}||${row.model}`;
      counts.set(k, (counts.get(k) || 0) + 1);
    }

    if (!total || !counts.size) continue;

    let bestKey = "";
    let bestCount = 0;
    let secondBest = 0;
    for (const [k, count] of counts.entries()) {
      if (count > bestCount) {
        secondBest = bestCount;
        bestCount = count;
        bestKey = k;
      } else if (count > secondBest) {
        secondBest = count;
      }
    }

    const confidence = bestCount / total;
    const clearWinner = counts.size === 1 || confidence >= 0.7 || (bestCount >= 3 && bestCount - secondBest >= 2);
    if (!clearWinner) continue;

    const [device_type, fullModel] = bestKey.split("||");
    const [make, model] = splitModel(fullModel || "");
    return { device_type, make, model };
  }

  return null;
}

async function restRequest(path, { method = "GET", body = null, prefer = "" } = {}) {
  const headers = {
    apikey: SUPABASE_KEY,
    Authorization: `Bearer ${SUPABASE_KEY}`,
  };
  if (body !== null) headers["Content-Type"] = "application/json";
  if (prefer) headers.Prefer = prefer;

  const response = await fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    method,
    headers,
    body: body === null ? undefined : JSON.stringify(body),
  });

  const text = await response.text();
  const json = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const msg = (json && (json.message || json.error || json.error_description)) || text || response.statusText;
    throw new Error(msg);
  }
  return json;
}

async function getDeviceBySerial(token) {
  const variants = serialVariants(token);
  if (!variants.length) return null;

  const orExpr = variants.map((v) => `serial.eq.${encodeURIComponent(v)}`).join(",");
  const path = `devices?select=*&or=(${orExpr})&order=updated_at.desc&limit=1`;
  const rows = await restRequest(path);
  return Array.isArray(rows) && rows.length ? rows[0] : null;
}

async function loadByScannedValue(rawValue) {
  const token = extractPreferredSerial(rawValue);
  if (!token) {
    if (String(rawValue || "").trim()) {
      els.serial.value = "";
      setIdentityEditable(true);
      setStatus("Serial must be S + 14 digits, or first token like laptop QR serial", "error");
    }
    return;
  }

  const cleaned = cleanToken(token);
  els.serial.value = cleaned;
  els.lookupSerial.value = cleaned;

  let device = null;
  try {
    device = await getDeviceBySerial(cleaned);
  } catch (error) {
    setStatus(`Database error: ${error.message}`, "error");
    return;
  }

  if (device) {
    fillFormFromDevice(device);
    setStatus("Loaded from database", "ok");
    return;
  }

  resetIdentityFields();
  resetMutableFields();
  setIdentityEditable(true);

  const guessed = guessFromCache(cleaned);
  if (guessed) {
    applyGuess(guessed);
    setStatus("Auto-filled from learned serial prefixes", "ok");
    return;
  }

  const hinted = PREFIX_HINTS[getPrefixKey(cleaned)] || null;
  if (hinted) {
    applyGuess(hinted);
    setStatus("Auto-filled by known prefix", "ok");
    return;
  }

  setStatus("New device detected. Fill Type/Make/Model and save.");
}

async function saveDevice() {
  const token = extractPreferredSerial(els.serial.value);
  if (!token) {
    setStatus("Serial must be valid before saving", "error");
    return;
  }

  const cleaned = cleanToken(token);
  els.serial.value = cleaned;

  let existing = null;
  try {
    existing = await getDeviceBySerial(cleaned);
  } catch (error) {
    setStatus(`Lookup failed: ${error.message}`, "error");
    return;
  }

  const editPayload = {
    from_store: els.fromStore.value.trim(),
    to_store: els.toStore.value.trim(),
    status: els.statusSelect.value,
    comment: els.comment.value.trim(),
  };

  try {
    if (existing) {
      const path = `devices?id=eq.${encodeURIComponent(existing.id)}`;
      await restRequest(path, { method: "PATCH", body: editPayload, prefer: "return=minimal" });
      setStatus("Updated existing device", "ok");
    } else {
      const insertPayload = {
        serial: normalizeForStore(cleaned),
        device_type: (els.type.value || "scanner").trim() || "scanner",
        model: composeModel(els.make.value, els.model.value),
        ...editPayload,
      };
      await restRequest("devices", { method: "POST", body: insertPayload, prefer: "return=minimal" });
      setStatus("Added new device", "ok");
    }
  } catch (error) {
    setStatus(`Save failed: ${error.message}`, "error");
    return;
  }

  await loadDevicesList();
  await loadByScannedValue(cleaned);
}

function renderDevicesList() {
  const filter = String(els.listFilter.value || "").trim().toLowerCase();
  const rows = !filter
    ? devicesCache
    : devicesCache.filter((row) => {
        return [row.serial, row.device_type, row.model, row.status, row.from_store, row.to_store, row.comment]
          .map((v) => String(v || "").toLowerCase())
          .some((v) => v.includes(filter));
      });

  els.listStatus.textContent = `Showing ${rows.length}`;

  if (!rows.length) {
    const helper = filter ? "No rows match this filter" : "No devices visible. Check Supabase SELECT policy.";
    els.devicesList.innerHTML = `
      <div class="row">
        <span>No devices visible</span>
        <span>-</span>
        <span>-</span>
        <span>-</span>
        <span>-</span>
        <span>-</span>
        <span>${helper}</span>
      </div>
    `;
    return;
  }

  els.devicesList.innerHTML = rows
    .map(
      (row) => `
      <div class="row" data-serial="${row.serial || ""}">
        <span data-label="Serial">${row.serial || ""}</span>
        <span data-label="Type">${row.device_type || ""}</span>
        <span data-label="Model">${row.model || ""}</span>
        <span data-label="Status">${row.status || ""}</span>
        <span data-label="From">${row.from_store || ""}</span>
        <span data-label="To">${row.to_store || ""}</span>
        <span data-label="Comment">${row.comment || ""}</span>
      </div>
    `
    )
    .join("");
}

async function loadDevicesList() {
  els.listStatus.textContent = "Loading...";
  els.devicesList.innerHTML = `
    <div class="row">
      <span>Loading database...</span>
      <span>-</span>
      <span>-</span>
      <span>-</span>
      <span>-</span>
      <span>-</span>
      <span>Please wait</span>
    </div>
  `;

  try {
    const data = await restRequest(
      "devices?select=id,serial,device_type,model,status,from_store,to_store,comment,updated_at&order=updated_at.desc&limit=300"
    );
    devicesCache = Array.isArray(data) ? data : [];
    renderDevicesList();
  } catch (error) {
    devicesCache = [];
    els.listStatus.textContent = `Database error: ${error.message}`;
    els.devicesList.innerHTML = `
      <div class="row">
        <span>Database error</span>
        <span>-</span>
        <span>-</span>
        <span>-</span>
        <span>-</span>
        <span>-</span>
        <span>${String(error.message || "Unknown error")}</span>
      </div>
    `;
  }
}

async function loadFromLookup() {
  const token = extractPreferredSerial(els.lookupSerial.value);
  if (!token) {
    setStatus("Enter serial in scanner or laptop format", "error");
    return;
  }
  const cleaned = cleanToken(token);
  els.lookupSerial.value = cleaned;
  els.serial.value = cleaned;
  await loadByScannedValue(cleaned);
}

els.serial.addEventListener("input", () => {
  els.serial.value = sanitizeSerialField(els.serial.value);
  clearTimeout(scanTimer);

  if (!els.serial.value) {
    setIdentityEditable(true);
    return;
  }

  scanTimer = setTimeout(() => {
    loadByScannedValue(els.serial.value);
  }, 140);
});

els.serial.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    loadByScannedValue(els.serial.value);
  }
});

els.lookupSerial.addEventListener("input", () => {
  els.lookupSerial.value = sanitizeLookupField(els.lookupSerial.value);
});

els.lookupSerial.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    loadFromLookup();
  }
});

els.lookupLoad.addEventListener("click", loadFromLookup);
els.save.addEventListener("click", saveDevice);
els.clear.addEventListener("click", () => {
  resetForm();
  setStatus("Cleared");
  els.serial.focus();
});
els.refreshList.addEventListener("click", loadDevicesList);
els.listFilter.addEventListener("input", renderDevicesList);

els.devicesList.addEventListener("click", (e) => {
  const row = e.target.closest(".row[data-serial]");
  if (!row) return;
  const token = extractPreferredSerial(row.getAttribute("data-serial") || "");
  if (!token) return;
  const cleaned = cleanToken(token);
  els.lookupSerial.value = cleaned;
  loadFromLookup();
});

resetForm();
els.serial.focus();
loadDevicesList();
setTimeout(loadDevicesList, 1200);
window.addEventListener("focus", loadDevicesList);
setInterval(loadDevicesList, 20000);
