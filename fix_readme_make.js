const fs = require('fs');
let text = fs.readFileSync('readme.md', 'utf-8');
text = text.replace(/- \*\*Laptops:\*\* Apple, Asus, Dell, Lenovo, HP/g, '- **Laptops:** Apple, Asus, Dell, HP');
text = text.replace(/- \*\*Tablets:\*\* Samsung, Apple, Lenovo, Zebra, Microsoft, Getac/g, '- **Tablets:** Samsung, Apple, Zebra');
text = text.replace(/- \*\*Phones & Other.*Nokia, etc. \(Acer and Motorola explicitly removed\)/g, '- **Phones & Other:** Samsung, Apple, HP, Datalogic, Zebra');
fs.writeFileSync('readme.md', text);
