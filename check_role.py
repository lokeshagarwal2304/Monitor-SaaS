import sys
import os
sys.path.append(os.getcwd())
from backend.database import SessionLocal
from backend.models.user import User

def check_role():
    db = SessionLocal()
    try:
        email = input("Enter the email you logged in with (e.g., lokeshagarwal2304@gmail.com): ").strip()
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            print("====================================")
            print(f"✅ User Name in DB: {user.name}")
            print(f"✅ Current Role in DB: {user.role.value}")
            print("====================================")
        else:
            print("❌ User not found in database.")
    finally:
        db.close()

if __name__ == "__main__":
    check_role()