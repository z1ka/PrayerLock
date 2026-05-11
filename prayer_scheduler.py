"""
PrayerLock Prayer Scheduler
Calculates prayer times and determines lock schedule.
Uses Aladhan API with offline adhan fallback.
"""
import datetime
import logging
import threading
import requests
from dataclasses import dataclass
from typing import Optional, Tuple, List
import pytz

logger = logging.getLogger(__name__)

# Prayer display names and arabic equivalents
PRAYER_META = {
    "fajr":    {"display": "Fajr",    "arabic": "الفجر"},
    "dhuhr":   {"display": "Dhuhr",   "arabic": "الظهر"},
    "asr":     {"display": "Asr",     "arabic": "العصر"},
    "maghrib": {"display": "Maghrib", "arabic": "المغرب"},
    "isha":    {"display": "Isha",    "arabic": "العشاء"},
}

# Aladhan API method IDs
ALADHAN_METHODS = {
    "UmmAlQura": 4,
    "MWL":       3,
    "ISNA":      2,
    "Egypt":     5,
    "Karachi":   1,
    "Gulf":      8,
    "Kuwait":    9,
    "Qatar":    10,
    "Singapore": 11,
    "Turkey":   13,
}


@dataclass
class PrayerEntry:
    name: str            # e.g. "fajr"
    display_name: str    # e.g. "Fajr"
    arabic_name: str     # e.g. "الفجر"
    prayer_time: datetime.datetime
    lock_at: datetime.datetime
    unlock_at: datetime.datetime


