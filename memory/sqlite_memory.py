import sqlite3
import uuid
from datetime import datetime
from pathlib import Path


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
                    timestamp TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    source TEXT DEFAULT 'explicit_user',
                    project TEXT DEFAULT '',
                    profile TEXT DEFAULT 'jarvis',
                    expires_at TEXT,
                    last_used_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_summaries (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    message_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    due_at TEXT NOT NULL,
                    repeat TEXT DEFAULT 'once',
                    enabled INTEGER DEFAULT 1,
                    notified INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_feedback (
                    id TEXT PRIMARY KEY,
                    memory_id TEXT,
                    conversation_id TEXT,
                    feedback TEXT NOT NULL,
                    reason TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS privacy_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
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
        self._migrate()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_project ON memories(project)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_profile ON memories(profile)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_timestamp ON memories(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_summaries_conversation ON conversation_summaries(conversation_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reminders_due ON reminders(due_at)")
            conn.commit()

    def _migrate(self):
        with sqlite3.connect(self.db_path) as conn:
            columns = {row[1] for row in conn.execute("PRAGMA table_info(memories)").fetchall()}
            if "confidence" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN confidence REAL DEFAULT 1.0")
            if "source" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN source TEXT DEFAULT 'explicit_user'")
            if "project" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN project TEXT DEFAULT ''")
            if "profile" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN profile TEXT DEFAULT 'jarvis'")
            if "expires_at" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN expires_at TEXT")
            if "last_used_at" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN last_used_at TEXT")
            if "created_at" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN created_at TEXT NOT NULL DEFAULT ''")
            if "updated_at" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''")
            conn.commit()

    def create_conversation(self, title: str | None = None) -> dict:
        conv_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO conversations (id, timestamp, title, created_at) VALUES (?, ?, ?, ?)",
                (conv_id, timestamp, title, timestamp),
            )
            conn.commit()
        return {"id": conv_id, "title": title, "timestamp": timestamp, "created_at": timestamp}

    def get_conversation(self, conv_id: str) -> dict | None:
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

    def remember(self, content: str, category: str = "general", key_override: str = "", confidence: float = 1.0, source: str = "explicit_user", project: str = "", profile: str = "jarvis", expires_at: str | None = None) -> dict:
        mem_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        key = key_override if key_override else content[:64]
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO memories (id, key, value, category, timestamp, confidence, source, project, profile, expires_at, last_used_at, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (mem_id, key, content, category, timestamp, confidence, source, project, profile, expires_at, timestamp, timestamp, timestamp),
            )
            conn.commit()
        return {"id": mem_id, "key": key, "value": content, "category": category, "confidence": confidence, "source": source, "project": project, "profile": profile, "expires_at": expires_at, "timestamp": timestamp, "created_at": timestamp, "updated_at": timestamp}

    def forget(self, query: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM memories WHERE value LIKE ? OR key LIKE ?", (f"%{query}%", f"%{query}%"))
            conn.commit()
            return cursor.rowcount

    def forget_matching(self, query: str) -> int:
        return self.forget(query)

    def update_memory(self, memory_id: str, value: str, confidence: float | None = None, source: str | None = None) -> bool:
        timestamp = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            if confidence is not None or source is not None:
                existing = self.get_memory_by_id(memory_id)
                if existing:
                    new_confidence = confidence if confidence is not None else existing.get("confidence", 1.0)
                    new_source = source if source is not None else existing.get("source", "explicit_user")
                    cursor = conn.execute(
                        "UPDATE memories SET value = ?, confidence = ?, source = ?, updated_at = ? WHERE id = ?",
                        (value, new_confidence, new_source, timestamp, memory_id),
                    )
                else:
                    return False
            else:
                cursor = conn.execute("UPDATE memories SET value = ?, updated_at = ? WHERE id = ?", (value, timestamp, memory_id))
            conn.commit()
            return cursor.rowcount > 0

    def clear_all_memories(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM memories")
            conn.commit()
            return cursor.rowcount

    def recall(self, query: str = "", category: str | None = None, project: str | None = None, profile: str | None = None, min_confidence: float = 0.0, limit: int = 50) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            sql = "SELECT * FROM memories WHERE 1=1"
            params = []
            if query:
                sql += " AND (value LIKE ? OR key LIKE ?)"
                params.extend([f"%{query}%", f"%{query}%"])
            if category:
                sql += " AND category = ?"
                params.append(category)
            if project:
                sql += " AND project = ?"
                params.append(project)
            if profile:
                sql += " AND profile = ?"
                params.append(profile)
            if min_confidence > 0:
                sql += " AND confidence >= ?"
                params.append(min_confidence)
            sql += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

    def get_memory_by_id(self, memory_id: str) -> dict | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
            return dict(row) if row else None

    def delete_memory_by_id(self, memory_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_memory_stats(self) -> dict:
        count = 0
        size_bytes = 0
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT COUNT(*) FROM memories").fetchone()
            count = row[0] if row else 0
        path = Path(self.db_path)
        if path.exists():
            size_bytes = path.stat().st_size
        return {
            "count": count,
            "storage": str(path),
            "size_bytes": size_bytes,
        }

    def set_setting(self, key: str, value: str):
        timestamp = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                (key, value, timestamp),
            )
            conn.commit()

    def get_setting(self, key: str, default: str | None = None) -> str | None:
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
        set_clause = ", ".join(f"{k} = ?" for k in updates)
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

    def get_tasks(self, status: str | None = None) -> list[dict]:
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

    def update_task(self, task_id: str, status: str, result: str | None = None):
        timestamp = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE tasks SET status = ?, updated_at = ?, result = ? WHERE id = ?",
                (status, timestamp, result, task_id),
            )
            conn.commit()

    # ---------------------------------------------------------------- conversation summaries
    def add_conversation_summary(self, conversation_id: str, summary: str, message_count: int = 0) -> dict:
        summary_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO conversation_summaries (id, conversation_id, summary, message_count, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (summary_id, conversation_id, summary, message_count, timestamp, timestamp),
            )
            conn.commit()
        return {"id": summary_id, "conversation_id": conversation_id, "summary": summary, "message_count": message_count, "created_at": timestamp}

    def get_conversation_summaries(self, conversation_id: str | None = None, limit: int = 50) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if conversation_id:
                rows = conn.execute(
                    "SELECT * FROM conversation_summaries WHERE conversation_id = ? ORDER BY created_at DESC LIMIT ?",
                    (conversation_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM conversation_summaries ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(row) for row in rows]

    def update_conversation_summary(self, summary_id: str, summary: str) -> bool:
        timestamp = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE conversation_summaries SET summary = ?, updated_at = ? WHERE id = ?",
                (summary, timestamp, summary_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_conversation_summary(self, summary_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM conversation_summaries WHERE id = ?", (summary_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ---------------------------------------------------------------- reminders
    def add_reminder(self, title: str, description: str = "", due_at: str = "", repeat: str = "once") -> dict:
        reminder_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO reminders (id, title, description, due_at, repeat, enabled, notified, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (reminder_id, title, description, due_at, repeat, 1, 0, timestamp, timestamp),
            )
            conn.commit()
        return {"id": reminder_id, "title": title, "description": description, "due_at": due_at, "repeat": repeat, "enabled": True, "notified": False, "created_at": timestamp}

    def get_reminders(self, enabled: bool | None = None) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if enabled is not None:
                rows = conn.execute(
                    "SELECT * FROM reminders WHERE enabled = ? ORDER BY due_at ASC",
                    (1 if enabled else 0,),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM reminders ORDER BY due_at ASC").fetchall()
            return [dict(row) for row in rows]

    def update_reminder(self, reminder_id: str, updates: dict) -> bool:
        updates["updated_at"] = datetime.utcnow().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [reminder_id]
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(f"UPDATE reminders SET {set_clause} WHERE id = ?", values)
            conn.commit()
            return cursor.rowcount > 0

    def delete_reminder(self, reminder_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ---------------------------------------------------------------- memory feedback
    def add_memory_feedback(self, memory_id: str | None, conversation_id: str | None, feedback: str, reason: str = "") -> dict:
        feedback_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO memory_feedback (id, memory_id, conversation_id, feedback, reason, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (feedback_id, memory_id, conversation_id, feedback, reason, timestamp),
            )
            conn.commit()
        return {"id": feedback_id, "memory_id": memory_id, "conversation_id": conversation_id, "feedback": feedback, "reason": reason, "created_at": timestamp}

    def get_memory_feedback(self, memory_id: str | None = None, limit: int = 50) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if memory_id:
                rows = conn.execute(
                    "SELECT * FROM memory_feedback WHERE memory_id = ? ORDER BY created_at DESC LIMIT ?",
                    (memory_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM memory_feedback ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(row) for row in rows]

    # ---------------------------------------------------------------- privacy settings
    def set_privacy_setting(self, key: str, value: str):
        timestamp = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO privacy_settings (key, value, updated_at) VALUES (?, ?, ?)",
                (key, value, timestamp),
            )
            conn.commit()

    def get_privacy_setting(self, key: str, default: str | None = None) -> str | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT value FROM privacy_settings WHERE key = ?", (key,)).fetchone()
            return row[0] if row else default

    def get_all_privacy_settings(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT key, value FROM privacy_settings").fetchall()
            return {row["key"]: row["value"] for row in rows}


from memory.store import MemoryStore  # noqa: E402

MemoryStore.register(SQLiteMemory)
