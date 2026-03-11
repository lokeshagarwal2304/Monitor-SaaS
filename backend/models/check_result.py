from sqlalchemy import Column, Integer, Float, Boolean, String, DateTime, ForeignKey
from datetime import datetime
from backend.database import Base

class CheckResult(Base):
    __tablename__ = "check_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    website_id = Column(Integer, ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True)
    status_code = Column(Integer, nullable=True)
    response_time = Column(Float, nullable=True)  # in ms
    is_up = Column(Boolean, nullable=False)
    error_message = Column(String(500), nullable=True)
    checked_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<CheckResult(site={self.website_id}, up={self.is_up})>"