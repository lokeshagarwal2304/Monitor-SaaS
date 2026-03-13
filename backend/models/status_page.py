from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from datetime import datetime
from backend.database import Base

class StatusPage(Base):
    __tablename__ = "status_pages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    monitor_id = Column(Integer, ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True)
    current_status = Column(String(50), nullable=True)
    uptime_percentage = Column(Float, nullable=True)
    last_checked = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<StatusPage(monitor={self.monitor_id}, status={self.current_status})>"
