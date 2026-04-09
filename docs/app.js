const SUPABASE_URL = "https://qvlduxpdcwgmokjdsdfp.supabase.co";
const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF2bGR1eHBkY3dnbW9ramRzZGZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ5Mzk5MzMsImV4cCI6MjA5MDUxNTkzM30.3HiNhJKLrMmc0I11Y7qMS73fi0b1XUaEorTAL6wJOsk";

const SCANNER_SERIAL_RE = /^S\d{13,14}$/i;
const PLAIN_SCANNER_RE = /^\d{13,14}$/;
const GENERIC_SERIAL_RE = /^[A-Z0-9]{8,20}$/;

const FALLBACK_PREFIX_HINTS = {
  "D2:18": { device_type: "scanner", make: "Zebra", model: "TC51" },
  "D2:19": { device_type: "scanner", make: "Zebra", model: "TC52" },
  "D2:20": { device_type: "scanner", make: "Zebra", model: "TC52" },
  "D2:21": { device_type: "scanner", make: "Zebra", model: "TC52" },
  "D2:24": { device_type: "scanner", make: "Zebra", model: "TC52" },
  "A3:5CG": { device_type: "laptop", make: "HP", model: "EliteBook 840 G10" },
};

const WEB_DEVICE_CATALOG = {
  scanner: {
    Zebra: ["DS2208", "DS8178", "TC52", "TC57", "MC3300", "TC21", "TC26"],
    Honeywell: ["1900", "1902", "CT40", "EDA51"],
    Datalogic: ["Gryphon", "Memor", "Magellan", "Skorpio"],
  },
  laptop: {
    Lenovo: ["ThinkPad", "ThinkBook", "Yoga", "T14", "L14"],
    Dell: ["Latitude", "XPS", "Precision"],
    HP: ["EliteBook", "ProBook"],
    Apple: ["MacBook Air", "MacBook Pro"],
  },
  tablet: {
    Samsung: ["Galaxy Tab A", "Galaxy Tab S7", "Galaxy Tab S8", "Galaxy Tab Active3", "Galaxy Tab Active4 Pro"],
    Apple: ["iPad", "iPad Pro", "iPad Air", "iPad Mini"],
    Lenovo: ["Tab M10", "Tab P11"],
  },
  phone: {
    Samsung: ["Galaxy S22", "Galaxy S23", "Galaxy XCover 5", "Galaxy XCover 6 Pro", "Galaxy XCover 7"],
    Apple: ["iPhone 12", "iPhone 13", "iPhone 14", "iPhone 15", "iPhone SE"],
  },
};

const DRAFT_STORAGE_KEY = "rimi.inventory.draft.v1";
const QUEUE_STORAGE_KEY = "rimi.inventory.queue.v1";
const AUTH_TOKEN_STORAGE_KEY = "rimi.inventory.auth_jwt";
const WEB_LANG_STORAGE_KEY = "rimi.inventory.lang";
const SCAN_DEBOUNCE_MS = 900;
const SAVE_DEBOUNCE_MS = 1400;
const WEB_APP_VERSION = "web-2026.04.07";

const WEB_I18N = {
  en: {
    scanPopupTitle: "Scan result",
    scanPopupRegister: "Register new device",
    scanPopupClose: "Close",
    scanRegisterStatus: "Register a new device: confirm Type / Make / Model and save.",
    scanFoundDbStatus: "Loaded from database",
    scanFoundDbPopup: "Found in database: existing device loaded.",
    scanNotFoundHistoryStatus: "Not found in database. Auto-filled using database history.",
    scanNotFoundHistoryPopup:
      "Not found data in database. According to database history, data was automatically filled. Register new device?",
    scanNotFoundPrefixStatus: "Not found in database. Auto-filled using prefix rules.",
    scanNotFoundPrefixPopup:
      "Not found data in database. According to database prefix rules, data was automatically filled. Register new device?",
    scanNotFoundStatus: "Not found in database. Register new device.",
    scanNotFoundPopup: "Not found data in database. Register new device?",
    conflictTitle: "Conflict detected",
    conflictMessage: "This device was updated elsewhere. Choose how to continue.",
    conflictReload: "Reload latest",
    conflictOverwrite: "Overwrite with my values",
    conflictCancel: "Cancel",
    conflictReloadedStatus: "Conflict: latest database values reloaded.",
    conflictOverwrittenStatus: "Conflict resolved: overwritten with your values.",
    conflictNoChangeStatus: "Conflict detected. No changes applied.",
    prefixRulesAdminOnly: "Admin access required",
    prefixRulesLoadedStatus: "Rules loaded: {count}",
    prefixRuleSavedStatus: "Rule saved",
    prefixRuleDeletedStatus: "Rule deleted",
    prefixRuleInvalidKey: "Prefix key is required",
    prefixRuleDeleteSelect: "Select a rule to delete",
    prefixRuleDeleteConfirm: "Delete selected prefix rule?",
    prefixRulesLoadError: "Prefix rules load failed: {error}",
    prefixRulesSaveError: "Prefix rule save failed: {error}",
    prefixRulesDeleteError: "Prefix rule delete failed: {error}",
  },
  lv: {
    scanPopupTitle: "Skenēšanas rezultāts",
    scanPopupRegister: "Reģistrēt jaunu ierīci",
    scanPopupClose: "Aizvērt",
    scanRegisterStatus: "Reģistrē jaunu ierīci: pārbaudi Tips / Ražotājs / Modelis un saglabā.",
    scanFoundDbStatus: "Ielādēts no datubāzes",
    scanFoundDbPopup: "Atrasts datubāzē: esošā ierīce ielādēta.",
    scanNotFoundHistoryStatus: "Datubāzē nav atrasts. Automātiski aizpildīts pēc datubāzes vēstures.",
    scanNotFoundHistoryPopup:
      "Datubāzē dati nav atrasti. Pēc datubāzes vēstures dati automātiski aizpildīti. Reģistrēt jaunu ierīci?",
    scanNotFoundPrefixStatus: "Datubāzē nav atrasts. Automātiski aizpildīts pēc prefiksu noteikumiem.",
    scanNotFoundPrefixPopup:
      "Datubāzē dati nav atrasti. Pēc prefiksu noteikumiem dati automātiski aizpildīti. Reģistrēt jaunu ierīci?",
    scanNotFoundStatus: "Datubāzē nav atrasts. Reģistrē jaunu ierīci.",
    scanNotFoundPopup: "Datubāzē dati nav atrasti. Reģistrēt jaunu ierīci?",
    conflictTitle: "Konflikts atrasts",
    conflictMessage: "Šo ierīci citur jau atjaunināja. Izvēlies, kā turpināt.",
    conflictReload: "Ielādēt jaunāko",
    conflictOverwrite: "Pārrakstīt ar manām vērtībām",
    conflictCancel: "Atcelt",
    conflictReloadedStatus: "Konflikts: ielādētas jaunākās datubāzes vērtības.",
    conflictOverwrittenStatus: "Konflikts atrisināts: pārrakstīts ar tavām vērtībām.",
    conflictNoChangeStatus: "Konflikts atrasts. Izmaiņas netika saglabātas.",
    prefixRulesAdminOnly: "Nepieciešama admin piekļuve",
    prefixRulesLoadedStatus: "Noteikumi ielādēti: {count}",
    prefixRuleSavedStatus: "Noteikums saglabāts",
    prefixRuleDeletedStatus: "Noteikums dzēsts",
    prefixRuleInvalidKey: "Prefiksa atslēga ir obligāta",
    prefixRuleDeleteSelect: "Izvēlies noteikumu dzēšanai",
    prefixRuleDeleteConfirm: "Dzēst izvēlēto prefiksa noteikumu?",
    prefixRulesLoadError: "Prefiksu noteikumu ielāde neizdevās: {error}",
    prefixRulesSaveError: "Prefiksa noteikuma saglabāšana neizdevās: {error}",
    prefixRulesDeleteError: "Prefiksa noteikuma dzēšana neizdevās: {error}",
  },
};

