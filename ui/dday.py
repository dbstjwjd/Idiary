from datetime import date, datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QLineEdit,
                              QScrollArea, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from db import get_ddays, add_dday, delete_dday
from ui.utils import clear_layout


class DdayWidget(QWidget):
    dday_changed = pyqtSignal()

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        title = QLabel("📅 D-day 관리")
        title.setFont(QFont("NanumSquare Neo OTF", 13, QFont.Weight.Bold))

        # 입력 영역
        input_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("이름 (예: 생일)")
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("날짜 (YYYY-MM-DD)")
        self.date_input.returnPressed.connect(self._add_dday)
        add_btn = QPushButton("추가")
        add_btn.setFixedWidth(60)
        add_btn.clicked.connect(self._add_dday)
        input_layout.addWidget(self.name_input)
        input_layout.addWidget(self.date_input)
        input_layout.addWidget(add_btn)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)

        # 목록 스크롤
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.list_layout.setSpacing(8)
        scroll.setWidget(self.list_container)

        layout.addWidget(title)
        layout.addLayout(input_layout)
        layout.addWidget(line)
        layout.addWidget(scroll)

    def refresh(self):
        clear_layout(self.list_layout)

        t     = self.theme
        today = date.today()
        ddays = get_ddays()

        if not ddays:
            empty = QLabel("D-day를 추가해보세요!")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color: {t['text_sub']}; padding: 20px;")
            self.list_layout.addWidget(empty)
            return

        for did, name, target_str in ddays:
            target = datetime.strptime(target_str, "%Y-%m-%d").date()
            delta  = (target - today).days

            if delta > 0:
                d_text, d_color = f"D-{delta}", t["primary"]
            elif delta == 0:
                d_text, d_color = "D-Day! 🎉", "#ff6b8a"
            else:
                d_text, d_color = f"D+{abs(delta)}", t["text_sub"]

            name_lbl = QLabel(name)
            name_lbl.setFont(QFont("NanumSquare Neo OTF", 12))
            name_lbl.setStyleSheet("border: none; background: transparent;")

            date_lbl = QLabel(target_str)
            date_lbl.setFont(QFont("NanumSquare Neo OTF", 10))
            date_lbl.setStyleSheet(f"color: {t['text_sub']}; border: none; background: transparent;")

            d_lbl = QLabel(d_text)
            d_lbl.setFont(QFont("NanumSquare Neo OTF", 13, QFont.Weight.Bold))
            d_lbl.setStyleSheet(f"color: {d_color}; border: none; background: transparent;")

            del_btn = QPushButton("✕")
            del_btn.setFixedSize(24, 24)
            del_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {t['text_sub']};
                    border: none;
                    padding: 0px;
                }}
                QPushButton:hover {{ color: #ff6b8a; }}
            """)
            del_btn.clicked.connect(lambda _, i=did: self._delete(i))

            info_col = QVBoxLayout()
            info_col.setSpacing(2)
            info_col.addWidget(name_lbl)
            info_col.addWidget(date_lbl)

            row = QHBoxLayout()
            row.setContentsMargins(10, 10, 10, 10)
            row.addLayout(info_col)
            row.addStretch()
            row.addWidget(d_lbl)
            row.addWidget(del_btn)

            container = QWidget()
            container.setObjectName("ddayCard")
            container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            container.setLayout(row)
            container.setStyleSheet(f"""
                QWidget#ddayCard {{
                    background-color: {t['surface']};
                    border: 1px solid {t['border']};
                    border-radius: 10px;
                }}
            """)
            self.list_layout.addWidget(container)

    def _add_dday(self):
        name = self.name_input.text().strip()
        d    = self.date_input.text().strip()
        if not name or not d:
            return
        try:
            datetime.strptime(d, "%Y-%m-%d")
            add_dday(name, d)
            self.name_input.clear()
            self.date_input.clear()
            self.refresh()
            self.dday_changed.emit()
        except ValueError:
            self.date_input.setPlaceholderText("형식 오류! YYYY-MM-DD")

    def _delete(self, did: int):
        delete_dday(did)
        self.refresh()
        self.dday_changed.emit()

    def update_theme(self, theme: dict):
        self.theme = theme
        self.refresh()
