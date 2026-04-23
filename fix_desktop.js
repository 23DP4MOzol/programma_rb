const fs = require('fs');
let code = fs.readFileSync('desktop_app.py', 'utf-8');
const toRemove = [
    "Lenovo", "Microsoft", "Getac", "Google", "Nokia", "Xiaomi", "Fujitsu",
    "TSC", "SATO", "Brother", "Epson", "Bixolon", "Toshiba Tec", "Citizen", "Godex",
    "Elo", "NCR", "Toshiba", "Ingenico", "Verifone", "Other", "Acer", "Motorola"
];
toRemove.forEach(make => {
    // python dictionary "Make": ["...", ...], 
    const regex = new RegExp(`\\s*\"${make}\":\\s*\\[[^\\]]*\\]\\,?`, 'g');
    code = code.replace(regex, '');
});
fs.writeFileSync('desktop_app.py', code);
console.log("Stripped completely!");
