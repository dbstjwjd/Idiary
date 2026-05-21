from datetime import date, timedelta
from PyQt6.QtWidgets import QLayout


def clear_layout(layout: QLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()


def week_start_of(d: date) -> date:
    return d - timedelta(days=d.weekday())
