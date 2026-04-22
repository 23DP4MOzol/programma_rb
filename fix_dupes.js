const fs = require('fs');
let mainActivityPath = 'android/app/src/main/java/com/rimi/inventory/MainActivity.java';
let code = fs.readFileSync(mainActivityPath, 'utf-8');
// Fix duplicates in URL checks
code = code.replace(/url\.contains\("apple\.com"\) \|\| url\.contains\("asus\.com"\) \|\| url\.contains\("dell\.com"\) \|\| url\.contains\("apple\.com"\) \|\| url\.contains\("asus\.com"\) \|\| url\.contains\("dell\.com"\)/, 
    'url.contains("apple.com") || url.contains("asus.com") || url.contains("dell.com")');
// Fix duplicate JS injection logic. 
// Just remove the second set of else if's
code = code.replace(/\} else if \(currUrl\.indexOf\('apple\.com'\) > -1\) \{\s*input = deepQuery\('input\[id\*="serial"\], input\[name\*="serial"\], input\[placeholder\*="Serial"\], input\[type="text"\]'\);\s*btn = deepQuery\('button\[id\*="submit"\], button\[type="submit"\], button'\);\s*\} else if \(currUrl\.indexOf\('asus\.com'\) > -1\) \{\s*input = deepQuery\('input\[name="serialNumber"\], input\[id\*="serial"\], input\[placeholder\*="Serial"\], input\[type="text"\]'\);\s*btn = deepQuery\('button\[type="submit"\], button\[class\*="search"\], button\[class\*="submit"\], button'\);\s*\} else if \(currUrl\.indexOf\('dell\.com'\) > -1\) \{\s*input = deepQuery\('input\[id\*="ServiceTag"\], input\[id\*="serial"\], input\[name\*="serial"\], input\[placeholder\*="Service Tag"\], input\[placeholder\*="Serial"\], input\[type="text"\]'\);\s*btn = deepQuery\('button\[id\*="submit"\], button\[id\*="search"\], button\[class\*="submit"\], button\[class\*="search"\], button'\);\s*\}/, '');
fs.writeFileSync(mainActivityPath, code);
console.log("Fixed duplicates");
