const fs = require('fs');
const path1 = 'android/app/src/main/assets/web/app.js';
const path2 = 'docs/app.js';
function stripAll(filePath) {
    if (!fs.existsSync(filePath)) return;
    let code = fs.readFileSync(filePath, 'utf-8');
    // we will strictly strip: Lenovo, Microsoft, Getac, Google, Nokia, Xiaomi,
    // TSC, SATO, Brother, Epson, Bixolon, Toshiba Tec, Citizen, Godex,
    // Elo, NCR, Toshiba, Ingenico, Verifone, Fujitsu, ASUS
    const toRemove = [
        "Lenovo", "Microsoft", "Getac", "Google", "Nokia", "Xiaomi", "Fujitsu", "ASUS",
        "TSC", "SATO", "Brother", "Epson", "Bixolon", "Toshiba Tec", "Citizen", "Godex",
        "Elo", "NCR", "Toshiba", "Ingenico", "Verifone", "Other"
    ];
    toRemove.forEach(make => {
        // match Make: ["...", "...", ...], optionally with trailing comma
        const regex = new RegExp(`\\s*(?:\"?)${make}(?:\"?):\\s*\\[[^\\]]*\\]\\,?`, 'g');
        code = code.replace(regex, '');
    });
    fs.writeFileSync(filePath, code);
}
stripAll(path1);
stripAll(path2);
console.log("Stripped completely!");
