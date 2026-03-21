"""
Generates a two-host NPR Planet Money-style podcast script using configurable LLMs.

Primary model: Claude Opus 4.6 (Anthropic direct)
Fallback models via OpenRouter: Gemini 3.1 Pro, GPT-5.4, DeepSeek V3.2

The output is a structured list of dialogue turns with speaker types:
  - {"speaker": "ALEX", "text": "..."}          — host dialogue
  - {"speaker": "MAYA", "text": "..."}          — host dialogue
  - {"speaker": "SFX", "text": "..."}           — ambient sound marker
"""
from __future__ import annotations

import json
import logging
import re
import time
from datetime import date
from typing import Any

import anthropic
import httpx

import config
import settings as podcast_settings

log = logging.getLogger(__name__)

PROMPT_DEFAULTS = {
    "show_identity": """• Audience: tech execs, AI enthusiasts, and globally curious professionals
• Topics: AI & technology, Toronto/Canada life & policy, global trends — spanning
  economics, culture, science, health, climate, innovation, and geopolitics — all
  blended through a behavioural science and spirituality lens
• Vibe: ENERGETIC morning show — like the best coffee conversation with brilliant friends.
  Fast-paced, witty, story-driven. Think "Planet Money meets a sharp morning show."
  Bright, optimistic, intellectually playful. NEVER dull, slow, or lecture-y.
• Tone: Positive and forward-looking. Even when covering challenges, find the
  opportunity angle. Subtle humor throughout — wordplay, gentle irony, unexpected
  analogies, the occasional dad joke that lands. Make listeners smile.""",

    "host_alex": """ALEX: the tech-savvy polymath with sharp wit and infectious energy. Equally
at home explaining transformer architectures, urban transit policy, climate science,
or startup economics. Loves data, global context, and clever analogies that make
complex things click. Quick with a quip, occasionally self-deprecating. Turns dry
stats into "wait, really?!" moments. Connects robotics labs to Toronto bike lanes
to semiconductor supply chains to demographic shifts with enthusiasm.""",

    "host_maya": """MAYA: the behavioural scientist with playful curiosity and warm energy.
Always asks "but WHY do people actually do that?" with genuine delight.
Makes psychology feel like gossip about the human brain. Connects technology,
culture, and policy to cognitive biases, consciousness, and ancient wisdom with
a light touch. Fascinated by how innovation reshapes human behavior, communities,
and decision-making. Her spiritual references land because they're practical,
not preachy. Quick laugh, great at riffing off Alex's jokes.""",

    "episode_structure": """1. COLD OPEN (60-90 words, 2-3 turns)
   Drop the listener straight into a vivid scene, character, or moment. NO "welcome",
   NO "today on the show". Start mid-action. A person doing something. A surprising
   number. A place you can see and smell. The listener should feel like they walked
   into the middle of something happening.
   Examples: "Last Tuesday, a warehouse manager in Brampton opened her laptop and
   froze." or "A robotics startup in Waterloo just shipped its thousandth unit."

2. SHOW INTRO (one ALEX turn after the cold open)
   After the cold open hooks them, Alex delivers the bumper as a regular line:
   "This is Mind the Gap. I'm Alex, and with me is Maya. Today — [one-line tease of
   what the episode is about, phrased as a mystery or question]."
   This is the "This is Planet Money from NPR" moment. It's just a normal ALEX turn.

3. THE STORY WITH REAL QUOTES (the bulk of the episode)
   Tell the story using REAL quotes from the provided news articles and social media
   reactions. Bring it alive by weaving in voices of real people:

   FROM NEWS ARTICLES — quote officials, executives, researchers, or analysts named
   in the articles. Attribute clearly:
     "The city's chief planner told the Star, quote, 'we didn't expect this many
      applications for laneway housing — it's reshaping entire neighbourhoods.'"
     "According to Nature, the lead researcher said, quote,
      'the results surprised even us — the protein folded in seconds, not days.'"

   FROM REDDIT / SOCIAL MEDIA — use these as "voice of the people" color. Attribute
   to the subreddit, never to specific usernames:
     "One user on r/toronto put it perfectly: 'I saw a coyote on the Gardiner
      at 7 AM and honestly it felt like a metaphor for this whole city right now.'"
     "Over on r/MachineLearning, the reaction was mixed. One commenter wrote,
      'this is impressive engineering but the safety implications are terrifying.'"

   CRITICAL RULES FOR QUOTES:
   - ONLY use quotes that appear in the provided news summaries or social media
     reactions. NEVER fabricate or make up quotes.
   - If no good quotes are available for a section, the hosts discuss the topic
     without quotes — that's perfectly fine.
   - Do NOT create fictional characters, fictional interviews, or made-up people.
   - Every quote must have clear attribution (who said it, where it appeared).

4. THE BEHAVIOURAL TURN
   Maya reframes the story through human psychology, cognitive biases, or social
   dynamics. What are people actually thinking/feeling? Why do smart people make
   irrational choices? Reference specific concepts by name.

5. THE SPIRITUAL / PHILOSOPHICAL LENS
   Maya connects the story to mindfulness, consciousness, or ancient wisdom
   traditions. Stoic equanimity and navigating uncertainty. Vedantic non-attachment
   and career reinvention. Buddhist impermanence and shifting communities. Keep it
   grounded — a genuine insight, not a lecture.

6. THE TAKEAWAY
   Circle back to the opening scene. End with something the listener
   can do or notice today. A small gift of practical insight.""",
}

