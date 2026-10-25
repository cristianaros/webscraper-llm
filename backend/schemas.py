from pydantic import BaseModel, Field
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
    published_at: Optional[datetime] = None


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
    published_at: Optional[datetime] = None


class NewsResponse(NewsBase):
    id: int
    university_id: Optional[int] = None
    published_on: Optional[datetime] = None
    date_precision: Optional[str] = None
    publication_status: str = "published"
    image_status: str = "not_found"
    image_sha256: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    news_id: Optional[int] = Field(default=None, gt=0)
    history: list = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    sources: list = Field(default_factory=list)


class StatsResponse(BaseModel):
    total_news: int
    categories: dict
    universities: list
    featured_count: int
