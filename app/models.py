# app/models.py
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from app.database import Base

class URLItem(Base):
    __tablename__ = "urls"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    original_url = Column(String, nullable=False)
    short_code = Column(String(12), unique=True, index=True, nullable=True)
    clicks = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
