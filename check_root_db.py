
import sqlite3
import os

db_path = os.path.join(os.getcwd(), "data", "monitoring.db")
print(f"Checking DB: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in database:")
for t in tables:
    print(t[0])
    
cursor.execute("PRAGMA table_info(pagespeed_results)")
print(f"Columns in pagespeed_results: {cursor.fetchall()}")

conn.close()
