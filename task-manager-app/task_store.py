from __future__ import annotations

import sqlite3
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

STATUSES = ("todo", "in_progress", "done")
PRIORITIES = ("low", "medium", "high")


@contextmanager
def _connection(database_path: str | Path) -> Iterator[sqlite3.Connection]:
    with closing(sqlite3.connect(str(database_path), timeout=5)) as connection:
        connection.row_factory = sqlite3.Row
        with connection:
            yield connection


def initialize_database(database_path: str | Path) -> None:
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    with _connection(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL CHECK(length(trim(title)) BETWEEN 1 AND 200),
                description TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL CHECK(status IN ('todo', 'in_progress', 'done')),
                priority TEXT NOT NULL CHECK(priority IN ('low', 'medium', 'high')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


def create_task(
    database_path: str | Path,
    *,
    title: str,
    description: str,
    status: str,
    priority: str,
) -> int:
    now = _utc_now()
    with _connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO tasks (title, description, status, priority, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, description, status, priority, now, now),
        )
        return int(cursor.lastrowid)


def get_task(database_path: str | Path, task_id: int) -> dict[str, int | str] | None:
    with _connection(database_path) as connection:
        row = connection.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
        return dict(row) if row is not None else None


def list_tasks(
    database_path: str | Path,
    *,
    status: str | None = None,
    priority: str | None = None,
) -> list[dict[str, int | str]]:
    conditions: list[str] = []
    values: list[str] = []
    if status is not None:
        conditions.append("status = ?")
        values.append(status)
    if priority is not None:
        conditions.append("priority = ?")
        values.append(priority)

    query = "SELECT * FROM tasks"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY created_at DESC, id DESC"

    with _connection(database_path) as connection:
        rows = connection.execute(query, values).fetchall()
        return [dict(row) for row in rows]


def update_task(
    database_path: str | Path,
    task_id: int,
    *,
    title: str,
    description: str,
    status: str,
    priority: str,
) -> bool:
    with _connection(database_path) as connection:
        cursor = connection.execute(
            """
            UPDATE tasks
            SET title = ?, description = ?, status = ?, priority = ?, updated_at = ?
            WHERE id = ?
            """,
            (title, description, status, priority, _utc_now(), task_id),
        )
        return cursor.rowcount == 1


def delete_task(database_path: str | Path, task_id: int) -> bool:
    with _connection(database_path) as connection:
        cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return cursor.rowcount == 1


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")
