const fs = require('fs');
const appJsPath1 = 'android/app/src/main/assets/web/app.js';
const appJsPath2 = 'docs/app.js';
function patchAppJs(filePath) {
    if (!fs.existsSync(filePath)) return;
    let code = fs.readFileSync(filePath, 'utf-8');
    code = code.replace(/WARRANTY_CHECKER_SERIAL_PARAM_BY_MAKE = \{[\s\S]*?\n\s+lenovo: "serial",/, (match) => {
        if(match.indexOf('asus:') === -1) {
            return match.replace(/hp: "serialnumber",/, `hp: "serialnumber",\n    asus: "serial",\n    dell: "serviceTag",`);
        }
        return match;
    });
    fs.writeFileSync(filePath, code);
}
patchAppJs(appJsPath1);
patchAppJs(appJsPath2);
console.log("Patched params.");
