const SUPABASE_URL = "https://qvlduxpdcwgmokjdsdfp.supabase.co";
const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InF2bGR1eHBkY3dnbW9ramRzZGZwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ5Mzk5MzMsImV4cCI6MjA5MDUxNTkzM30.3HiNhJKLrMmc0I11Y7qMS73fi0b1XUaEorTAL6wJOsk";

const SCANNER_SERIAL_RE = /^S\d{13,14}$/i;
const PLAIN_SCANNER_RE = /^\d{13,14}$/;
const GENERIC_SERIAL_RE = /^[A-Z0-9]{8,20}$/;
const WEB_BARCODE_FORMATS = [
  "qr_code",
  "code_128",
  "code_39",
  "code_93",
  "codabar",
  "ean_13",
  "ean_8",
  "itf",
  "upc_a",
  "upc_e",
  "data_matrix",
  "pdf417",
  "aztec",
];

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
    Zebra: ["DS2208", "DS2278", "DS3608", "DS3678", "DS4608", "DS4678", "DS8108", "DS8178", "DS9308", "LI2208", "LS2208", "RS5100", "RS6100", "SE4710", "TC20", "TC21", "TC22", "TC25", "TC26", "TC51", "TC52", "TC53", "TC53-HC", "TC56", "TC57", "TC58", "TC58-HC", "TC70", "TC70x", "TC72", "TC75", "TC75x", "TC77", "MC40", "MC55", "MC67", "MC92N0", "MC93", "MC2200", "MC2700", "MC3300", "MC3300x", "MC3390x", "WS50"],
    Datalogic: ["Gryphon GD4500", "Gryphon GBT4500", "Gryphon GM4500", "QuickScan QD2430", "QuickScan QD2500", "PowerScan PD9630", "PowerScan PM9600", "PowerScan PBT9600", "Memor 10", "Memor 11", "Skorpio X4", "Skorpio X5", "Falcon X4", "Joya Touch"],
    Apple: ["MacBook Air M1", "MacBook Air M2", "MacBook Air M3", "MacBook Pro 13", "MacBook Pro 14", "MacBook Pro 16", "Mac Mini", "Mac Studio", "iMac", "Mac Pro"],
    Asus: ["ZenBook 14", "ZenBook Duo", "ZenBook Pro", "VivoBook 15", "VivoBook Pro", "ROG Zephyrus", "ROG Strix", "TUF Gaming", "ExpertBook"],
    Dell: ["Latitude 3420", "Latitude 5430", "Latitude 5440", "Latitude 7330", "Latitude 7430", "Latitude 7440", "XPS 13", "XPS 15", "Precision 3570", "Precision 3580", "Vostro 3520", "Inspiron 15", "Alienware m15", "Alienware x14"],
  },
  laptop: {
    Dell: ["Latitude 3420", "Latitude 5430", "Latitude 5440", "Latitude 7330", "Latitude 7430", "Latitude 7440", "XPS 13", "XPS 15", "Precision 3570", "Precision 3580", "Vostro 3520", "Inspiron 15", "Alienware m15", "Alienware x14"],
      Asus: ["ZenBook 14", "ZenBook Duo", "ZenBook Pro", "VivoBook 15", "VivoBook Pro", "ROG Zephyrus", "ROG Strix", "TUF Gaming", "ExpertBook"],
    HP: ["EliteBook 830 G8", "EliteBook 830 G9", "EliteBook 840 G8", "EliteBook 840 G9", "EliteBook 840 G10", "EliteBook 850 G8", "ProBook 440 G8", "ProBook 450 G8", "ProBook 440 G9", "ProBook 450 G9", "ZBook Firefly 14", "ZBook Power 15"],
    Apple: ["MacBook Air 13 M1", "MacBook Air 13 M2", "MacBook Air 15 M2", "MacBook Pro 13", "MacBook Pro 14", "MacBook Pro 16"],
  },
  tablet: {
    Samsung: ["Galaxy Tab A7", "Galaxy Tab A8", "Galaxy Tab S6 Lite", "Galaxy Tab S7", "Galaxy Tab S8", "Galaxy Tab S9", "Galaxy Tab Active3", "Galaxy Tab Active4 Pro", "Galaxy Tab Active5"],
    Apple: ["iPad 9th Gen", "iPad 10th Gen", "iPad Air 5", "iPad Mini 6", "iPad Pro 11", "iPad Pro 12.9"],
    Zebra: ["ET40", "ET45", "L10", "XSLATE L10"],
  },
  phone: {
    Samsung: ["Galaxy S21", "Galaxy S22", "Galaxy S23", "Galaxy S24", "Galaxy A54", "Galaxy A55", "Galaxy XCover 5", "Galaxy XCover 6 Pro", "Galaxy XCover 7"],
    Apple: ["iPhone 11", "iPhone 12", "iPhone 13", "iPhone 14", "iPhone 15", "iPhone 16", "iPhone SE"],
  },
  printer: {
    Zebra: ["ZD220", "ZD230", "ZD421", "ZD621", "ZT111", "ZT231", "ZT411", "ZT421", "GK420d", "GX430t", "QLn220", "QLn320", "ZQ310", "ZQ320", "ZQ511", "ZQ521", "ZR138"],
  },
  other: {
    HP: ["Engage One", "Engage Flex Pro", "RP9"],
    Datalogic: ["Magellan 1500i", "Magellan 3410VSi", "Joya Touch A6"],
    Zebra: ["CC600", "CC6000", "DS9308 Scale", "MP7000"],
  },
};

const DRAFT_STORAGE_KEY = "rimi.inventory.draft.v1";
const QUEUE_STORAGE_KEY = "rimi.inventory.queue.v1";
const AUTH_TOKEN_STORAGE_KEY = "rimi.inventory.auth_jwt";
const WEB_LANG_STORAGE_KEY = "rimi.inventory.lang";
const WEB_THEME_STORAGE_KEY = "rimi.inventory.theme";
const SCAN_DEBOUNCE_MS = 900;
const SAVE_DEBOUNCE_MS = 1400;
const WEB_APP_VERSION = "web-2026.04.07";

const WARRANTY_MARKER = "[WARRANTY]";
const WARRANTY_STRICT_MODE = true;
const WARRANTY_PUBLIC_API_ONLY = true;
const WARRANTY_PUBLIC_API_TIMEOUT_MS = 9000;
const WARRANTY_PUBLIC_API_CACHE_TTL_MS = 10 * 60 * 1000;
const WARRANTY_PUBLIC_API_BY_MAKE = {
  hp: { endpoint: "", serialParam: "serialNumber" },
  lenovo: { endpoint: "", serialParam: "serialNumber" },
  zebra: { endpoint: "", serialParam: "serial" },
  samsung: { endpoint: "", serialParam: "serialNumber" },
  apple: { endpoint: "", serialParam: "serialNumber" },
};
const WARRANTY_CHECKER_URL_BY_MAKE = {
  hp: "https://support.hp.com/us-en/check-warranty",
    asus: "https://www.asus.com/us/support/warranty-status",
    dell: "https://www.dell.com/support/home/en-us/?app=warranty",
  lenovo: "https://pcsupport.lenovo.com/us/en/warrantylookup#/",
  zebra: "https://support.zebra.com/warrantycheck",
  samsung: "https://www.samsung.com/us/support/warranty/",
  apple: "https://checkcoverage.apple.com/",
};
const WARRANTY_CHECKER_SERIAL_PARAM_BY_MAKE = {
  hp: "serialnumber",
    asus: "serial",
    dell: "serviceTag",
  lenovo: "serial",
  zebra: "serial",
  samsung: "serialNumber",
  apple: "sn",
};
const WARRANTY_MONTHS_BY_PREFIX = {
  "5CG32": 36,
  "5CG21": 36,
  "5CG": 36,
  PF: 36,
  PC: 36,
  "40": 36,
  "24": 36,
  "21": 36,
  "20": 36,
  "19": 36,
  "18": 36,
  "17": 36,
};
const WARRANTY_PREFIX_KEYS_DESC = Object.keys(WARRANTY_MONTHS_BY_PREFIX).sort((a, b) => b.length - a.length);
const WARRANTY_MONTHS_BY_TYPE = {
  scanner: 36,
  laptop: 36,
  tablet: 24,
  phone: 24,
  printer: 24,
  other: 12,
};

