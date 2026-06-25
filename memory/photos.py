"""
KIRA — Photo Memory
Analyze photos, remember with names
"""

import os
import base64
import json
import time
from pathlib import Path
import httpx

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


class PhotoMemory:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.openai_key = os.getenv("OPENAI_API_KEY", "")

    async def analyze_photo(self, image_bytes: bytes, filename: str = "photo.jpg") -> str:
        """
        Analyze photo and return description
        """
        # Try Gemini Vision first
        if self.gemini_key:
            try:
                return await self._analyze_gemini(image_bytes)
            except Exception:
                pass

        # Fallback to OpenAI Vision
        if self.openai_key:
            try:
                return await self._analyze_openai(image_bytes)
            except Exception:
                pass

        return "Photo analyze nahi ho payi"

    async def _analyze_gemini(self, image_bytes: bytes) -> str:
        """Analyze with Gemini Vision"""
        b64 = base64.b64encode(image_bytes).decode()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}",
                json={
                    "contents": [{
                        "parts": [
                            {
                                "inline_data": {
                                    "mime_type": "image/jpeg",
                                    "data": b64
                                }
                            },
                            {
                                "text": "Is photo mein kya hai? Short mein batao — objects, people, place. Hinglish mein."
                            }
                        ]
                    }],
                    "generationConfig": {"maxOutputTokens": 200}
                },
                timeout=30.0
            )
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    async def _analyze_openai(self, image_bytes: bytes) -> str:
        """Analyze with OpenAI Vision"""
        b64 = base64.b64encode(image_bytes).decode()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.openai_key}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                            },
                            {
                                "type": "text",
                                "text": "Is photo mein kya hai? Short mein batao. Hinglish mein."
                            }
                        ]
                    }],
                    "max_tokens": 200
                },
                timeout=30.0
            )
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def save_photo_with_label(
        self,
        image_bytes: bytes,
        label: str,
        filename: str = "photo.jpg"
    ) -> tuple[str, str]:
        """
        Save photo with a label
        Returns: (file_path, analysis)
        """
        # Save file
        safe_label = label.replace(" ", "_").lower()
        filepath = UPLOAD_DIR / f"{safe_label}_{int(time.time())}.jpg"
        with open(filepath, "wb") as f:
            f.write(image_bytes)

        # Analyze
        analysis = await self.analyze_photo(image_bytes, filename)

        return str(filepath), analysis

    async def search_photos(self, query: str) -> list:
        """Search saved photos by label"""
        photos = []
        query_lower = query.lower()
        for f in UPLOAD_DIR.iterdir():
            if query_lower in f.name.lower():
                photos.append(str(f))
        return photos


# Singleton
photo_memory = PhotoMemory()
