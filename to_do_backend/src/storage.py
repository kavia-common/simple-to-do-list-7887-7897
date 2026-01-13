"""
SQLite persistence layer for the To-Do app.

We intentionally use Python's built-in sqlite3 to avoid adding extra dependencies.
The database file is stored inside the backend container folder, and is created
automatically on startup.

Schema:
  tasks(id INTEGER PK, title TEXT, description TEXT, completed INTEGER, created_at TEXT, updated_at TEXT)
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Generator, List, Optional


def _utc_now_iso() -> str:
    """Return current UTC time in ISO-8601 format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _db_path() -> str:
    """
    Compute the on-disk SQLite DB path.

    We place the DB in the container root (to_do_backend/) so it persists for the
    running container lifecycle and is easy to locate.
    """
    # src/storage.py -> src -> to_do_backend
    backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(backend_root, "todo.db")


@contextmanager
def _get_conn() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for SQLite connection with dict row factory."""
    conn = sqlite3.connect(_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
        conn.commit()
    finally:
        conn.close()


# PUBLIC_INTERFACE
def init_db() -> None:
    """Initialize the SQLite database schema if it doesn't already exist."""
    with _get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_completed ON tasks(completed)")


def _row_to_task(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert a sqlite3.Row to the task JSON shape used by the API."""
    return {
        "id": int(row["id"]),
        "title": row["title"],
        "description": row["description"] or "",
        "completed": bool(row["completed"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


# PUBLIC_INTERFACE
def list_tasks() -> List[Dict[str, Any]]:
    """Return all tasks ordered newest-first."""
    with _get_conn() as conn:
        rows = conn.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
        return [_row_to_task(r) for r in rows]


# PUBLIC_INTERFACE
def get_task(task_id: int) -> Optional[Dict[str, Any]]:
    """Return a task by id, or None if not found."""
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return _row_to_task(row) if row else None


# PUBLIC_INTERFACE
def create_task(title: str, description: str = "") -> Dict[str, Any]:
    """Create a task and return it."""
    now = _utc_now_iso()
    with _get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO tasks(title, description, completed, created_at, updated_at)
            VALUES (?, ?, 0, ?, ?)
            """,
            (title, description or "", now, now),
        )
        task_id = int(cur.lastrowid)
    task = get_task(task_id)
    # task can't be None here; DB just inserted it.
    return task or {
        "id": task_id,
        "title": title,
        "description": description or "",
        "completed": False,
        "created_at": now,
        "updated_at": now,
    }


# PUBLIC_INTERFACE
def update_task(
    task_id: int,
    *,
    title: Optional[str] = None,
    description: Optional[str] = None,
    completed: Optional[bool] = None,
) -> Optional[Dict[str, Any]]:
    """Update fields on a task. Returns updated task or None if not found."""
    existing = get_task(task_id)
    if not existing:
        return None

    new_title = title if title is not None else existing["title"]
    new_description = description if description is not None else existing["description"]
    new_completed = completed if completed is not None else existing["completed"]

    now = _utc_now_iso()
    with _get_conn() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET title = ?, description = ?, completed = ?, updated_at = ?
            WHERE id = ?
            """,
            (new_title, new_description or "", 1 if new_completed else 0, now, task_id),
        )
    return get_task(task_id)


# PUBLIC_INTERFACE
def delete_task(task_id: int) -> bool:
    """Delete a task. Returns True if deleted, False if not found."""
    with _get_conn() as conn:
        cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return cur.rowcount > 0
