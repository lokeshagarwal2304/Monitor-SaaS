import sqlite3
import os

db_path = r"c:\Users\Lokesh Agarwal\Desktop\Monitor-SaaS\data\monitoring.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"Tables in {db_path}:")
for t in tables:
    print(t[0])
conn.close()
