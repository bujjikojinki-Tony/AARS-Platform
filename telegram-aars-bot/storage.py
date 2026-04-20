import json
import sqlite3
from pathlib import Path
from typing import Optional, List, Any
from models import ProjectSession


DB_PATH = Path("aars_runtime.db")


class SQLiteStorage:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runtime_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    value TEXT NOT NULL,
                    is_archived INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    # =========================
    # Generic JSON state helpers
    # =========================

    def get_json_state(self, key: str) -> Optional[Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM runtime_state WHERE key = ?",
                (key,)
            ).fetchone()

        if row is None:
            return None
        try:
            return json.loads(row[0])
        except json.JSONDecodeError:
            # Backward compatibility for legacy rows that stored plain strings.
            return row[0]

    def set_json_state(self, key: str, value: Any) -> None:
        payload = json.dumps(value, ensure_ascii=False)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO runtime_state (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, payload),
            )
            conn.commit()

    # =========================
    # Active project helpers
    # =========================

    def get_active_project_id(self) -> Optional[str]:
        value = self.get_json_state("active_project_id")
        return value

    def set_active_project_id(self, project_id: str) -> None:
        self.set_json_state("active_project_id", project_id)

    def clear_active_project_id(self) -> None:
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM runtime_state WHERE key = ?",
                ("active_project_id",)
            )
            conn.commit()

    # =========================
    # Project CRUD
    # =========================

    def save_project(self, session: ProjectSession, is_archived: int = 0) -> None:
        payload = json.dumps(session.to_dict(), ensure_ascii=False)

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO projects (project_id, name, value, is_archived, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(project_id) DO UPDATE SET
                    name = excluded.name,
                    value = excluded.value,
                    is_archived = excluded.is_archived,
                    updated_at = excluded.updated_at
                """,
                (
                    session.project_id,
                    session.name,
                    payload,
                    is_archived,
                    session.updated_at,
                ),
            )
            conn.commit()

    def get_project(self, project_id: str) -> Optional[ProjectSession]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM projects WHERE project_id = ?",
                (project_id,)
            ).fetchone()

        if row is None:
            return None

        data = json.loads(row[0])
        return ProjectSession.from_dict(data)

    def list_projects(self, include_archived: bool = False) -> List[dict]:
        query = """
            SELECT project_id, name, is_archived, updated_at
            FROM projects
        """
        if not include_archived:
            query += " WHERE is_archived = 0"
        query += " ORDER BY updated_at DESC"

        with self._connect() as conn:
            rows = conn.execute(query).fetchall()

        return [
            {
                "project_id": row[0],
                "name": row[1],
                "is_archived": bool(row[2]),
                "updated_at": row[3],
            }
            for row in rows
        ]

    def archive_project(self, project_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE projects SET is_archived = 1 WHERE project_id = ?",
                (project_id,)
            )
            conn.commit()

        active_id = self.get_active_project_id()
        if active_id == project_id:
            self.clear_active_project_id()

    # =========================
    # Compatibility API
    # =========================

    def get_active_session(self) -> Optional[ProjectSession]:
        project_id = self.get_active_project_id()
        if project_id is None:
            return None
        return self.get_project(project_id)

    def save_active_session(self, session: ProjectSession) -> None:
        self.save_project(session, is_archived=0)
        self.set_active_project_id(session.project_id)

    def clear_active_session(self) -> None:
        self.clear_active_project_id()


storage = SQLiteStorage(DB_PATH)
