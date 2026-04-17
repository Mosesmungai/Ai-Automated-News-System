"""
KenyaNews — social_scraper.py
Scrapes social media platforms for trending Kenyan news mentions.

Platforms:
  1. Twitter/X  — via free public Nitter instances (no API key required)
  2. Reddit     — via Reddit JSON API (no API key required for read-only)
  3. Telegram   — via public channel preview pages (t.me)

Results are used by verifier.py to boost story confidence scores.
"""

import requests
import re
import logging
import time
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# ─────────────────────────────────────────
# 1. Twitter/X — via Nitter (free, no API key)
#    Nitter is an open-source Twitter front-end.
#    We rotate through public instances in case one is down.
# ─────────────────────────────────────────

NITTER_INSTANCES = [
    "https://nitter.poast.org",
    "https://nitter.privacydev.net",
    "https://nitter.1d4.us",
    "https://nitter.kavin.rocks",
]

TWITTER_SEARCH_TERMS = [
    "Kenya news",
    "Kenya breaking",
    "#KenyaNews",
    "#Kenya",
    "Nairobi",
    "Ruto",
    "Kenya economy",
]

# Kenyan news Twitter accounts to scrape timelines
KENYA_TWITTER_ACCOUNTS = [
    "StandardKenya",
    "citizentvkenya",
    "NationAfrica",
    "KTNNewsKE",
    "ntvkenya",
]


def _get_working_nitter() -> Optional[str]:
    """Return the first reachable Nitter instance."""
    for instance in NITTER_INSTANCES:
        try:
            r = requests.get(instance, headers=HEADERS, timeout=6)
            if r.status_code == 200:
                return instance
        except Exception:
            continue
    logger.warning("No Nitter instances reachable — Twitter scrape skipped.")
    return None


def scrape_nitter_search(query: str, base_url: str, max_items: int = 10) -> list[dict]:
    """Scrape Nitter search results for a given query."""
    results = []
    url = f"{base_url}/search?f=tweets&q={requests.utils.quote(query)}&since=&until=&near="
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "lxml")
        tweets = soup.select(".timeline-item")
        for tweet in tweets[:max_items]:
            content_el = tweet.select_one(".tweet-content")
            time_el    = tweet.select_one(".tweet-date a")
            user_el    = tweet.select_one(".username")
            if not content_el:
                continue
            text = content_el.get_text(separator=" ").strip()
            link = (base_url + time_el["href"]) if time_el and time_el.get("href") else ""
            user = user_el.get_text().strip() if user_el else "unknown"
            results.append({
                "platform": "Twitter/X",
                "text": text,
                "user": user,
                "link": link,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
            })
    except Exception as e:
        logger.debug(f"Nitter search error ({query}): {e}")
    return results


def scrape_nitter_account(account: str, base_url: str, max_items: int = 5) -> list[dict]:
    """Scrape a Kenyan news account's recent tweets from Nitter."""
    results = []
    url = f"{base_url}/{account}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "lxml")
        tweets = soup.select(".timeline-item")
        for tweet in tweets[:max_items]:
            content_el = tweet.select_one(".tweet-content")
            if not content_el:
                continue
            text = content_el.get_text(separator=" ").strip()
            results.append({
                "platform": "Twitter/X",
                "text": text,
                "user": f"@{account}",
                "link": url,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
            })
    except Exception as e:
        logger.debug(f"Nitter account error ({account}): {e}")
    return results


def scrape_twitter() -> list[dict]:
    """Master Twitter scraper: searches + account timelines via Nitter."""
    base = _get_working_nitter()
    if not base:
        return []

    all_tweets = []

    # Search trending terms
    for term in TWITTER_SEARCH_TERMS[:4]:  # limit to 4 searches
        tweets = scrape_nitter_search(term, base, max_items=8)
        all_tweets.extend(tweets)
        time.sleep(1)

    # Account timelines
    for account in KENYA_TWITTER_ACCOUNTS:
        tweets = scrape_nitter_account(account, base, max_items=5)
        all_tweets.extend(tweets)
        time.sleep(0.8)

    logger.info(f"Twitter/X: {len(all_tweets)} posts collected.")
    return all_tweets


# ─────────────────────────────────────────
# 2. Reddit — via free JSON API (no auth needed)
# ─────────────────────────────────────────

REDDIT_SUBREDDITS = [
    "Kenya",
    "Africa",
    "worldnews",
    "nairobi",
]

REDDIT_SEARCH_TERMS = ["Kenya", "Nairobi", "East Africa"]


def scrape_reddit_subreddit(subreddit: str, limit: int = 10) -> list[dict]:
    """Fetch hot posts from a subreddit using Reddit's free JSON API."""
    results = []
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
    try:
        resp = requests.get(url, headers={**HEADERS, "Accept": "application/json"}, timeout=10)
        if resp.status_code != 200:
            return []
        data = resp.json()
        posts = data.get("data", {}).get("children", [])
        for post in posts:
            p = post.get("data", {})
            title = p.get("title", "").strip()
            selftext = p.get("selftext", "").strip()
            link = "https://reddit.com" + p.get("permalink", "")
            score = p.get("score", 0)
            if score < 5:  # skip very low-engagement posts
                continue
            results.append({
                "platform": "Reddit",
                "text": title + (" — " + selftext[:200] if selftext else ""),
                "user": p.get("author", "unknown"),
                "link": link,
                "score": score,
                "subreddit": subreddit,
                "timestamp": datetime.fromtimestamp(
                    p.get("created_utc", 0), tz=timezone.utc
                ).strftime("%Y-%m-%d %H:%M"),
            })
    except Exception as e:
        logger.debug(f"Reddit error ({subreddit}): {e}")
    return results