function resolveWebLanguage() {
  let candidate = "";
  try {
    const q = new URLSearchParams(window.location.search || "").get("lang") || "";
    candidate = String(q || "").trim().toLowerCase();
  } catch {
    candidate = "";
  }

  if (!candidate) {
    try {
      candidate = String(localStorage.getItem(WEB_LANG_STORAGE_KEY) || "").trim().toLowerCase();
    } catch {
      candidate = "";
    }
  }

  if (!candidate) {
    candidate = String((navigator.language || "en").slice(0, 2)).toLowerCase();
  }

  const lang = candidate === "lv" ? "lv" : "en";
  try {
    localStorage.setItem(WEB_LANG_STORAGE_KEY, lang);
  } catch {
    // ignore storage errors
  }
  return lang;
}

const WEB_LANG = resolveWebLanguage();

function trWeb(key) {
  return WEB_I18N[WEB_LANG]?.[key] || WEB_I18N.en[key] || key;
}

function trWebFmt(key, vars = {}) {
  const template = trWeb(key);
  return String(template).replace(/\{(\w+)\}/g, (_m, k) => String(vars[k] ?? ""));
}

const els = {
  serial: document.getElementById("serial"),
  statusText: document.getElementById("status"),
  queueStatus: document.getElementById("queueStatus"),
  appVersion: document.getElementById("appVersion"),
  syncInfo: document.getElementById("syncInfo"),
  type: document.getElementById("type"),
  statusSelect: document.getElementById("statusSelect"),
  make: document.getElementById("make"),
  makeHint: document.getElementById("makeHint"),
  model: document.getElementById("model"),
  modelHint: document.getElementById("modelHint"),
  fromStore: document.getElementById("fromStore"),
  toStore: document.getElementById("toStore"),
  comment: document.getElementById("comment"),
  save: document.getElementById("save"),
  clear: document.getElementById("clear"),
  devicesList: document.getElementById("devicesList"),
  listStatus: document.getElementById("listStatus"),
  listFilter: document.getElementById("listFilter"),
  refreshList: document.getElementById("refreshList"),
  syncNow: document.getElementById("syncNow"),
  exportCsv: document.getElementById("exportCsv"),
  auditSerial: document.getElementById("auditSerial"),
  auditLoad: document.getElementById("auditLoad"),
  auditStatus: document.getElementById("auditStatus"),
  auditList: document.getElementById("auditList"),
  auditCard: document.getElementById("auditCard"),
  prefixRulesCard: document.getElementById("prefixRulesCard"),
  prefixRulesStatus: document.getElementById("prefixRulesStatus"),
  prefixRulesRefresh: document.getElementById("prefixRulesRefresh"),
  prefixKey: document.getElementById("prefixKey"),
  prefixType: document.getElementById("prefixType"),
  prefixMake: document.getElementById("prefixMake"),
  prefixModel: document.getElementById("prefixModel"),
  prefixPriority: document.getElementById("prefixPriority"),
  prefixActive: document.getElementById("prefixActive"),
  prefixSave: document.getElementById("prefixSave"),
  prefixDelete: document.getElementById("prefixDelete"),
  prefixClear: document.getElementById("prefixClear"),
  prefixRulesList: document.getElementById("prefixRulesList"),
  diagStatus: document.getElementById("diagStatus"),
  diagOnline: document.getElementById("diagOnline"),
  diagQueue: document.getElementById("diagQueue"),
  diagRole: document.getElementById("diagRole"),
  diagLastSync: document.getElementById("diagLastSync"),
  diagApi: document.getElementById("diagApi"),
  diagRefresh: document.getElementById("diagRefresh"),
  scanPopup: document.getElementById("scanPopup"),
  scanPopupTitle: document.getElementById("scanPopupTitle"),
  scanPopupMessage: document.getElementById("scanPopupMessage"),
  scanPopupRegister: document.getElementById("scanPopupRegister"),
  scanPopupClose: document.getElementById("scanPopupClose"),
  conflictPopup: document.getElementById("conflictPopup"),
  conflictPopupTitle: document.getElementById("conflictPopupTitle"),
  conflictPopupMessage: document.getElementById("conflictPopupMessage"),
  conflictReload: document.getElementById("conflictReload"),
  conflictOverwrite: document.getElementById("conflictOverwrite"),
  conflictCancel: document.getElementById("conflictCancel"),
  lookupSerial: document.getElementById("lookupSerial"),
  lookupLoad: document.getElementById("lookupLoad"),
  authInfo: document.getElementById("authInfo"),
};

let devicesCache = [];
let scanTimer = null;
let queueSyncInProgress = false;
let lastLoadedSerial = "";
let lastLoadedAt = 0;
let lastSavedSerial = "";
let lastSavedAt = 0;
let lastSuccessfulSyncAt = "";
let prefixHintsByKey = { ...FALLBACK_PREFIX_HINTS };
const loadedRevisionBySerial = new Map();
let authContext = null;
let pendingRegisterSerial = "";
let prefixRulesCache = [];
let selectedPrefixRuleId = "";
let conflictResolve = null;
let currentMakeSuggestion = "";
let currentModelSuggestion = "";

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