def _get_prompt_section(key: str) -> str:
    s = podcast_settings.load()
    custom = s.get("prompt_sections", {})
    return custom.get(key, PROMPT_DEFAULTS.get(key, ""))


def _build_system_prompt() -> str:
    s = podcast_settings.load()

    show_identity = _get_prompt_section("show_identity")
    host_alex = _get_prompt_section("host_alex")
    host_maya = _get_prompt_section("host_maya")
    episode_structure = _get_prompt_section("episode_structure")

    base = f"""You are the head writer for "Mind the Gap", a daily morning podcast for tech executives and AI enthusiasts. Your job is to make listeners excited to start their day.

SHOW IDENTITY
─────────────
{show_identity}
• Two hosts:
    - {host_alex}
    - {host_maya}

EPISODE STRUCTURE (follow this arc exactly — this is what makes Planet Money great)
────────────────────────────────────────────────────────────────────────────────────

{episode_structure}
"""

    editorial = "\nEDITORIAL DIRECTIVES (for this episode)\n───────────────────────────────────────\n"

    n = s.get("story_count", 1)
    if n <= 1:
        editorial += "• Narrative: Weave ONE strong narrative thread. One compelling story, not a news roundup.\n"
    else:
        editorial += f"• Narrative: Weave exactly {n} distinct story threads that interconnect by the end of the episode.\n"

    bc = s.get("behavioral_concepts", 2)
    if bc == 0:
        editorial += "• Behavioral economics: Do NOT include behavioral economics concepts in this episode.\n"
    else:
        editorial += (
            f"• Behavioral economics: Include exactly {bc} behavioral economics concept(s) "
            f"(e.g., anchoring, loss aversion, nudge theory, sunk cost fallacy, "
            f"availability heuristic). Weave them naturally into the dialogue.\n"
        )

    sc = s.get("spirituality_concepts", 1)
    if sc == 0:
        editorial += "• Spirituality: Do NOT include spirituality or spiritual/philosophical references in this episode.\n"
    else:
        editorial += (
            f"• Spirituality: Include exactly {sc} spirituality/wisdom reference(s) "
            f"(e.g., Stoic equanimity, Vedantic non-attachment, Buddhist impermanence, "
            f"mindfulness practice). Weave them naturally — grounded insights, not lectures.\n"
        )

    gt = s.get("geo_toronto_pct", 25)
    gc = s.get("geo_canada_pct", 25)
    ga = s.get("geo_ai_tech_pct", 25)
    gw = s.get("geo_world_pct", 25)
    editorial += (
        f"• Topic weight: approximately {gt}% Toronto/local, {gc}% Canada, "
        f"{ga}% AI/Tech, {gw}% World/global.\n"
    )

    target_words = min(1550 + (n - 1) * 220, 3100)
    target_minutes = round(target_words / 180)

    output_format = f"""
OUTPUT FORMAT (strict JSON)
────────────────────────────
Return ONLY a JSON array of turns. No markdown fences, no preamble.

Turn types:
1. Host dialogue: {{"speaker": "ALEX", "text": "spoken words"}}
   or: {{"speaker": "MAYA", "text": "spoken words"}}

2. Sound/music cues (8-12 throughout — this is critical for production quality):
   {{"speaker": "SFX", "text": "brief sound or music description"}}

   SFX TYPES (use a MIX of all of these):
   a) Ambient scene-setters: {{"speaker": "SFX", "text": "busy Toronto street corner with distant TTC bell"}}
   b) Musical transitions: {{"speaker": "SFX", "text": "short jazzy piano riff transitioning to next segment"}}
   c) Mood music beds: {{"speaker": "SFX", "text": "gentle lo-fi beat fading in underneath"}}
   d) Dramatic stingers: {{"speaker": "SFX", "text": "suspenseful synth hit"}}
   e) Breather moments: {{"speaker": "SFX", "text": "soft ambient pad, a beat of reflective silence"}}

   Place SFX:
   - After the cold open (musical transition into the show)
   - Between major story segments (musical bridges, not just silence)
   - Before a big reveal or surprising stat (dramatic stinger)
   - During emotional or reflective moments (ambient pad or soft music)
   - At the sign-off (upbeat closing music)
   - At least 2-3 "breather" moments where the pace slows and music fills the space

PACING (target ~180 words per minute — energetic but with breathing room):
- Total ~{target_words} words across all host dialogue turns (~{target_minutes} minutes)
- Each host dialogue turn ≈ 20–60 words — punchy, rapid-fire back-and-forth
- HIGH ENERGY throughout: this is a morning show, listeners are grabbing coffee and
  need to feel awake and engaged. The hosts are excited about what they're discussing.
- Quick reactions: "Oh wow—", "Ha! That's exactly—", "OK wait, but here's the thing—"
- Subtle humor: clever wordplay, unexpected analogies, gentle irony, the occasional
  playful jab between hosts. Not stand-up comedy — just naturally funny smart people.
- PAUSES & BREATHING ROOM: Not every moment should be rapid-fire. Build in contrast:
  - After a powerful stat or quote, let it land — a host can say "...let that sink in"
    or just "Wow." before the other picks up
  - Use "..." ellipses and em-dashes in host text to signal natural pauses
  - 2-3 times per episode, slow down for a reflective beat with soft music underneath
- NO long monologues — if a point takes 60+ words, break it into energetic back-and-forth
- Positive framing: even challenging news gets a "but here's what's interesting" angle

Rules:
- The show intro ("This is Mind the Gap...") is a regular ALEX turn — no special speaker type
- SFX descriptions: 3-8 words, placed at natural scene transitions AND story transitions
- Hosts refer to each other by first name occasionally
- Use contractions, ellipses, "I mean…", "right?", "Wait—"
- References span geographies: TTC, city hall, university labs, Silicon Valley, global health agencies, climate summits, etc.
- When quoting real people, the hosts say the quote as part of their dialogue
- NEVER create fictional characters or fabricated interviews

TOPIC FRESHNESS (critical):
- Each episode MUST feel different from the last. Do NOT rehash yesterday's lead story.
- If the news feed is dominated by one topic (e.g., oil prices, housing), find the
  SECOND or THIRD most interesting story instead. Listeners already heard about the big story.
- Variety is more valuable than covering the "biggest" story again.
- When previous episode context is provided, treat it as a hard constraint: skip those topics
  and find something the audience hasn't heard yet.
"""

    return base + editorial + output_format


