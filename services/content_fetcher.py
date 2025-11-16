"""Utilities for fetching article content and related assets."""

from __future__ import annotations

import logging
from io import BytesIO
from typing import Tuple

import requests
from newspaper import Article


DEFAULT_IMAGE_MAX_BYTES = 7_000_000  # stay below Discord's ~8 MiB limit


def fetch_article_text(url: str) -> str | None:
    """Download and parse an article to extract its text."""
    text, _ = fetch_article_with_image(url)
    return text


def fetch_article_with_image(url: str) -> Tuple[str | None, str | None]:
    """Download article content, returning (text, top_image_url)."""
    try:
        article = Article(url)
        article.download()
        article.parse()
        text = article.text or None
        top_image = getattr(article, "top_image", None) or None
        return text, top_image
    except Exception as exc:  # pylint: disable=broad-except
        logging.error("Failed to scrape article at %s: %s", url, exc)
        return None, None


def download_image(url: str, *, max_bytes: int = DEFAULT_IMAGE_MAX_BYTES) -> bytes | None:
    """Download image bytes, enforcing a max size to satisfy Discord limits."""
    try:
        response = requests.get(url, timeout=10, stream=True)
        response.raise_for_status()

        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > max_bytes:
            logging.warning("Skipping image at %s because it exceeds %s bytes", url, max_bytes)
            return None

        buffer = BytesIO()
        for chunk in response.iter_content(chunk_size=8192):
            if not chunk:
                continue
            buffer.write(chunk)
            if buffer.tell() > max_bytes:
                logging.warning("Skipping image at %s due to size over %s bytes", url, max_bytes)
                return None

        if buffer.tell() == 0:
            logging.warning("No data downloaded for image at %s", url)
            return None

        return buffer.getvalue()
    except Exception as exc:  # pylint: disable=broad-except
        logging.error("Failed to download image at %s: %s", url, exc)
        return None
