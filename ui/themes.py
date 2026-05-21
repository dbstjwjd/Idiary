THEMES = {
    "idis": {
            "name": "🏢 IDIS",
            "bg": "#f0fafa",
            "surface": "#ffffff",
            "surface2": "#e0f5f5",
            "primary": "#009CA6",
            "primary_hover": "#007a82",
            "text": "#0a2e30",
            "text_sub": "#4a8a8e",
            "border": "#b0e0e4",
            "done_text": "#88c8cc",
            "calendar_selected": "#009CA6",
            "calendar_today": "#ff6b8a",
        },
    "dark": {
        "name": "🌙 Dark",
        "bg": "#1e1e2e",
        "surface": "#27273d",
        "surface2": "#313150",
        "primary": "#b4a7ff",
        "primary_hover": "#c8beff",
        "text": "#eeeef8",
        "text_sub": "#9090aa",
        "border": "#42425a",
        "done_text": "#606075",
        "calendar_selected": "#b4a7ff",
        "calendar_today": "#ff8fab",
    },
    "light": {
        "name": "☀️ Light",
        "bg": "#fafafa",
        "surface": "#ffffff",
        "surface2": "#f0f0f5",
        "primary": "#7b8cff",
        "primary_hover": "#5c6ef5",
        "text": "#2a2a3e",
        "text_sub": "#8888aa",
        "border": "#e0e0ee",
        "done_text": "#bbbbcc",
        "calendar_selected": "#7b8cff",
        "calendar_today": "#ff6b8a",
    },
    "ocean": {
        "name": "☁ Sky",
        "bg": "#eef8ff",
        "surface": "#ffffff",
        "surface2": "#ddf0fc",
        "primary": "#4db8e8",
        "primary_hover": "#2aa8de",
        "text": "#1a3244",
        "text_sub": "#6699bb",
        "border": "#c0e0f5",
        "done_text": "#99cce0",
        "calendar_selected": "#4db8e8",
        "calendar_today": "#ff7aaa",
    },
    "blossom": {
        "name": "🌸 Blossom",
        "bg": "#fff5f9",
        "surface": "#ffffff",
        "surface2": "#ffe8f2",
        "primary": "#ff80b0",
        "primary_hover": "#ff5c99",
        "text": "#3a1a28",
        "text_sub": "#cc7799",
        "border": "#ffd0e8",
        "done_text": "#ffaacb",
        "calendar_selected": "#ff80b0",
        "calendar_today": "#c084fc",
    },
    "forest": {
        "name": "🌿 Mint",
        "bg": "#f2fdf6",
        "surface": "#ffffff",
        "surface2": "#e0f8ec",
        "primary": "#3dcc88",
        "primary_hover": "#2ab874",
        "text": "#1a3328",
        "text_sub": "#66aa88",
        "border": "#c0eedb",
        "done_text": "#99ddbb",
        "calendar_selected": "#3dcc88",
        "calendar_today": "#ff7096",
    },
    "cat": {
        "name": "🐱 고양이",
        "bg": "#fff8f2",
        "surface": "#ffffff",
        "surface2": "#ffeee4",
        "primary": "#ff8c69",
        "primary_hover": "#ff7050",
        "text": "#3d2010",
        "text_sub": "#b07860",
        "border": "#ffd4b8",
        "done_text": "#d4a890",
        "calendar_selected": "#ff8c69",
        "calendar_today": "#d966b0",
        "mascot": "😸",
        "empty_todo": "냥~ 할일이 없어요 😺",
        "empty_memo": "냥냥~ 메모가 없어요 🐾\n날짜를 클릭해서 작성해봐요!",
        "nav_icons": ["🐾", "😺", "🔔", "📊"],
    },
}

DEFAULT_THEME = "light"


def get_stylesheet(theme: dict, font_family: str = "NanumSquare Neo OTF", font_size: int = 14) -> str:
    t = theme
    return f"""
    QMainWindow, QWidget {{
        background-color: {t['bg']};
        color: {t['text']};
        font-family: '{font_family}', '맑은 고딕', sans-serif;
        font-size: {font_size}pt;
    }}
    QLabel {{
        color: {t['text']};
        background: transparent;
        padding-bottom: 6px;
    }}
    QPushButton {{
        background-color: {t['primary']};
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 7px 16px;
        font-weight: bold;
        font-size: {font_size}pt;
    }}
    QPushButton:hover {{
        background-color: {t['primary_hover']};
    }}
    QPushButton[class="secondary"] {{
        background-color: {t['surface2']};
        color: {t['text']};
    }}
    QPushButton[class="secondary"]:hover {{
        background-color: {t['border']};
    }}
    QLineEdit, QTextEdit {{
        background-color: {t['surface']};
        color: {t['text']};
        border: 1.5px solid {t['border']};
        border-radius: 8px;
        padding: 7px;
        font-size: {font_size}pt;
    }}
    QLineEdit:focus, QTextEdit:focus {{
        border: 1.5px solid {t['primary']};
    }}
    QScrollBar:vertical {{
        background: {t['surface']};
        width: 6px;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical {{
        background: {t['border']};
        border-radius: 3px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QMenuBar {{
        background-color: {t['surface']};
        color: {t['text']};
        padding: 2px;
        font-size: {font_size}pt;
    }}
    QMenuBar::item:selected {{
        background-color: {t['primary']};
        color: #ffffff;
        border-radius: 4px;
    }}
    QMenu {{
        background-color: {t['surface']};
        color: {t['text']};
        border: 1px solid {t['border']};
        border-radius: 8px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 20px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: {t['primary']};
        color: #ffffff;
    }}
    QCheckBox {{
        color: {t['text']};
        font-size: {font_size}pt;
    }}
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 2px solid {t['border']};
        border-radius: 4px;
        background: {t['surface']};
    }}
    QCheckBox::indicator:checked {{
        background-color: {t['primary']};
        border-color: {t['primary']};
    }}
    QTabWidget::pane {{
        border: 1px solid {t['border']};
        border-radius: 8px;
        background-color: {t['bg']};
    }}
    QTabBar::tab {{
        color: {t['text']};
        background-color: {t['surface2']};
        padding: 6px 16px;
        min-width: 72px;
        min-height: 28px;
        border-radius: 6px;
        margin-right: 2px;
        font-size: {font_size}pt;
    }}
    QTabBar::tab:selected {{
        color: {t['primary']};
        background-color: {t['surface']};
        font-weight: bold;
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {t['border']};
    }}
    """