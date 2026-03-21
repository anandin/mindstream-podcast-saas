"""
Generates podcast audio using ElevenLabs text_to_dialogue (GenFM) or
OpenAI TTS, with simple sequential mixing pipeline.

Audio pipeline
──────────────
1. Generate ALL host dialogue via GenFM or OpenAI TTS (batched, 2 speakers)
2. Generate ambient SFX clips via ElevenLabs Sound Effects API
3. Load intro & outro jingles
4. Mix: intro jingle (fade out) → dialogue with SFX beds → outro jingle (fade in)
"""
from __future__ import annotations

import io
import logging
import shutil
import tempfile
import time
from pathlib import Path

from elevenlabs.client import ElevenLabs
from elevenlabs.types import DialogueInput
from pydub import AudioSegment

import config
import settings as podcast_settings

log = logging.getLogger(__name__)

MAX_CHARS_PER_CALL = 3000

DIALOGUE_SPEAKERS = {"ALEX", "MAYA"}
SKIP_FOR_GENFM = {"SFX"}


def _get_voice_map() -> dict[str, str]:
    s = podcast_settings.load()
    return {
        "ALEX": s.get("voice_alex", podcast_settings.MALE_VOICES[0]["id"]),
        "MAYA": s.get("voice_maya", podcast_settings.FEMALE_VOICES[0]["id"]),
    }


def _build_dialogue_inputs(
    turns: list[dict[str, str]],
    voice_map: dict[str, str],
) -> list[DialogueInput]:
    inputs: list[DialogueInput] = []
    for turn in turns:
        speaker = turn["speaker"].upper()
        text = turn["text"].strip()
        if not text or speaker in SKIP_FOR_GENFM:
            continue
        voice_id = voice_map.get(speaker)
        if not voice_id:
            log.warning("Unknown speaker '%s' — skipping.", speaker)
            continue
        inputs.append(DialogueInput(voice_id=voice_id, text=text))
    return inputs


GENFM_MODEL = "eleven_v3"


def _genfm_call(
    client: ElevenLabs,
    inputs: list[DialogueInput],
    retries: int = 5,
) -> bytes:
    for attempt in range(1, retries + 1):
        try:
            return b"".join(
                client.text_to_dialogue.convert(
                    inputs=inputs,
                    output_format="mp3_44100_192",
                    model_id=GENFM_MODEL,
                )
            )
        except Exception as exc:
            wait = min(2 ** attempt, 30)
            log.warning(
                "GenFM attempt %d/%d failed (%s: %s) — retrying in %ds",
                attempt, retries, type(exc).__name__, exc, wait,
            )
            if attempt < retries:
                time.sleep(wait)
    raise RuntimeError(f"ElevenLabs GenFM failed after {retries} attempts.")


def _generate_dialogue_audio(
    client: ElevenLabs,
    turns: list[dict[str, str]],
    voice_map: dict[str, str],
) -> AudioSegment:
    dialogue_turns = [t for t in turns if t["speaker"].upper() in DIALOGUE_SPEAKERS]
    inputs = _build_dialogue_inputs(dialogue_turns, voice_map)
    if not inputs:
        return AudioSegment.silent(duration=100)

    total_words = sum(len(t["text"].split()) for t in dialogue_turns)
    log.info(
        "Generating dialogue via GenFM — %d turns, ~%d words.",
        len(inputs), total_words,
    )

    batches: list[list[DialogueInput]] = []
    current_batch: list[DialogueInput] = []
    current_chars = 0
    for inp in inputs:
        turn_chars = len(inp.text)
        if current_batch and current_chars + turn_chars > MAX_CHARS_PER_CALL:
            batches.append(current_batch)
            current_batch = []
            current_chars = 0
        current_batch.append(inp)
        current_chars += turn_chars
    if current_batch:
        batches.append(current_batch)

    chunks: list[bytes] = []
    for batch_num, batch in enumerate(batches, 1):
        batch_chars = sum(len(i.text) for i in batch)
        log.info(
            "  GenFM batch %d/%d (%d turns, %d chars)…",
            batch_num, len(batches), len(batch), batch_chars,
        )
        chunks.append(_genfm_call(client, batch))

    audio_bytes = b"".join(chunks)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    tmp_path.write_bytes(audio_bytes)
    audio = AudioSegment.from_mp3(tmp_path)
    tmp_path.unlink(missing_ok=True)
    return audio


OPENAI_VOICE_MAP = {
    "ALEX": "onyx",
    "MAYA": "nova",
}

OPENAI_TTS_MODEL = "gpt-4o-mini-tts"


