import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.config import get_settings

log = logging.getLogger("app.history")

_initialised = False


def _connect() -> sqlite3.Connection:
    global _initialised
    settings = get_settings()
    Path(settings.history_db).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.history_db)
    if not _initialised:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS turns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                sources TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
        _initialised = True
    return conn


def new_session() -> str:
    return uuid.uuid4().hex


def save_turn(session_id: str, question: str, answer: str, sources: list[dict]) -> None:
    conn = _connect()
    conn.execute(
        "INSERT INTO turns (session_id, question, answer, sources, created_at) VALUES (?, ?, ?, ?, ?)",
        (session_id, question, answer, json.dumps(sources), datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


def get_turns(session_id: str) -> list[dict]:
    conn = _connect()
    rows = conn.execute(
        "SELECT question, answer, created_at FROM turns WHERE session_id = ? ORDER BY id",
        (session_id,),
    ).fetchall()
    conn.close()
    return [{"question": q, "answer": a, "created_at": ts} for q, a, ts in rows]
