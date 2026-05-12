"""
PrayerLock Uninstaller
"""
import os
import sys
import ctypes
import subprocess
import shutil
import getpass
from pathlib import Path

# Flat structure — ensure the app directory is on the import path.
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit(0)


def main():
    print("=" * 60)
    print("  PrayerLock Uninstaller")
    print("=" * 60)

    if not is_admin():
        print("Administrator privileges required. Relaunching...")
        run_as_admin()
        return

    confirm = input("\nAre you sure you want to uninstall PrayerLock? (yes/no): ")
    if confirm.lower() != "yes":
        print("Cancelled.")
        return

    # Verify with password
    print("\nFor security, please enter the master password:")
    pwd = getpass.getpass("Password: ")

    try:
        from config_manager import ConfigManager   # flat import — fixed from config.manager
        cfg = ConfigManager()
        if not cfg.verify_password(pwd):
            print("ERROR: Incorrect password. Uninstall aborted.")
            sys.exit(1)
    except Exception as e:
        print(f"Could not verify password: {e}")
        print("Uninstall aborted.")
        sys.exit(1)

    print("\nUninstalling...")

    # Stop and remove service
    print("Stopping service...")
    subprocess.run(["sc", "stop", "PrayerLockService"], capture_output=True)
    subprocess.run(["sc", "delete", "PrayerLockService"], capture_output=True)

    # Remove from startup
    try:
        import winreg
        for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            try:
                key = winreg.OpenKey(
                    hive,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                    0, winreg.KEY_SET_VALUE
                )
                try:
                    winreg.DeleteValue(key, "PrayerLock")
                    winreg.DeleteValue(key, "PrayerLockWatchdog")
                except FileNotFoundError:
                    pass
                winreg.CloseKey(key)
            except Exception:
                pass
    except Exception:
        pass

    # Remove data directory
    data_dir = Path("C:/ProgramData/PrayerLock")
    if data_dir.exists():
        keep = input(f"\nDelete config & data at {data_dir}? (yes/no): ")
        if keep.lower() == "yes":
            shutil.rmtree(data_dir, ignore_errors=True)
            print("Data directory removed.")

    # Remove install directory
    install_dir = Path("C:/Program Files/PrayerLock")
    if install_dir.exists():
        try:
            shutil.rmtree(install_dir, ignore_errors=True)
            print(f"Removed {install_dir}")
        except Exception as e:
            print(f"Could not remove install dir: {e}")

    # Remove desktop shortcut
    try:
        shortcut = Path.home() / "Desktop" / "PrayerLock.lnk"
        if shortcut.exists():
            shortcut.unlink()
    except Exception:
        pass

    print("\n" + "=" * 60)
    print("  PrayerLock has been uninstalled.")
    print("=" * 60)
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