function setSyncInfo(message, tone = "info") {
  if (!els.syncInfo) return;
  let text = `Sync: ${message}`;
  if (message === "up to date" && lastSuccessfulSyncAt) {
    const local = new Date(lastSuccessfulSyncAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    text = `Sync: ${message} (${local})`;
  }
  els.syncInfo.textContent = text;
  if (tone === "error") {
    els.syncInfo.style.color = "#b00020";
  } else if (tone === "ok") {
    els.syncInfo.style.color = "#0a7a2f";
  } else {
    els.syncInfo.style.color = "#6b6b6b";
  }
  updateDiagnosticsPanel();
}

function updateQueueStatus() {
  if (!els.queueStatus) return;
  const count = getQueuedSaves().length;
  if (count > 0) {
    els.queueStatus.textContent = `Queued: ${count}`;
    els.queueStatus.style.color = "#b00020";
  } else {
    els.queueStatus.textContent = "Queued: 0";
    els.queueStatus.style.color = "#0a7a2f";
  }
  updateDiagnosticsPanel();
}

function setIdentityEditable(enabled) {
  els.type.disabled = !enabled;
  els.make.readOnly = !enabled;
  els.model.readOnly = !enabled;
  refreshInlineSuggestions();
}

function uniqueSorted(values) {
  const map = new Map();
  for (const value of values || []) {
    const text = String(value || "").trim();
    if (!text) continue;
    const key = text.toLowerCase();
    if (!map.has(key)) {
      map.set(key, text);
    }
  }
  return Array.from(map.values()).sort((a, b) => a.localeCompare(b, undefined, { sensitivity: "base" }));
}

function findInlineSuggestion(typedValue, options) {
  const typed = String(typedValue || "").trim();
  if (!typed) return "";
  const lowerTyped = typed.toLowerCase();

  for (const option of options || []) {
    const text = String(option || "").trim();
    if (!text) continue;
    if (text.toLowerCase().startsWith(lowerTyped) && text.length > typed.length) {
      return text;
    }
  }
  return "";
}

function makeCatalogForType(deviceType) {
  const type = String(deviceType || "scanner").toLowerCase();
  const catalog = WEB_DEVICE_CATALOG[type] || {};
  return catalog;
}

function buildMakeSuggestions() {
  const type = String(els.type?.value || "scanner").toLowerCase();
  const catalog = makeCatalogForType(type);
  const out = [];

  out.push(...Object.keys(catalog));

  for (const row of devicesCache || []) {
    if (String(row?.device_type || "scanner").toLowerCase() !== type) continue;
    const [make] = splitModel(row?.model || "");
    if (make) out.push(make);
  }

  for (const hint of Object.values(prefixHintsByKey || {})) {
    if (!hint) continue;
    if (String(hint.device_type || "scanner").toLowerCase() !== type) continue;
    if (hint.make) out.push(String(hint.make));
  }

  return uniqueSorted(out);
}

function buildModelSuggestions() {
  const type = String(els.type?.value || "scanner").toLowerCase();
  const makeTyped = String(els.make?.value || "").trim();
  const makeLower = makeTyped.toLowerCase();
  const catalog = makeCatalogForType(type);
  const out = [];

  if (makeTyped) {
    for (const [catalogMake, models] of Object.entries(catalog)) {
      if (catalogMake.toLowerCase() === makeLower) {
        out.push(...(models || []));
      }
    }
  } else {
    for (const models of Object.values(catalog)) {
      out.push(...(models || []));
    }
  }

  for (const row of devicesCache || []) {
    if (String(row?.device_type || "scanner").toLowerCase() !== type) continue;
    const [rowMake, rowModel] = splitModel(row?.model || "");
    if (makeTyped && rowMake.toLowerCase() !== makeLower) continue;
    if (rowModel) out.push(rowModel);
  }

  for (const hint of Object.values(prefixHintsByKey || {})) {
    if (!hint) continue;
    if (String(hint.device_type || "scanner").toLowerCase() !== type) continue;
    const hintMake = String(hint.make || "").trim();
    if (makeTyped && hintMake.toLowerCase() !== makeLower) continue;
    if (hint.model) out.push(String(hint.model));
  }

  return uniqueSorted(out);
}

function updateMakeInlineSuggestion() {
  currentMakeSuggestion = "";
  if (!els.makeHint) return;

  if (els.make?.readOnly) {
    els.makeHint.textContent = "";
    return;
  }

  const typed = String(els.make?.value || "");
  currentMakeSuggestion = findInlineSuggestion(typed, buildMakeSuggestions());
  els.makeHint.textContent = currentMakeSuggestion || "";
}

function updateModelInlineSuggestion() {
  currentModelSuggestion = "";
  if (!els.modelHint) return;

  if (els.model?.readOnly) {
    els.modelHint.textContent = "";
    return;
  }

  const typed = String(els.model?.value || "");
  currentModelSuggestion = findInlineSuggestion(typed, buildModelSuggestions());
  els.modelHint.textContent = currentModelSuggestion || "";
}

function refreshInlineSuggestions() {
  updateMakeInlineSuggestion();
  updateModelInlineSuggestion();
}

function setPopupVisibility(popupEl, visible) {
  if (!popupEl) return;
  if (visible) {
    popupEl.classList.remove("hidden");
    popupEl.style.display = "grid";
  } else {
    popupEl.classList.add("hidden");
    popupEl.style.display = "none";
  }
}

function hideScanPopup() {
  setPopupVisibility(els.scanPopup, false);
}

function showScanPopup(message, { allowRegister = false, serial = "" } = {}) {
  if (!els.scanPopup || !els.scanPopupMessage) return;

  pendingRegisterSerial = String(serial || "").trim();
  els.scanPopupMessage.textContent = String(message || "");
  setPopupVisibility(els.scanPopup, true);

  if (els.scanPopupRegister) {
    els.scanPopupRegister.classList.toggle("hidden", !allowRegister);
  }
}

function registerPendingDevice() {
  hideScanPopup();
  const serial = cleanToken(pendingRegisterSerial || els.serial.value || "");
  if (serial) {
    els.serial.value = serial;
    els.lookupSerial.value = serial;
  }
  setIdentityEditable(true);
  setStatus(trWeb("scanRegisterStatus"));
  if (els.make) {
    els.make.focus();
  }
}

function applyWebLanguageLabels() {
  if (els.scanPopupTitle) {
    els.scanPopupTitle.textContent = trWeb("scanPopupTitle");
  }
  if (els.scanPopupRegister) {
    els.scanPopupRegister.textContent = trWeb("scanPopupRegister");
  }
  if (els.scanPopupClose) {
    els.scanPopupClose.textContent = trWeb("scanPopupClose");
  }
  if (els.conflictPopupTitle) {
    els.conflictPopupTitle.textContent = trWeb("conflictTitle");
  }
  if (els.conflictPopupMessage) {
    els.conflictPopupMessage.textContent = trWeb("conflictMessage");
  }
  if (els.conflictReload) {
    els.conflictReload.textContent = trWeb("conflictReload");
  }
  if (els.conflictOverwrite) {
    els.conflictOverwrite.textContent = trWeb("conflictOverwrite");
  }
  if (els.conflictCancel) {
    els.conflictCancel.textContent = trWeb("conflictCancel");
  }
}

function normalizePrefixKey(value) {
  let raw = String(value || "").toUpperCase().replace(/[^A-Z0-9:]/g, "").trim();
  if (!raw) return "";
  if (raw.includes(":")) {
    const parts = raw.split(":", 2);
    return `${parts[0]}:${parts[1] || ""}`;
  }
  return raw;
}

function clearPrefixRuleForm() {
  selectedPrefixRuleId = "";
  if (els.prefixKey) els.prefixKey.value = "";
  if (els.prefixType) els.prefixType.value = "scanner";
  if (els.prefixMake) els.prefixMake.value = "";
  if (els.prefixModel) els.prefixModel.value = "";
  if (els.prefixPriority) els.prefixPriority.value = "100";
  if (els.prefixActive) els.prefixActive.checked = true;
}

function fillPrefixRuleForm(row) {
  selectedPrefixRuleId = String(row?.id || "");
  if (els.prefixKey) els.prefixKey.value = String(row?.prefix_key || "");
  if (els.prefixType) els.prefixType.value = String(row?.device_type || "scanner");
  if (els.prefixMake) els.prefixMake.value = String(row?.make || "");
  if (els.prefixModel) els.prefixModel.value = String(row?.model || "");
  if (els.prefixPriority) els.prefixPriority.value = String(row?.priority ?? 100);
  if (els.prefixActive) els.prefixActive.checked = row?.active !== false;
}

function renderPrefixRules(rows) {
  if (!els.prefixRulesList) return;
  if (!Array.isArray(rows) || !rows.length) {
    els.prefixRulesList.innerHTML = `
      <div class="prefix-row">
        <span>No rules</span>
        <span>-</span>
        <span>-</span>
        <span>-</span>
        <span>-</span>
        <span>-</span>
      </div>
    `;
    return;
  }

  els.prefixRulesList.innerHTML = rows
    .map(
      (row) => `
      <div class="prefix-row" data-prefix-id="${row.id}">
        <span>${row.prefix_key || ""}</span>
        <span>${row.device_type || ""}</span>
        <span>${row.make || ""}</span>
        <span>${row.model || ""}</span>
        <span>${row.priority ?? ""}</span>
        <span>${row.active === false ? "no" : "yes"}</span>
      </div>
    `
    )
    .join("");
}

async function loadPrefixRulesAdmin() {
  if (!authContext?.isAdmin) {
    if (els.prefixRulesStatus) {
      els.prefixRulesStatus.textContent = trWeb("prefixRulesAdminOnly");
    }
    renderPrefixRules([]);
    return;
  }

  if (els.prefixRulesStatus) {
    els.prefixRulesStatus.textContent = "Loading...";
  }

  try {
    const rows = await restRequest(
      "device_prefix_rules?select=id,prefix_key,device_type,make,model,priority,active,updated_at&order=priority.asc"
    );
    prefixRulesCache = Array.isArray(rows) ? rows : [];
    renderPrefixRules(prefixRulesCache);
    if (els.prefixRulesStatus) {
      els.prefixRulesStatus.textContent = trWebFmt("prefixRulesLoadedStatus", { count: prefixRulesCache.length });
    }
  } catch (error) {
    if (els.prefixRulesStatus) {
      els.prefixRulesStatus.textContent = trWebFmt("prefixRulesLoadError", { error: error.message });
    }
    setStatus(trWebFmt("prefixRulesLoadError", { error: error.message }), "error");
  }
}

async function savePrefixRule() {
  if (!authContext?.isAdmin) {
    setStatus(trWeb("prefixRulesAdminOnly"), "error");
    return;
  }

  const prefixKey = normalizePrefixKey(els.prefixKey?.value || "");
  if (!prefixKey) {
    setStatus(trWeb("prefixRuleInvalidKey"), "error");
    return;
  }

  const payload = {
    prefix_key: prefixKey,
    device_type: String(els.prefixType?.value || "scanner").trim() || "scanner",
    make: String(els.prefixMake?.value || "").trim(),
    model: String(els.prefixModel?.value || "").trim(),
    priority: Number(els.prefixPriority?.value || 100) || 100,
    active: Boolean(els.prefixActive?.checked),
  };

  try {
    if (selectedPrefixRuleId) {
      await restRequest(`device_prefix_rules?id=eq.${encodeURIComponent(selectedPrefixRuleId)}`, {
        method: "PATCH",
        body: payload,
      });
    } else {
      await restRequest("device_prefix_rules", {
        method: "POST",
        body: payload,
        prefer: "return=representation",
      });
    }
    setStatus(trWeb("prefixRuleSavedStatus"), "ok");
    await loadPrefixRules();
    await loadPrefixRulesAdmin();
    clearPrefixRuleForm();
  } catch (error) {
    setStatus(trWebFmt("prefixRulesSaveError", { error: error.message }), "error");
  }
}

async function deletePrefixRule() {
  if (!authContext?.isAdmin) {
    setStatus(trWeb("prefixRulesAdminOnly"), "error");
    return;
  }
  if (!selectedPrefixRuleId) {
    setStatus(trWeb("prefixRuleDeleteSelect"), "error");
    return;
  }
  if (!window.confirm(trWeb("prefixRuleDeleteConfirm"))) {
    return;
  }
  try {
    await restRequest(`device_prefix_rules?id=eq.${encodeURIComponent(selectedPrefixRuleId)}`, {
      method: "DELETE",
    });
    setStatus(trWeb("prefixRuleDeletedStatus"), "ok");
    await loadPrefixRules();
    await loadPrefixRulesAdmin();
    clearPrefixRuleForm();
  } catch (error) {
    setStatus(trWebFmt("prefixRulesDeleteError", { error: error.message }), "error");
  }
}

function askConflictResolution() {
  if (!els.conflictPopup) {
    return Promise.resolve("reload");
  }
  return new Promise((resolve) => {
    conflictResolve = resolve;
    setPopupVisibility(els.conflictPopup, true);
  });
}

function resolveConflictPopup(choice) {
  setPopupVisibility(els.conflictPopup, false);
  const done = conflictResolve;
  conflictResolve = null;
  if (done) done(choice);
}

function readStorageText(key) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? String(raw) : "";
  } catch {
    return "";
  }
}

