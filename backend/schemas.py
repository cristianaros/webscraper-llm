from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NewsBase(BaseModel):
    title: str
    summary: Optional[str] = None
    content: str
    category: str = "General"
    university: str = "Universidad Demo"
    author: Optional[str] = None
    image_url: Optional[str] = None
    source_url: Optional[str] = None
    is_featured: bool = False


class NewsCreate(NewsBase):
    pass


class NewsUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    university: Optional[str] = None
    author: Optional[str] = None
    image_url: Optional[str] = None
    source_url: Optional[str] = None
    is_featured: Optional[bool] = None


class NewsResponse(NewsBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    question: str
    history: Optional[list] = []


class ChatResponse(BaseModel):
    answer: str
    sources: Optional[list] = []


class StatsResponse(BaseModel):
    total_news: int
    categories: dict
    universities: list
    featured_count: int
