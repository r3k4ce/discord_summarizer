"""Discord bot bootstrap for news and YouTube summarization."""

from __future__ import annotations

import logging
from pathlib import Path

import discord
from discord.ext import commands

from config import DISCORD_TOKEN


class SummarizerBot(commands.Bot):
    """Discord bot that loads cogs dynamically and syncs slash commands."""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        await self._load_cogs()
        try:
            synced = await self.tree.sync()
            logging.info("Synced %s command(s)", len(synced))
        except Exception as exc:  # pylint: disable=broad-except
            logging.error("Failed to sync commands: %s", exc)

    async def _load_cogs(self) -> None:
        cogs_dir = Path(__file__).parent / "cogs"
        if not cogs_dir.exists():
            logging.warning("Cogs directory %s does not exist", cogs_dir)
            return

        for file in cogs_dir.iterdir():
            if file.suffix == ".py" and not file.name.startswith("_"):
                module_name = f"cogs.{file.stem}"
                try:
                    await self.load_extension(module_name)
                    logging.info("Loaded cog: %s", module_name)
                except Exception as exc:  # pylint: disable=broad-except
                    logging.error("Failed to load cog %s: %s", module_name, exc)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    if not DISCORD_TOKEN:
        logging.error("DISCORD_TOKEN not configured. Check your .env file.")
        return

    bot = SummarizerBot()

    @bot.event
    async def on_ready() -> None:
        if bot.user:
            logging.info("Logged in as %s (%s)", bot.user, bot.user.id)
        logging.info("Bot ready. Slash commands registered.")

    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
