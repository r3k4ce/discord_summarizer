"""Central configuration for the Discord summarizer bot."""

import logging
import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# --- Required secrets ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TEST_GUILD_ID = os.getenv("TEST_GUILD_ID")

if not DISCORD_TOKEN or not OPENAI_API_KEY or not GEMINI_API_KEY:
    logging.warning(
        "Missing one or more API keys. Bot functionality and tests may fail until they are set."
    )

# --- Feed configuration ---
RSS_FEEDS = [
    # "http://feeds.bbci.co.uk/news/world/rss.xml",
    # "http://rss.cnn.com/rss/cnn_topstories.rss",
    # "https://feeds.reuters.com/reuters/topNews",
    "https://www.montevideo.com.uy/anxml.aspx?58",
    "https://www.elobservador.com.uy/rss/pages/nacional.xml"
]

YOUTUBE_CHANNEL_FEEDS = [
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCBJycsmduvYEL83R_U4JriQ",  # MKBHD
    "https://www.youtube.com/feeds/videos.xml?channel_id=UCSHZKyawb77ixDdsGog4iWA",  # Lex Fridman
]

__all__ = [
    "DISCORD_TOKEN",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "RSS_FEEDS",
    "YOUTUBE_CHANNEL_FEEDS",
    "TEST_GUILD_ID",
]
