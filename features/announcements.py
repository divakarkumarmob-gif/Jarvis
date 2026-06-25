"""
KIRA — Announcements
Status voice messages, API switch alerts
"""


class Announcements:

    MESSAGES = {
        # Session
        "wake": "Kira is live, main sun rahi hoon",
        "sleep": "Kira going to sleep, phir milenge",
        "warning_15": "Boss 15 second mein band ho rahi hoon",
        "restart": "Kira restarting, thodi der mein wapas hoon",
        "back": "Kira is live, fresh start",

        # PIN
        "pin_required": "Boss PIN batao",
        "pin_correct": "Welcome back",
        "pin_wrong": "Galat PIN",
        "pin_locked": "Kira lock ho gayi",

        # API Switch
        "switch_gemini": "Gemini pe aa gayi",
        "switch_openrouter": "OpenRouter pe switch ho gayi",
        "switch_openai": "OpenAI pe aa gayi",
        "switch_offline": "Offline mode mein aa gayi, local brain activate",
        "switch_online": "Online wapas, cloud connected",

        # Mode
        "helper_on": "Helper mode on",
        "helper_off": "Helper mode off",
        "girlfriend_on": "Girlfriend mode on baby",
        "stealth_on": "Stealth on",
        "privacy_on": "Privacy mode on, kuch save nahi hoga",

        # Errors
        "no_internet": "Internet nahi hai, offline mode mein aa rahi hoon",
        "api_error": "Thodi problem aayi, dobara try karo",
        "mic_error": "Awaaz nahi aa rahi, mic check karo",
        "all_apis_down": "Sab APIs band hain, internet check karo",

        # Device
        "battery_low": "Boss charge laga lo",
        "battery_full": "Full charge ho gaya, nikaalo",
        "bt_connected": "Earbuds connect ho gaye",
        "bt_disconnected": "Earbuds disconnect ho gaye",
        "wifi_weak": "Internet slow hai",
    }

    @classmethod
    def get(cls, key: str, **kwargs) -> str:
        """Get announcement message"""
        msg = cls.MESSAGES.get(key, "")
        if kwargs:
            msg = msg.format(**kwargs)
        return msg

    @classmethod
    def api_switch(cls, from_api: str, to_api: str) -> str:
        """API switch announcement"""
        return f"{to_api} pe switch ho gayi"

    @classmethod
    def error_message(cls, error_type: str) -> str:
        """Simple error in human language"""
        errors = {
            "connection": "Internet check karo",
            "timeout": "Response nahi mila, dobara bolo",
            "auth": "API key galat hai",
            "rate_limit": "Thodi der mein try karo",
            "server": "Server mein problem hai",
            "unknown": "Kuch gadbad ho gayi"
        }
        return errors.get(error_type, errors["unknown"])


announcements = Announcements()
