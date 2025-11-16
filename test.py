"""Utility script for manually testing the AI services and content fetching."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import feedparser

from config import RSS_FEEDS, YOUTUBE_CHANNEL_FEEDS
from services.ai_services import get_ai_summary, get_gemini_summary
from services.content_fetcher import fetch_article_text


async def test_content_fetching() -> Optional[str]:
    """Fetch text from the first configured RSS feed."""
    if not RSS_FEEDS:
        logging.error("RSS_FEEDS is empty. Update config.py before running this test.")
        return None

    feed_url = RSS_FEEDS[0]
    logging.info("Parsing RSS feed: %s", feed_url)
    feed = await asyncio.to_thread(feedparser.parse, feed_url)

    if not feed.entries:
        logging.error("No entries found in feed: %s", feed_url)
        return None

    entry = feed.entries[0]
    article_link = entry.link
    logging.info("Fetching article text from: %s", article_link)

    article_text = await asyncio.to_thread(fetch_article_text, article_link)
    if not article_text:
        logging.error("Failed to fetch article text from %s", article_link)
        return None

    logging.info("Fetched article text (%s characters)", len(article_text))
    print("\nArticle snippet:\n", article_text[:400], "...", sep="")
    return article_text


async def test_ai_summary(article_text: Optional[str]) -> None:
    """Test the OpenAI summarizer using provided article text."""
    if not article_text:
        logging.warning("Skipping OpenAI summary test because article text is missing.")
        return

    logging.info("Requesting OpenAI summary...")
    summary = await asyncio.to_thread(get_ai_summary, article_text)
    if summary:
        print("\nOpenAI Summary:\n", summary)
    else:
        logging.error("OpenAI summary failed.")


async def test_gemini_summary() -> None:
    """Test the Gemini video summarizer using the first configured YouTube feed."""
    if not YOUTUBE_CHANNEL_FEEDS:
        logging.error("YOUTUBE_CHANNEL_FEEDS is empty. Update config.py before running this test.")
        return

    feed_url = YOUTUBE_CHANNEL_FEEDS[0]
    logging.info("Parsing YouTube feed: %s", feed_url)
    feed = await asyncio.to_thread(feedparser.parse, feed_url)

    if not feed.entries:
        logging.error("No videos found in YouTube feed: %s", feed_url)
        return

    video_link = feed.entries[0].link
    logging.info("Requesting Gemini summary for video: %s", video_link)

    summary = await asyncio.to_thread(get_gemini_summary, video_link)
    if summary:
        print("\nGemini Summary:\n", summary)
    else:
        logging.error("Gemini summary failed.")


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    print("Starting service tests...\n")
    article_text = await test_content_fetching()
    await test_ai_summary(article_text)
    await test_gemini_summary()
    print("\nAll tests complete.")


if __name__ == "__main__":
    asyncio.run(main())
