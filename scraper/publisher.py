"""
KenyaNews — publisher.py
Sends verified, summarised stories to the FastAPI backend via REST API.
Skips duplicates (backend returns 409 for known headlines).
"""

import os
import logging
import requests
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
API_KEY     = os.getenv("BACKEND_API_KEY", "dev-secret-key")

HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY,
}


def build_payload(story: dict) -> dict:
    """Convert internal story dict to the API payload schema."""
    media = []
    if story.get("image"):
        media.append(story["image"])

    return {
        "headline":     story["headline"],
        "summary":      story.get("summary", story.get("description", "")),
        "bullets":      story.get("bullets", []),
        "source_links": [story["link"]] + [
            s for s in story.get("verified_sources_links", [])
        ],
        "media":        media,
        "category":     story.get("category", "General"),
        "source":       story.get("source", "Unknown"),
        "verified_by":  story.get("verified_sources", [story.get("source", "")]),
        "confidence":   story.get("confidence", 0.5),
        "timestamp":    story.get("timestamp",
                                  datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")),
    }


def publish_story(story: dict) -> bool:
    """POST one story to the backend. Returns True on success."""
    payload = build_payload(story)
    try:
        resp = requests.post(
            f"{BACKEND_URL}/api/stories",
            json=payload,
            headers=HEADERS,
            timeout=15,
        )
        if resp.status_code == 201:
            logger.info(f"  ✓ Published: {story['headline'][:60]}")
            return True
        elif resp.status_code == 409:
            logger.info(f"  ~ Duplicate: {story['headline'][:60]}")
            return False
        else:
            logger.warning(f"  ✗ Backend {resp.status_code}: {resp.text[:200]}")
            return False
    except requests.RequestException as e:
        logger.error(f"  ✗ Publish failed: {e}")
        return False


def publish_all(stories: list[dict]) -> dict:
    """Publish all stories; return counts."""
    published = skipped = failed = 0
    for story in stories:
        result = publish_story(story)
        if result is True:
            published += 1
        elif result is False and "Duplicate" in str(result):
            skipped += 1
        else:
            failed += 1
    logger.info(f"Publish summary → published={published}, skipped={skipped}, failed={failed}")
    return {"published": published, "skipped": skipped, "failed": failed}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Quick local test (requires backend running)
    test_story = {
        "headline": "Test: Kenya Economy Grows by 5 Percent",
        "summary": "Kenya's GDP grew by 5% per the latest World Bank report.",
        "bullets": ["GDP grew 5%", "World Bank report confirmed the figures."],
        "link": "https://example.com/story/1",
        "image": None,
        "category": "Business",
        "source": "Standard Media",
        "verified_sources": ["Standard Media", "BBC Africa"],
        "confidence": 0.8,
        "timestamp": "2024-06-01 10:00",
    }
    publish_story(test_story)
