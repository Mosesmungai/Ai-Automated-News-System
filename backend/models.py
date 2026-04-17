"""
KenyaNews — backend/models.py
Pydantic v2 schemas for the stories API.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional
from datetime import datetime


class StoryCreate(BaseModel):
    headline:       str
    summary:        str
    bullets:        list[str]       = []
    source_links:   list[str]       = []
    media:          list[str]       = []
    category:       str             = "General"
    source:         str             = "Unknown"
    verified_by:    list[str]       = []
    confidence:     float           = 0.5
    social_mentions: int            = 0
    social_platforms: list[str]     = []
    timestamp:      str             = Field(
        default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    )


class StoryResponse(BaseModel):
    id:             str
    headline:       str
    summary:        str
    bullets:        list[str]       = []
    source_links:   list[str]       = []
    media:          list[str]       = []
    category:       str
    source:         str
    verified_by:    list[str]       = []
    confidence:     float
    social_mentions: int            = 0
    social_platforms: list[str]     = []
    timestamp:      str


class SubscriberCreate(BaseModel):
    email: str
    name:  Optional[str] = None


class PaginatedStories(BaseModel):
    stories:    list[StoryResponse]
    total:      int
    page:       int
    page_size:  int
    has_next:   bool
