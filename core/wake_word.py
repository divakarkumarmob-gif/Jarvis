"""
KIRA — Wake Word & Session Manager
Handles: Kira ON/OFF, timeout, announcements
"""

import time
import asyncio


class SessionManager:
    def __init__(self):
        self.is_active = False
        self.timeout_seconds = 120  # 2 minutes
        self.last_activity = None
        self.warning_sent = False
        self._timeout_task = None

    def activate(self) -> str:
        """Activate Kira"""
        self.is_active = True
        self.last_activity = time.time()
        self.warning_sent = False
        return "Kira is live, main sun rahi hoon"

    def deactivate(self) -> str:
        """Deactivate Kira"""
        self.is_active = False
        self.last_activity = None
        if self._timeout_task:
            self._timeout_task.cancel()
        return "Kira going to sleep, phir milenge"

    def update_activity(self):
        """Update last activity time"""
        self.last_activity = time.time()
        self.warning_sent = False

    def check_timeout(self) -> str | None:
        """
        Check if timeout reached
        Returns announcement message or None
        """
        if not self.is_active or not self.last_activity:
            return None

        elapsed = time.time() - self.last_activity

        # Warning at 1min 45sec
        if elapsed >= 105 and not self.warning_sent:
            self.warning_sent = True
            return "Boss 15 second mein band ho rahi hoon, kuch bolna hai?"

        # Auto off at 2 min
        if elapsed >= self.timeout_seconds:
            self.deactivate()
            return "Kira going to sleep, phir milenge"

        return None

    def process_text(self, text: str) -> tuple[str, bool]:
        """
        Process text for wake word / stop word
        Returns: (action, should_process)
        """
        text_lower = text.lower().strip()

        # Wake word detection
        if "kira" in text_lower and not self.is_active:
            msg = self.activate()
            return msg, False

        # Stop command
        if "kira stop" in text_lower and self.is_active:
            msg = self.deactivate()
            return msg, False

        # If active, update activity
        if self.is_active:
            self.update_activity()
            return "", True

        return "", False

    def get_status(self) -> dict:
        """Get current status"""
        return {
            "active": self.is_active,
            "last_activity": self.last_activity,
            "uptime": time.time() - self.last_activity if self.last_activity else 0
        }


# Singleton
session_manager = SessionManager()
