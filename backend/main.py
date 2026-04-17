"""
KenyaNews — backend/main.py
FastAPI REST API for the KenyaNews platform.

Endpoints:
  GET  /health                   → health check
  GET  /api/stories              → paginated story list (filterable)
  GET  /api/stories/{id}         → single story
  GET  /api/stories/category/{cat} → stories by category
  GET  /api/search?q=...         → full-text search
  POST /api/stories              → create story (API-key protected)
  POST /api/subscribe            → add email subscriber
  GET  /api/stats                → platform statistics
"""

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Depends, Query, Header, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from bson import ObjectId
from dotenv import load_dotenv

from database import connect_db, close_db, stories_collection, subscribers_collection
from models   import StoryCreate, StoryResponse, PaginatedStories, SubscriberCreate

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
load_dotenv()
logger = logging.getLogger(__name__)

API_KEY      = os.getenv("API_KEY", "dev-secret-key")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

VALID_CATEGORIES = [
    "Kenya", "Africa", "World", "Business",
    "Sports", "Technology", "Health", "Politics", "General",
]


# ─────────────────────────────────────────
# Lifespan (replaces on_event)
# ─────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    # Ensure indexes
    col = stories_collection()
    await col.create_index("headline", unique=True)
    await col.create_index([("timestamp", -1)])
    await col.create_index("category")
    await col.create_index([("headline", "text"), ("summary", "text")])
    yield
    await close_db()


# ─────────────────────────────────────────
# App
# ─────────────────────────────────────────

app = FastAPI(
    title="KenyaNews API",
    description="Automated Kenyan news aggregation API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# ─────────────────────────────────────────
# Auth dependency
# ─────────────────────────────────────────

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key


# ─────────────────────────────────────────
# Serialiser helper
# ─────────────────────────────────────────

def serialise(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


# ─────────────────────────────────────────
# Routes
# ─────────────────────────────────────────

@app.get("/health")
@limiter.limit("60/minute")
async def health(request: Request):
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/stats")
@limiter.limit("100/minute")
async def get_stats(request: Request):
    col = stories_collection()
    total = await col.count_documents({})
    by_category = {}
    for cat in VALID_CATEGORIES:
        count = await col.count_documents({"category": cat})
        if count:
            by_category[cat] = count
    latest_doc = await col.find_one({}, sort=[("timestamp", -1)])
    latest_ts  = latest_doc["timestamp"] if latest_doc else None
    return {
        "total_stories": total,
        "by_category":   by_category,
        "latest_update": latest_ts,
    }


@app.get("/api/stories", response_model=PaginatedStories)
@limiter.limit("100/minute")
async def get_stories(
    request: Request,
    page:     int = Query(1, ge=1),
    size:     int = Query(20, ge=1, le=100),
    category: str = Query(None),
    source:   str = Query(None),
):
    col    = stories_collection()
    query  = {}
    if category:
        query["category"] = category
    if source:
        query["source"] = source

    total  = await col.count_documents(query)
    skip   = (page - 1) * size
    cursor = col.find(query).sort("timestamp", -1).skip(skip).limit(size)
    docs   = [serialise(d) async for d in cursor]

    return PaginatedStories(
        stories=docs,
        total=total,
        page=page,
        page_size=size,
        has_next=(skip + size) < total,
    )


@app.get("/api/stories/category/{category}")
@limiter.limit("100/minute")
async def get_by_category(request: Request, category: str, limit: int = Query(20, ge=1, le=100)):
    col  = stories_collection()
    cur  = col.find({"category": category}).sort("timestamp", -1).limit(limit)
    docs = [serialise(d) async for d in cur]
    return {"category": category, "stories": docs, "count": len(docs)}


@app.get("/api/search")
@limiter.limit("60/minute")
async def search_stories(
    request: Request,
    q:    str = Query(..., min_length=2),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    col   = stories_collection()
    query = {"$text": {"$search": q}}
    total = await col.count_documents(query)
    skip  = (page - 1) * size
    cur   = col.find(query, {"score": {"$meta": "textScore"}}).sort(
        [("score", {"$meta": "textScore"})]
    ).skip(skip).limit(size)
    docs  = [serialise(d) async for d in cur]
    return {"query": q, "stories": docs, "total": total, "page": page}


@app.get("/api/stories/{story_id}")
@limiter.limit("100/minute")
async def get_story(request: Request, story_id: str):
    try:
        oid = ObjectId(story_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid story ID")
    col = stories_collection()
    doc = await col.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Story not found")
    return serialise(doc)


@app.post("/api/stories", status_code=201)
@limiter.limit("30/minute")
async def create_story(request: Request, story: StoryCreate, _: str = Depends(verify_api_key)):
    col = stories_collection()
    # Check duplicate by headline
    existing = await col.find_one({"headline": story.headline})
    if existing:
        raise HTTPException(status_code=409, detail="Story already exists")

    doc = story.model_dump()
    doc["created_at"] = datetime.now(timezone.utc).isoformat()
    result = await col.insert_one(doc)
    return {"id": str(result.inserted_id), "headline": story.headline}


@app.post("/api/subscribe", status_code=201)
@limiter.limit("5/minute")
async def subscribe(request: Request, sub: SubscriberCreate):
    col = subscribers_collection()
    existing = await col.find_one({"email": sub.email})
    if existing:
        return JSONResponse(
            status_code=200,
            content={"message": "Already subscribed", "email": sub.email}
        )
    await col.insert_one({**sub.model_dump(), "subscribed_at": datetime.now(timezone.utc).isoformat()})
    return {"message": "Subscribed successfully", "email": sub.email}


@app.delete("/api/stories/{story_id}", status_code=204)
@limiter.limit("30/minute")
async def delete_story(request: Request, story_id: str, _: str = Depends(verify_api_key)):
    try:
        oid = ObjectId(story_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid story ID")
    col    = stories_collection()
    result = await col.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Story not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
