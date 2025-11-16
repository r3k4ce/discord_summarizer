"""Slash command cog for news summarization."""

from __future__ import annotations

import asyncio
import logging

import discord
import feedparser
from discord import app_commands
from discord.ext import commands

from config import RSS_FEEDS
from services.ai_services import get_ai_summary
from services.content_fetcher import fetch_article_text


class NewsCog(commands.Cog):
    """Handles /summarizenews requests."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="summarizenews", description="Summarize the latest stories from configured RSS feeds")
    async def summarize_news(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)
        loop = asyncio.get_running_loop()
        sent_anything = False

        for feed_url in RSS_FEEDS:
            try:
                feed = await loop.run_in_executor(None, feedparser.parse, feed_url)
                feed_title = feed.feed.get("title", "News Feed")

                for entry in feed.entries[:2]:
                    article_title = entry.title
                    article_link = entry.link
                    article_text = await loop.run_in_executor(None, fetch_article_text, article_link)

                    if not article_text:
                        logging.warning("Could not scrape article: %s", article_title)
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
                    embed.set_footer(text=f"Source: {feed_title}")
                    await interaction.followup.send(embed=embed)
                    sent_anything = True
            except Exception as exc:  # pylint: disable=broad-except
                logging.exception("Error processing feed %s", feed_url)
                await interaction.followup.send(
                    f"Error processing feed `{feed_url}`. Check logs for details.", ephemeral=True
                )

        if not sent_anything:
            await interaction.followup.send(
                "Could not fetch or summarize any news right now. Please try again later.",
                ephemeral=True,
            )
        else:
            await interaction.followup.send("All feeds summarized!", ephemeral=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(NewsCog(bot))
