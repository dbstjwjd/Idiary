import sys
import sqlite3
import json
from contextlib import contextmanager
from pathlib import Path


def _user_data_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent


DB_PATH = _user_data_dir() / "diary.db"


@contextmanager
def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with _get_conn() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS categories (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name  TEXT    NOT NULL,
            color TEXT    DEFAULT '#009CA6'
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS todos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            is_done     INTEGER DEFAULT 0,
            category_id INTEGER,
            alarm_time  TEXT,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS memo (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            date    TEXT    NOT NULL UNIQUE,
            content TEXT
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS notes (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            date    TEXT    NOT NULL,
            content TEXT    NOT NULL
        )''')
        conn.execute("CREATE INDEX IF NOT EXISTS idx_notes_date ON notes(date)")
        # 기존 memo 데이터 마이그레이션 (최초 1회)
        if conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0] == 0:
            rows = conn.execute(
                "SELECT date, content FROM memo WHERE content IS NOT NULL AND content != ''"
            ).fetchall()
            if rows:
                conn.executemany("INSERT INTO notes (date, content) VALUES (?, ?)", rows)
        conn.execute('''CREATE TABLE IF NOT EXISTS ddays (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            target_date TEXT    NOT NULL
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS reminders (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            title   TEXT    NOT NULL,
            time    TEXT    NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1
        )''')
        conn.execute("CREATE INDEX IF NOT EXISTS idx_todos_date     ON todos(date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_memo_date      ON memo(date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ddays_date     ON ddays(target_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_reminders_time ON reminders(time)")


def get_todo_stats(year: int, month: int) -> tuple:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*), SUM(is_done) FROM todos WHERE date LIKE ?",
            (f"{year}-{month:02d}-%",),
        ).fetchone()
    return (row[0] or 0, row[1] or 0)


def get_todo_stats_range(start: str, end: str) -> tuple:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*), SUM(is_done) FROM todos WHERE date BETWEEN ? AND ?",
            (start, end),
        ).fetchone()
    return (row[0] or 0, row[1] or 0)


def get_ddays() -> list:
    with _get_conn() as conn:
        return conn.execute(
            "SELECT id, name, target_date FROM ddays ORDER BY target_date"
        ).fetchall()


def add_dday(name: str, target_date: str):
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO ddays (name, target_date) VALUES (?, ?)", (name, target_date)
        )


def delete_dday(did: int):
    with _get_conn() as conn:
        conn.execute("DELETE FROM ddays WHERE id = ?", (did,))


def update_dday(did: int, name: str, target_date: str):
    with _get_conn() as conn:
        conn.execute("UPDATE ddays SET name = ?, target_date = ? WHERE id = ?", (name, target_date, did))


def get_memos_for_month(year: int, month: int) -> dict:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT date FROM notes WHERE date LIKE ?",
            (f"{year}-{month:02d}-%",),
        ).fetchall()
    return {row[0]: True for row in rows}


def get_notes_for_date(date_str: str) -> list:
    with _get_conn() as conn:
        return conn.execute(
            "SELECT id, content FROM notes WHERE date = ? ORDER BY id",
            (date_str,),
        ).fetchall()


def add_note(date_str: str, content: str):
    with _get_conn() as conn:
        conn.execute("INSERT INTO notes (date, content) VALUES (?, ?)", (date_str, content))


def update_note(note_id: int, content: str):
    with _get_conn() as conn:
        conn.execute("UPDATE notes SET content = ? WHERE id = ?", (content, note_id))


def delete_note_by_id(note_id: int):
    with _get_conn() as conn:
        conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))


def get_memo(date_str: str) -> str:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT content FROM memo WHERE date = ?", (date_str,)
        ).fetchone()
    return row[0] if row else ""


def save_memo(date_str: str, content: str):
    with _get_conn() as conn:
        conn.execute(
            """INSERT INTO memo (date, content) VALUES (?, ?)
               ON CONFLICT(date) DO UPDATE SET content = excluded.content""",
            (date_str, content),
        )


def delete_memo(date_str: str):
    with _get_conn() as conn:
        conn.execute("DELETE FROM memo WHERE date = ?", (date_str,))


def get_todos_for_date(date_str: str) -> list:
    with _get_conn() as conn:
        return conn.execute(
            "SELECT id, title, date, is_done FROM todos WHERE date = ? ORDER BY is_done, id",
            (date_str,),
        ).fetchall()


def add_todo(title: str, date_str: str):
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO todos (title, date) VALUES (?, ?)", (title, date_str)
        )


def toggle_todo(todo_id: int):
    with _get_conn() as conn:
        conn.execute(
            "UPDATE todos SET is_done = CASE WHEN is_done = 0 THEN 1 ELSE 0 END WHERE id = ?",
            (todo_id,),
        )


def delete_todo(todo_id: int):
    with _get_conn() as conn:
        conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))


def get_reminders() -> list:
    with _get_conn() as conn:
        return conn.execute(
            "SELECT id, title, time, enabled FROM reminders ORDER BY time"
        ).fetchall()


def add_reminder(title: str, time: str):
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO reminders (title, time) VALUES (?, ?)", (title, time)
        )


def delete_reminder(rid: int):
    with _get_conn() as conn:
        conn.execute("DELETE FROM reminders WHERE id = ?", (rid,))


def update_reminder(rid: int, title: str, time: str):
    with _get_conn() as conn:
        conn.execute("UPDATE reminders SET title = ?, time = ? WHERE id = ?", (title, time, rid))


def toggle_reminder(rid: int):
    with _get_conn() as conn:
        conn.execute(
            "UPDATE reminders SET enabled = 1 - enabled WHERE id = ?", (rid,)
        )


def export_data() -> dict:
    with _get_conn() as conn:
        todos = conn.execute("SELECT title, date, is_done FROM todos").fetchall()
        notes = conn.execute("SELECT date, content FROM notes").fetchall()
        ddays = conn.execute("SELECT name, target_date FROM ddays").fetchall()
        reminders = conn.execute("SELECT title, time, enabled FROM reminders").fetchall()
    return {
        "todos":     [{"title": r[0], "date": r[1], "is_done": r[2]} for r in todos],
        "notes":     [{"date": r[0], "content": r[1]} for r in notes],
        "ddays":     [{"name": r[0], "target_date": r[1]} for r in ddays],
        "reminders": [{"title": r[0], "time": r[1], "enabled": r[2]} for r in reminders],
    }


def import_data(data: dict):
    with _get_conn() as conn:
        conn.execute("DELETE FROM todos")
        conn.execute("DELETE FROM notes")
        conn.execute("DELETE FROM ddays")
        conn.execute("DELETE FROM reminders")
        conn.executemany(
            "INSERT INTO todos (title, date, is_done) VALUES (?, ?, ?)",
            [(r["title"], r["date"], r["is_done"]) for r in data.get("todos", [])],
        )
        conn.executemany(
            "INSERT INTO notes (date, content) VALUES (?, ?)",
            [(r["date"], r["content"]) for r in data.get("notes", [])],
        )
        conn.executemany(
            "INSERT INTO ddays (name, target_date) VALUES (?, ?)",
            [(r["name"], r["target_date"]) for r in data.get("ddays", [])],
        )
        conn.executemany(
            "INSERT INTO reminders (title, time, enabled) VALUES (?, ?, ?)",
            [(r["title"], r["time"], r["enabled"]) for r in data.get("reminders", [])],
        )


if __name__ == "__main__":
    init_db()
    print("DB 초기화 완료!")
