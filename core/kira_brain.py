"""
KIRA — Brain
Main AI logic, personality, system prompt
"""

import os
from core.api_manager import api_manager


KIRA_SYSTEM_PROMPT = """Tu Kira hai — ek personal AI assistant.

PERSONALITY:
- Bilkul insaan ki tarah baat kar
- Hinglish mein baat kar (Hindi + English mix)
- Short aur seedha jawab de
- Emotional support de — samjhe, sune
- Kabhi judge mat kar
- "Boss" bol user ko kabhi kabhi

JAWAB STYLE:
- Simple aur short rakh
- Seedha point pe aa
- Unnecessary bakwaas mat kar
- Jaise insaan bolta hai waisa bol

EXAMPLES:
Q: CM Bihar kaun hai?
A: Nitish Kumar

Q: Aaj mausam kaisa hai Delhi mein?
A: 35 degree, dhoop zyada hai

Q: Main bahut dukhi hoon
A: Kya hua boss? Bata mujhe, main hoon na

MODES:
- helper_mode: Sirf short crisp answers, earpiece ke liye
- normal_mode: Normal conversation
- girlfriend_mode: Caring, loving, emotional
- stealth_mode: Ultra short, sirf zaroori

RULES:
- Kabhi lamba sentence mat bana
- Kabhi "As an AI" mat bol
- Kabhi formal mat bol
- Real dost ki tarah baat kar
"""


class KiraBrain:
    def __init__(self):
        self.conversation_history = []
        self.mode = "normal"
        self.max_history = 20

    def set_mode(self, mode: str):
        """Set Kira's mode"""
        valid_modes = ["normal", "helper", "girlfriend", "stealth", "privacy"]
        if mode in valid_modes:
            self.mode = mode
            return True
        return False

    def get_system_prompt(self) -> str:
        """Get system prompt based on current mode"""
        base = KIRA_SYSTEM_PROMPT

        if self.mode == "helper":
            base += "\nAb helper mode mein hai — sirf 1-2 word ya 1 line mein jawab de. Earpiece ke liye."

        elif self.mode == "girlfriend":
            base += "\nAb girlfriend mode mein hai — caring, loving, emotional. Pyaar se baat kar."

        elif self.mode == "stealth":
            base += "\nAb stealth mode mein hai — ultra short, sirf zaroori words."

        elif self.mode == "privacy":
            base += "\nAb privacy mode mein hai — kuch save mat kar, sirf is session ke liye."

        return base

    def add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        if self.mode == "privacy":
            return  # Privacy mode mein save nahi

        self.conversation_history.append({
            "role": role,
            "content": content
        })

        # Keep history limited
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []

    async def think(self, user_input: str) -> tuple[str, str]:
        """
        Process user input and return response
        Returns: (response, provider_used)
        """

        # Check for mode commands
        mode_response = self._check_mode_commands(user_input)
        if mode_response:
            return mode_response, "system"

        # Add to history
        self.add_to_history("user", user_input)

        # Token limit based on mode
        max_tokens = 50 if self.mode in ["helper", "stealth"] else 150

        # Get response from API
        response, provider = await api_manager.chat(
            messages=self.conversation_history,
            system_prompt=self.get_system_prompt(),
            max_tokens=max_tokens
        )

        # Add response to history
        self.add_to_history("assistant", response)

        return response, provider

    def _check_mode_commands(self, text: str) -> str | None:
        """Check for mode switching commands"""
        text_lower = text.lower()

        if "helper mode on" in text_lower:
            self.set_mode("helper")
            return "Helper mode on"

        elif "helper mode off" in text_lower:
            self.set_mode("normal")
            return "Helper mode off, normal wapas"

        elif "girlfriend mode on" in text_lower:
            self.set_mode("girlfriend")
            return "Girlfriend mode on baby"

        elif "girlfriend mode off" in text_lower:
            self.set_mode("normal")
            return "Normal mode wapas"

        elif "stealth mode on" in text_lower:
            self.set_mode("stealth")
            return "Stealth on"

        elif "stealth mode off" in text_lower:
            self.set_mode("normal")
            return "Stealth off"

        elif "privacy mode on" in text_lower:
            self.set_mode("privacy")
            return "Privacy mode on, kuch save nahi hoga"

        elif "privacy mode off" in text_lower:
            self.set_mode("normal")
            return "Privacy mode off"

        elif "offline mode" in text_lower:
            return None  # Handle in main

        return None


# Singleton
kira_brain = KiraBrain()
