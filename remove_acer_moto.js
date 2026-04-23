const fs = require('fs');
const path1 = 'android/app/src/main/assets/web/app.js';
const path2 = 'docs/app.js';
function removeMakes(filePath) {
    if (!fs.existsSync(filePath)) return;
    let code = fs.readFileSync(filePath, 'utf-8');
    // Remove Acer and Motorola along with their arrays and optional trailing commas
    code = code.replace(/\s*Acer:\s*\[[^\]]*\]\,?/g, '');
    code = code.replace(/\s*Motorola:\s*\[[^\]]*\]\,?/g, '');
    fs.writeFileSync(filePath, code);
    console.log("Removed Acer and Motorola from", filePath);
}
removeMakes(path1);
removeMakes(path2);
