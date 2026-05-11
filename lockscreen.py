"""
PrayerLock Lockscreen
Beautiful Islamic-inspired fullscreen lock window with anti-bypass protection.
"""
import sys
import os
import math
import random
import datetime
import threading

from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QGraphicsOpacityEffect,
    QSizePolicy, QMessageBox
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    pyqtSignal, QThread, QSize, QPoint, QRect,
    QSequentialAnimationGroup, QPauseAnimation
)
from PyQt6.QtGui import (
    QPainter, QPainterPath, QColor, QLinearGradient,
    QFont, QFontMetrics, QPen, QBrush, QKeySequence,
    QIcon, QPixmap, QPalette, QRadialGradient, QConicalGradient
)

# Flat structure — ROOT is the directory this file lives in
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ─── QURAN VERSES & MESSAGES ────────────────────────────────────────────────

VERSES = [
    {
        "arabic": "\u0625\u0650\u0646\u0651\u064e \u0627\u0644\u0635\u0651\u064e\u0644\u064e\u0627\u0629\u064e \u0643\u064e\u0627\u0646\u064e\u062a\u0652 \u0639\u064e\u0644\u064e\u0649 \u0627\u0644\u0652\u0645\u064f\u0624\u0652\u0645\u0650\u0646\u0650\u064a\u0646\u064e \u0643\u0650\u062a\u064e\u0627\u0628\u064b\u0627 \u0645\u064e\u0648\u0652\u0642\u064f\u0648\u062a\u064b\u0627",
        "ref": "\u0633\u0648\u0631\u0629 \u0627\u0644\u0646\u0633\u0627\u0621 \u0664:\u0661\u0660\u0663"
    },
    {
        "arabic": "\u0648\u064e\u0623\u064e\u0642\u0650\u064a\u0645\u064f\u0648\u0627 \u0627\u0644\u0635\u0651\u064e\u0644\u064e\u0627\u0629\u064e \u0648\u064e\u0622\u062a\u064f\u0648\u0627 \u0627\u0644\u0632\u0651\u064e\u0643\u064e\u0627\u0629\u064e \u0648\u064e\u0627\u0631\u0652\u0643\u064e\u0639\u064f\u0648\u0627 \u0645\u064e\u0639\u064e \u0627\u0644\u0631\u0651\u064e\u0627\u0643\u0650\u0639\u0650\u064a\u0646\u064e",
        "ref": "\u0633\u0648\u0631\u0629 \u0627\u0644\u0628\u0642\u0631\u0629 \u0662:\u0664\u0663"
    },
    {
        "arabic": "\u062d\u064e\u0627\u0641\u0650\u0638\u064f\u0648\u0627 \u0639\u064e\u0644\u064e\u0649 \u0627\u0644\u0635\u0651\u064e\u0644\u064e\u0648\u064e\u0627\u062a\u0650 \u0648\u064e\u0627\u0644\u0635\u0651\u064e\u0644\u064e\u0627\u0629\u0650 \u0627\u0644\u0652\u0648\u064f\u0633\u0652\u0637\u064e\u0649\u0670",
        "ref": "\u0633\u0648\u0631\u0629 \u0627\u0644\u0628\u0642\u0631\u0629 \u0662:\u0662\u0663\u0668"
    },
    {
        "arabic": "\u0648\u064e\u0627\u0633\u0652\u062a\u064e\u0639\u0650\u064a\u0646\u064f\u0648\u0627 \u0628\u0650\u0627\u0644\u0635\u0651\u064e\u0628\u0652\u0631\u0650 \u0648\u064e\u0627\u0644\u0635\u0651\u064e\u0644\u064e\u0627\u0629\u0650 \u06da \u0648\u064e\u0625\u0650\u0646\u0651\u064e\u0647\u064e\u0627 \u0644\u064e\u0643\u064e\u0628\u0650\u064a\u0631\u064e\u0629\u064c \u0625\u0650\u0644\u0651\u064e\u0627 \u0639\u064e\u0644\u064e\u0649 \u0627\u0644\u0652\u062e\u064e\u0627\u0634\u0650\u0639\u0650\u064a\u0646\u064e",
        "ref": "\u0633\u0648\u0631\u0629 \u0627\u0644\u0628\u0642\u0631\u0629 \u0662:\u0664\u0665"
    },
    {
        "arabic": "\u0627\u0644\u0651\u064e\u0630\u0650\u064a\u0646\u064e \u0647\u064f\u0645\u0652 \u0639\u064e\u0644\u064e\u0649\u0670 \u0635\u064e\u0644\u064e\u0627\u062a\u0650\u0647\u0650\u0645\u0652 \u062f\u064e\u0627\u0626\u0650\u0645\u064f\u0648\u0646\u064e",
        "ref": "\u0633\u0648\u0631\u0629 \u0627\u0644\u0645\u0639\u0627\u0631\u062c \u0667\u0660:\u0662\u0663"
    },
]