function writeStorageText(key, value) {
  try {
    localStorage.setItem(key, String(value || ""));
  } catch {
    // ignore storage errors
  }
}

function normalizeTokenInput(raw) {
  return String(raw || "").trim().replace(/^Bearer\s+/i, "");
}

function decodeJwtPayload(token) {
  const parts = String(token || "").split(".");
  if (parts.length < 2) return null;
  const payloadPart = parts[1];
  if (!payloadPart) return null;

  try {
    const normalized = payloadPart.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, "=");
    const bytes = Uint8Array.from(atob(padded), (ch) => ch.charCodeAt(0));
    const payloadJson = new TextDecoder().decode(bytes);
    const parsed = JSON.parse(payloadJson);
    return parsed && typeof parsed === "object" ? parsed : null;
  } catch {
    return null;
  }
}

function claimToBool(value) {
  if (typeof value === "boolean") return value;
  if (typeof value === "number") return value !== 0;
  if (typeof value === "string") {
    const text = value.trim().toLowerCase();
    return text === "true" || text === "1" || text === "yes";
  }
  return false;
}

function extractAccessTokenFromUrl() {
  const tokenKeys = ["access_token", "token", "jwt"];
  let found = "";

  try {
    const search = new URLSearchParams(window.location.search || "");
    for (const key of tokenKeys) {
      const value = normalizeTokenInput(search.get(key) || "");
      if (value) {
        found = value;
        search.delete(key);
      }
    }
    if (found) {
      const nextSearch = search.toString();
      const nextUrl = `${window.location.pathname}${nextSearch ? `?${nextSearch}` : ""}${window.location.hash || ""}`;
      window.history.replaceState({}, "", nextUrl);
      return found;
    }
  } catch {
    // ignore URL parsing issues
  }

  try {
    const hash = String(window.location.hash || "").replace(/^#/, "");
    const hashParams = new URLSearchParams(hash);
    for (const key of tokenKeys) {
      const value = normalizeTokenInput(hashParams.get(key) || "");
      if (value) {
        found = value;
        break;
      }
    }
    if (found) {
      const nextUrl = `${window.location.pathname}${window.location.search || ""}`;
      window.history.replaceState({}, "", nextUrl);
      return found;
    }
  } catch {
    // ignore URL parsing issues
  }

  return "";
}

function resolveAuthContext() {
  const tokenFromUrl = extractAccessTokenFromUrl();
  if (tokenFromUrl) {
    writeStorageText(AUTH_TOKEN_STORAGE_KEY, tokenFromUrl);
  }

  const storedToken = normalizeTokenInput(readStorageText(AUTH_TOKEN_STORAGE_KEY));
  const jwtToken = normalizeTokenInput(tokenFromUrl || storedToken);
  const jwtClaims = decodeJwtPayload(jwtToken);

  const anonClaims = decodeJwtPayload(SUPABASE_KEY) || {};
  const roleFromJwt = String((jwtClaims && jwtClaims.role) || "").trim();
  const role = roleFromJwt || String(anonClaims.role || "anon");

  const appMetadata = (jwtClaims && typeof jwtClaims.app_metadata === "object" && jwtClaims.app_metadata) || {};
  const isAdmin =
    role.toLowerCase() === "service_role" ||
    claimToBool(jwtClaims && jwtClaims.device_admin) ||
    claimToBool(appMetadata.device_admin);

  return {
    role,
    isAdmin,
    hasJwtSession: Boolean(jwtToken),
    bearerToken: jwtToken || SUPABASE_KEY,
  };
}

function applyAuthUiState() {
  if (els.authInfo) {
    const mode = authContext?.hasJwtSession ? "session" : "anon";
    const adminText = authContext?.isAdmin ? "admin" : "operator";
    els.authInfo.textContent = `Role: ${authContext?.role || "anon"} (${adminText}, ${mode})`;
    els.authInfo.style.color = authContext?.isAdmin ? "#0a7a2f" : "#6b6b6b";
  }

  if (els.auditCard) {
    if (authContext?.isAdmin) {
      els.auditCard.classList.remove("hidden");
    } else {
      els.auditCard.classList.add("hidden");
      if (els.auditStatus) {
        els.auditStatus.textContent = "Admin only";
      }
    }
  }

  if (els.prefixRulesCard) {
    if (authContext?.isAdmin) {
      els.prefixRulesCard.classList.remove("hidden");
    } else {
      els.prefixRulesCard.classList.add("hidden");
      if (els.prefixRulesStatus) {
        els.prefixRulesStatus.textContent = trWeb("prefixRulesAdminOnly");
      }
    }
  }

  updateDiagnosticsPanel();
}

function updateDiagnosticsPanel() {
  if (!els.diagStatus) return;

  const queued = getQueuedSaves().length;
  const roleText = `${authContext?.role || "anon"} (${authContext?.isAdmin ? "admin" : "operator"})`;
  const lastSyncText = lastSuccessfulSyncAt
    ? new Date(lastSuccessfulSyncAt).toLocaleString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })
    : "n/a";

  if (els.diagOnline) {
    els.diagOnline.textContent = navigator.onLine ? "yes" : "no";
    els.diagOnline.style.color = navigator.onLine ? "#0a7a2f" : "#b00020";
  }
  if (els.diagQueue) {
    els.diagQueue.textContent = String(queued);
    els.diagQueue.style.color = queued > 0 ? "#b00020" : "#0a7a2f";
  }
  if (els.diagRole) {
    els.diagRole.textContent = roleText;
  }
  if (els.diagLastSync) {
    els.diagLastSync.textContent = lastSyncText;
  }
  if (els.diagApi) {
    els.diagApi.textContent = SUPABASE_URL;
  }

  const health = !navigator.onLine ? "offline" : queued > 0 ? "queue pending" : "healthy";
  els.diagStatus.textContent = `Health: ${health}`;
  els.diagStatus.style.color = health === "healthy" ? "#0a7a2f" : "#b00020";
}

