"""Central config — reads from .env and environment variables."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# === Anthropic ===
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# === ElevenLabs ===
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_HOST_1 = os.getenv("ELEVENLABS_VOICE_HOST_1", "21m00Tcm4TlvDq8ikWAM")
ELEVENLABS_VOICE_HOST_2 = os.getenv("ELEVENLABS_VOICE_HOST_2", "pNInz6obpgDQGcFmaJgB")
ELEVENLABS_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")

# === Transistor.fm (required only for publishing) ===
TRANSISTOR_API_KEY = os.getenv("TRANSISTOR_API_KEY", "")
TRANSISTOR_SHOW_ID = os.getenv("TRANSISTOR_SHOW_ID", "")
TRANSISTOR_BASE_URL = "https://api.transistor.fm/v1"

# === OpenAI (TTS provider) ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# === Voxtral/Mistral (TTS provider - high quality, mid cost) ===
VOXTRAL_API_KEY = os.getenv("VOXTRAL_API_KEY", "")

# === MiniMax (TTS provider - budget, standard quality) ===
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
MINIMAX_GROUP_ID = os.getenv("MINIMAX_GROUP_ID", "")

# === OpenRouter (fallback LLM provider) ===
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# === NewsAPI (optional — RSS feeds used as fallback) ===
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
NEWS_API_BASE_URL = "https://newsapi.org/v2"


# === Podcast identity ===
PODCAST_TITLE_PREFIX = os.getenv("PODCAST_TITLE_PREFIX", "Mind the Gap")
HOST_1_NAME = os.getenv("HOST_1_NAME", "Alex")
HOST_2_NAME = os.getenv("HOST_2_NAME", "Maya")
SHOW_LANGUAGE = os.getenv("SHOW_LANGUAGE", "en")
TARGET_WORD_COUNT = int(os.getenv("TARGET_WORD_COUNT", "1500"))

# === RSS feeds ===
RSS_FEEDS = [
    # Toronto / Canadian economics & business
    "https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/business/",
    "https://financialpost.com/feed",
    "https://www.cbc.ca/cmlink/rss-topstories",
    "https://www.cbc.ca/cmlink/rss-business",
    # Global macro / econ
    "https://feeds.bloomberg.com/markets/news.rss",
    "https://www.economist.com/finance-and-economics/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Economy.xml",
    # AI / tech
    "https://techcrunch.com/feed/",
    "https://www.technologyreview.com/feed/",
    "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "https://www.wired.com/feed/rss",
    "https://spectrum.ieee.org/feeds/feed.rss",
    # Behavioural science & spirituality
    "https://www.psychologytoday.com/us/blog/feed",
    "https://behavioralscientist.org/feed/",
    # General world news (for variety)
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.theguardian.com/world/rss",
    "https://feeds.bbci.co.uk/news/world/rss.xml",
]
