"""
PrayerLock Security Module
Anti-bypass, process monitoring, and protection utilities.
"""
import os
import sys
import logging
import threading
import time
import subprocess
from typing import List, Optional

logger = logging.getLogger(__name__)

# Common game processes to terminate
DEFAULT_GAME_PROCESSES = [
    "steam.exe", "steamwebhelper.exe",
    "epicgameslauncher.exe", "fortnite.exe",
    "valorant.exe", "leagueclient.exe",
    "battle.net.exe", "bnetlauncher.exe",
    "origin.exe", "eadesktop.exe",
    "minecraft.exe", "javaw.exe",
    "robloxplayerbeta.exe", "robloxplayer.exe",
    "gta5.exe", "gtav.exe",
    "csgo.exe", "cs2.exe",
    "dota2.exe", "overwatch.exe",
    "pubg.exe", "tslgame.exe",
]


class ProcessMonitor:
    """Monitor and optionally terminate game processes."""

    def __init__(self, config_manager):
        self.config = config_manager

    def get_game_processes(self) -> List[str]:
        cfg = self.config.load()
        custom = cfg.get("game_processes", [])
        return list(set(DEFAULT_GAME_PROCESSES + custom))

    def terminate_games(self):
        """Terminate configured game processes."""
        try:
            import psutil
            targets = {p.lower() for p in self.get_game_processes()}
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'].lower() in targets:
                        proc.terminate()
                        logger.info(
                            f"Terminated game process: {proc.info['name']} "
                            f"(PID {proc.info['pid']})"
                        )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except ImportError:
            logger.warning("psutil not available — cannot monitor processes.")

    def is_game_running(self) -> bool:
        """Return True if any known game process is running."""
        try:
            import psutil
            targets = {p.lower() for p in self.get_game_processes()}
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'].lower() in targets:
                        return True
                except psutil.NoSuchProcess:
                    pass
        except ImportError:
            pass
        return False


class WindowManager:
    """Windows window management utilities."""

    @staticmethod
    def minimize_all():
        """Minimize all windows using Win+D equivalent."""
        try:
            import win32gui
            import win32con
            def callback(hwnd, _):
                try:
                    if win32gui.IsWindowVisible(hwnd):
                        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                except Exception:
                    pass
            win32gui.EnumWindows(callback, None)
        except Exception as e:
            logger.debug(f"minimize_all: {e}")
            try:
                subprocess.run(
                    ["powershell", "-Command",
                     "(New-Object -ComObject Shell.Application).MinimizeAll()"],
                    capture_output=True, timeout=5
                )
            except Exception:
                pass

    @staticmethod
    def hide_taskbar():
        """Hide the Windows taskbar."""
        try:
            import win32gui
            import win32con
            taskbar = win32gui.FindWindow("Shell_traywnd", "")
            if taskbar:
                win32gui.ShowWindow(taskbar, win32con.SW_HIDE)
            start = win32gui.FindWindow("Button", "Start")
            if start:
                win32gui.ShowWindow(start, win32con.SW_HIDE)
        except Exception as e:
            logger.debug(f"hide_taskbar: {e}")

    @staticmethod
    def show_taskbar():
        """Restore the Windows taskbar."""
        try:
            import win32gui
            import win32con
            taskbar = win32gui.FindWindow("Shell_traywnd", "")
            if taskbar:
                win32gui.ShowWindow(taskbar, win32con.SW_SHOW)
            start = win32gui.FindWindow("Button", "Start")
            if start:
                win32gui.ShowWindow(start, win32con.SW_SHOW)
        except Exception as e:
            logger.debug(f"show_taskbar: {e}")

    @staticmethod
    def block_task_manager():
        """Block Task Manager via registry (requires admin)."""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
                0, winreg.KEY_SET_VALUE | winreg.KEY_CREATE_SUB_KEY
            )
            winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            logger.info("Task Manager blocked via registry.")
        except Exception as e:
            logger.debug(f"block_task_manager: {e}")

    @staticmethod
    def unblock_task_manager():
        """Unblock Task Manager."""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
                0, winreg.KEY_SET_VALUE
            )
            winreg.DeleteValue(key, "DisableTaskMgr")
            winreg.CloseKey(key)
            logger.info("Task Manager unblocked.")
        except Exception as e:
            logger.debug(f"unblock_task_manager: {e}")

    @staticmethod
    def set_topmost(hwnd):
        """Set window as topmost using Windows API."""
        try:
            import win32gui
            import win32con
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
            )
        except Exception as e:
            logger.debug(f"set_topmost: {e}")


class LockEnforcer:
    """
    Main lock enforcement coordinator.
    Called by the service when a prayer lock should be active.
    """

    def __init__(self, config_manager):
        self.config = config_manager
        self.monitor = ProcessMonitor(config_manager)
        self._active = False
        self._thread: Optional[threading.Thread] = None

    def activate(self, prayer_name: str, duration_seconds: int):
        """Activate lock enforcement."""
        if self._active:
            return
        self._active = True
        cfg = self.config.load()

        if cfg.get("terminate_games", False):
            self.monitor.terminate_games()

        WindowManager.minimize_all()

        if cfg.get("block_task_manager", False):
            WindowManager.block_task_manager()

        logger.info(f"Lock activated for {prayer_name} ({duration_seconds}s)")

    def deactivate(self):
        """Deactivate lock enforcement."""
        if not self._active:
            return
        self._active = False

        cfg = self.config.load()
        if cfg.get("block_task_manager", False):
            WindowManager.unblock_task_manager()

        WindowManager.show_taskbar()
        logger.info("Lock deactivated.")


class StreakTracker:
    """Tracks prayer lock statistics."""

    def __init__(self, config_manager):
        self.config = config_manager

    def record_lock(self, prayer_name: str, unlocked_early: bool = False):
        """Record a prayer lock event and update streak."""
        import datetime as _dt   # local import to avoid circular issues
        cfg = self.config.load()
        cfg["total_prayers_locked"] = cfg.get("total_prayers_locked", 0) + 1
        if not unlocked_early:
            cfg["streak_count"] = cfg.get("streak_count", 0) + 1
        else:
            # Early unlock breaks the streak
            cfg["streak_count"] = 0

        history = cfg.get("lock_history", [])
        history.append({
            "prayer":       prayer_name,
            "date":         str(_dt.date.today()),
            "early_unlock": unlocked_early,
        })
        # Keep last ~90 days (5 prayers × 90 days = 450; keep 270 as a safe buffer)
        cfg["lock_history"] = history[-270:]
        self.config.save(cfg)

    def get_streak(self) -> int:
        return self.config.get("streak_count", 0)

    def get_history(self) -> list:
        return self.config.get("lock_history", [])
