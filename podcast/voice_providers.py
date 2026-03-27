"""
Multi-provider voice synthesis for Mind Stream.

Supports:
- 11Labs (premium): Best quality, highest cost
- Voxtral/Mistral (high): Good quality, mid cost  
- MiniMax (budget): Standard quality, lowest cost

Provider selection is based on user tier and preferences.
"""
from __future__ import annotations

import base64
import io
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import requests
from pydub import AudioSegment

import config

log = logging.getLogger(__name__)


class VoiceProvider(Enum):
    ELEVENLABS = "11labs"
    VOXTRAL = "voxtral"
    MINIMAX = "minimax"
    OPENAI = "openai"


@dataclass
class VoiceConfig:
    provider: VoiceProvider
    voice_id: str
    quality: str  # "premium", "high", "standard"
    cost_per_1k_chars: float


# Default voice configurations per provider
VOICE_CONFIGS = {
    # 11Labs voices (premium)
    VoiceProvider.ELEVENLABS: {
        "voices": {
            "ALEX": "21m00Tcm4TlvDq8ikWAM",  # Male voice
            "MAYA": "pNInz6obpgDQGcFmaJgB",  # Female voice
        },
        "model": "eleven_v3",
        "cost_per_1k": 0.30,
    },
    # Voxtral/Mistral voices (high quality)
    VoiceProvider.VOXTRAL: {
        "voices": {
            "ALEX": "drew",   # Male - calm, authoritative
            "MAYA": "jessie", # Female - friendly, professional
        },
        "model": "voxtral-24khz",
        "cost_per_1k": 0.15,
    },
    # MiniMax voices (budget)
    VoiceProvider.MINIMAX: {
        "voices": {
            "ALEX": "male-qn_baymax",       # English male
            "MAYA": "female-qn_xingchen",   # Chinese female (for bilingual)
        },
        "model": "speech-01",
        "cost_per_1k": 0.05,
    },
}


def get_provider_for_tier(tier: str, persona: str = "creator") -> VoiceProvider:
    """
    Select optimal voice provider based on user tier and persona.
    
    Priority: Pro+ tiers always get 11Labs for premium quality.
    Free tiers get MiniMax for cost savings.
    Growth tiers get Voxtral for balance.
    """
    tier = tier.lower()
    
    # Pro+ tiers always get premium
    if tier in ["pro", "studio", "enterprise"]:
        return VoiceProvider.ELEVENLABS
    
    # Free tier gets budget
    if tier == "free":
        return VoiceProvider.MINIMAX
    
    # Growth tier gets high quality
    if tier == "growth":
        return VoiceProvider.VOXTRAL
    
    # Persona-based defaults
    persona_defaults = {
        "thought_leader": VoiceProvider.ELEVENLABS,
        "publisher": VoiceProvider.ELEVENLABS,
        "developer": VoiceProvider.VOXTRAL,
        "creator": VoiceProvider.VOXTRAL,
        "learner": VoiceProvider.MINIMAX,
    }
    
    return persona_defaults.get(persona, VoiceProvider.VOXTRAL)


class BaseVoiceProvider(ABC):
    """Abstract base class for voice providers."""
    
    @abstractmethod
    def generate_speech(
        self, 
        text: str, 
        voice_id: str, 
        voice_name: str = "speaker"
    ) -> AudioSegment:
        """Generate speech audio from text."""
        pass
    
    @abstractmethod
    def estimate_cost(self, text: str) -> float:
        """Estimate cost for generating speech."""
        pass


class ElevenLabsProvider(BaseVoiceProvider):
    """11Labs TTS provider (premium quality)."""
    
    def __init__(self):
        self.api_key = config.ELEVENLABS_API_KEY
        if not self.api_key:
            raise RuntimeError("ELEVENLABS_API_KEY is not configured")
        from elevenlabs.client import ElevenLabs
        self.client = ElevenLabs(api_key=self.api_key)
    
    def generate_speech(
        self, 
        text: str, 
        voice_id: str, 
        voice_name: str = "speaker"
    ) -> AudioSegment:
        """Generate speech using 11Labs API."""
        from elevenlabs.types import DialogueInput
        
        log.info("Generating speech via 11Labs: voice=%s, chars=%d", voice_id, len(text))
        
        try:
            audio_bytes = b"".join(
                self.client.text_to_dialogue.convert(
                    inputs=[DialogueInput(voice_id=voice_id, text=text)],
                    output_format="mp3_44100_192",
                    model_id="eleven_v3",
                )
            )
        except Exception as exc:
            log.error("11Labs TTS failed: %s", exc)
            raise RuntimeError(f"11Labs TTS failed: {exc}")
        
        return AudioSegment.from_mp3(io.BytesIO(audio_bytes))
    
    def estimate_cost(self, text: str) -> float:
        chars = len(text)
        return (chars / 1000) * 0.30


class VoxtralProvider(BaseVoiceProvider):
    """Voxtral (Mistral) TTS provider (high quality, mid cost)."""
    
    def __init__(self):
        self.api_key = config.VOXTRAL_API_KEY
        if not self.api_key:
            raise RuntimeError("VOXTRAL_API_KEY is not configured")
    
    def generate_speech(
        self, 
        text: str, 
        voice_id: str, 
        voice_name: str = "speaker"
    ) -> AudioSegment:
        """Generate speech using Voxtral (Mistral) API."""
        log.info("Generating speech via Voxtral: voice=%s, chars=%d", voice_id, len(text))
        
        url = "https://api.mistral.ai/v1/audio/speech"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "voxtral-24khz",
            "voice": voice_id,
            "input": text,
            "response_format": "mp3",
        }
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=60)
            response.raise_for_status()
            audio_bytes = response.content
        except requests.exceptions.RequestException as exc:
            log.error("Voxtral TTS failed: %s", exc)
            raise RuntimeError(f"Voxtral TTS failed: {exc}")
        
        return AudioSegment.from_mp3(io.BytesIO(audio_bytes))
    
    def estimate_cost(self, text: str) -> float:
        chars = len(text)
        return (chars / 1000) * 0.15


