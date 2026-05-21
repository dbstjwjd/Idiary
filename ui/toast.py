from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QGraphicsOpacityEffect, QApplication)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont


class Toast(QWidget):
    _active: list = []

    def __init__(self, title: str, message: str, theme: dict):
        # 최상위 창: 투명 (border-radius 둥근 모서리용)
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        t = theme

        # 배경을 실제로 그리는 컨테이너 (WA_StyledBackground 필수)
        card = QWidget(self)
        card.setObjectName("toastCard")
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        card.setStyleSheet(f"""
            QWidget#toastCard {{
                background-color: {t['surface']};
                border: 2px solid {t['primary']};
                border-radius: 14px;
            }}
        """)

        inner = QVBoxLayout(card)
        inner.setContentsMargins(16, 12, 12, 14)
        inner.setSpacing(4)

        header = QHBoxLayout()
        header.setSpacing(8)

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("NanumSquare Neo OTF", 11, QFont.Weight.Bold))
        title_lbl.setStyleSheet(
            f"color: {t['primary']}; background: transparent; border: none;"
        )

        check_btn = QPushButton("✓")
        check_btn.setFixedSize(26, 26)
        check_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['primary']};
                color: #ffffff;
                border: none;
                border-radius: 13px;
                font-size: 13px;
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton:hover {{ background-color: {t['primary']}cc; }}
        """)
        check_btn.clicked.connect(self._start_fade_out)

        header.addWidget(title_lbl)
        header.addStretch()
        header.addWidget(check_btn)
        inner.addLayout(header)

        if message:
            msg_lbl = QLabel(message)
            msg_lbl.setFont(QFont("NanumSquare Neo OTF", 10))
            msg_lbl.setWordWrap(True)
            msg_lbl.setMaximumWidth(260)
            msg_lbl.setStyleSheet(
                f"color: {t['text']}; background: transparent; border: none;"
            )
            inner.addWidget(msg_lbl)

        # 최상위 창 레이아웃: 컨테이너만 채움
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(card)

        self.setFixedWidth(300)
        self.adjustSize()
        self._place()

        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._effect.setOpacity(0.0)

        Toast._active.append(self)
        self.show()
        self._animate(0.0, 1.0, 280)

    def _place(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.right() - self.width() - 20
        y = screen.bottom() - self.height() - 60
        for other in Toast._active:
            y -= other.height() + 10
        self.move(x, y)

    def _animate(self, start: float, end: float, ms: int):
        self._anim = QPropertyAnimation(self._effect, b"opacity")
        self._anim.setDuration(ms)
        self._anim.setStartValue(start)
        self._anim.setEndValue(end)
        self._anim.setEasingCurve(
            QEasingCurve.Type.OutCubic if end > start else QEasingCurve.Type.InCubic
        )
        self._anim.start()

    def _start_fade_out(self):
        self._animate(1.0, 0.0, 380)
        self._anim.finished.connect(self.close)

    def closeEvent(self, event):
        if self in Toast._active:
            Toast._active.remove(self)
        super().closeEvent(event)
