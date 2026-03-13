import sqlite3
import os

db_path = r'c:\Users\Lokesh Agarwal\Desktop\MoniFy\data\monitoring.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Listing all users from 'users' table:")
    try:
        cursor.execute("SELECT id, email, password, role, name FROM users")
        users = cursor.fetchall()
        for user in users:
            print(f"ID: {user[0]}, Email: {user[1]}, Password (hashed): {user[2]}, Role: {user[3]}, Name: {user[4]}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
else:
    print(f"Database not found at {db_path}")
