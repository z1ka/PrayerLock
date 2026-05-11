"""
Small pre-Athan countdown overlay.
"""
import datetime
import os
import sys

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QLabel,
    QVBoxLayout,
)


ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _trace(message: str):
    if os.environ.get("PRAYERLOCK_DEBUG_OVERLAY") != "1":
        return
    try:
        path = os.path.join(os.environ.get("ProgramData", ROOT), "PrayerLock", "overlay_debug.log")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now().isoformat(timespec='seconds')} {message}\n")
    except Exception:
        pass


PRAYER_ARABIC_NAMES = {
    "fajr": "\u0627\u0644\u0641\u062c\u0631",
    "dhuhr": "\u0627\u0644\u0638\u0647\u0631",
    "asr": "\u0627\u0644\u0639\u0635\u0631",
    "maghrib": "\u0627\u0644\u0645\u063a\u0631\u0628",
    "isha": "\u0627\u0644\u0639\u0634\u0627\u0621",
}


class WarningOverlayWindow(QDialog):
    def __init__(
        self,
        prayer_name: str,
        athan_seconds: int,
        lock_seconds: int,
        suppress_seconds: int,
        respect_dismissal: bool = True,
        parent_pid: int = 0,
    ):
        super().__init__()
        _trace(f"init start prayer={prayer_name} athan={athan_seconds} lock={lock_seconds} respect={respect_dismissal}")
        self.prayer_name = prayer_name
        self.prayer_key = prayer_name.lower()
        self.athan_remaining = max(0, athan_seconds)
        self.lock_remaining = max(1, lock_seconds)
        self.suppress_seconds = max(1, suppress_seconds)
        self.respect_dismissal = respect_dismissal
        self.parent_pid = max(0, int(parent_pid or 0))
        self._dismissed = False
        self._setup_window()
        self._setup_ui()
        self._position_bottom_right()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)
        self._update_labels()
        _trace("init done")

    def _setup_window(self):
        _trace("setup window")
        self.setWindowTitle("PrayerLock")
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setFixedSize(340, 142)

    def _setup_ui(self):
        _trace("setup ui")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        self._panel = QFrame(self)
        self._panel.setObjectName("panel")
        self._panel.setFrameShape(QFrame.Shape.NoFrame)
        self._panel.setStyleSheet("""
            #panel {
                background-color: rgba(8, 12, 22, 190);
                border: 1px solid rgba(232, 198, 112, 120);
                border-radius: 8px;
            }
            QLabel {
                background: transparent;
                font-family: 'Segoe UI', 'Traditional Arabic', serif;
            }
        """)
        panel_layout = QVBoxLayout(self._panel)
        panel_layout.setContentsMargins(16, 14, 16, 14)
        panel_layout.setSpacing(8)

        arabic_name = PRAYER_ARABIC_NAMES.get(self.prayer_key, "\u0627\u0644\u0635\u0644\u0627\u0629")
        self._title = QLabel(f"\u0627\u0642\u062a\u0631\u0628 \u0623\u0630\u0627\u0646 {arabic_name}")
        self._title.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._title.setMinimumHeight(34)
        self._title.setStyleSheet(
            "font-family: 'Traditional Arabic', 'Segoe UI', serif; "
            "font-size: 23px; font-weight: 600; color: rgb(245, 215, 142);"
        )
        panel_layout.addWidget(self._title)

        self._athan_label = QLabel()
        self._athan_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._athan_label.setMinimumHeight(24)
        self._athan_label.setStyleSheet(
            "font-family: 'Traditional Arabic', 'Segoe UI', serif; "
            "font-size: 17px; color: rgb(245, 235, 210);"
        )
        panel_layout.addWidget(self._athan_label)

        self._lock_label = QLabel()
        self._lock_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._lock_label.setMinimumHeight(24)
        self._lock_label.setStyleSheet(
            "font-family: 'Traditional Arabic', 'Segoe UI', serif; "
            "font-size: 17px; color: rgb(245, 235, 210);"
        )
        panel_layout.addWidget(self._lock_label)

        layout.addWidget(self._panel)

    def _position_bottom_right(self):
        _trace("position")
        screen = QApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()
        margin = 18
        self.move(
            geo.right() - self.width() - margin,
            geo.bottom() - self.height() - margin,
        )

    def showEvent(self, event):
        super().showEvent(event)
        _trace("showEvent")
        self.raise_()
        QTimer.singleShot(250, self._apply_click_through_styles)

    def _apply_click_through_styles(self):
        if os.name != "nt":
            return
        try:
            import win32con
            import win32gui

            hwnd = int(self.winId())
            ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            ex_style |= (
                win32con.WS_EX_LAYERED
                | win32con.WS_EX_TRANSPARENT
                | win32con.WS_EX_TOOLWINDOW
                | win32con.WS_EX_TOPMOST
                | win32con.WS_EX_NOACTIVATE
            )
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
            win32gui.SetLayeredWindowAttributes(
                hwnd,
                0,
                235,
                win32con.LWA_ALPHA,
            )
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOPMOST,
                0,
                0,
                0,
                0,
                win32con.SWP_NOMOVE
                | win32con.SWP_NOSIZE
                | win32con.SWP_NOACTIVATE
                | win32con.SWP_FRAMECHANGED
                | win32con.SWP_SHOWWINDOW,
            )
        except Exception:
            pass

    def _tick(self):
        _trace(f"tick dismissed={self._dismissed} athan={self.athan_remaining} lock={self.lock_remaining}")
        if self._dismissed:
            return
        if self._parent_process_exited():
            _trace("closing because parent process exited")
            self._dismissed = True
            self.close()
            app = QApplication.instance()
            if app:
                app.quit()
            return
        if self._was_dismissed_from_tray():
            _trace("closing because dismissed state")
            self._dismissed = True
            self.close()
            app = QApplication.instance()
            if app:
                app.quit()
            return
        self.athan_remaining = max(0, self.athan_remaining - 1)
        self.lock_remaining = max(0, self.lock_remaining - 1)
        self._update_labels()
        if self.lock_remaining <= 0:
            _trace("closing because lock countdown ended")
            self._dismissed = True
            self.close()
            app = QApplication.instance()
            if app:
                app.quit()

    def _update_labels(self):
        self._athan_label.setText(
            f"\u0627\u0644\u0623\u0630\u0627\u0646 \u0628\u0639\u062f: {self._format_seconds(self.athan_remaining)}"
        )
        self._lock_label.setText(
            f"\u0627\u0644\u0642\u0641\u0644 \u0628\u0639\u062f: {self._format_seconds(self.lock_remaining)}"
        )

    def closeEvent(self, event):
        _trace(f"closeEvent dismissed={self._dismissed}")
        if self._dismissed:
            event.accept()
        else:
            event.ignore()

    def _was_dismissed_from_tray(self) -> bool:
        if not self.respect_dismissal:
            return False
        try:
            from lock_state import is_intentionally_unlocked
            return is_intentionally_unlocked(self.prayer_name)
        except Exception:
            return False

    def _parent_process_exited(self) -> bool:
        if not self.parent_pid:
            return False
        try:
            import psutil

            if not psutil.pid_exists(self.parent_pid):
                return True
            parent = psutil.Process(self.parent_pid)
            return parent.status() == psutil.STATUS_ZOMBIE
        except Exception:
            return False

    @staticmethod
    def _format_seconds(seconds: int) -> str:
        seconds = max(0, int(seconds))
        mins, secs = divmod(seconds, 60)
        return f"{mins:02d}:{secs:02d}"
