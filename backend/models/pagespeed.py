from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
from backend.database import Base

class PageSpeedResult(Base):
    __tablename__ = "pagespeed_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    monitor_id = Column(Integer, ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True)
    score = Column(Integer, nullable=False) # 0-100
    load_time = Column(Float, nullable=False) # in ms
    status = Column(String, default="UP") # UP/DOWN
    fcp = Column(Float, nullable=True) # First Contentful Paint in ms
    checked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
