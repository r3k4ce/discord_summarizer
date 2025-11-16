"""Text command cog for news summarization (prefix commands)."""

from __future__ import annotations

import asyncio
import logging
from io import BytesIO

import discord
import feedparser
from discord.ext import commands

from config import ARTICLES_PER_FEED, GATING_SHOW_MATCHES, RSS_FEEDS
from services.ai_services import get_ai_summary
from services.content_fetcher import download_image, fetch_article_with_image
from services.gating import should_summarize_with_matches


class NewsCog(commands.Cog):
    """Handles !summarizenews requests (text-based commands)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="summarizenews", help="Summarize the latest stories from configured RSS feeds")
    async def summarize_news(self, ctx: commands.Context) -> None:
        # Let users know the command is being processed
        await ctx.send("Fetching and summarizing news...")
        loop = asyncio.get_running_loop()
        sent_anything = False

        for feed_url in RSS_FEEDS:
            try:
                feed = await loop.run_in_executor(None, feedparser.parse, feed_url)
                feed_title = feed.feed.get("title", "News Feed")

                for entry in feed.entries[:ARTICLES_PER_FEED]:
                    article_title = entry.title
                    article_link = entry.link

                    article_text, article_image_url = await loop.run_in_executor(
                        None, fetch_article_with_image, article_link
                    )

                    if not article_text:
                        logging.warning("Could not scrape article: %s", article_title)
                        continue

                    allowed, matches = await loop.run_in_executor(
                        None, should_summarize_with_matches, article_text
                    )
                    if not allowed:
                        logging.info("Skipping article due to gating: %s (matches=%s)", article_title, matches)
                        continue

                    summary = await loop.run_in_executor(None, get_ai_summary, article_text)
                    if not summary:
                        logging.warning("AI summary failed for: %s", article_title)
                        continue

                    embed = discord.Embed(
                        title=article_title,
                        description=summary,
                        url=article_link,
                        color=discord.Color.blue(),
                    )
                    footer_text = f"Source: {feed_title}"
                    if GATING_SHOW_MATCHES and matches:
                        footer_text = f"{footer_text} • Matches: {', '.join(matches)}"
                    embed.set_footer(text=footer_text)
                    file = None
                    if article_image_url:
                        image_bytes = await loop.run_in_executor(None, download_image, article_image_url)
                        if image_bytes:
                            file = discord.File(BytesIO(image_bytes), filename="article.jpg")
                            embed.set_image(url="attachment://article.jpg")
                        else:
                            logging.warning("Image download failed for article: %s", article_title)

                    if file:
                        await ctx.send(embed=embed, file=file)
                    else:
                        await ctx.send(embed=embed)
                    sent_anything = True
            except Exception as exc:  # pylint: disable=broad-except
                logging.exception("Error processing feed %s", feed_url)
                await ctx.send(f"Error processing feed `{feed_url}`. Check logs for details.")

        if not sent_anything:
            await ctx.send("Could not fetch or summarize any news right now. Please try again later.")
        else:
            await ctx.send("All feeds summarized!")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(NewsCog(bot))
