# Mind the Gap — Daily Podcast Generator

> Toronto's daily podcast on economics, behavioural science & AI.
> *Inspired by NPR Planet Money — storytelling-first, never boring.*

Two hosts. One story. Every weekday morning.

- **Alex** — the economist: data, context, dry wit
- **Maya** — the behavioural scientist: the human "why", philosophy, AI's impact on society

---

## Stack

| Layer | Tool |
|-------|------|
| Script writing | Claude Opus 4.6 (adaptive thinking) via Anthropic API |
| News sourcing | NewsAPI + 8 RSS feeds (Globe, Financial Post, BNN, CBC, TechCrunch…) |
| Audio synthesis | ElevenLabs TTS (two host voices, multi-turn) |
| Hosting & distribution | Transistor.fm API |

---

## Quick Start

### 1. Install dependencies

```bash
cd podcast/
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

You'll also need `ffmpeg` for pydub audio processing:
```bash
# macOS
brew install ffmpeg
# Ubuntu/Debian
sudo apt-get install ffmpeg
```

### 2. Configure API keys

```bash
cp .env.example .env
# Edit .env and fill in all API keys
```

Required keys:
| Variable | Where to get it |
|----------|----------------|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |
| `ELEVENLABS_API_KEY` | [elevenlabs.io/app/settings/api-keys](https://elevenlabs.io/app/settings/api-keys) |
| `TRANSISTOR_API_KEY` | [transistor.fm/account/api-key](https://transistor.fm/account/api-key) |
| `TRANSISTOR_SHOW_ID` | Your show's ID in Transistor.fm dashboard |
| `NEWS_API_KEY` | [newsapi.org/register](https://newsapi.org/register) (free: 100 req/day) |

### 3. (Optional) Find ElevenLabs voice IDs

```python
from elevenlabs.client import ElevenLabs
client = ElevenLabs(api_key="YOUR_KEY")
for v in client.voices.get_all().voices:
    print(v.voice_id, v.name)
```

Set your preferred voice IDs in `.env` as `ELEVENLABS_VOICE_HOST_1` and `ELEVENLABS_VOICE_HOST_2`.

---

## Running

```bash
# Full run: fetch news → write script → synthesise → publish
python generate_podcast.py

# Review the script without generating audio
python generate_podcast.py --script-only

# Generate audio but don't publish (for review)
python generate_podcast.py --no-publish

# Use a pre-written JSON script (skip news + writing)
python generate_podcast.py --from-script output/2024-03-08_script.json
```

### Automate with cron (daily at 5 AM Mon–Fri)

```bash
chmod +x run_daily.sh
crontab -e
# Add:
# 0 5 * * 1-5 /path/to/mind/podcast/run_daily.sh >> /var/log/mind_podcast.log 2>&1
```

---

## Output files

After each run, the `output/` directory contains:

| File | Contents |
|------|----------|
| `YYYY-MM-DD_script.json` | Raw structured script (list of dialogue turns) |
| `YYYY-MM-DD_transcript.txt` | Human-readable transcript |
| `YYYY-MM-DD_description.txt` | Episode title + show notes |
| `YYYY-MM-DD_episode.mp3` | Final podcast audio |
| `output/logs/YYYY-MM-DD.log` | Full pipeline log |

---

## Architecture

```
generate_podcast.py          ← main orchestrator (CLI entry point)
├── news_fetcher.py          ← NewsAPI + RSS → categorised article lists
├── script_writer.py         ← Claude Opus 4.6 → structured dialogue JSON
├── audio_generator.py       ← ElevenLabs TTS → concatenated MP3
└── publisher.py             ← Transistor.fm API → create / upload / publish
config.py                    ← all env vars in one place
```

### Script format

The script is a JSON array of turns:
```json
[
  {"speaker": "ALEX", "text": "Here's a number that should terrify you…"},
  {"speaker": "MAYA", "text": "Or maybe not terrify — more like unsettle in a productive way."},
  ...
]
```

### Customising voices & tone

- Change host names in `.env` (`HOST_1_NAME`, `HOST_2_NAME`) — the system prompt updates automatically
- Change voice IDs in `.env` (`ELEVENLABS_VOICE_HOST_1`, `ELEVENLABS_VOICE_HOST_2`)
- Edit the `SYSTEM_PROMPT` in `script_writer.py` to adjust tone, structure, or topics

---

## Costs (approximate, per episode)

| Service | Cost |
|---------|------|
| Claude Opus 4.6 (~10K tokens) | ~$0.30 |
| ElevenLabs (~1500 words × 2 voices) | ~$0.15–0.30 (depends on plan) |
| NewsAPI | Free (100 req/day on free plan) |
| Transistor.fm | Included in your podcast plan |
| **Total per episode** | **~$0.45–0.60** |
