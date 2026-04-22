const fs = require('fs');
const path1 = 'android/app/src/main/assets/web/app.js';
const path2 = 'docs/app.js';
function fix(filePath) {
    if (!fs.existsSync(filePath)) return;
    let code = fs.readFileSync(filePath, 'utf-8');
    let pieces = code.split('laptop: {');
    if (pieces.length === 2) {
        let scannerPart = pieces[0];
        if (scannerPart.indexOf('Apple: [') === -1) {
            scannerPart = scannerPart.replace(/Datalogic:.*?\]\,?/m, (m) => {
                if (!m.endsWith(',')) m += ',';
                return m + `\n    Apple: ["MacBook Air M1", "MacBook Air M2", "MacBook Air M3", "MacBook Pro 13", "MacBook Pro 14", "MacBook Pro 16", "Mac Mini", "Mac Studio", "iMac", "Mac Pro"],\n    Asus: ["ZenBook 14", "ZenBook Duo", "ZenBook Pro", "VivoBook 15", "VivoBook Pro", "ROG Zephyrus", "ROG Strix", "TUF Gaming", "ExpertBook"],\n    Dell: ["Latitude 3420", "Latitude 5430", "Latitude 5440", "Latitude 7330", "Latitude 7430", "Latitude 7440", "XPS 13", "XPS 15", "Precision 3570", "Precision 3580", "Vostro 3520", "Inspiron 15", "Alienware m15", "Alienware x14"],`;
            });
            fs.writeFileSync(filePath, scannerPart + 'laptop: {' + pieces[1]);
            console.log("Inserted into", filePath);
        }
    }
}
fix(path1);
fix(path2);
