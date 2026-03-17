
import sys
import os
import asyncio

# Add current directory to path
sys.path.append(os.getcwd())

from sqlalchemy.orm import sessionmaker
from backend.database import Base, engine as db_engine
from backend.models.website import Website
from backend.models.pagespeed import PageSpeedResult
from backend.models.user import User
from backend.routers.pagespeed import get_pagespeed_check
import traceback

async def test_check():
    try:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
        db = SessionLocal()

        # Mock a user
        mock_user = db.query(User).first()
        if not mock_user:
            print("No user found in DB to test with.")
        else:
            print(f"Testing with user: {mock_user.email}, role: {mock_user.role}")
            try:
                # Test with google.com
                url = "google.com"
                print(f"Checking URL: {url}")
                result = await get_pagespeed_check(url, db, mock_user)
                print("Result successfully fetched!")
                print(result)
            except Exception as e:
                print("ERROR IN get_pagespeed_check:")
                print(traceback.format_exc())

        db.close()
    except Exception as e:
        print("CRITICAL ERROR IN SCRIPT:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_check())
