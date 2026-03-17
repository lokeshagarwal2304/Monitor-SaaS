import os
import sys
import asyncio
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.getcwd())

from backend.database import SessionLocal
from backend.models.website import Website, WebsiteStatus
from backend.models.check_result import CheckResult
from sqlalchemy import func

async def test_get_monitor_logic(monitor_id):
    db = SessionLocal()
    try:
        # Step 1: Query Monitor
        print(f"Querying monitor {monitor_id}...")
        monitor = db.query(Website).filter(Website.id == monitor_id).first()
        if not monitor:
            print("Monitor not found")
            return
            
        print(f"Monitor found: {monitor.url}, status={monitor.status}, up_since={monitor.up_since}")
        
        # Step 2: Simulate Response Dict
        resp = {
            "id": monitor.id,
            "name": monitor.name,
            "url": monitor.url,
            "type": "HTTPS" if str(monitor.url).startswith("https") else "HTTP",
            "status": monitor.status,
            "interval": monitor.check_interval,
            "created_at": monitor.created_at,
            "last_checked": monitor.last_checked,
            "up_since": monitor.up_since,
            "region": monitor.region
        }
        print("Response dict created successfully")

        # Step 3: Test JSON Serialization (simulating FastAPI)
        import json
        from pydantic.json import pydantic_encoder
        
        def default_encoder(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if hasattr(obj, 'value'): # For Enums
                return obj.value
            return pydantic_encoder(obj)

        try:
            json.dumps(resp, default=default_encoder)
            print("JSON serialization successful")
        except Exception as e:
            print(f"JSON serialization FAILED: {e}")

    except Exception as e:
        print(f"Logic FAILED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_get_monitor_logic(3))
