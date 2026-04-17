"""
KenyaNews Scraper — scraper.py
Scrapes RSS feeds from trusted Kenyan and global news sources.
Extracts headlines, article body, images, and metadata.
"""

import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import logging
import time
import re
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# RSS Feed Sources
# ─────────────────────────────────────────
RSS_SOURCES = {
    "Standard Media": {
        "url": "https://www.standardmedia.co.ke/rss/headlines.php",
        "category": "Kenya",
    },
    "Kenyans.co.ke": {
        "url": "https://www.kenyans.co.ke/feeds/news",
        "category": "Kenya",
    },
    "Kenya News Agency": {
        "url": "https://kenyanews.go.ke/feed",
        "category": "Kenya",
    },
    "Nation Africa": {
        "url": "https://nation.africa/rss",
        "category": "Kenya",
    },
    "Citizen Digital": {
        "url": "https://citizen.digital/feed",
        "category": "Kenya",
    },
    "Google News Kenya": {
        "url": "https://news.google.com/rss/search?q=kenya&hl=en-KE&gl=KE&ceid=KE:en",
        "category": "Kenya",
    },
    "BBC Africa": {
        "url": "https://feeds.bbci.co.uk/news/world/africa/rss.xml",
        "category": "Africa",
    },
    "Reuters Africa": {
        "url": "https://feeds.reuters.com/reuters/AFRICANews",
        "category": "Africa",
    },
    "Al Jazeera": {
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "category": "World",
    },
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────

def clean_text(text: str) -> str:
    """Strip HTML tags and normalise whitespace."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_image_from_entry(entry, article_url: str) -> Optional[str]:
    """Try several strategies to find an image URL for the story."""
    # 1. media:content / media:thumbnail
    for attr in ("media_content", "media_thumbnail"):
        media = getattr(entry, attr, None)
        if media and isinstance(media, list) and media[0].get("url"):
            return media[0]["url"]

    # 2. enclosure links
    for link in getattr(entry, "links", []):
        if link.get("type", "").startswith("image"):
            return link.get("href")

    # 3. Scrape article page for og:image
    try:
        resp = requests.get(article_url, headers=HEADERS, timeout=8)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "lxml")
            og = soup.find("meta", property="og:image")
            if og and og.get("content"):
                return og["content"]
            # fallback: first <img src>
            img = soup.find("img", src=True)
            if img:
                return img["src"]
    except Exception:
        pass

    return None


def fetch_article_body(url: str) -> str:
    """Fetch full article text for summarisation."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return ""
        soup = BeautifulSoup(resp.text, "lxml")

        # Remove noise
        for tag in soup(["script", "style", "nav", "header", "footer",
                          "aside", "form", "iframe", "noscript"]):
            tag.decompose()

        # Common article container selectors
        for selector in ["article", "[class*='article-body']",
                          "[class*='story-body']", "[class*='post-content']",
                          "main", ".content"]:
            container = soup.select_one(selector)
            if container:
                paragraphs = container.find_all("p")
                text = " ".join(p.get_text() for p in paragraphs)
                if len(text) > 200:
                    return clean_text(text)

        # Last resort: all paragraphs
        paragraphs = soup.find_all("p")
        return clean_text(" ".join(p.get_text() for p in paragraphs))

    except Exception as e:
        logger.warning(f"Could not fetch article body from {url}: {e}")
        return ""


# ─────────────────────────────────────────
# Main Scraper
# ─────────────────────────────────────────

def scrape_feed(source_name: str, source_info: dict) -> list[dict]:
    """Parse a single RSS feed and return a list of raw story dicts."""
    url = source_info["url"]
    category = source_info["category"]
    stories = []

    logger.info(f"Scraping: {source_name}")
    try:
        feed = feedparser.parse(url)
        if feed.bozo and not feed.entries:
            logger.warning(f"Feed error for {source_name}: {feed.bozo_exception}")
            return []

        for entry in feed.entries[:10]:  # cap at 10 per source per run
            headline = clean_text(getattr(entry, "title", ""))
            link = getattr(entry, "link", "")
            published_raw = getattr(entry, "published", "")

            if not headline or not link:
                continue

            # Parse publish date
            try:
                from email.utils import parsedate_to_datetime
                timestamp = parsedate_to_datetime(published_raw).strftime("%Y-%m-%d %H:%M")
            except Exception:
                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

            # Snippet / description
            description = clean_text(
                getattr(entry, "summary", "") or getattr(entry, "description", "")
            )

            story = {
                "headline": headline,
                "description": description,
                "link": link,
                "source": source_name,
                "category": category,
                "timestamp": timestamp,
                "image": None,   # filled later
                "body": "",      # filled later
            }
            stories.append(story)

    except Exception as e:
        logger.error(f"Failed to scrape {source_name}: {e}")

    return stories


def enrich_story(story: dict) -> dict:
    """Fetch full body text and image for a story."""
    url = story["link"]
    story["body"] = fetch_article_body(url) or story["description"]
    story["image"] = extract_image_from_entry(object(), url)  # placeholder entry
    time.sleep(0.5)  # polite delay
    return story


def run_scraper() -> list[dict]:
    """Run all scrapers and return enriched raw stories."""
    all_stories = []
    for source_name, source_info in RSS_SOURCES.items():
        stories = scrape_feed(source_name, source_info)
        all_stories.extend(stories)
        time.sleep(1)  # polite between feeds

    logger.info(f"Total raw stories scraped: {len(all_stories)}")

    # Enrich top 30 only (to stay within GitHub Actions time)
    enriched = []
    for story in all_stories[:30]:
        enriched.append(enrich_story(story))

    logger.info(f"Enriched stories: {len(enriched)}")
    return enriched


if __name__ == "__main__":
    stories = run_scraper()
    for s in stories[:3]:
        print(f"\n{'='*60}")
        print(f"Headline : {s['headline']}")
        print(f"Source   : {s['source']}")
        print(f"Category : {s['category']}")
        print(f"Timestamp: {s['timestamp']}")
        print(f"Link     : {s['link']}")
        print(f"Image    : {s['image']}")
        print(f"Body     : {s['body'][:300]}...")
