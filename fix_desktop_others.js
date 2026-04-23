const fs = require('fs');
let code = fs.readFileSync('desktop_app.py', 'utf-8');
const makesToRemove = [
    "lenovo", "microsoft", "getac", "google", "nokia", "xiaomi", "fujitsu", 
    "tsc", "sato", "brother", "epson", "bixolon", "toshibatec", "citizen", "godex", 
    "elo", "ncr", "toshiba", "ingenico", "verifone", "acer", "motorola", "honeywell", "unitech", "urovo", "newland", "cipherlab", "bluebird", "chainway", "panasonic"
];
makesToRemove.forEach(make => {
    const rx1 = new RegExp(`\\s*"${make}":\\s*\\{[^}]*\\},?`, 'ig');
    code = code.replace(rx1, '');
    const rx2 = new RegExp(`\\s*"${make}":\\s*\\([^\)]*\\),?`, 'ig');
    code = code.replace(rx2, '');
    const rx3 = new RegExp(`\\s*"${make}":\\s*"[^"]*",?`, 'ig');
    code = code.replace(rx3, '');
});
// Clean upPREFIX_MAP too
code = code.replace(/\s*"PF": \("laptop",\s*"Lenovo", "Lenovo ThinkPad"\),.*/g, '');
code = code.replace(/\s*"PC": \("laptop",\s*"Lenovo", "Lenovo ThinkPad"\),.*/g, '');
fs.writeFileSync('desktop_app.py', code);
console.log("Other things replaced!");
