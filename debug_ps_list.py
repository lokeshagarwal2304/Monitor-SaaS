
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base, SQLALCHEMY_DATABASE_URL
from backend.models.website import Website
from backend.models.pagespeed import PageSpeedResult
from backend.models.user import User
from backend.routers.pagespeed import get_latest_pagespeed_results
from unittest.mock import MagicMock

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Mock a user
mock_user = db.query(User).first()
if not mock_user:
    print("No user found in DB to test with.")
else:
    print(f"Testing with user: {mock_user.email}, role: {mock_user.role}")
    try:
        results = get_latest_pagespeed_results(db, mock_user)
        print("Results successfully fetched!")
        print(f"Count: {len(results)}")
    except Exception as e:
        import traceback
        traceback.print_exc()

db.close()
