"""
KenyaNews — main.py (pipeline entry point)
Orchestrates: scrape → verify → summarise → publish → notify
Run by GitHub Actions every 10 minutes.
"""

import logging
import sys
from scraper        import run_scraper
from social_scraper import run_social_scraper
from verifier       import verify_stories
from summarizer     import summarise_all
from publisher      import publish_all
from notifier       import send_digest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 60)
    logger.info("  KenyaNews Pipeline — Starting")
    logger.info("=" * 60)

    # 1. Scrape (news + social in parallel)
    logger.info("\n[1/5] SCRAPING …")
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_news   = executor.submit(run_scraper)
        future_social = executor.submit(run_social_scraper)
        raw_stories  = future_news.result()
        social_posts = future_social.result()

    if not raw_stories:
        logger.warning("No stories scraped. Exiting.")
        return

    # 2. Verify (cross-source + social signals)
    logger.info("\n[2/5] VERIFYING …")
    verified = verify_stories(raw_stories, social_posts=social_posts)
    if not verified:
        logger.warning("No stories passed verification. Exiting.")
        return

    # 3. Summarise
    logger.info("\n[3/5] SUMMARISING …")
    summarised = summarise_all(verified)

    # 4. Publish
    logger.info("\n[4/5] PUBLISHING …")
    stats = publish_all(summarised)

    # 5. Notify (only if we actually published new stories)
    if stats["published"] > 0:
        logger.info(f"\n[5/5] NOTIFYING — {stats['published']} new stories …")
        send_digest(summarised)
    else:
        logger.info("\n[5/5] No new stories published — skipping email.")

    logger.info("\n" + "=" * 60)
    logger.info(f"  Pipeline complete → {stats}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