class MiniMaxProvider(BaseVoiceProvider):
    """MiniMax TTS provider (budget, standard quality)."""
    
    def __init__(self):
        self.api_key = config.MINIMAX_API_KEY
        self.group_id = config.MINIMAX_GROUP_ID
        if not self.api_key:
            raise RuntimeError("MINIMAX_API_KEY is not configured")
    
    def generate_speech(
        self, 
        text: str, 
        voice_id: str, 
        voice_name: str = "speaker"
    ) -> AudioSegment:
        """Generate speech using MiniMax API."""
        log.info("Generating speech via MiniMax: voice=%s, chars=%d", voice_id, len(text))
        
        url = "https://api.minimax.chat/v1/t2a_v2"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "speech-01",
            "text": text,
            "stream": False,
            "voice_setting": {
                "voice_id": voice_id,
                "speed": 1.0,
                "pitch": 0,
                "volume": 0,
                "emotion": "neutral"
            },
            "audio_setting": {
                "format": "mp3",
                "sample_rate": 32000,
                "bitrate": 128000,
                "channels": 1
            },
            "group_id": self.group_id
        }
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            # MiniMax returns base64 encoded audio
            audio_base64 = result.get("data", {}).get("audio", "")
            if not audio_base64:
                raise RuntimeError("No audio data in MiniMax response")
            
            audio_bytes = base64.b64decode(audio_base64)
        except requests.exceptions.RequestException as exc:
            log.error("MiniMax TTS failed: %s", exc)
            raise RuntimeError(f"MiniMax TTS failed: {exc}")
        except (KeyError, ValueError) as exc:
            log.error("MiniMax response parsing failed: %s", exc)
            raise RuntimeError(f"MiniMax response parsing failed: {exc}")
        
        return AudioSegment.from_mp3(io.BytesIO(audio_bytes))
    
    def estimate_cost(self, text: str) -> float:
        chars = len(text)
        return (chars / 1000) * 0.05


class OpenAIProvider(BaseVoiceProvider):
    """OpenAI TTS provider (fallback option)."""
    
    def __init__(self):
        self.api_key = config.OPENAI_API_KEY
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        from openai import OpenAI
        self.client = OpenAI(api_key=self.api_key)
    
    VOICE_MAP = {
        "ALEX": "onyx",
        "MAYA": "nova",
    }
    
    def generate_speech(
        self, 
        text: str, 
        voice_id: str, 
        voice_name: str = "speaker"
    ) -> AudioSegment:
        """Generate speech using OpenAI TTS."""
        log.info("Generating speech via OpenAI: voice=%s, chars=%d", voice_id, len(text))
        
        # Map voice_id to OpenAI voice name if needed
        openai_voice = self.VOICE_MAP.get(voice_name.upper(), "onyx")
        
        try:
            response = self.client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice=openai_voice,
                input=text,
                response_format="mp3",
            )
            audio_bytes = response.read()
        except Exception as exc:
            log.error("OpenAI TTS failed: %s", exc)
            raise RuntimeError(f"OpenAI TTS failed: {exc}")
        
        return AudioSegment.from_mp3(io.BytesIO(audio_bytes))
    
    def estimate_cost(self, text: str) -> float:
        # OpenAI TTS pricing varies, approximate at $0.20/1k chars
        chars = len(text)
        return (chars / 1000) * 0.20


def get_provider(provider_name: str) -> BaseVoiceProvider:
    """Get voice provider instance by name."""
    provider_name = provider_name.lower()
    
    if provider_name in ("elevenlabs", "11labs"):
        return ElevenLabsProvider()
    elif provider_name == "voxtral":
        return VoxtralProvider()
    elif provider_name == "minimax":
        return MiniMaxProvider()
    elif provider_name == "openai":
        return OpenAIProvider()
    else:
        raise ValueError(f"Unknown voice provider: {provider_name}")


def get_voice_id(provider: VoiceProvider, speaker: str) -> str:
    """Get the default voice ID for a speaker on a given provider."""
    configs = VOICE_CONFIGS.get(provider, {})
    voices = configs.get("voices", {})
    return voices.get(speaker.upper(), list(voices.values())[0] if voices else "")


# Cost tracking
def track_voice_usage(
    user_id: int,
    provider: str, 
    chars_used: int, 
    cost: float,
    db_session = None
):
    """Log voice generation for billing/analytics."""
    log.info(
        "Voice usage: user=%d, provider=%s, chars=%d, cost=$%.4f",
        user_id, provider, chars_used, cost
    )
    
    # Import here to avoid circular imports
    try:
        from saas.db.models import UsageLog
        if db_session:
            usage_log = UsageLog(
                user_id=user_id,
                action="voice_generation",
                provider=provider,
                characters_used=chars_used,
                cost_usd=cost,
            )
            db_session.add(usage_log)
            db_session.commit()
    except ImportError:
        log.warning("Could not import UsageLog for tracking")
    except Exception as exc:
        log.warning("Failed to track voice usage: %s", exc)
