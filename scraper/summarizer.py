"""
KenyaNews — summarizer.py
Summarises verified stories using Hugging Face BART (facebook/bart-large-cnn).
Falls back to extractive summarisation if model load fails.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# Model loader (lazy – avoids loading on import)
# ─────────────────────────────────────────

_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        try:
            from transformers import pipeline
            logger.info("Loading facebook/bart-large-cnn …")
            _pipeline = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                tokenizer="facebook/bart-large-cnn",
                device=-1,          # CPU only (free tier)
            )
            logger.info("Model loaded.")
        except Exception as e:
            logger.warning(f"Could not load BART: {e}. Using extractive fallback.")
            _pipeline = "fallback"
    return _pipeline


# ─────────────────────────────────────────
# Extractive fallback (no GPU/model needed)
# ─────────────────────────────────────────

def extractive_summary(text: str, max_sentences: int = 3) -> str:
    """
    Simple extractive summary: returns the first N meaningful sentences.
    Used as fallback when the Hugging Face model cannot be loaded.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    # Filter very short fragments
    sentences = [s for s in sentences if len(s.split()) > 6]
    summary = " ".join(sentences[:max_sentences])
    return summary or text[:500]


# ─────────────────────────────────────────
# Bullet-point formatter
# ─────────────────────────────────────────

def format_as_bullets(summary_text: str) -> list[str]:
    """Split summary into bullet points at sentence boundaries."""
    sentences = re.split(r"(?<=[.!?])\s+", summary_text.strip())
    bullets = [s.strip() for s in sentences if len(s.strip()) > 10]
    return bullets[:4]  # max 4 bullets


# ─────────────────────────────────────────
# Core summariser
# ─────────────────────────────────────────

def summarise_story(story: dict) -> dict:
    """
    Adds 'summary' (string) and 'bullets' (list[str]) keys to the story dict.
    Input text is the article body; falls back to description if body is short.
    """
    text = story.get("body", "") or story.get("description", "")
    text = text.strip()

    # Ensure minimum length for BART (needs ≥ ~60 words)
    word_count = len(text.split())

    if word_count < 30:
        summary_text = text or story.get("headline", "")
        story["summary"] = summary_text
        story["bullets"] = [summary_text]
        return story

    pipe = get_pipeline()

    if pipe == "fallback" or word_count < 60:
        summary_text = extractive_summary(text)
    else:
        try:
            # BART input cap: 1024 tokens — truncate ~3000 chars
            input_text = text[:3000]
            result = pipe(
                input_text,
                max_length=180,
                min_length=60,
                do_sample=False,
                truncation=True,
            )
            summary_text = result[0]["summary_text"]
        except Exception as e:
            logger.warning(f"BART inference failed: {e}. Using extractive fallback.")
            summary_text = extractive_summary(text)

    story["summary"] = summary_text
    story["bullets"] = format_as_bullets(summary_text)
    return story


def summarise_all(stories: list[dict]) -> list[dict]:
    """Summarise a list of verified stories."""
    logger.info(f"Summarising {len(stories)} stories …")
    summarised = []
    for i, story in enumerate(stories, 1):
        try:
            summarised.append(summarise_story(story))
            logger.info(f"  [{i}/{len(stories)}] ✓ {story['headline'][:60]}")
        except Exception as e:
            logger.error(f"  [{i}/{len(stories)}] ✗ Failed: {e}")
            story["summary"] = story.get("description", story.get("headline", ""))
            story["bullets"] = [story["summary"]]
            summarised.append(story)
    logger.info("Summarisation complete.")
    return summarised


if __name__ == "__main__":
    sample = [{
        "headline": "Kenya Signs New Climate Deal",
        "description": "Kenya has signed a landmark climate deal at the UN summit.",
        "body": (
            "Kenyan President William Ruto signed a landmark climate agreement "
            "at the United Nations Climate Summit in New York on Thursday. "
            "The deal commits Kenya to a 30 percent reduction in carbon emissions "
            "by 2030 and unlocks $1.5 billion in green financing from international partners. "
            "Environment Cabinet Secretary Soipan Tuya called the agreement a historic step "
            "for the country. Kenya already generates over 90 percent of its electricity "
            "from renewable sources, making it one of Africa's leaders in clean energy. "
            "The funds will be directed toward reforestation, geothermal expansion, "
            "and drought-resilient agriculture programmes. Critics warn that implementation "
            "timelines remain vague and call for stronger accountability mechanisms."
        ),
    }]
    result = summarise_all(sample)
    print("Summary:", result[0]["summary"])
    print("Bullets:", result[0]["bullets"])