class PrayerScheduler:
    """
    Calculates today's prayer schedule and exposes helper methods
    consumed by the tray app and service.
    """

    def __init__(self, config_manager):
        self.config = config_manager
        self._schedule_cache: Optional[List[PrayerEntry]] = None
        self._cache_date: Optional[datetime.date] = None
        self._lock = threading.Lock()

    # ── Public API ─────────────────────────────────────────────────────────────

    def get_schedule(self) -> List[PrayerEntry]:
        """Return today's prayer schedule (cached per day)."""
        today = datetime.date.today()
        with self._lock:
            if self._schedule_cache is None or self._cache_date != today:
                self._schedule_cache = self._build_schedule(today)
                self._cache_date = today
        return self._schedule_cache

    def get_formatted_schedule(self) -> List[dict]:
        """Return schedule as a list of dicts for the dashboard table."""
        entries = self.get_schedule()
        result = []
        for e in entries:
            result.append({
                "name": e.name,
                "display_name": e.display_name,
                "arabic_name": e.arabic_name,
                "time": e.prayer_time.strftime("%I:%M %p"),
                "lock_at": e.lock_at.strftime("%I:%M %p"),
            })
        return result

    def should_be_locked(self) -> Optional[PrayerEntry]:
        """
        Returns the active PrayerEntry if we are currently in a lock window,
        otherwise None.
        """
        now = datetime.datetime.now()
        for entry in self.get_schedule():
            if entry.lock_at <= now < entry.unlock_at:
                return entry
        return None

    def get_next_lock_event(self) -> Optional[Tuple[PrayerEntry, str]]:
        """
        Returns (PrayerEntry, event_type) for the next upcoming lock or unlock,
        where event_type is 'lock' or 'unlock'.
        """
        now = datetime.datetime.now()
        candidates = []

        for entry in self.get_schedule():
            if entry.lock_at > now:
                candidates.append((entry.lock_at, entry, "lock"))
            if entry.unlock_at > now:
                candidates.append((entry.unlock_at, entry, "unlock"))

        if not candidates:
            return None

        candidates.sort(key=lambda x: x[0])
        _, entry, event_type = candidates[0]
        return entry, event_type

    # ── Internal schedule builder ─────────────────────────────────────────────

    def _build_schedule(self, date: datetime.date) -> List[PrayerEntry]:
        """Build PrayerEntry list for the given date."""
        cfg = self.config.load()
        lat = cfg.get("latitude", 21.3891)
        lng = cfg.get("longitude", 39.8579)
        method = cfg.get("calculation_method", "UmmAlQura")
        tz_name = cfg.get("timezone", "Asia/Riyadh")
        delay_min = cfg.get("lock_delay_minutes", 0)
        duration_min = cfg.get("lock_duration_minutes", 15)

        raw_times = self._fetch_prayer_times(date, lat, lng, method, tz_name)

        try:
            tz = pytz.timezone(tz_name)
        except Exception:
            tz = pytz.UTC

        entries = []
        for name in ["fajr", "dhuhr", "asr", "maghrib", "isha"]:
            time_str = raw_times.get(name)
            if not time_str:
                continue
            try:
                prayer_dt = self._parse_time(date, time_str, tz)
                lock_dt = prayer_dt + datetime.timedelta(minutes=delay_min)
                unlock_dt = lock_dt + datetime.timedelta(minutes=duration_min)
                meta = PRAYER_META.get(name, {"display": name.capitalize(), "arabic": ""})
                entries.append(PrayerEntry(
                    name=name,
                    display_name=meta["display"],
                    arabic_name=meta["arabic"],
                    prayer_time=prayer_dt,
                    lock_at=lock_dt,
                    unlock_at=unlock_dt,
                ))
            except Exception as e:
                logger.warning(f"Could not parse prayer time for {name}: {e}")

        return entries

    def _parse_time(self, date: datetime.date, time_str: str,
                    tz: pytz.BaseTzInfo) -> datetime.datetime:
        """Parse '05:30' into a timezone-aware datetime for today."""
        # Strip AM/PM suffix if present (Aladhan sometimes returns "05:30 (BST)")
        time_str = time_str.split("(")[0].strip()
        t = datetime.datetime.strptime(time_str, "%H:%M").time()
        naive = datetime.datetime.combine(date, t)
        try:
            aware = tz.localize(naive, is_dst=None)
        except Exception:
            aware = tz.localize(naive)
        return aware.replace(tzinfo=None)  # strip tz for naive comparison with datetime.now()

    # ── Time fetching ─────────────────────────────────────────────────────────

    def _fetch_prayer_times(self, date: datetime.date, lat: float, lng: float,
                            method: str, tz_name: str) -> dict:
        """Try Aladhan API first, fall back to adhan."""
        try:
            return self._fetch_from_aladhan(date, lat, lng, method)
        except Exception as e:
            logger.warning(f"Aladhan API failed ({e}), using offline calculation.")
            return self._calculate_offline(date, lat, lng, method, tz_name)

    def _fetch_from_aladhan(self, date: datetime.date, lat: float, lng: float,
                             method: str) -> dict:
        method_id = ALADHAN_METHODS.get(method, 4)
        url = (
            f"https://api.aladhan.com/v1/timings/"
            f"{date.day}-{date.month}-{date.year}"
            f"?latitude={lat}&longitude={lng}&method={method_id}"
        )
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        timings = data["data"]["timings"]

        return {
            "fajr":    timings.get("Fajr", ""),
            "dhuhr":   timings.get("Dhuhr", ""),
            "asr":     timings.get("Asr", ""),
            "maghrib": timings.get("Maghrib", ""),
            "isha":    timings.get("Isha", ""),
        }

    def _calculate_offline(self, date: datetime.date, lat: float, lng: float,
                            method: str, tz_name: str) -> dict:
        """Offline fallback using adhan."""
        try:
            import adhan
            from adhan import Coordinates, CalculationMethod, PrayerTimes

            coords = Coordinates(lat, lng)

            method_map = {
                "UmmAlQura":  CalculationMethod.UmmAlQura,
                "MWL":        CalculationMethod.MuslimWorldLeague,
                "ISNA":       CalculationMethod.NorthAmerica,
                "Egypt":      CalculationMethod.Egyptian,
                "Karachi":    CalculationMethod.Karachi,
                "Kuwait":     CalculationMethod.Kuwait,
                "Qatar":      CalculationMethod.Qatar,
                "Singapore":  CalculationMethod.Singapore,
                "Turkey":     CalculationMethod.Turkey,
                "Gulf":       CalculationMethod.UmmAlQura,  # closest match
            }
            params = method_map.get(method, CalculationMethod.UmmAlQura)()

            date_components = adhan.DateComponents(date.year, date.month, date.day)
            pt = PrayerTimes(coords, date_components, params)

            def fmt(t):
                if t is None:
                    return ""
                if isinstance(t, datetime.datetime):
                    return t.strftime("%H:%M")
                return str(t)

            return {
                "fajr":    fmt(pt.fajr),
                "dhuhr":   fmt(pt.dhuhr),
                "asr":     fmt(pt.asr),
                "maghrib": fmt(pt.maghrib),
                "isha":    fmt(pt.isha),
            }
        except Exception as e:
            logger.error(f"Offline calculation failed: {e}")
            # Last resort: return hardcoded approximate times so the app doesn't crash
            return {
                "fajr":    "05:00",
                "dhuhr":   "12:15",
                "asr":     "15:30",
                "maghrib": "18:00",
                "isha":    "19:30",
            }
