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

let supabase = null;
let scanTimer = null;
let devicesCache = [];
let activeSerialDigits = "";
let recordLoaded = false;

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

function initSupabase() {
  if (!window.supabase || !window.supabase.createClient) {
    setStatus("Supabase script failed to load", "error");
    return null;
  }
  return window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
}

function splitModel(modelText) {
  const text = String(modelText || "").trim();
  if (!text) return ["", ""];
  const parts = text.split(" ", 2);
  if (parts.length === 1) return [parts[0], ""];
  return [parts[0], parts[1]];
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
  const text = String(raw || "").trim();
  if (!text) return null;

  const tokens = text.split(/[\s,;|]+/).filter(Boolean);
  for (const t of tokens) {
    if (SERIAL_RE.test(t)) {
      return t.toUpperCase();
    }
  }
  return null;
}

function serialDigitsFromAnyInput(raw) {
  const text = String(raw || "").trim().toUpperCase();
  if (!text) return "";
  if (/^\d{14}$/.test(text)) return text;
  const token = extractSerialToken(text);
  if (!token) return "";
  const m = token.match(SERIAL_RE);
  return m ? m[1] : "";
}

function resetForm() {
  activeSerialDigits = "";
  recordLoaded = false;
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
  recordLoaded = true;
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
  recordLoaded = false;
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
    const s = String(row.serial || "");
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

async function guessFromDb(serialDigits) {
  const prefix2 = serialDigits.slice(0, 2);
  if (!prefix2) return null;

  const { data, error } = await supabase
    .from("devices")
    .select("serial,device_type,model")
    .ilike("serial", `${prefix2}%`)
    .limit(200);

  if (error || !Array.isArray(data) || !data.length) return null;

  const counts = new Map();
  for (const row of data) {
    if (!row.model) continue;
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

async function loadByScannedValue(rawValue) {
  const token = extractSerialToken(rawValue);
  if (!token) {
    const typed = String(rawValue || "").trim();
    if (typed.length > 0) {
      els.serial.value = "";
      activeSerialDigits = "";
      recordLoaded = false;
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
  if (!supabase) supabase = initSupabase();
  if (!supabase) return;

  const { data, error } = await supabase
    .from("devices")
    .select("*")
    .eq("serial", serialDigits)
    .maybeSingle();

  if (error) {
    setStatus(`Database error: ${error.message}`, "error");
    return;
  }

  activeSerialDigits = serialDigits;

  if (data) {
    fillFormFromDevice(data);
    setStatus("Loaded from database", "ok");
    return;
  }

  recordLoaded = false;
  setTypeEditable(true);
  els.statusSelect.value = "RECEIVED";
  els.fromStore.value = "";
  els.toStore.value = "";
  els.comment.value = "";

  const hint = PREFIX_HINTS[serialDigits.slice(0, 2)] || null;
  const guessed = hint || guessFromCache(serialDigits) || (await guessFromDb(serialDigits));
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
  if (!supabase) supabase = initSupabase();
  if (!supabase) return;

  const { data: existing, error: findError } = await supabase
    .from("devices")
    .select("id,serial")
    .eq("serial", serialDigits)
    .maybeSingle();

  if (findError) {
    setStatus(`Lookup failed: ${findError.message}`, "error");
    return;
  }

  const editPayload = {
    from_store: els.fromStore.value.trim(),
    to_store: els.toStore.value.trim(),
    status: els.statusSelect.value,
    comment: els.comment.value.trim(),
  };

  if (existing) {
    const { error } = await supabase.from("devices").update(editPayload).eq("serial", serialDigits);
    if (error) {
      setStatus(`Update failed: ${error.message}`, "error");
      return;
    }
    setStatus("Updated", "ok");
  } else {
    const insertPayload = {
      serial: serialDigits,
      device_type: (els.type.value || "scanner").trim(),
      model: composeModel(els.make.value, els.model.value),
      ...editPayload,
    };
    const { error } = await supabase.from("devices").insert(insertPayload);
    if (error) {
      setStatus(`Insert failed: ${error.message}`, "error");
      return;
    }
    setStatus("Added", "ok");
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
  els.devicesList.innerHTML = rows
    .map(
      (row) => `
      <div class="row" data-serial="${row.serial || ""}">
        <span>${row.serial || ""}</span>
        <span>${row.device_type || ""}</span>
        <span>${row.model || ""}</span>
        <span>${row.status || ""}</span>
        <span>${row.from_store || ""}</span>
        <span>${row.to_store || ""}</span>
        <span>${row.comment || ""}</span>
      </div>
    `
    )
    .join("");
}

async function loadDevicesList() {
  if (!supabase) supabase = initSupabase();
  if (!supabase) return;

  const { data, error } = await supabase
    .from("devices")
    .select("serial,device_type,model,status,from_store,to_store,comment,updated_at")
    .order("updated_at", { ascending: false })
    .limit(200);

  if (error) {
    els.listStatus.textContent = `Database error: ${error.message}`;
    els.devicesList.innerHTML = "";
    return;
  }

  devicesCache = Array.isArray(data) ? data : [];
  renderDevicesList();
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
  els.serial.value = String(els.serial.value || "").toUpperCase().trim();
  clearTimeout(scanTimer);
  scanTimer = setTimeout(() => {
    loadByScannedValue(els.serial.value);
  }, 160);
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
els.devicesList.addEventListener("click", (e) => {
  const row = e.target.closest(".row[data-serial]");
  if (!row) return;
  const serial = row.getAttribute("data-serial") || "";
  if (!serial) return;
  els.lookupSerial.value = `S${serial}`;
  loadFromLookup();
});

supabase = initSupabase();
resetForm();
els.serial.focus();
loadDevicesList();
setTimeout(loadDevicesList, 1200);
window.addEventListener("focus", loadDevicesList);
