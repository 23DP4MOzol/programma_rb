const SUPABASE_URL = "https://qvlduxpdcwgmokjdsdfp.supabase.co";
const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF2bGR1eHBkY3dnbW9ramRzZGZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ5Mzk5MzMsImV4cCI6MjA5MDUxNTkzM30.3HiNhJKLrMmc0I11Y7qMS73fi0b1XUaEorTAL6wJOsk";

const SERIAL_RE = /^S(\d{14})$/i;
const PREFIX_HINTS = {
  "18": { device_type: "scanner", make: "Zebra", model: "TC51" },
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

let scanTimer = null;
let devicesCache = [];

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

function setTypeEditable(enabled) {
  els.type.disabled = !enabled;
}

function sanitizeSerialField(value) {
  const clean = String(value || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
  if (!clean.startsWith("S")) return "";
  const digits = clean.slice(1).replace(/\D/g, "").slice(0, 14);
  return `S${digits}`;
}

function sanitizeLookupField(value) {
  const raw = String(value || "").toUpperCase().trim().replace(/[^A-Z0-9]/g, "");
  if (!raw) return "";
  if (raw.startsWith("S")) {
    const digits = raw.slice(1).replace(/\D/g, "").slice(0, 14);
    return `S${digits}`;
  }
  return raw.replace(/\D/g, "").slice(0, 14);
}

async function restRequest(path, { method = "GET", body = null, prefer = "" } = {}) {
  const headers = {
    apikey: SUPABASE_KEY,
    Authorization: `Bearer ${SUPABASE_KEY}`,
  };
  if (body !== null) {
    headers["Content-Type"] = "application/json";
  }
  if (prefer) {
    headers.Prefer = prefer;
  }

  const response = await fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    method,
    headers,
    body: body === null ? undefined : JSON.stringify(body),
  });

  const text = await response.text();
  const json = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const msg = (json && (json.message || json.error_description || json.error)) || text || response.statusText;
    throw new Error(msg);
  }
  return json;
}

function splitModel(modelText) {
  const text = String(modelText || "").trim();
  if (!text) return ["", ""];
  const parts = text.split(" ", 2);
  return parts.length === 1 ? [parts[0], ""] : [parts[0], parts[1]];
}

function composeModel(make, model) {
  const m = String(make || "").trim();
  const md = String(model || "").trim();
  if (!m && !md) return "";
  if (!m) return md;
  if (!md) return m;
  if (md.toLowerCase().startsWith(m.toLowerCase())) return md;
  return `${m} ${md}`;
}

function extractSerialToken(raw) {
  const text = String(raw || "").trim().toUpperCase();
  if (!text) return null;
  const tokens = text.split(/[\s,;|]+/).filter(Boolean);
  for (const t of tokens) {
    if (SERIAL_RE.test(t)) return t;
  }
  return null;
}

function serialDigitsFromAnyInput(raw) {
  const text = String(raw || "").trim().toUpperCase();
  if (!text) return "";
  if (/^\d{14}$/.test(text)) return text;
  const token = extractSerialToken(text);
  if (!token) return "";
  const match = token.match(SERIAL_RE);
  return match ? match[1] : "";
}

function serialTokenFromDigits(serialDigits) {
  return /^\d{14}$/.test(serialDigits || "") ? `S${serialDigits}` : "";
}

function resetForm() {
  els.serial.value = "";
  els.type.value = "scanner";
  setTypeEditable(true);
  els.make.value = "";
  els.model.value = "";
  els.statusSelect.value = "RECEIVED";
  els.fromStore.value = "";
  els.toStore.value = "";
  els.comment.value = "";
}

function fillFormFromDevice(device) {
  els.type.value = device.device_type || "scanner";
  setTypeEditable(false);
  const [make, model] = splitModel(device.model || "");
  els.make.value = make;
  els.model.value = model;
  els.statusSelect.value = device.status || "RECEIVED";
  els.fromStore.value = device.from_store || "";
  els.toStore.value = device.to_store || "";
  els.comment.value = device.comment || "";
}

function applyGuess(guess) {
  setTypeEditable(true);
  els.type.value = guess.device_type || "scanner";
  if (guess.make && guess.model) {
    els.make.value = guess.make;
    els.model.value = guess.model;
  } else {
    const [make, model] = splitModel(guess.model || "");
    els.make.value = make;
    els.model.value = model;
  }
}

function guessFromCache(serialDigits) {
  const prefix2 = serialDigits.slice(0, 2);
  if (!prefix2) return null;

  const counts = new Map();
  for (const row of devicesCache) {
    const s = serialDigitsFromAnyInput(row.serial || "");
    if (!s.startsWith(prefix2) || !row.model) continue;
    const key = `${row.device_type || "scanner"}||${row.model}`;
    counts.set(key, (counts.get(key) || 0) + 1);
  }

  let winner = null;
  let best = 0;
  for (const [key, count] of counts.entries()) {
    if (count > best) {
      best = count;
      const [device_type, model] = key.split("||");
      winner = { device_type, model };
    }
  }
  return winner;
}

