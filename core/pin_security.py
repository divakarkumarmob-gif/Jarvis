"""
KIRA — PIN Security System
Dynamic PIN, lockout, 24hr reset
"""

import os
import json
import time
import hashlib
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
PIN_FILE = DATA_DIR / "pin_data.json"


class PinSecurity:
    def __init__(self):
        self.max_attempts = int(os.getenv("MAX_PIN_ATTEMPTS", 5))
        self.lockout_attempts = int(os.getenv("LOCKOUT_ATTEMPTS", 10))
        self.pin_reset_hours = int(os.getenv("PIN_RESET_HOURS", 24))
        self._load_data()

    def _load_data(self):
        """Load PIN data from file"""
        if PIN_FILE.exists():
            with open(PIN_FILE, "r") as f:
                self.data = json.load(f)
        else:
            default_pin = os.getenv("DEFAULT_PIN", "1234")
            self.data = {
                "pin_hash": self._hash_pin(default_pin),
                "attempts": 0,
                "locked": False,
                "last_unlock": None,
                "last_restart": time.time()
            }
            self._save_data()

    def _save_data(self):
        """Save PIN data to file"""
        with open(PIN_FILE, "w") as f:
            json.dump(self.data, f)

    def _hash_pin(self, pin: str) -> str:
        """Hash PIN securely"""
        salt = os.getenv("SECRET_KEY", "kira_salt")
        return hashlib.sha256(f"{pin}{salt}".encode()).hexdigest()

    def verify_pin(self, pin: str) -> tuple[bool, str]:
        """
        Verify PIN
        Returns: (success, message)
        """
        # Check if locked
        if self.data["locked"]:
            return False, "Kira locked hai, restart karo"

        # Check attempts
        if self.data["attempts"] >= self.lockout_attempts:
            self.data["locked"] = True
            self._save_data()
            return False, "Bahut zyada galat try — Kira lock ho gayi"

        # Verify
        if self._hash_pin(pin) == self.data["pin_hash"]:
            self.data["attempts"] = 0
            self.data["last_unlock"] = time.time()
            self._save_data()
            return True, "PIN sahi hai"

        else:
            self.data["attempts"] += 1
            remaining = self.max_attempts - self.data["attempts"]
            self._save_data()

            if remaining <= 0:
                return False, f"Galat PIN — {self.lockout_attempts - self.data['attempts']} chances baki"
            return False, f"Galat PIN — {remaining} chances baki"

    def change_pin(self, old_pin: str, new_pin: str) -> tuple[bool, str]:
        """Change PIN"""
        success, msg = self.verify_pin(old_pin)
        if not success:
            return False, msg

        if len(new_pin) < 4:
            return False, "PIN kam se kam 4 digits ka hona chahiye"

        self.data["pin_hash"] = self._hash_pin(new_pin)
        self.data["attempts"] = 0
        self._save_data()
        return True, "PIN change ho gaya"

    def needs_pin_check(self) -> bool:
        """Check if PIN is needed — after 24hr restart"""
        if not self.data.get("last_unlock"):
            return True

        hours_since = (time.time() - self.data["last_unlock"]) / 3600
        return hours_since >= self.pin_reset_hours

    def is_locked(self) -> bool:
        return self.data["locked"]

    def unlock(self):
        """Admin unlock"""
        self.data["locked"] = False
        self.data["attempts"] = 0
        self._save_data()

    def verify_security_code(self, code: str) -> bool:
        """Verify security code for code analysis/updates"""
        stored = os.getenv("SECURITY_CODE", "")
        return code == stored


# Singleton
pin_security = PinSecurity()