def _build_user_prompt(
    news_summary: str,
    episode_date: date,
    story_context: str = "",
) -> str:
    s = podcast_settings.load()
    n = s.get("story_count", 1)
    is_sunday = episode_date.weekday() == 6

    if is_sunday and story_context:
        narrative_instruction = (
            "This is a SUNDAY WEEK IN REVIEW episode. Below you'll find both today's "
            "fresh news AND a summary of all stories covered this week (Mon–Sat). "
            f"Your job: weave {n} COMPELLING NARRATIVE THREAD(S) that REFLECT on the "
            "week's themes, connect story arcs that evolved over multiple days, identify "
            "emerging patterns, and provide a cohesive weekly narrative. You may include "
            "brand-new Sunday news, but the primary structure should be a thoughtful "
            "recap tying the week together. Reference specific days when stories broke "
            "or evolved (e.g., 'Remember Monday when we talked about…')."
        )
    elif n <= 1:
        narrative_instruction = (
            "Your job: find the STRONGEST SINGLE NARRATIVE THREAD that connects stories "
            "across these geographies and domains. Planet Money style — one compelling story, "
            "not a news roundup."
        )
    else:
        narrative_instruction = (
            f"Your job: find {n} COMPELLING NARRATIVE THREADS that interconnect across "
            f"geographies and domains. Each thread should have its own arc but they "
            f"should weave together by the episode's end."
        )

    return f"""Today is {episode_date.strftime('%A, %B %d, %Y')}.

Here are today's news headlines and summaries spanning AI/tech, Toronto/Canada,
global policy, science, culture, markets, and behavioural science/spirituality.

{narrative_instruction}

Look for surprising connections across domains — a robotics breakthrough and a
shift in urban planning, or a biotech discovery and a Stoic insight about resilience.

IMPORTANT: Use ONLY real quotes from the news articles and social media reactions
provided below. Do NOT create fictional characters or fabricated interviews.
If the sources include quotes from real people, weave them naturally into the
hosts' dialogue with clear attribution. If social media reactions are included,
use them as "voice of the people" color.

{news_summary}
{story_context}
Write the full episode script now. Return ONLY the JSON array."""


