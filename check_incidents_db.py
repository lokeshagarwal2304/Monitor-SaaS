from backend.database import SessionLocal
from backend.models.incident import Incident
import json

db = SessionLocal()
try:
    incidents = db.query(Incident).all()
    print(f"Total Incidents: {len(incidents)}")
    for inc in incidents:
        print(f"ID: {inc.id}, Monitor: {inc.monitor_name}, Status: {inc.new_status}, State: {'Ongoing' if inc.resolved_at is None else 'Resolved'}, Started: {inc.started_at}, Resolved: {inc.resolved_at}")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
