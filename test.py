"""Utility script for manually testing the AI services and content fetching."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

import feedparser

from config import RSS_FEEDS, YOUTUBE_CHANNEL_FEEDS
from services.ai_services import get_ai_summary, get_gemini_summary
from services.content_fetcher import download_image, fetch_article_with_image


async def test_content_fetching() -> tuple[Optional[str], Optional[str]]:
    """Fetch text and top image from the first configured RSS feed."""
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

    article_text, top_image_url = await asyncio.to_thread(fetch_article_with_image, article_link)
    if not article_text:
        logging.error("Failed to fetch article text from %s", article_link)
        return None, None

    logging.info("Fetched article text (%s characters)", len(article_text))
    print("\nArticle snippet:\n", article_text[:400], "...", sep="")
    if top_image_url:
        logging.info("Article top image: %s", top_image_url)
    else:
        logging.warning("Article did not provide a top image")
    return article_text, top_image_url


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


async def test_image_download(top_image_url: Optional[str]) -> None:
    """Download the article top image to validate downloader behavior."""
    if not top_image_url:
        logging.warning("Skipping image download test because no top image was provided.")
        return

    logging.info("Downloading image from: %s", top_image_url)
    image_bytes = await asyncio.to_thread(download_image, top_image_url)
    if not image_bytes:
        logging.error("Image download failed for %s", top_image_url)
        return

    logging.info("Downloaded image (%s bytes)", len(image_bytes))
    print("First 100 bytes:", image_bytes[:100])


async def test_youtube_thumbnail_extraction() -> Optional[str]:
    """Extract the first thumbnail URL from the first configured YouTube feed."""
    if not YOUTUBE_CHANNEL_FEEDS:
        logging.error("YOUTUBE_CHANNEL_FEEDS is empty. Update config.py before running this test.")
        return None

    feed_url = YOUTUBE_CHANNEL_FEEDS[0]
    logging.info("Parsing YouTube feed for thumbnail test: %s", feed_url)
    feed = await asyncio.to_thread(feedparser.parse, feed_url)

    if not feed.entries:
        logging.error("No videos found in YouTube feed: %s", feed_url)
        return None

    entry = feed.entries[0]
    thumbnail_url = None
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        thumbnail_url = entry.media_thumbnail[0].get("url")
    elif hasattr(entry, "media_content") and entry.media_content:
        thumbnail_url = entry.media_content[0].get("url")
    else:
        thumbnail_url = entry.get("thumbnail")

    if thumbnail_url:
        logging.info("Found YouTube thumbnail: %s", thumbnail_url)
    else:
        logging.warning("No thumbnail found for first YouTube entry.")

    return thumbnail_url


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
    article_text, article_image = await test_content_fetching()
    await test_ai_summary(article_text)
    await test_image_download(article_image)
    await test_youtube_thumbnail_extraction()
    await test_gemini_summary()
    print("\nAll tests complete.")


if __name__ == "__main__":
    asyncio.run(main())
