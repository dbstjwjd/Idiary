import calendar
from datetime import date
from PyQt6.QtWidgets import (QWidget, QGridLayout, QVBoxLayout,
                              QHBoxLayout, QLabel, QPushButton, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from db import get_memos_for_month, get_ddays


def _label_style(color: str) -> str:
    return f"QLabel {{ color: {color}; background: transparent; border: none; }}"


class _DayCell(QWidget):
    def __init__(self, d: date, col: int, theme: dict,
                 has_memo: bool, dday_name: str | None,
                 is_selected: bool,
                 on_click, on_dbl_click, parent=None):
        super().__init__(parent)
        self._d = d
        self._on_click = on_click
        self._on_dbl_click = on_dbl_click

        t = theme
        is_today   = (d == date.today())
        is_weekend = col == 0 or col == 6

        if is_today and is_selected:
            bg, num_color = t["surface2"], t["primary"]
            border = f"3px solid {t['primary']}"
        elif is_today:
            bg, num_color = t["surface"], t["primary"]
            border = f"3px solid {t['primary']}"
        elif is_selected:
            bg, num_color = t["surface2"], t["primary"]
            border = f"2px solid {t['primary']}"
        elif dday_name:
            bg, num_color = t["surface2"], t["primary"]
            border = f"1px solid {t['border']}"
        elif is_weekend:
            bg, num_color = t["surface2"], "#ff6b8a"
            border = f"1px solid {t['border']}"
        else:
            bg, num_color = t["surface"], t["text"]
            border = f"1px solid {t['border']}"

        self.setFixedHeight(80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("dayCell")
        self.setStyleSheet(f"""
            QWidget#dayCell {{
                background-color: {bg};
                border: {border};
                border-radius: 8px;
            }}
            QWidget#dayCell:hover {{
                border: 2px solid {t['primary']};
                background-color: {t['surface2']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 6)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        num_lbl = QLabel(str(d.day))
        num_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        num_lbl.setFont(QFont("NanumSquare Neo OTF", 14,
                               QFont.Weight.Bold if is_today else QFont.Weight.Normal))
        num_lbl.setStyleSheet(_label_style(num_color))
        layout.addWidget(num_lbl)

        if dday_name:
            dday_lbl = QLabel(dday_name)
            dday_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dday_lbl.setFont(QFont("NanumSquare Neo OTF", 9))
            dday_lbl.setStyleSheet(_label_style(t['primary']))
            dday_lbl.setWordWrap(True)
            layout.addWidget(dday_lbl)

        if has_memo:
            dot_lbl = QLabel("•")
            dot_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dot_lbl.setFont(QFont("NanumSquare Neo OTF", 6))
            dot_lbl.setStyleSheet(_label_style(t['primary']))
            layout.addWidget(dot_lbl)

        layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_click(self._d)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        self._on_dbl_click(self._d)
        super().mouseDoubleClickEvent(event)


class CalendarWidget(QWidget):
    date_clicked = pyqtSignal(date)
    date_double_clicked = pyqtSignal(date)

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.today = date.today()
        self.current_year  = self.today.year
        self.current_month = self.today.month
        self.selected_date = self.today
        self.memo_dates = {}
        self.dday_dates = {}

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        nav = QHBoxLayout()
        self.prev_btn = QPushButton("◀")
        self.next_btn = QPushButton("▶")
        self.today_btn = QPushButton("오늘")
        self.month_label = QLabel()
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.month_label.setFont(QFont("NanumSquare Neo OTF", 16, QFont.Weight.Bold))

        self.prev_btn.setFixedSize(44, 36)
        self.next_btn.setFixedSize(44, 36)
        self.today_btn.setFixedSize(48, 28)
        self.prev_btn.clicked.connect(self._prev_month)
        self.next_btn.clicked.connect(self._next_month)
        self.today_btn.clicked.connect(self._go_today)
        self._update_nav_style()

        nav.addWidget(self.prev_btn)
        nav.addWidget(self.month_label)
        nav.addWidget(self.next_btn)
        nav.addWidget(self.today_btn)

        self.grid = QGridLayout()
        self.grid.setSpacing(4)
        days = ["일", "월", "화", "수", "목", "금", "토"]
        for i, d in enumerate(days):
            lbl = QLabel(d)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFont(QFont("NanumSquare Neo OTF", 11))
            color = "#ff6b6b" if i == 0 or i == 6 else self.theme["primary"]
            lbl.setStyleSheet(f"color: {color};")
            self.grid.addWidget(lbl, 0, i)

        self.main_layout.addLayout(nav)
        self.main_layout.addLayout(self.grid)

    def refresh(self):
        for i in reversed(range(self.grid.count())):
            item = self.grid.itemAt(i)
            if item and self.grid.getItemPosition(i)[0] > 0:
                w = item.widget()
                if w:
                    w.deleteLater()

        self.month_label.setText(f"{self.current_year}년 {self.current_month}월")

        self.memo_dates = get_memos_for_month(self.current_year, self.current_month)
        self.dday_dates = {
            row[2]: row[1]
            for row in get_ddays()
            if row[2].startswith(f"{self.current_year}-{self.current_month:02d}-")
        }

        cal = calendar.Calendar(firstweekday=6).monthdayscalendar(self.current_year, self.current_month)
        for row, week in enumerate(cal):
            for col, day in enumerate(week):
                if day == 0:
                    self.grid.addWidget(QLabel(""), row + 1, col)
                    continue
                d    = date(self.current_year, self.current_month, day)
                cell = _DayCell(
                    d, col, self.theme,
                    has_memo    = str(d) in self.memo_dates,
                    dday_name   = self.dday_dates.get(str(d)),
                    is_selected = (d == self.selected_date),
                    on_click      = self._on_cell_clicked,
                    on_dbl_click  = self.date_double_clicked.emit,
                )
                self.grid.addWidget(cell, row + 1, col)

    def _on_cell_clicked(self, d: date):
        self.selected_date = d
        self.refresh()
        self.date_clicked.emit(d)

    def _prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.refresh()

    def _next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.refresh()

    def _go_today(self):
        self.current_year  = self.today.year
        self.current_month = self.today.month
        self.selected_date = self.today
        self.refresh()
        self.date_clicked.emit(self.today)

    def _update_nav_style(self):
        t = self.theme
        style = f"""
            QPushButton {{
                background-color: {t['surface2']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                padding: 4px 8px;
                font-size: 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {t['primary']};
                color: #ffffff;
                border-color: {t['primary']};
            }}
        """
        self.prev_btn.setStyleSheet(style)
        self.next_btn.setStyleSheet(style)
        self.today_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['surface2']};
                color: {t['primary']};
                border: 1px solid {t['primary']};
                border-radius: 8px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {t['primary']};
                color: #ffffff;
            }}
        """)

    def update_theme(self, theme: dict):
        self.theme = theme
        self._update_nav_style()
        self.refresh()