const WEB_I18N = {
  en: {
    scanPopupTitle: "Scan result",
    scanPopupRegister: "Register new device",
    scanPopupClose: "Close",
    scanQrTitle: "Scan QR code",
    scanQrStarting: "Starting camera...",
    scanQrUnsupported: "Camera QR scan is not supported on this WebView. Use scanner input instead.",
    scanQrPermissionDenied: "Camera permission denied. Allow Camera permission and try again.",
    scanQrCanceled: "QR scan canceled",
    scanQrDetected: "QR scanned: {serial}",
    scanQrUnrecognized: "QR read, but serial format was not recognized",
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
    uiThemeDark: "Dark mode",
    uiThemeLight: "Light mode",
    uiBrandSubtitle: "Device tracking",
    uiActionTitle: "Action",
    uiActionSubtitle: "Scan scanner serial (S + 13/14 digits) or laptop QR first token (e.g. 5CG3285C9K,...)",
    uiDevicesTitle: "Devices",
    uiDevicesSubtitle: "Read-only list from database",
    uiDiagTitle: "Diagnostics",
    uiDiagSubtitle: "Current connectivity and sync health",
    uiDiagOnline: "Online",
    uiDiagLastSync: "Last sync",
    uiDiagApi: "API",
    uiAuditTitle: "Audit (Admin)",
    uiAuditSubtitle: "Change history from database (admin access required)",
    uiPrefixTitle: "Prefix Rules (Admin)",
    uiPrefixSubtitle: "Manage DB prefix->device model mapping",
    uiPrefixKey: "Prefix key",
    uiPrefixPriority: "Priority",
    uiPrefixActive: "Active",
    uiFooterHosted: "Hosted on GitHub Pages",
    uiLabelSerial: "Serial (scan here)",
    uiLabelType: "Type",
    uiLabelStatus: "Status",
    uiLabelMake: "Make",
    uiLabelModel: "Model",
    uiLabelFrom: "From store",
    uiLabelTo: "To store",
    uiLabelComment: "Comment",
    uiSaveUpdate: "Save / Update",
    uiClear: "Clear",
    uiConnectZq620: "Connect ZQ620",
    uiPrintSticker: "Print asset sticker",
    uiScanQr: "Scan QR (camera)",
    uiSelectPrinter: "Select printer...",
    uiFindPrinters: "Find printers",
    uiConnectSelected: "Connect selected",
    uiPrinterNotConnected: "Printer: not connected",
    uiSyncNow: "Sync now",
    uiRefresh: "Refresh",
    uiRefreshDiagnostics: "Refresh diagnostics",
    uiExportCsv: "Export CSV",
    uiLoad: "Load",
    uiOpenChecker: "Open checker",
    uiLoadAudit: "Load audit",
    uiSaveRule: "Save rule",
    uiDeleteRule: "Delete rule",
    uiClearForm: "Clear form",
    uiClearFilters: "Clear filters",
    uiRefreshRules: "Refresh rules",
    uiLookupPlaceholder: "Find exact serial (S18167522504743 / 18167522504743 / 5CG3285C9K)",
    uiFilterPlaceholder: "Filter by serial/model/status",
    uiAuditPlaceholder: "Optional serial filter",
    uiQueued: "Queued",
    uiSyncPrefix: "Sync",
    uiRolePrefix: "Role",
    uiHealthPrefix: "Health",
    uiHealthOffline: "offline",
    uiHealthOfflineNoInternet: "offline (no internet)",
    uiHealthQueuePending: "queue pending",
    uiHealthHealthy: "healthy",
    status_RECEIVED: "Received",
    status_PREPARING: "Preparing",
    status_PREPARED: "Prepared",
    status_SENT: "Sent",
    status_IN_USE: "In use",
    status_RETURNED: "Returned",
    status_RETIRED: "Retired",
    type_scanner: "Scanner",
    type_laptop: "Laptop",
    type_tablet: "Tablet",
    type_phone: "Phone",
    type_printer: "Printer",
    type_other: "Other",
    uiTableSerial: "Serial",
    uiTableType: "Type",
    uiTableModel: "Model",
    uiTableStatus: "Status",
    uiTableFrom: "From",
    uiTableTo: "To",
    uiTableComment: "Comment",
    uiTableTime: "Time",
    uiTableOperation: "Operation",
    uiTableActor: "Actor",
    msgShowing: "Showing {count}",
    msgNoRowsMatchFilter: "No rows match this filter",
    msgNoDevicesVisible: "No devices visible",
    msgCheckPolicy: "No devices visible. Check Supabase SELECT policy.",
    msgLoading: "Loading...",
    msgLoadingDb: "Loading database...",
    msgPleaseWait: "Please wait",
    msgDatabaseError: "Database error",
    msgNoAuditRows: "No audit rows",
    msgRowsCount: "Rows: {count}",
    msgAdminOnly: "Admin only",
    msgAdminRequired: "Admin access required",
    msgEnterSerialFormat: "Enter serial in scanner or laptop format",
    msgCleared: "Cleared",
    msgRecoveredDraft: "Recovered unsaved draft",
    msgBackOnlineSyncing: "Back online. Syncing queued saves...",
    msgOfflineQueued: "Offline mode: saves will be queued",
    msgNoInternet: "No internet connection. Connect to Wi-Fi or mobile data.",
    msgWarrantyCheckerOpened: "Warranty checker opened",
    msgWarrantyCheckerOpenFailed: "Could not open warranty checker on this device",
    msgWarrantyCheckerUnavailable: "Warranty checker is not available for this make",
    uiDiagApiOffline: "offline (no internet)",
    sync_starting: "starting",
    sync_offline: "offline",
    sync_back_online: "back online",
    sync_up_to_date: "up to date",
    sync_syncing_queued_saves: "syncing queued saves",
  },
  lv: {
    scanPopupTitle: "Skenēšanas rezultāts",
    scanPopupRegister: "Reģistrēt jaunu ierīci",
    scanPopupClose: "Aizvērt",
    scanQrTitle: "Skenēt QR kodu",
    scanQrStarting: "Palaižu kameru...",
    scanQrUnsupported: "QR skenēšana ar kameru šajā WebView nav atbalstīta. Izmanto skenera ievadi.",
    scanQrPermissionDenied: "Kameras atļauja liegta. Atļauj kameru un mēģini vēlreiz.",
    scanQrCanceled: "QR skenēšana atcelta",
    scanQrDetected: "QR nolasīts: {serial}",
    scanQrUnrecognized: "QR nolasīts, bet seriāla formātu neatpazina",
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
    uiThemeDark: "Tumšais režīms",
    uiThemeLight: "Gaišais režīms",
    uiBrandSubtitle: "Ierīču uzskaite",
    uiActionTitle: "Darbība",
    uiActionSubtitle: "Skenē skenera seriālu (S + 13/14 cipari) vai laptop QR pirmo daļu (piem. 5CG3285C9K,...)",
    uiDevicesTitle: "Ierīces",
    uiDevicesSubtitle: "Tikai lasāms saraksts no datubāzes",
    uiDiagTitle: "Diagnostika",
    uiDiagSubtitle: "Pašreizējā savienojuma un sinhronizācijas veselība",
    uiDiagOnline: "Tiešsaistē",
    uiDiagLastSync: "Pēdējā sinhr.",
    uiDiagApi: "API",
    uiAuditTitle: "Audits (Admin)",
    uiAuditSubtitle: "Izmaiņu vēsture no datubāzes (nepieciešama admin piekļuve)",
    uiPrefixTitle: "Prefiksu noteikumi (Admin)",
    uiPrefixSubtitle: "Pārvaldi DB prefikss->ierīces modelis kartējumu",
    uiPrefixKey: "Prefiksa atslēga",
    uiPrefixPriority: "Prioritāte",
    uiPrefixActive: "Aktīvs",
    uiFooterHosted: "Publicēts GitHub Pages",
    uiLabelSerial: "Seriāls (skenē šeit)",
    uiLabelType: "Tips",
    uiLabelStatus: "Statuss",
    uiLabelMake: "Ražotājs",
    uiLabelModel: "Modelis",
    uiLabelFrom: "No veikala",
    uiLabelTo: "Uz veikalu",
    uiLabelComment: "Komentārs",
    uiSaveUpdate: "Saglabāt / Atjaunināt",
    uiClear: "Notīrīt",
    uiConnectZq620: "Pieslēgt ZQ620",
    uiPrintSticker: "Drukāt uzlīmi",
    uiScanQr: "Skenēt QR (kamera)",
    uiSelectPrinter: "Izvēlies printeri...",
    uiFindPrinters: "Meklēt printerus",
    uiConnectSelected: "Pieslēgt izvēlēto",
    uiPrinterNotConnected: "Printeris: nav pieslēgts",
    uiSyncNow: "Sinhronizēt tagad",
    uiRefresh: "Atjaunot",
    uiRefreshDiagnostics: "Atjaunot diagnostiku",
    uiExportCsv: "Eksportēt CSV",
    uiLoad: "Ielādēt",
    uiOpenChecker: "Atvērt garantijas pārbaudi",
    uiLoadAudit: "Ielādēt auditu",
    uiSaveRule: "Saglabāt noteikumu",
    uiDeleteRule: "Dzēst noteikumu",
    uiClearForm: "Notīrīt formu",
    uiClearFilters: "Notīrīt filtrus",
    uiRefreshRules: "Atjaunot noteikumus",
    uiLookupPlaceholder: "Meklē precīzu seriālu (S18167522504743 / 18167522504743 / 5CG3285C9K)",
    uiFilterPlaceholder: "Filtrē pēc seriāla/modeļa/statusa",
    uiAuditPlaceholder: "Neobligāts seriāla filtrs",
    uiQueued: "Rindā",
    uiSyncPrefix: "Sinhr.",
    uiRolePrefix: "Loma",
    uiHealthPrefix: "Veselība",
    uiHealthOffline: "bezsaistē",
    uiHealthOfflineNoInternet: "bezsaistē (nav interneta)",
    uiHealthQueuePending: "rinda gaida",
    uiHealthHealthy: "ok",
    status_RECEIVED: "Saņemts",
    status_PREPARING: "Sagatavošanā",
    status_PREPARED: "Sagatavots",
    status_SENT: "Nosūtīts",
    status_IN_USE: "Lietošanā",
    status_RETURNED: "Atgriezts",
    status_RETIRED: "Norakstīts",
    type_scanner: "Skeneris",
    type_laptop: "Portatīvais",
    type_tablet: "Planšete",
    type_phone: "Telefons",
    type_printer: "Printeris",
    type_other: "Cits",
    uiTableSerial: "Seriāls",
    uiTableType: "Tips",
    uiTableModel: "Modelis",
    uiTableStatus: "Statuss",
    uiTableFrom: "No",
    uiTableTo: "Uz",
    uiTableComment: "Komentārs",
    uiTableTime: "Laiks",
    uiTableOperation: "Darbība",
    uiTableActor: "Lietotājs",
    msgShowing: "Rāda {count}",
    msgNoRowsMatchFilter: "Šim filtram nav rindu",
    msgNoDevicesVisible: "Nav redzamu ierīču",
    msgCheckPolicy: "Nav redzamu ierīču. Pārbaudi Supabase SELECT politiku.",
    msgLoading: "Ielādē...",
    msgLoadingDb: "Ielādē datubāzi...",
    msgPleaseWait: "Lūdzu uzgaidi",
    msgDatabaseError: "Datubāzes kļūda",
    msgNoAuditRows: "Nav audita ierakstu",
    msgRowsCount: "Rindas: {count}",
    msgAdminOnly: "Tikai admin",
    msgAdminRequired: "Nepieciešama admin piekļuve",
    msgEnterSerialFormat: "Ievadi seriālu skenera vai laptop formātā",
    msgCleared: "Notīrīts",
    msgRecoveredDraft: "Atjaunots nesaglabāts melnraksts",
    msgBackOnlineSyncing: "Atkal tiešsaistē. Sinhronizēju gaidošos ierakstus...",
    msgOfflineQueued: "Bezsaistes režīms: saglabāšana tiks ielikta rindā",
    msgNoInternet: "Nav interneta savienojuma. Pieslēdzies Wi-Fi vai mobilajiem datiem.",
    msgWarrantyCheckerOpened: "Garantijas pārbaude atvērta",
    msgWarrantyCheckerOpenFailed: "Neizdevās atvērt garantijas pārbaudi šajā ierīcē",
    msgWarrantyCheckerUnavailable: "Šim ražotājam nav pieejama garantijas pārbaude",
    uiDiagApiOffline: "bezsaistē (nav interneta)",
    sync_starting: "sāk",
    sync_offline: "bezsaistē",
    sync_back_online: "atkal tiešsaistē",
    sync_up_to_date: "aktuāls",
    sync_syncing_queued_saves: "sinhronizē rindu",
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

function resolveWebTheme() {
  let candidate = "";
  try {
    candidate = String(localStorage.getItem(WEB_THEME_STORAGE_KEY) || "").trim().toLowerCase();
  } catch {
    candidate = "";
  }

  if (candidate === "dark" || candidate === "light") {
    return candidate;
  }

  try {
    if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      return "dark";
    }
  } catch {
    // ignore media query errors
  }
  return "light";
}

let WEB_THEME = resolveWebTheme();

function trWeb(key) {
  return WEB_I18N[WEB_LANG]?.[key] || WEB_I18N.en[key] || key;
}

function trWebFmt(key, vars = {}) {
  const template = trWeb(key);
  return String(template).replace(/\{(\w+)\}/g, (_m, k) => String(vars[k] ?? ""));
}

function trSyncMessage(message) {
  const key = `sync_${String(message || "").trim().replace(/\s+/g, "_")}`;
  const translated = trWeb(key);
  return translated === key ? String(message || "") : translated;
}

const els = {
  brandSubtitle: document.getElementById("brandSubtitle"),
  langSelect: document.getElementById("langSelect"),
  themeToggle: document.getElementById("themeToggle"),
  serial: document.getElementById("serial"),
  scanQr: document.getElementById("scanQr"),
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
  printerConnect: document.getElementById("printerConnect"),
  printSticker: document.getElementById("printSticker"),
  printerPicker: document.getElementById("printerPicker"),
  printerRefresh: document.getElementById("printerRefresh"),
  printerConnectSelected: document.getElementById("printerConnectSelected"),
  printerStatus: document.getElementById("printerStatus"),
  printerHealthConnection: document.getElementById("printerHealthConnection"),
  printerHealthTarget: document.getElementById("printerHealthTarget"),
  printerHealthPerms: document.getElementById("printerHealthPerms"),
  printerHealthBonded: document.getElementById("printerHealthBonded"),
  printerHealthLastPrint: document.getElementById("printerHealthLastPrint"),
  devicesList: document.getElementById("devicesList"),
  listStatus: document.getElementById("listStatus"),
  listFilter: document.getElementById("listFilter"),
  itemsPerPage: document.getElementById("itemsPerPage"),
  paginationInfo: document.getElementById("paginationInfo"),
  prevPage: document.getElementById("prevPage"),
  nextPage: document.getElementById("nextPage"),
  listClear: document.getElementById("listClear"),
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
  qrScanPopup: document.getElementById("qrScanPopup"),
  qrScanTitle: document.getElementById("qrScanTitle"),
  qrScanVideo: document.getElementById("qrScanVideo"),
  qrScanMessage: document.getElementById("qrScanMessage"),
  qrScanClose: document.getElementById("qrScanClose"),
  conflictPopup: document.getElementById("conflictPopup"),
  conflictPopupTitle: document.getElementById("conflictPopupTitle"),
  conflictPopupMessage: document.getElementById("conflictPopupMessage"),
  conflictReload: document.getElementById("conflictReload"),
  conflictOverwrite: document.getElementById("conflictOverwrite"),
  conflictCancel: document.getElementById("conflictCancel"),
  lookupSerial: document.getElementById("lookupSerial"),
  lookupLoad: document.getElementById("lookupLoad"),
  authInfo: document.getElementById("authInfo"),
  footerHosted: document.getElementById("footerHosted"),
};

let devicesCache = [];
let scanTimer = null;
let currentPage = 1;
let itemsPerPage = 10;
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
let printerCandidates = [];
let lastPrinterPrintAt = "";
let qrScanStream = null;
let qrScanActive = false;
let qrScanAnimationId = 0;
let qrDetector = null;
const loadedCreatedAtBySerial = new Map();
const loadedWarrantyBySerial = new Map();
const warrantyApiResultByKey = new Map();

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

function setPrinterStatus(message, tone = "info") {
  if (!els.printerStatus) return;
  els.printerStatus.textContent = String(message || "");
  if (tone === "error") {
    els.printerStatus.style.color = "#b00020";
  } else if (tone === "ok") {
    els.printerStatus.style.color = "#0a7a2f";
  } else {
    els.printerStatus.style.color = "#6b6b6b";
  }
}

function parsePrinterBridgeResponse(raw) {
  if (raw && typeof raw === "object") {
    return raw;
  }
  try {
    const parsed = JSON.parse(String(raw || ""));
    if (parsed && typeof parsed === "object") {
      return parsed;
    }
  } catch {
    // ignore parse errors
  }
  return { ok: false, message: String(raw || "Unknown printer bridge response") };
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function hasPrinterBridge() {
  return Boolean(window.AndroidPrinter && typeof window.AndroidPrinter === "object");
}

function callPrinterBridge(method, ...args) {
  if (!hasPrinterBridge()) {
    return { ok: false, message: "Printer bridge unavailable in this build" };
  }
  try {
    const fn = window.AndroidPrinter[method];
    if (typeof fn !== "function") {
      return { ok: false, message: `Printer method not available: ${method}` };
    }
    const res = fn.apply(window.AndroidPrinter, args);
    return parsePrinterBridgeResponse(res);
  } catch (error) {
    return { ok: false, message: String(error && error.message ? error.message : error || "Printer bridge error") };
  }
}

function zplSafe(value, maxLen = 40) {
  const normalized = String(value || "")
    .replace(/[\^~]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  return normalized.slice(0, maxLen) || "-";
}

function buildAssetStickerZpl(device) {
  const serial = zplSafe(device?.serial || "-", 28);
  const [makeFromModel, modelFromModel] = splitModel(device?.model || "");
  const make = zplSafe(makeFromModel || "-", 18);
  const model = zplSafe(modelFromModel || device?.model || "-", 22);
  const typeCode = String(device?.device_type || "device").trim().toLowerCase();
  const translatedType = trWeb(`type_${typeCode}`);
  const typeLabel = zplSafe(translatedType && translatedType !== `type_${typeCode}` ? translatedType : typeCode, 12);
  const topLine = zplSafe(`${typeLabel} : ${make} ${model}`.replace(/\s+/g, " "), 44);
  const commentRaw = String(device?.comment || "").trim();
  const commentLine = commentRaw ? zplSafe(commentRaw, 48) : "";

  return [
    "^XA",
    "^PW576",
    "^LL360",
    "^LH0,0",
    "^CI28",
    "^FO8,8^GB560,344,8^FS",
    `^FO20,28^A0N,38,38^FB536,1,0,C^FD${topLine}^FS`,
    `^FO188,98^BQN,2,6^FDLA,${serial}^FS`,
    ...(commentLine ? [`^FO20,296^A0N,24,24^FB536,1,0,C^FD${commentLine}^FS`] : []),
    `^FO20,312^A0N,34,34^FB536,1,0,C^FD${serial}^FS`,
    "^XZ",
  ].join("\n");
}

function findDeviceInCacheByToken(token) {
  const variants = serialVariants(token).map((x) => cleanToken(x));
  return (
    (devicesCache || []).find((row) => {
      const rowSerial = cleanToken(row?.serial || "");
      return variants.includes(rowSerial);
    }) || null
  );
}

function setPrinterHealthField(element, text, tone = "info") {
  if (!element) return;
  element.textContent = String(text || "-");
  if (tone === "error") {
    element.style.color = "#b00020";
  } else if (tone === "ok") {
    element.style.color = "#0a7a2f";
  } else {
    element.style.color = "var(--ink)";
  }
}

function formatLocalDateTime(iso) {
  if (!iso) return "-";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "-";
  return date.toLocaleString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function renderPrinterPicker(candidates, selectedAddress = "") {
  if (!els.printerPicker) return;
  const safeList = Array.isArray(candidates) ? candidates : [];
  printerCandidates = safeList;

  const options = ['<option value="">Select printer...</option>'];
  for (const item of safeList) {
    const name = String(item?.name || "(unnamed)");
    const address = String(item?.address || "");
    if (!address) continue;
    const bondedTag = item?.bonded ? " [bonded]" : " [new]";
    const label = `${name}${bondedTag} (${address})`;
    options.push(`<option value="${escapeHtml(address)}">${escapeHtml(label)}</option>`);
  }

  if (options.length === 1) {
    options.push('<option value="">No printers found</option>');
  }

  els.printerPicker.innerHTML = options.join("");

  const requested = String(selectedAddress || "").trim();
  if (requested) {
    els.printerPicker.value = requested;
  }
}

function refreshPrinterHealth({ silent = false } = {}) {
  if (!hasPrinterBridge()) {
    setPrinterHealthField(els.printerHealthConnection, "Bridge unavailable", "error");
    setPrinterHealthField(els.printerHealthTarget, "Android WebView only", "info");
    setPrinterHealthField(els.printerHealthPerms, "Unknown", "info");
    setPrinterHealthField(els.printerHealthBonded, "-", "info");
    setPrinterHealthField(els.printerHealthLastPrint, formatLocalDateTime(lastPrinterPrintAt), "info");
    if (!silent) {
      setPrinterStatus("Printer bridge unavailable", "error");
    }
    return;
  }

  const health = callPrinterBridge("getPrinterHealth");
  const connected = Boolean(health.connected);
  const printerName = String(health.printer || "").trim();
  const printerAddress = String(health.address || "").trim();
  const targetText = printerName
    ? `${printerName}${printerAddress ? ` (${printerAddress})` : ""}`
    : els.printerPicker?.selectedOptions?.[0]?.textContent || "-";

  const connectPermOk = Boolean(health.connectPermission);
  const scanPermOk = Boolean(health.scanPermission);
  const locationPermOk = Boolean(health.locationPermission);
  const permissionTone = connectPermOk && scanPermOk && locationPermOk ? "ok" : "error";
  const permissionText = `connect:${connectPermOk ? "ok" : "missing"}, scan:${scanPermOk ? "ok" : "missing"}, location:${locationPermOk ? "ok" : "missing"}`;

  const connectionText = connected
    ? `Connected${printerName ? ` (${printerName})` : ""}`
    : String(health.message || "Not connected");

  setPrinterHealthField(els.printerHealthConnection, connectionText, connected ? "ok" : "info");
  setPrinterHealthField(els.printerHealthTarget, targetText, connected ? "ok" : "info");
  setPrinterHealthField(els.printerHealthPerms, permissionText, permissionTone);
  setPrinterHealthField(els.printerHealthBonded, String(health.bondedCount ?? "-"), "info");
  setPrinterHealthField(els.printerHealthLastPrint, formatLocalDateTime(lastPrinterPrintAt), lastPrinterPrintAt ? "ok" : "info");

  if (connected) {
    setPrinterStatus(`Printer connected: ${printerName || "ZQ620"}`, "ok");
  } else {
    const msg = String(health.message || "not connected");
    const lowered = msg.toLowerCase();
    const tone =
      lowered.includes("disabled") || lowered.includes("permission") || lowered.includes("unavailable")
        ? "error"
        : "info";
    setPrinterStatus(`Printer: ${msg}`, tone);
  }
}

async function refreshPrinterCandidates({ silent = false } = {}) {
  if (!hasPrinterBridge()) {
    renderPrinterPicker([]);
    refreshPrinterHealth({ silent: true });
    if (!silent) {
      setStatus("Printer integration is available only inside Android WebView APK", "error");
    }
    return;
  }

  const previouslySelected = String(els.printerPicker?.value || "").trim();
  let result = callPrinterBridge("refreshOnlinePrinters");
  const unsupportedRefreshMethod = !result.ok && /not available/i.test(String(result.message || ""));
  if (unsupportedRefreshMethod) {
    result = callPrinterBridge("listLikelyPrinters");
  }
  const candidates = Array.isArray(result.printers) ? result.printers : [];
  renderPrinterPicker(candidates, previouslySelected);

  if (!silent) {
    if (result.ok) {
      setStatus(`Found ${candidates.length} powered printer(s)`, "ok");
    } else {
      setStatus(`Printer scan failed: ${result.message || "unknown error"}`, "error");
    }
  }

  refreshPrinterHealth({ silent: true });
}

async function connectSelectedPrinter() {
  if (!hasPrinterBridge()) {
    setStatus("Printer integration is available only inside Android WebView APK", "error");
    return;
  }

  const selectedAddress = String(els.printerPicker?.value || "").trim();
  if (!selectedAddress) {
    setStatus("Select a printer first", "error");
    return;
  }

  const result = callPrinterBridge("connectPrinterByAddress", selectedAddress);
  if (result.ok) {
    const selected = printerCandidates.find((x) => String(x?.address || "") === selectedAddress);
    const name = String(result.printer || selected?.name || "ZQ620");
    setPrinterStatus(`Printer connected: ${name}`, "ok");
    setStatus(`Connected selected printer: ${name}`, "ok");
    await refreshPrinterCandidates({ silent: true });
    refreshPrinterHealth({ silent: true });
  } else {
    setPrinterStatus(`Printer error: ${result.message || "connect failed"}`, "error");
    setStatus(`Selected printer connect failed: ${result.message || "unknown error"}`, "error");
    refreshPrinterHealth({ silent: true });
  }
}

async function connectZq620Printer() {
  const result = callPrinterBridge("connectZq620");
  if (result.ok) {
    const printerName = String(result.printer || "ZQ620");
    setPrinterStatus(`Printer connected: ${printerName}`, "ok");
    setStatus(`Printer connected: ${printerName}`, "ok");
    await refreshPrinterCandidates({ silent: true });
    refreshPrinterHealth({ silent: true });
  } else {
    setPrinterStatus(`Printer error: ${result.message || "connect failed"}`, "error");
    setStatus(`Printer connect failed: ${result.message || "unknown error"}`, "error");
    refreshPrinterHealth({ silent: true });
  }
}

function refreshPrinterStatus() {
  if (!hasPrinterBridge()) {
    setPrinterStatus("Printer bridge unavailable", "error");
    refreshPrinterHealth({ silent: true });
    return;
  }
  const status = callPrinterBridge("getPrinterStatus");
  if (status.ok) {
    const printerName = String(status.printer || "ZQ620");
    setPrinterStatus(`Printer connected: ${printerName}`, "ok");
  } else {
    setPrinterStatus(`Printer: ${status.message || "not connected"}`, "info");
  }
  refreshPrinterHealth({ silent: true });
}

async function printAssetSticker() {
  if (!hasPrinterBridge()) {
    setStatus("Printer integration is available only inside Android WebView APK", "error");
    setPrinterStatus("Printer bridge unavailable", "error");
    return;
  }

  const token = extractPreferredSerial(els.serial.value || els.lookupSerial.value || "");
  if (!token) {
    setStatus("Scan or load a device first", "error");
    return;
  }

  const cleaned = cleanToken(token);
  let device = null;

  try {
    device = await getDeviceBySerial(cleaned);
  } catch {
    device = null;
  }

  if (!device) {
    device = findDeviceInCacheByToken(cleaned);
  }

  if (!device) {
    setStatus("Device not found in database. Load existing device first.", "error");
    return;
  }

  const zpl = buildAssetStickerZpl(device);
  const result = callPrinterBridge("printZpl", zpl);
  if (result.ok) {
    const serial = String(device.serial || cleaned);
    lastPrinterPrintAt = new Date().toISOString();
    setStatus(`Sticker printed for ${serial}`, "ok");
    setPrinterStatus(`Printed: ${serial}`, "ok");
    refreshPrinterHealth({ silent: true });
  } else {
    setStatus(`Print failed: ${result.message || "unknown error"}`, "error");
    setPrinterStatus(`Printer error: ${result.message || "print failed"}`, "error");
    refreshPrinterHealth({ silent: true });
  }
}

function setSyncInfo(message, tone = "info") {
  if (!els.syncInfo) return;
  const translatedMessage = trSyncMessage(message);
  let text = `${trWeb("uiSyncPrefix")}: ${translatedMessage}`;
  if (message === "up to date" && lastSuccessfulSyncAt) {
    const local = new Date(lastSuccessfulSyncAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    text = `${trWeb("uiSyncPrefix")}: ${translatedMessage} (${local})`;
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
    els.queueStatus.textContent = `${trWeb("uiQueued")}: ${count}`;
    els.queueStatus.style.color = "#b00020";
  } else {
    els.queueStatus.textContent = `${trWeb("uiQueued")}: 0`;
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

function setQrScanMessage(message, tone = "info") {
  if (!els.qrScanMessage) return;
  els.qrScanMessage.textContent = String(message || "");
  if (tone === "error") {
    els.qrScanMessage.style.color = "#b00020";
  } else if (tone === "ok") {
    els.qrScanMessage.style.color = "#0a7a2f";
  } else {
    els.qrScanMessage.style.color = "var(--ink)";
  }
}

async function handleAndroidQrScanResult(payload) {
  let parsed = payload;
  if (typeof payload === "string") {
    try {
      parsed = JSON.parse(payload);
    } catch {
      parsed = { rawValue: String(payload || "") };
    }
  }

  const canceled = Boolean(parsed?.canceled);
  const rawValue = String(parsed?.rawValue || parsed?.text || "").trim();
  if (canceled || !rawValue) {
    setStatus(trWeb("scanQrCanceled"));
    return;
  }

  await handleQrDetected(rawValue);
}

window.onAndroidQrScanResult = (payload) => {
  handleAndroidQrScanResult(payload);
};

function stopQrCameraScan() {
  if (qrScanAnimationId) {
    cancelAnimationFrame(qrScanAnimationId);
  }
  qrScanAnimationId = 0;
  qrScanActive = false;

  if (qrScanStream) {
    for (const track of qrScanStream.getTracks()) {
      try {
        track.stop();
      } catch {
        // ignore track stop failures
      }
    }
  }
  qrScanStream = null;

  if (els.qrScanVideo) {
    try {
      els.qrScanVideo.pause();
    } catch {
      // ignore pause errors
    }
    els.qrScanVideo.srcObject = null;
  }
}

function hideQrScanPopup({ silent = false } = {}) {
  stopQrCameraScan();
  setPopupVisibility(els.qrScanPopup, false);
  if (!silent) {
    setStatus(trWeb("scanQrCanceled"));
  }
}

async function handleQrDetected(rawValue) {
  stopQrCameraScan();
  setPopupVisibility(els.qrScanPopup, false);

  const raw = String(rawValue || "").trim();
  if (!raw) {
    setStatus(trWeb("scanQrUnrecognized"), "error");
    return;
  }

  const token = extractPreferredSerial(raw, { allowGenericSingle: true });
  if (!token) {
    setStatus(trWeb("scanQrUnrecognized"), "error");
    return;
  }

  const cleaned = cleanToken(token);
  els.serial.value = cleaned;
  els.lookupSerial.value = cleaned;
  saveDraft();
  setStatus(trWebFmt("scanQrDetected", { serial: cleaned }), "ok");
  await loadByScannedValue(cleaned, { allowGenericSingle: true });
}

function scheduleQrFrame() {
  qrScanAnimationId = requestAnimationFrame(runQrScanFrame);
}

function runQrScanFrame() {
  if (!qrScanActive || !els.qrScanVideo || !qrDetector) {
    return;
  }

  qrDetector
    .detect(els.qrScanVideo)
    .then((codes) => {
      if (!qrScanActive) {
        return;
      }

      const found = (codes || []).find((item) => item && String(item.rawValue || "").trim());
      if (found) {
        handleQrDetected(found.rawValue);
        return;
      }

      scheduleQrFrame();
    })
    .catch(() => {
      if (qrScanActive) {
        scheduleQrFrame();
      }
    });
}

async function startQrCameraScan() {
  if (qrScanActive) {
    return;
  }

  if (hasPrinterBridge()) {
    const nativeResult = callPrinterBridge("scanQr");
    if (nativeResult.ok) {
      setStatus(trWeb("scanQrStarting"));
      return;
    }
  }

  if (!navigator.mediaDevices || typeof navigator.mediaDevices.getUserMedia !== "function") {
    setStatus(trWeb("scanQrUnsupported"), "error");
    return;
  }

  if (typeof window.BarcodeDetector !== "function") {
    setStatus(trWeb("scanQrUnsupported"), "error");
    return;
  }

  try {
    qrDetector = new window.BarcodeDetector({ formats: WEB_BARCODE_FORMATS });
  } catch {
    try {
      qrDetector = new window.BarcodeDetector();
    } catch {
      setStatus(trWeb("scanQrUnsupported"), "error");
      return;
    }
  }

  setPopupVisibility(els.qrScanPopup, true);
  setQrScanMessage(trWeb("scanQrStarting"));

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: { ideal: "environment" },
        width: { ideal: 1280 },
        height: { ideal: 720 },
      },
      audio: false,
    });

    qrScanStream = stream;
    if (els.qrScanVideo) {
      els.qrScanVideo.srcObject = stream;
      await els.qrScanVideo.play();
    }
    qrScanActive = true;
    scheduleQrFrame();
  } catch (error) {
    stopQrCameraScan();
    setPopupVisibility(els.qrScanPopup, false);
    const text = String(error?.name || error?.message || "");
    if (/NotAllowedError|PermissionDenied/i.test(text)) {
      setStatus(trWeb("scanQrPermissionDenied"), "error");
    } else {
      setStatus(trWeb("scanQrUnsupported"), "error");
    }
  }
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

function setTextBySelector(selector, value) {
  const el = document.querySelector(selector);
  if (el) {
    el.textContent = String(value || "");
  }
}

function setPlaceholderBySelector(selector, value) {
  const el = document.querySelector(selector);
  if (el) {
    el.setAttribute("placeholder", String(value || ""));
  }
}

function setOptionText(selectEl, value, label) {
  if (!selectEl) return;
  const option = selectEl.querySelector(`option[value="${value}"]`);
  if (option) {
    option.textContent = String(label || value);
  }
}

function applyWebLanguageLabels() {
  document.documentElement.setAttribute("lang", WEB_LANG);

  if (els.langSelect) {
    els.langSelect.value = WEB_LANG;
  }

  if (els.brandSubtitle) {
    els.brandSubtitle.textContent = trWeb("uiBrandSubtitle");
  }

  setTextBySelector(".card--action .card__title", trWeb("uiActionTitle"));
  setTextBySelector(".card--action .card__subtitle", trWeb("uiActionSubtitle"));
  setTextBySelector("#devicesCard .card__title", trWeb("uiDevicesTitle"));
  setTextBySelector("#devicesCard .card__subtitle", trWeb("uiDevicesSubtitle"));
  setTextBySelector("#diagnosticsCard .card__title", trWeb("uiDiagTitle"));
  setTextBySelector("#diagnosticsCard .card__subtitle", trWeb("uiDiagSubtitle"));
  setTextBySelector("#auditCard .card__title", trWeb("uiAuditTitle"));
  setTextBySelector("#auditCard .card__subtitle", trWeb("uiAuditSubtitle"));
  setTextBySelector("#prefixRulesCard .card__title", trWeb("uiPrefixTitle"));
  setTextBySelector("#prefixRulesCard .card__subtitle", trWeb("uiPrefixSubtitle"));

  setTextBySelector('label[for="serial"]', trWeb("uiLabelSerial"));
  setTextBySelector('label[for="type"]', trWeb("uiLabelType"));
  setTextBySelector('label[for="statusSelect"]', trWeb("uiLabelStatus"));
  setTextBySelector('label[for="make"]', trWeb("uiLabelMake"));
  setTextBySelector('label[for="model"]', trWeb("uiLabelModel"));
  setTextBySelector('label[for="fromStore"]', trWeb("uiLabelFrom"));
  setTextBySelector('label[for="toStore"]', trWeb("uiLabelTo"));
  setTextBySelector('label[for="comment"]', trWeb("uiLabelComment"));

  if (els.save) els.save.textContent = trWeb("uiSaveUpdate");
  if (els.clear) els.clear.textContent = trWeb("uiClear");
  if (els.scanQr) els.scanQr.textContent = trWeb("uiScanQr");
  if (els.printerConnect) els.printerConnect.textContent = trWeb("uiConnectZq620");
  if (els.printSticker) els.printSticker.textContent = trWeb("uiPrintSticker");
  if (els.printerRefresh) els.printerRefresh.textContent = trWeb("uiFindPrinters");
  if (els.printerConnectSelected) els.printerConnectSelected.textContent = trWeb("uiConnectSelected");

  if (els.printerPicker) {
    const firstOption = els.printerPicker.querySelector('option[value=""]');
    if (firstOption) {
      firstOption.textContent = trWeb("uiSelectPrinter");
    }
  }

  if (els.syncNow) els.syncNow.textContent = trWeb("uiSyncNow");
  if (els.refreshList) els.refreshList.textContent = trWeb("uiRefresh");
  if (els.exportCsv) els.exportCsv.textContent = trWeb("uiExportCsv");
  if (els.lookupLoad) els.lookupLoad.textContent = trWeb("uiLoad");
  if (els.listClear) els.listClear.textContent = trWeb("uiClearFilters");
  if (els.diagRefresh) els.diagRefresh.textContent = trWeb("uiRefreshDiagnostics");
  if (els.auditLoad) els.auditLoad.textContent = trWeb("uiLoadAudit");
  if (els.prefixRulesRefresh) els.prefixRulesRefresh.textContent = trWeb("uiRefreshRules");
  if (els.prefixSave) els.prefixSave.textContent = trWeb("uiSaveRule");
  if (els.prefixDelete) els.prefixDelete.textContent = trWeb("uiDeleteRule");
  if (els.prefixClear) els.prefixClear.textContent = trWeb("uiClearForm");

  setPlaceholderBySelector("#lookupSerial", trWeb("uiLookupPlaceholder"));
  setPlaceholderBySelector("#listFilter", trWeb("uiFilterPlaceholder"));
  setPlaceholderBySelector("#auditSerial", trWeb("uiAuditPlaceholder"));

  if (els.type) {
    setOptionText(els.type, "scanner", trWeb("type_scanner"));
    setOptionText(els.type, "laptop", trWeb("type_laptop"));
    setOptionText(els.type, "tablet", trWeb("type_tablet"));
    setOptionText(els.type, "phone", trWeb("type_phone"));
    setOptionText(els.type, "printer", trWeb("type_printer"));
    setOptionText(els.type, "other", trWeb("type_other"));
  }

  if (els.prefixType) {
    setOptionText(els.prefixType, "scanner", trWeb("type_scanner"));
    setOptionText(els.prefixType, "laptop", trWeb("type_laptop"));
    setOptionText(els.prefixType, "tablet", trWeb("type_tablet"));
    setOptionText(els.prefixType, "phone", trWeb("type_phone"));
    setOptionText(els.prefixType, "other", trWeb("type_other"));
  }

  if (els.statusSelect) {
    setOptionText(els.statusSelect, "RECEIVED", trWeb("status_RECEIVED"));
    setOptionText(els.statusSelect, "PREPARING", trWeb("status_PREPARING"));
    setOptionText(els.statusSelect, "PREPARED", trWeb("status_PREPARED"));
    setOptionText(els.statusSelect, "SENT", trWeb("status_SENT"));
    setOptionText(els.statusSelect, "IN_USE", trWeb("status_IN_USE"));
    setOptionText(els.statusSelect, "RETURNED", trWeb("status_RETURNED"));
    setOptionText(els.statusSelect, "RETIRED", trWeb("status_RETIRED"));
  }

  setTextBySelector("#devicesCard .row--head span:nth-child(1)", trWeb("uiTableSerial"));
  setTextBySelector("#devicesCard .row--head span:nth-child(2)", trWeb("uiTableType"));
  setTextBySelector("#devicesCard .row--head span:nth-child(3)", trWeb("uiTableModel"));
  setTextBySelector("#devicesCard .row--head span:nth-child(4)", trWeb("uiTableStatus"));
  setTextBySelector("#devicesCard .row--head span:nth-child(5)", trWeb("uiTableFrom"));
  setTextBySelector("#devicesCard .row--head span:nth-child(6)", trWeb("uiTableTo"));
  setTextBySelector("#devicesCard .row--head span:nth-child(7)", trWeb("uiTableComment"));

  setTextBySelector("#auditCard .audit-row--head span:nth-child(1)", trWeb("uiTableTime"));
  setTextBySelector("#auditCard .audit-row--head span:nth-child(2)", trWeb("uiTableOperation"));
  setTextBySelector("#auditCard .audit-row--head span:nth-child(3)", trWeb("uiTableSerial"));
  setTextBySelector("#auditCard .audit-row--head span:nth-child(4)", trWeb("uiTableActor"));

  setTextBySelector("#diagnosticsCard .diag-item:nth-child(1) span", trWeb("uiDiagOnline"));
  setTextBySelector("#diagnosticsCard .diag-item:nth-child(2) span", trWeb("uiQueued"));
  setTextBySelector("#diagnosticsCard .diag-item:nth-child(3) span", trWeb("uiRolePrefix"));
  setTextBySelector("#diagnosticsCard .diag-item:nth-child(4) span", trWeb("uiDiagLastSync"));
  setTextBySelector("#diagnosticsCard .diag-item:nth-child(5) span", trWeb("uiDiagApi"));

  setTextBySelector('label[for="prefixKey"]', trWeb("uiPrefixKey"));
  setTextBySelector('label[for="prefixType"]', trWeb("uiLabelType"));
  setTextBySelector('label[for="prefixMake"]', trWeb("uiLabelMake"));
  setTextBySelector('label[for="prefixModel"]', trWeb("uiLabelModel"));
  setTextBySelector('label[for="prefixPriority"]', trWeb("uiPrefixPriority"));
  setTextBySelector('label[for="prefixActive"]', trWeb("uiPrefixActive"));

  setTextBySelector("#footerHosted", trWeb("uiFooterHosted"));

  const printerStatusText = String(els.printerStatus?.textContent || "").trim().toLowerCase();
  if (els.printerStatus && (!printerStatusText || printerStatusText.includes("not connected") || printerStatusText.includes("nav pieslēgts"))) {
    els.printerStatus.textContent = trWeb("uiPrinterNotConnected");
  }

  applyWebTheme(WEB_THEME);

  if (els.scanPopupTitle) {
    els.scanPopupTitle.textContent = trWeb("scanPopupTitle");
  }
  if (els.scanPopupRegister) {
    els.scanPopupRegister.textContent = trWeb("scanPopupRegister");
  }
  if (els.scanPopupClose) {
    els.scanPopupClose.textContent = trWeb("scanPopupClose");
  }
  if (els.qrScanTitle) {
    els.qrScanTitle.textContent = trWeb("scanQrTitle");
  }
  if (els.qrScanMessage) {
    els.qrScanMessage.textContent = trWeb("scanQrStarting");
  }
  if (els.qrScanClose) {
    els.qrScanClose.textContent = trWeb("scanPopupClose");
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

function applyWebTheme(theme) {
  WEB_THEME = theme === "dark" ? "dark" : "light";
  document.body.classList.toggle("theme-dark", WEB_THEME === "dark");
  try {
    localStorage.setItem(WEB_THEME_STORAGE_KEY, WEB_THEME);
  } catch {
    // ignore storage errors
  }

  if (els.themeToggle) {
    els.themeToggle.textContent = WEB_THEME === "dark" ? trWeb("uiThemeLight") : trWeb("uiThemeDark");
  }
}

function toggleWebTheme() {
  applyWebTheme(WEB_THEME === "dark" ? "light" : "dark");
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
      <div class="prefix-row" data-prefix-id="${escapeHtml(row.id)}">
        <span>${escapeHtml(row.prefix_key || "")}</span>
        <span>${escapeHtml(row.device_type || "")}</span>
        <span>${escapeHtml(row.make || "")}</span>
        <span>${escapeHtml(row.model || "")}</span>
        <span>${escapeHtml(row.priority ?? "")}</span>
        <span>${escapeHtml(row.active === false ? "no" : "yes")}</span>
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
    els.authInfo.textContent = `${trWeb("uiRolePrefix")}: ${authContext?.role || "anon"} (${adminText}, ${mode})`;
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
    els.diagApi.textContent = navigator.onLine ? SUPABASE_URL : trWeb("uiDiagApiOffline");
    els.diagApi.style.color = navigator.onLine ? "#0a7a2f" : "#b00020";
  }

  const isHealthy = navigator.onLine && queued === 0;
  const health = !navigator.onLine
    ? trWeb("uiHealthOfflineNoInternet")
    : queued > 0
      ? trWeb("uiHealthQueuePending")
      : trWeb("uiHealthHealthy");
  els.diagStatus.textContent = `${trWeb("uiHealthPrefix")}: ${health}`;
  els.diagStatus.style.color = isHealthy ? "#0a7a2f" : "#b00020";
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

function safeDecodeComponent(value) {
  try {
    return decodeURIComponent(String(value || "").replace(/\+/g, "%20"));
  } catch {
    return String(value || "");
  }
}

function addTokenCandidate(candidates, value) {
  const cleaned = cleanToken(value);
  if (cleaned) {
    candidates.add(cleaned);
  }
}

function collectJsonTokenCandidates(node, candidates) {
  if (node == null) return;

  if (Array.isArray(node)) {
    node.forEach((item) => collectJsonTokenCandidates(item, candidates));
    return;
  }

  if (typeof node !== "object") {
    addTokenCandidate(candidates, node);
    return;
  }

  const preferredKeyRe = /^(SERIAL|SERIALNUMBER|SERIAL_NUMBER|SN|SNR|ASSET|ASSETTAG|ASSET_TAG|DEVICEID|DEVICE_ID|ID|CODE)$/;

  Object.entries(node).forEach(([key, value]) => {
    const normalizedKey = String(key || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
    if (preferredKeyRe.test(normalizedKey)) {
      addTokenCandidate(candidates, value);
    }
    if (typeof value === "object") {
      collectJsonTokenCandidates(value, candidates);
    }
  });
}

function tokenizeScan(rawValue) {
  const raw = String(rawValue || "");
  const upper = raw.toUpperCase();
  const candidates = new Set();

  upper
    .split(/[\s,;|+]+/)
    .forEach((part) => addTokenCandidate(candidates, part));

  const keyValueRe = /\b(?:SERIAL|SN|SNR|ASSET(?:_?TAG)?|DEVICE(?:_?ID)?|DEV(?:_?ID)?|ID|CODE)\s*[:=]\s*([A-Z0-9\-_/]+)/gi;
  let match;
  while ((match = keyValueRe.exec(upper)) !== null) {
    addTokenCandidate(candidates, match[1]);
  }

  const queryRe = /(?:[?&]|^)(?:SERIAL|SN|SNR|ASSET(?:_?TAG)?|DEVICE(?:_?ID)?|DEV(?:_?ID)?|ID|CODE)=([^&#]+)/gi;
  while ((match = queryRe.exec(raw)) !== null) {
    addTokenCandidate(candidates, safeDecodeComponent(match[1]));
  }

  const gs1Match = upper.match(/\(21\)\s*([A-Z0-9\-]{4,30})/);
  if (gs1Match) {
    addTokenCandidate(candidates, gs1Match[1]);
  }

  const trimmed = raw.trim();
  if ((trimmed.startsWith("{") && trimmed.endsWith("}")) || (trimmed.startsWith("[") && trimmed.endsWith("]"))) {
    try {
      const parsed = JSON.parse(trimmed);
      collectJsonTokenCandidates(parsed, candidates);
    } catch {
      // Keep best-effort tokenization when payload is not valid JSON.
    }
  }

  const genericRuns = upper.match(/[A-Z0-9]{8,24}/g) || [];
  genericRuns.forEach((part) => addTokenCandidate(candidates, part));

  return Array.from(candidates);
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

function scoreSerialCandidate(token, mode, hasStructuredPayload) {
  if (!token) return -1;

  let score = -1;
  if (isScannerToken(token)) {
    score = 120;
  } else if (isPlainScannerToken(token)) {
    score = 110;
  } else if (isGenericToken(token)) {
    score = 75;
  } else {
    return -1;
  }

  if (mode === "laptop" || mode === "other") {
    score += 10;
  }
  if (hasStructuredPayload) {
    score += 5;
  }
  if (/^\d+$/.test(token)) {
    score += 4;
  }
  if (token.length >= 13 && token.length <= 16) {
    score += 6;
  }
  if (/^S\d{13,14}$/.test(token)) {
    score += 8;
  }

  return score;
}

function extractPreferredSerial(rawValue, options = {}) {
  const source = String(rawValue || "");
  const tokens = tokenizeScan(source);
  if (!tokens.length) return null;

  const hasPlusPayload = /\+/.test(source);
  const mode = String(options.mode || els.type?.value || "scanner").toLowerCase();
  const allowGenericSingle = options.allowGenericSingle === true;
  const hasStructuredPayload = /[,;|+=?&:\/{}\[\]()]/.test(source);

  // Some tablet QR payloads are "part+SERIAL+part"; serial is the middle token.
  if (hasPlusPayload && tokens.length >= 2) {
    const middleToken = tokens[Math.floor(tokens.length / 2)] || "";
    if (isGenericToken(middleToken)) return middleToken;

    const secondToken = tokens[1] || "";
    if (isGenericToken(secondToken)) return secondToken;
  }

  const ranked = tokens
    .map((token) => ({
      token,
      score: scoreSerialCandidate(token, mode, hasStructuredPayload),
    }))
    .filter((entry) => entry.score >= 0)
    .sort((a, b) => b.score - a.score);

  if (ranked.length) {
    const best = ranked[0].token;
    if (isScannerToken(best) || isPlainScannerToken(best)) return best;
    if ((mode === "laptop" || mode === "other" || allowGenericSingle || hasStructuredPayload || tokens.length === 1) && isGenericToken(best)) {
      return best;
    }
  }

  if (tokens.length === 1 && allowGenericSingle && isGenericToken(tokens[0])) return tokens[0];
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

function parseIsoDateOnly(value) {
  const raw = String(value || "").trim();
  if (!raw) return null;
  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) return null;
  return new Date(Date.UTC(parsed.getUTCFullYear(), parsed.getUTCMonth(), parsed.getUTCDate()));
}

function addMonthsUtc(baseDate, months) {
  if (!(baseDate instanceof Date) || Number.isNaN(baseDate.getTime())) {
    return null;
  }
  if (!Number.isFinite(months) || months <= 0) {
    return new Date(baseDate.getTime());
  }

  const year = baseDate.getUTCFullYear();
  const month = baseDate.getUTCMonth();
  const day = baseDate.getUTCDate();

  const firstDayTarget = new Date(Date.UTC(year, month + months, 1));
  const lastDayTarget = new Date(Date.UTC(firstDayTarget.getUTCFullYear(), firstDayTarget.getUTCMonth() + 1, 0));
  const safeDay = Math.min(day, lastDayTarget.getUTCDate());

  return new Date(Date.UTC(firstDayTarget.getUTCFullYear(), firstDayTarget.getUTCMonth(), safeDay));
}

function warrantyMonthsForSerial(token, deviceType) {
  const normalized = cleanToken(token);
  if (!normalized) {
    const fallback = WARRANTY_MONTHS_BY_TYPE[String(deviceType || "other").toLowerCase()] || WARRANTY_MONTHS_BY_TYPE.other;
    return { months: fallback, source: `device-type:${String(deviceType || "other").toLowerCase()}` };
  }

  const candidates = [normalized];
  if (isScannerToken(normalized)) {
    candidates.push(normalized.slice(1));
  }

  for (const prefix of WARRANTY_PREFIX_KEYS_DESC) {
    if (candidates.some((candidate) => candidate.startsWith(prefix))) {
      return { months: WARRANTY_MONTHS_BY_PREFIX[prefix], source: `serial-prefix:${prefix}` };
    }
  }

  const fallbackType = String(deviceType || "other").toLowerCase();
  const fallback = WARRANTY_MONTHS_BY_TYPE[fallbackType] || WARRANTY_MONTHS_BY_TYPE.other;
  return { months: fallback, source: `device-type:${fallbackType}` };
}

function splitCommentAndWarrantySegment(comment) {
  const text = String(comment || "").trim();
  if (!text) return { base: "", warranty: "" };

  const idx = text.toUpperCase().indexOf(WARRANTY_MARKER);
  if (idx < 0) {
    return { base: text, warranty: "" };
  }

  const base = text.slice(0, idx).replace(/[\s|]+$/g, "").trim();
  const warranty = text.slice(idx).trim();
  return { base, warranty };
}

function normalizeMakeForPublicApi(make) {
  return String(make || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function getWarrantyPublicApiProvider(make) {
  const normalized = normalizeMakeForPublicApi(make);
  if (!normalized) return null;

  if (WARRANTY_PUBLIC_API_BY_MAKE[normalized]) {
    return { key: normalized, ...WARRANTY_PUBLIC_API_BY_MAKE[normalized] };
  }

  const firstWord = normalized.split(" ")[0];
  const provider = WARRANTY_PUBLIC_API_BY_MAKE[firstWord];
  return provider ? { key: firstWord, ...provider } : null;
}

function readWarrantyApiField(payload, fieldSpec) {
  if (!payload || !fieldSpec) return undefined;

  const paths = Array.isArray(fieldSpec) ? fieldSpec : [fieldSpec];
  for (const path of paths) {
    const parts = String(path || "")
      .split(".")
      .map((x) => x.trim())
      .filter(Boolean);
    if (!parts.length) continue;

    let value = payload;
    let ok = true;
    for (const part of parts) {
      if (value && typeof value === "object" && part in value) {
        value = value[part];
      } else {
        ok = false;
        break;
      }
    }
    if (ok) return value;
  }
  return undefined;
}

function buildWarrantyPublicApiQueryUrl(make, serial) {
  const provider = getWarrantyPublicApiProvider(make);
  const endpoint = String(provider?.endpoint || "").trim();
  if (!endpoint) return "";

  const cleaned = cleanToken(serial);
  const serialParam = String(provider?.serialParam || "serial").trim() || "serial";
  if (!cleaned) return endpoint;

  try {
    const url = new URL(endpoint);
    if (!url.searchParams.has(serialParam)) {
      url.searchParams.set(serialParam, cleaned);
    }
    return url.toString();
  } catch {
    return endpoint;
  }
}

function warrantyCheckerUrlForMake(make) {
  const normalized = normalizeMakeForPublicApi(make);
  if (!normalized) return "";

  if (WARRANTY_CHECKER_URL_BY_MAKE[normalized]) {
    return WARRANTY_CHECKER_URL_BY_MAKE[normalized];
  }

  const firstWord = normalized.split(" ")[0];
  return WARRANTY_CHECKER_URL_BY_MAKE[firstWord] || "";
}

function warrantyCheckerSerialParamForMake(make) {
  const normalized = normalizeMakeForPublicApi(make);
  if (!normalized) return "";

  if (WARRANTY_CHECKER_SERIAL_PARAM_BY_MAKE[normalized]) {
    return WARRANTY_CHECKER_SERIAL_PARAM_BY_MAKE[normalized];
  }

  const firstWord = normalized.split(" ")[0];
  return WARRANTY_CHECKER_SERIAL_PARAM_BY_MAKE[firstWord] || "";
}

function buildWarrantyCheckerAutomationUrl(make, serial) {
  const baseUrl = warrantyCheckerUrlForMake(make);
  if (!baseUrl) return "";

  const cleaned = cleanToken(serial);
  if (!cleaned) return baseUrl;

  const serialParam = warrantyCheckerSerialParamForMake(make);
  if (!serialParam) return baseUrl;

  try {
    const url = new URL(baseUrl);
    if (!url.searchParams.has(serialParam)) {
      url.searchParams.set(serialParam, cleaned);
    }
    return url.toString();
  } catch {
    return baseUrl;
  }
}

function openWarrantyCheckerUrl(url) {
  const target = String(url || "").trim();
  if (!target) return false;

  let parsed;
  try {
    parsed = new URL(target);
  } catch {
    return false;
  }

  if (!/^https?:$/i.test(parsed.protocol)) {
    return false;
  }

  // Detect if running inside Android WebView
  const isWebView = window.navigator.userAgent.toLowerCase().includes('wv') || (window.external && window.external.notify) || window.android;

  if (isWebView) {
    try {
      window.location.assign(parsed.toString());
      return true;
    } catch {
      return false;
    }
  } else {
    try {
      const popup = window.open(parsed.toString(), "_blank", "noopener,noreferrer");
      if (popup) {
        try {
          popup.opener = null;
        } catch {
          // ignore opener assignment failures
        }
        return true;
      }
    } catch {
      // ignore and try same-tab fallback
    }

    try {
      window.location.assign(parsed.toString());
      return true;
    } catch {
      return false;
    }
  }
}

function getWarrantyApiCacheKey(make, serial) {
  const normalizedMake = normalizeMakeForPublicApi(make);
  const cleaned = cleanToken(serial);
  return `${normalizedMake}::${cleaned}`;
}

function boolFromApi(value) {
  if (value === true) return true;
  if (value === false) return false;
  const text = String(value || "").trim().toLowerCase();
  return text === "true" || text === "1" || text === "yes" || text === "verified" || text === "active";
}

function normalizeWarrantyApiDate(value) {
  const parsed = parseIsoDateOnly(value);
  return parsed ? parsed.toISOString().slice(0, 10) : "";
}

function normalizeWarrantyApiStatus(value) {
  const text = String(value || "")
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9 _-]/g, "")
    .replace(/\s+/g, " ");
  return text || "VERIFIED";
}

function buildVerifiedWarrantySegmentFromApi(make, serial, result) {
  const cleaned = cleanToken(serial);
  const resolvedMake = String(make || "").trim() || "manufacturer";
  const status = normalizeWarrantyApiStatus(result?.status);
  const endDate = normalizeWarrantyApiDate(result?.warrantyEndDate);
  const sourceUrl = String(result?.sourceUrl || result?.queryUrl || "").trim();
  const endText = endDate ? ` until ${endDate}` : "";
  const sourceText = sourceUrl ? ` ${sourceUrl}` : "";
  return `${WARRANTY_MARKER} VERIFIED via PUBLIC API (${resolvedMake}) ${status}${endText} (serial ${cleaned})${sourceText}`;
}

async function fetchWarrantyFromPublicApi(make, serial) {
  const provider = getWarrantyPublicApiProvider(make);
  const queryUrl = buildWarrantyPublicApiQueryUrl(make, serial);

  if (!provider || !queryUrl) {
    return { ok: false, reason: "api_not_configured", queryUrl: "" };
  }

  const cacheKey = getWarrantyApiCacheKey(make, serial);
  const cached = warrantyApiResultByKey.get(cacheKey);
  if (cached && Date.now() - cached.checkedAt < WARRANTY_PUBLIC_API_CACHE_TTL_MS) {
    return cached.result;
  }

  const headers = { Accept: "application/json" };
  const timeoutMs = Number(provider.timeoutMs || WARRANTY_PUBLIC_API_TIMEOUT_MS) || WARRANTY_PUBLIC_API_TIMEOUT_MS;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  let result;
  try {
    const response = await fetch(queryUrl, {
      method: String(provider.method || "GET").toUpperCase(),
      headers,
      signal: controller.signal,
    });

    if (!response.ok) {
      result = {
        ok: false,
        reason: `http_${response.status}`,
        queryUrl,
      };
    } else {
      const payload = await response.json();
      const verifiedRaw = readWarrantyApiField(payload, provider.verifiedField || ["verified", "data.verified", "warranty.verified"]);
      const statusRaw = readWarrantyApiField(payload, provider.statusField || ["status", "data.status", "warranty.status"]);
      const endDateRaw = readWarrantyApiField(payload, provider.endDateField || ["warrantyEndDate", "data.warrantyEndDate", "warranty.endDate"]);
      const sourceRaw = readWarrantyApiField(payload, provider.sourceField || ["sourceUrl", "data.sourceUrl", "meta.sourceUrl"]);

      if (boolFromApi(verifiedRaw)) {
        result = {
          ok: true,
          status: statusRaw,
          warrantyEndDate: endDateRaw,
          sourceUrl: String(sourceRaw || queryUrl || ""),
          queryUrl,
        };
      } else {
        result = {
          ok: false,
          reason: "not_found",
          queryUrl,
        };
      }
    }
  } catch (error) {
    const text = String(error?.name || error?.message || "error").toLowerCase();
    result = {
      ok: false,
      reason: text.includes("abort") ? "timeout" : "request_error",
      queryUrl,
    };
  } finally {
    clearTimeout(timer);
  }

  warrantyApiResultByKey.set(cacheKey, {
    checkedAt: Date.now(),
    result,
  });
  return result;
}

async function resolveVerifiedWarrantySegmentForPersist({ serial, make } = {}) {
  if (!WARRANTY_STRICT_MODE || !WARRANTY_PUBLIC_API_ONLY) return "";

  const cleaned = cleanToken(serial);
  const resolvedMake = String(make || "").trim();
  if (!cleaned || !resolvedMake) return "";

  const result = await fetchWarrantyFromPublicApi(resolvedMake, cleaned);
  if (!result.ok) return "";

  return buildVerifiedWarrantySegmentFromApi(resolvedMake, cleaned, result);
}

function isVerifiedWarrantySegment(segment) {
  return /\[WARRANTY\]\s+VERIFIED\b/i.test(String(segment || ""));
}

function buildWarrantyMarkerFromContext({ serial, deviceType, createdAt, make }) {
  const cleaned = cleanToken(serial);
  if (!cleaned) return "";

  if (WARRANTY_STRICT_MODE) {
    const resolvedMake = String(make || "").trim() || "manufacturer";
    const queryUrl = buildWarrantyPublicApiQueryUrl(resolvedMake, cleaned);
    if (queryUrl) {
      return `${WARRANTY_MARKER} PUBLIC-API AUTO-CHECK: couldn't find it for ${resolvedMake} (serial ${cleaned}) ${queryUrl}`;
    }
    const checkerUrl = buildWarrantyCheckerAutomationUrl(resolvedMake, cleaned);
    if (checkerUrl) {
      return `${WARRANTY_MARKER} WEBVIEW-CHECK: public API is not configured for ${resolvedMake}; open checker for serial ${cleaned}: ${checkerUrl}`;
    }
    return `${WARRANTY_MARKER} PUBLIC-API AUTO-CHECK: couldn't find it for ${resolvedMake} (serial ${cleaned}); public API is not configured`;
  }

  const { months, source } = warrantyMonthsForSerial(cleaned, deviceType);
  if (!months || months <= 0) return "";

  const startDate = parseIsoDateOnly(createdAt) || parseIsoDateOnly(new Date().toISOString());
  const endDate = addMonthsUtc(startDate, months);
  if (!endDate) return "";

  const today = parseIsoDateOnly(new Date().toISOString());
  const status = today && today.getTime() <= endDate.getTime() ? "ACTIVE" : "EXPIRED";
  const endText = endDate.toISOString().slice(0, 10);
  return `${WARRANTY_MARKER} ${status} until ${endText} (${months}m; ${source})`;
}

function prepareCommentForPersist(
  rawComment,
  { serial, deviceType, createdAt, make, allowAdminOverride = false, existingWarrantySegment = "" } = {}
) {
  const text = String(rawComment || "").trim();
  if (allowAdminOverride && !WARRANTY_PUBLIC_API_ONLY) {
    return text;
  }

  const { base } = splitCommentAndWarrantySegment(text);
  const trustedWarranty = isVerifiedWarrantySegment(existingWarrantySegment) ? String(existingWarrantySegment).trim() : "";
  if (trustedWarranty) {
    return base ? `${base} | ${trustedWarranty}` : trustedWarranty;
  }

  const marker = buildWarrantyMarkerFromContext({ serial, deviceType, createdAt, make });
  if (!marker) return base;
  return base ? `${base} | ${marker}` : marker;
}

function commentWithWarrantyPreview(comment, { serial, deviceType, createdAt, make, existingWarrantySegment = "" } = {}) {
  return prepareCommentForPersist(comment, {
    serial,
    deviceType,
    createdAt,
    make,
    existingWarrantySegment,
    allowAdminOverride: false,
  });
}

function rememberCreatedAtForToken(token, createdAt) {
  const value = String(createdAt || "").trim();
  if (!value) return;
  for (const variant of serialVariants(token)) {
    loadedCreatedAtBySerial.set(variant, value);
  }
}

function getKnownCreatedAtForToken(token) {
  for (const variant of serialVariants(token)) {
    const createdAt = loadedCreatedAtBySerial.get(variant);
    if (createdAt) return createdAt;
  }
  return "";
}

function rememberWarrantySegmentForToken(token, segment) {
  const value = String(segment || "").trim();
  if (!isVerifiedWarrantySegment(value)) {
    return;
  }
  for (const variant of serialVariants(token)) {
    loadedWarrantyBySerial.set(variant, value);
  }
}

function getKnownWarrantySegmentForToken(token) {
  for (const variant of serialVariants(token)) {
    const segment = loadedWarrantyBySerial.get(variant);
    if (segment) return segment;
  }
  return "";
}

function resolveCreatedAtForSave(cleanedToken, existingDevice = null) {
  const direct = String(existingDevice?.created_at || "").trim();
  if (direct) return direct;
  return getKnownCreatedAtForToken(cleanedToken);
}

function refreshWarrantyCommentPreview({ serial, deviceType, createdAt } = {}) {
  if (authContext?.isAdmin) return;
  const cleaned = cleanToken(serial || els.serial.value || "");
  if (!cleaned) return;

  const resolvedType = String(deviceType || els.type.value || "scanner").trim().toLowerCase() || "scanner";
  const resolvedMake = String(els.make.value || "").trim();
  const resolvedCreatedAt =
    createdAt !== undefined ? String(createdAt || "").trim() : resolveCreatedAtForSave(cleaned, null);
  const existingWarrantySegment = getKnownWarrantySegmentForToken(cleaned);

  els.comment.value = commentWithWarrantyPreview(els.comment.value, {
    serial: cleaned,
    deviceType: resolvedType,
    createdAt: resolvedCreatedAt,
    make: resolvedMake,
    existingWarrantySegment,
  });
  saveDraft();
}

function sanitizeSerialField(value) {
  const raw = String(value || "").toUpperCase();
  if (!raw) return "";

  // Keep common payload separators for URL/JSON/key-value scan formats.
  return raw.replace(/[^A-Z0-9,;|+\s:\/?&=%._\-{}\[\]()"']/g, "").slice(0, 220);
}

function sanitizeLookupField(value) {
  const raw = String(value || "").toUpperCase();
  if (!raw) return "";

  // Same behavior for lookup/paste workflows.
  return raw.replace(/[^A-Z0-9,;|+\s:\/?&=%._\-{}\[\]()"']/g, "").slice(0, 220);
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

function buildSaveOperation(cleanedToken, options = {}) {
  const expected = getKnownRevisionForToken(cleanedToken);
  const resolvedType = String(options.deviceType || els.type.value || "scanner").trim() || "scanner";
  const resolvedModel = String(options.model || composeModel(els.make.value, els.model.value)).trim();
  const modelMake = splitModel(resolvedModel)[0] || "";
  const resolvedMake = String(options.make || els.make.value || modelMake).trim();
  const resolvedCreatedAt = resolveCreatedAtForSave(cleanedToken, options.existingDevice || null);
  const resolvedExistingWarranty = String(
    options.existingWarrantySegment || getKnownWarrantySegmentForToken(cleanedToken) || ""
  ).trim();
  const comment = prepareCommentForPersist(els.comment.value, {
    serial: cleanedToken,
    deviceType: resolvedType,
    createdAt: resolvedCreatedAt,
    make: resolvedMake,
    existingWarrantySegment: resolvedExistingWarranty,
    allowAdminOverride: Boolean(authContext?.isAdmin),
  });

  return {
    serial: normalizeForStore(cleanedToken),
    device_type: resolvedType,
    model: resolvedModel,
    make: resolvedMake,
    from_store: els.fromStore.value.trim(),
    to_store: els.toStore.value.trim(),
    status: els.statusSelect.value,
    comment,
    created_at: resolvedCreatedAt || null,
    existing_warranty: resolvedExistingWarranty || "",
    allow_admin_override: Boolean(authContext?.isAdmin),
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
  refreshWarrantyCommentPreview();
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
  const preview = commentWithWarrantyPreview(device.comment || "", {
    serial: device.serial || els.serial.value || "",
    deviceType: device.device_type || "scanner",
    createdAt: device.created_at || "",
    make,
    existingWarrantySegment: splitCommentAndWarrantySegment(device.comment || "").warranty || "",
  });
  els.comment.value = authContext?.isAdmin ? String(device.comment || "") : preview;
  rememberCreatedAtForToken(device.serial || "", device.created_at || "");
  rememberWarrantySegmentForToken(device.serial || "", splitCommentAndWarrantySegment(device.comment || "").warranty || "");
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
  refreshWarrantyCommentPreview({ serial: els.serial.value, deviceType: guess.device_type || "scanner", createdAt: "" });
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

  let response;
  try {
    response = await fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
      method,
      headers,
      body: body === null ? undefined : JSON.stringify(body),
    });
  } catch (error) {
    const text = String((error && error.message) || error || "");
    if (!navigator.onLine || /failed to fetch|network|internet/i.test(text)) {
      throw new Error(trWeb("msgNoInternet"));
    }
    throw error;
  }

  const text = await response.text();
  let json = null;
  if (text) {
    try {
      json = JSON.parse(text);
    } catch {
      json = null;
    }
  }
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
        const serialForComment = String(op.serial || existing?.serial || "").trim();
        const deviceTypeForComment = String(op.device_type || existing?.device_type || "scanner").trim() || "scanner";
        const createdAtForComment = String(op.created_at || existing?.created_at || getKnownCreatedAtForToken(serialForComment) || "").trim();
        const modelForComment = String(op.model || existing?.model || "").trim();
        const makeForComment = String(op.make || splitModel(modelForComment)[0] || "").trim();
        const apiVerifiedWarrantySegment = await resolveVerifiedWarrantySegmentForPersist({
          serial: serialForComment,
          make: makeForComment,
        });
        const existingWarrantySegment = String(
          apiVerifiedWarrantySegment ||
          splitCommentAndWarrantySegment(existing?.comment || "").warranty ||
            op.existing_warranty ||
            getKnownWarrantySegmentForToken(serialForComment) ||
            ""
        ).trim();
        const commentForPersist = prepareCommentForPersist(op.comment, {
          serial: serialForComment,
          deviceType: deviceTypeForComment,
          createdAt: createdAtForComment,
          make: makeForComment,
          existingWarrantySegment,
          allowAdminOverride: Boolean(op.allow_admin_override),
        });
        const editPayload = {
          from_store: op.from_store || "",
          to_store: op.to_store || "",
          status: op.status || "RECEIVED",
          comment: commentForPersist || "",
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
          rememberCreatedAtForToken(op.serial || "", existing.created_at || createdAtForComment || rows?.[0]?.created_at || "");
          rememberWarrantySegmentForToken(
            op.serial || "",
            splitCommentAndWarrantySegment(rows?.[0]?.comment || existing?.comment || commentForPersist || "").warranty || ""
          );
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
          if (Array.isArray(rows) && rows[0]?.created_at) {
            rememberCreatedAtForToken(op.serial || "", rows[0].created_at);
          }
          if (Array.isArray(rows) && rows[0]?.comment) {
            rememberWarrantySegmentForToken(
              op.serial || "",
              splitCommentAndWarrantySegment(rows[0].comment || "").warranty || ""
            );
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

async function loadByScannedValue(rawValue, options = {}) {
  const token = extractPreferredSerial(rawValue, {
    allowGenericSingle: options.allowGenericSingle === true,
  });
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
    if (isConnectivityError(error)) {
      setStatus(trWeb("msgNoInternet"), "error");
      updateDiagnosticsPanel();
      return;
    }
    setStatus(`Database error: ${error.message}`, "error");
    return;
  }

  if (device) {
    rememberRevisionForToken(cleaned, device.updated_at || "");
    if (device.serial) {
      rememberRevisionForToken(device.serial, device.updated_at || "");
      rememberCreatedAtForToken(device.serial, device.created_at || "");
      rememberWarrantySegmentForToken(device.serial, splitCommentAndWarrantySegment(device.comment || "").warranty || "");
    }
    rememberCreatedAtForToken(cleaned, device.created_at || "");
    rememberWarrantySegmentForToken(cleaned, splitCommentAndWarrantySegment(device.comment || "").warranty || "");
    fillFormFromDevice(device);
    setStatus(trWeb("scanFoundDbStatus"), "ok");
    showScanPopup(trWeb("scanFoundDbPopup"));
    return;
  }

  await loadPrefixRules();

  for (const variant of serialVariants(cleaned)) {
    loadedRevisionBySerial.delete(variant);
    loadedCreatedAtBySerial.delete(variant);
    loadedWarrantyBySerial.delete(variant);
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
  const firstMake = String(els.make.value || "").trim();
  const apiVerifiedFromForm = await resolveVerifiedWarrantySegmentForPersist({
    serial: cleaned,
    make: firstMake,
  });
  let queuedOperation = buildSaveOperation(cleaned, {
    make: firstMake,
    model: composeModel(els.make.value, els.model.value),
    existingWarrantySegment: apiVerifiedFromForm || getKnownWarrantySegmentForToken(cleaned),
  });
  els.comment.value = queuedOperation.comment || "";
  saveDraft();

  let existing = null;
  try {
    existing = await getDeviceBySerial(cleaned);
    if (existing?.created_at) {
      rememberCreatedAtForToken(cleaned, existing.created_at);
      rememberCreatedAtForToken(existing.serial || cleaned, existing.created_at);
    }
    const existingWarrantySegment = splitCommentAndWarrantySegment(existing?.comment || "").warranty || "";
    if (existing?.serial) {
      rememberWarrantySegmentForToken(existing.serial, existingWarrantySegment);
    }
    rememberWarrantySegmentForToken(cleaned, existingWarrantySegment);
    const resolvedMakeForApi = String(els.make.value || splitModel(existing?.model || "")[0] || "").trim();
    const apiVerifiedFromLookup = await resolveVerifiedWarrantySegmentForPersist({
      serial: cleaned,
      make: resolvedMakeForApi,
    });
    queuedOperation = buildSaveOperation(cleaned, {
      existingDevice: existing,
      make: resolvedMakeForApi,
      model: composeModel(els.make.value, els.model.value) || String(existing?.model || "").trim(),
      existingWarrantySegment: apiVerifiedFromLookup || existingWarrantySegment,
    });
    els.comment.value = queuedOperation.comment || "";
    saveDraft();
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
    comment: queuedOperation.comment || "",
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
          if (Array.isArray(overwriteRows) && overwriteRows[0]?.created_at) {
            rememberCreatedAtForToken(cleaned, overwriteRows[0].created_at);
          }
          if (Array.isArray(overwriteRows) && overwriteRows[0]?.comment) {
            rememberWarrantySegmentForToken(
              cleaned,
              splitCommentAndWarrantySegment(overwriteRows[0].comment || "").warranty || ""
            );
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
        if (Array.isArray(rows) && rows[0]?.created_at) {
          rememberCreatedAtForToken(cleaned, rows[0].created_at);
        }
        if (Array.isArray(rows) && rows[0]?.comment) {
          rememberWarrantySegmentForToken(cleaned, splitCommentAndWarrantySegment(rows[0].comment || "").warranty || "");
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
      if (Array.isArray(rows) && rows[0]?.created_at) {
        rememberCreatedAtForToken(cleaned, rows[0].created_at);
      }
      if (Array.isArray(rows) && rows[0]?.comment) {
        rememberWarrantySegmentForToken(cleaned, splitCommentAndWarrantySegment(rows[0].comment || "").warranty || "");
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
  const allRows = getFilteredRows();
  const hasFilter = String(els.listFilter.value || "").trim().length > 0;

  const totalItems = allRows.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / itemsPerPage));
  if (currentPage > totalPages) currentPage = totalPages;
  if (currentPage < 1) currentPage = 1;

  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
  const rows = allRows.slice(startIndex, endIndex);

  els.listStatus.textContent = trWebFmt("msgShowing", { count: totalItems });
  if (els.paginationInfo) {
    els.paginationInfo.textContent = totalItems > 0 ? `${startIndex + 1}-${endIndex} / ${totalItems} showing, page ${currentPage}` : `0 / 0 showing, page 1`;
  }
  if (els.prevPage) els.prevPage.disabled = currentPage === 1;
  if (els.nextPage) els.nextPage.disabled = currentPage === totalPages || totalItems === 0;

  if (!rows.length) {
    const helper = hasFilter ? trWeb("msgNoRowsMatchFilter") : trWeb("msgCheckPolicy");
    els.devicesList.innerHTML = `
      <div class="row">
        <span>${trWeb("msgNoDevicesVisible")}</span>
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

  const checkerButtonLabel = escapeHtml(trWeb("uiOpenChecker"));

  els.devicesList.innerHTML = rows
    .map((row) => {
      const rowSerial = cleanToken(row.serial || "");
      const rowMake = splitModel(row.model || "")[0] || "";
      const checkerUrl = buildWarrantyCheckerAutomationUrl(rowMake, rowSerial);
      const checkerButton = checkerUrl
        ? `<button type="button" class="btn btn--small row__checker-btn js-open-checker" data-checker-url="${escapeHtml(
            checkerUrl
          )}">${checkerButtonLabel}</button>`
        : "";

      return `
      <div class="row" data-serial="${escapeHtml(row.serial || "")}">
        <span data-label="${escapeHtml(trWeb("uiTableSerial"))}">${escapeHtml(row.serial || "")}</span>
        <span data-label="${escapeHtml(trWeb("uiTableType"))}">${escapeHtml(row.device_type || "")}</span>
        <span data-label="${escapeHtml(trWeb("uiTableModel"))}">${escapeHtml(row.model || "")}</span>
        <span data-label="${escapeHtml(trWeb("uiTableStatus"))}">${escapeHtml(row.status || "")}</span>
        <span data-label="${escapeHtml(trWeb("uiTableFrom"))}">${escapeHtml(row.from_store || "")}</span>
        <span data-label="${escapeHtml(trWeb("uiTableTo"))}">${escapeHtml(row.to_store || "")}</span>
        <span data-label="${escapeHtml(trWeb("uiTableComment"))}"><span class="row__comment-text">${escapeHtml(
          row.comment || ""
        )}</span>${checkerButton}</span>
      </div>
    `
    })
    .join("");
}

async function loadDevicesList() {
  els.listStatus.textContent = trWeb("msgLoading");
  setSyncInfo(trWeb("msgLoading"));
  els.devicesList.innerHTML = `
    <div class="row">
      <span>${trWeb("msgLoadingDb")}</span>
      <span>-</span>
      <span>-</span>
      <span>-</span>
      <span>-</span>
      <span>-</span>
      <span>${trWeb("msgPleaseWait")}</span>
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
    if (isConnectivityError(error)) {
      const offlineMessage = trWeb("msgNoInternet");
      devicesCache = [];
      els.listStatus.textContent = `${trWeb("msgDatabaseError")}: ${offlineMessage}`;
      setSyncInfo("offline", "error");
      setStatus(offlineMessage, "error");
      els.devicesList.innerHTML = `
        <div class="row">
          <span>${trWeb("msgDatabaseError")}</span>
          <span>-</span>
          <span>-</span>
          <span>-</span>
          <span>-</span>
          <span>-</span>
          <span>${offlineMessage}</span>
        </div>
      `;
      updateDiagnosticsPanel();
      return;
    }
    devicesCache = [];
    els.listStatus.textContent = `${trWeb("msgDatabaseError")}: ${error.message}`;
    setSyncInfo(trWeb("msgDatabaseError"), "error");
    els.devicesList.innerHTML = `
      <div class="row">
        <span>${trWeb("msgDatabaseError")}</span>
        <span>-</span>
        <span>-</span>
        <span>-</span>
        <span>-</span>
        <span>-</span>
        <span>${escapeHtml(String(error.message || "Unknown error"))}</span>
      </div>
    `;
  }
}

function renderAuditRows(rows) {
  if (!els.auditList) return;
  if (!Array.isArray(rows) || !rows.length) {
    els.auditList.innerHTML = `
      <div class="audit-row">
        <span>${trWeb("msgNoAuditRows")}</span>
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
        <span>${escapeHtml(String(row.event_time || "").replace("T", " "))}</span>
        <span>${escapeHtml(row.operation || "")}</span>
        <span>${escapeHtml(row.serial || "")}</span>
        <span>${escapeHtml(row.actor || "")}</span>
      </div>
    `
    )
    .join("");
}

async function loadAuditLogs() {
  if (!els.auditList || !els.auditStatus) return;

  if (!authContext?.isAdmin) {
    renderAuditRows([]);
    els.auditStatus.textContent = trWeb("msgAdminOnly");
    return;
  }

  const serialFilter = cleanToken(els.auditSerial?.value || "");
  let path = "device_audit_log?select=id,event_time,operation,serial,actor,source,txid&order=event_time.desc&limit=120";
  if (serialFilter) {
    path += `&serial=ilike.${encodeURIComponent(`%${serialFilter}%`)}`;
  }

  els.auditStatus.textContent = trWeb("msgLoading");
  try {
    const rows = await restRequest(path);
    renderAuditRows(Array.isArray(rows) ? rows : []);
    els.auditStatus.textContent = trWebFmt("msgRowsCount", { count: Array.isArray(rows) ? rows.length : 0 });
  } catch (error) {
    renderAuditRows([]);
    els.auditStatus.textContent = trWeb("msgAdminRequired");
    setStatus(`Audit unavailable: ${error.message}`, "error");
  }
}

async function loadFromLookup() {
  const token = extractPreferredSerial(els.lookupSerial.value, { allowGenericSingle: true });
  if (!token) {
    setStatus(trWeb("msgEnterSerialFormat"), "error");
    return;
  }
  const cleaned = cleanToken(token);
  els.lookupSerial.value = cleaned;
  els.serial.value = cleaned;
  saveDraft();
  await loadByScannedValue(cleaned, { allowGenericSingle: true });
}

function clearDevicesListTools() {
  if (els.lookupSerial) {
    els.lookupSerial.value = "";
  }
  if (els.listFilter) {
    els.listFilter.value = "";
  }
  renderDevicesList();
  setStatus(trWeb("msgCleared"));
  if (els.listFilter) {
    els.listFilter.focus();
  }
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
  refreshWarrantyCommentPreview();
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
if (els.langSelect) {
  els.langSelect.addEventListener("change", () => {
    const nextLang = String(els.langSelect.value || "en").trim().toLowerCase() === "lv" ? "lv" : "en";
    try {
      localStorage.setItem(WEB_LANG_STORAGE_KEY, nextLang);
    } catch {
      // ignore storage errors
    }
    window.location.reload();
  });
}
if (els.themeToggle) {
  els.themeToggle.addEventListener("click", () => {
    toggleWebTheme();
  });
}
if (els.scanQr) {
  els.scanQr.addEventListener("click", startQrCameraScan);
}
if (els.printerConnect) {
  els.printerConnect.addEventListener("click", connectZq620Printer);
}
if (els.printSticker) {
  els.printSticker.addEventListener("click", printAssetSticker);
}
if (els.printerRefresh) {
  els.printerRefresh.addEventListener("click", () => {
    refreshPrinterCandidates();
  });
}
if (els.printerConnectSelected) {
  els.printerConnectSelected.addEventListener("click", connectSelectedPrinter);
}
if (els.printerPicker) {
  els.printerPicker.addEventListener("change", () => {
    refreshPrinterHealth({ silent: true });
  });
}
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
if (els.qrScanClose) {
  els.qrScanClose.addEventListener("click", () => hideQrScanPopup());
}
if (els.qrScanPopup) {
  els.qrScanPopup.addEventListener("click", (e) => {
    if (e.target === els.qrScanPopup) {
      hideQrScanPopup();
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
    hideQrScanPopup({ silent: true });
    resolveConflictPopup("cancel");
  }
});
window.addEventListener("beforeunload", () => {
  stopQrCameraScan();
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
  setStatus(trWeb("msgCleared"));
  els.serial.focus();
});
els.refreshList.addEventListener("click", loadDevicesList);

els.itemsPerPage.addEventListener("change", (e) => {
  itemsPerPage = parseInt(e.target.value, 10) || 10;
  currentPage = 1;
  renderDevicesList();
});

els.prevPage.addEventListener("click", () => {
  if (currentPage > 1) {
    currentPage--;
    renderDevicesList();
  }
});

els.nextPage.addEventListener("click", () => {
  currentPage++;
  renderDevicesList();
});

els.listFilter.addEventListener("input", () => {
  currentPage = 1;
  renderDevicesList();
});

if (els.listClear) {
  els.listClear.addEventListener("click", clearDevicesListTools);
}

els.devicesList.addEventListener("click", (e) => {
  const checkerButton = e.target.closest(".js-open-checker");
  if (checkerButton) {
    e.preventDefault();
    e.stopPropagation();

    const checkerUrl = String(checkerButton.getAttribute("data-checker-url") || "").trim();
    if (!checkerUrl) {
      setStatus(trWeb("msgWarrantyCheckerUnavailable"), "error");
      return;
    }

    const opened = openWarrantyCheckerUrl(checkerUrl);
    setStatus(trWeb(opened ? "msgWarrantyCheckerOpened" : "msgWarrantyCheckerOpenFailed"), opened ? "ok" : "error");
    return;
  }

  const row = e.target.closest(".row[data-serial]");
  if (!row) return;
  const cleaned = cleanToken(row.getAttribute("data-serial") || "");
  if (!cleaned) return;
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
refreshPrinterStatus();
refreshPrinterCandidates({ silent: true });
refreshPrinterHealth({ silent: true });
setSyncInfo(navigator.onLine ? "starting" : "offline", navigator.onLine ? "info" : "error");
updateDiagnosticsPanel();
const recoveredDraft = restoreDraft();
if (recoveredDraft) {
  setStatus(trWeb("msgRecoveredDraft"));
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
  refreshPrinterStatus();
  refreshPrinterCandidates({ silent: true });
  refreshPrinterHealth({ silent: true });
  loadPrefixRules();
  loadPrefixRulesAdmin();
  loadDevicesList();
  processQueuedSaves();
});
window.addEventListener("online", () => {
  setStatus(trWeb("msgBackOnlineSyncing"));
  setSyncInfo("back online", "ok");
  updateDiagnosticsPanel();
  processQueuedSaves();
});
window.addEventListener("offline", () => {
  setStatus(trWeb("msgNoInternet"), "error");
  setSyncInfo("offline", "error");
  updateDiagnosticsPanel();
});
setInterval(() => {
  if (document.visibilityState && document.visibilityState !== "visible") {
    return;
  }
  authContext = resolveAuthContext();
  applyAuthUiState();
  loadPrefixRules();
  loadPrefixRulesAdmin();
  loadDevicesList();
  processQueuedSaves();
}, 60000);
