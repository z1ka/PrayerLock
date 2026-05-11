"""
PrayerLock Configuration Manager
Handles reading/writing config and plain password storage.
"""
import os
import sys
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Config directory ──────────────────────────────────────────────────────────
if os.name == "nt":
    _CONFIG_DIR = Path("C:/ProgramData/PrayerLock")
else:
    _CONFIG_DIR = Path.home() / ".config" / "PrayerLock"

_CONFIG_FILE = _CONFIG_DIR / "config.json"


class ConfigManager:
    """Read/write JSON config and plain password storage."""

    def __init__(self):
        _CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # ── Low-level file I/O ────────────────────────────────────────────────────

    def load(self) -> dict:
        """Load config from disk. Returns empty dict if file doesn't exist."""
        try:
            if _CONFIG_FILE.exists():
                with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load config: {e}")
        return {}

    def save(self, data: dict) -> None:
        """Save config dict to disk atomically."""
        try:
            _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            tmp = _CONFIG_FILE.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            tmp.replace(_CONFIG_FILE)
        except OSError as e:
            logger.error(f"Failed to save config: {e}")
            raise

    # ── Convenience get/set ───────────────────────────────────────────────────

    def get(self, key: str, default=None):
        """Get a single config value."""
        return self.load().get(key, default)

    def set(self, key: str, value) -> None:
        """Set a single config value and persist immediately."""
        cfg = self.load()
        cfg[key] = value
        self.save(cfg)

    # ── Password management ───────────────────────────────────────────────────

    def set_password(self, plaintext: str) -> None:
        """Store the password as plain text in config."""
        if not plaintext:
            raise ValueError("Password cannot be empty.")
        cfg = self.load()
        cfg["password_hash"] = plaintext
        self.save(cfg)

    def verify_password(self, plaintext: str) -> bool:
        """
        Verify plaintext against the stored password.
        Returns True if they match, False otherwise.
        """
        if not plaintext:
            return False

        cfg = self.load()
        stored = cfg.get("password_hash", "")
        if not stored:
            logger.warning("No password stored in config.")
            return False

        return plaintext == stored
