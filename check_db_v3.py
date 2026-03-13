import sqlite3
import os
import sys

# Try to use the same logic as backend/database.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "data")
DATABASE_PATH = os.path.join(DATABASE_DIR, "monitoring.db")

print(f"Checking database at: {DATABASE_PATH}")

if os.path.exists(DATABASE_PATH):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables found: {[t[0] for t in tables]}")
    
    for table in [t[0] for t in tables]:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"Table {table} has {count} rows")
        
        if table == 'websites' and count > 0:
            cursor.execute("SELECT id, name, url, owner_id FROM websites")
            for row in cursor.fetchall():
                print(f"  Website: {row}")
        
    conn.close()
else:
    print("Database file NOT FOUND at that path.")
