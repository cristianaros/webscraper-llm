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
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    question: str
    history: list = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    sources: list = Field(default_factory=list)


class StatsResponse(BaseModel):
    total_news: int
    categories: dict
    universities: list
    featured_count: int


class ScrapeUplaRequest(BaseModel):
    limit: int = Field(default=5, ge=1, le=10)


class ScrapeItemResult(BaseModel):
    title: str
    source_url: str
    status: str
    news_id: Optional[int] = None
    error: Optional[str] = None


class ScrapeUplaResponse(BaseModel):
    requested: int
    found: int
    created: int
    skipped: int
    failed: int
    model: str
    items: list[ScrapeItemResult] = Field(default_factory=list)
