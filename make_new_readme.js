const fs = require('fs');
const readme = `# Rimi Baltic Inventory System
[Latvieðu](#latvieðu) | [English](#english)
## Table of Contents
- [Latvieðu](#latvieðu)
  - [Ievads](#ievads)
  - [Atbalstîtâs iekârtas un raþotâji](#atbalstîtâs-iekârtas-un-raþotâji)
  - [Funkciju matrica](#funkciju-matrica)
  - [PC Web Aplikâcija](#pc-web-aplikâcija)
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
## Latvieðu
### Ievads
Vienota inventarizâcijas sistçma Rimi Baltic infrastruktûras un IT tehnikas uzskaitei. Sistçma sastâv no pârlûkâ bâzçtas PC aplikâcijas (hostçtas caur GitHub Pages \`docs\` mapç) un specializçtas Android WebView lietotnes mobilajiem skeneriem un planðetdatoriem, kas nodroðina papildu sistçmas lîmeòa funkcijas.
### Atbalstîtâs iekârtas un raþotâji
Sistçmâ ir integrçtas sekojoðas ierîèu kategorijas un raþotâji. Automâtiskâ garantijas statusa pârbaude un ievietoðana ar WebView darbojas lielâkajai daïai no ðiem raþotâjiem:
- **Portatîvie Datori (Laptops):** Apple, Asus, Dell, Lenovo, HP
- **Planðetdatori (Tablets):** Samsung, Apple, Lenovo, Zebra, Microsoft, Getac
- **Skeneri (Scanners):** Zebra, Datalogic, Apple, Asus, Dell (Pievienots âtrai piekïuvei)
- **Telefoni un citas iekârtas (Phones, Printers, POS):** Samsung, Apple, Google, Nokia utt. (Vairs neatbalsta Acer un Motorola datorus/telefonus)
### Funkciju matrica
| Funkcija | PC Web Pârlûks | Android APK |
| :--- | :---: | :---: |
| Datu ievade sistçmâ (Supabase) | Jâ | Jâ |
| Automâtiska garantijas lapas ielâde | Manuâli jâklikðíina | Jâ (JavaScript injekcija) |
| Automâtiska sçrijas numuru aizpilde garantijas lapâs | Nç | Jâ (Apple, Asus, Dell, HP, Lenovo, Samsung, Zebra) |
| Bluetooth Drukâðana (Zebra ZQ620 / ZPL) | Nç | Jâ |
| Iebûvçts kameras QR/Svîtrkodu Skeneris | Nç | Jâ |
### PC Web Aplikâcija
Aplikâcija pieejama jebkurâ pârlûkâ. Tâ komunicç tieði ar Supabase API. Atbalsta datu filtrâciju, ievadi, meklçðanu un laboðanu. Sçrijas numura formâta validâcija notiek lokâli caur \`app.js\`, nodroðinot, ka katalogâ tiek piemçrots pareizas iekârtas modelis, kas pçc noklusçjuma atrodas \`WEB_DEVICE_CATALOG\`.
### Android WebView APK
Lokâlâ Android (\`MainActivity.java\`) aplikâcija ir kâ ietvars ap Web aplikâciju ar papildu funkcionalitâti:
1. **JavaScript Injekcija:** Pârejot uz ârçjâm raþotâju garantijas lapâm (piem., \`lenovo.com\`, \`dell.com\`, \`apple.com\`), iekðçjâs pârlûkprogrammas klients (\`InventoryWebViewClient\`) automâtiski ievieto sçrijas numuru, izmantojot lokâlu JavaScript un Shadow DOM traversçðanu bez nepiecieðamîbas lietotâjam ievadît to manuâli.
2. **Bluetooth Printeri (\`AndroidPrinterBridge\`):** Aplikâcija var pieslçgties Zebra ZQ620 vai citiem RFCOMM-atbalstoðiem printeriem, lai izprintçtu maríçjuma uzlîmes (ZPL) uzreiz no Web GUI. Tâ atbalsta fona skençðanu un statusa pârbaudi.
3. **Kameras skençðana:** Atbalsta vizuâlo 1D/2D svîtrkodu lasîðanu caur Android \`ScanContract\`.
### Supabase Backend
Rimi Baltic Supabase instances integrâcija ïauj sinhronizçt visus fiziskos ierakstus. JWT atslçgas lokâli ir ierakstîtas \`app.js\` savienojuma izveidei.
---
## English
### Introduction
Unified inventory system for Rimi Baltic infrastructure and IT equipment tracking. The system consists of a browser-based PC application (hosted via GitHub Pages in the \`docs\` folder) and a specialized Android WebView application for mobile scanners/tablets providing additional deep-system features.
### Supported Devices and Makes
The system integrates the following device categories and manufacturers. The automated warranty checker and WebView injection autofills the portals for most of these tech brands:
- **Laptops:** Apple, Asus, Dell, Lenovo, HP
- **Tablets:** Samsung, Apple, Lenovo, Zebra, Microsoft, Getac
- **Scanners:** Zebra, Datalogic, Apple, Asus, Dell (Added into default UI flow for fast access)
- **Phones & Other (Printers, POS):** Samsung, Apple, Google, Nokia, etc. (Acer and Motorola explicitly removed)
### Feature Matrix
| Feature | PC Web Browser | Android APK |
| :--- | :---: | :---: |
| Data entry to database (Supabase) | Yes | Yes |
| Automatic warranty page loading | Manual click required | Yes (JavaScript Injection) |
| Autofill serial numbers on warranty portals | No | Yes (Apple, Asus, Dell, HP, Lenovo, Samsung, Zebra) |
| Bluetooth Printer integration (Zebra ZQ620 / ZPL) | No | Yes |
| Built-in Camera Barcode/QR Scanner | No | Yes |
### PC Web App
Accessible from any modern browser. Communicates natively with the Supabase API. Handles data filtering, input, searching, and editing. Serial format logic and model assignments are contained in \`app.js\` under the \`WEB_DEVICE_CATALOG\`.
### Android WebView APK
The local Android container (\`MainActivity.java\`) acts as a wrapper with extended deep capabilities:
1. **JavaScript JS Injections:** When navigating to external vendor portals (e.g., \`lenovo.com\`, \`dell.com\`, \`apple.com\`), the custom \`InventoryWebViewClient\` automatically intercepts the WebResource loading state and injects a script utilizing deep Shadow DOM traversal to autofill the targeted serial number directly into the website's form.
2. **Bluetooth Printing (\`AndroidPrinterBridge\`):** Connects to Bluetooth Zebra ZQ620 printers over unsecured/secure RFCOMM sockets, allowing immediate label ZPL printing triggered by the web frontend. Includes background discovery routines and connection persistence checks.
3. **Native Camera Scanning:** Facilitated 1D/2D barcode reading seamlessly into the web input.
### Supabase Backend
Integration with the Rimi Baltic Supabase instance provides real-time persistent data storage for technical assets. JWT and URL connection strings are loaded primarily through \`app.js\`.
`
fs.writeFileSync('README.md', readme, 'utf8');
console.log('README fully rewritten to include completely up to date information!');
