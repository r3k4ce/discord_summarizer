"""Text command cog for YouTube summarization (prefix commands)."""

from __future__ import annotations

import asyncio
import logging
from io import BytesIO
from typing import Any

import discord
import feedparser
from discord.ext import commands

from config import YOUTUBE_CHANNEL_FEEDS
from services.ai_services import get_gemini_summary
from services.content_fetcher import download_image


def _extract_thumbnail_url(entry: feedparser.FeedParserDict) -> str | None:
    """Return the first available thumbnail/media URL from a feed entry."""
    possible_lists: list[Any] = []
    for attr in ("media_thumbnail", "media_content"):
        value = getattr(entry, attr, None)
        if value:
            possible_lists.append(value)
        if attr in entry:
            possible_lists.append(entry[attr])

    for items in possible_lists:
        if not items:
            continue
        if isinstance(items, dict):
            items = [items]
        for item in items:
            if not isinstance(item, dict):
                continue
            url = item.get("url") or item.get("@url")
            if url:
                return url

    # Generic fallbacks
    return entry.get("thumbnail") or entry.get("media_thumbnail_url")


class YoutubeCog(commands.Cog):
    """Handles !summarizeyoutube requests (text-based commands)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="summarizeyoutube", help="Summarize the latest videos from configured YouTube channels")
    async def summarize_youtube(self, ctx: commands.Context) -> None:
        await ctx.send("Fetching and summarizing YouTube videos...")
        loop = asyncio.get_running_loop()
        sent_anything = False

        for feed_url in YOUTUBE_CHANNEL_FEEDS:
            try:
                feed = await loop.run_in_executor(None, feedparser.parse, feed_url)
                feed_title = feed.feed.get("title", "YouTube Channel")

                for entry in feed.entries[:2]:
                    video_title = entry.title
                    video_link = entry.link

                    summary = await loop.run_in_executor(None, get_gemini_summary, video_link)
                    if not summary:
                        logging.warning("Gemini summary failed for: %s", video_title)
                        continue

                    embed = discord.Embed(
                        title=video_title,
                        description=summary,
                        url=video_link,
                        color=discord.Color.red(),
                    )
                    embed.set_footer(text=f"Source: {feed_title}")
                    file = None
                    thumbnail_url = _extract_thumbnail_url(entry)
                    if thumbnail_url:
                        image_bytes = await loop.run_in_executor(None, download_image, thumbnail_url)
                        if image_bytes:
                            file = discord.File(BytesIO(image_bytes), filename="video.jpg")
                            embed.set_image(url="attachment://video.jpg")
                        else:
                            logging.warning("Thumbnail download failed for video: %s", video_title)

                    if file:
                        await ctx.send(embed=embed, file=file)
                    else:
                        await ctx.send(embed=embed)
                    sent_anything = True
            except Exception as exc:  # pylint: disable=broad-except
                logging.exception("Error processing YouTube feed %s", feed_url)
                await ctx.send(f"Error processing YouTube feed `{feed_url}`. Check logs for details.")

        if not sent_anything:
            await ctx.send("Could not summarize any YouTube videos at the moment. Please try again later.")
        else:
            await ctx.send("All YouTube feeds summarized!")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(YoutubeCog(bot))
