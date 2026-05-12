"""
PrayerLock Windows Service
==========================
Runs as a Windows service (SYSTEM account) and:

  1. Checks the prayer schedule every 60 seconds.
  2. Shows a configurable warning overlay before Athan.
  3. Launches the lock screen (via a subprocess call to main.py --lockscreen)
     when a lock window opens.
  4. Records each completed lock to the streak tracker.
  5. Refreshes the schedule at midnight so the cache never goes stale.

All source files live in the same flat directory — no subpackages.

Install / control via main.py:
    python main.py --install-service
    python main.py --start-service
    python main.py --uninstall-service

Or directly with sc.exe after install:
    sc start PrayerLockService
    sc stop  PrayerLockService
"""

import os
import sys
import time
import logging
import datetime
import threading
import subprocess
from typing import Optional

# ── Make sure the app directory is importable ────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from logger import setup_logging
    setup_logging("service")
except Exception:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

# ── pywin32 service base classes ──────────────────────────────────────────────
_WIN32_AVAILABLE = False
try:
    import win32service      # Added this import
    import win32serviceutil
    import win32event
    import servicemanager
    _WIN32_AVAILABLE = True
except ImportError:
    logger.warning("pywin32 not installed. Service mode will be unavailable.")
    # Provide stub so the rest of the module is still importable for testing.
    class _StubBase:
        _svc_name_         = "PrayerLockService"
        _svc_display_name_ = "PrayerLock Service"
        _svc_description_  = "Monitors prayer times and locks the screen."
    win32service = type("_", (), {"SERVICE_AUTO_START": 2})()
    win32serviceutil = type("_", (), {"ServiceFramework": _StubBase})()


# ── Constants ─────────────────────────────────────────────────────────────────

# How often (seconds) the main loop checks the prayer schedule.
POLL_INTERVAL = 5

# Minimum retry gap (seconds) between consecutive warning overlay launch attempts.
WARNING_COOLDOWN = 60


# ─────────────────────────────────────────────────────────────────────────────
# Helper: launch the lock screen in a separate process
# ─────────────────────────────────────────────────────────────────────────────

def _launch_lockscreen(prayer_name: str, duration_seconds: int):
    """
    Spawn the lock screen as a detached GUI process.

    When running as a compiled PyInstaller exe the executable is re-invoked
    with --lockscreen flags.  When running from source, sys.executable
    (the Python interpreter) is used with main.py.
    """
    if getattr(sys, "frozen", False):
        # Running as a bundled .exe — re-invoke self with flags.
        cmd = [sys.executable,
               "--lockscreen",
               "--prayer", prayer_name,
               "--duration", str(duration_seconds)]
    else:
        # Running from source.
        main_script = os.path.join(ROOT, "main.py")
        cmd = [sys.executable, main_script,
               "--lockscreen",
               "--prayer", prayer_name,
               "--duration", str(duration_seconds)]

    logger.info(f"Launching lock screen: {subprocess.list2cmdline(cmd)}")
    proc = _launch_lockscreen_for_active_user(cmd)
    if proc is not None:
        return proc

    try:
        proc = subprocess.Popen(
            cmd,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                          | subprocess.DETACHED_PROCESS,
            close_fds=True,
        )
        return proc
    except Exception as e:
        logger.error(f"Failed to launch lock screen: {e}")
        return None


