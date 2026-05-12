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
    QSpinBox, QFrame, QApplication, QSizePolicy,
    QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QPixmap, QPalette, QColor, QIcon

# Flat structure
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

DROPDOWN_ARROW_PATH = os.path.join(ROOT, "assets", "dropdown_arrow.svg").replace("\\", "/")


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
    background: rgba(255,255,255,0.075);
    border: 1px solid rgba(212,160,40,0.55);
    border-radius: 10px;
    color: white;
    font-size: 13px;
    padding: 9px 46px 9px 14px;
    min-height: 36px;
}
QComboBox:hover {
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(212,160,40,0.85);
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 38px;
    border-left: 1px solid rgba(212,160,40,0.45);
    border-top-right-radius: 9px;
    border-bottom-right-radius: 9px;
    background: rgba(212,160,40,0.28);
}
QComboBox::down-arrow {
    image: url("__DROPDOWN_ARROW_PATH__");
    width: 12px;
    height: 8px;
    margin-right: 13px;
}
QComboBox QAbstractItemView {
    background: #1A2540;
    border: 1px solid rgba(212,160,40,0.3);
    color: white;
    selection-background-color: rgba(212,160,40,0.3);
}
QSpinBox {
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
""".replace("__DROPDOWN_ARROW_PATH__", DROPDOWN_ARROW_PATH)


TIMEZONES = [
    "Asia/Riyadh", "Asia/Mecca", "Asia/Dubai", "Asia/Qatar",
    "Asia/Kuwait", "Asia/Bahrain", "Asia/Muscat", "Asia/Aden",
    "Asia/Amman", "Asia/Jerusalem", "Asia/Beirut", "Asia/Damascus",
    "Asia/Karachi", "Asia/Dhaka", "Asia/Kolkata", "Asia/Jakarta",
    "Asia/Kuala_Lumpur", "Asia/Baghdad", "Asia/Tehran",
    "Africa/Cairo", "Africa/Tunis", "Africa/Algiers", "Africa/Casablanca",
    "Africa/Khartoum", "Africa/Nairobi", "Africa/Dakar",
    "Europe/Istanbul", "Europe/London", "America/New_York", "America/Chicago",
    "America/Los_Angeles", "America/Toronto", "Australia/Sydney",
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

COUNTRIES = {
    "SA": "Saudi Arabia",
    "EG": "Egypt",
    "AE": "United Arab Emirates",
    "QA": "Qatar",
    "KW": "Kuwait",
    "BH": "Bahrain",
    "OM": "Oman",
    "YE": "Yemen",
    "JO": "Jordan",
    "PS": "Palestine",
    "LB": "Lebanon",
    "SY": "Syria",
    "TR": "Turkey",
    "PK": "Pakistan",
    "BD": "Bangladesh",
    "ID": "Indonesia",
    "MY": "Malaysia",
    "GB": "United Kingdom",
    "US": "United States",
    "CA": "Canada",
    "AU": "Australia",
    "IQ": "Iraq",
    "IR": "Iran",
    "MA": "Morocco",
    "TN": "Tunisia",
    "DZ": "Algeria",
    "SD": "Sudan",
    "KE": "Kenya",
    "SN": "Senegal",
}

CITY_COUNTRIES = {
    city: "SA"
    for city in [
        "Mecca", "Medina", "Riyadh", "Jeddah", "Dammam", "Khobar",
        "Dhahran", "Taif", "Tabuk", "Abha", "Khamis Mushait", "Buraidah",
        "Hail", "Jazan", "Najran", "Yanbu", "Al Jubail", "Al Ahsa",
    ]
}
CITY_COUNTRIES.update({
    "Cairo": "EG", "Dubai": "AE", "Istanbul": "TR", "Ankara": "TR",
    "Karachi": "PK", "Lahore": "PK", "Islamabad": "PK",
    "Dhaka": "BD", "Jakarta": "ID", "Kuala Lumpur": "MY",
    "London": "GB", "New York": "US", "Chicago": "US",
    "Los Angeles": "US", "Toronto": "CA", "Sydney": "AU",
    "Baghdad": "IQ", "Tehran": "IR", "Casablanca": "MA",
    "Tunis": "TN", "Algiers": "DZ", "Khartoum": "SD",
    "Nairobi": "KE", "Dakar": "SN",
})

COUNTRY_CODES_BY_NAME = {name: code for code, name in COUNTRIES.items()}

EXTRA_CITY_DATA = {
    "United Arab Emirates": {
        "Abu Dhabi": (24.4539, 54.3773), "Sharjah": (25.3463, 55.4209),
        "Ajman": (25.4052, 55.5136), "Ras Al Khaimah": (25.8007, 55.9762),
        "Fujairah": (25.1288, 56.3265), "Al Ain": (24.1302, 55.8023),
    },
    "Qatar": {
        "Doha": (25.2854, 51.5310), "Al Rayyan": (25.2919, 51.4244),
        "Al Wakrah": (25.1659, 51.5976), "Al Khor": (25.6804, 51.4969),
        "Umm Salal": (25.4152, 51.4065),
    },
    "Kuwait": {
        "Kuwait City": (29.3759, 47.9774), "Hawalli": (29.3328, 48.0286),
        "Farwaniya": (29.2775, 47.9586), "Salmiya": (29.3339, 48.0761),
        "Jahra": (29.3375, 47.6581), "Ahmadi": (29.0769, 48.0838),
    },
    "Bahrain": {
        "Manama": (26.2235, 50.5876), "Muharraq": (26.2572, 50.6119),
        "Riffa": (26.1290, 50.5550), "Hamad Town": (26.1153, 50.5069),
        "Isa Town": (26.1736, 50.5478),
    },
    "Oman": {
        "Muscat": (23.5880, 58.3829), "Salalah": (17.0194, 54.1108),
        "Sohar": (24.3475, 56.7094), "Nizwa": (22.9333, 57.5333),
        "Sur": (22.5667, 59.5289), "Ibri": (23.2257, 56.5157),
    },
    "Yemen": {
        "Sana'a": (15.3694, 44.1910), "Aden": (12.7855, 45.0187),
        "Taiz": (13.5795, 44.0209), "Hodeidah": (14.7978, 42.9545),
        "Mukalla": (14.5425, 49.1242), "Ibb": (13.9667, 44.1833),
    },
    "Jordan": {
        "Amman": (31.9539, 35.9106), "Zarqa": (32.0728, 36.0870),
        "Irbid": (32.5556, 35.8500), "Aqaba": (29.5321, 35.0063),
        "Madaba": (31.7167, 35.8000), "Salt": (32.0392, 35.7272),
    },
    "Palestine": {
        "Jerusalem": (31.7683, 35.2137), "Gaza": (31.5017, 34.4668),
        "Hebron": (31.5326, 35.0998), "Nablus": (32.2211, 35.2544),
        "Ramallah": (31.9038, 35.2034), "Jenin": (32.4594, 35.3009),
    },
    "Lebanon": {
        "Beirut": (33.8938, 35.5018), "Tripoli": (34.4367, 35.8497),
        "Sidon": (33.5630, 35.3688), "Tyre": (33.2700, 35.2033),
        "Zahle": (33.8468, 35.9020),
    },
    "Syria": {
        "Damascus": (33.5138, 36.2765), "Aleppo": (36.2021, 37.1343),
        "Homs": (34.7324, 36.7137), "Hama": (35.1318, 36.7578),
        "Latakia": (35.5317, 35.7901), "Deir ez-Zor": (35.3359, 40.1408),
    },
    "Iraq": {
        "Basra": (30.5085, 47.7804), "Mosul": (36.3489, 43.1577),
        "Erbil": (36.1911, 44.0092), "Najaf": (32.0000, 44.3333),
        "Karbala": (32.6160, 44.0249), "Sulaymaniyah": (35.5570, 45.4350),
    },
    "Iran": {
        "Mashhad": (36.2605, 59.6168), "Isfahan": (32.6546, 51.6680),
        "Shiraz": (29.5918, 52.5837), "Tabriz": (38.0962, 46.2738),
        "Qom": (34.6416, 50.8746), "Ahvaz": (31.3183, 48.6706),
    },
    "Turkey": {
        "Konya": (37.8746, 32.4932), "Bursa": (40.1828, 29.0663),
        "Izmir": (38.4237, 27.1428), "Gaziantep": (37.0662, 37.3833),
    },
    "Egypt": {
        "Alexandria": (31.2001, 29.9187), "Giza": (30.0131, 31.2089),
        "Mansoura": (31.0409, 31.3785), "Aswan": (24.0889, 32.8998),
        "Luxor": (25.6872, 32.6396), "Suez": (29.9668, 32.5498),
    },
}

for _country_name, _cities in EXTRA_CITY_DATA.items():
    _country_code = COUNTRY_CODES_BY_NAME[_country_name]
    for _city, _coords in _cities.items():
        CITY_COORDS[_city] = _coords
        CITY_COUNTRIES[_city] = _country_code
        CITY_TIMEZONES[_city] = {
            "United Arab Emirates": "Asia/Dubai",
            "Qatar": "Asia/Qatar",
            "Kuwait": "Asia/Kuwait",
            "Bahrain": "Asia/Bahrain",
            "Oman": "Asia/Muscat",
            "Yemen": "Asia/Aden",
            "Jordan": "Asia/Amman",
            "Palestine": "Asia/Jerusalem",
            "Lebanon": "Asia/Beirut",
            "Syria": "Asia/Damascus",
            "Iraq": "Asia/Baghdad",
            "Iran": "Asia/Tehran",
            "Turkey": "Europe/Istanbul",
            "Egypt": "Africa/Cairo",
        }[_country_name]

COUNTRY_CODES_BY_NAME = {name: code for code, name in COUNTRIES.items()}
COUNTRY_CITIES = {}
for _city, _country_code in CITY_COUNTRIES.items():
    COUNTRY_CITIES.setdefault(_country_code, []).append(_city)
for _city_list in COUNTRY_CITIES.values():
    _city_list.sort()

CALC_METHODS = [
    "UmmAlQura", "MWL", "ISNA", "Egypt", "Karachi",
    "Gulf", "Kuwait", "Qatar", "Singapore", "Turkey",
]

COUNTRY_METHODS = {
    "SA": "UmmAlQura",
    "AE": "Gulf",
    "QA": "Qatar",
    "KW": "Kuwait",
    "BH": "Gulf",
    "OM": "Gulf",
    "YE": "UmmAlQura",
    "EG": "Egypt",
    "TR": "Turkey",
    "PK": "Karachi",
    "BD": "Karachi",
    "JO": "MWL",
    "PS": "MWL",
    "LB": "MWL",
    "SY": "MWL",
    "IQ": "MWL",
    "IR": "MWL",
}


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

        note = QLabel(
            "Choose your country and city. PrayerLock uses the selected city "
            "to calculate prayer times and timezone automatically."
        )
        note.setWordWrap(True)
        note.setStyleSheet("""
            background: rgba(212,160,40,0.08);
            border: 1px solid rgba(212,160,40,0.18);
            border-radius: 10px;
            color: rgba(230,220,200,0.82);
            font-size: 12px;
            padding: 10px 12px;
        """)
        layout.addWidget(note)

        detect_row = QHBoxLayout()
        self.detect_btn = QPushButton("Auto-select location")
        self.detect_btn.clicked.connect(self._detect_location)
        self.detect_status = QLabel("Uses network location as a starting point. You can change it if it is wrong.")
        self.detect_status.setWordWrap(True)
        self.detect_status.setStyleSheet("color: rgba(230,220,200,0.58); font-size: 11px;")
        detect_row.addWidget(self.detect_btn)
        detect_row.addWidget(self.detect_status, 1)
        layout.addLayout(detect_row)

        layout.addWidget(make_field_label("Country"))
        self.country_combo = QComboBox()
        self.country_combo.setEditable(True)
        self.country_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.country_combo.addItems(
            sorted(COUNTRIES.values(), key=lambda name: (name != "Saudi Arabia", name))
        )
        self.country_combo.setCurrentText("Saudi Arabia")
        self.country_combo.currentTextChanged.connect(self._country_changed)
        layout.addWidget(self.country_combo)

        layout.addWidget(make_field_label("City"))
        self.city_combo = QComboBox()
        self.city_combo.setEditable(True)
        self.city_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.city_combo.setCurrentText("Mecca")
        self.city_combo.currentTextChanged.connect(self._city_changed)
        layout.addWidget(self.city_combo)

        self.location_status = QLabel("")
        self.location_status.setWordWrap(True)
        self.location_status.setStyleSheet("color: rgba(230,220,200,0.58); font-size: 11px;")
        layout.addWidget(self.location_status)

        self.tz_combo = QComboBox()
        self.tz_combo.addItems(TIMEZONES)
        self.tz_combo.setCurrentText("Asia/Riyadh")

        layout.addWidget(make_field_label("Calculation Method"))
        self.method_combo = QComboBox()
        self.method_combo.addItems(CALC_METHODS)
        self.method_combo.setCurrentText("UmmAlQura")
        layout.addWidget(self.method_combo)

        layout.addStretch()

        self.registerField("city", self.city_combo, "currentText")
        self.registerField("timezone", self.tz_combo, "currentText")
        self.registerField("calcMethod", self.method_combo, "currentText")

        self._country_changed("Saudi Arabia")
        self._city_changed("Mecca")
        QTimer.singleShot(250, self._detect_location)

    def _country_changed(self, country_name: str):
        country_code = COUNTRY_CODES_BY_NAME.get(country_name, "SA")
        self.country_code = country_code
        cities = COUNTRY_CITIES.get(country_code, COUNTRY_CITIES["SA"])
        self.method_combo.setCurrentText(COUNTRY_METHODS.get(country_code, "MWL"))

        current = self.city_combo.currentText()
        self.city_combo.blockSignals(True)
        self.city_combo.clear()
        self.city_combo.addItems(cities)
        if current in cities:
            self.city_combo.setCurrentText(current)
        elif country_code == "SA" and "Mecca" in cities:
            self.city_combo.setCurrentText("Mecca")
        elif cities:
            self.city_combo.setCurrentText(cities[0])
        self.city_combo.blockSignals(False)
        self._city_changed(self.city_combo.currentText())

    def _city_changed(self, city: str):
        country_code = CITY_COUNTRIES.get(city, self.country_code)
        self.country_code = country_code
        country_name = COUNTRIES.get(country_code, country_code)
        if self.country_combo.currentText() != country_name:
            self.country_combo.blockSignals(True)
            self.country_combo.setCurrentText(country_name)
            self.country_combo.blockSignals(False)
        if city in CITY_TIMEZONES:
            self.tz_combo.setCurrentText(CITY_TIMEZONES[city])
        if city in CITY_COORDS:
            lat, lng = CITY_COORDS[city]
            self.location_status.setText(
                f"{city}, {country_name} selected. Timezone: {self.tz_combo.currentText()}."
            )

    def _detect_location(self):
        self.detect_status.setText("Detecting...")
        QApplication.processEvents()
        try:
            resp = requests.get(
                "http://ip-api.com/json/?fields=status,message,city,countryCode",
                timeout=5,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") != "success":
                raise RuntimeError(data.get("message", "location lookup failed"))

            country_code = data.get("countryCode") or "SA"
            city = data.get("city") or ""
            country_name = COUNTRIES.get(country_code)
            if country_name:
                self.country_combo.setCurrentText(country_name)

            city_lookup = {name.lower(): name for name in CITY_COUNTRIES}
            matched_city = city_lookup.get(city.lower())
            if matched_city and CITY_COUNTRIES.get(matched_city) == country_code:
                self.city_combo.setCurrentText(matched_city)
                self.detect_status.setText(f"Auto-selected {matched_city}. Change it if needed.")
            elif country_name:
                self.detect_status.setText(
                    f"Auto-selected {country_name}. Choose your city if this is not exact."
                )
            else:
                self.detect_status.setText("Could not match your country. Choose it manually.")
        except Exception:
            self.detect_status.setText("Auto-select unavailable. Choose country and city manually.")

    def validatePage(self):
        city = self.city_combo.currentText()
        if city not in CITY_COORDS:
            QMessageBox.warning(
                self,
                "Location Required",
                "Please choose a city from the list.",
            )
            return False
        return True

    def selected_location(self):
        city = self.city_combo.currentText()
        lat, lng = CITY_COORDS[city]
        return {
            "city": city,
            "country": CITY_COUNTRIES.get(city, self.country_code),
            "timezone": CITY_TIMEZONES.get(city, self.tz_combo.currentText()),
            "latitude": lat,
            "longitude": lng,
        }


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
            location = self._location.selected_location()

            # Build and save the main configuration dictionary
            # Note: We save this FIRST because save() may overwrite the file
            cfg = {
                "city":                 location["city"],
                "country":              location["country"],
                "timezone":             location["timezone"],
                "latitude":             location["latitude"],
                "longitude":            location["longitude"],
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
        if getattr(sys, "frozen", False):
            self._remove_per_user_startup()
            return
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

    def _remove_per_user_startup(self):
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
