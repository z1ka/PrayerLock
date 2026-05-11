"""
PrayerLock System Tray Application
Background tray icon with prayer schedule display and controls.
"""
import sys
import os
import datetime
import subprocess
import threading
import logging

from PyQt6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QSizePolicy, QScrollArea, QInputDialog, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QIcon, QPixmap, QColor, QFont, QPainter, QPainterPath

# Flat structure — ensure the app directory is on the path
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

logger = logging.getLogger(__name__)

APP_ICON_PATH = os.path.join(ROOT, "assets", "app_icon.ico")


def app_command(*args: str) -> list:
    """Build a command for this app in source and frozen builds."""
    if getattr(sys, "frozen", False):
        return [sys.executable, *args]
    return [sys.executable, os.path.join(ROOT, "main.py"), *args]


def _draw_crescent_icon(size: int = 32) -> QIcon:
    """Create the fallback crescent moon icon."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Draw crescent moon by subtracting one ellipse from another
    outer_path = QPainterPath()
    outer_path.addEllipse(4, 4, 24, 24)
    inner_path = QPainterPath()
    inner_path.addEllipse(10, 2, 20, 20)
    crescent = outer_path.subtracted(inner_path)

    painter.setBrush(QColor(212, 160, 40))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawPath(crescent)
    painter.end()
    return QIcon(pixmap)


def create_app_icon() -> QIcon:
    """Return the packaged app icon, falling back to the drawn tray icon."""
    if os.path.exists(APP_ICON_PATH):
        icon = QIcon(APP_ICON_PATH)
        if not icon.isNull():
            return icon
    return _draw_crescent_icon()


def create_tray_icon() -> QIcon:
    """Return the tray icon."""
    return create_app_icon()


DASHBOARD_STYLE = """
QDialog, QWidget {
    background-color: rgba(8, 12, 18, 232);
    color: #E8E0D0;
    font-family: 'Segoe UI', Arial, sans-serif;
}
QLabel { background: transparent; }
QPushButton {
    background: rgba(212,160,40,0.15);
    border: 1px solid rgba(212,160,40,0.4);
    border-radius: 8px;
    color: #D4A028;
    font-size: 12px;
    padding: 8px 18px;
}
QPushButton:hover { background: rgba(212,160,40,0.25); }
QTableWidget {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    gridline-color: rgba(255,255,255,0.06);
    color: #E8E0D0;
    font-size: 13px;
}
QTableWidget::item:selected { background: rgba(212,160,40,0.2); }
QHeaderView::section {
    background: rgba(212,160,40,0.1);
    border: none;
    color: #D4A028;
    font-size: 11px;
    font-weight: bold;
    padding: 6px;
}
QScrollBar:vertical {
    background: rgba(255,255,255,0.03);
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: rgba(212,160,40,0.3);
    border-radius: 4px;
}
"""


class DashboardWindow(QDialog):
    """Prayer schedule dashboard."""

    def __init__(self, config_manager, scheduler, parent=None, tray_app=None):
        super().__init__(parent)
        self.config = config_manager
        self.scheduler = scheduler
        self.tray_app = tray_app
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        self.setWindowTitle("PrayerLock Dashboard")
        self.setFixedSize(620, 560)
        self.setStyleSheet(DASHBOARD_STYLE)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint
        )

        # Center on screen
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(
                geo.center().x() - self.width() // 2,
                geo.center().y() - self.height() // 2
            )

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # ── Header ──
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("""
            background: rgba(10, 13, 18, 210);
            border-bottom: 1px solid rgba(212,160,40,0.2);
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)

        icon_lbl = QLabel("🕌")
        icon_lbl.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(icon_lbl)
        header_layout.addSpacing(12)

        title_col = QVBoxLayout()
        title = QLabel("PrayerLock")
        title.setStyleSheet(
            "color: #D4A028; font-size: 20px; font-weight: bold; font-family: Georgia, serif;"
        )
        subtitle = QLabel("Prayer Schedule & Settings")
        subtitle.setStyleSheet("color: rgba(200,180,140,0.6); font-size: 11px;")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header_layout.addLayout(title_col)
        header_layout.addStretch()

        self._datetime_lbl = QLabel()
        self._datetime_lbl.setStyleSheet("color: rgba(200,180,140,0.5); font-size: 12px;")
        self._update_datetime()
        header_layout.addWidget(self._datetime_lbl)
        layout.addWidget(header)

        # ── Content ──
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 20, 24, 20)
        content_layout.setSpacing(16)

        cfg = self.config.load()
        city = cfg.get("city", "—")
        self._location_lbl = QLabel(f"📍 {city}")
        self._location_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._location_lbl.setStyleSheet("""
            background: rgba(255,255,255,0.035);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 8px;
            color: rgba(232,224,208,0.82);
            font-size: 12px;
            padding: 10px 14px;
        """)
        content_layout.addWidget(self._location_lbl)

        # Schedule label
        sched_lbl = QLabel("TODAY'S PRAYER TIMES")
        sched_lbl.setStyleSheet(
            "color: #D4A028; font-size: 11px; font-weight: bold;"
        )
        content_layout.addWidget(sched_lbl)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Prayer", "Time", "Lock At", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setFixedHeight(230)
        content_layout.addWidget(self.table)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        for label, slot in [
            ("🔄  Refresh", self._load_data),
            ("🔒  Test Lock", self._test_lockscreen),
            ("⏳  Test Overlay", self._test_warning_overlay),
            ("⚙️  Settings", self._open_settings),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(slot)
            btn_row.addWidget(btn)
        content_layout.addLayout(btn_row)

        # Next event label
        self._next_lbl = QLabel("")
        self._next_lbl.setStyleSheet("""
            background: rgba(212,160,40,0.06);
            border: 1px solid rgba(212,160,40,0.15);
            border-radius: 8px;
            color: rgba(212,160,40,0.8);
            font-size: 12px;
            padding: 10px 14px;
        """)
        content_layout.addWidget(self._next_lbl)
        content_layout.addStretch()

        layout.addWidget(content)

        # Clock refresh timer
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_datetime)
        self._clock_timer.start(10_000)

    def _make_stat_card(self, icon: str, value: str, label: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.032);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 10px;
            }
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(12, 12, 12, 12)
        cl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_lbl = QLabel(f"{icon} {value}")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("color: #D4A028; font-size: 18px; font-weight: bold;")

        lbl = QLabel(label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: rgba(200,180,140,0.5); font-size: 11px;")

        cl.addWidget(icon_lbl)
        cl.addWidget(lbl)
        return card

    def _load_data(self):
        """Load today's prayer schedule into the table."""
        try:
            # Force cache refresh
            self.scheduler._schedule_cache = None
            schedule = self.scheduler.get_formatted_schedule()
            self.table.setRowCount(len(schedule))
            locked = self.scheduler.should_be_locked()
            cfg = self.config.load()
            if hasattr(self, "_location_lbl"):
                self._location_lbl.setText(f"📍 {cfg.get('city', '—')}")

            for row, prayer in enumerate(schedule):
                is_active = locked is not None and locked.name == prayer["name"]
                items = [
                    f"{prayer['display_name']}  {prayer.get('arabic_name', '')}",
                    prayer["time"],
                    prayer["lock_at"],
                    "🔒 Active" if is_active else "—"
                ]
                for col, text in enumerate(items):
                    item = QTableWidgetItem(text)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if col == 3 and is_active:
                        item.setForeground(QColor("#FF6B6B"))
                    self.table.setItem(row, col, item)

            # Next event
            result = self.scheduler.get_next_lock_event()
            if result:
                prayer_entry, event_type = result
                action = "🔒 Lock" if event_type == "lock" else "🔓 Unlock"
                t = prayer_entry.lock_at if event_type == "lock" else prayer_entry.unlock_at
                self._next_lbl.setText(
                    f"Next: {action} for {prayer_entry.display_name} at "
                    f"{t.strftime('%I:%M %p') if t else '—'}"
                )
            else:
                self._next_lbl.setText("No upcoming lock events today.")
        except Exception as e:
            self._next_lbl.setText(f"Error loading schedule: {e}")

    def _update_datetime(self):
        self._datetime_lbl.setText(
            datetime.datetime.now().strftime("%a, %b %d  %I:%M %p")
        )

    def _test_lockscreen(self):
        """Launch a 30-second test lock screen."""
        try:
            subprocess.Popen(
                app_command("--lockscreen", "--prayer", "Dhuhr", "--duration", "30")
            )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not launch test lock screen:\n{e}")

    def _test_warning_overlay(self):
        """Launch a short overlay preview."""
        if self.tray_app is not None:
            self.tray_app._test_warning_overlay()
            return
        try:
            subprocess.Popen(
                app_command(
                    "--warning-overlay",
                    "--prayer",
                    "Dhuhr",
                    "--athan-seconds",
                    "5",
                    "--lock-seconds",
                    "10",
                    "--suppress-seconds",
                    "30",
                    "--ignore-dismissal",
                    "--parent-pid",
                    str(os.getpid()),
                )
            )
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not launch warning overlay:\n{e}")

    def _open_settings(self):
        QMessageBox.information(
            self, "Settings",
            "To change settings, please uninstall and reinstall PrayerLock.\n\n"
            "A settings editing panel is planned for a future update."
        )


class TrayApplication:
    """PrayerLock system tray application."""

    def __init__(self, config_manager):
        self.config = config_manager
        self._dashboard = None
        self._scheduler = None
        self._active_lock_name = None
        self._lockscreen_proc = None
        self._warning_name = None
        self._warning_proc = None
        self._init_scheduler()
        self._init_tray()

    def _init_scheduler(self):
        from prayer_scheduler import PrayerScheduler   # flat import
        self._scheduler = PrayerScheduler(self.config)

    def _init_tray(self):
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(create_tray_icon())
        self.tray.setToolTip("PrayerLock — Prayer enforcement active")
        self.tray.activated.connect(self._on_tray_activated)

        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background: rgba(8, 12, 18, 232);
                border: 1px solid rgba(212,160,40,0.3);
                border-radius: 8px;
                color: white;
                padding: 4px;
            }
            QMenu::item { padding: 8px 20px; border-radius: 4px; }
            QMenu::item:selected { background: rgba(212,160,40,0.2); }
            QMenu::separator { height: 1px; background: rgba(255,255,255,0.1); margin: 4px 8px; }
        """)

        self._status_action = menu.addAction("🕌 PrayerLock Active")
        self._status_action.setEnabled(False)
        menu.addSeparator()

        dashboard_action = menu.addAction("📊 Dashboard")
        dashboard_action.triggered.connect(self._show_dashboard)
        menu.addSeparator()

        self._next_prayer_action = menu.addAction("⏰ Loading...")
        self._next_prayer_action.setEnabled(False)
        test_overlay_action = menu.addAction("Test Warning Overlay")
        test_overlay_action.triggered.connect(self._test_warning_overlay)
        dismiss_action = menu.addAction("Skip Upcoming Overlay/Lock...")
        dismiss_action.triggered.connect(self._dismiss_upcoming_prayer)
        menu.addSeparator()

        quit_action = menu.addAction("🔐 Quit (Password Required)")
        quit_action.triggered.connect(self._request_quit)

        self.tray.setContextMenu(menu)
        self.tray.show()
        app = QApplication.instance()
        if app:
            app.aboutToQuit.connect(self._cleanup_child_processes)

        # Update next prayer every minute
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_next_prayer)
        self._update_timer.start(60_000)
        self._update_next_prayer()

        # If the Windows service is not running, the tray app still runs in the
        # user's desktop session and can enforce the active lock window.
        self._enforce_timer = QTimer()
        self._enforce_timer.timeout.connect(self._enforce_current_lock)
        self._enforce_timer.start(10_000)
        self._enforce_current_lock()

    def _update_next_prayer(self):
        try:
            service_state = self._get_service_state()
            locked = self._scheduler.should_be_locked()
            if locked:
                if service_state == "RUNNING":
                    status = f"Lock active: {locked.display_name}"
                elif service_state == "STOPPED":
                    status = f"Lock active: {locked.display_name} (tray fallback)"
                else:
                    status = (
                        f"Lock active: {locked.display_name} "
                        f"(service {service_state.lower()})"
                    )
            else:
                if service_state == "RUNNING":
                    status = "PrayerLock Active"
                else:
                    status = f"PrayerLock Active (service {service_state.lower()})"
            self._status_action.setText(status)

            result = self._scheduler.get_next_lock_event()
            if result:
                prayer_entry, event_type = result
                t = prayer_entry.lock_at if event_type == "lock" else prayer_entry.unlock_at
                action = "Lock" if event_type == "lock" else "Unlock"
                time_str = t.strftime("%I:%M %p") if t else "—"
                self._next_prayer_action.setText(
                    f"⏰ Next {action}: {prayer_entry.display_name} at {time_str}"
                )
        except Exception:
            pass

    def _get_service_state(self) -> str:
        """Return RUNNING/STOPPED/etc. for the Windows service."""
        if os.name != "nt":
            return "UNAVAILABLE"
        try:
            result = subprocess.run(
                ["sc.exe", "query", "PrayerLockService"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            output = f"{result.stdout}\n{result.stderr}".upper()
            for state in ("RUNNING", "STOPPED", "START_PENDING", "STOP_PENDING"):
                if state in output:
                    return state
            if "DOES NOT EXIST" in output:
                return "MISSING"
        except Exception as e:
            logger.debug(f"Service state check failed: {e}")
        return "UNKNOWN"

    def _enforce_current_lock(self):
        """Launch the lockscreen from the tray when the service is not running."""
        try:
            self._enforce_warning_overlay()

            active = self._scheduler.should_be_locked()
            if active is None:
                self._active_lock_name = None
                self._lockscreen_proc = None
                return

            if self._is_intentionally_unlocked(active.name):
                self._active_lock_name = active.name
                self._lockscreen_proc = None
                return

            service_state = self._get_service_state()
            if service_state == "RUNNING":
                return

            if (
                self._active_lock_name == active.name
                and self._lockscreen_proc is not None
                and self._lockscreen_proc.poll() is None
            ):
                return

            remaining = max(
                1,
                int((active.unlock_at - datetime.datetime.now()).total_seconds()),
            )
            self._terminate_process(self._warning_proc)
            self._warning_proc = None
            self._warning_name = active.name
            creationflags = 0
            if os.name == "nt":
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

            self._lockscreen_proc = subprocess.Popen(
                app_command(
                    "--lockscreen",
                    "--prayer",
                    active.display_name,
                    "--duration",
                    str(remaining),
                ),
                creationflags=creationflags,
            )
            self._active_lock_name = active.name
            logger.warning(
                "Windows service is %s; launched lockscreen from tray for %s.",
                service_state,
                active.display_name,
            )
        except Exception as e:
            logger.error(f"Tray lock enforcement failed: {e}", exc_info=True)

    def _enforce_warning_overlay(self):
        service_state = self._get_service_state()
        now = datetime.datetime.now()
        warning_lead_seconds = self._get_overlay_lead_seconds()
        if warning_lead_seconds <= 0:
            return

        for entry in self._scheduler.get_schedule():
            if self._is_intentionally_unlocked(entry.name):
                continue

            seconds_until_athan = (entry.prayer_time - now).total_seconds()
            seconds_until_lock = (entry.lock_at - now).total_seconds()
            if not (0 < seconds_until_athan <= warning_lead_seconds and seconds_until_lock > 0):
                continue

            if (
                self._warning_name == entry.name
                and self._warning_proc is not None
                and self._warning_proc.poll() is None
            ):
                return

            creationflags = 0
            if os.name == "nt":
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

            self._warning_proc = subprocess.Popen(
                app_command(
                    "--warning-overlay",
                    "--prayer",
                    entry.display_name,
                    "--athan-seconds",
                    str(max(1, int(seconds_until_athan))),
                    "--lock-seconds",
                    str(max(1, int(seconds_until_lock))),
                    "--suppress-seconds",
                    str(max(1, int((entry.unlock_at - now).total_seconds()))),
                    "--parent-pid",
                    str(os.getpid()),
                ),
                creationflags=creationflags,
            )
            self._warning_name = entry.name
            logger.info(
                "Launched warning overlay for %s (service %s).",
                entry.display_name,
                service_state,
            )
            return

    def _is_intentionally_unlocked(self, prayer_name: str) -> bool:
        try:
            from lock_state import is_intentionally_unlocked
            return is_intentionally_unlocked(prayer_name)
        except Exception as e:
            logger.debug(f"Intentional unlock check failed: {e}")
            return False

    def _get_overlay_lead_seconds(self) -> int:
        try:
            minutes = int(self.config.get("overlay_warning_minutes", 5))
        except Exception:
            minutes = 5
        return max(0, minutes) * 60

    def _terminate_process(self, proc):
        if proc is None:
            return
        try:
            if proc.poll() is None:
                proc.terminate()
        except Exception:
            pass

    def _cleanup_child_processes(self):
        self._terminate_process(self._warning_proc)
        self._warning_proc = None

    def _test_warning_overlay(self):
        try:
            creationflags = 0
            if os.name == "nt":
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
            self._terminate_process(self._warning_proc)
            self._warning_proc = subprocess.Popen(
                app_command(
                    "--warning-overlay",
                    "--prayer",
                    "Dhuhr",
                    "--athan-seconds",
                    "5",
                    "--lock-seconds",
                    "10",
                    "--suppress-seconds",
                    "30",
                    "--ignore-dismissal",
                    "--parent-pid",
                    str(os.getpid()),
                ),
                creationflags=creationflags,
            )
            self._warning_name = "Dhuhr"
        except Exception as e:
            QMessageBox.warning(None, "PrayerLock", f"Could not launch warning overlay:\n{e}")

    def _dismiss_upcoming_prayer(self):
        target = self._get_dismiss_target()
        if target is None:
            QMessageBox.information(
                None,
                "PrayerLock",
                "No upcoming prayer lock was found for today.",
            )
            return

        pwd, ok = QInputDialog.getText(
            None,
            "PrayerLock",
            f"Enter master password to skip {target.display_name}:",
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            return
        if not self.config.verify_password(pwd):
            QMessageBox.warning(None, "PrayerLock", "Incorrect password.")
            return

        try:
            from lock_state import mark_intentionally_unlocked
            now = datetime.datetime.now()
            suppress_seconds = max(1, int((target.unlock_at - now).total_seconds()))
            mark_intentionally_unlocked(target.name, suppress_seconds)
            self._active_lock_name = target.name
            self._warning_name = target.name
            self._terminate_process(self._warning_proc)
            self._lockscreen_proc = None
            self._warning_proc = None
            self._update_next_prayer()
            QMessageBox.information(
                None,
                "PrayerLock",
                f"{target.display_name} overlay and lock were skipped.",
            )
        except Exception as e:
            QMessageBox.warning(None, "PrayerLock", f"Could not skip prayer:\n{e}")

    def _get_dismiss_target(self):
        now = datetime.datetime.now()
        schedule = self._scheduler.get_schedule()
        active = self._scheduler.should_be_locked()
        if active is not None:
            return active

        candidates = [
            entry for entry in schedule
            if entry.unlock_at > now and not self._is_intentionally_unlocked(entry.name)
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda entry: entry.prayer_time)
        return candidates[0]

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_dashboard()

    def _show_dashboard(self):
        if self._dashboard is None or not self._dashboard.isVisible():
            self._dashboard = DashboardWindow(
                self.config,
                self._scheduler,
                tray_app=self,
            )
        self._dashboard.show()
        self._dashboard.raise_()
        self._dashboard.activateWindow()
        self._dashboard._load_data()

    def _request_quit(self):
        pwd, ok = QInputDialog.getText(
            None,
            "PrayerLock",
            "Enter master password to quit:",
            QLineEdit.EchoMode.Password
        )
        if ok and pwd:
            if self.config.verify_password(pwd):
                self._cleanup_child_processes()
                QApplication.instance().quit()
            else:
                QMessageBox.warning(None, "PrayerLock", "Incorrect password.")

    def run(self):
        """Start the tray app (non-blocking — event loop managed by caller)."""
        pass
