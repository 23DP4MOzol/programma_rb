# Rimi Baltic Inventory System
[Latvie�u](#latvie�u) | [English](#english)
## Table of Contents
- [Latvie�u](#latvie�u)
  - [Ievads](#ievads)
  - [Atbalst�t�s iek�rtas un ra�ot�ji](#atbalst�t�s-iek�rtas-un-ra�ot�ji)
  - [Funkciju matrica](#funkciju-matrica)
  - [PC Web Aplik�cija](#pc-web-aplik�cija)
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
## Latvie�u
### Ievads
Vienota inventariz�cijas sist�ma Rimi Baltic infrastrukt�ras un IT tehnikas uzskaitei. Sist�ma sast�v no p�rl�k� b�z�tas PC aplik�cijas (host�tas caur GitHub Pages `docs` map�) un specializ�tas Android WebView lietotnes mobilajiem skeneriem un plan�etdatoriem, kas nodro�ina papildu sist�mas l�me�a funkcijas.
### Atbalst�t�s iek�rtas un ra�ot�ji
Sist�m� ir integr�tas sekojo�as ier��u kategorijas un ra�ot�ji. Autom�tisk� garantijas statusa p�rbaude un ievieto�ana ar WebView darbojas liel�kajai da�ai no �iem ra�ot�jiem:
- **Portat�vie Datori (Laptops):** Apple, Asus, Dell, Lenovo, HP
- **Plan�etdatori (Tablets):** Samsung, Apple, Lenovo, Zebra, Microsoft, Getac
- **Skeneri (Scanners):** Zebra, Datalogic, Apple, Asus, Dell (Pievienots �trai piek�uvei)
- **Telefoni un citas iek�rtas (Phones, Printers, POS):** Samsung, Apple, Google, Nokia utt. (Vairs neatbalsta Acer un Motorola datorus/telefonus)
### Funkciju matrica
| Funkcija | PC Web P�rl�ks | Android APK |
| :--- | :---: | :---: |
| Datu ievade sist�m� (Supabase) | J� | J� |
| Autom�tiska garantijas lapas iel�de | Manu�li j�klik��ina | J� (JavaScript injekcija) |
| Autom�tiska s�rijas numuru aizpilde garantijas lap�s | N� | J� (Apple, Asus, Dell, HP, Lenovo, Samsung, Zebra) |
| Bluetooth Druk��ana (Zebra ZQ620 / ZPL) | N� | J� |
| Ieb�v�ts kameras QR/Sv�trkodu Skeneris | N� | J� |
### PC Web Aplik�cija
Aplik�cija pieejama jebkur� p�rl�k�. T� komunic� tie�i ar Supabase API. Atbalsta datu filtr�ciju, ievadi, mekl��anu un labo�anu. S�rijas numura form�ta valid�cija notiek lok�li caur `app.js`, nodro�inot, ka katalog� tiek piem�rots pareizas iek�rtas modelis, kas p�c noklus�juma atrodas `WEB_DEVICE_CATALOG`.
### Android WebView APK
Lok�l� Android (`MainActivity.java`) aplik�cija ir k� ietvars ap Web aplik�ciju ar papildu funkcionalit�ti:
1. **JavaScript Injekcija:** P�rejot uz �r�j�m ra�ot�ju garantijas lap�m (piem., `lenovo.com`, `dell.com`, `apple.com`), iek��j�s p�rl�kprogrammas klients (`InventoryWebViewClient`) autom�tiski ievieto s�rijas numuru, izmantojot lok�lu JavaScript un Shadow DOM travers��anu bez nepiecie�am�bas lietot�jam ievad�t to manu�li.
2. **Bluetooth Printeri (`AndroidPrinterBridge`):** Aplik�cija var piesl�gties Zebra ZQ620 vai citiem RFCOMM-atbalsto�iem printeriem, lai izprint�tu mar��juma uzl�mes (ZPL) uzreiz no Web GUI. T� atbalsta fona sken��anu un statusa p�rbaudi.
3. **Kameras sken��ana:** Atbalsta vizu�lo 1D/2D sv�trkodu las��anu caur Android `ScanContract`.
### Supabase Backend
Rimi Baltic Supabase instances integr�cija �auj sinhroniz�t visus fiziskos ierakstus. JWT atsl�gas lok�li ir ierakst�tas `app.js` savienojuma izveidei.
---
## English
### Introduction
Unified inventory system for Rimi Baltic infrastructure and IT equipment tracking. The system consists of a browser-based PC application (hosted via GitHub Pages in the `docs` folder) and a specialized Android WebView application for mobile scanners/tablets providing additional deep-system features.
### Supported Devices and Makes
The system integrates the following device categories and manufacturers. The automated warranty checker and WebView injection autofills the portals for most of these tech brands:
- **Laptops:** Apple, Asus, Dell, HP
- **Tablets:** Samsung, Apple, Zebra
- **Scanners:** Zebra, Datalogic, Apple, Asus, Dell (Added into default UI flow for fast access)
- **Phones & Other:** Samsung, Apple, HP, Datalogic, Zebra
### Feature Matrix
| Feature | PC Web Browser | Android APK |
| :--- | :---: | :---: |
| Data entry to database (Supabase) | Yes | Yes |
| Automatic warranty page loading | Manual click required | Yes (JavaScript Injection) |
| Autofill serial numbers on warranty portals | No | Yes (Apple, Asus, Dell, HP, Lenovo, Samsung, Zebra) |
| Bluetooth Printer integration (Zebra ZQ620 / ZPL) | No | Yes |
| Built-in Camera Barcode/QR Scanner | No | Yes |
### PC Web App
Accessible from any modern browser. Communicates natively with the Supabase API. Handles data filtering, input, searching, and editing. Serial format logic and model assignments are contained in `app.js` under the `WEB_DEVICE_CATALOG`.
### Android WebView APK
The local Android container (`MainActivity.java`) acts as a wrapper with extended deep capabilities:
1. **JavaScript JS Injections:** When navigating to external vendor portals (e.g., `lenovo.com`, `dell.com`, `apple.com`), the custom `InventoryWebViewClient` automatically intercepts the WebResource loading state and injects a script utilizing deep Shadow DOM traversal to autofill the targeted serial number directly into the website's form.
2. **Bluetooth Printing (`AndroidPrinterBridge`):** Connects to Bluetooth Zebra ZQ620 printers over unsecured/secure RFCOMM sockets, allowing immediate label ZPL printing triggered by the web frontend. Includes background discovery routines and connection persistence checks.
3. **Native Camera Scanning:** Facilitated 1D/2D barcode reading seamlessly into the web input.
### Supabase Backend
Integration with the Rimi Baltic Supabase instance provides real-time persistent data storage for technical assets. JWT and URL connection strings are loaded primarily through `app.js`.
