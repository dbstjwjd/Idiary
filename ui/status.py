from datetime import date
from PyQt6.QtWidgets import (QWidget, QVBoxLayout,
                              QLabel, QProgressBar, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from db import get_todo_stats, get_todo_stats_range


class StatusWidget(QWidget):
    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        stats_label = QLabel("📊 이번 달 할일 완료율")
        stats_label.setFont(QFont("NanumSquare Neo OTF", 12, QFont.Weight.Bold))

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")

        self.stats_detail = QLabel()
        self.stats_detail.setFont(QFont("NanumSquare Neo OTF", 10))

        self.week_label = QLabel()
        self.week_label.setFont(QFont("NanumSquare Neo OTF", 10))

        layout.addWidget(stats_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.stats_detail)
        layout.addWidget(self.week_label)
        layout.addStretch()

    def refresh(self):
        self._render_stats()

    def _render_stats(self):
        t = self.theme
        today = date.today()

        # 이번 달 통계
        total, done = get_todo_stats(today.year, today.month)
        pct = int(done / total * 100) if total > 0 else 0
        self.progress_bar.setValue(pct)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {t['surface2']};
                border-radius: 10px;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {t['primary']};
                border-radius: 10px;
            }}
        """)
        self.stats_detail.setText(
            f"이번 달: 총 {total}개 중 {done}개 완료"
        )
        self.stats_detail.setStyleSheet(f"color: {t['text_sub']};")

        # 이번 주 통계
        from datetime import timedelta
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        wtotal, wdone = get_todo_stats_range(str(week_start), str(week_end))
        wpct = int(wdone / wtotal * 100) if wtotal > 0 else 0
        self.week_label.setText(
            f"이번 주: 총 {wtotal}개 중 {wdone}개 완료 ({wpct}%)"
        )
        self.week_label.setStyleSheet(f"color: {t['text_sub']};")

    def update_theme(self, theme: dict):
        self.theme = theme
        self.refresh()