function readStorageJson(key, fallbackValue) {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallbackValue;
    return JSON.parse(raw);
  } catch {
    return fallbackValue;
  }
}

function writeStorageJson(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // ignore storage errors
  }
}

function clearStorageKey(key) {
  try {
    localStorage.removeItem(key);
  } catch {
    // ignore storage errors
  }
}

function saveDraft() {
  writeStorageJson(DRAFT_STORAGE_KEY, {
    serial: els.serial.value || "",
    type: els.type.value || "scanner",
    status: els.statusSelect.value || "RECEIVED",
    make: els.make.value || "",
    model: els.model.value || "",
    from_store: els.fromStore.value || "",
    to_store: els.toStore.value || "",
    comment: els.comment.value || "",
  });
}

function restoreDraft() {
  const draft = readStorageJson(DRAFT_STORAGE_KEY, null);
  if (!draft || typeof draft !== "object") return false;

  els.serial.value = String(draft.serial || "");
  els.type.value = String(draft.type || "scanner");
  els.statusSelect.value = String(draft.status || "RECEIVED");
  els.make.value = String(draft.make || "");
  els.model.value = String(draft.model || "");
  els.fromStore.value = String(draft.from_store || "");
  els.toStore.value = String(draft.to_store || "");
  els.comment.value = String(draft.comment || "");
  return true;
}

function clearDraft() {
  clearStorageKey(DRAFT_STORAGE_KEY);
}

function getQueuedSaves() {
  const queue = readStorageJson(QUEUE_STORAGE_KEY, []);
  return Array.isArray(queue) ? queue : [];
}

function setQueuedSaves(queue) {
  writeStorageJson(QUEUE_STORAGE_KEY, Array.isArray(queue) ? queue : []);
  updateQueueStatus();
}

function enqueueSaveOperation(operation) {
  const queue = getQueuedSaves();
  queue.push({ ...operation, queued_at: new Date().toISOString() });
  setQueuedSaves(queue);
}

function shouldThrottleScan(cleanedSerial) {
  const now = Date.now();
  if (cleanedSerial === lastLoadedSerial && now - lastLoadedAt < SCAN_DEBOUNCE_MS) {
    return true;
  }
  lastLoadedSerial = cleanedSerial;
  lastLoadedAt = now;
  return false;
}

function shouldThrottleSave(cleanedSerial) {
  const now = Date.now();
  return cleanedSerial === lastSavedSerial && now - lastSavedAt < SAVE_DEBOUNCE_MS;
}

function markSave(cleanedSerial) {
  lastSavedSerial = cleanedSerial;
  lastSavedAt = Date.now();
}

