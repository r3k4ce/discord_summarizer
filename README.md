# Discord Summarizer Bot

A Discord bot that automatically summarizes news articles and YouTube videos using AI. Get quick, digestible summaries of the latest content from your favorite sources directly in your Discord server.

## Features

- **📰 News Summarization**: Fetches and summarizes articles from Uruguayan and international news sources
- **🎥 YouTube Summarization**: Summarizes videos from configured YouTube channels
- **🎧 Audio Overviews**: Generates Spanish audio narrations of article summaries using Google Gemini TTS
- **🤖 AI-Powered**: Uses OpenAI GPT-5-mini for news and Google Gemini Flash for YouTube videos
- **🔍 Smart Filtering**: Model-based content filtering to identify politics/economy articles with keyword fallback
- **⚡ Prefix Commands**: Use `!summarizenews` and `!summarizeyoutube` to invoke the bot

## Prerequisites

- Python 3.8 or higher
- A Discord Bot Token ([Create one here](https://discord.com/developers/applications))
- OpenAI API Key ([Get one here](https://platform.openai.com/api-keys))
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))

## Installation

1. **Clone or download this repository**

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   
   Create a `.env` file in the project root with your API keys:
   ```env
   DISCORD_TOKEN=your_discord_bot_token_here
   OPENAI_API_KEY=your_openai_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   
   # Optional: Enable audio overviews (disabled by default)
   ENABLE_AUDIO_OVERVIEWS=true
   AUDIO_SUMMARY_MODEL=gpt-5-mini
   TTS_MODEL=gemini-2.5-pro-preview-tts
   TTS_LANGUAGE_CODE=es-ES
   TTS_VOICE=Zephyr
   ```

## Usage

1. **Start the bot**:
   ```bash
   python bot.py
   ```

2. **Invite the bot to your Discord server**:
   - Go to the [Discord Developer Portal](https://discord.com/developers/applications)
   - Select your application
   - Go to OAuth2 → URL Generator
   - Select scopes: `bot` and `applications.commands`
   - Select bot permissions: `Send Messages`, `Embed Links`
   - Use the generated URL to invite the bot to your server

3. **Use the bot commands in Discord**:
   - `!summarizenews` - Summarizes the latest 2 articles from each configured news feed
   - `!summarizeyoutube` - Summarizes the latest 2 videos from each configured YouTube channel

   ---

   ### ⚡ Fast testing (prefix commands)

   For prefix commands, features are available as soon as the bot is online in your server; you do not need to wait for global sync.

## Configuration

You can customize the news sources and YouTube channels in `config.py`:

- **RSS_FEEDS**: List of RSS feed URLs for news sources
- **YOUTUBE_CHANNEL_FEEDS**: List of YouTube channel feed URLs

### Gating & filtering

The bot intelligently filters (gates) which articles/videos are summarized based on relevance. By default, it uses **model-based gating** where an AI classifier (`is_article_relevant`) determines if content is about politics, economy, or related topics.

Environment variables (set in `.env`):

- **ENABLE_GATING**: Enable or disable content filtering (default: `true`)
- **GATING_STRATEGY**: Strategy to use — `model` (AI classifier) or `keywords` (pattern matching). Default: `model`
- **USE_MODEL_BASED_GATING**: Enable AI-based classification (default: `true`)
- **MODEL_BASED_GATING_MODEL**: Model name for classification (default: `gpt-5-nano`)
- **MODEL_BASED_GATING_FALLBACK_TO_KEYWORDS**: If `true`, falls back to keyword matching when the AI classifier fails or returns inconclusive results (default: `true`)
- **GATING_KEYWORDS**: Comma-separated keywords for fallback matching (see `config.py` for defaults)
- **GATING_MATCH_MODE**: How keywords are evaluated — `allow_if_any` or `deny_if_any` (default: `allow_if_any`)
- **GATING_DEFAULT_ON_ERROR**: Default decision when gating encounters errors (default: `true`)
- **GATING_CACHE_TTL_SECONDS**: How long to cache gating decisions in seconds (default: `86400` = 24 hours)

The model-based approach is more accurate and context-aware than simple keyword matching, but has higher latency and API costs. The fallback mechanism ensures the bot continues working even if the AI service is unavailable.

### Audio overviews

The bot can generate Spanish audio narrations for article summaries. This feature is **disabled by default**.

Environment variables (set in `.env`):

- **ENABLE_AUDIO_OVERVIEWS**: Enable or disable audio generation (default: `false`)
- **AUDIO_SUMMARY_MODEL**: OpenAI model for creating concise audio-friendly summaries (default: `gpt-5-mini`)
- **TTS_MODEL**: Google Gemini text-to-speech model (default: `gemini-2.5-pro-preview-tts`)
- **TTS_LANGUAGE_CODE**: Language code for audio generation (default: `es-ES` for Spanish)
- **TTS_VOICE**: Voice name for TTS (default: `Zephyr`)

When enabled, each summarized article includes:
1. A short, audio-optimized summary generated by OpenAI
2. Spanish TTS audio file attached to the Discord message
3. An embed field noting "Resumen en audio" with instructions to play the attachment

**Note**: Audio files appear as downloadable attachments below the embed in Discord (not embedded players). Users can click the attachment to download or play the audio.

Example YouTube channel feed URL format:
```
https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID_HERE
```

## Project Structure

```
summarizer/
├── bot.py                    # Main bot entry point
├── config.py                 # Configuration and API keys
├── requirements.txt          # Python dependencies
├── test.py                   # Manual testing harness (no Discord required)
├── .env                      # Environment variables (not in git)
├── .github/
│   └── copilot-instructions.md  # AI agent guidance
├── cogs/
│   ├── news.py              # News summarization command
│   └── youtube.py           # YouTube summarization command
├── services/
│   ├── ai_services.py       # AI provider wrappers (OpenAI, Gemini)
│   ├── content_fetcher.py   # Article content extraction
│   └── gating.py            # Content filtering logic (model + keywords)
└── tools/
    └── check_feeds.py       # Feed validation utility
```

## Troubleshooting

- **Bot doesn't respond**: Make sure the bot is invited with the right permissions and you are using the `!` prefix commands.
   - If the bot is in the server but not responding, double-check bot permissions (Send Messages, Embed Links) and that your message starts with `!`.
- **"Missing API keys" warning**: Check your `.env` file has all three required keys
- **AI summary fails**: Check your API key quotas and limits. For OpenAI, ensure you have access to the configured models.
- **Article scraping fails**: Some websites block automated scraping; this is expected for certain sources
- **Model gating errors**: If you see `max_output_tokens` errors, the OpenAI Responses API requires minimum 16 tokens. This is already configured correctly.
- **All articles filtered out**: Check your gating configuration. Run `python test.py` to see gating decisions and matches in the logs.
- **High API costs**: Consider setting `GATING_STRATEGY=keywords` or reducing `ARTICLES_PER_FEED` to lower the number of AI calls.
- **Audio overviews not appearing**: 
  - Verify `ENABLE_AUDIO_OVERVIEWS=true` in `.env` (check spelling)
  - Ensure `GEMINI_API_KEY` is set and valid
  - Check bot logs for TTS generation errors
  - Audio appears as a file attachment below the embed (not inside it) — look for the attachment icon in Discord
  - Restart the bot after changing `.env` variables

## License

This project is provided as-is for educational and personal use.