def _launch_warning_overlay(
    prayer_name: str,
    athan_seconds: int,
    lock_seconds: int,
    suppress_seconds: int,
):
    if getattr(sys, "frozen", False):
        cmd = [
            sys.executable,
            "--warning-overlay",
            "--prayer", prayer_name,
            "--athan-seconds", str(athan_seconds),
            "--lock-seconds", str(lock_seconds),
            "--suppress-seconds", str(suppress_seconds),
        ]
    else:
        main_script = os.path.join(ROOT, "main.py")
        cmd = [
            sys.executable,
            main_script,
            "--warning-overlay",
            "--prayer", prayer_name,
            "--athan-seconds", str(athan_seconds),
            "--lock-seconds", str(lock_seconds),
            "--suppress-seconds", str(suppress_seconds),
        ]

    logger.info(f"Launching warning overlay: {subprocess.list2cmdline(cmd)}")
    proc = _launch_lockscreen_for_active_user(cmd)
    if proc is not None:
        return proc

    try:
        return subprocess.Popen(
            cmd,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                          | subprocess.DETACHED_PROCESS,
            close_fds=True,
        )
    except Exception as e:
        logger.error(f"Failed to launch warning overlay: {e}")
        return None


def _launch_lockscreen_for_active_user(cmd: list):
    """
    Launch the GUI in the logged-in user's desktop session.

    Windows services run in session 0, so a direct Popen from the service will
    not appear on the user's desktop. When the service is running as LocalSystem,
    WTSQueryUserToken lets us create the process in the active console session.
    """
    if not _WIN32_AVAILABLE:
        return None

    token = primary_token = env = None
    try:
        import win32con
        import win32process
        import win32profile
        import win32security
        import win32ts

        session_id = win32ts.WTSGetActiveConsoleSessionId()
        if session_id == 0xFFFFFFFF:
            logger.warning("No active console session found for lock screen.")
            return None

        token = win32ts.WTSQueryUserToken(session_id)
        primary_token = win32security.DuplicateTokenEx(
            token,
            win32con.MAXIMUM_ALLOWED,
            None,
            win32security.SecurityImpersonation,
            win32security.TokenPrimary,
        )

        try:
            env = win32profile.CreateEnvironmentBlock(primary_token, False)
        except Exception as e:
            logger.warning(f"Could not build user environment block: {e}")
            env = None

        startup = win32process.STARTUPINFO()
        startup.lpDesktop = "winsta0\\default"
        startup.dwFlags = win32process.STARTF_USESHOWWINDOW
        startup.wShowWindow = win32con.SW_SHOWNORMAL

        creation_flags = (
            win32process.CREATE_NEW_CONSOLE
            | getattr(win32process, "CREATE_UNICODE_ENVIRONMENT", 0)
        )
        command_line = subprocess.list2cmdline(cmd)
        process_handle, thread_handle, process_id, _thread_id = win32process.CreateProcessAsUser(
            primary_token,
            None,
            command_line,
            None,
            None,
            False,
            creation_flags,
            env,
            ROOT,
            startup,
        )
        logger.info(
            f"Lock screen launched in active session {session_id}: "
            f"{command_line} (pid={process_id})"
        )
        thread_handle.Close()
        return _ProcessHandleAdapter(process_handle)
    except Exception as e:
        logger.warning(
            f"Active-session launch failed; falling back to service session: {e}"
        )
        return None
    finally:
        if env is not None:
            try:
                win32profile.DestroyEnvironmentBlock(env)
            except Exception:
                pass
        for handle in (primary_token, token):
            if handle is not None:
                try:
                    handle.Close()
                except Exception:
                    pass


class _ProcessHandleAdapter:
    """Small adapter exposing poll() for a pywin32 process handle."""

    def __init__(self, process_handle):
        self._process_handle = process_handle
        self._closed = False

    def poll(self):
        if self._closed:
            return 0

        try:
            import win32event

            result = win32event.WaitForSingleObject(self._process_handle, 0)
            if result == win32event.WAIT_TIMEOUT:
                return None
            self._process_handle.Close()
            self._closed = True
            return 0
        except Exception:
            self._closed = True
            return 0

    def terminate(self):
        if self._closed:
            return
        try:
            import win32process

            win32process.TerminateProcess(self._process_handle, 0)
            self._process_handle.Close()
        except Exception:
            pass
        self._closed = True


# ─────────────────────────────────────────────────────────────────────────────
# Helper: Windows toast notification (non-blocking, best-effort)
# ─────────────────────────────────────────────────────────────────────────────

