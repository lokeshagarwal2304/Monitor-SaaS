from backend.database import SessionLocal
from backend.models.pagespeed import PageSpeedResult
from backend.models.website import Website

db = SessionLocal()
try:
    results = db.query(PageSpeedResult).all()
    print(f"Total PageSpeed results: {len(results)}")
    for r in results:
        print(f"ID: {r.id}, Monitor: {r.monitor_id}, Score: {r.score}, LoadTime: {r.load_time}, Status: {r.status}, FCP: {r.fcp}")
    
    websites = db.query(Website).all()
    print(f"Total Websites: {len(websites)}")
    for w in websites:
         print(f"ID: {w.id}, Name: {w.name}, URL: {w.url}")
finally:
    db.close()
