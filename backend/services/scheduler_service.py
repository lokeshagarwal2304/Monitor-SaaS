from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.database import SessionLocal
from backend.services.monitoring_service import process_monitoring_check

scheduler = AsyncIOScheduler()

async def run_monitoring_job():
    db = SessionLocal()
    try:
        await process_monitoring_check(db)
    finally:
        db.close()

def start_scheduler():
    if not scheduler.running:
        # Add job to run every 5 minutes
        scheduler.add_job(run_monitoring_job, 'interval', minutes=5)
        scheduler.start()
        print("⏰ Monitoring Scheduler Started (Running every 5 mins)")