def _show_toast(title: str, message: str):
    """Show a Windows balloon / toast notification from the service."""
    try:
        # Try win10toast first (nicer, modern toast)
        from win10toast import ToastNotifier
        notifier = ToastNotifier()
        notifier.show_toast(title, message, duration=8, threaded=True)
        return
    except ImportError:
        pass

    # Fallback: use servicemanager's LogInfoMsg to write to the Event Log
    # (visible but not a desktop notification)
    try:
        servicemanager.LogInfoMsg(f"{title}: {message}")
    except Exception:
        pass

    # Final fallback: PowerShell toast (Windows 10+)
    try:
        ps = (
            f"[Windows.UI.Notifications.ToastNotificationManager, "
            f"Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; "
            f"$t = [Windows.UI.Notifications.ToastTemplateType]::ToastText02; "
            f"$x = [Windows.UI.Notifications.ToastNotificationManager]"
            f"::GetTemplateContent($t); "
            f"$x.GetElementsByTagName('text')[0].AppendChild($x.CreateTextNode('{title}')) | Out-Null; "
            f"$x.GetElementsByTagName('text')[1].AppendChild($x.CreateTextNode('{message}')) | Out-Null; "
            f"$n = [Windows.UI.Notifications.ToastNotification]::new($x); "
            f"[Windows.UI.Notifications.ToastNotificationManager]"
            f"::CreateToastNotifier('PrayerLock').Show($n)"
        )
        subprocess.Popen(
            ["powershell", "-WindowStyle", "Hidden", "-Command", ps],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except Exception as e:
        logger.debug(f"Toast fallback failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Core scheduler loop (runs in its own thread)
# ─────────────────────────────────────────────────────────────────────────────

class _SchedulerLoop:
    """
    Runs on a background thread inside the service.

    State tracked per run:
      _locked_prayers   : set of prayer names whose lock window is currently
                          active (prevents re-launching the screen every tick).
      _warned_prayers   : dict of prayer_name → timestamp of last warning overlay
                          launch attempt.
      _lockscreen_procs : dict of prayer_name → Popen object so we can check
                          whether the process is still alive.
    """

    def __init__(self, stop_event: threading.Event):
        self._stop = stop_event
        self._locked_prayers: set = set()
        self._warned_prayers: dict = {}
        self._lockscreen_procs: dict = {}
        self._warning_procs: dict = {}
        self._config = None
        self._scheduler = None

    # ── Initialise heavy imports inside the thread ────────────────────────────

    def _init_components(self):
        from config_manager import ConfigManager
        from prayer_scheduler import PrayerScheduler
        self._config = ConfigManager()
        self._scheduler = PrayerScheduler(self._config)
        logger.info("SchedulerLoop components initialised.")

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self):
        logger.info("SchedulerLoop starting.")
        try:
            self._init_components()
        except Exception as e:
            logger.error(f"Failed to initialise components: {e}")
            return

        last_date = datetime.date.today()

        while not self._stop.is_set():
            try:
                today = datetime.date.today()

                # Midnight cache flush
                if today != last_date:
                    logger.info("New day — flushing prayer schedule cache.")
                    self._scheduler._schedule_cache = None
                    self._locked_prayers.clear()
                    self._warned_prayers.clear()
                    self._lockscreen_procs.clear()
                    self._warning_procs.clear()
                    last_date = today

                self._tick()

            except Exception as e:
                logger.error(f"Tick error: {e}", exc_info=True)

            # Sleep in 5-second increments so we can respond to stop quickly.
            for _ in range(POLL_INTERVAL // 5):
                if self._stop.is_set():
                    break
                time.sleep(5)

        logger.info("SchedulerLoop stopped.")

    # ── Single tick ───────────────────────────────────────────────────────────

    def _tick(self):
        now = datetime.datetime.now()
        schedule = self._scheduler.get_schedule()

        for entry in schedule:
            name = entry.name

            # ── 1. Warning overlay before Athan ──────────────────────────────
            seconds_until_athan = (entry.prayer_time - now).total_seconds()
            seconds_until_lock = (entry.lock_at - now).total_seconds()
            warning_lead_seconds = self._get_overlay_lead_seconds()
            if (
                self._service_overlay_enabled()
                and warning_lead_seconds > 0
                and seconds_until_athan <= warning_lead_seconds
                and seconds_until_lock > 0
                and not self._is_intentionally_unlocked(name, now)
            ):
                last_warned = self._warned_prayers.get(name, 0)
                proc = self._warning_procs.get(name)
                proc_running = proc is not None and proc.poll() is None
                if not proc_running and time.time() - last_warned >= WARNING_COOLDOWN:
                    mins_left = int(seconds_until_athan // 60)
                    self._warned_prayers[name] = time.time()
                    logger.info(
                        f"Warning overlay: {entry.display_name} in ~{mins_left} min."
                    )
                    proc = _launch_warning_overlay(
                        entry.display_name,
                        max(1, int(seconds_until_athan)),
                        max(1, int(seconds_until_lock)),
                        max(1, int((entry.unlock_at - now).total_seconds())),
                    )
                    if proc:
                        self._warning_procs[name] = proc

            # ── 2. Lock window active? ────────────────────────────────────────
            in_window = entry.lock_at <= now < entry.unlock_at
            if in_window and self._is_intentionally_unlocked(name, now):
                self._locked_prayers.add(name)
                self._lockscreen_procs.pop(name, None)
                continue

            if in_window and name not in self._locked_prayers:
                # Enter lock window — launch the lock screen.
                self._terminate_proc(self._warning_procs.pop(name, None))
                duration_sec = max(
                    1,
                    int((entry.unlock_at - now).total_seconds())
                )
                logger.info(
                    f"Lock window opened for {entry.display_name} "
                    f"({duration_sec}s remaining)."
                )
                self._locked_prayers.add(name)
                proc = _launch_lockscreen(entry.display_name, duration_sec)
                if proc:
                    self._lockscreen_procs[name] = proc

            elif not in_window and name in self._locked_prayers:
                # Lock window has closed — record streak and clean up.
                logger.info(f"Lock window closed for {entry.display_name}.")
                self._locked_prayers.discard(name)

                proc = self._lockscreen_procs.pop(name, None)
                unlocked_early = proc is not None and proc.poll() is None
                # If the process is still running when the window expired,
                # it will close itself (timer expired path in lockscreen.py).

                self._record_lock(name, unlocked_early=False)

            elif in_window and name in self._locked_prayers:
                # We are inside the lock window and already launched the screen.
                # If the process died unexpectedly (crash / taskkill), relaunch.
                proc = self._lockscreen_procs.get(name)
                if proc is not None and proc.poll() is not None:
                    # Process exited while lock window is still active.
                    now2 = datetime.datetime.now()
                    remaining = max(1, int((entry.unlock_at - now2).total_seconds()))
                    logger.warning(
                        f"Lock screen process for {entry.display_name} "
                        f"exited unexpectedly — relaunching."
                    )
                    new_proc = _launch_lockscreen(entry.display_name, remaining)
                    if new_proc:
                        self._lockscreen_procs[name] = new_proc

    # ── Streak recording ──────────────────────────────────────────────────────

    def _is_intentionally_unlocked(self, prayer_name: str, now) -> bool:
        try:
            from lock_state import is_intentionally_unlocked
            return is_intentionally_unlocked(prayer_name, now)
        except Exception as e:
            logger.debug(f"Intentional unlock check failed: {e}")
            return False

    def _get_overlay_lead_seconds(self) -> int:
        try:
            minutes = int(self._config.get("overlay_warning_minutes", 5))
        except Exception:
            minutes = 5
        return max(0, minutes) * 60

    def _service_overlay_enabled(self) -> bool:
        try:
            return bool(self._config.get("service_shows_overlay", False))
        except Exception:
            return False

    def _terminate_proc(self, proc):
        if proc is None:
            return
        try:
            if proc.poll() is None and hasattr(proc, "terminate"):
                proc.terminate()
        except Exception:
            pass

    def _record_lock(self, prayer_name: str, unlocked_early: bool):
        try:
            from anti_bypass import StreakTracker
            tracker = StreakTracker(self._config)
            tracker.record_lock(prayer_name, unlocked_early=unlocked_early)
            logger.info(
                f"Streak recorded for {prayer_name} "
                f"(early_unlock={unlocked_early})."
            )
        except Exception as e:
            logger.error(f"Failed to record streak: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Windows Service class
# ─────────────────────────────────────────────────────────────────────────────

if _WIN32_AVAILABLE:
    _ServiceBase = win32serviceutil.ServiceFramework
else:
    _ServiceBase = object


class PrayerLockService(_ServiceBase):
    """
    Windows service wrapper.

    pywin32 calls SvcDoRun() from a dedicated thread after the SCM
    confirms the service is running.  We spin up _SchedulerLoop on a
    daemon thread and wait on a win32event until the SCM sends a stop.
    """

    _svc_name_         = "PrayerLockService"
    _svc_display_name_ = "PrayerLock Prayer Monitor"
    _svc_description_  = (
        "Monitors Islamic prayer times and activates the PrayerLock "
        "screen lock at each prayer interval."
    )
    _svc_start_type_ = win32service.SERVICE_AUTO_START     # Use win32service instead

    def __init__(self, args):
        if _WIN32_AVAILABLE:
            win32serviceutil.ServiceFramework.__init__(self, args)
        self._thread_stop = threading.Event()
        self._hWaitStop = (
            win32event.CreateEvent(None, 0, 0, None)
            if _WIN32_AVAILABLE
            else None
        )
        self._loop_thread = None
        self._loop = None

    # ── SCM callbacks ─────────────────────────────────────────────────────────

    def SvcStop(self):
        logger.info("Service stop requested.")
        if _WIN32_AVAILABLE:
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self._hWaitStop)
        self._thread_stop.set()

    def SvcDoRun(self):
        logger.info("PrayerLockService starting.")
        if _WIN32_AVAILABLE:
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, ""),
            )

        self._start_loop()

        if _WIN32_AVAILABLE:
            # Block until the SCM sends a stop signal.
            win32event.WaitForSingleObject(
                self._hWaitStop,
                win32event.INFINITE,
            )
        else:
            # Fallback for non-service direct execution (testing).
            while not self._thread_stop.is_set():
                time.sleep(1)

        self._stop_loop()
        logger.info("PrayerLockService stopped.")

    # ── Internal ──────────────────────────────────────────────────────────────

    def _start_loop(self):
        self._loop = _SchedulerLoop(self._thread_stop)
        self._loop_thread = threading.Thread(
            target=self._loop.run,
            name="PrayerSchedulerLoop",
            daemon=True,
        )
        self._loop_thread.start()
        logger.info("SchedulerLoop thread started.")

    def _stop_loop(self):
        self._thread_stop.set()
        if self._loop_thread and self._loop_thread.is_alive():
            self._loop_thread.join(timeout=15)
        logger.info("SchedulerLoop thread joined.")


# ─────────────────────────────────────────────────────────────────────────────
# Allow running directly for quick manual testing (not as a service)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if _WIN32_AVAILABLE:
        win32serviceutil.HandleCommandLine(PrayerLockService)
    else:
        print("pywin32 not available. Running scheduler loop directly for testing...")
        stop = threading.Event()
        loop = _SchedulerLoop(stop)
        try:
            loop.run()
        except KeyboardInterrupt:
            stop.set()
