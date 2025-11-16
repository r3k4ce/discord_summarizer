"""Slash command cog for YouTube summarization."""

from __future__ import annotations

import asyncio
import logging

import discord
import feedparser
from discord import app_commands
from discord.ext import commands

from config import YOUTUBE_CHANNEL_FEEDS
from services.ai_services import get_gemini_summary


class YoutubeCog(commands.Cog):
    """Handles /summarizeyoutube requests."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="summarizeyoutube",
        description="Summarize the latest videos from configured YouTube channels",
    )
    async def summarize_youtube(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)
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
                    await interaction.followup.send(embed=embed)
                    sent_anything = True
            except Exception as exc:  # pylint: disable=broad-except
                logging.exception("Error processing YouTube feed %s", feed_url)
                await interaction.followup.send(
                    f"Error processing YouTube feed `{feed_url}`. Check logs for details.",
                    ephemeral=True,
                )

        if not sent_anything:
            await interaction.followup.send(
                "Could not summarize any YouTube videos at the moment. Please try again later.",
                ephemeral=True,
            )
        else:
            await interaction.followup.send("All YouTube feeds summarized!", ephemeral=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(YoutubeCog(bot))
