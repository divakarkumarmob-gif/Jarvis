"""
KIRA — Google Search
Live search for real-time info
"""

import os
import httpx
from core.api_manager import api_manager


class SearchManager:
    def __init__(self):
        self.google_key = os.getenv("GOOGLE_SEARCH_API_KEY", "")
        self.google_cx = os.getenv("GOOGLE_SEARCH_CX", "")

    async def search(self, query: str) -> str:
        """
        Search Google and return simple answer
        """
        # Try Google Custom Search
        if self.google_key and self.google_cx:
            try:
                results = await self._google_search(query)
                if results:
                    return await self._summarize(query, results)
            except Exception:
                pass

        # Fallback — ask AI directly with search intent
        return await self._ai_search(query)

    async def _google_search(self, query: str) -> list:
        """Google Custom Search API"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/customsearch/v1",
                params={
                    "key": self.google_key,
                    "cx": self.google_cx,
                    "q": query,
                    "num": 3
                },
                timeout=10.0
            )
            data = response.json()
            items = data.get("items", [])
            return [
                {
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", "")
                }
                for item in items
            ]

    async def _summarize(self, query: str, results: list) -> str:
        """Summarize search results simply"""
        context = "\n".join([f"{r['title']}: {r['snippet']}" for r in results])

        prompt = f"""User ne poochha: {query}

Search results:
{context}

Sirf seedha jawab do — 1-2 line mein. Hinglish mein. Short aur simple."""

        response, _ = await api_manager.chat(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80
        )
        return response

    async def _ai_search(self, query: str) -> str:
        """Fallback — AI direct answer"""
        response, _ = await api_manager.chat(
            messages=[{"role": "user", "content": f"Short mein batao: {query}"}],
            max_tokens=80
        )
        return response

    def is_search_query(self, text: str) -> bool:
        """Detect if query needs live search"""
        keywords = [
            "abhi", "aaj", "kal", "score", "news", "khabar",
            "price", "rate", "mausam", "weather", "live",
            "current", "latest", "kaun hai", "cm ", "pm ",
            "president", "winner", "result", "stock", "rupee"
        ]
        text_lower = text.lower()
        return any(kw in text_lower for kw in keywords)


# Singleton
search_manager = SearchManager()