function isConnectivityError(error) {
  const text = String((error && error.message) || error || "").toLowerCase();
  return !navigator.onLine || text.includes("failed to fetch") || text.includes("network") || text.includes("fetch");
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
  const firstSpace = text.indexOf(" ");
  if (firstSpace < 0) return [text, ""];
  return [text.slice(0, firstSpace), text.slice(firstSpace + 1).trim()];
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

function buildSaveOperation(cleanedToken) {
  const expected = getKnownRevisionForToken(cleanedToken);
  return {
    serial: normalizeForStore(cleanedToken),
    device_type: (els.type.value || "scanner").trim() || "scanner",
    model: composeModel(els.make.value, els.model.value),
    from_store: els.fromStore.value.trim(),
    to_store: els.toStore.value.trim(),
    status: els.statusSelect.value,
    comment: els.comment.value.trim(),
    expected_updated_at: expected || null,
  };
}

function getKnownRevisionForToken(token) {
  for (const variant of serialVariants(token)) {
    const rev = loadedRevisionBySerial.get(variant);
    if (rev) return rev;
  }
  return "";
}

function rememberRevisionForToken(token, updatedAt) {
  if (!updatedAt) return;
  for (const variant of serialVariants(token)) {
    loadedRevisionBySerial.set(variant, updatedAt);
  }
}

function buildPrefixHintsMap(rows) {
  const map = { ...FALLBACK_PREFIX_HINTS };
  if (!Array.isArray(rows)) return map;

  const sorted = [...rows].sort((a, b) => Number(a?.priority ?? 100) - Number(b?.priority ?? 100));
  for (const row of sorted) {
    if (!row || row.active === false) continue;
    const key = String(row.prefix_key || "").trim().toUpperCase();
    if (!key) continue;
    map[key] = {
      device_type: String(row.device_type || "scanner").trim().toLowerCase() || "scanner",
      make: String(row.make || "").trim(),
      model: String(row.model || "").trim(),
    };
  }
  return map;
}

async function loadPrefixRules() {
  try {
    const rows = await restRequest(
      "device_prefix_rules?select=prefix_key,device_type,make,model,priority,active&order=priority.asc"
    );
    prefixHintsByKey = buildPrefixHintsMap(rows);
  } catch {
    prefixHintsByKey = { ...FALLBACK_PREFIX_HINTS };
  }
}

function getPrefixHint(token) {
  return prefixHintsByKey[getPrefixKey(token)] || null;
}

function getFilteredRows() {
  const filter = String(els.listFilter.value || "").trim().toLowerCase();
  if (!filter) return devicesCache;

  return devicesCache.filter((row) => {
    return [row.serial, row.device_type, row.model, row.status, row.from_store, row.to_store, row.comment]
      .map((v) => String(v || "").toLowerCase())
      .some((v) => v.includes(filter));
  });
}

function csvEscape(value) {
  const text = String(value || "");
  if (text.includes('"') || text.includes(",") || text.includes("\n")) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

function isAndroidWebView() {
  const ua = String(navigator.userAgent || "");
  return /Android/i.test(ua) && (/\bwv\b/i.test(ua) || /; wv\)/i.test(ua));
}

async function copyTextToClipboard(text) {
  const payload = String(text || "");
  if (!payload) return false;

  try {
    if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
      await navigator.clipboard.writeText(payload);
      return true;
    }
  } catch {
    // continue with legacy fallback
  }

  try {
    const ta = document.createElement("textarea");
    ta.value = payload;
    ta.setAttribute("readonly", "readonly");
    ta.style.position = "fixed";
    ta.style.top = "-1000px";
    ta.style.left = "-1000px";
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    const copied = document.execCommand("copy");
    document.body.removeChild(ta);
    return Boolean(copied);
  } catch {
    return false;
  }
}

async function exportVisibleDevicesCsv() {
  const rows = getFilteredRows();
  if (!rows.length) {
    setStatus("No rows to export", "error");
    return;
  }

  const headers = ["serial", "device_type", "model", "status", "from_store", "to_store", "comment", "updated_at"];
  const lines = [headers.join(",")];

  for (const row of rows) {
    const vals = [
      row.serial,
      row.device_type,
      row.model,
      row.status,
      row.from_store,
      row.to_store,
      row.comment,
      row.updated_at,
    ].map(csvEscape);
    lines.push(vals.join(","));
  }

  const csv = lines.join("\n");
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const filename = `devices_${stamp}.csv`;

  let downloaded = false;
  try {
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.rel = "noopener";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    downloaded = true;
  } catch {
    downloaded = false;
  }

  if (downloaded && !isAndroidWebView()) {
    setStatus(`Exported ${rows.length} row(s) to CSV`, "ok");
    return;
  }

  const copied = await copyTextToClipboard(csv);
  if (copied) {
    setStatus(`CSV copied (${rows.length} row(s)). Paste into a file named ${filename}.`, "ok");
    return;
  }

  try {
    const dataUrl = `data:text/csv;charset=utf-8,${encodeURIComponent(csv)}`;
    window.open(dataUrl, "_blank");
    setStatus(`CSV opened in browser view. Save as ${filename}.`, "ok");
    return;
  } catch {
    setStatus("CSV export is not supported on this device WebView. Use desktop browser for export.", "error");
  }
}

async function syncNow() {
  setStatus("Manual sync started...");
  await processQueuedSaves();
  await loadDevicesList();
  const pending = getQueuedSaves().length;
  if (pending > 0) {
    setStatus(`Manual sync done. Pending queue: ${pending}`, "error");
  } else {
    setStatus("Manual sync complete", "ok");
  }
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
  refreshInlineSuggestions();
}

