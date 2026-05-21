import sys
from pathlib import Path
from datetime import date, datetime


def _user_data_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def _resource_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget,
                              QHBoxLayout, QVBoxLayout, QStackedWidget,
                              QLabel, QPushButton, QSplitter)
from PyQt6.QtGui import QAction, QFontDatabase, QFont
from PyQt6.QtCore import Qt, QTimer, QRect, QEvent
from db import init_db
from ui.status import StatusWidget
from ui.memo import MemoWidget
from ui.themes import THEMES, DEFAULT_THEME, get_stylesheet
from ui.calender import CalendarWidget
from ui.todo import TodoWidget
from ui.dday import DdayWidget
from ui.reminder import ReminderWidget
import json

CONFIG_PATH = _user_data_dir() / "config.json"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📅 Idiary")
        self.setMinimumSize(900, 650)
        icon_path = _resource_dir() / "icon" / "diary.ico"
        if icon_path.exists():
            from PyQt6.QtGui import QIcon
            self.setWindowIcon(QIcon(str(icon_path)))
        self._load_config()

        init_db()
        self._build_menubar()
        self._build_ui()
        self._apply_theme(self.current_theme_key)

        self.setWindowOpacity(self.current_opacity)
        if self.desktop_mode:
            self._apply_desktop_flags(True)
        elif self.always_on_top:
            self.setWindowFlags(
                self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
            )
            self.show()
        self._drag_pos = None

        self._fired_today: set = set()
        self._check_startup_notifications()

        self._reminder_timer = QTimer(self)
        self._reminder_timer.setInterval(10_000)
        self._reminder_timer.timeout.connect(self._check_reminders)
        self._reminder_timer.start()
        self._check_reminders()


    def _load_config(self):
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
            self.current_theme_key = config.get("theme", DEFAULT_THEME)
            family = config.get("font_family", "NanumSquare Neo OTF")
            size = config.get("font_size", 13)
            self.app_font = QFont(family if family != "NanumSquare Neo OTF" else "NanumSquare Neo OTF", size)
            self.current_opacity  = config.get("opacity", 1.0)
            self.always_on_top    = config.get("always_on_top", False)
            self.desktop_mode     = config.get("desktop_mode", False)
        else:
            self.current_theme_key = DEFAULT_THEME
            self.app_font          = QFont("NanumSquare Neo OTF", 13)
            self.current_opacity   = 1.0
            self.always_on_top     = False
            self.desktop_mode      = False

    def _save_config(self):
        config = {
            "theme":         self.current_theme_key,
            "font_family":   self.app_font.family(),
            "font_size":     self.app_font.pointSize(),
            "opacity":       self.current_opacity,
            "always_on_top": self.always_on_top,
            "desktop_mode":  self.desktop_mode,
        }
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def _open_font_dialog(self):
        from PyQt6.QtWidgets import QFontDialog
        font, ok = QFontDialog.getFont(self.app_font, self)
        if ok:
            self.app_font = font
            QApplication.instance().setFont(font)
            self._apply_theme(self.current_theme_key)

    def _build_menubar(self):
        menubar = self.menuBar()

        # 설정 메뉴
        settings_menu = menubar.addMenu("설정")
        theme_menu = settings_menu.addMenu("🎨 테마")
        font_action = QAction("🔤 폰트 설정", self)
        font_action.triggered.connect(self._open_font_dialog)
        settings_menu.addAction(font_action)
        for key, theme in THEMES.items():
            action = QAction(theme["name"], self)
            action.setCheckable(True)
            action.setChecked(key == self.current_theme_key)
            action.triggered.connect(lambda checked, k=key: self._apply_theme(k))
            theme_menu.addAction(action)
        self._theme_menu = theme_menu

        settings_menu.addSeparator()
        opacity_menu = settings_menu.addMenu("🔆 투명도")
        self._opacity_menu = opacity_menu
        for pct in [100, 90, 80, 70, 60, 50]:
            act = QAction(f"{pct}%", self)
            act.setCheckable(True)
            act.setChecked(pct == int(round(self.current_opacity * 100)))
            act.triggered.connect(lambda _, v=pct / 100: self._set_opacity(v))
            opacity_menu.addAction(act)

        self.aot_action = QAction("📌 항상 위에 고정", self)
        self.aot_action.setCheckable(True)
        self.aot_action.setChecked(self.always_on_top)
        self.aot_action.triggered.connect(self._toggle_always_on_top)
        settings_menu.addAction(self.aot_action)

        self.desktop_action = QAction("🖥️ 바탕화면에 고정", self)
        self.desktop_action.setCheckable(True)
        self.desktop_action.setChecked(self.desktop_mode)
        self.desktop_action.triggered.connect(self._toggle_desktop_mode)
        settings_menu.addAction(self.desktop_action)

        settings_menu.addSeparator()
        export_action = QAction("📤 데이터 내보내기", self)
        export_action.triggered.connect(self._export_data)
        settings_menu.addAction(export_action)
        import_action = QAction("📥 데이터 가져오기", self)
        import_action.triggered.connect(self._import_data)
        settings_menu.addAction(import_action)


    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self._build_main_page())

    def _build_main_page(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(0)

        self.calendar = CalendarWidget(THEMES[self.current_theme_key])
        self.calendar.date_clicked.connect(self._on_date_selected)
        self.calendar.date_double_clicked.connect(self._on_date_selected)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)

        # 오른쪽 패널: 사이드바 + 콘텐츠
        right_panel = QWidget()
        right_panel.setObjectName("rightPanel")
        right_panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        right_h = QHBoxLayout(right_panel)
        right_h.setContentsMargins(0, 0, 0, 0)
        right_h.setSpacing(0)

        # 사이드바
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sideBar")
        self.sidebar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.sidebar.setFixedWidth(68)
        sidebar_v = QVBoxLayout(self.sidebar)
        sidebar_v.setContentsMargins(6, 12, 6, 12)
        sidebar_v.setSpacing(4)
        sidebar_v.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._mascot_label = QLabel()
        self._mascot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._mascot_label.setFont(QFont("Segoe UI Emoji", 26))
        self._mascot_label.setFixedHeight(52)
        sidebar_v.addWidget(self._mascot_label)

        self._sidebar_btns: list[QPushButton] = []
        self._sidebar_tab_defs = [("📝", "메모"), ("📅", "D-day"), ("⏰", "알림"), ("📊", "통계"), ("✅", "TODO")]
        for i, (icon, label) in enumerate(self._sidebar_tab_defs):
            btn = QPushButton(f"{icon}\n{label}")
            btn.setCheckable(True)
            btn.setFixedHeight(60)
            btn.setFont(QFont("NanumSquare Neo OTF", 9))
            btn.clicked.connect(lambda _, idx=i: self._switch_right_tab(idx))
            sidebar_v.addWidget(btn)
            self._sidebar_btns.append(btn)
        sidebar_v.addStretch()

        # 콘텐츠 스택
        self.right_stack = QStackedWidget()

        self.memo_widget     = MemoWidget(THEMES[self.current_theme_key])
        self.dday_widget     = DdayWidget(THEMES[self.current_theme_key])
        self.reminder_widget = ReminderWidget(THEMES[self.current_theme_key])
        self.status_widget   = StatusWidget(THEMES[self.current_theme_key])
        self.todo_widget     = TodoWidget(THEMES[self.current_theme_key])

        self.right_stack.addWidget(self.memo_widget)
        self.right_stack.addWidget(self.dday_widget)
        self.right_stack.addWidget(self.reminder_widget)
        self.right_stack.addWidget(self.status_widget)
        self.right_stack.addWidget(self.todo_widget)

        self.dday_widget.dday_changed.connect(self.calendar.refresh)
        self.reminder_widget.reminder_added.connect(self._check_reminders)
        self.todo_widget.todo_changed.connect(self.status_widget.refresh)
        self.memo_widget.memo_changed.connect(self.calendar.refresh)

        right_h.addWidget(self.sidebar)
        right_h.addWidget(self.right_stack)

        self._switch_right_tab(0)

        self._splitter.addWidget(self.calendar)
        self._splitter.addWidget(right_panel)
        self._splitter.setStretchFactor(0, 3)
        self._splitter.setStretchFactor(1, 2)
        layout.addWidget(self._splitter)

        return page

    def _switch_right_tab(self, idx: int):
        self.right_stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._sidebar_btns):
            btn.setChecked(i == idx)
        self._update_sidebar_style()

    def _update_sidebar_style(self):
        t = THEMES[self.current_theme_key]
        self.sidebar.setStyleSheet(f"""
            QWidget#sideBar {{
                background-color: {t['surface2']};
                border-right: 1px solid {t['border']};
            }}
        """)

        # 마스코트 이모지 (테마마다 다름)
        mascot = t.get("mascot", "")
        self._mascot_label.setText(mascot)
        self._mascot_label.setVisible(bool(mascot))

        # 테마별 아이콘 (고양이 테마는 고양이 아이콘)
        nav_icons = t.get("nav_icons", None)
        labels = ["메모", "D-day", "알림", "통계", "TODO"]
        defaults = ["📝", "📅", "⏰", "📊", "✅"]
        icons = nav_icons if nav_icons else defaults
        for btn, icon, label in zip(self._sidebar_btns, icons, labels):
            btn.setText(f"{icon}\n{label}")

        for btn in self._sidebar_btns:
            if btn.isChecked():
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {t['primary']};
                        color: #ffffff;
                        border: none;
                        border-radius: 10px;
                        font-size: 9pt;
                        font-weight: bold;
                        padding: 4px 2px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {t['text_sub']};
                        border: none;
                        border-radius: 10px;
                        font-size: 9pt;
                        padding: 4px 2px;
                    }}
                    QPushButton:hover {{
                        background-color: {t['border']};
                        color: {t['text']};
                    }}
                """)

    def _on_date_selected(self, selected_date: date):
        self.memo_widget.load_date(selected_date)

    def _apply_theme(self, key: str):
        self.current_theme_key = key
        theme = THEMES[key]
        family = self.app_font.family() if hasattr(self, 'app_font') else "NanumSquare Neo OTF"
        size   = self.app_font.pointSize() if hasattr(self, 'app_font') else 13
        self.setStyleSheet(get_stylesheet(theme, family, size))
        self._save_config()

        # 각 위젯 테마 업데이트
        if hasattr(self, 'calendar'):
            self.calendar.update_theme(theme)
        if hasattr(self, 'todo_widget'):
            self.todo_widget.update_theme(theme)
        if hasattr(self, 'dday_widget'):
            self.dday_widget.update_theme(theme)
        if hasattr(self, 'reminder_widget'):
            self.reminder_widget.update_theme(theme)
        if hasattr(self, 'status_widget'):
            self.status_widget.update_theme(theme)
        if hasattr(self, '_sidebar_btns'):
            self._update_sidebar_style()
        if hasattr(self, 'memo_widget'):
            self.memo_widget.update_theme(theme)

        # 메뉴 체크 상태 업데이트
        for action in self._theme_menu.actions():
            action.setChecked(action.text() == theme["name"])

    def _set_opacity(self, value: float):
        self.current_opacity = value
        self.setWindowOpacity(value)
        for act in self._opacity_menu.actions():
            act.setChecked(act.text() == f"{int(round(value * 100))}%")
        self._save_config()

    def _toggle_always_on_top(self, checked: bool):
        self.always_on_top = checked
        if checked and self.desktop_mode:
            self._toggle_desktop_mode(False)
        flags = self.windowFlags()
        if checked:
            self.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()
        self._save_config()

    def _apply_desktop_flags(self, enable: bool):
        if enable:
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnBottomHint |
                Qt.WindowType.Tool
            )
            self.menuBar().hide()
            QApplication.instance().installEventFilter(self)
        else:
            self.setWindowFlags(Qt.WindowType.Window)
            self.menuBar().show()
            QApplication.instance().removeEventFilter(self)
        self.show()

    def eventFilter(self, _, event):
        if self.desktop_mode and event.type() == QEvent.Type.MouseMove:
            if not event.buttons():
                local = self.mapFromGlobal(event.globalPosition().toPoint())
                self.setCursor(self._resize_cursor(*self._resize_edges(local)))
        return False

    def _toggle_desktop_mode(self, checked: bool):
        self.desktop_mode = checked
        if checked and self.always_on_top:
            self.always_on_top = False
            self.aot_action.setChecked(False)
        self._apply_desktop_flags(checked)
        if hasattr(self, 'desktop_action'):
            self.desktop_action.setChecked(checked)
        self._save_config()

    def contextMenuEvent(self, event):
        if self.desktop_mode:
            from PyQt6.QtWidgets import QMenu
            menu = QMenu(self)
            menu.addAction("⚙️ 설정 열기").triggered.connect(self._exit_desktop_and_settings)
            menu.addAction("🖥️ 바탕화면 고정 해제").triggered.connect(
                lambda: self._toggle_desktop_mode(False)
            )
            menu.exec(event.globalPos())

    def _exit_desktop_and_settings(self):
        self._toggle_desktop_mode(False)

    _RESIZE_MARGIN = 8

    def _resize_edges(self, pos):
        m, w, h = self._RESIZE_MARGIN, self.width(), self.height()
        return (pos.x() < m, pos.y() < m,
                pos.x() > w - m, pos.y() > h - m)  # left, top, right, bottom

    def _resize_cursor(self, left, top, right, bottom):
        if (left and top) or (right and bottom): return Qt.CursorShape.SizeFDiagCursor
        if (right and top) or (left and bottom): return Qt.CursorShape.SizeBDiagCursor
        if left or right:                        return Qt.CursorShape.SizeHorCursor
        if top or bottom:                        return Qt.CursorShape.SizeVerCursor
        return Qt.CursorShape.ArrowCursor

    def mousePressEvent(self, event):
        if self.desktop_mode and event.button() == Qt.MouseButton.LeftButton:
            local = event.position().toPoint()
            edges = self._resize_edges(local)
            if any(edges):
                self._resize_dir   = edges
                self._resize_origin = event.globalPosition().toPoint()
                self._resize_geo   = self.geometry()
                self._drag_pos     = None
            else:
                self._drag_pos     = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                self._resize_dir   = None

    def mouseMoveEvent(self, event):
        if not self.desktop_mode:
            return
        gpos  = event.globalPosition().toPoint()
        local = event.position().toPoint()
        if not event.buttons():
            self.setCursor(self._resize_cursor(*self._resize_edges(local)))
        elif event.buttons() == Qt.MouseButton.LeftButton:
            if self._resize_dir:
                left, top, right, bottom = self._resize_dir
                dx = gpos.x() - self._resize_origin.x()
                dy = gpos.y() - self._resize_origin.y()
                geo = QRect(self._resize_geo)
                min_w, min_h = self.minimumWidth(), self.minimumHeight()
                if left   and geo.width()  - dx >= min_w: geo.setLeft(geo.left()   + dx)
                if top    and geo.height() - dy >= min_h: geo.setTop(geo.top()     + dy)
                if right:  geo.setRight(geo.right()   + dx)
                if bottom: geo.setBottom(geo.bottom() + dy)
                if geo.width() >= min_w and geo.height() >= min_h:
                    self.setGeometry(geo)
            elif self._drag_pos is not None:
                self.move(gpos - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos    = None
        self._resize_dir  = None
        self.unsetCursor()
        super().mouseReleaseEvent(event)

    def _notify(self, title: str, msg: str):
        from ui.toast import Toast
        Toast(title, msg, THEMES[self.current_theme_key])

    def _export_data(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from db import export_data
        path, _ = QFileDialog.getSaveFileName(
            self, "데이터 내보내기", "diary_backup.json", "JSON 파일 (*.json)"
        )
        if not path:
            return
        data = export_data()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        QMessageBox.information(self, "완료", "데이터를 내보냈어요! ✓")

    def _import_data(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from db import import_data
        path, _ = QFileDialog.getOpenFileName(
            self, "데이터 가져오기", "", "JSON 파일 (*.json)"
        )
        if not path:
            return
        reply = QMessageBox.question(
            self, "확인",
            "기존 데이터가 모두 교체됩니다.\n계속할까요?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        import_data(data)
        self.calendar.refresh()
        self.memo_widget.load_date(date.today())
        for widget in (self.dday_widget, self.reminder_widget, self.status_widget):
            widget.refresh()
        QMessageBox.information(self, "완료", "데이터를 가져왔어요! ✓")

    def _check_startup_notifications(self):
        from db import get_ddays, get_todos_for_date
        today = date.today()

        approaching = []
        for _, name, target_str in get_ddays():
            delta = (date.fromisoformat(target_str) - today).days
            if 0 <= delta <= 3:
                label = "D-Day! 🎉" if delta == 0 else f"D-{delta}"
                approaching.append(f"{name}  {label}")
        if approaching:
            self._notify("📅 D-day 임박", "\n".join(approaching))

        undone = [t for t in get_todos_for_date(str(today)) if not t[3]]
        if undone:
            self._notify("✅ 오늘 할일", f"미완료 {len(undone)}개가 남았어요")

    def _check_reminders(self):
        from db import get_reminders
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        today = str(now.date())

        for rid, title, time, enabled in get_reminders():
            if not enabled:
                continue
            key = (today, rid)
            if time == current_time and key not in self._fired_today:
                self._fired_today.add(key)
                self._notify("⏰ 리마인더", title)

        self._fired_today = {k for k in self._fired_today if k[0] == today}


if __name__ == "__main__":
    app = QApplication(sys.argv)

    icon_path = _resource_dir() / "icon" / "diary.ico"
    if icon_path.exists():
        from PyQt6.QtGui import QIcon
        app.setWindowIcon(QIcon(str(icon_path)))

    font_path = _resource_dir() / "assets" / "fonts"
    font_family = "NanumSquare Neo OTF Neo"
    fid = QFontDatabase.addApplicationFont(str(font_path / "NanumSquareNeoOTF-Rg.otf"))
    QFontDatabase.addApplicationFont(str(font_path / "NanumSquareNeoOTF-Bd.otf"))
    if fid != -1:
        loaded = QFontDatabase.applicationFontFamilies(fid)
        if loaded:
            font_family = loaded[0]
    app.setFont(QFont(font_family, 11))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())