def _openai_tts_call(
    client,
    text: str,
    voice: str,
    instructions: str = "",
    retries: int = 3,
) -> bytes:
    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            kwargs: dict = {
                "model": OPENAI_TTS_MODEL,
                "voice": voice,
                "input": text,
                "response_format": "mp3",
            }
            if instructions:
                kwargs["instructions"] = instructions
            response = client.audio.speech.create(**kwargs)
            return response.read()
        except Exception as exc:
            last_exc = exc
            exc_name = type(exc).__name__
            if "insufficient_quota" in str(exc) or "RateLimitError" in exc_name:
                raise RuntimeError(
                    "OpenAI API quota exceeded — please add credits at "
                    "platform.openai.com/settings/billing or switch TTS "
                    "provider to ElevenLabs in the Configure tab."
                ) from exc
            if "AuthenticationError" in exc_name:
                raise RuntimeError(
                    "OpenAI API key is invalid. Please update OPENAI_API_KEY "
                    "in Secrets."
                ) from exc
            wait = min(2 ** attempt, 15)
            log.warning(
                "OpenAI TTS attempt %d/%d failed (%s: %s) — retrying in %ds",
                attempt, retries, exc_name, exc, wait,
            )
            if attempt < retries:
                time.sleep(wait)
    raise RuntimeError(
        f"OpenAI TTS failed after {retries} attempts: {last_exc}"
    )


def _generate_dialogue_openai(
    turns: list[dict[str, str]],
) -> AudioSegment:
    from openai import OpenAI

    if not config.OPENAI_API_KEY:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Please add it in the Secrets tab."
        )

    client = OpenAI(api_key=config.OPENAI_API_KEY)

    s = podcast_settings.load()
    voice_directions = {
        "ALEX": s.get("voice_direction_alex", ""),
        "MAYA": s.get("voice_direction_maya", ""),
    }

    dialogue_turns = [t for t in turns if t["speaker"].upper() in DIALOGUE_SPEAKERS]
    if not dialogue_turns:
        return AudioSegment.silent(duration=100)

    total_words = sum(len(t["text"].split()) for t in dialogue_turns)
    log.info(
        "Generating dialogue via OpenAI TTS (%s) — %d turns, ~%d words.",
        OPENAI_TTS_MODEL, len(dialogue_turns), total_words,
    )

    chunks: list[AudioSegment] = []
    pause_between = AudioSegment.silent(duration=350)

    for i, turn in enumerate(dialogue_turns):
        speaker = turn["speaker"].upper()
        text = turn["text"].strip()
        if not text:
            continue
        voice = OPENAI_VOICE_MAP.get(speaker, "onyx")
        instructions = voice_directions.get(speaker, "")
        log.info(
            "  OpenAI TTS turn %d/%d (%s → %s, %d chars)…",
            i + 1, len(dialogue_turns), speaker, voice, len(text),
        )
        audio_bytes = _openai_tts_call(client, text, voice, instructions=instructions)
        segment = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
        if chunks:
            chunks.append(pause_between)
        chunks.append(segment)

    if not chunks:
        return AudioSegment.silent(duration=100)

    combined = chunks[0]
    for seg in chunks[1:]:
        combined += seg
    return combined


def _generate_sfx_clips(
    script: list[dict[str, str]],
) -> list[tuple[int, AudioSegment]]:
    sfx_entries = [
        (i, t) for i, t in enumerate(script) if t["speaker"].upper() == "SFX"
    ]
    if not sfx_entries:
        return []

    from sfx_generator import generate_sfx

    clips: list[tuple[int, AudioSegment]] = []
    for idx, entry in sfx_entries:
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            generate_sfx(entry["text"], 8.0, tmp_path)
            clip = AudioSegment.from_mp3(tmp_path)
            clips.append((idx, clip))
            tmp_path.unlink(missing_ok=True)
        except Exception as exc:
            log.warning("Failed to generate SFX '%s': %s", entry["text"], exc)

    log.info("Generated %d/%d ambient SFX clips.", len(clips), len(sfx_entries))
    return clips


def _speedup(audio: AudioSegment, factor: float) -> AudioSegment:
    import subprocess
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as src_f:
        src_path = Path(src_f.name)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as dst_f:
        dst_path = Path(dst_f.name)
    try:
        audio.export(str(src_path), format="wav")
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(src_path),
                "-filter:a", f"atempo={factor}",
                str(dst_path),
            ],
            check=True,
            capture_output=True,
        )
        return AudioSegment.from_wav(dst_path)
    except Exception as exc:
        log.warning("ffmpeg atempo speedup failed (%s), skipping speedup.", exc)
        return audio
    finally:
        src_path.unlink(missing_ok=True)
        dst_path.unlink(missing_ok=True)