function resetForm() {
  els.serial.value = "";
  resetIdentityFields();
  resetMutableFields();
  setIdentityEditable(true);
  saveDraft();
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
  refreshInlineSuggestions();
  saveDraft();
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
  refreshInlineSuggestions();
  saveDraft();
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
    Authorization: `Bearer ${authContext?.bearerToken || SUPABASE_KEY}`,
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

async function processQueuedSaves() {
  if (queueSyncInProgress || !navigator.onLine) return;

  const queue = getQueuedSaves();
  if (!queue.length) return;

  queueSyncInProgress = true;
  setSyncInfo("syncing queued saves");

  let synced = 0;
  const remaining = [];

  try {
    for (let i = 0; i < queue.length; i += 1) {
      const op = queue[i];
      try {
        const existing = await getDeviceBySerial(op.serial || "");
        const editPayload = {
          from_store: op.from_store || "",
          to_store: op.to_store || "",
          status: op.status || "RECEIVED",
          comment: op.comment || "",
        };

        if (existing) {
          const expected = String(op.expected_updated_at || "").trim();
          const path = expected
            ? `devices?id=eq.${encodeURIComponent(existing.id)}&updated_at=eq.${encodeURIComponent(expected)}`
            : `devices?id=eq.${encodeURIComponent(existing.id)}`;
          const rows = await restRequest(path, { method: "PATCH", body: editPayload, prefer: "return=representation" });

          if (expected && Array.isArray(rows) && rows.length === 0) {
            remaining.push({ ...op, conflict: true });
            continue;
          }

          if (Array.isArray(rows) && rows[0]?.updated_at) {
            rememberRevisionForToken(op.serial || "", rows[0].updated_at);
          }
        } else {
          const rows = await restRequest("devices", {
            method: "POST",
            body: {
              serial: op.serial || "",
              device_type: op.device_type || "scanner",
              model: op.model || "",
              ...editPayload,
            },
            prefer: "return=representation",
          });
          if (Array.isArray(rows) && rows[0]?.updated_at) {
            rememberRevisionForToken(op.serial || "", rows[0].updated_at);
          }
        }
        synced += 1;
      } catch (error) {
        if (isConnectivityError(error)) {
          remaining.push(op, ...queue.slice(i + 1));
          break;
        }
        remaining.push(op);
      }
    }
  } finally {
    setQueuedSaves(remaining);
    queueSyncInProgress = false;
  }

  if (synced > 0) {
    lastSuccessfulSyncAt = new Date().toISOString();
    setStatus(`Synced ${synced} queued save(s)`, "ok");
    setSyncInfo(`synced ${synced} queued save(s)`, "ok");
    await loadDevicesList();
  }

  if (remaining.length && navigator.onLine) {
    const conflicts = remaining.filter((x) => x && x.conflict).length;
    if (conflicts > 0) {
      setStatus(`Queue pending: ${remaining.length} save(s), ${conflicts} conflict(s)`, "error");
      setSyncInfo(`queued pending ${remaining.length} with conflicts`, "error");
    } else {
      setStatus(`Queue pending: ${remaining.length} save(s)`, "error");
      setSyncInfo(`queued pending ${remaining.length}`, "error");
    }
  } else if (!remaining.length && navigator.onLine) {
    setSyncInfo("up to date", "ok");
  }
}

async function loadByScannedValue(rawValue) {
  const token = extractPreferredSerial(rawValue);
  if (!token) {
    if (String(rawValue || "").trim()) {
      els.serial.value = "";
      setIdentityEditable(true);
      setStatus("Serial must be S + 13/14 digits, or first token like laptop QR serial", "error");
      saveDraft();
    }
    return;
  }

  const cleaned = cleanToken(token);
  if (shouldThrottleScan(cleaned)) {
    return;
  }

  els.serial.value = cleaned;
  els.lookupSerial.value = cleaned;
  saveDraft();

  let device = null;
  try {
    device = await getDeviceBySerial(cleaned);
  } catch (error) {
    setStatus(`Database error: ${error.message}`, "error");
    return;
  }

  if (device) {
    rememberRevisionForToken(cleaned, device.updated_at || "");
    if (device.serial) {
      rememberRevisionForToken(device.serial, device.updated_at || "");
    }
    fillFormFromDevice(device);
    setStatus(trWeb("scanFoundDbStatus"), "ok");
    showScanPopup(trWeb("scanFoundDbPopup"));
    return;
  }

  await loadPrefixRules();

  for (const variant of serialVariants(cleaned)) {
    loadedRevisionBySerial.delete(variant);
  }

  resetIdentityFields();
  resetMutableFields();
  setIdentityEditable(true);

  const guessed = guessFromCache(cleaned);
  if (guessed) {
    applyGuess(guessed);
    setStatus(trWeb("scanNotFoundHistoryStatus"), "ok");
    showScanPopup(trWeb("scanNotFoundHistoryPopup"), { allowRegister: true, serial: cleaned });
    return;
  }

  const hinted = getPrefixHint(cleaned);
  if (hinted) {
    applyGuess(hinted);
    setStatus(trWeb("scanNotFoundPrefixStatus"), "ok");
    showScanPopup(trWeb("scanNotFoundPrefixPopup"), { allowRegister: true, serial: cleaned });
    return;
  }

  setStatus(trWeb("scanNotFoundStatus"));
  showScanPopup(trWeb("scanNotFoundPopup"), { allowRegister: true, serial: cleaned });
  saveDraft();
}

async function saveDevice() {
  const token = extractPreferredSerial(els.serial.value);
  if (!token) {
    setStatus("Serial must be valid before saving", "error");
    return;
  }

  const cleaned = cleanToken(token);
  if (shouldThrottleSave(cleaned)) {
    setStatus("Ignored duplicate save tap");
    return;
  }

  els.serial.value = cleaned;
  saveDraft();

  const queuedOperation = buildSaveOperation(cleaned);

  let existing = null;
  try {
    existing = await getDeviceBySerial(cleaned);
  } catch (error) {
    if (isConnectivityError(error)) {
      enqueueSaveOperation(queuedOperation);
      markSave(cleaned);
      setStatus("Offline: save queued and will sync automatically", "error");
      return;
    }
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
      const expected = queuedOperation.expected_updated_at || getKnownRevisionForToken(cleaned);
      const path = expected
        ? `devices?id=eq.${encodeURIComponent(existing.id)}&updated_at=eq.${encodeURIComponent(expected)}`
        : `devices?id=eq.${encodeURIComponent(existing.id)}`;
      const rows = await restRequest(path, { method: "PATCH", body: editPayload, prefer: "return=representation" });
      if (expected && Array.isArray(rows) && rows.length === 0) {
        const decision = await askConflictResolution();
        if (decision === "overwrite") {
          const overwriteRows = await restRequest(`devices?id=eq.${encodeURIComponent(existing.id)}`, {
            method: "PATCH",
            body: editPayload,
            prefer: "return=representation",
          });
          if (Array.isArray(overwriteRows) && overwriteRows[0]?.updated_at) {
            rememberRevisionForToken(cleaned, overwriteRows[0].updated_at);
          }
          setStatus(trWeb("conflictOverwrittenStatus"), "ok");
          markSave(cleaned);
        } else if (decision === "reload") {
          await loadByScannedValue(cleaned);
          setStatus(trWeb("conflictReloadedStatus"), "error");
          return;
        } else {
          setStatus(trWeb("conflictNoChangeStatus"), "error");
          return;
        }
      } else {
        if (Array.isArray(rows) && rows[0]?.updated_at) {
          rememberRevisionForToken(cleaned, rows[0].updated_at);
        }
        setStatus("Updated existing device", "ok");
        markSave(cleaned);
      }
    } else {
      const insertPayload = {
        serial: normalizeForStore(cleaned),
        device_type: (els.type.value || "scanner").trim() || "scanner",
        model: composeModel(els.make.value, els.model.value),
        ...editPayload,
      };
      const rows = await restRequest("devices", { method: "POST", body: insertPayload, prefer: "return=representation" });
      if (Array.isArray(rows) && rows[0]?.updated_at) {
        rememberRevisionForToken(cleaned, rows[0].updated_at);
      }
      setStatus("Added new device", "ok");
      markSave(cleaned);
    }
  } catch (error) {
    if (isConnectivityError(error)) {
      enqueueSaveOperation(queuedOperation);
      markSave(cleaned);
      setStatus("Offline: save queued and will sync automatically", "error");
      return;
    }
    setStatus(`Save failed: ${error.message}`, "error");
    return;
  }

  await loadDevicesList();
  await loadByScannedValue(cleaned);
  await processQueuedSaves();
}

