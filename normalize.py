import sqlite3
import os

db_path = r"C:\Users\LV02XVY\OneDrive - Rimi Baltic\Documents\programma_rb\inventory.db"
if not os.path.exists(db_path):
    # try relative
    db_path = "inventory.db"

conn = sqlite3.connect(db_path)

mapping = {
    "Skeneris": "scanner",
    "Portatīvais": "laptop",
    "Planšete": "tablet",
    "Telefons": "phone",
    "Cits": "other",
    "Scanner": "scanner",
    "Laptop": "laptop",
    "Tablet": "tablet",
    "Phone": "phone",
    "Other": "other"
}

for old, new in mapping.items():
    cur = conn.execute("UPDATE devices SET device_type = ? WHERE device_type = ?", (new, old))
    if cur.rowcount > 0:
        print(f"Updated {cur.rowcount} rows: {old} -> {new}")

conn.commit()
print("Done normalization.")
