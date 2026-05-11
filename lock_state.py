"""
Shared lock-window state for the service, tray fallback, and lockscreen.
"""
import datetime
import json
import os
from pathlib import Path


if os.name == "nt":
    _STATE_DIR = Path("C:/ProgramData/PrayerLock")
else:
    _STATE_DIR = Path.home() / ".config" / "PrayerLock"

_UNLOCK_FILE = _STATE_DIR / "intentional_unlocks.json"

_PRAYER_ALIASES = {
    "fajr": "fajr",
    "dhuhr": "dhuhr",
    "zuhr": "dhuhr",
    "asr": "asr",
    "maghrib": "maghrib",
    "isha": "isha",
}


def normalize_prayer_name(name: str) -> str:
    key = "".join(ch for ch in str(name).lower() if ch.isalpha())
    return _PRAYER_ALIASES.get(key, key)


def _load_state() -> dict:
    try:
        if _UNLOCK_FILE.exists():
            with open(_UNLOCK_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_state(state: dict) -> None:
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = _UNLOCK_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    tmp.replace(_UNLOCK_FILE)


def mark_intentionally_unlocked(prayer_name: str, seconds: int) -> None:
    """Remember that the current lock window was unlocked by password."""
    prayer = normalize_prayer_name(prayer_name)
    until = datetime.datetime.now() + datetime.timedelta(seconds=max(1, seconds) + 5)
    state = _load_state()
    state[prayer] = until.isoformat(timespec="seconds")
    _save_state(state)


def is_intentionally_unlocked(prayer_name: str, now=None) -> bool:
    prayer = normalize_prayer_name(prayer_name)
    now = now or datetime.datetime.now()
    state = _load_state()
    raw_until = state.get(prayer)
    if not raw_until:
        return False
    try:
        until = datetime.datetime.fromisoformat(raw_until)
    except ValueError:
        return False
    return now < until
