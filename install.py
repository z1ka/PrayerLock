"""
PrayerLock Installer Script
Run as Administrator to install the Windows service and configure startup.
"""
import os
import sys
import ctypes
import subprocess
import shutil
from pathlib import Path

# Flat structure — add our own directory to sys.path
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit(0)


def find_exe() -> Path:
    """Find the PrayerLock executable."""
    candidates = [
        Path("dist/PrayerLock/PrayerLock.exe"),
        Path("PrayerLock.exe"),
        Path(sys.executable),
    ]
    for c in candidates:
        if c.exists():
            return c.resolve()
    raise FileNotFoundError(
        "PrayerLock.exe not found. Build it first with:\n"
        "  pyinstaller PrayerLock.spec"
    )


def install_to_program_files(exe_path: Path) -> Path:
    """Copy application to Program Files."""
    dest = Path("C:/Program Files/PrayerLock")
    dest.mkdir(parents=True, exist_ok=True)
    src_dir = exe_path.parent
    print(f"Copying {src_dir} → {dest}")
    if dest != src_dir:
        shutil.rmtree(dest, ignore_errors=True)
        shutil.copytree(str(src_dir), str(dest), dirs_exist_ok=True)
    return dest / exe_path.name


def create_data_dir():
    data_dir = Path("C:/ProgramData/PrayerLock")
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "logs").mkdir(exist_ok=True)
    print(f"Created data directory: {data_dir}")


def install_service(exe_path: Path):
    print("Installing Windows service...")
    result = subprocess.run(
        [str(exe_path), "--install-service"],
        capture_output=True, text=True
    )
    print(result.stdout or "Service install command sent.")
    if result.stderr:
        print(f"stderr: {result.stderr}")


def start_service():
    print("Starting service...")
    result = subprocess.run(
        ["sc", "start", "PrayerLockService"],
        capture_output=True, text=True
    )
    print(result.stdout or "Service start command sent.")


def add_to_startup(exe_path: Path):
    try:
        import winreg
        cmd = f'"{exe_path}" --tray'
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "PrayerLock", 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        print("Added PrayerLock to startup.")
    except Exception as e:
        print(f"Startup registration failed: {e}")


def create_desktop_shortcut(exe_path: Path):
    try:
        desktop = Path.home() / "Desktop"
        shortcut_path = desktop / "PrayerLock.lnk"
        ps_script = (
            f'$s=(New-Object -ComObject WScript.Shell).CreateShortcut("{shortcut_path}");'
            f'$s.TargetPath="{exe_path}";'
            f'$s.Description="PrayerLock - Prayer Time Enforcement";'
            f'$s.Save()'
        )
        subprocess.run(["powershell", "-Command", ps_script], capture_output=True)
        print("Created desktop shortcut.")
    except Exception as e:
        print(f"Desktop shortcut failed: {e}")


def main():
    print("=" * 60)
    print("  PrayerLock Installer")
    print("=" * 60)

    if not is_admin():
        print("Administrator privileges required. Relaunching...")
        run_as_admin()
        return

    try:
        exe_path = find_exe()
        print(f"Found executable: {exe_path}")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print("\nInstalling PrayerLock...")
    create_data_dir()
    installed_exe = install_to_program_files(exe_path)
    install_service(installed_exe)
    start_service()
    add_to_startup(installed_exe)
    create_desktop_shortcut(installed_exe)

    print("\n" + "=" * 60)
    print("  Installation Complete!")
    print("=" * 60)
    print(f"\n  Executable : {installed_exe}")
    print("  Service    : PrayerLockService (auto-start)")
    print("  Data       : C:\\ProgramData\\PrayerLock\\")
    print("\n  جزاك الله خيرًا")
    print("=" * 60)
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
