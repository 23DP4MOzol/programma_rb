# Rimi Baltic Inventory System
[Latviešu](#latviešu) | [English](#english)

## Table of Contents
- [Latviešu](#latviešu)
  - [Ievads](#ievads)
  - [Atbalstītās iekārtas un ražotāji](#atbalstītās-iekārtas-un-ražotāji)
  - [Funkciju matrica](#funkciju-matrica)
  - [PC Web Aplikācija](#pc-web-aplikācija)
  - [Android WebView APK](#android-webview-apk)
  - [Supabase Backend](#supabase-backend)
- [English](#english)
  - [Introduction](#introduction)
  - [Supported Devices and Makes](#supported-devices-and-makes)
  - [Feature Matrix](#feature-matrix)
  - [PC Web App](#pc-web-app)
  - [Android WebView APK](#android-webview-apk)
  - [Supabase Backend](#supabase-backend)

---

## Latviešu

### Ievads
Vienota inventarizācijas sistēma Rimi Baltic infrastruktūras un IT tehnikas uzskaitei. Sistēma sastāv no pārlūkā bāzētas PC aplikācijas (hostētas caur GitHub Pages `docs` mapē) un specializētas Android WebView lietotnes mobilajiem skeneriem un planšetdatoriem, kas nodrošina papildu sistēmas līmeņa funkcijas.

### Atbalstītās iekārtas un ražotāji
Sistēmā ir integrētas sekojošas ierīču kategorijas un ražotāji. Automātiskā garantijas statusa pārbaude un ievietošana ar WebView darbojas lielākajai daļai no šiem ražotājiem:

- **Portatīvie datori (Laptops):** Apple, Asus, Dell, Lenovo, HP
- **Planšetdatori (Tablets):** Samsung, Apple, Lenovo, Zebra, Microsoft, Getac
- **Skeneri (Scanners):** Zebra, Datalogic, Apple, Asus, Dell (pievienots ātrai piekļuvei)
- **Telefoni un citas iekārtas (Phones, Printers, POS):** Samsung, Apple, Google, Nokia u.c. (vairs neatbalsta Acer un Motorola datorus/telefonus)

### Funkciju matrica

| Funkcija | PC Web pārlūks | Android APK |
| :--- | :---: | :---: |
| Datu ievade sistēmā (Supabase) | Jā | Jā |
| Automātiska garantijas lapas ielāde | Manuāli jānoklikšķina | Jā (JavaScript injekcija) |
| Automātiska sērijas numuru aizpilde garantijas lapās | Nē | Jā (Apple, Asus, Dell, HP, Lenovo, Samsung, Zebra) |
| Bluetooth drukāšana (Zebra ZQ620 / ZPL) | Nē | Jā |
| Iebūvēts kameras QR/svītrkodu skeneris | Nē | Jā |

### PC Web Aplikācija
Aplikācija pieejama jebkurā pārlūkā. Tā komunicē tieši ar Supabase API. Atbalsta datu filtrēšanu, ievadi, meklēšanu un labošanā. Sērijas numura formāta validācija notiek lokāli caur `app.js`, nodrošinot, ka katalogā tiek piemeklēts pareizais iekārtas modelis, kas pēc noklusējuma atrodas `WEB_DEVICE_CATALOG`.

### Android WebView APK
Lokālā Android (`MainActivity.java`) aplikācija ir kā ietvars ap Web aplikāciju ar papildu funkcionalitāti:

1. **JavaScript injekcija:** Pārejot uz ārējām ražotāju garantijas lapām (piem., `lenovo.com`, `dell.com`, `apple.com`), iekšējais pārlūka klients (`InventoryWebViewClient`) automātiski ievieto sērijas numuru, izmantojot lokālu JavaScript un Shadow DOM traversēšanu bez nepieciešamības lietotājam ievadīt to manuāli.  
2. **Bluetooth printeri (`AndroidPrinterBridge`):** Aplikācija var pieslēgties Zebra ZQ620 vai citiem RFCOMM-atbalstošiem printeriem, lai izprintētu marķējuma uzlīmes (ZPL) uzreiz no Web GUI. Tā atbalsta fona skenēšanu un statusa pārbaudi.  
3. **Kameras skenēšana:** Atbalsta vizuālo 1D/2D svītrkodu lasīšanu caur Android `ScanContract`.

### Supabase Backend
Supabase instances integrācija ļauj sinhronizēt visus fiziskos ierakstus. JWT atslēgas lokāli ir ierakstītas `app.js` savienojuma izveidei.

---

## English

### Introduction
Unified inventory system for Rimi Baltic infrastructure and IT equipment tracking. The system consists of a browser-based PC application (hosted via GitHub Pages in the `docs` folder) and a specialized Android WebView application for mobile scanners/tablets providing additional deep-system features.

### Supported Devices and Makes
The system integrates the following device categories and manufacturers. The automated warranty checker and WebView injection autofills the portals for most of these tech brands:

- **Laptops:** Apple, Asus, Dell, HP
- **Tablets:** Samsung, Apple, Zebra
- **Scanners:** Zebra, Datalogic, Apple, Asus, Dell (added into default UI flow for fast access)
- **Phones & Other:** Samsung, Apple, HP, Datalogic, Zebra

### Feature Matrix

| Feature | PC Web Browser | Android APK |
| :--- | :---: | :---: |
| Data entry to database (Supabase) | Yes | Yes |
| Automatic warranty page loading | Manual click required | Yes (JavaScript Injection) |
| Autofill serial numbers on warranty portals | No | Yes (Apple, Asus, Dell, HP, Lenovo, Samsung, Zebra) |
| Bluetooth printer integration (Zebra ZQ620 / ZPL) | No | Yes |
| Built-in camera barcode/QR scanner | No | Yes |

### PC Web App
Accessible from any modern browser. Communicates natively with the Supabase API. Handles data filtering, input, searching, and editing. Serial format logic and model assignments are contained in `app.js` under the `WEB_DEVICE_CATALOG`.

### Android WebView APK
The local Android container (`MainActivity.java`) acts as a wrapper with extended deep capabilities:

1. **JavaScript injections:** When navigating to external vendor portals (e.g., `lenovo.com`, `dell.com`, `apple.com`), the custom `InventoryWebViewClient` automatically intercepts the loading state and injects a script utilizing Shadow DOM traversal to autofill the serial number directly into the website's form.  
2. **Bluetooth printing (`AndroidPrinterBridge`):** Connects to Zebra ZQ620 printers over RFCOMM sockets, allowing immediate ZPL label printing triggered by the web frontend. Includes background discovery and connection checks.  
3. **Native camera scanning:** Enables seamless 1D/2D barcode input into the web interface.

### Supabase Backend
Integration with the Supabase instance provides real-time persistent data storage for technical assets. JWT and connection configuration are primarily loaded through `app.js`.