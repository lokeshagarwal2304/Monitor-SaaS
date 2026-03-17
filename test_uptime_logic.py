import asyncio
import os
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend.services.monitoring_service import process_monitoring_check
from backend.models.website import Website, WebsiteStatus
from datetime import datetime

async def main():
    db = SessionLocal()
    try:
        # First, let's artificially set one monitor to DOWN to test the transition
        monitor = db.query(Website).filter(Website.status == WebsiteStatus.UP).first()
        if monitor:
            print(f"Test: Setting monitor {monitor.id} ({monitor.url}) to DOWN to test transition.")
            monitor.status = WebsiteStatus.DOWN
            monitor.up_since = None
            db.commit()

        print("Running monitoring check...")
        await process_monitoring_check(db)
        
        # Verify results
        monitors = db.query(Website).all()
        print("\nVerification Results:")
        for m in monitors:
            print(f"ID: {m.id}, URL: {m.url}, Status: {m.status}, Up Since: {m.up_since}")
            
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
