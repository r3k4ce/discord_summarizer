# Discord Summarizer Bot

A Discord bot that automatically summarizes news articles and YouTube videos using AI. Get quick, digestible summaries of the latest content from your favorite sources directly in your Discord server.

## Features

- **📰 News Summarization**: Fetches and summarizes articles from major news sources (BBC, CNN, Reuters)
- **🎥 YouTube Summarization**: Summarizes videos from configured YouTube channels
- **🤖 AI-Powered**: Uses OpenAI GPT-5-mini for news and Google Gemini Flash for YouTube videos
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

The bot filters (gates) which articles/videos are summarized. By default the system uses a model-based gating strategy (OpenAI) and falls back to keyword checks on errors.

- **ENABLE_GATING**: Enable or disable gating (default: `true`).
- **GATING_STRATEGY**: Which strategy to use for gating (`model` or `keywords`). Default: `model`.
- **MODEL_BASED_GATING_MODEL**: The model name to use (default: `gpt-5-nano`).
- **MODEL_BASED_GATING_FALLBACK_TO_KEYWORDS**: If true, fallback to keywords when the model cannot classify (default: `true`).


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
├── .env                      # Environment variables (not in git)
├── cogs/
│   ├── news.py              # News summarization command
│   └── youtube.py           # YouTube summarization command
└── services/
    ├── ai_services.py       # AI provider wrappers (OpenAI, Gemini)
    └── content_fetcher.py   # Article content extraction
```

## Troubleshooting

- **Bot doesn't respond**: Make sure the bot is invited with the right permissions and you are using the `!` prefix commands.
   - If the bot is in the server but not responding, double-check bot permissions (Send Messages, Embed Links) and that your message starts with `!`.
- **"Missing API keys" warning**: Check your `.env` file has all three required keys
- **AI summary fails**: Check your API key quotas and limits
- **Article scraping fails**: Some websites block automated scraping; this is expected for certain sources

## License

This project is provided as-is for educational and personal use.