VALID_SPEAKERS = {"ALEX", "MAYA", "SFX"}


def _find_matching_bracket(text: str, start: int) -> int:
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == "\\":
            if in_string:
                escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return i
    return -1


def _extract_json_array(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```\s*$", "", raw)
    raw = raw.strip()

    bracket_start = raw.find("[")
    if bracket_start == -1:
        raise ValueError("Could not find a JSON array in Claude's response.")

    bracket_end = _find_matching_bracket(raw, bracket_start)

    if bracket_end == -1:
        return raw[bracket_start:]

    return raw[bracket_start : bracket_end + 1]


def _fix_json_issues(text: str) -> str:
    text = re.sub(r",\s*([}\]])", r"\1", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    return text


def _repair_truncated_json(text: str) -> str:
    text = text.rstrip()
    text = re.sub(r",\s*$", "", text)

    in_string = False
    escape = False
    open_braces = 0
    open_brackets = 0
    for ch in text:
        if escape:
            escape = False
            continue
        if ch == "\\":
            if in_string:
                escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            open_braces += 1
        elif ch == "}":
            open_braces -= 1
        elif ch == "[":
            open_brackets += 1
        elif ch == "]":
            open_brackets -= 1

    if in_string:
        text += '"'

    text = re.sub(r",\s*$", "", text.rstrip())

    text += "}" * max(open_braces, 0)
    text += "]" * max(open_brackets, 0)

    return text


def _parse_script(raw: str) -> list[dict[str, str]]:
    log.debug("Raw script response length: %d chars", len(raw))

    try:
        json_str = _extract_json_array(raw)
    except ValueError:
        log.error("Failed to extract JSON array. First 500 chars of response:\n%s", raw[:500])
        raise

    attempts = [
        ("raw", json_str),
        ("fix_trailing", _fix_json_issues(json_str)),
        ("repair_truncated", _repair_truncated_json(_fix_json_issues(json_str))),
    ]
    parsed = None
    last_err = None

    for label, attempt in attempts:
        try:
            parsed = json.loads(attempt)
            if label != "raw":
                log.info("JSON parsed successfully using '%s' strategy.", label)
            break
        except json.JSONDecodeError as e:
            last_err = e
            continue

    if parsed is None:
        log.error("JSON parse failed after all attempts. First 500 chars:\n%s", json_str[:500])
        raise ValueError(f"Could not parse JSON from Claude's response: {last_err}")

    if not isinstance(parsed, list):
        raise ValueError(f"Expected a JSON array, got: {type(parsed)}")

    normalised: list[dict[str, str]] = []
    for turn in parsed:
        if not isinstance(turn, dict):
            continue
        speaker = turn.get("speaker", "").upper().strip()
        text = turn.get("text", "").strip()
        if speaker not in VALID_SPEAKERS or not text:
            continue
        entry: dict[str, str] = {"speaker": speaker, "text": text}
        normalised.append(entry)

    if not normalised:
        log.error("Script parsed but no valid turns. Raw turns: %s", parsed[:3])
        raise ValueError("Script parsed but contained no valid dialogue turns.")

    return normalised


MIN_DIALOGUE_TURNS = 10
MIN_SCRIPT_WORDS = 400


def _validate_script(script: list[dict[str, str]]) -> list[str]:
    issues: list[str] = []
    dialogue_count = sum(1 for t in script if t["speaker"] in ("ALEX", "MAYA"))
    word_count = sum(
        len(t["text"].split()) for t in script
        if t["speaker"] in ("ALEX", "MAYA")
    )
    if dialogue_count < MIN_DIALOGUE_TURNS:
        issues.append(f"Only {dialogue_count} dialogue turns (need {MIN_DIALOGUE_TURNS}+)")
    if word_count < MIN_SCRIPT_WORDS:
        issues.append(f"Only ~{word_count} words (need {MIN_SCRIPT_WORDS}+)")
    return issues


def _call_claude(
    client: anthropic.Anthropic,
    system_prompt: str,
    user_prompt: str,
) -> tuple[str, str | None]:
    for thinking_attempt in range(3):
        thinking_cfg = {"type": "adaptive"}
        if thinking_attempt > 0:
            thinking_cfg = {"type": "enabled", "budget_tokens": 5000}
            log.warning(
                "Retrying with capped thinking budget (attempt %d)…",
                thinking_attempt + 1,
            )

        with client.messages.stream(
            model="claude-opus-4-6",
            max_tokens=16000,
            thinking=thinking_cfg,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        ) as stream:
            final = stream.get_final_message()

        text_parts = []
        for block in final.content:
            if block.type == "text":
                text_parts.append(block.text)
        raw_text = "\n".join(text_parts)

        if raw_text.strip():
            break

        block_types = [b.type for b in final.content]
        log.warning("Claude returned no text blocks (types: %s), retrying…", block_types)

    if not raw_text:
        log.error("Claude returned no text blocks after all attempts.")
        raise ValueError("Claude returned no text content in the response.")

    stop_reason = getattr(final, "stop_reason", None)
    if stop_reason == "max_tokens":
        log.warning(
            "Claude response was TRUNCATED (hit max_tokens). "
            "Output may be incomplete — will attempt repair."
        )

    log.info(
        "Script generated. Tokens used — input: %d, output: %d (stop: %s)",
        final.usage.input_tokens,
        final.usage.output_tokens,
        stop_reason or "unknown",
    )

    return raw_text, stop_reason


OPENROUTER_MODEL_MAP = {
    "gemini-3.1-pro": "google/gemini-3.1-pro-preview",
    "gpt-5.4": "openai/gpt-5.4",
    "deepseek-v3.2": "deepseek/deepseek-v3.2",
}

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def _call_openrouter(
    model_key: str,
    system_prompt: str,
    user_prompt: str,
) -> tuple[str, str | None]:
    if not config.OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set. Please add it in the Secrets tab.")

    or_model = OPENROUTER_MODEL_MAP.get(model_key)
    if not or_model:
        raise ValueError(f"Unknown OpenRouter model key: {model_key}")

    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://mind-the-gap.replit.app",
        "X-Title": "Mind the Gap Podcast",
    }
    payload = {
        "model": or_model,
        "max_tokens": 16000,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    last_error = None
    for attempt in range(2):
        if attempt > 0:
            log.warning("OpenRouter retry attempt %d for %s…", attempt + 1, or_model)

        try:
            with httpx.Client(timeout=180) as client:
                resp = client.post(OPENROUTER_URL, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()

            choices = data.get("choices", [])
            if not choices:
                raise ValueError(f"OpenRouter returned no choices for {or_model}")

            raw_text = choices[0].get("message", {}).get("content", "")
            finish_reason = choices[0].get("finish_reason")

            if not raw_text.strip():
                raise ValueError(f"OpenRouter returned empty content from {or_model}")

            usage = data.get("usage", {})
            log.info(
                "Script generated via OpenRouter (%s). Tokens — input: %s, output: %s (finish: %s)",
                or_model,
                usage.get("prompt_tokens", "?"),
                usage.get("completion_tokens", "?"),
                finish_reason or "unknown",
            )

            stop_reason = "max_tokens" if finish_reason == "length" else finish_reason
            return raw_text, stop_reason

        except (httpx.HTTPStatusError, httpx.RequestError, ValueError) as exc:
            last_error = exc
            log.warning("OpenRouter call failed (%s): %s", or_model, exc)

    raise RuntimeError(f"OpenRouter call failed after 2 attempts ({or_model}): {last_error}")


def _call_model(
    model_key: str,
    system_prompt: str,
    user_prompt: str,
) -> tuple[str, str | None]:
    if model_key == "claude-opus":
        if not config.ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY is not set.")
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        return _call_claude(client, system_prompt, user_prompt)
    else:
        return _call_openrouter(model_key, system_prompt, user_prompt)


def _model_display_name(model_key: str) -> str:
    for m in podcast_settings.SCRIPT_MODELS:
        if m["id"] == model_key:
            return m["name"]
    return model_key


def _try_generate_with_model(
    model_key: str,
    system_prompt: str,
    user_prompt: str,
    max_retries: int = 2,
) -> tuple[list[dict[str, str]], str]:
    display = _model_display_name(model_key)
    last_error = None

    for attempt in range(1, max_retries + 1):
        log.info(
            "Generating script with %s (attempt %d/%d)…",
            display, attempt, max_retries,
        )
        try:
            t0 = time.time()
            raw_text, stop_reason = _call_model(model_key, system_prompt, user_prompt)
            elapsed = time.time() - t0
            script = _parse_script(raw_text)

            issues = _validate_script(script)
            if issues and stop_reason == "max_tokens" and attempt < max_retries:
                log.warning(
                    "Script truncated and has issues (%s) — retrying.",
                    "; ".join(issues),
                )
                continue

            if issues:
                log.warning("Script has quality issues: %s", "; ".join(issues))

            dialogue_count = sum(1 for t in script if t["speaker"] in ("ALEX", "MAYA"))
            sfx_count = sum(1 for t in script if t["speaker"] == "SFX")
            word_count = sum(
                len(t["text"].split()) for t in script
                if t["speaker"] in ("ALEX", "MAYA")
            )
            log.info(
                "Script from %s: %d turns (%d dialogue, %d SFX), ~%d words in %.0fs.",
                display, len(script), dialogue_count, sfx_count, word_count, elapsed,
            )
            return script, model_key

        except (ValueError, json.JSONDecodeError, RuntimeError) as exc:
            last_error = exc
            if attempt < max_retries:
                log.warning("%s attempt %d failed: %s — retrying.", display, attempt, exc)
            else:
                log.error("%s failed on final attempt: %s", display, exc)

    raise RuntimeError(f"{display} failed after {max_retries} attempts: {last_error}")


def generate_script(
    news_summary: str,
    episode_date: date | None = None,
    max_retries: int = 2,
    model_override: str | None = None,
    story_context: str = "",
) -> list[dict[str, str]]:
    if episode_date is None:
        episode_date = date.today()

    system_prompt = _build_system_prompt()
    user_prompt = _build_user_prompt(news_summary, episode_date, story_context)

    s = podcast_settings.load()
    primary = model_override or s.get("script_model", "claude-opus")
    fallback = s.get("fallback_model", "gemini-3.1-pro")

    try:
        script, used_model = _try_generate_with_model(
            primary, system_prompt, user_prompt, max_retries,
        )
        return script
    except RuntimeError as primary_err:
        if fallback == primary or model_override:
            raise

        log.warning(
            "Primary model %s failed. Auto-switching to fallback %s…",
            _model_display_name(primary),
            _model_display_name(fallback),
        )
        try:
            script, used_model = _try_generate_with_model(
                fallback, system_prompt, user_prompt, max_retries,
            )
            log.info("Fallback model %s succeeded.", _model_display_name(fallback))
            return script
        except RuntimeError as fallback_err:
            raise RuntimeError(
                f"All models failed. Primary ({_model_display_name(primary)}): {primary_err} | "
                f"Fallback ({_model_display_name(fallback)}): {fallback_err}"
            ) from fallback_err


def script_to_plain_text(script: list[dict[str, str]]) -> str:
    lines = []
    for turn in script:
        speaker = turn["speaker"]
        if speaker == "SFX":
            lines.append(f"[Sound: {turn['text']}]")
        else:
            lines.append(f"{speaker}: {turn['text']}")
    return "\n\n".join(lines)


def derive_episode_title(script: list[dict[str, str]], episode_date: date) -> str:
    opener = "\n".join(
        f"{t['speaker']}: {t['text']}"
        for t in script[:6]
        if t["speaker"] in ("ALEX", "MAYA")
    )

    settings = podcast_settings.load()
    model_key = settings.get("script_model", "claude-opus")

    prompt = (
        f"Based on this podcast episode opening, write ONE punchy, "
        f"NPR Planet Money-style episode title (max 8 words, no quotes):\n\n{opener}"
    )

    raw_text, _ = _call_model(model_key, "You generate short podcast episode titles.", prompt)
    title_suffix = raw_text.strip().strip('"').strip("'")
    return f"{config.PODCAST_TITLE_PREFIX}: {title_suffix}"
