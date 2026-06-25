"""
KIRA — API Manager
Handles Gemini, OpenRouter, OpenAI with smart fallback
"""

import os
import httpx
from enum import Enum
from typing import Optional
import google.generativeai as genai
from openai import AsyncOpenAI
import logging

logger = logging.getLogger(__name__)


class APIProvider(Enum):
    GEMINI = "gemini"
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    OFFLINE = "offline"


class APIManager:
    def __init__(self):
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.offline_url = os.getenv("OFFLINE_LLM_URL", "http://localhost:11434")
        self.offline_model = os.getenv("OFFLINE_LLM_MODEL", "llama3")

        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        self.current_provider = None
        self.offline_mode = False

        # Setup clients
        self._setup_clients()

    def _setup_clients(self):
        """Setup available API clients"""
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
            logger.info("Gemini API ready")

        if self.openai_key:
            self.openai_client = AsyncOpenAI(api_key=self.openai_key)
            logger.info("OpenAI API ready")

        if self.openrouter_key:
            self.openrouter_client = AsyncOpenAI(
                api_key=self.openrouter_key,
                base_url="https://openrouter.ai/api/v1"
            )
            logger.info("OpenRouter API ready")

    def get_available_providers(self) -> list:
        """Get list of available providers"""
        providers = []
        if self.gemini_key:
            providers.append(APIProvider.GEMINI)
        if self.openrouter_key:
            providers.append(APIProvider.OPENROUTER)
        if self.openai_key:
            providers.append(APIProvider.OPENAI)
        if self.offline_mode:
            providers.append(APIProvider.OFFLINE)
        return providers

    async def switch_offline(self) -> str:
        """Switch to offline LLM mode"""
        self.offline_mode = True
        self.current_provider = APIProvider.OFFLINE
        return "Offline mode mein aa gayi hoon"

    async def switch_online(self) -> str:
        """Switch back to online mode"""
        self.offline_mode = False
        self.current_provider = None
        return "Online mode mein wapas aa gayi hoon"

    async def chat(
        self,
        messages: list,
        system_prompt: str = "",
        max_tokens: int = 150
    ) -> tuple[str, str]:
        """
        Main chat function with auto fallback
        Returns: (response_text, provider_used)
        """

        if self.offline_mode:
            return await self._chat_offline(messages, system_prompt, max_tokens)

        providers = self.get_available_providers()

        for provider in providers:
            try:
                if provider == APIProvider.GEMINI:
                    response = await self._chat_gemini(messages, system_prompt, max_tokens)
                    self.current_provider = provider
                    return response, "gemini"

                elif provider == APIProvider.OPENROUTER:
                    response = await self._chat_openrouter(messages, system_prompt, max_tokens)
                    self.current_provider = provider
                    return response, "openrouter"

                elif provider == APIProvider.OPENAI:
                    response = await self._chat_openai(messages, system_prompt, max_tokens)
                    self.current_provider = provider
                    return response, "openai"

            except Exception as e:
                logger.warning(f"{provider.value} failed: {e}")
                continue

        # All APIs failed
        return "Bhai sab APIs band hain, internet check karo", "none"

    async def _chat_gemini(self, messages: list, system_prompt: str, max_tokens: int) -> str:
        """Chat with Gemini"""
        model = genai.GenerativeModel(
            model_name=self.gemini_model,
            system_instruction=system_prompt if system_prompt else None
        )

        # Convert messages to Gemini format
        gemini_messages = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            gemini_messages.append({
                "role": role,
                "parts": [msg["content"]]
            })

        chat = model.start_chat(history=gemini_messages[:-1])
        response = await chat.send_message_async(
            gemini_messages[-1]["parts"][0],
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.7
            )
        )
        return response.text

    async def _chat_openrouter(self, messages: list, system_prompt: str, max_tokens: int) -> str:
        """Chat with OpenRouter"""
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        response = await self.openrouter_client.chat.completions.create(
            model=self.openrouter_model,
            messages=full_messages,
            max_tokens=max_tokens,
            temperature=0.7
        )
        return response.choices[0].message.content

    async def _chat_openai(self, messages: list, system_prompt: str, max_tokens: int) -> str:
        """Chat with OpenAI"""
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        response = await self.openai_client.chat.completions.create(
            model=self.openai_model,
            messages=full_messages,
            max_tokens=max_tokens,
            temperature=0.7
        )
        return response.choices[0].message.content

    async def _chat_offline(self, messages: list, system_prompt: str, max_tokens: int) -> tuple[str, str]:
        """Chat with local Ollama LLM"""
        async with httpx.AsyncClient() as client:
            full_messages = []
            if system_prompt:
                full_messages.append({"role": "system", "content": system_prompt})
            full_messages.extend(messages)

            response = await client.post(
                f"{self.offline_url}/api/chat",
                json={
                    "model": self.offline_model,
                    "messages": full_messages,
                    "stream": False,
                    "options": {"num_predict": max_tokens}
                },
                timeout=60.0
            )
            data = response.json()
            return data["message"]["content"], "offline"

    async def update_model_settings(self, provider: str, model: str, api_key: str = None):
        """Update model settings dynamically — for 3rd blank slot"""
        if provider == "custom_tts":
            os.environ["CUSTOM_TTS_MODEL"] = model
            if api_key:
                os.environ["CUSTOM_TTS_API_KEY"] = api_key
            return "Custom TTS model set ho gaya"

        elif provider == "openrouter":
            self.openrouter_model = model
            return f"OpenRouter model {model} set ho gaya"

        elif provider == "openai":
            self.openai_model = model
            return f"OpenAI model {model} set ho gaya"

        elif provider == "gemini":
            self.gemini_model = model
            return f"Gemini model {model} set ho gaya"

        return "Provider nahi mila"


# Singleton instance
api_manager = APIManager()
