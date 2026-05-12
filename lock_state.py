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
                state = json.load(f)
                return state if isinstance(state, dict) else {}
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
    now = datetime.datetime.now()
    until = now + datetime.timedelta(seconds=max(1, seconds) + 5)
    state = _load_state()
    state[prayer] = {
        "until": until.isoformat(timespec="seconds"),
        "date": now.date().isoformat(),
    }
    _save_state(state)


def _entry_until(raw):
    if isinstance(raw, dict):
        raw = raw.get("until")
    if not raw:
        return None
    try:
        return datetime.datetime.fromisoformat(raw)
    except (TypeError, ValueError):
        return None


def _entry_date(raw):
    if isinstance(raw, dict) and raw.get("date"):
        try:
            return datetime.date.fromisoformat(raw["date"])
        except (TypeError, ValueError):
            return None
    until = _entry_until(raw)
    return until.date() if until else None


def is_intentionally_unlocked(prayer_name: str, now=None) -> bool:
    prayer = normalize_prayer_name(prayer_name)
    now = now or datetime.datetime.now()
    state = _load_state()
    until = _entry_until(state.get(prayer))
    if until is None:
        return False
    return now < until


def was_intentionally_unlocked_today(prayer_name: str, now=None) -> bool:
    """Return True for dashboard display even after the lock window expires."""
    prayer = normalize_prayer_name(prayer_name)
    now = now or datetime.datetime.now()
    state = _load_state()
    marked_date = _entry_date(state.get(prayer))
    return marked_date == now.date()
