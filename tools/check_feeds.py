"""Simple utility to check RSS_FEEDS and optionally fetch article text.

Usage:
    python tools/check_feeds.py            # just list feed meta
    python tools/check_feeds.py --fetch   # also try to download/parse article text
    python tools/check_feeds.py --feed 0  # check only feed at index 0
    python tools/check_feeds.py --max 5   # show up to 5 entries per feed
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Iterable

import feedparser

from config import RSS_FEEDS

try:
    from services.content_fetcher import fetch_article_text
except Exception:  # pragma: no cover - optional dependency
    fetch_article_text = None


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def print_entry(entry: feedparser.util.FeedParserDict, index: int, fetch: bool = False):
    title = entry.get("title", "<no title>")
    link = entry.get("link", "<no link>")
    published = entry.get("published", entry.get("updated", "<no date>"))

    print(f"[{index}] {title}")
    print(f"    link: {link}")
    print(f"    date: {published}")

    if fetch:
        if not fetch_article_text:
            print("    fetch_article_text helper not available; skipping text fetch.")
            return

        print("    fetching article text (this may take a moment)...")
        text = fetch_article_text(link)
        if text:
            snippet = text[:400].replace("\n", " ").strip()
            print(f"    text snippet: {snippet}...")
        else:
            print("    failed to fetch/parse article text (fetch_article_text returned None)")


def check_feed(url: str, max_entries: int, fetch: bool):
    d = feedparser.parse(url)

    print(f"\nChecking feed: {url}")
    if d.bozo:
        logging.warning("feedparser reported a problem parsing this feed (bozo=True).")
    print(f"Feed title: {d.feed.get('title', '<no title>')}")
    print(f"Entries found: {len(d.entries)}")

    for i, entry in enumerate(d.entries[:max_entries], start=1):
        print_entry(entry, i, fetch)


def parse_args(argv: Iterable[str] | None = None):
    parser = argparse.ArgumentParser(description="Check RSS feeds and optionally fetch article text.")
    parser.add_argument("--fetch", action="store_true", help="Attempt to fetch article text for each entry")
    parser.add_argument("--max", type=int, default=3, help="Max entries to display per feed (default 3)")
    parser.add_argument(
        "--feed", type=int, default=None, help="Index of feed to check (0-based). Omit to check all feeds"
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Iterable[str] | None = None):
    args = parse_args(argv)

    feeds = RSS_FEEDS
    if args.feed is not None:
        try:
            feeds = [RSS_FEEDS[args.feed]]
        except Exception as exc:  # pragma: no cover - user error
            logging.error("Invalid feed index %s: %s", args.feed, exc)
            return 2

    for url in feeds:
        check_feed(url, args.max, args.fetch)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
