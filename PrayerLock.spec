# PrayerLock PyInstaller Spec
# All source files are in one flat directory — no subpackages.
# Build with: pyinstaller PrayerLock.spec

import os
import sys
from PyInstaller.utils.hooks import collect_all, copy_metadata

block_cipher = None

datas = []
binaries = []
hiddenimports = []

icon_path = os.path.abspath(os.path.join('assets', 'app_icon.ico'))
assets_dir = os.path.abspath('assets')
if os.path.exists(assets_dir):
    datas.append((assets_dir, 'assets'))

# Collect data files and binaries for packages that need them.
# collect_all() takes the IMPORTABLE name, not the pip package name:
#   argon2-cffi (pip)  →  argon2  (import)
for pkg in ['adhan', 'pytz', 'cryptography', 'argon2', 'psutil', 'cffi', 'requests']:
    try:
        pkg_datas, pkg_binaries, pkg_imports = collect_all(pkg)
        datas    += pkg_datas
        binaries += pkg_binaries
        hiddenimports += pkg_imports
    except Exception:
        pass  # skip silently if not installed

# Copy dist-info metadata for packages that introspect their own version at runtime.
# argon2-cffi reads its own metadata, so this prevents PackageNotFoundError inside
# the frozen .exe when PasswordHasher is first instantiated.
for pkg in ['argon2-cffi', 'argon2-cffi-bindings', 'cryptography', 'psutil', 'cffi', 'requests']:
    try:
        datas += copy_metadata(pkg)
    except Exception:
        pass

hiddenimports += [
    # ── argon2-cffi (password hashing) ───────────────────────────────────────
    # Public API layer
    'argon2',
    'argon2._utils',
    'argon2._password_hasher',
    'argon2.low_level',
    'argon2.exceptions',
    'argon2.profiles',
    # argon2-cffi-bindings (the compiled C extension)
    # NOTE: 'argon2._cffi_bindings' does NOT exist in argon2-cffi >= 21.x.
    # The correct compiled module is accessed through 'argon2.low_level' which
    # uses '_cffi_backend' from cffi. Do NOT add 'argon2._cffi_bindings' here.
    '_cffi_backend',          # CFFI C extension
    'cffi',
    'cffi.backend_ctypes',

    # ── win32 / pywin32 ──────────────────────────────────────────────────────
    'win32serviceutil',
    'win32service',
    'win32event',
    'win32api',
    'win32con',
    'win32gui',
    'win32process',
    'win32profile',
    'win32security',
    'win32ts',
    'ntsecuritycon',
    'servicemanager',
    'pywintypes',

    # ── PyQt6 ─────────────────────────────────────────────────────────────────
    'PyQt6.QtCore',
    'PyQt6.QtWidgets',
    'PyQt6.QtGui',
    'PyQt6.sip',

    # ── Networking / timezone ─────────────────────────────────────────────────
    'requests',
    'urllib3',
    'pytz',

    # ── App modules (flat — all in the same directory as main.py) ─────────────
    'config_manager',
    'prayer_scheduler',
    'lockscreen',
    'lock_state',
    'warning_overlay',
    'setup_wizard',
    'tray_app',
    'anti_bypass',
    'logger',
    'prayer_service',
    # prayer_service / watchdog are optional (Windows service only)
    # add them here if you have those files:
    # 'prayer_service',
    # 'watchdog',
]

a = Analysis(
    ['main.py'],
    pathex=[os.path.dirname(os.path.abspath('main.py'))],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PrayerLock',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # No console window in production
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=False,          # Normal tray/setup launches should not prompt for UAC
    icon=icon_path if os.path.exists(icon_path) else None,
    version_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PrayerLock',
)
