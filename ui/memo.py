from datetime import date as date_type
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QPushButton, QScrollArea, QFrame, QTextEdit,
                              QDialog, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QKeyCombination
from PyQt6.QtGui import QFont, QKeyEvent


class _MemoInput(QTextEdit):
    submit = pyqtSignal()

    def keyPressEvent(self, e: QKeyEvent):
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not e.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.submit.emit()
        else:
            super().keyPressEvent(e)
from db import get_notes_for_date, add_note, update_note, delete_note_by_id


class _EditDialog(QDialog):
    def __init__(self, content: str, theme: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("메모 수정")
        self.setMinimumWidth(420)
        self.setModal(True)
        t = theme

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.editor = QTextEdit()
        self.editor.setText(content)
        self.editor.setFont(QFont("NanumSquare Neo OTF", 11))
        self.editor.setMinimumHeight(130)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("취소")
        cancel_btn.setProperty("class", "secondary")
        save_btn = QPushButton("저장")
        cancel_btn.clicked.connect(self.reject)
        save_btn.clicked.connect(self.accept)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)

        layout.addWidget(self.editor)
        layout.addLayout(btn_row)

        self.setStyleSheet(f"""
            QDialog {{ background-color: {t['bg']}; }}
            QTextEdit {{
                background-color: {t['surface']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                padding: 8px;
            }}
            QTextEdit:focus {{ border-color: {t['primary']}; }}
            QPushButton {{
                background-color: {t['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 7px 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {t['primary_hover']}; }}
            QPushButton[class="secondary"] {{
                background-color: {t['surface2']};
                color: {t['text']};
            }}
            QPushButton[class="secondary"]:hover {{ background-color: {t['border']}; }}
        """)

    def get_text(self) -> str:
        return self.editor.toPlainText().strip()


class MemoWidget(QWidget):
    memo_changed = pyqtSignal()

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self.theme = theme
        self._current_date = date_type.today()
        self._build_ui()
        self.load_date(self._current_date)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.date_label = QLabel()
        self.date_label.setFont(QFont("NanumSquare Neo OTF", 13, QFont.Weight.Bold))

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(2, 2, 2, 2)
        self.cards_layout.setSpacing(8)
        self.cards_layout.addStretch()
        self.scroll.setWidget(self.cards_container)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        self.input = _MemoInput()
        self.input.setPlaceholderText("새 메모 입력... (Enter로 추가, Shift+Enter 줄바꿈)")
        self.input.submit.connect(self._add_note)
        self.input.setFont(QFont("NanumSquare Neo OTF", 11))
        self.input.setFixedHeight(72)
        self.input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.add_btn = QPushButton("추가")
        self.add_btn.setFixedSize(68, 72)
        self.add_btn.clicked.connect(self._add_note)
        input_row.addWidget(self.input)
        input_row.addWidget(self.add_btn)

        layout.addWidget(self.date_label)
        layout.addWidget(self.scroll, 1)
        layout.addLayout(input_row)

        self._apply_style()

    def _apply_style(self):
        t = self.theme
        self.date_label.setStyleSheet(f"color: {t['text']};")
        self.scroll.setStyleSheet("background: transparent;")
        self.cards_container.setStyleSheet("background: transparent;")
        self.input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {t['surface']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 8px;
                padding: 6px;
            }}
            QTextEdit:focus {{ border-color: {t['primary']}; }}
            QTextEdit {{ padding: 4px 6px; }}
        """)
        self.add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 11pt;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {t['primary_hover']}; }}
        """)

    def load_date(self, d: date_type):
        self._current_date = d
        self.date_label.setText(d.strftime("%Y년 %m월 %d일"))
        self._refresh_cards()

    def _refresh_cards(self):
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        notes = get_notes_for_date(str(self._current_date))
        if not notes:
            empty = QLabel("메모가 없어요.\n아래에서 추가해보세요!")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setFont(QFont("NanumSquare Neo OTF", 11))
            empty.setStyleSheet(f"color: {self.theme['text_sub']}; border: none;")
            self.cards_layout.insertWidget(0, empty)
        else:
            for i, (note_id, content) in enumerate(notes):
                card = self._make_card(note_id, content)
                self.cards_layout.insertWidget(i, card)

    def _make_card(self, note_id: int, content: str) -> QFrame:
        t = self.theme
        card = QFrame()
        card.setObjectName("noteCard")
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        card.setStyleSheet(f"""
            QFrame#noteCard {{
                background-color: {t['surface']};
                border: 1px solid {t['border']};
                border-radius: 8px;
            }}
        """)

        row = QHBoxLayout(card)
        row.setContentsMargins(12, 6, 8, 6)
        row.setSpacing(6)

        content_lbl = QLabel(content)
        content_lbl.setFont(QFont("NanumSquare Neo OTF", 11))
        content_lbl.setStyleSheet(f"color: {t['text']}; background: transparent; border: none;")
        content_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        edit_btn = QPushButton("수정")
        del_btn  = QPushButton("삭제")
        small_font = QFont("NanumSquare Neo OTF", 7)
        for btn in (edit_btn, del_btn):
            btn.setFixedHeight(24)
            btn.setFixedWidth(44)
            btn.setFont(small_font)
        edit_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {t['text_sub']};
                border: 1px solid {t['border']}; border-radius: 5px; padding: 0px;
            }}
            QPushButton:hover {{ background: {t['primary']}; color: white; border-color: {t['primary']}; }}
        """)
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {t['text_sub']};
                border: 1px solid {t['border']}; border-radius: 5px; padding: 0px;
            }}
            QPushButton:hover {{ background: #ff6b8a; color: white; border-color: #ff6b8a; }}
        """)
        edit_btn.clicked.connect(lambda _, nid=note_id, c=content: self._edit_note(nid, c))
        del_btn.clicked.connect(lambda _, nid=note_id: self._delete_note(nid))

        row.addWidget(content_lbl, 1)
        row.addWidget(edit_btn)
        row.addWidget(del_btn)

        return card

    def _add_note(self):
        content = self.input.toPlainText().strip()
        if not content:
            return
        add_note(str(self._current_date), content)
        self.input.clear()
        self._refresh_cards()
        self.memo_changed.emit()

    def _edit_note(self, note_id: int, content: str):
        dialog = _EditDialog(content, self.theme, self)
        if dialog.exec():
            new_content = dialog.get_text()
            if new_content:
                update_note(note_id, new_content)
                self._refresh_cards()
                self.memo_changed.emit()

    def _delete_note(self, note_id: int):
        delete_note_by_id(note_id)
        self._refresh_cards()
        self.memo_changed.emit()

    def update_theme(self, theme: dict):
        self.theme = theme
        self._apply_style()
        self._refresh_cards()