function renderDevicesList() {
  const rows = getFilteredRows();
  const hasFilter = String(els.listFilter.value || "").trim().length > 0;

  els.listStatus.textContent = `Showing ${rows.length}`;

  if (!rows.length) {
    const helper = hasFilter ? "No rows match this filter" : "No devices visible. Check Supabase SELECT policy.";
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
  setSyncInfo("loading device list");
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
    refreshInlineSuggestions();
    lastSuccessfulSyncAt = new Date().toISOString();
    setSyncInfo("up to date", "ok");
  } catch (error) {
    devicesCache = [];
    els.listStatus.textContent = `Database error: ${error.message}`;
    setSyncInfo("database error", "error");
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

function renderAuditRows(rows) {
  if (!els.auditList) return;
  if (!Array.isArray(rows) || !rows.length) {
    els.auditList.innerHTML = `
      <div class="audit-row">
        <span>No audit rows</span>
        <span>-</span>
        <span>-</span>
        <span>-</span>
      </div>
    `;
    return;
  }

  els.auditList.innerHTML = rows
    .map(
      (row) => `
      <div class="audit-row">
        <span>${String(row.event_time || "").replace("T", " ")}</span>
        <span>${row.operation || ""}</span>
        <span>${row.serial || ""}</span>
        <span>${row.actor || ""}</span>
      </div>
    `
    )
    .join("");
}

async function loadAuditLogs() {
  if (!els.auditList || !els.auditStatus) return;

  if (!authContext?.isAdmin) {
    renderAuditRows([]);
    els.auditStatus.textContent = "Admin only";
    return;
  }

  const serialFilter = cleanToken(els.auditSerial?.value || "");
  let path = "device_audit_log?select=id,event_time,operation,serial,actor,source,txid&order=event_time.desc&limit=120";
  if (serialFilter) {
    path += `&serial=ilike.${encodeURIComponent(`%${serialFilter}%`)}`;
  }

  els.auditStatus.textContent = "Loading...";
  try {
    const rows = await restRequest(path);
    renderAuditRows(Array.isArray(rows) ? rows : []);
    els.auditStatus.textContent = `Rows: ${Array.isArray(rows) ? rows.length : 0}`;
  } catch (error) {
    renderAuditRows([]);
    els.auditStatus.textContent = "Admin access required";
    setStatus(`Audit unavailable: ${error.message}`, "error");
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
  saveDraft();
  await loadByScannedValue(cleaned);
}

els.serial.addEventListener("input", () => {
  els.serial.value = sanitizeSerialField(els.serial.value);
  clearTimeout(scanTimer);
  saveDraft();

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

[els.type, els.statusSelect, els.make, els.model, els.fromStore, els.toStore, els.comment].forEach((input) => {
  input.addEventListener("input", saveDraft);
  input.addEventListener("change", saveDraft);
});

els.type.addEventListener("change", () => {
  refreshInlineSuggestions();
});

els.make.addEventListener("input", () => {
  updateMakeInlineSuggestion();
  updateModelInlineSuggestion();
});

els.model.addEventListener("input", () => {
  updateModelInlineSuggestion();
});

els.make.addEventListener("keydown", (e) => {
  if (e.key !== "Tab") return;
  if (!currentMakeSuggestion) return;
  els.make.value = currentMakeSuggestion;
  saveDraft();
  updateMakeInlineSuggestion();
  updateModelInlineSuggestion();
});

els.model.addEventListener("keydown", (e) => {
  if (e.key !== "Tab") return;
  if (!currentModelSuggestion) return;
  els.model.value = currentModelSuggestion;
  saveDraft();
  updateModelInlineSuggestion();
});

els.lookupLoad.addEventListener("click", loadFromLookup);
els.save.addEventListener("click", saveDevice);
els.syncNow.addEventListener("click", syncNow);
els.exportCsv.addEventListener("click", exportVisibleDevicesCsv);
if (els.auditLoad) {
  els.auditLoad.addEventListener("click", loadAuditLogs);
}
if (els.auditSerial) {
  els.auditSerial.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      loadAuditLogs();
    }
  });
}
if (els.scanPopupClose) {
  els.scanPopupClose.addEventListener("click", hideScanPopup);
}
if (els.scanPopupRegister) {
  els.scanPopupRegister.addEventListener("click", registerPendingDevice);
}
if (els.scanPopup) {
  els.scanPopup.addEventListener("click", (e) => {
    if (e.target === els.scanPopup) {
      hideScanPopup();
    }
  });
}
if (els.conflictReload) {
  els.conflictReload.addEventListener("click", () => resolveConflictPopup("reload"));
}
if (els.conflictOverwrite) {
  els.conflictOverwrite.addEventListener("click", () => resolveConflictPopup("overwrite"));
}
if (els.conflictCancel) {
  els.conflictCancel.addEventListener("click", () => resolveConflictPopup("cancel"));
}
if (els.conflictPopup) {
  els.conflictPopup.addEventListener("click", (e) => {
    if (e.target === els.conflictPopup) {
      resolveConflictPopup("cancel");
    }
  });
}
window.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    hideScanPopup();
    resolveConflictPopup("cancel");
  }
});
if (els.prefixRulesRefresh) {
  els.prefixRulesRefresh.addEventListener("click", loadPrefixRulesAdmin);
}
if (els.prefixSave) {
  els.prefixSave.addEventListener("click", savePrefixRule);
}
if (els.prefixDelete) {
  els.prefixDelete.addEventListener("click", deletePrefixRule);
}
if (els.prefixClear) {
  els.prefixClear.addEventListener("click", clearPrefixRuleForm);
}
if (els.prefixKey) {
  els.prefixKey.addEventListener("input", () => {
    els.prefixKey.value = normalizePrefixKey(els.prefixKey.value);
  });
}
if (els.prefixRulesList) {
  els.prefixRulesList.addEventListener("click", (e) => {
    const row = e.target.closest(".prefix-row[data-prefix-id]");
    if (!row) return;
    const id = String(row.getAttribute("data-prefix-id") || "");
    if (!id) return;
    const found = prefixRulesCache.find((x) => String(x?.id || "") === id);
    if (found) fillPrefixRuleForm(found);
  });
}
if (els.diagRefresh) {
  els.diagRefresh.addEventListener("click", () => {
    updateDiagnosticsPanel();
    loadDevicesList();
    processQueuedSaves();
  });
}
els.clear.addEventListener("click", () => {
  resetForm();
  clearDraft();
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
applyWebLanguageLabels();
refreshInlineSuggestions();
updateQueueStatus();
if (els.appVersion) {
  els.appVersion.textContent = `Version: ${WEB_APP_VERSION}`;
}
authContext = resolveAuthContext();
applyAuthUiState();
setSyncInfo(navigator.onLine ? "starting" : "offline", navigator.onLine ? "info" : "error");
updateDiagnosticsPanel();
const recoveredDraft = restoreDraft();
if (recoveredDraft) {
  setStatus("Recovered unsaved draft");
  if (els.serial.value) {
    loadByScannedValue(els.serial.value);
  }
}
loadPrefixRules();
loadPrefixRulesAdmin();
els.serial.focus();
loadDevicesList();
setTimeout(() => {
  loadPrefixRules();
  loadPrefixRulesAdmin();
  loadDevicesList();
  processQueuedSaves();
}, 1200);
window.addEventListener("focus", () => {
  authContext = resolveAuthContext();
  applyAuthUiState();
  loadPrefixRules();
  loadPrefixRulesAdmin();
  loadDevicesList();
  processQueuedSaves();
});
window.addEventListener("online", () => {
  setStatus("Back online. Syncing queued saves...");
  setSyncInfo("back online", "ok");
  updateDiagnosticsPanel();
  processQueuedSaves();
});
window.addEventListener("offline", () => {
  setStatus("Offline mode: saves will be queued", "error");
  setSyncInfo("offline", "error");
  updateDiagnosticsPanel();
});
setInterval(() => {
  authContext = resolveAuthContext();
  applyAuthUiState();
  loadPrefixRules();
  loadPrefixRulesAdmin();
  loadDevicesList();
  processQueuedSaves();
}, 20000);