def _mix_episode(
    dialogue: AudioSegment,
    sfx_clips: list[tuple[int, AudioSegment]],
    script: list[dict[str, str]],
    intro: AudioSegment | None = None,
    outro: AudioSegment | None = None,
) -> AudioSegment:
    final = AudioSegment.empty()

    if intro is not None:
        faded_intro = intro.fade_out(2000)
        final += faded_intro

    dialogue_mixed = dialogue
    duration_ms = len(dialogue)

    dialogue_indices = [
        i for i, t in enumerate(script) if t["speaker"].upper() in DIALOGUE_SPEAKERS
    ]
    total_dialogue = len(dialogue_indices)

    for sfx_script_idx, clip in sfx_clips:
        preceding = sum(1 for di in dialogue_indices if di < sfx_script_idx)
        position_ratio = preceding / max(total_dialogue, 1)
        position_ms = int(position_ratio * duration_ms)
        position_ms = max(0, min(position_ms, duration_ms - 1000))

        quiet_clip = clip - 15
        if len(quiet_clip) > 8000:
            quiet_clip = quiet_clip[:8000]
        quiet_clip = quiet_clip.fade_in(800).fade_out(800)

        dialogue_mixed = dialogue_mixed.overlay(quiet_clip, position=position_ms)

    final += dialogue_mixed

    if outro is not None:
        faded_outro = outro.fade_in(2000)
        final += faded_outro

    return final


def generate_audio(
    script: list[dict[str, str]],
    output_path: Path,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not shutil.which("ffmpeg"):
        raise RuntimeError(
            "ffmpeg is required for audio mixing but was not found on PATH."
        )

    cfg = podcast_settings.load()
    tts_provider = cfg.get("tts_provider", "elevenlabs")

    log.info("=== STEP 3a: Generating all dialogue (provider: %s) ===", tts_provider)

    if tts_provider == "openai":
        dialogue_audio = _generate_dialogue_openai(script)
    else:
        if not config.ELEVENLABS_API_KEY:
            raise RuntimeError(
                "ELEVENLABS_API_KEY is not set. Please add it in the Secrets tab."
            )
        client = ElevenLabs(api_key=config.ELEVENLABS_API_KEY)
        voice_map = _get_voice_map()
        log.info("Voice mapping: ALEX=%s, MAYA=%s", voice_map["ALEX"], voice_map["MAYA"])
        dialogue_audio = _generate_dialogue_audio(client, script, voice_map)

    log.info("=== STEP 3b: Generating ambient SFX clips ===")
    sfx_clips = _generate_sfx_clips(script)

    log.info("=== STEP 3c: Loading intro/outro jingles ===")
    from sfx_generator import generate_intro_jingle, generate_outro_jingle

    intro_audio = None
    outro_audio = None
    try:
        intro_path = generate_intro_jingle()
        intro_audio = AudioSegment.from_mp3(intro_path)
    except Exception as exc:
        log.warning("Failed to generate intro jingle: %s", exc)

    try:
        outro_path = generate_outro_jingle()
        outro_audio = AudioSegment.from_mp3(outro_path)
    except Exception as exc:
        log.warning("Failed to generate outro jingle: %s", exc)

    speed_pct = cfg.get("audio_speed", 110)
    speed_factor = speed_pct / 100.0
    if speed_factor != 1.0:
        log.info("=== STEP 3d: Speeding up dialogue (%.2fx) ===", speed_factor)
        dialogue_audio = _speedup(dialogue_audio, speed_factor)
    else:
        log.info("=== STEP 3d: Dialogue speed at 1.0x (natural) — skipping speedup ===")

    log.info("=== STEP 3e: Mixing final episode ===")
    final = _mix_episode(
        dialogue=dialogue_audio,
        sfx_clips=sfx_clips,
        script=script,
        intro=intro_audio,
        outro=outro_audio,
    )

    final.export(str(output_path), format="mp3", bitrate="192k")

    duration_sec = len(final) / 1000
    file_size = output_path.stat().st_size
    log.info(
        "Final episode: %.1f min, %.1f MB → %s",
        duration_sec / 60,
        file_size / 1_048_576,
        output_path,
    )
    return output_path


def generate_episode_description(
    script: list[dict[str, str]],
    episode_title: str,
) -> str:
    dialogue = [t for t in script if t["speaker"] in ("ALEX", "MAYA")]
    opener = " ".join(t["text"] for t in dialogue[:2])[:400]
    closer = dialogue[-1]["text"][:200] if dialogue else ""

    return (
        f"{episode_title}\n\n"
        f"{opener}...\n\n"
        f"In today's episode, Alex and Maya explore how Toronto's economy, AI's rapid "
        f"evolution, and behavioural science intersect — and what it all means for how "
        f"we live and work.\n\n"
        f"Takeaway: {closer}\n\n"
        f"New episodes drop every weekday morning."
    )