PRAYER_ARABIC_NAMES = {
    "fajr": "\u0627\u0644\u0641\u062c\u0631",
    "dhuhr": "\u0627\u0644\u0638\u0647\u0631",
    "asr": "\u0627\u0644\u0639\u0635\u0631",
    "maghrib": "\u0627\u0644\u0645\u063a\u0631\u0628",
    "isha": "\u0627\u0644\u0639\u0634\u0627\u0621",
}

PRAYER_ICONS = {
    "fajr":    "🌙",
    "dhuhr":   "☀️",
    "asr":     "🌤️",
    "maghrib": "🌅",
    "isha":    "✨",
}

# Verse rotation interval in milliseconds (60 seconds)
VERSE_ROTATION_MS = 60_000


# ─── ANIMATED BACKGROUND CANVAS ──────────────────────────────────────────────

class IslamicPatternWidget(QWidget):
    """Animated geometric Islamic pattern background."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tick = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(50)  # 20 fps for background
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def _animate(self):
        self._tick += 1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        if w == 0 or h == 0:
            return

        # Deep dark background gradient
        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0.0, QColor(8, 12, 22))
        grad.setColorAt(0.4, QColor(12, 18, 35))
        grad.setColorAt(1.0, QColor(6, 10, 20))
        painter.fillRect(self.rect(), grad)

        # Radial glow center
        cx, cy = w // 2, h // 2
        glow = QRadialGradient(cx, cy, max(w, h) * 0.6)
        glow.setColorAt(0.0, QColor(120, 80, 20, 30))
        glow.setColorAt(0.5, QColor(60, 40, 10, 15))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(self.rect(), glow)

        # Draw star-polygon Islamic pattern
        painter.setOpacity(0.06)
        self._draw_tiling(painter, w, h)

        # Floating particles
        painter.setOpacity(0.5)
        self._draw_particles(painter, w, h)

        # Top and bottom vignette
        painter.setOpacity(1.0)
        top_grad = QLinearGradient(0, 0, 0, h * 0.35)
        top_grad.setColorAt(0, QColor(0, 0, 0, 180))
        top_grad.setColorAt(1, QColor(0, 0, 0, 0))
        painter.fillRect(self.rect(), top_grad)

        bot_grad = QLinearGradient(0, h * 0.65, 0, h)
        bot_grad.setColorAt(0, QColor(0, 0, 0, 0))
        bot_grad.setColorAt(1, QColor(0, 0, 0, 200))
        painter.fillRect(self.rect(), bot_grad)

    def _draw_tiling(self, painter, w, h):
        """Draw a repeating 8-pointed star Islamic tile pattern."""
        pen = QPen(QColor(200, 160, 60), 1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        cell = 120
        for row in range(-1, h // cell + 2):
            for col in range(-1, w // cell + 2):
                cx = col * cell + (cell // 2 if row % 2 else 0)
                cy = row * cell
                self._draw_star8(painter, cx, cy, cell * 0.38)

    def _draw_star8(self, painter, cx, cy, r):
        """Draw an 8-pointed star."""
        path = QPainterPath()
        inner_r = r * 0.42
        n = 8
        first = True
        for i in range(n * 2):
            angle = math.pi / n * i - math.pi / 2
            radius = r if i % 2 == 0 else inner_r
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            if first:
                path.moveTo(x, y)
                first = False
            else:
                path.lineTo(x, y)
        path.closeSubpath()
        painter.drawPath(path)

    def _draw_particles(self, painter, w, h):
        """Draw slowly drifting star particles."""
        random.seed(42)  # fixed seed for consistent positions
        t = self._tick * 0.3

        for i in range(40):
            base_x = random.uniform(0, w)
            base_y = random.uniform(0, h)
            speed = random.uniform(0.2, 0.8)
            size = random.uniform(1, 3)
            phase = random.uniform(0, 6.28)

            x = (base_x + math.sin(t * speed + phase) * 15) % w
            y = (base_y - t * speed * 0.5) % h
            brightness = int(160 + 80 * math.sin(t * speed * 2 + phase))
            alpha = int(100 + 100 * math.sin(t * speed + phase))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(brightness, brightness, int(brightness * 0.7), alpha))
            painter.drawEllipse(int(x - size), int(y - size),
                                int(size * 2), int(size * 2))


# ─── COUNTDOWN RING WIDGET ────────────────────────────────────────────────────

class CountdownRing(QWidget):
    """Circular countdown progress ring."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._total = 1
        self._remaining = 1
        self._tick = 0
        self.setFixedSize(190, 190)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._pulse)
        self._pulse_timer.start(50)

    def _pulse(self):
        self._tick += 1
        self.update()

    def set_values(self, total: int, remaining: int):
        self._total = max(1, total)
        self._remaining = max(0, remaining)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        margin = 14
        rect = QRect(margin, margin, w - 2 * margin, h - 2 * margin)

        # Background ring
        pen = QPen(QColor(255, 255, 255, 20), 8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(rect, 0, 360 * 16)

        # Progress arc
        progress = self._remaining / self._total
        span = int(progress * 360 * 16)

        pulse = math.sin(self._tick * 0.15) * 0.15 + 0.85
        gold_r = int(min(255, 212 * pulse))
        gold_g = int(min(255, 160 * pulse))
        gold_b = int(min(255, 40 * pulse))

        pen2 = QPen(QColor(gold_r, gold_g, gold_b, 220), 8)
        pen2.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen2)
        # Draw arc clockwise from top (90°); span is negative for clockwise in Qt
        painter.drawArc(rect, 90 * 16, -span)

        # Inner glow
        glow = QRadialGradient(w // 2, h // 2, (w - 2 * margin) // 2)
        glow.setColorAt(0.6, QColor(212, 160, 40, 0))
        glow.setColorAt(0.85, QColor(212, 160, 40, int(30 * pulse)))
        glow.setColorAt(1.0, QColor(212, 160, 40, 0))
        painter.setBrush(glow)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(rect)

        # Center time text
        mins = self._remaining // 60
        secs = self._remaining % 60
        time_str = f"{mins:02d}:{secs:02d}"

        painter.setPen(QColor(255, 255, 255, 220))
        font = QFont("Georgia", 24, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, time_str)

        label_rect = QRect(margin, h // 2 + 20, w - 2 * margin, 24)
        painter.setPen(QColor(200, 160, 60, 160))
        font2 = QFont("Georgia", 9)
        painter.setFont(font2)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, "REMAINING")


# ─── PASSWORD DIALOG ─────────────────────────────────────────────────────────

class PasswordOverlay(QWidget):
    """Stylized password entry panel."""

    password_entered = pyqtSignal(str)
    cancelled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Card container
        self.card = QFrame()
        self.card.setFixedWidth(380)
        self.card.setObjectName("passwordCard")
        self.card.setStyleSheet("""
            #passwordCard {
                background: rgba(12, 18, 35, 0.97);
                border: 1px solid rgba(212, 160, 40, 0.4);
                border-radius: 20px;
            }
        """)

        card_layout = QVBoxLayout(self.card)
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(36, 36, 36, 36)

        # Lock icon
        icon_lbl = QLabel("🔐")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 40px; background: transparent;")

        # Title
        title = QLabel("\u0623\u062f\u062e\u0644 \u0643\u0644\u0645\u0629 \u0627\u0644\u0645\u0631\u0648\u0631")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            color: #D4A028;
            font-family: 'Traditional Arabic', 'Segoe UI', serif;
            font-size: 24px;
            font-weight: bold;
            background: transparent;
        """)

        # Subtitle
        subtitle = QLabel(
            "\u064a\u0645\u0643\u0646 \u0625\u063a\u0644\u0627\u0642 \u0647\u0630\u0647 \u0627\u0644\u0634\u0627\u0634\u0629\n"
            "\u0628\u0643\u0644\u0645\u0629 \u0627\u0644\u0645\u0631\u0648\u0631 \u0623\u0648 \u0639\u0646\u062f \u0627\u0646\u062a\u0647\u0627\u0621 \u0627\u0644\u0648\u0642\u062a."
        )
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("""
            color: rgba(200, 190, 170, 0.7);
            font-size: 12px;
            background: transparent;
        """)

        # Password field
        self.password_field = QLineEdit()
        self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_field.setPlaceholderText("••••••••••••")
        self.password_field.setFixedHeight(48)
        self.password_field.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(212, 160, 40, 0.3);
                border-radius: 12px;
                color: white;
                font-size: 18px;
                padding: 8px 16px;
            }
            QLineEdit:focus {
                border: 1px solid rgba(212, 160, 40, 0.8);
                background: rgba(255, 255, 255, 0.09);
            }
        """)
        self.password_field.returnPressed.connect(self._submit)

        # Error label
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setStyleSheet(
            "color: #FF6B6B; font-size: 12px; background: transparent;"
        )
        self.error_label.hide()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.cancel_btn = QPushButton("\u0625\u0644\u063a\u0627\u0621")
        self.cancel_btn.setFixedHeight(44)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 10px;
                color: rgba(255, 255, 255, 0.6);
                font-size: 14px;
            }
            QPushButton:hover { background: rgba(255, 255, 255, 0.10); }
        """)
        self.cancel_btn.clicked.connect(self.cancelled.emit)

        self.submit_btn = QPushButton("\u0641\u062a\u062d")
        self.submit_btn.setFixedHeight(44)
        self.submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #B8860B, stop:1 #D4A028);
                border: none;
                border-radius: 10px;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #D4A028, stop:1 #F0BC38);
            }
            QPushButton:pressed { background: #A07820; }
        """)
        self.submit_btn.clicked.connect(self._submit)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.submit_btn)

        card_layout.addWidget(icon_lbl)
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(4)
        card_layout.addWidget(self.password_field)
        card_layout.addWidget(self.error_label)
        card_layout.addLayout(btn_layout)

        layout.addWidget(self.card, alignment=Qt.AlignmentFlag.AlignCenter)

    def _submit(self):
        pwd = self.password_field.text()
        if pwd:
            self.password_entered.emit(pwd)
        else:
            self.show_error("\u0627\u0644\u0631\u062c\u0627\u0621 \u0625\u062f\u062e\u0627\u0644 \u0643\u0644\u0645\u0629 \u0627\u0644\u0645\u0631\u0648\u0631.")

    def show_error(self, msg: str):
        self.error_label.setText(msg)
        self.error_label.show()
        self.password_field.clear()
        self.password_field.setFocus()

    def showEvent(self, event):
        super().showEvent(event)
        self.password_field.clear()
        self.error_label.hide()
        self.password_field.setFocus()


