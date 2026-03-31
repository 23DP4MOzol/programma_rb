import sqlite3
import os

db_path = r"C:\Users\LV02XVY\OneDrive - Rimi Baltic\Documents\programma_rb\inventory.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get distinct types
cur.execute("SELECT DISTINCT device_type FROM devices")
types = [r[0] for r in cur.fetchall()]
print(f"Distinct types: {types}")

# Get all data for models to check why it's not extracting make properly
cur.execute("SELECT device_type, model FROM devices LIMIT 10")
models = cur.fetchall()
print("Sample models:")
for row in models:
    print(row)
