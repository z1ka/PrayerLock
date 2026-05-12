"""
PrayerLock — Entry Point
========================
Handles all launch modes:

    python main.py                  → normal launch (setup wizard or tray)
    python main.py --tray           → launch tray app directly
    python main.py --lockscreen     → launch lock screen (called by service)
    python main.py --install-service  → register Windows service
    python main.py --uninstall-service → remove Windows service
    python main.py --start-service  → start the service

All source files live in the same flat directory — no subpackages.
"""

import sys
import os
import argparse
import ctypes
import subprocess

_SINGLE_INSTANCE_HANDLES = []

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

# Ensure the app's own directory is on the import path regardless of
# how/where Python is invoked (installed service, tray startup, etc.)
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def parse_args():
    parser = argparse.ArgumentParser(prog="PrayerLock")
    parser.add_argument("--tray",              action="store_true", help="Launch system tray app")
    parser.add_argument("--lockscreen",        action="store_true", help="Show lock screen")
    parser.add_argument("--warning-overlay",   action="store_true", help="Show pre-Athan warning overlay")
    parser.add_argument("--prayer",            type=str, default="Dhuhr",
                        help="Prayer name (used with --lockscreen/--warning-overlay)")
    parser.add_argument("--duration",          type=int, default=900,
                        help="Lock duration in seconds (used with --lockscreen)")
    parser.add_argument("--athan-seconds",     type=int, default=600,
                        help="Seconds until Athan (used with --warning-overlay)")
    parser.add_argument("--lock-seconds",      type=int, default=1200,
                        help="Seconds until lock (used with --warning-overlay)")
    parser.add_argument("--suppress-seconds",  type=int, default=1800,
                        help="Seconds to suppress lock after password dismissal")
    parser.add_argument("--ignore-dismissal",  action="store_true",
                        help="Show warning overlay even if this prayer was skipped")
    parser.add_argument("--parent-pid",        type=int, default=0,
                        help="Close warning overlay when this launcher process exits")
    parser.add_argument("--install-service",   action="store_true", help="Install Windows service")
    parser.add_argument("--uninstall-service", action="store_true", help="Uninstall Windows service")
    parser.add_argument("--start-service",     action="store_true", help="Start Windows service")
    parser.add_argument("--stop-service",      action="store_true", help="Stop Windows service")
    parser.add_argument("--verify-password-file", type=str, default="",
                        help="Verify master password from a file and exit")
    args, unknown = parser.parse_known_args()
    if unknown:
        try:
            from logger import setup_logging
            setup_logging("main")
            import logging
            logging.getLogger(__name__).warning(
                "Ignoring unknown command-line arguments: %s",
                unknown,
            )
        except Exception:
            pass
    return args


def is_admin() -> bool:
    if os.name != "nt":
        return True
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin() -> bool:
    """Ask Windows for UAC elevation and relaunch the current command."""
    if os.name != "nt" or is_admin():
        return False
    argv = sys.argv[1:] if getattr(sys, "frozen", False) else sys.argv
    params = subprocess.list2cmdline(argv)
    result = ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        params,
        ROOT,
        1,
    )
    return result > 32


def cleanup_legacy_user_startup():
    """Remove the old per-user startup entry that duplicated the installer entry."""
    if os.name != "nt":
        return
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        )
        try:
            winreg.DeleteValue(key, "PrayerLock")
        except FileNotFoundError:
            pass
        winreg.CloseKey(key)
    except Exception:
        pass


def acquire_instance_lock(name: str) -> bool:
    """Return False if another process already owns this app-level lock."""
    if os.name != "nt":
        return True
    try:
        handle = ctypes.windll.kernel32.CreateMutexW(
            None,
            False,
            name,
        )
        if not handle:
            return True
        if ctypes.windll.kernel32.GetLastError() == 183:
            ctypes.windll.kernel32.CloseHandle(handle)
            return False
        _SINGLE_INSTANCE_HANDLES.append(handle)
        return True
    except Exception:
        return True


def acquire_tray_instance_lock() -> bool:
    """Return False if the tray/dashboard process is already running."""
    return acquire_instance_lock("Local\\PrayerLockTrayInstance")


def acquire_lockscreen_instance_lock() -> bool:
    """Return False if a lockscreen is already covering this desktop session."""
    return acquire_instance_lock("Local\\PrayerLockLockscreenInstance")