async function getDeviceBySerial(serialDigits) {
  const serialToken = serialTokenFromDigits(serialDigits);
  if (!serialToken) return null;
  const path =
    `devices?select=*` +
    `&or=(serial.eq.${encodeURIComponent(serialDigits)},serial.eq.${encodeURIComponent(serialToken)})` +
    `&order=updated_at.desc&limit=1`;
  const rows = await restRequest(path);
  return Array.isArray(rows) && rows.length ? rows[0] : null;
}

async function loadByScannedValue(rawValue) {
  const token = extractSerialToken(rawValue);
  if (!token) {
    if (String(rawValue || "").trim()) {
      els.serial.value = "";
      setTypeEditable(true);
      setStatus("Only serial barcode is allowed (S + 14 digits)", "error");
    }
    return;
  }

  const match = token.match(SERIAL_RE);
  const serialDigits = match ? match[1] : "";
  if (!serialDigits) {
    setStatus("Invalid serial barcode", "error");
    return;
  }

  els.serial.value = token;

  let device = null;
  try {
    device = await getDeviceBySerial(serialDigits);
  } catch (error) {
    setStatus(`Database error: ${error.message}`, "error");
    return;
  }

  if (device) {
    fillFormFromDevice(device);
    setStatus("Loaded from database", "ok");
    return;
  }

  setTypeEditable(true);
  els.statusSelect.value = "RECEIVED";
  els.fromStore.value = "";
  els.toStore.value = "";
  els.comment.value = "";

  const guessed = PREFIX_HINTS[serialDigits.slice(0, 2)] || guessFromCache(serialDigits);
  if (guessed) {
    applyGuess(guessed);
    setStatus("Auto-filled by existing scanner prefixes", "ok");
    return;
  }

  els.type.value = "scanner";
  els.make.value = "";
  els.model.value = "";
  setStatus("New serial. Fill status/store/comment and save.");
}

async function saveDevice() {
  const token = extractSerialToken(els.serial.value);
  if (!token) {
    setStatus("Only serial barcode is allowed (S + 14 digits)", "error");
    return;
  }

  const serialDigits = token.match(SERIAL_RE)[1];
  const serialToken = serialTokenFromDigits(serialDigits);

  let existing = null;
  try {
    existing = await getDeviceBySerial(serialDigits);
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
      setStatus("Updated", "ok");
    } else {
      const insertPayload = {
        serial: serialToken,
        device_type: (els.type.value || "scanner").trim(),
        model: composeModel(els.make.value, els.model.value),
        ...editPayload,
      };
      await restRequest("devices", { method: "POST", body: insertPayload, prefer: "return=minimal" });
      setStatus("Added", "ok");
    }
  } catch (error) {
    setStatus(`Save failed: ${error.message}`, "error");
    return;
  }

  await loadDevicesList();
  await loadByScannedValue(token);
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
    const helper = filter ? "No rows match this filter" : "Check Supabase SELECT policy for anon role";
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
      "devices?select=serial,device_type,model,status,from_store,to_store,comment,updated_at&order=updated_at.desc&limit=200"
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
  const serialDigits = serialDigitsFromAnyInput(els.lookupSerial.value);
  if (!serialDigits) {
    setStatus("Enter serial as S + 14 digits or 14 digits", "error");
    return;
  }
  const token = `S${serialDigits}`;
  els.serial.value = token;
  await loadByScannedValue(token);
}

els.serial.addEventListener("input", () => {
  els.serial.value = sanitizeSerialField(els.serial.value);
  clearTimeout(scanTimer);
  if (!els.serial.value) {
    setTypeEditable(true);
    return;
  }
  scanTimer = setTimeout(() => {
    loadByScannedValue(els.serial.value);
  }, 120);
});

els.serial.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    loadByScannedValue(els.serial.value);
  }
});

els.save.addEventListener("click", saveDevice);
els.clear.addEventListener("click", () => {
  resetForm();
  setStatus("Cleared");
  els.serial.focus();
});
els.refreshList.addEventListener("click", loadDevicesList);
els.listFilter.addEventListener("input", renderDevicesList);
els.lookupLoad.addEventListener("click", loadFromLookup);
els.lookupSerial.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    loadFromLookup();
  }
});
els.lookupSerial.addEventListener("input", () => {
  els.lookupSerial.value = sanitizeLookupField(els.lookupSerial.value);
});
els.devicesList.addEventListener("click", (e) => {
  const row = e.target.closest(".row[data-serial]");
  if (!row) return;
  const serial = serialDigitsFromAnyInput(row.getAttribute("data-serial") || "");
  if (!serial) return;
  els.lookupSerial.value = `S${serial}`;
  loadFromLookup();
});

resetForm();
els.serial.focus();
loadDevicesList();
setTimeout(loadDevicesList, 1200);
window.addEventListener("focus", loadDevicesList);
setInterval(loadDevicesList, 15000);
