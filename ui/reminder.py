import re
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QLineEdit,
                              QScrollArea, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from db import get_reminders, add_reminder, delete_reminder, toggle_reminder
from ui.utils import clear_layout


class ReminderWidget(QWidget):
    reminder_added = pyqtSignal()

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        title = QLabel("⏰ 리마인더")
        title.setFont(QFont("NanumSquare Neo OTF", 13, QFont.Weight.Bold))

        input_layout = QHBoxLayout()
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("알림 내용")
        self.time_input = QLineEdit()
        self.time_input.setPlaceholderText("HH:MM")
        self.time_input.setFixedWidth(80)
        self.time_input.returnPressed.connect(self._add)
        add_btn = QPushButton("추가")
        add_btn.setFixedWidth(60)
        add_btn.clicked.connect(self._add)
        input_layout.addWidget(self.title_input)
        input_layout.addWidget(self.time_input)
        input_layout.addWidget(add_btn)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)

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
        t = self.theme
        reminders = get_reminders()

        if not reminders:
            empty = QLabel("리마인더를 추가해보세요!")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color: {t['text_sub']}; padding: 20px;")
            self.list_layout.addWidget(empty)
            return

        for rid, title, time, enabled in reminders:
            time_lbl = QLabel(time)
            time_lbl.setFont(QFont("NanumSquare Neo OTF", 13, QFont.Weight.Bold))
            time_lbl.setStyleSheet(
                f"color: {t['primary'] if enabled else t['text_sub']}; border: none; background: transparent;"
            )

            title_lbl = QLabel(title)
            title_lbl.setFont(QFont("NanumSquare Neo OTF", 11))
            title_lbl.setStyleSheet(
                f"color: {t['text'] if enabled else t['text_sub']}; border: none; background: transparent;"
            )

            toggle = QPushButton("🔔" if enabled else "🔕")
            toggle.setFixedSize(28, 28)
            toggle.setToolTip("알림 켜기/끄기")
            toggle.setStyleSheet("""
                QPushButton { background: transparent; border: none; font-size: 15px; padding: 0px; }
                QPushButton:hover { background: transparent; }
            """)
            toggle.clicked.connect(lambda _, i=rid: self._toggle(i))

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
            del_btn.clicked.connect(lambda _, i=rid: self._delete(i))

            row = QHBoxLayout()
            row.setContentsMargins(10, 10, 10, 10)
            row.addWidget(time_lbl)
            row.addWidget(title_lbl)
            row.addStretch()
            row.addWidget(toggle)
            row.addWidget(del_btn)

            container = QWidget()
            container.setObjectName("reminderCard")
            container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            container.setLayout(row)
            container.setStyleSheet(f"""
                QWidget#reminderCard {{
                    background-color: {t['surface']};
                    border: 1px solid {t['border']};
                    border-radius: 10px;
                }}
            """)
            self.list_layout.addWidget(container)

    def _add(self):
        title = self.title_input.text().strip()
        time  = self.time_input.text().strip()
        if not title or not time:
            return
        if not re.match(r'^\d{2}:\d{2}$', time):
            self.time_input.setPlaceholderText("형식 오류!")
            return
        h, m = int(time[:2]), int(time[3:])
        if not (0 <= h <= 23 and 0 <= m <= 59):
            self.time_input.setPlaceholderText("형식 오류!")
            return
        add_reminder(title, time)
        self.title_input.clear()
        self.time_input.clear()
        self.refresh()
        self.reminder_added.emit()

    def _toggle(self, rid: int):
        toggle_reminder(rid)
        self.refresh()

    def _delete(self, rid: int):
        delete_reminder(rid)
        self.refresh()

    def update_theme(self, theme: dict):
        self.theme = theme
        self.refresh()
