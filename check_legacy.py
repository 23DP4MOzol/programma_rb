import sqlite3

def run():
    conn = sqlite3.connect("inventory.db")
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT device_type, model FROM devices")
    rows = cur.fetchall()
    print("Existing distinct devices:")
    for r in rows:
        print(r)

if __name__ == "__main__":
    run()
