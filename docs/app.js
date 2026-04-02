const DEFAULTS = {
  supabaseUrl: "https://qvlduxpdcwgmokjdsdfp.supabase.co",
  supabaseKey: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF2bGR1eHBkY3dnbW9ramRzZGZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ5Mzk5MzMsImV4cCI6MjA5MDUxNTkzM30.3HiNhJKLrMmc0I11Y7qMS73fi0b1XUaEorTAL6wJOsk",
  prefixRules: "",
};

const SERIAL_DIGITS_MIN = 13;
const SERIAL_DIGITS_MAX = 14;

const store = {
  get() {
    try {
      return JSON.parse(localStorage.getItem("rimiSettings")) || { ...DEFAULTS };
    } catch {
      return { ...DEFAULTS };
    }
  },
  set(next) {
    localStorage.setItem("rimiSettings", JSON.stringify(next));
  },
};

const els = {
  serial: document.getElementById("serial"),
  status: document.getElementById("status"),
  type: document.getElementById("type"),
  statusSelect: document.getElementById("statusSelect"),
  make: document.getElementById("make"),
  model: document.getElementById("model"),
  fromStore: document.getElementById("fromStore"),
  toStore: document.getElementById("toStore"),
  comment: document.getElementById("comment"),
  overwrite: document.getElementById("overwrite"),
  bulk: document.getElementById("bulk"),
  save: document.getElementById("save"),
  sync: document.getElementById("sync"),
  supabaseUrl: document.getElementById("supabaseUrl"),
  supabaseKey: document.getElementById("supabaseKey"),
  prefixRules: document.getElementById("prefixRules"),
  saveSettings: document.getElementById("saveSettings"),
  settingsCard: document.getElementById("settingsCard"),
  devicesList: document.getElementById("devicesList"),
  listStatus: document.getElementById("listStatus"),
  listFilter: document.getElementById("listFilter"),
  refreshList: document.getElementById("refreshList"),
};

let supabase = null;
let pending = [];
let devicesCache = [];
let lastLoadedSerial = "";

function status(msg, tone = "info") {
  els.status.textContent = msg;
  els.status.style.color = tone === "error" ? "#b00020" : tone === "ok" ? "#1b5f5a" : "#5b544d";
}

function getSettings() {
  return store.get();
}

function initSupabase() {
  const { supabaseUrl, supabaseKey } = getSettings();
  if (!supabaseUrl || !supabaseKey) {
    status("Set Supabase URL and Key in settings.", "error");
    return null;
  }
  return window.supabase.createClient(supabaseUrl, supabaseKey);
}

function getPrefixRules() {
  const raw = getSettings().prefixRules;
  if (!raw) return {};
  try {
    const parsed = JSON.parse(raw);
    return typeof parsed === "object" && parsed ? parsed : {};
  } catch {
    return {};
  }
}

function splitMakeModel(modelText) {
  if (!modelText) return ["", ""];
  const parts = modelText.trim().split(" ", 2);
  return parts.length === 2 ? parts : [parts[0], ""];
}

function normalizeSerialInput(raw) {
  const text = (raw || "").trim();
  if (!text) return { ok: false, serial: "" };

  // Only accept tokens that are exactly S + 13-14 digits (device serial)
  const tokens = text.split(/[\s,;|]+/).filter(Boolean);
  for (const token of tokens) {
    const re = new RegExp(`^S\\d{${SERIAL_DIGITS_MIN},${SERIAL_DIGITS_MAX}}$`, "i");
    if (re.test(token)) {
      return { ok: true, serial: token.toUpperCase().slice(1) };
    }
  }

  return { ok: false, serial: "" };
}

function inferGuessFromCache(serial) {
  if (!serial || !devicesCache.length) return null;
  const prefix2 = serial.slice(0, 2);
  if (!prefix2) return null;

  const counts = new Map();
  for (const row of devicesCache) {
    const s = String(row.serial || "");
    if (!s.startsWith(prefix2) || !row.model) continue;
    const key = `${row.device_type || "scanner"}||${row.model}`;
    counts.set(key, (counts.get(key) || 0) + 1);
  }

  let best = null;
  let bestCount = 0;
  for (const [key, count] of counts.entries()) {
    if (count > bestCount) {
      bestCount = count;
      const [device_type, model] = key.split("||");
      best = { device_type, model };
    }
  }
  return best;
}

function fillDevice(dev) {
  els.type.value = dev.device_type || "scanner";
  els.statusSelect.value = dev.status || "RECEIVED";
  els.fromStore.value = dev.from_store || "";
  els.toStore.value = dev.to_store || "";
  els.comment.value = dev.comment || "";
  const [make, model] = splitMakeModel(dev.model || "");
  els.make.value = make;
  els.model.value = model;
}

async function loadDevice(serial) {
  const normalized = normalizeSerialInput(serial);
  if (!normalized.ok) {
    if ((serial || "").trim().length > 5) {
      els.serial.value = "";
      status(`Only serial barcode is allowed: S + ${SERIAL_DIGITS_MIN}-${SERIAL_DIGITS_MAX} digits`, "error");
    }
    return;
  }
  serial = normalized.serial;
  els.serial.value = serial;
  if (lastLoadedSerial === serial) return;
  lastLoadedSerial = serial;
  if (!supabase) supabase = initSupabase();
  if (!supabase) return;

  const { data, error } = await supabase
    .from("devices")
    .select("*")
    .eq("serial", serial)
    .maybeSingle();

  if (error) {
    status(`DB error: ${error.message}`, "error");
    return;
  }

  if (data) {
    els.overwrite.checked = true;
    fillDevice(data);
    status("Loaded from database", "ok");
    return;
  }

  els.overwrite.checked = false;
  const upper = serial.toUpperCase();
  const rules = { ...getPrefixRules() };

  for (const prefix of Object.keys(rules)) {
    if (upper.startsWith(prefix.toUpperCase())) {
      const [deviceType, make, model] = rules[prefix];
      els.type.value = deviceType || "scanner";
      els.make.value = make || "";
      els.model.value = model ? model.replace(make + " ", "") : "";
      status(`Auto-detected ${make} ${model}`, "ok");
      return;
    }
  }

  const guessed = inferGuessFromCache(serial) || (await guessFromDatabase(serial));
  if (guessed) {
    els.type.value = guessed.device_type || "scanner";
    const [make, model] = splitMakeModel(guessed.model || "");
    els.make.value = make;
    els.model.value = model;
    status("Auto-filled from existing devices", "ok");
    return;
  }

  status("New device. Fill details.");
}