def scrape_reddit_search(query: str, limit: int = 8) -> list[dict]:
    """Search Reddit for a keyword using the free JSON API."""
    results = []
    url = f"https://www.reddit.com/search.json?q={requests.utils.quote(query)}&sort=new&limit={limit}"
    try:
        resp = requests.get(url, headers={**HEADERS, "Accept": "application/json"}, timeout=10)
        if resp.status_code != 200:
            return []
        data = resp.json()
        posts = data.get("data", {}).get("children", [])
        for post in posts:
            p = post.get("data", {})
            results.append({
                "platform": "Reddit",
                "text": p.get("title", "").strip(),
                "user": p.get("author", "unknown"),
                "link": "https://reddit.com" + p.get("permalink", ""),
                "score": p.get("score", 0),
                "timestamp": datetime.fromtimestamp(
                    p.get("created_utc", 0), tz=timezone.utc
                ).strftime("%Y-%m-%d %H:%M"),
            })
    except Exception as e:
        logger.debug(f"Reddit search error ({query}): {e}")
    return results


def scrape_reddit() -> list[dict]:
    """Master Reddit scraper: hot posts + keyword searches."""
    all_posts = []
    for sub in REDDIT_SUBREDDITS:
        posts = scrape_reddit_subreddit(sub, limit=10)
        all_posts.extend(posts)
        time.sleep(1)
    for term in REDDIT_SEARCH_TERMS:
        posts = scrape_reddit_search(term, limit=8)
        all_posts.extend(posts)
        time.sleep(1)
    logger.info(f"Reddit: {len(all_posts)} posts collected.")
    return all_posts


# ─────────────────────────────────────────
# 3. Telegram — via public preview pages (t.me)
#    Scrapes public Kenyan news Telegram channels
# ─────────────────────────────────────────

TELEGRAM_CHANNELS = [
    "KenyaNewsUpdates",
    "standardkenya",
    "citizentvkenya",
    "nairobiupdates",
    "kenyabreaking",
]


def scrape_telegram_channel(channel: str, max_items: int = 8) -> list[dict]:
    """Scrape a public Telegram channel's t.me preview page."""
    results = []
    url = f"https://t.me/s/{channel}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "lxml")
        messages = soup.select(".tgme_widget_message_text")
        dates    = soup.select(".tgme_widget_message_date time")
        for i, msg in enumerate(messages[:max_items]):
            text = msg.get_text(separator=" ").strip()
            ts_raw = dates[i]["datetime"] if i < len(dates) and dates[i].get("datetime") else ""
            try:
                ts = datetime.fromisoformat(ts_raw).strftime("%Y-%m-%d %H:%M")
            except Exception:
                ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
            if len(text) < 20:
                continue
            results.append({
                "platform": "Telegram",
                "text": text,
                "user": f"@{channel}",
                "link": f"https://t.me/{channel}",
                "timestamp": ts,
            })
    except Exception as e:
        logger.debug(f"Telegram error ({channel}): {e}")
    return results


def scrape_telegram() -> list[dict]:
    """Master Telegram scraper."""
    all_posts = []
    for ch in TELEGRAM_CHANNELS:
        posts = scrape_telegram_channel(ch)
        all_posts.extend(posts)
        time.sleep(1)
    logger.info(f"Telegram: {len(all_posts)} posts collected.")
    return all_posts


# ─────────────────────────────────────────
# Master social media runner
# ─────────────────────────────────────────

def run_social_scraper() -> list[dict]:
    """
    Run all social media scrapers and return a unified list of posts.
    Each post has: platform, text, user, link, timestamp.
    """
    logger.info("Running social media scrapers …")
    all_social = []

    twitter  = scrape_twitter()
    all_social.extend(twitter)

    reddit   = scrape_reddit()
    all_social.extend(reddit)

    telegram = scrape_telegram()
    all_social.extend(telegram)

    logger.info(f"Social media total: {len(all_social)} posts "
                f"(Twitter={len(twitter)}, Reddit={len(reddit)}, Telegram={len(telegram)})")
    return all_social


# ─────────────────────────────────────────
# Social signal matcher (used by verifier)
# ─────────────────────────────────────────

def get_social_mentions(headline: str, social_posts: list[dict]) -> list[dict]:
    """
    Return social posts that mention keywords from a headline.
    Used by verifier.py to boost confidence of news stories.
    """
    keywords = set(re.findall(r"[a-z]{4,}", headline.lower()))
    keywords -= {"that", "this", "with", "from", "they", "were", "have", "been",
                 "will", "said", "says", "news", "also", "more", "over", "into"}
    matches = []
    for post in social_posts:
        post_text = post["text"].lower()
        matched = sum(1 for kw in keywords if kw in post_text)
        if matched >= 2:
            matches.append({**post, "keyword_matches": matched})
    return matches


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    posts = run_social_scraper()
    print(f"\nTotal social posts: {len(posts)}")
    for p in posts[:5]:
        print(f"[{p['platform']}] {p['text'][:100]}")
