from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from datetime import datetime
from backend.database import Base

class MonitorStatusHistory(Base):
    __tablename__ = "monitor_status_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    monitor_id = Column(Integer, ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    response_time = Column(Float, nullable=True)
    checked_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<MonitorStatusHistory(monitor={self.monitor_id}, status={self.status})>"
