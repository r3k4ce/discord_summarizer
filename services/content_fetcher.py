"""Utilities for fetching article content."""

import logging
from newspaper import Article


def fetch_article_text(url: str) -> str | None:
    """Download and parse an article to extract its text."""
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as exc:  # pylint: disable=broad-except
        logging.error("Failed to scrape article at %s: %s", url, exc)
        return None
