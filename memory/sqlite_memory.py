import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class SQLiteMemory:
    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    title TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    timestamp TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS automations (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    trigger TEXT NOT NULL,
                    action TEXT NOT NULL,
                    schedule TEXT,
                    enabled INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    result TEXT
                )
            """)
            conn.commit()

    def create_conversation(self, title: Optional[str] = None) -> dict:
        conv_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO conversations (id, timestamp, title, created_at) VALUES (?, ?, ?, ?)",
                (conv_id, timestamp, title, timestamp),
            )
            conn.commit()
        return {"id": conv_id, "title": title, "timestamp": timestamp, "created_at": timestamp}

    def get_conversation(self, conv_id: str) -> Optional[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,)).fetchone()
            return dict(row) if row else None

    def get_conversations(self, limit: int = 50) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM conversations ORDER BY timestamp DESC LIMIT ?", (limit,)
            ).fetchall()
            convs = []
            for row in rows:
                conv = dict(row)
                count = conn.execute(
                    "SELECT COUNT(*) FROM messages WHERE conversation_id = ?", (row["id"],)
                ).fetchone()[0]
                conv["message_count"] = count
                first_user = conn.execute(
                    "SELECT content FROM messages WHERE conversation_id = ? AND role = 'user' ORDER BY timestamp ASC LIMIT 1",
                    (row["id"],),
                ).fetchone()
                conv["preview"] = (first_user[0] if first_user else "")[:80]
                convs.append(conv)
            return convs

    def rename_conversation(self, conv_id: str, title: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE conversations SET title = ? WHERE id = ?", (title, conv_id))
            conn.commit()

    def auto_title_conversation(self, conv_id: str, first_user_message: str) -> None:
        title = first_user_message.strip().replace("\n", " ")
        if len(title) > 48:
            title = title[:48].rstrip() + "..."
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE conversations SET title = COALESCE(title, ?) WHERE id = ?", (title, conv_id))
            conn.commit()

    def delete_conversation(self, conv_id: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
            conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
            conn.commit()

    def add_message(self, conv_id: str, role: str, content: str) -> str:
        msg_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO messages (id, conversation_id, timestamp, role, content) VALUES (?, ?, ?, ?, ?)",
                (msg_id, conv_id, timestamp, role, content),
            )
            conn.commit()
        return msg_id

    def get_history(self, conv_id: str, limit: int = 200) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC LIMIT ?",
                (conv_id, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def clear_history(self, conv_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
            conn.commit()

    def remember(self, content: str, category: str = "general", key_override: str = "") -> dict:
        mem_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        key = key_override if key_override else content[:64]
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO memories (id, key, value, category, timestamp) VALUES (?, ?, ?, ?, ?)",
                (mem_id, key, content, category, timestamp),
            )
            conn.commit()
        return {"id": mem_id, "key": key, "value": content, "category": category}

    def forget(self, query: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM memories WHERE value LIKE ? OR key LIKE ?", (f"%{query}%", f"%{query}%"))
            conn.commit()
            return cursor.rowcount

    def forget_matching(self, query: str) -> int:
        return self.forget(query)

    def update_memory(self, memory_id: str, value: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("UPDATE memories SET value = ? WHERE id = ?", (value, memory_id))
            conn.commit()
            return cursor.rowcount > 0

    def clear_all_memories(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM memories")
            conn.commit()
            return cursor.rowcount

    def recall(self, query: str = "") -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if query:
                rows = conn.execute(
                    "SELECT * FROM memories WHERE value LIKE ? OR key LIKE ? ORDER BY timestamp DESC",
                    (f"%{query}%", f"%{query}%"),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM memories ORDER BY timestamp DESC").fetchall()
            return [dict(row) for row in rows]

    def set_setting(self, key: str, value: str):
        timestamp = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                (key, value, timestamp),
            )
            conn.commit()

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
            return row[0] if row else default

    def get_all_settings(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT key, value FROM settings").fetchall()
            return {row["key"]: row["value"] for row in rows}

    def add_automation(self, automation: dict) -> str:
        automation_id = str(uuid.uuid4())
        automation["id"] = automation_id
        automation["created_at"] = datetime.utcnow().isoformat()
        automation["updated_at"] = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO automations (id, name, trigger, action, schedule, enabled, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    automation_id,
                    automation.get("name", ""),
                    automation.get("trigger", ""),
                    automation.get("action", ""),
                    automation.get("schedule", ""),
                    automation.get("enabled", True),
                    automation["created_at"],
                    automation["updated_at"],
                ),
            )
            conn.commit()
        return automation_id

    def get_automations(self) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM automations ORDER BY created_at DESC").fetchall()
            return [dict(row) for row in rows]

    def update_automation(self, automation_id: str, updates: dict):
        updates["updated_at"] = datetime.utcnow().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [automation_id]
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"UPDATE automations SET {set_clause} WHERE id = ?", values)
            conn.commit()

    def delete_automation(self, automation_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM automations WHERE id = ?", (automation_id,))
            conn.commit()

    def add_task(self, task: dict) -> str:
        task_id = str(uuid.uuid4())
        task["id"] = task_id
        task["created_at"] = datetime.utcnow().isoformat()
        task["updated_at"] = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO tasks (id, description, status, created_at, updated_at, result) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    task_id,
                    task.get("description", ""),
                    task.get("status", "pending"),
                    task["created_at"],
                    task["updated_at"],
                    task.get("result"),
                ),
            )
            conn.commit()
        return task_id

    def get_tasks(self, status: Optional[str] = None) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if status:
                rows = conn.execute(
                    "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC",
                    (status,),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
            return [dict(row) for row in rows]

    def update_task(self, task_id: str, status: str, result: Optional[str] = None):
        timestamp = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE tasks SET status = ?, updated_at = ?, result = ? WHERE id = ?",
                (status, timestamp, result, task_id),
            )
            conn.commit()


from memory.store import MemoryStore  # noqa: E402

MemoryStore.register(SQLiteMemory)
