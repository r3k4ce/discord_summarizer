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

# --- Gating configuration ---
ENABLE_GATING = os.getenv("ENABLE_GATING", "true").lower() == "true"
GATING_STRATEGY = os.getenv("GATING_STRATEGY", "model")
GATING_MATCH_MODE = os.getenv("GATING_MATCH_MODE", "allow_if_any")
GATING_KEYWORDS = [
    kw.strip().lower()
    for kw in os.getenv(
        "GATING_KEYWORDS",
        ",".join(
            [
                "gobierno",
                "impuestos",
                "inflacion",
                "libertario",
                "socialismo",
                "estatismo",
                "inversion",
                "seguridad social",
                "politica fiscal",
                # Specific to Urguuay
                "gobierno uruguayo",
                "Frente Amplio",
                "Partido Nacional",
                "Partido Colorado",
                "Ministerio de Economía",
                "Banco Central del Uruguay",
                "mercosur",
            ]
        ),
    ).split(",")
    if kw.strip()
]
GATING_DEFAULT_ON_ERROR = os.getenv("GATING_DEFAULT_ON_ERROR", "true").lower() == "true"
GATING_CACHE_TTL_SECONDS = int(os.getenv("GATING_CACHE_TTL_SECONDS", "86400"))
GATING_SHOW_MATCHES = os.getenv("GATING_SHOW_MATCHES", "false").lower() == "true"

# --- Model-based gating configuration (prefer this method by default) ---
USE_MODEL_BASED_GATING = os.getenv("USE_MODEL_BASED_GATING", "true").lower() == "true"
MODEL_BASED_GATING_MODEL = os.getenv("MODEL_BASED_GATING_MODEL", "gpt-5-nano")
# When classifier cannot be used (API errors, missing key), fallback to keyword gating
MODEL_BASED_GATING_FALLBACK_TO_KEYWORDS = os.getenv(
    "MODEL_BASED_GATING_FALLBACK_TO_KEYWORDS", "true"
).lower() == "true"

# --- Feed configuration ---
ARTICLES_PER_FEED = int(os.getenv("ARTICLES_PER_FEED", "10"))
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
    "ARTICLES_PER_FEED",
    "ENABLE_GATING",
    "GATING_STRATEGY",
    "GATING_MATCH_MODE",
    "GATING_KEYWORDS",
    "GATING_DEFAULT_ON_ERROR",
    "GATING_CACHE_TTL_SECONDS",
    "GATING_SHOW_MATCHES",
    "USE_MODEL_BASED_GATING",
    "MODEL_BASED_GATING_MODEL",
    "MODEL_BASED_GATING_FALLBACK_TO_KEYWORDS",
    "TEST_GUILD_ID",
]
