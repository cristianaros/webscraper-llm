from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from database import Base


class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, default="General")
    university = Column(String(200), nullable=False, default="Universidad Demo")
    author = Column(String(150), nullable=True)
    image_url = Column(String(500), nullable=True)
    source_url = Column(String(500), nullable=True)
    is_featured = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
