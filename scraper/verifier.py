"""
KenyaNews — verifier.py
Cross-checks scraped stories against multiple sources.
Uses headline keyword overlap (Jaccard similarity) to confirm relevance.
Also uses social media signals (Twitter/X, Reddit, Telegram) to boost confidence.
Only stories verified by ≥2 independent sources are passed forward.
"""

import re
import logging
from social_scraper import get_social_mentions
from collections import defaultdict
from typing import Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# Stop-words to ignore in keyword matching
# ─────────────────────────────────────────
STOP_WORDS = {
    "the", "a", "an", "is", "in", "on", "at", "of", "to", "and", "or",
    "but", "for", "with", "by", "from", "as", "that", "this", "it",
    "was", "be", "are", "were", "has", "have", "had", "will", "would",
    "could", "should", "may", "its", "his", "her", "their", "our",
    "says", "said", "after", "over", "into", "about", "up", "out",
    "than", "more", "he", "she", "we", "they", "who", "how", "why",
    "what", "when", "where", "new", "government", "kenya", "kenyan",
}

MIN_JACCARD = 0.12        # minimum similarity score to consider a match
MIN_SOURCES  = 2          # stories must appear in at least this many sources
MAX_STORIES  = 20         # cap final output


# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────

def tokenise(text: str) -> set[str]:
    """Lowercase alphanumeric tokens, minus stop-words."""
    tokens = re.findall(r"[a-z]+", text.lower())
    return {t for t in tokens if t not in STOP_WORDS and len(t) > 2}


def jaccard_similarity(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union if union else 0.0


def normalise_headline(headline: str) -> str:
    """Remove punctuation and lowercase for grouping."""
    return re.sub(r"[^\w\s]", "", headline.lower()).strip()


# ─────────────────────────────────────────
# Cluster stories by topic similarity
# ─────────────────────────────────────────

def cluster_stories(stories: list[dict]) -> dict[int, list[dict]]:
    """
    Group stories into topic clusters using greedy Jaccard matching.
    Returns {cluster_id: [story, ...]}
    """
    clusters: dict[int, list[dict]] = {}
    cluster_tokens: dict[int, set] = {}
    cluster_id = 0

    for story in stories:
        tokens = tokenise(story["headline"] + " " + story.get("description", ""))
        matched_cluster: Optional[int] = None
        best_score = 0.0

        for cid, ctokens in cluster_tokens.items():
            score = jaccard_similarity(tokens, ctokens)
            if score >= MIN_JACCARD and score > best_score:
                best_score = score
                matched_cluster = cid

        if matched_cluster is not None:
            clusters[matched_cluster].append(story)
            # Expand cluster tokens with new words
            cluster_tokens[matched_cluster] |= tokens
        else:
            clusters[cluster_id] = [story]
            cluster_tokens[cluster_id] = tokens
            cluster_id += 1

    return clusters


# ─────────────────────────────────────────
# Main Verifier
# ─────────────────────────────────────────

def verify_stories(raw_stories: list[dict], social_posts: list[dict] = None) -> list[dict]:
    """
    Filter raw stories to only those confirmed by ≥2 independent sources.
    Optionally boosts confidence using social media mentions.
    Returns a deduplicated, verified list of stories (best representative per cluster).
    """
    logger.info(f"Verifying {len(raw_stories)} raw stories…")
    clusters = cluster_stories(raw_stories)
    verified = []

    for cid, cluster in clusters.items():
        # Count distinct sources
        sources = {s["source"] for s in cluster}
        source_count = len(sources)

        if source_count >= MIN_SOURCES:
            # Pick the story with the longest body as the representative
            best = max(cluster, key=lambda s: len(s.get("body", "")))
            best["verified_sources"] = list(sources)
            best["source_count"] = source_count

            # Boost confidence with social media mentions
            social_mentions = []
            if social_posts:
                social_mentions = get_social_mentions(best["headline"], social_posts)
            social_boost = min(0.2, len(social_mentions) * 0.04)
            base_confidence = min(0.8, source_count / 5)
            best["confidence"] = round(min(1.0, base_confidence + social_boost), 2)
            best["social_mentions"] = len(social_mentions)
            best["social_platforms"] = list({m["platform"] for m in social_mentions})

            verified.append(best)
            logger.info(
                f"✓ Verified [{source_count} sources, {len(social_mentions)} social]: "
                f"{best['headline'][:60]}"
            )
        else:
            logger.debug(
                f"✗ Skipped (only {source_count} source): {cluster[0]['headline'][:70]}"
            )

    # Sort by source_count desc, then timestamp desc
    verified.sort(key=lambda s: (s["source_count"], s["timestamp"]), reverse=True)
    verified = verified[:MAX_STORIES]

    logger.info(f"Verification complete: {len(verified)} stories passed.")
    return verified


if __name__ == "__main__":
    # Quick smoke-test
    sample = [
        {"headline": "Ruto signs new finance bill", "description": "President Ruto signed the finance bill today amid protests.", "source": "Standard Media", "body": "Long text...", "category": "Kenya", "timestamp": "2024-06-01 10:00", "link": "https://example.com/1", "image": None},
        {"headline": "Kenya finance bill signed by Ruto", "description": "Kenya's president signed the contentious finance bill.", "source": "BBC Africa", "body": "Long text...", "category": "Africa", "timestamp": "2024-06-01 10:05", "link": "https://example.com/2", "image": None},
        {"headline": "Manchester United loses again", "description": "Man Utd suffered another defeat at Old Trafford.", "source": "Kenyans.co.ke", "body": "Short text.", "category": "Sports", "timestamp": "2024-06-01 10:10", "link": "https://example.com/3", "image": None},
    ]
    result = verify_stories(sample)
    for s in result:
        print(s["headline"], "→ sources:", s["verified_sources"])
