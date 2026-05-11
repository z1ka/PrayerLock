"""
PrayerLock Logging Configuration
"""
import os
import logging
import logging.handlers
from pathlib import Path


def setup_logging(component: str = "main", level: int = logging.INFO) -> logging.Logger:
    """Configure rotating file + console logging for a component."""
    if os.name == "nt":
        log_dir = Path("C:/ProgramData/PrayerLock/logs")
    else:
        log_dir = Path.home() / ".config" / "PrayerLock" / "logs"

    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        # If we can't create the log dir (e.g. no admin rights yet), fall back
        # to a temp directory so logging never crashes the app.
        import tempfile
        log_dir = Path(tempfile.gettempdir()) / "PrayerLock" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"{component}.log"

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Rotating file handler — 5 MB × 3 backups
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
    except OSError:
        file_handler = None

    # Console handler (warnings and above only)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.WARNING)

    root_logger = logging.getLogger()
    # Avoid adding duplicate handlers if setup_logging is called more than once
    if not root_logger.handlers:
        root_logger.setLevel(level)
        if file_handler:
            root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
