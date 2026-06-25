"""
KIRA — Speech to Text
Using Groq Whisper — Fast & Free
"""

import os
import httpx
from pathlib import Path


class STTManager:
    def __init__(self):
        self.groq_key = os.getenv("GROQ_API_KEY", "")
        self.language = os.getenv("DEFAULT_LANGUAGE", "hi")

    async def transcribe(self, audio_bytes: bytes, filename: str = "audio.webm") -> str:
        """
        Convert speech to text
        Returns transcribed text
        """
        if not audio_bytes:
            return ""

        # Try Groq first
        if self.groq_key:
            try:
                return await self._transcribe_groq(audio_bytes, filename)
            except Exception as e:
                pass

        # Fallback to OpenAI Whisper
        openai_key = os.getenv("OPENAI_API_KEY", "")
        if openai_key:
            try:
                return await self._transcribe_openai(audio_bytes, filename, openai_key)
            except Exception:
                pass

        return ""

    async def _transcribe_groq(self, audio_bytes: bytes, filename: str) -> str:
        """Groq Whisper — Fast STT"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {self.groq_key}"},
                files={"file": (filename, audio_bytes, "audio/webm")},
                data={
                    "model": "whisper-large-v3",
                    "language": "hi",
                    "response_format": "text"
                },
                timeout=30.0
            )
            return response.text.strip()

    async def _transcribe_openai(self, audio_bytes: bytes, filename: str, api_key: str) -> str:
        """OpenAI Whisper fallback"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                files={"file": (filename, audio_bytes, "audio/webm")},
                data={
                    "model": "whisper-1",
                    "language": "hi"
                },
                timeout=30.0
            )
            data = response.json()
            return data.get("text", "").strip()


# Singleton
stt_manager = STTManager()
