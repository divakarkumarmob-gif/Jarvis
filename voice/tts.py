"""
KIRA — Text to Speech
3 Providers: Google, ElevenLabs, Custom
"""

import os
import httpx
import base64
from gtts import gTTS
from pathlib import Path
import io

AUDIO_DIR = Path("audio_cache")
AUDIO_DIR.mkdir(exist_ok=True)


class TTSManager:
    def __init__(self):
        self.provider = os.getenv("TTS_PROVIDER", "google")
        self.elevenlabs_key = os.getenv("ELEVENLABS_API_KEY", "")
        self.elevenlabs_voice = os.getenv("ELEVENLABS_VOICE_ID", "")
        self.custom_key = os.getenv("CUSTOM_TTS_API_KEY", "")
        self.custom_url = os.getenv("CUSTOM_TTS_URL", "")
        self.custom_model = os.getenv("CUSTOM_TTS_MODEL", "")
        self.google_lang = os.getenv("TTS_GOOGLE_LANGUAGE", "hi")
        self.google_tld = os.getenv("TTS_GOOGLE_TLD", "co.in")

    def switch_provider(self, provider: str) -> str:
        """Switch TTS provider"""
        valid = ["google", "elevenlabs", "custom"]
        if provider in valid:
            self.provider = provider
            os.environ["TTS_PROVIDER"] = provider
            return f"Voice {provider} pe switch ho gayi"
        return "Provider nahi mila"

    async def speak(self, text: str) -> bytes | None:
        """
        Convert text to speech
        Returns audio bytes
        """
        if not text or text.strip() == "":
            return None

        # Try current provider first, fallback if fails
        providers = [self.provider]

        # Add fallbacks
        all_providers = ["google", "elevenlabs", "custom"]
        for p in all_providers:
            if p not in providers:
                providers.append(p)

        for provider in providers:
            try:
                if provider == "google":
                    return await self._speak_google(text)
                elif provider == "elevenlabs" and self.elevenlabs_key:
                    return await self._speak_elevenlabs(text)
                elif provider == "custom" and self.custom_url:
                    return await self._speak_custom(text)
            except Exception:
                continue

        return None

    async def _speak_google(self, text: str) -> bytes:
        """Google TTS — Indian voice"""
        tts = gTTS(
            text=text,
            lang=self.google_lang,
            tld=self.google_tld,
            slow=False
        )
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        audio_io.seek(0)
        return audio_io.read()

    async def _speak_elevenlabs(self, text: str) -> bytes:
        """ElevenLabs TTS — Ultra human voice"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{self.elevenlabs_voice}",
                headers={
                    "xi-api-key": self.elevenlabs_key,
                    "Content-Type": "application/json"
                },
                json={
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75
                    }
                },
                timeout=30.0
            )
            return response.content

    async def _speak_custom(self, text: str) -> bytes:
        """Custom TTS provider"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.custom_url,
                headers={
                    "Authorization": f"Bearer {self.custom_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "text": text,
                    "model": self.custom_model
                },
                timeout=30.0
            )
            return response.content

    def set_custom_provider(self, url: str, api_key: str, model: str) -> str:
        """Set custom TTS provider — via Kira command"""
        self.custom_url = url
        self.custom_key = api_key
        self.custom_model = model
        os.environ["CUSTOM_TTS_URL"] = url
        os.environ["CUSTOM_TTS_API_KEY"] = api_key
        os.environ["CUSTOM_TTS_MODEL"] = model
        return "Custom TTS provider set ho gaya"


# Singleton
tts_manager = TTSManager()
