const fs = require('fs');
let mainActivityPath = 'android/app/src/main/java/com/rimi/inventory/MainActivity.java';
let code = fs.readFileSync(mainActivityPath, 'utf-8');
code = code.replace(/\} \}\s*else if \(currUrl\.indexOf\('apple\.com'\) > -1\)/g, '} } } } else if (currUrl.indexOf(\'apple.com\') > -1)');
fs.writeFileSync(mainActivityPath, code);
console.log("Fixed bracket");
