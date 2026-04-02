const DEFAULTS = {
  supabaseUrl: "https://qvlduxpdcwgmokjdsdfp.supabase.co",
  supabaseKey: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF2bGR1eHBkY3dnbW9ramRzZGZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ5Mzk5MzMsImV4cCI6MjA5MDUxNTkzM30.3HiNhJKLrMmc0I11Y7qMS73fi0b1XUaEorTAL6wJOsk",
  prefixRules: "",
};

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
};

let supabase = null;
let pending = [];

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

async function saveDevice() {
  const serial = els.serial.value.trim();
  if (!serial) {
    status("Serial is required", "error");
    return;
  }

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
  els.serial.focus();
}

function applySettings() {
  const settings = getSettings();
  els.supabaseUrl.value = settings.supabaseUrl || "";
  els.supabaseKey.value = settings.supabaseKey || "";
  els.prefixRules.value = settings.prefixRules || "";
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

els.serial.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    loadDevice(els.serial.value.trim());
  }
});

els.save.addEventListener("click", saveDevice);

applySettings();
els.serial.focus();