def launch_setup_or_tray(config):
    """Show setup wizard on first run, otherwise go straight to tray."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("PrayerLock")
    try:
        from tray_app import create_app_icon
        app.setWindowIcon(create_app_icon())
    except Exception:
        pass

    cfg = config.load()

    if cfg.get("first_run", True):
        from setup_wizard import SetupWizard
        wizard = SetupWizard(config)
        wizard.show()
    else:
        cleanup_legacy_user_startup()
        if not acquire_tray_instance_lock():
            sys.exit(0)
        from tray_app import TrayApplication
        tray = TrayApplication(config)
        # Keep reference alive on app object so GC doesn't collect it
        app._tray = tray  # noqa: SLF001

    sys.exit(app.exec())


def launch_tray(config):
    """Launch only the tray app (used at Windows startup)."""
    from PyQt6.QtWidgets import QApplication

    cleanup_legacy_user_startup()
    if not acquire_tray_instance_lock():
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("PrayerLock")
    try:
        from tray_app import create_app_icon
        app.setWindowIcon(create_app_icon())
    except Exception:
        pass

    from tray_app import TrayApplication
    tray = TrayApplication(config)
    app._tray = tray  # noqa: SLF001

    sys.exit(app.exec())


def launch_lockscreen(prayer_name: str, duration_seconds: int, config):
    """Launch the fullscreen lock screen."""
    from PyQt6.QtWidgets import QApplication

    if not acquire_lockscreen_instance_lock():
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    try:
        from tray_app import create_app_icon
        app.setWindowIcon(create_app_icon())
    except Exception:
        pass

    from lockscreen import LockScreenWindow
    window = LockScreenWindow(
        prayer_name=prayer_name,
        duration=duration_seconds,   # ← parameter is `duration`, not `duration_seconds`
    )
    app._lockscreen_window = window  # keep the top-level widget alive

    sys.exit(app.exec())


def launch_warning_overlay(
    prayer_name: str,
    athan_seconds: int,
    lock_seconds: int,
    suppress_seconds: int,
    respect_dismissal: bool,
    parent_pid: int,
    config,
):
    """Launch the small pre-Athan countdown overlay."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    try:
        from tray_app import create_app_icon
        app.setWindowIcon(create_app_icon())
    except Exception:
        pass

    from warning_overlay import WarningOverlayWindow
    window = WarningOverlayWindow(
        prayer_name=prayer_name,
        athan_seconds=athan_seconds,
        lock_seconds=lock_seconds,
        suppress_seconds=suppress_seconds,
        respect_dismissal=respect_dismissal,
        parent_pid=parent_pid,
    )
    app._warning_overlay_window = window  # keep the top-level widget alive
    window.show()

    sys.exit(app.exec())


def handle_service_command(command: str):
    """Install, uninstall, or start the Windows service."""
    if os.name == "nt" and not is_admin():
        if relaunch_as_admin():
            print("Requested Administrator permission; continuing in elevated window.")
            return
        print("Administrator permission is required for service commands.")
        sys.exit(1)

    try:
        import winerror
        import win32service
        import win32serviceutil
        from prayer_service import PrayerLockService   # flat import

        if command == "install":
            service_class = (
                f"{PrayerLockService.__module__}."
                f"{PrayerLockService.__name__}"
            )
            try:
                win32serviceutil.InstallService(
                    service_class,
                    PrayerLockService._svc_name_,
                    PrayerLockService._svc_display_name_,
                    startType=win32service.SERVICE_AUTO_START,
                    description=PrayerLockService._svc_description_,
                )
                print("Service installed successfully.")
            except win32service.error as exc:
                if exc.winerror != winerror.ERROR_SERVICE_EXISTS:
                    raise
                win32serviceutil.ChangeServiceConfig(
                    service_class,
                    PrayerLockService._svc_name_,
                    displayName=PrayerLockService._svc_display_name_,
                    startType=win32service.SERVICE_AUTO_START,
                    description=PrayerLockService._svc_description_,
                )
                print("Service already existed; configuration updated.")

        elif command == "uninstall":
            win32serviceutil.RemoveService(PrayerLockService._svc_name_)
            print("Service removed.")

        elif command == "start":
            win32serviceutil.StartService(PrayerLockService._svc_name_)
            print("Service started.")

        elif command == "stop":
            win32serviceutil.StopService(PrayerLockService._svc_name_)
            print("Service stopped.")

    except Exception as e:
        print(f"Service command '{command}' failed: {e}")
        if getattr(e, "winerror", None) == 5:
            print("Run this command from an elevated Administrator terminal.")
        sys.exit(1)


def main():
    args = parse_args()

    # Set up logging first (non-critical — don't abort if it fails)
    try:
        from logger import setup_logging   # flat import
        setup_logging("main")
    except Exception:
        pass

    # Load config (may not exist yet on first run — that's fine)
    try:
        from config_manager import ConfigManager   # flat import
        config = ConfigManager()
    except Exception as e:
        print(f"Failed to initialise ConfigManager: {e}")
        config = None

    if args.verify_password_file:
        if config is None:
            sys.exit(1)
        try:
            with open(args.verify_password_file, "r", encoding="utf-8") as f:
                password = f.read()
            sys.exit(0 if config.verify_password(password) else 1)
        except Exception:
            sys.exit(1)

    # ── Route to the correct mode ─────────────────────────────────────────────

    if args.install_service:
        handle_service_command("install")

    elif args.uninstall_service:
        handle_service_command("uninstall")

    elif args.start_service:
        handle_service_command("start")

    elif args.stop_service:
        handle_service_command("stop")

    elif args.lockscreen:
        if config is None:
            print("Cannot show lock screen: config not found.")
            sys.exit(1)
        launch_lockscreen(args.prayer, args.duration, config)

    elif args.warning_overlay:
        if config is None:
            print("Cannot show warning overlay: config not found.")
            sys.exit(1)
        launch_warning_overlay(
            args.prayer,
            args.athan_seconds,
            args.lock_seconds,
            args.suppress_seconds,
            not args.ignore_dismissal,
            args.parent_pid,
            config,
        )

    elif args.tray:
        if config is None:
            print("Cannot launch tray: config not found.")
            sys.exit(1)
        launch_tray(config)

    else:
        # Default: setup wizard on first run, tray app otherwise
        if config is None:
            from config_manager import ConfigManager
            config = ConfigManager()
        launch_setup_or_tray(config)


if __name__ == "__main__":
    main()