function buildPayload() {
  const make = els.make.value.trim();
  const modelText = els.model.value.trim();
  let model = modelText;
  if (make && modelText && !modelText.startsWith(make)) {
    model = `${make} ${modelText}`;
  }
  return {
    serial: els.serial.value.trim(),
    device_type: els.type.value,
    model,
    from_store: els.fromStore.value.trim(),
    to_store: els.toStore.value.trim(),
    status: els.statusSelect.value,
    comment: els.comment.value.trim(),
  };
}

async function guessFromDatabase(serial) {
  if (!supabase) return null;
  const prefix2 = serial.slice(0, 2);
  if (!prefix2) return null;

  const { data, error } = await supabase
    .from("devices")
    .select("serial,device_type,model")
    .ilike("serial", `${prefix2}%`)
    .limit(200);

  if (error || !data || !data.length) return null;

  const counts = new Map();
  for (const row of data) {
    if (!row.model) continue;
    const key = `${row.device_type || "scanner"}||${row.model}`;
    counts.set(key, (counts.get(key) || 0) + 1);
  }

  let best = null;
  let bestCount = 0;
  for (const [key, count] of counts.entries()) {
    if (count > bestCount) {
      bestCount = count;
      const [device_type, model] = key.split("||");
      best = { device_type, model };
    }
  }

  return best;
}

async function saveDevice() {
  const normalized = normalizeSerialInput(els.serial.value);
  if (!normalized.ok) {
    status(`Only serial barcode is allowed: S + ${SERIAL_DIGITS_MIN}-${SERIAL_DIGITS_MAX} digits`, "error");
    return;
  }
  els.serial.value = normalized.serial;

  if (!supabase) supabase = initSupabase();
  if (!supabase) return;

  const payload = buildPayload();
  const { error } = await supabase.from("devices").upsert(payload);
  if (error) {
    status(`Save failed: ${error.message}`, "error");
    return;
  }

  status("Saved", "ok");
  if (!els.bulk.checked) {
    els.serial.value = "";
  }
  lastLoadedSerial = "";
  els.serial.focus();
  await loadDevice(els.serial.value || normalized.serial);
  await loadDevicesList();
}

async function loadDevicesList() {
  if (!supabase) supabase = initSupabase();
  if (!supabase) return;

  const { data, error } = await supabase
    .from("devices")
    .select("serial,device_type,model,status")
    .order("updated_at", { ascending: false })
    .limit(50);

  if (error) {
    els.listStatus.textContent = "DB error";
    return;
  }

  devicesCache = data || [];
  renderDevicesList();
}

function renderDevicesList() {
  const filter = (els.listFilter?.value || "").trim().toLowerCase();
  const rows = !filter
    ? devicesCache
    : devicesCache.filter((row) => {
        return [row.serial, row.device_type, row.model, row.status]
          .map((v) => String(v || "").toLowerCase())
          .some((v) => v.includes(filter));
      });

  els.listStatus.textContent = `Showing ${rows.length}`;
  els.devicesList.innerHTML = rows
    .map(
      (row) => `
      <div class="row">
        <span>${row.serial || ""}</span>
        <span>${row.device_type || ""}</span>
        <span>${row.model || ""}</span>
        <span>${row.status || ""}</span>
      </div>
    `
    )
    .join("");
}

function applySettings() {
  const settings = getSettings();
  els.supabaseUrl.value = settings.supabaseUrl || "";
  els.supabaseKey.value = settings.supabaseKey || "";
  els.prefixRules.value = settings.prefixRules || "";

  const hasDefaults = settings.supabaseUrl && settings.supabaseKey;
  if (hasDefaults) {
    els.supabaseUrl.setAttribute("readonly", "readonly");
    els.supabaseKey.setAttribute("readonly", "readonly");
    els.settingsCard.classList.add("hidden");
  }
}

els.saveSettings.addEventListener("click", () => {
  store.set({
    supabaseUrl: els.supabaseUrl.value.trim(),
    supabaseKey: els.supabaseKey.value.trim(),
    prefixRules: els.prefixRules.value.trim(),
  });
  supabase = null;
  status("Settings saved", "ok");
});

let serialTimer = null;
els.serial.addEventListener("input", () => {
  clearTimeout(serialTimer);
  serialTimer = setTimeout(() => loadDevice(els.serial.value), 80);
});

els.serial.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    loadDevice(els.serial.value);
  }
});

els.save.addEventListener("click", saveDevice);
els.sync.addEventListener("click", () => {
  status("Sync not needed: direct write to Supabase is active.", "ok");
  loadDevicesList();
});
els.listFilter.addEventListener("input", renderDevicesList);
els.refreshList.addEventListener("click", loadDevicesList);

applySettings();
els.serial.focus();
loadDevicesList();
