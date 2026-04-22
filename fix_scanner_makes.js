const fs = require('fs');
const appJsPath1 = 'android/app/src/main/assets/web/app.js';
const appJsPath2 = 'docs/app.js';
function patchAppJs(filePath) {
    if (!fs.existsSync(filePath)) return;
    let code = fs.readFileSync(filePath, 'utf-8');
    // Extract the models
    const appleMatch = code.match(/Apple:\s*\[([^\]]+)\]/);
    const appleModels = appleMatch ? appleMatch[1] : '"MacBook Air 13 M1", "MacBook Air 13 M2", "MacBook Air 15 M2", "MacBook Pro 13", "MacBook Pro 14", "MacBook Pro 16", "iMac", "Mac Studio", "Mac mini", "Mac Pro"';
    const asusModels = '"ZenBook 14", "ZenBook Duo", "ZenBook Pro", "VivoBook 15", "VivoBook Pro", "ROG Zephyrus", "ROG Strix", "TUF Gaming", "ExpertBook"';
    const dellModels = '"Latitude 3420", "Latitude 5430", "Latitude 5440", "Latitude 7330", "Latitude 7430", "Latitude 7440", "XPS 13", "XPS 15", "Precision 3570", "Precision 3580", "Vostro 3520", "Inspiron 15", "Alienware m15", "Alienware x14"';
    // Inject into scanner if not present
    if (code.indexOf('scanner: {\n    Zebra:') !== -1 || code.indexOf('scanner: {\n      Zebra:') !== -1) {
        code = code.replace(/scanner:\s*\{[\s\S]*?Datalogic:.*?\]\,/m, (match) => {
            if (match.indexOf('Apple:') === -1) {
                return match + `\n      Apple: [${appleModels}],\n      Asus: [${asusModels}],\n      Dell: [${dellModels}],`;
            }
            return match;
        });
    }
    fs.writeFileSync(filePath, code);
}
patchAppJs(appJsPath1);
patchAppJs(appJsPath2);
console.log("Patched scanner makes.");
