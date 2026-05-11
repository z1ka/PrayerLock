"""
PrayerLock Setup Wizard
Modern multi-step setup wizard for first-time configuration.
"""
import sys
import os
import subprocess
import requests

from PyQt6.QtWidgets import (
    QWidget, QWizard, QWizardPage, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QSpinBox, QFrame, QApplication, QSizePolicy, QDoubleSpinBox,
    QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QPixmap, QPalette, QColor, QIcon

# Flat structure
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


DARK_STYLE = """
QWizard, QWizardPage {
    background-color: #0C1223;
    color: #E8E0D0;
    font-family: 'Segoe UI', Arial, sans-serif;
}
QWizard > QPushButton, QWizardPage QPushButton {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #8B6914,stop:1 #D4A028);
    border: none;
    border-radius: 8px;
    color: white;
    font-size: 13px;
    font-weight: bold;
    padding: 10px 24px;
    min-width: 90px;
}
QWizard > QPushButton:hover {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #D4A028,stop:1 #F0BC38);
}
QWizard > QPushButton#qt_wizard_back {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.15);
    color: rgba(255,255,255,0.7);
}
QWizard > QPushButton#qt_wizard_cancel {
    background: transparent;
    border: none;
    color: rgba(255,255,255,0.4);
}
QLineEdit {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(212,160,40,0.3);
    border-radius: 10px;
    color: white;
    font-size: 14px;
    padding: 10px 14px;
    selection-background-color: #D4A028;
}
QLineEdit:focus {
    border: 1px solid rgba(212,160,40,0.8);
    background: rgba(255,255,255,0.09);
}
QComboBox {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(212,160,40,0.3);
    border-radius: 10px;
    color: white;
    font-size: 13px;
    padding: 9px 14px;
    min-height: 36px;
}
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background: #1A2540;
    border: 1px solid rgba(212,160,40,0.3);
    color: white;
    selection-background-color: rgba(212,160,40,0.3);
}
QSpinBox, QDoubleSpinBox {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(212,160,40,0.3);
    border-radius: 10px;
    color: white;
    font-size: 13px;
    padding: 8px 12px;
}
QCheckBox {
    color: rgba(230,220,200,0.9);
    font-size: 13px;
    spacing: 10px;
}
QCheckBox::indicator {
    width: 18px; height: 18px;
    border: 1px solid rgba(212,160,40,0.4);
    border-radius: 4px;
    background: rgba(255,255,255,0.05);
}
QCheckBox::indicator:checked {
    background: #D4A028;
    border-color: #D4A028;
}
QLabel { color: #E8E0D0; background: transparent; }
"""


TIMEZONES = [
    "Asia/Riyadh", "Asia/Mecca", "Asia/Dubai", "Asia/Karachi",
    "Asia/Dhaka", "Asia/Kolkata", "Asia/Jakarta", "Asia/Kuala_Lumpur",
    "Asia/Baghdad", "Asia/Tehran",
    "Africa/Cairo", "Africa/Tunis", "Africa/Algiers", "Africa/Casablanca",
    "Africa/Khartoum", "Africa/Nairobi", "Africa/Dakar",
    "Europe/Istanbul", "Europe/London", "America/New_York", "America/Chicago",
    "America/Los_Angeles", "America/Toronto", "Australia/Sydney",
]

CITIES = [
    "Mecca", "Medina", "Riyadh", "Jeddah", "Dammam", "Khobar", "Dhahran",
    "Taif", "Tabuk", "Abha", "Khamis Mushait", "Buraidah", "Hail",
    "Jazan", "Najran", "Yanbu", "Al Jubail", "Al Ahsa", "Cairo", "Dubai", "Istanbul",
    "Karachi", "Lahore", "Dhaka", "Jakarta", "Kuala Lumpur", "London",
    "New York", "Chicago", "Los Angeles", "Toronto", "Sydney",
    "Islamabad", "Baghdad", "Tehran", "Ankara", "Casablanca", "Tunis",
    "Algiers", "Khartoum", "Nairobi", "Dakar",
]

CITY_COORDS = {
    "Mecca": (21.3891, 39.8579), "Medina": (24.4686, 39.6142),
    "Riyadh": (24.6877, 46.7219), "Jeddah": (21.5433, 39.1728),
    "Dammam": (26.4207, 50.0888), "Khobar": (26.2172, 50.1971),
    "Dhahran": (26.2361, 50.0393), "Taif": (21.4373, 40.5127),
    "Tabuk": (28.3838, 36.5550), "Abha": (18.2465, 42.5117),
    "Khamis Mushait": (18.3064, 42.7292), "Buraidah": (26.3592, 43.9818),
    "Hail": (27.5114, 41.7208), "Jazan": (16.8892, 42.5511),
    "Najran": (17.5656, 44.2289), "Yanbu": (24.0895, 38.0618),
    "Al Jubail": (27.0046, 49.6460), "Al Ahsa": (25.3830, 49.5866),
    "Cairo": (30.0444, 31.2357), "Dubai": (25.2048, 55.2708),
    "Istanbul": (41.0082, 28.9784), "Karachi": (24.8607, 67.0011),
    "Lahore": (31.5204, 74.3587), "Dhaka": (23.8103, 90.4125),
    "Jakarta": (-6.2088, 106.8456), "Kuala Lumpur": (3.1390, 101.6869),
    "London": (51.5074, -0.1278), "New York": (40.7128, -74.0060),
    "Chicago": (41.8781, -87.6298), "Los Angeles": (34.0522, -118.2437),
    "Toronto": (43.6532, -79.3832), "Sydney": (-33.8688, 151.2093),
    "Islamabad": (33.6844, 73.0479), "Baghdad": (33.3152, 44.3661),
    "Tehran": (35.6892, 51.3890), "Ankara": (39.9334, 32.8597),
    "Casablanca": (33.5731, -7.5898), "Tunis": (36.8065, 10.1815),
    "Algiers": (36.7372, 3.0865), "Khartoum": (15.5007, 32.5599),
    "Nairobi": (-1.2921, 36.8219), "Dakar": (14.7167, -17.4677),
}

CITY_TIMEZONES = {
    city: "Asia/Riyadh"
    for city in [
        "Mecca", "Medina", "Riyadh", "Jeddah", "Dammam", "Khobar",
        "Dhahran", "Taif", "Tabuk", "Abha", "Khamis Mushait", "Buraidah",
        "Hail", "Jazan", "Najran", "Yanbu", "Al Jubail", "Al Ahsa",
    ]
}
CITY_TIMEZONES.update({
    "Cairo": "Africa/Cairo", "Dubai": "Asia/Dubai",
    "Istanbul": "Europe/Istanbul", "Karachi": "Asia/Karachi",
    "Lahore": "Asia/Karachi", "Islamabad": "Asia/Karachi",
    "Dhaka": "Asia/Dhaka", "Jakarta": "Asia/Jakarta",
    "Kuala Lumpur": "Asia/Kuala_Lumpur", "London": "Europe/London",
    "New York": "America/New_York", "Chicago": "America/Chicago",
    "Los Angeles": "America/Los_Angeles", "Toronto": "America/Toronto",
    "Sydney": "Australia/Sydney", "Baghdad": "Asia/Baghdad",
    "Tehran": "Asia/Tehran", "Ankara": "Europe/Istanbul",
    "Casablanca": "Africa/Casablanca", "Tunis": "Africa/Tunis",
    "Algiers": "Africa/Algiers", "Khartoum": "Africa/Khartoum",
    "Nairobi": "Africa/Nairobi", "Dakar": "Africa/Dakar",
})

CALC_METHODS = [
    "UmmAlQura", "MWL", "ISNA", "Egypt", "Karachi",
    "Gulf", "Kuwait", "Qatar", "Singapore", "Turkey",
]


def make_field_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet("color: rgba(230,220,200,0.7); font-size: 12px;")
    return lbl


class WelcomePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 30, 40, 30)

        logo_lbl = QLabel("🕌")
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_lbl.setStyleSheet("font-size: 72px; background: transparent;")

        title = QLabel("PrayerLock")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "color: #D4A028; font-family: Georgia, serif; font-size: 36px; font-weight: bold;"
        )

        subtitle = QLabel("Disciplined Prayer. Every Time.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(
            "color: rgba(212,160,40,0.6); font-size: 14px;"
        )

        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setMaximumWidth(280)
        divider.setStyleSheet("background: rgba(212,160,40,0.3);")

        desc = QLabel(
            "PrayerLock helps you maintain your Salah by temporarily\n"
            "locking your PC during prayer times.\n\n"
            "This setup wizard will help you configure:\n"
            "  ✦  Your location for accurate prayer times\n"
            "  ✦  A secure master password\n"
            "  ✦  Lock timing preferences"
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: rgba(230,220,200,0.75); font-size: 13px;")

        layout.addStretch()
        layout.addWidget(logo_lbl)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(8)
        layout.addWidget(divider, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addSpacing(8)
        layout.addWidget(desc)
        layout.addStretch()


class LocationPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Your Location")
        self.setSubTitle("Required for accurate prayer time calculation.")
        self.country_code = "SA"
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(30, 10, 30, 10)

        detect_row = QHBoxLayout()
        self.detect_btn = QPushButton("Detect location automatically")
        self.detect_btn.clicked.connect(self._detect_location)
        self.detect_status = QLabel("City sets coordinates and timezone automatically.")
        self.detect_status.setWordWrap(True)
        self.detect_status.setStyleSheet("color: rgba(230,220,200,0.6); font-size: 11px;")
        detect_row.addWidget(self.detect_btn)
        detect_row.addWidget(self.detect_status, 1)
        layout.addLayout(detect_row)

        layout.addWidget(make_field_label("City"))
        self.city_combo = QComboBox()
        self.city_combo.setEditable(True)
        self.city_combo.addItems(sorted(CITIES))
        self.city_combo.setCurrentText("Mecca")
        self.city_combo.currentTextChanged.connect(self._city_changed)
        layout.addWidget(self.city_combo)

        timezone_note = QLabel("Timezone is filled automatically from the selected city.")
        timezone_note.setWordWrap(True)
        timezone_note.setStyleSheet("color: rgba(230,220,200,0.55); font-size: 11px;")
        layout.addWidget(timezone_note)
        self.tz_combo = QComboBox()
        self.tz_combo.addItems(TIMEZONES)
        self.tz_combo.setCurrentText("Asia/Riyadh")

        coords_row = QHBoxLayout()
        lat_col = QVBoxLayout()
        lat_col.addWidget(make_field_label("Latitude"))
        self.lat_spin = QDoubleSpinBox()
        self.lat_spin.setRange(-90, 90)
        self.lat_spin.setDecimals(4)
        self.lat_spin.setValue(21.3891)
        lat_col.addWidget(self.lat_spin)

        lng_col = QVBoxLayout()
        lng_col.addWidget(make_field_label("Longitude"))
        self.lng_spin = QDoubleSpinBox()
        self.lng_spin.setRange(-180, 180)
        self.lng_spin.setDecimals(4)
        self.lng_spin.setValue(39.8579)
        lng_col.addWidget(self.lng_spin)

        coords_row.addLayout(lat_col)
        coords_row.addLayout(lng_col)
        layout.addLayout(coords_row)

        layout.addWidget(make_field_label("Calculation Method"))
        self.method_combo = QComboBox()
        self.method_combo.addItems(CALC_METHODS)
        self.method_combo.setCurrentText("UmmAlQura")
        layout.addWidget(self.method_combo)

        layout.addStretch()

        self.registerField("city", self.city_combo, "currentText")
        self.registerField("timezone", self.tz_combo, "currentText")
        self.registerField("calcMethod", self.method_combo, "currentText")

        QTimer.singleShot(250, self._detect_location)

    def _city_changed(self, city: str):
        if city in CITY_COORDS:
            lat, lng = CITY_COORDS[city]
            self.lat_spin.setValue(lat)
            self.lng_spin.setValue(lng)
        if city in CITY_TIMEZONES:
            self.tz_combo.setCurrentText(CITY_TIMEZONES[city])

    def _detect_location(self):
        self.detect_status.setText("Detecting...")
        QApplication.processEvents()
        try:
            resp = requests.get(
                "http://ip-api.com/json/?fields=status,message,city,country,countryCode,lat,lon,timezone",
                timeout=5,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") != "success":
                raise RuntimeError(data.get("message", "location lookup failed"))

            city = data.get("city") or "Detected location"
            self.country_code = data.get("countryCode") or ""
            timezone = data.get("timezone") or "Asia/Riyadh"
            lat = float(data.get("lat"))
            lon = float(data.get("lon"))

            if self.city_combo.findText(city) < 0:
                self.city_combo.addItem(city)
            self.city_combo.setCurrentText(city)
            self.lat_spin.setValue(lat)
            self.lng_spin.setValue(lon)
            if self.tz_combo.findText(timezone) < 0:
                self.tz_combo.addItem(timezone)
            self.tz_combo.setCurrentText(timezone)
            self.detect_status.setText(f"Detected {city}.")
        except Exception as e:
            self.detect_status.setText(
                f"Auto-detect unavailable. Choose your city manually. ({e})"
            )


class PasswordPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Master Password")
        self.setSubTitle("Set a strong password to unlock PrayerLock.")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(30, 10, 30, 10)

        info = QLabel(
            "This password will be required to unlock the screen early.\n"
            "Store it somewhere safe — there is no recovery option."
        )
        info.setWordWrap(True)
        info.setStyleSheet("""
            background: rgba(212,160,40,0.08);
            border: 1px solid rgba(212,160,40,0.2);
            border-radius: 10px;
            color: rgba(230,220,200,0.8);
            font-size: 12px;
            padding: 12px;
        """)
        layout.addWidget(info)
        layout.addSpacing(4)

        layout.addWidget(make_field_label("Master Password"))
        self.pwd1 = QLineEdit()
        self.pwd1.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd1.setPlaceholderText("Enter a strong password")
        layout.addWidget(self.pwd1)

        layout.addWidget(make_field_label("Confirm Password"))
        self.pwd2 = QLineEdit()
        self.pwd2.setEchoMode(QLineEdit.EchoMode.Password)
        self.pwd2.setPlaceholderText("Repeat the password")
        layout.addWidget(self.pwd2)

        self.strength_label = QLabel("")
        self.strength_label.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.strength_label)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #FF6B6B; font-size: 12px;")
        layout.addWidget(self.error_label)

        self.pwd1.textChanged.connect(self._update_strength)
        layout.addStretch()

    def _update_strength(self, pwd: str):
        if not pwd:
            self.strength_label.setText("")
            return
        score = sum([
            len(pwd) >= 8,
            len(pwd) >= 12,
            any(c.isupper() for c in pwd),
            any(c.isdigit() for c in pwd),
            any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in pwd),
        ])
        for threshold, label, color in [
            (1, "Weak",   "#FF6B6B"),
            (2, "Fair",   "#FFA500"),
            (3, "Good",   "#FFD700"),
            (5, "Strong", "#4CAF50"),
        ]:
            if score <= threshold:
                self.strength_label.setText(f"Strength: {label}")
                self.strength_label.setStyleSheet(f"color: {color}; font-size: 11px;")
                return
        self.strength_label.setText("Strength: Strong")
        self.strength_label.setStyleSheet("color: #4CAF50; font-size: 11px;")

    def validatePage(self):
        pwd1 = self.pwd1.text()
        pwd2 = self.pwd2.text()
        if len(pwd1) < 6:
            self.error_label.setText("Password must be at least 6 characters.")
            return False
        if pwd1 != pwd2:
            self.error_label.setText("Passwords do not match.")
            return False
        self.error_label.setText("")
        return True

    def get_password(self) -> str:
        return self.pwd1.text()


class TimingPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Lock Settings")
        self.setSubTitle("Choose exactly when PrayerLock starts and how long it stays on.")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(30, 10, 30, 10)

        summary = QLabel(
            "Example: if Dhuhr Athan is at 12:00 and the delay is 10 minutes, "
            "PrayerLock will lock your screen at 12:10."
        )
        summary.setWordWrap(True)
        summary.setStyleSheet("""
            background: rgba(212,160,40,0.08);
            border: 1px solid rgba(212,160,40,0.18);
            border-radius: 10px;
            color: rgba(230,220,200,0.82);
            font-size: 12px;
            padding: 10px 12px;
        """)
        layout.addWidget(summary)

        delay_row = QHBoxLayout()
        delay_lbl_col = QVBoxLayout()
        delay_lbl_col.addWidget(make_field_label("Start locking after Athan"))
        delay_hint = QLabel("How many minutes after Athan before the screen locks.")
        delay_hint.setWordWrap(True)
        delay_hint.setStyleSheet("color: rgba(230,220,200,0.58); font-size: 11px;")
        delay_lbl_col.addWidget(delay_hint)
        delay_row.addLayout(delay_lbl_col)
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(0, 60)
        self.delay_spin.setValue(10)
        self.delay_spin.setSuffix(" min")
        self.delay_spin.setFixedWidth(100)
        delay_row.addWidget(self.delay_spin)
        layout.addLayout(delay_row)

        overlay_row = QHBoxLayout()
        overlay_lbl_col = QVBoxLayout()
        overlay_lbl_col.addWidget(make_field_label("Show reminder before Athan"))
        overlay_hint = QLabel("How many minutes before Athan the small desktop overlay appears.")
        overlay_hint.setWordWrap(True)
        overlay_hint.setStyleSheet("color: rgba(230,220,200,0.58); font-size: 11px;")
        overlay_lbl_col.addWidget(overlay_hint)
        overlay_row.addLayout(overlay_lbl_col)
        self.overlay_spin = QSpinBox()
        self.overlay_spin.setRange(0, 30)
        self.overlay_spin.setValue(5)
        self.overlay_spin.setSuffix(" min")
        self.overlay_spin.setFixedWidth(100)
        overlay_row.addWidget(self.overlay_spin)
        layout.addLayout(overlay_row)

        duration_row = QHBoxLayout()
        duration_lbl_col = QVBoxLayout()
        duration_lbl_col.addWidget(make_field_label("Keep screen locked for"))
        duration_hint = QLabel("How long the lock screen stays active once it starts.")
        duration_hint.setWordWrap(True)
        duration_hint.setStyleSheet("color: rgba(230,220,200,0.58); font-size: 11px;")
        duration_lbl_col.addWidget(duration_hint)
        duration_row.addLayout(duration_lbl_col)
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(5, 120)
        self.duration_spin.setValue(15)
        self.duration_spin.setSuffix(" min")
        self.duration_spin.setFixedWidth(100)
        duration_row.addWidget(self.duration_spin)
        layout.addLayout(duration_row)

        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background: rgba(255,255,255,0.08);")
        layout.addWidget(divider)

        self.verse_check = QCheckBox("Show Quran verses on lock screen")
        self.verse_check.setChecked(True)
        layout.addWidget(self.verse_check)

        self.games_check = QCheckBox("Terminate game processes when locking")
        self.games_check.setChecked(False)
        layout.addWidget(self.games_check)

        self.task_mgr_check = QCheckBox("Block Task Manager during lock (admin required)")
        self.task_mgr_check.setChecked(False)
        layout.addWidget(self.task_mgr_check)

        self.startup_check = QCheckBox("Start PrayerLock automatically with Windows")
        self.startup_check.setChecked(True)
        layout.addWidget(self.startup_check)

        layout.addStretch()


class FinishPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 20, 40, 20)

        icon = QLabel("✅")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 64px;")

        title = QLabel("PrayerLock is Ready!")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "color: #D4A028; font-size: 28px; font-family: Georgia, serif; font-weight: bold;"
        )

        desc = QLabel(
            "Your prayer schedule will be calculated automatically.\n\n"
            "The service will monitor prayer times in the background\n"
            "and lock your screen when it's time to pray.\n\n"
            "بَارَكَ اللَّهُ فِيكَ\n"
            "May Allah bless you."
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet("color: rgba(230,220,200,0.8); font-size: 13px;")

        layout.addStretch()
        layout.addWidget(icon)
        layout.addWidget(title)
        layout.addSpacing(8)
        layout.addWidget(desc)
        layout.addStretch()


class SetupWizard(QWizard):
    """Multi-step setup wizard."""

    setup_complete = pyqtSignal(dict)

    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self._tray = None  # holds TrayApplication so GC doesn't collect it
        self._setup_window()
        self._add_pages()
        self.finished.connect(self._on_finish)

    def _setup_window(self):
        self.setWindowTitle("PrayerLock Setup")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setFixedSize(620, 560)
        self.setStyleSheet(DARK_STYLE)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint
        )

        # Remove side banner images
        self.setPixmap(QWizard.WizardPixmap.WatermarkPixmap, QPixmap())
        self.setPixmap(QWizard.WizardPixmap.LogoPixmap, QPixmap())
        self.setPixmap(QWizard.WizardPixmap.BannerPixmap, QPixmap())
        self.setPixmap(QWizard.WizardPixmap.BackgroundPixmap, QPixmap())

        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(
                geo.center().x() - self.width() // 2,
                geo.center().y() - self.height() // 2
            )

    def _add_pages(self):
        self._welcome  = WelcomePage()
        self._location = LocationPage()
        self._password = PasswordPage()
        self._timing   = TimingPage()
        self._finish   = FinishPage()
        for page in [self._welcome, self._location, self._password,
                     self._timing, self._finish]:
            self.addPage(page)

    def _on_finish(self, result: int):
        if result != QWizard.DialogCode.Accepted:
            QApplication.instance().quit()
            return

        try:
            # First, gather the password and main configuration data
            pwd = self._password.get_password()
            city = self._location.city_combo.currentText()
            lat  = self._location.lat_spin.value()
            lng  = self._location.lng_spin.value()

            # Build and save the main configuration dictionary
            # Note: We save this FIRST because save() may overwrite the file
            cfg = {
                "city":                 city,
                "country":              self._location.country_code,
                "timezone":             self._location.tz_combo.currentText(),
                "latitude":             lat,
                "longitude":            lng,
                "calculation_method":   self._location.method_combo.currentText(),
                "lock_delay_minutes":   self._timing.delay_spin.value(),
                "overlay_warning_minutes": self._timing.overlay_spin.value(),
                "lock_duration_minutes": self._timing.duration_spin.value(),
                "show_quran_verse":     self._timing.verse_check.isChecked(),
                "terminate_games":      self._timing.games_check.isChecked(),
                "block_task_manager":   self._timing.task_mgr_check.isChecked(),
                "startup_enabled":      self._timing.startup_check.isChecked(),
                "first_run":            False,
                "streak_count":         0,
                "total_prayers_locked": 0,
                "lock_history":         [],
            }
            self.config.save(cfg)

            # Hash and store password AFTER the main config is saved
            # to ensure it is correctly persisted in the configuration file.
            self.config.set_password(pwd)
            self._install_and_start_service()

            if self._timing.startup_check.isChecked():
                self._add_to_startup()

            self.setup_complete.emit(cfg)

            # Launch tray — keep reference alive on wizard AND on the QApp
            from tray_app import TrayApplication   # flat import
            self._tray = TrayApplication(self.config)
            app = QApplication.instance()
            if app:
                app._tray = self._tray  # noqa: SLF001

        except Exception as e:
            QMessageBox.critical(
                self, "Setup Error",
                f"Failed to save configuration:\n{e}"
            )

    def _add_to_startup(self):
        """Add PrayerLock tray app to Windows startup registry."""
        try:
            import winreg
            # In a flat installation the executable / script is in ROOT
            exe = sys.executable
            if getattr(sys, "frozen", False):
                cmd = f'"{exe}" --tray'
            else:
                script = os.path.join(ROOT, "main.py")
                cmd = f'"{exe}" "{script}" --tray'
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, "PrayerLock", 0, winreg.REG_SZ, cmd)
            winreg.CloseKey(key)
        except Exception:
            pass  # Non-fatal: user can enable startup manually

    def _install_and_start_service(self):
        if os.name != "nt":
            return
        try:
            if getattr(sys, "frozen", False):
                base_cmd = [sys.executable]
            else:
                base_cmd = [sys.executable, os.path.join(ROOT, "main.py")]

            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            subprocess.run(
                base_cmd + ["--install-service"],
                cwd=ROOT,
                creationflags=flags,
                timeout=30,
                check=False,
            )
            subprocess.run(
                base_cmd + ["--start-service"],
                cwd=ROOT,
                creationflags=flags,
                timeout=30,
                check=False,
            )
        except Exception:
            pass
