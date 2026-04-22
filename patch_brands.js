const fs = require('fs');
const appJsPath1 = 'android/app/src/main/assets/web/app.js';
const appJsPath2 = 'docs/app.js';
const mainActivityPath = 'android/app/src/main/java/com/rimi/inventory/MainActivity.java';
function patchAppJs(filePath) {
    if (!fs.existsSync(filePath)) return;
    let code = fs.readFileSync(filePath, 'utf-8');
    // Remove old brands from scanner catalog
    code = code.replace(/\s*Bluebird:.*?\]\,/g, '');
    code = code.replace(/\s*Chainway:.*?\]\,/g, '');
    code = code.replace(/\s*CipherLab:.*?\]\,/g, '');
    code = code.replace(/\s*Honeywell:.*?\]\,/g, '');
    code = code.replace(/\s*Newland:.*?\]\,/g, '');
    code = code.replace(/\s*Panasonic:.*?\]\,/g, '');
    code = code.replace(/\s*Unitech:.*?\]\,/g, '');
    code = code.replace(/\s*Urovo:.*?\]\,/g, '');
    // Add models
    const asusLaptops = `Asus: ["ZenBook 14", "ZenBook Duo", "ZenBook Pro", "VivoBook 15", "VivoBook Pro", "ROG Zephyrus", "ROG Strix", "TUF Gaming", "ExpertBook"],`;
    const dellLaptops = `Dell: ["Latitude 3420", "Latitude 5430", "Latitude 5440", "Latitude 7330", "Latitude 7430", "Latitude 7440", "XPS 13", "XPS 15", "Precision 3570", "Precision 3580", "Vostro 3520", "Inspiron 15", "Alienware m15", "Alienware x14"],`;
    if (code.indexOf('Asus: [') === -1) {
        code = code.replace(/laptop: \{([\s\S]*?)Dell:.*?\]\,/m, `laptop: {$1${dellLaptops}\n      ${asusLaptops}`);
        if(code.indexOf('Asus: [') === -1) {
            code = code.replace(/laptop: \{/, `laptop: {\n      ${dellLaptops}\n      ${asusLaptops}`);
        }
    }
    if (code.indexOf('asus:') === -1 && code.indexOf('WARRANTY_CHECKER_URL_BY_MAKE = {') !== -1) {
        code = code.replace(/hp: "https:\/\/support\.hp\.com\/us-en\/check-warranty",/, 
            `hp: "https://support.hp.com/us-en/check-warranty",\n    asus: "https://www.asus.com/us/support/warranty-status",\n    dell: "https://www.dell.com/support/home/en-us/?app=warranty",`);
    }
    if (code.indexOf('asus:') === -1 && code.indexOf('WARRANTY_CHECKER_SERIAL_PARAM_BY_MAKE = {') !== -1) {
        code = code.replace(/hp: "serialnumber",/, 
            `hp: "serialnumber",\n    asus: "serial",\n    dell: "serial",`);
    }
    fs.writeFileSync(filePath, code);
}
patchAppJs(appJsPath1);
patchAppJs(appJsPath2);
// UPDATE MAIN ACTIVITY
let mainActivity = fs.readFileSync(mainActivityPath, 'utf-8');
// Update conditions
mainActivity = mainActivity.replace(/url\.contains\("lenovo\.com"\)\s*\|\|\s*url\.contains\("support\.hp\.com"\)/, 
    'url.contains("lenovo.com") || url.contains("support.hp.com") || url.contains("apple.com") || url.contains("asus.com") || url.contains("dell.com")');
// Extract the JS block
let jsBlockMatch = mainActivity.match(/String js = "try \{ \(function\(\) \{".*?catch\(e\) \{\}";/s);
if (jsBlockMatch) {
    let jsBlock = jsBlockMatch[0];
    // Fix lenovo
    jsBlock = jsBlock.replace(/else if \(currUrl\.indexOf\('lenovo'\) > -1\) \{.*?\}(?=\s*else if| \s*if|\s*try \s*\{)/s,
        `else if (currUrl.indexOf('lenovo') > -1) {` +
        `      input = deepQuery('input.button-placeholder__input, input[name="search-text"], input#input-search, input.search-input, input.sn-search, input[placeholder*="Serial"], input[type="text"]');` +
        `      btn = deepQuery('button.basic-search__suffix-btn, button[aria-label*="Search"], button.search-button, button#search-btn, button[type="submit"]');` +
        `      if (!btn) { var allBtns = document.querySelectorAll('button'); for(var i=0;i<allBtns.length;i++){ var t=allBtns[i].innerText?allBtns[i].innerText.toLowerCase():''; if(t.indexOf('search')>-1||t.indexOf('submit')>-1||t.indexOf('check')>-1){ btn=allBtns[i]; break; } } }` +
        `    } else if (currUrl.indexOf('apple.com') > -1) {` +
        `      input = deepQuery('input[id*="serial"], input[name*="serial"], input[placeholder*="Serial"], input[type="text"]');` +
        `      btn = deepQuery('button[id*="submit"], button[type="submit"], button');` +
        `    } else if (currUrl.indexOf('asus.com') > -1) {` +
        `      input = deepQuery('input[name="serialNumber"], input[id*="serial"], input[placeholder*="Serial"], input[type="text"]');` +
        `      btn = deepQuery('button[type="submit"], button[class*="search"], button[class*="submit"], button');` +
        `    } else if (currUrl.indexOf('dell.com') > -1) {` +
        `      input = deepQuery('input[id*="ServiceTag"], input[id*="serial"], input[name*="serial"], input[placeholder*="Service Tag"], input[placeholder*="Serial"], input[type="text"]');` +
        `      btn = deepQuery('button[id*="submit"], button[id*="search"], button[class*="submit"], button[class*="search"], button');` +
        `    }`
    );
    mainActivity = mainActivity.replace(jsBlockMatch[0], jsBlock);
    fs.writeFileSync(mainActivityPath, mainActivity);
    console.log("Patched successfully!");
} else {
    console.log("Could not find JS block in MainActivity.");
}
