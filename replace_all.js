const fs = require('fs');
let code = fs.readFileSync('desktop_app.py', 'utf-8');
// The replacement dict block
const catalogReplacement = `DEVICE_CATALOG: dict[str, dict[str, list[str]]] = {
    "scanner": {
        "Zebra": ["DS2208", "DS2278", "DS3608", "DS3678", "DS4608", "DS4678", "DS8108", "DS8178", "DS9308", "LI2208", "LS2208", "RS5100", "RS6100", "SE4710", "TC20", "TC21", "TC22", "TC25", "TC26", "TC51", "TC52", "TC53", "TC53-HC", "TC56", "TC57", "TC58", "TC58-HC", "TC70", "TC70x", "TC72", "TC75", "TC75x", "TC77", "MC40", "MC55", "MC67", "MC92N0", "MC93", "MC2200", "MC2700", "MC3300", "MC3300x", "MC3390x", "WS50"],
        "Datalogic": ["Gryphon GD4500", "Gryphon GBT4500", "Gryphon GM4500", "QuickScan QD2430", "QuickScan QD2500", "PowerScan PD9630", "PowerScan PM9600", "PowerScan PBT9600", "Memor 10", "Memor 11", "Skorpio X4", "Skorpio X5", "Falcon X4", "Joya Touch"],
        "Apple": ["MacBook Air M1", "MacBook Air M2", "MacBook Air M3", "MacBook Pro 13", "MacBook Pro 14", "MacBook Pro 16", "Mac Mini", "Mac Studio", "iMac", "Mac Pro"],
        "Asus": ["ZenBook 14", "ZenBook Duo", "ZenBook Pro", "VivoBook 15", "VivoBook Pro", "ROG Zephyrus", "ROG Strix", "TUF Gaming", "ExpertBook"],
        "Dell": ["Latitude 3420", "Latitude 5430", "Latitude 5440", "Latitude 7330", "Latitude 7430", "Latitude 7440", "XPS 13", "XPS 15", "Precision 3570", "Precision 3580", "Vostro 3520", "Inspiron 15", "Alienware m15", "Alienware x14"]
    },
    "laptop": {
        "Dell": ["Latitude 3420", "Latitude 5430", "Latitude 5440", "Latitude 7330", "Latitude 7430", "Latitude 7440", "XPS 13", "XPS 15", "Precision 3570", "Precision 3580", "Vostro 3520", "Inspiron 15", "Alienware m15", "Alienware x14"],
        "Asus": ["ZenBook 14", "ZenBook Duo", "ZenBook Pro", "VivoBook 15", "VivoBook Pro", "ROG Zephyrus", "ROG Strix", "TUF Gaming", "ExpertBook"],
        "HP": ["EliteBook 830 G8", "EliteBook 830 G9", "EliteBook 840 G8", "EliteBook 840 G9", "EliteBook 840 G10", "EliteBook 850 G8", "ProBook 440 G8", "ProBook 450 G8", "ProBook 440 G9", "ProBook 450 G9", "ZBook Firefly 14", "ZBook Power 15"],
        "Apple": ["MacBook Air 13 M1", "MacBook Air 13 M2", "MacBook Air 15 M2", "MacBook Pro 13", "MacBook Pro 14", "MacBook Pro 16"]
    },
    "tablet": {
        "Samsung": ["Galaxy Tab A7", "Galaxy Tab A8", "Galaxy Tab S6 Lite", "Galaxy Tab S7", "Galaxy Tab S8", "Galaxy Tab S9", "Galaxy Tab Active3", "Galaxy Tab Active4 Pro", "Galaxy Tab Active5"],
        "Apple": ["iPad 9th Gen", "iPad 10th Gen", "iPad Air 5", "iPad Mini 6", "iPad Pro 11", "iPad Pro 12.9"],
        "Zebra": ["ET40", "ET45", "L10", "XSLATE L10"]
    },
    "phone": {
        "Samsung": ["Galaxy S21", "Galaxy S22", "Galaxy S23", "Galaxy S24", "Galaxy A54", "Galaxy A55", "Galaxy XCover 5", "Galaxy XCover 6 Pro", "Galaxy XCover 7"],
        "Apple": ["iPhone 11", "iPhone 12", "iPhone 13", "iPhone 14", "iPhone 15", "iPhone 16", "iPhone SE"]
    },
    "printer": {
        "Zebra": ["ZD220", "ZD230", "ZD421", "ZD621", "ZT111", "ZT231", "ZT411", "ZT421", "GK420d", "GX430t", "QLn220", "QLn320", "ZQ310", "ZQ320", "ZQ511", "ZQ521", "ZR138"]
    },
    "other": {
        "HP": ["Engage One", "Engage Flex Pro", "RP9"],
        "Datalogic": ["Magellan 1500i", "Magellan 3410VSi", "Joya Touch A6"],
        "Zebra": ["CC600", "CC6000", "DS9308 Scale", "MP7000"]
    }
}
WARRANTY_MARKER`;
// replace from DEVICE_CATALOG to WARRANTY_MARKER
code = code.replace(/DEVICE_CATALOG:[^]+WARRANTY_MARKER/g, catalogReplacement);
fs.writeFileSync('desktop_app.py', code);
console.log("Done replace!");