# ─── MAIN LOCKSCREEN WINDOW ───────────────────────────────────────────────────

class LockScreenWindow(QWidget):
    """
    Main fullscreen lockscreen.
    Covers all monitors, blocks interaction, prevents Alt+F4/task-switch.
    """

    def __init__(self, prayer_name: str = "Prayer", duration: int = 900):
        """
        :param prayer_name: Display name of the prayer (e.g. "Dhuhr").
        :param duration:    Lock duration in seconds.
        """
        super().__init__()
        self.prayer_name = prayer_name
        self.prayer_name_lower = prayer_name.lower()
        self.prayer_name_arabic = PRAYER_ARABIC_NAMES.get(
            self.prayer_name_lower,
            "\u0627\u0644\u0635\u0644\u0627\u0629",
        )
        self.total_duration = duration
        self.remaining = duration
        self._password_shown = False
        self._unlocked = False
        self._current_verse_idx = random.randrange(len(VERSES))
        self._tick = 0

        self._setup_window()
        self._setup_ui()

        # Show fullscreen AFTER UI is built so background widget paints correctly
        self.showFullScreen()
        self._hide_taskbar()
        self._raise_to_top()

        self._setup_timers()
        self._setup_anti_bypass()

        # Fade-in animation — set up opacity effect BEFORE calling _fade_in
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._fade_anim = None   # keep reference so GC doesn't destroy it
        self._unlock_anim = None
        self._fade_in()

    # ── Window setup ─────────────────────────────────────────────────────────

    def _setup_window(self):
        """Configure window flags and geometry — do NOT show yet."""
        self.setWindowTitle("PrayerLock")
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.CustomizeWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

        # Cover all monitors — set geometry now so child widgets know their size
        app = QApplication.instance()
        if app:
            screens = app.screens()
            if screens:
                total_geo = screens[0].geometry()
                for screen in screens[1:]:
                    total_geo = total_geo.united(screen.geometry())
                self.setGeometry(total_geo)

        # showFullScreen() is called AFTER _setup_ui() in __init__
        # so that child widgets are already built when the window first paints.

    def _hide_taskbar(self):
        """Hide the Windows taskbar."""
        try:
            import win32gui
            import win32con
            taskbar = win32gui.FindWindow("Shell_traywnd", "")
            if taskbar:
                win32gui.ShowWindow(taskbar, win32con.SW_HIDE)
        except Exception:
            pass

    def _restore_taskbar(self):
        """Restore the Windows taskbar."""
        try:
            import win32gui
            import win32con
            taskbar = win32gui.FindWindow("Shell_traywnd", "")
            if taskbar:
                win32gui.ShowWindow(taskbar, win32con.SW_SHOW)
        except Exception:
            pass

    def _raise_to_top(self):
        """Force window to topmost using Windows API."""
        try:
            import win32gui
            import win32con
            hwnd = int(self.winId())
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
            )
        except Exception:
            pass

    def _minimize_all_windows(self):
        """Minimize all other open windows."""
        try:
            import win32gui
            import win32con
            own_hwnd = int(self.winId())
            def enum_callback(hwnd, _):
                if win32gui.IsWindowVisible(hwnd) and hwnd != own_hwnd:
                    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            win32gui.EnumWindows(enum_callback, None)
        except Exception:
            pass

    # ── UI setup ─────────────────────────────────────────────────────────────

    def _setup_ui(self):
        """Build the UI layers."""
        # Layer 1: animated background — sized via resizeEvent
        self._bg = IslamicPatternWidget(self)

        # Layer 2: content overlay
        self._content = QWidget(self)
        self._content.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        content_layout = QVBoxLayout(self._content)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.setSpacing(0)
        content_layout.setContentsMargins(84, 54, 84, 54)

        content_layout.addSpacing(8)

        # ── Prayer icon + name ──
        icon = PRAYER_ICONS.get(self.prayer_name_lower, "🕌")
        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setMinimumHeight(58)
        icon_lbl.setStyleSheet("font-size: 46px; background: transparent;")
        content_layout.addWidget(icon_lbl)
        content_layout.addSpacing(6)

        prayer_lbl = QLabel(f"\u062d\u0627\u0646 \u0648\u0642\u062a \u0635\u0644\u0627\u0629 {self.prayer_name_arabic}")
        prayer_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        prayer_lbl.setMinimumHeight(74)
        prayer_lbl.setStyleSheet("""
            color: white;
            font-family: 'Traditional Arabic', 'Amiri', 'Segoe UI', serif;
            font-size: 52px;
            font-weight: bold;
            background: transparent;
        """)
        content_layout.addWidget(prayer_lbl)

        subtitle_lbl = QLabel("\u0627\u0644\u0644\u0647\u0645 \u0623\u0639\u0646\u0651\u0627 \u0639\u0644\u0649 \u0630\u0643\u0631\u0643 \u0648\u0634\u0643\u0631\u0643 \u0648\u062d\u0633\u0646 \u0639\u0628\u0627\u062f\u062a\u0643")
        subtitle_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_lbl.setMinimumHeight(44)
        subtitle_lbl.setStyleSheet("""
            color: rgba(212, 160, 40, 0.8);
            font-family: 'Traditional Arabic', 'Amiri', 'Segoe UI', serif;
            font-size: 27px;
            background: transparent;
            margin-top: 4px;
        """)
        content_layout.addWidget(subtitle_lbl)
        content_layout.addSpacing(18)

        # ── Countdown ring ──
        ring_row = QHBoxLayout()
        ring_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ring = CountdownRing()
        self._ring.set_values(self.total_duration, self.remaining)
        ring_row.addWidget(self._ring)
        content_layout.addLayout(ring_row)
        content_layout.addSpacing(22)

        # ── Quran verse card ──
        verse_card = QFrame()
        verse_card.setObjectName("verseCard")
        verse_card.setMinimumWidth(0)
        verse_card.setMaximumWidth(1080)
        verse_card.setMinimumHeight(260)
        verse_card.setStyleSheet("""
            #verseCard {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(232, 198, 112, 0.34);
                border-radius: 18px;
            }
            #verseCard QLabel {
                background: transparent;
                border: none;
            }
        """)
        verse_layout = QVBoxLayout(verse_card)
        verse_layout.setContentsMargins(76, 58, 76, 52)
        verse_layout.setSpacing(24)

        verse = VERSES[self._current_verse_idx]

        self._arabic_lbl = QLabel(verse["arabic"])
        self._arabic_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._arabic_lbl.setWordWrap(True)
        self._arabic_lbl.setMinimumHeight(120)
        self._arabic_lbl.setStyleSheet("""
            color: rgba(245, 215, 142, 0.96);
            font-family: 'Traditional Arabic', 'Amiri', 'Segoe UI', serif;
            font-size: 46px;
        """)

        self._ref_lbl = QLabel(verse["ref"])
        self._ref_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ref_lbl.setMinimumHeight(38)
        self._ref_lbl.setStyleSheet("""
            color: rgba(232, 198, 112, 0.62);
            font-family: 'Traditional Arabic', 'Amiri', 'Segoe UI', serif;
            font-size: 26px;
        """)

        verse_layout.addWidget(self._arabic_lbl)
        verse_layout.addWidget(self._ref_lbl)

        card_row = QHBoxLayout()
        card_row.addStretch()
        card_row.addWidget(verse_card)
        card_row.addStretch()
        content_layout.addLayout(card_row)
        content_layout.addSpacing(20)

        # ── Bottom: clock + unlock button ──
        self._clock_lbl = QLabel()
        self._clock_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._clock_lbl.setStyleSheet("""
            color: rgba(255, 255, 255, 0.4);
            font-size: 12px;
            background: transparent;
        """)
        self._update_clock()
        content_layout.addWidget(self._clock_lbl)
        content_layout.addSpacing(12)

        unlock_btn = QPushButton("\u0625\u062f\u062e\u0627\u0644 \u0643\u0644\u0645\u0629 \u0627\u0644\u0645\u0631\u0648\u0631")
        unlock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        unlock_btn.setFixedHeight(56)
        unlock_btn.setMinimumWidth(270)
        unlock_btn.setMaximumWidth(360)
        unlock_btn.setStyleSheet("""
            QPushButton {
                background: rgba(212, 160, 40, 0.12);
                border: 1px solid rgba(212, 160, 40, 0.35);
                border-radius: 20px;
                color: rgba(212, 160, 40, 0.85);
                font-family: 'Segoe UI', 'Traditional Arabic', serif;
                font-size: 18px;
                padding: 10px 28px;
            }
            QPushButton:hover {
                background: rgba(212, 160, 40, 0.22);
                border: 1px solid rgba(212, 160, 40, 0.6);
                color: #D4A028;
            }
        """)
        unlock_btn.clicked.connect(self._show_password_dialog)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(unlock_btn)
        btn_row.addStretch()
        content_layout.addLayout(btn_row)

        # ── Password overlay (hidden until user clicks unlock) ──
        # Created as a direct child of self; geometry is set in resizeEvent.
        self._pwd_overlay = QWidget(self)
        self._pwd_overlay.setStyleSheet("background: rgba(0, 0, 0, 0.75);")
        self._pwd_overlay.hide()

        self._pwd_widget = PasswordOverlay(self._pwd_overlay)
        self._pwd_widget.password_entered.connect(self._check_password)
        self._pwd_widget.cancelled.connect(self._hide_password_dialog)

        # Trigger initial geometry sizing
        self._resize_children()

    def _make_divider(self) -> QWidget:
        """Create a decorative gold divider."""
        w = QWidget()
        w.setFixedHeight(2)
        w.setMaximumWidth(300)
        w.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 transparent,
                stop:0.3 rgba(212,160,40,0.5),
                stop:0.7 rgba(212,160,40,0.5),
                stop:1 transparent);
        """)
        return w

    # ── Timer setup ──────────────────────────────────────────────────────────

    def _setup_timers(self):
        """Setup countdown, clock, topmost-enforcer, and verse-rotation timers."""
        # 1-second countdown tick
        self._countdown_timer = QTimer(self)
        self._countdown_timer.timeout.connect(self._tick_countdown)
        self._countdown_timer.start(1000)

        # Clock update every 10 s
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(10_000)

        # Keep-on-top enforcer every 2 s
        self._topmost_timer = QTimer(self)
        self._topmost_timer.timeout.connect(self._enforce_topmost)
        self._topmost_timer.start(2000)

        # Verse rotation every 60 s
        self._verse_timer = QTimer(self)
        self._verse_timer.timeout.connect(self._rotate_verse)
        self._verse_timer.start(VERSE_ROTATION_MS)

    # ── Anti-bypass setup ─────────────────────────────────────────────────────

    def _setup_anti_bypass(self):
        """Setup anti-bypass protections."""
        # Re-run resize after event loop starts so children get correct fullscreen geometry
        QTimer.singleShot(0, self._resize_children)
        # Minimize all other windows 500 ms after showing (so we're on top first)
        QTimer.singleShot(500, self._minimize_all_windows)

    def _enforce_topmost(self):
        """Periodically re-assert topmost position."""
        if not self._unlocked:
            self.raise_()
            self.activateWindow()
            self._raise_to_top()
            self._ensure_fullscreen()

    def _ensure_fullscreen(self):
        """Make sure we're still fullscreen."""
        if not self.isFullScreen():
            self.showFullScreen()

    # ── Countdown logic ───────────────────────────────────────────────────────

    def _tick_countdown(self):
        """Decrement countdown by 1 second and check for expiry."""
        if self._unlocked:
            return
        self.remaining = max(0, self.remaining - 1)
        self._ring.set_values(self.total_duration, self.remaining)
        if self.remaining <= 0:
            self._unlock(by_timer=True)

    def _update_clock(self):
        now = datetime.datetime.now()
        self._clock_lbl.setText(now.strftime("%A, %B %d  ·  %I:%M %p"))

    # ── Verse rotation ────────────────────────────────────────────────────────

    def _rotate_verse(self):
        """Advance to the next Quran verse."""
        if self._unlocked:
            return
        self._current_verse_idx = (self._current_verse_idx + 1) % len(VERSES)
        verse = VERSES[self._current_verse_idx]
        self._arabic_lbl.setText(verse["arabic"])
        self._ref_lbl.setText(verse["ref"])

    # ── Animations ───────────────────────────────────────────────────────────

    def _fade_in(self):
        """Fade in the window."""
        anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        anim.setDuration(800)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._fade_anim = anim  # prevent GC

    # ── Password dialog ───────────────────────────────────────────────────────

    def _show_password_dialog(self):
        """Show the password overlay."""
        self._pwd_overlay.raise_()
        self._pwd_overlay.show()
        self._pwd_widget.show()
        self._pwd_widget.password_field.setFocus()
        self._password_shown = True

    def _hide_password_dialog(self):
        """Hide the password overlay."""
        self._pwd_overlay.hide()
        self._password_shown = False

    def _check_password(self, password: str):
        """Verify the master password via ConfigManager."""
        try:
            from config_manager import ConfigManager   # flat import
            config = ConfigManager()
            if config.verify_password(password):
                try:
                    from lock_state import mark_intentionally_unlocked
                    mark_intentionally_unlocked(self.prayer_name, self.remaining)
                except Exception:
                    pass
                # Mark as early unlock in streak (streak_count stays, not incremented here)
                try:
                    from anti_bypass import StreakTracker
                    tracker = StreakTracker(config)
                    tracker.record_lock(self.prayer_name, unlocked_early=True)
                except Exception:
                    pass
                self._unlock(by_timer=False)
            else:
                self._pwd_widget.show_error("\u0643\u0644\u0645\u0629 \u0627\u0644\u0645\u0631\u0648\u0631 \u063a\u064a\u0631 \u0635\u062d\u064a\u062d\u0629.")
        except Exception as e:
            self._pwd_widget.show_error(f"\u062e\u0637\u0623: {str(e)[:50]}")

    # ── Unlock ───────────────────────────────────────────────────────────────

    def _unlock(self, by_timer: bool = False):
        """Unlock and close the lockscreen."""
        if self._unlocked:
            return  # guard against double-unlock
        self._unlocked = True
        self._countdown_timer.stop()
        self._topmost_timer.stop()
        self._verse_timer.stop()
        self._restore_taskbar()

        # Remove topmost flag
        try:
            import win32gui
            import win32con
            hwnd = int(self.winId())
            win32gui.SetWindowPos(
                hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
            )
        except Exception:
            pass

        # Fade out then close + quit the Qt event loop
        anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        anim.setDuration(600)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.setEasingCurve(QEasingCurve.Type.InCubic)
        anim.finished.connect(self.close)
        app = QApplication.instance()
        if app:
            anim.finished.connect(app.quit)
        anim.start()
        self._unlock_anim = anim  # prevent GC

    # ── Widget resize ─────────────────────────────────────────────────────────

    def _resize_children(self):
        """Size background and overlay children to fill the window."""
        geo = self.rect()
        if hasattr(self, '_bg'):
            self._bg.setGeometry(geo)
        if hasattr(self, '_content'):
            self._content.setGeometry(geo)
        if hasattr(self, '_pwd_overlay'):
            self._pwd_overlay.setGeometry(geo)
            if hasattr(self, '_pwd_widget'):
                self._pwd_widget.setGeometry(geo)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_children()

    # ── Anti-bypass event overrides ──────────────────────────────────────────

    def keyPressEvent(self, event):
        """Block all key events except when the password dialog is visible."""
        key = event.key()
        mods = event.modifiers()

        blocked = {
            Qt.Key.Key_F4, Qt.Key.Key_Escape,
            Qt.Key.Key_Tab, Qt.Key.Key_Meta,
            Qt.Key.Key_Super_L, Qt.Key.Key_Super_R,
        }

        if key in blocked:
            event.ignore()
            return
        # Alt+F4
        if (mods & Qt.KeyboardModifier.AltModifier) and key == Qt.Key.Key_F4:
            event.ignore()
            return

        if self._password_shown:
            super().keyPressEvent(event)
        else:
            event.ignore()

    def closeEvent(self, event):
        """Prevent closing unless unlocked."""
        if not self._unlocked:
            event.ignore()
        else:
            event.accept()

    def mousePressEvent(self, event):
        """Absorb background clicks."""
        if not self._password_shown:
            event.accept()
        else:
            super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        """Block right-click context menu."""
        event.ignore()

    def changeEvent(self, event):
        """Prevent minimizing."""
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized() and not self._unlocked:
                self.showFullScreen()
        super().changeEvent(event)
