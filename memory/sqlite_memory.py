import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from memory.audit import MemoryAuditLog
from memory.types import MemoryImportance, MemorySource, MemoryStatus, MemoryType, normalize_memory_type


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
                    updated_at TEXT NOT NULL,
                    importance REAL DEFAULT 0.5,
                    access_count INTEGER DEFAULT 0,
                    tags TEXT NOT NULL DEFAULT '[]',
                    related_ids TEXT NOT NULL DEFAULT '[]',
                    memory_type TEXT DEFAULT 'fact',
                    decay_factor REAL DEFAULT 1.0
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
                CREATE TABLE IF NOT EXISTS session_memories (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    memory_type TEXT DEFAULT 'fact',
                    importance REAL DEFAULT 0.5,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    expires_at TEXT
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
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflows (
                    workflow_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    trigger TEXT NOT NULL DEFAULT '{}',
                    steps TEXT NOT NULL DEFAULT '[]',
                    variables TEXT NOT NULL DEFAULT '{}',
                    permissions TEXT NOT NULL DEFAULT '{}',
                    status TEXT NOT NULL DEFAULT 'draft',
                    enabled INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_run TEXT,
                    next_run TEXT,
                    tags TEXT NOT NULL DEFAULT '[]',
                    project TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflow_runs (
                    run_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'running',
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    duration_seconds REAL DEFAULT 0.0,
                    steps TEXT NOT NULL DEFAULT '[]',
                    errors TEXT NOT NULL DEFAULT '[]',
                    result TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflow_approvals (
                    approval_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    step_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    arguments TEXT NOT NULL DEFAULT '{}',
                    risk_level TEXT NOT NULL DEFAULT 'medium',
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    resolved_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflow_versions (
                    version_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    definition TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workflow_audit (
                    audit_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    run_id TEXT,
                    event TEXT NOT NULL,
                    detail TEXT NOT NULL DEFAULT '{}',
                    timestamp TEXT NOT NULL
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
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )
            """)
            row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
            current = row[0] if row and row[0] is not None else 0
            if current < 1:
                conn.execute("INSERT INTO schema_version (version, applied_at) VALUES (?, ?)", (1, datetime.utcnow().isoformat()))
            conn.commit()
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
            if "importance" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN importance REAL DEFAULT 0.5")
            if "access_count" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN access_count INTEGER DEFAULT 0")
            if "tags" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN tags TEXT NOT NULL DEFAULT '[]'")
            if "related_ids" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN related_ids TEXT NOT NULL DEFAULT '[]'")
            if "memory_type" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN memory_type TEXT DEFAULT 'fact'")
            if "decay_factor" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN decay_factor REAL DEFAULT 1.0")
            if "privacy_level" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN privacy_level TEXT DEFAULT 'normal'")
            if "is_pinned" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN is_pinned INTEGER DEFAULT 0")
            if "trust_level" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN trust_level TEXT DEFAULT 'normal'")
            if "quality_score" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN quality_score REAL DEFAULT 0.5")
            if "previous_value" not in columns:
                conn.execute("ALTER TABLE memories ADD COLUMN previous_value TEXT")
            conn.commit()

        conn.execute("""
            CREATE TABLE IF NOT EXISTS ideas (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                tags TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'idea',
                project TEXT DEFAULT '',
                profile TEXT DEFAULT 'jarvis',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS error_memories (
                id TEXT PRIMARY KEY,
                error_signature TEXT NOT NULL,
                resolution TEXT NOT NULL,
                category TEXT DEFAULT 'other',
                project TEXT DEFAULT '',
                profile TEXT DEFAULT 'jarvis',
                confidence REAL DEFAULT 1.0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ideas_status ON ideas(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ideas_project ON ideas(project)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_error_memories_signature ON error_memories(error_signature)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_error_memories_project ON error_memories(project)")
        conn.commit()

        task_columns = {row[1] for row in conn.execute("PRAGMA table_info(tasks)").fetchall()}
        for col, col_type in [
            ("task_type", "TEXT DEFAULT 'general'"),
            ("complexity", "TEXT DEFAULT 'moderate'"),
            ("priority", "TEXT DEFAULT 'normal'"),
            ("agent", "TEXT DEFAULT ''"),
            ("skill", "TEXT DEFAULT ''"),
            ("project", "TEXT DEFAULT ''"),
            ("dependencies", "TEXT NOT NULL DEFAULT '[]'"),
            ("progress", "REAL DEFAULT 0.0"),
            ("error", "TEXT DEFAULT ''"),
            ("retry_count", "INTEGER DEFAULT 0"),
            ("max_retries", "INTEGER DEFAULT 3"),
            ("requires_approval", "INTEGER DEFAULT 0"),
            ("risk_level", "TEXT DEFAULT 'medium'"),
            ("metadata", "TEXT DEFAULT '{}'"),
            ("started_at", "TEXT"),
            ("completed_at", "TEXT"),
            ("elapsed_seconds", "REAL DEFAULT 0.0"),
            ("pid", "INTEGER"),
            ("checkpoints", "TEXT NOT NULL DEFAULT '[]'"),
            ("logs", "TEXT NOT NULL DEFAULT '[]'"),
            ("artifacts", "TEXT NOT NULL DEFAULT '[]'"),
            ("parent_task_id", "TEXT DEFAULT ''"),
        ]:
            if col not in task_columns:
                conn.execute(f"ALTER TABLE tasks ADD COLUMN {col} {col_type}")
        conn.commit()

    def remember_session(self, session_id: str, content: str, category: str = "general", memory_type: str = "fact", importance: float = 0.5, expires_at: str | None = None) -> dict:
        mem_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO session_memories (id, session_id, content, category, memory_type, importance, created_at, updated_at, expires_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (mem_id, session_id, content, category, memory_type, importance, timestamp, timestamp, expires_at),
            )
            conn.commit()
        return {"id": mem_id, "session_id": session_id, "content": content, "category": category, "memory_type": memory_type, "importance": importance, "created_at": timestamp, "expires_at": expires_at}

    def get_session_memories(self, session_id: str, limit: int = 50) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM session_memories WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def delete_session_memory(self, memory_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM session_memories WHERE id = ?", (memory_id,))
            conn.commit()
            return cursor.rowcount > 0

    def clear_session_memories(self, session_id: str) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM session_memories WHERE session_id = ?", (session_id,))
            conn.commit()
            return cursor.rowcount

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

    def remember(self, content: str, category: str = "general", key_override: str = "", confidence: float = 1.0, source: str = "explicit_user", project: str = "", profile: str = "jarvis", expires_at: str | None = None, importance: float = 0.5, tags: list[str] | None = None, memory_type: str = "fact", related_ids: list[str] | None = None, privacy_level: str = "normal", is_pinned: bool = False, trust_level: str = "normal", quality_score: float = 0.5, previous_value: str | None = None) -> dict:
        mem_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        key = key_override if key_override else content[:64]
        tags_json = json.dumps(tags or [])
        related_json = json.dumps(related_ids or [])
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO memories (id, key, value, category, timestamp, confidence, source, project, profile, expires_at, last_used_at, created_at, updated_at, importance, access_count, tags, related_ids, memory_type, decay_factor, privacy_level, is_pinned, trust_level, quality_score, previous_value) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (mem_id, key, content, category, timestamp, confidence, source, project, profile, expires_at, timestamp, timestamp, timestamp, importance, 0, tags_json, related_json, memory_type, 1.0, privacy_level, 1 if is_pinned else 0, trust_level, quality_score, previous_value),
            )
            conn.commit()
        return {"id": mem_id, "key": key, "value": content, "category": category, "confidence": confidence, "source": source, "project": project, "profile": profile, "expires_at": expires_at, "timestamp": timestamp, "created_at": timestamp, "updated_at": timestamp, "importance": importance, "access_count": 0, "tags": tags or [], "related_ids": related_ids or [], "memory_type": memory_type, "decay_factor": 1.0, "privacy_level": privacy_level, "is_pinned": is_pinned, "trust_level": trust_level, "quality_score": quality_score, "previous_value": previous_value}

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
                existing = self.get_memory_by_id(memory_id)
                prev_value = existing.get("value") if existing else None
                cursor = conn.execute(
                    "UPDATE memories SET value = ?, updated_at = ?, previous_value = ? WHERE id = ?",
                    (value, timestamp, prev_value, memory_id),
                )
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
            return [self._parse_memory_row(row) for row in rows]

    def get_memory_by_id(self, memory_id: str) -> dict | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
            if not row:
                return None
            return self._parse_memory_row(row)

    def _parse_memory_row(self, row) -> dict:
        data = dict(row)
        for key in ("tags", "related_ids"):
            value = data.get(key)
            if isinstance(value, str):
                try:
                    data[key] = json.loads(value)
                except Exception:
                    data[key] = []
        if "is_pinned" in data and isinstance(data["is_pinned"], int):
            data["is_pinned"] = bool(data["is_pinned"])
        return data

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

    def increment_access(self, memory_id: str) -> None:
        timestamp = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE memories SET access_count = access_count + 1, last_used_at = ? WHERE id = ?",
                (timestamp, memory_id),
            )
            conn.commit()

    def update_memory_fields(self, memory_id: str, updates: dict) -> dict | None:
        allowed = {"value", "confidence", "source", "project", "profile", "importance", "tags", "related_ids", "memory_type", "decay_factor", "expires_at", "privacy_level", "is_pinned", "trust_level", "quality_score"}
        filtered = {k: v for k, v in updates.items() if k in allowed}
        if not filtered:
            return self.get_memory_by_id(memory_id)
        filtered["updated_at"] = datetime.utcnow().isoformat()
        if "tags" in filtered and isinstance(filtered["tags"], list):
            filtered["tags"] = json.dumps(filtered["tags"])
        if "related_ids" in filtered and isinstance(filtered["related_ids"], list):
            filtered["related_ids"] = json.dumps(filtered["related_ids"])
        set_clause = ", ".join(f"{k} = ?" for k in filtered)
        values = list(filtered.values()) + [memory_id]
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"UPDATE memories SET {set_clause} WHERE id = ?", values)
            conn.commit()
        return self.get_memory_by_id(memory_id)

    def search_with_ranking(self, query: str = "", category: str | None = None, project: str | None = None, profile: str | None = None, min_confidence: float = 0.0, limit: int = 50) -> list[dict]:
        rows = self.recall(query=query, category=category, project=project, profile=profile, min_confidence=min_confidence, limit=limit * 3)
        now = datetime.utcnow().timestamp()
        scored = []
        for row in rows:
            score = 0.0
            if row.get("confidence"):
                score += float(row["confidence"]) * 0.3
            if row.get("importance"):
                score += float(row["importance"]) * 0.3
            access = row.get("access_count", 0) or 0
            score += min(access / 10.0, 1.0) * 0.2
            try:
                created = datetime.fromisoformat(row.get("created_at", "")).timestamp()
                age_hours = (now - created) / 3600.0
                recency = max(0.0, 1.0 - (age_hours / (24.0 * 30)))
                score += recency * 0.2
            except Exception:
                score += 0.1
            decay = float(row.get("decay_factor", 1.0) or 1.0)
            score *= decay
            row["_score"] = score
            scored.append(row)
        scored.sort(key=lambda r: r.get("_score", 0.0), reverse=True)
        return scored[:limit]

    def get_memories_for_context(self, query: str, project: str | None = None, profile: str | None = None, limit: int = 8) -> list[dict]:
        return self.search_with_ranking(query=query, project=project, profile=profile, limit=limit, min_confidence=0.3)

    def detect_duplicates(self, threshold: float = 0.85) -> list[dict]:
        rows = self.recall(limit=200)
        duplicates = []
        seen = {}
        for row in rows:
            text = (row.get("value") or "").strip().lower()
            if not text:
                continue
            for existing_text, existing_ids in seen.items():
                similarity = self._string_similarity(text, existing_text)
                if similarity >= threshold:
                    duplicates.append({
                        "existing_id": existing_ids[0],
                        "candidate_id": row["id"],
                        "similarity": similarity,
                        "existing_text": existing_text,
                        "candidate_text": text,
                    })
                    break
            else:
                seen.setdefault(text, []).append(row["id"])
        return duplicates

    def detect_contradictions(self) -> list[dict]:
        contradictions = []
        pref_rows = self.recall(category="preferences", limit=200)
        by_key: dict[str, list[dict]] = {}
        for row in pref_rows:
            key = (row.get("key") or "").strip().lower()
            if not key:
                continue
            by_key.setdefault(key, []).append(row)
        for key, items in by_key.items():
            if len(items) < 2:
                continue
            values = [it.get("value", "").strip().lower() for it in items if it.get("value")]
            unique = list(dict.fromkeys(values))
            if len(unique) > 1:
                contradictions.append({
                    "key": key,
                    "values": unique,
                    "memory_ids": [it["id"] for it in items],
                })
        return contradictions

    def apply_decay(self, decay_rate: float = 0.01) -> int:
        now = datetime.utcnow().timestamp()
        rows = self.recall(limit=1000)
        updated = 0
        for row in rows:
            try:
                created = datetime.fromisoformat(row.get("created_at", "")).timestamp()
                age_days = (now - created) / 86400.0
                current = float(row.get("decay_factor", 1.0) or 1.0)
                new_decay = max(0.1, current - (decay_rate * age_days))
                if abs(new_decay - current) > 0.001:
                    self.update_memory_fields(row["id"], {"decay_factor": new_decay})
                    updated += 1
            except Exception:
                continue
        return updated

    def get_health(self) -> dict:
        stats = self.get_memory_stats()
        try:
            duplicates = self.detect_duplicates()
        except Exception:
            duplicates = []
        try:
            contradictions = self.detect_contradictions()
        except Exception:
            contradictions = []
        low_confidence = 0
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT COUNT(*) FROM memories WHERE confidence < 0.5").fetchone()
            low_confidence = row[0] if row else 0
        return {
            "total_memories": stats.get("count", 0),
            "storage_bytes": stats.get("size_bytes", 0),
            "duplicates": len(duplicates),
            "contradictions": len(contradictions),
            "low_confidence": low_confidence,
            "vector_enabled": getattr(self, "_vector_enabled", False),
        }

    def export_memories(self, category: str | None = None, project: str | None = None, profile: str | None = None) -> dict:
        rows = self.recall(category=category, project=project, profile=profile, limit=10000)
        return {
            "exported_at": datetime.utcnow().isoformat(),
            "count": len(rows),
            "memories": rows,
        }

    def import_memories(self, data: dict, mode: str = "merge") -> dict:
        if not isinstance(data, dict) or "memories" not in data:
            raise ValueError("Invalid import format")
        memories = data.get("memories", [])
        imported = 0
        skipped = 0
        for mem in memories:
            if not isinstance(mem, dict) or not mem.get("value"):
                skipped += 1
                continue
            if mode == "overwrite":
                self.remember(
                    mem.get("value", ""),
                    category=mem.get("category", "general"),
                    key_override=mem.get("key", ""),
                    confidence=mem.get("confidence", 1.0),
                    source=mem.get("source", "explicit_user"),
                    project=mem.get("project", ""),
                    profile=mem.get("profile", "jarvis"),
                    importance=mem.get("importance", 0.5),
                    tags=mem.get("tags", []),
                    memory_type=mem.get("memory_type", "fact"),
                    related_ids=mem.get("related_ids", []),
                )
                imported += 1
            elif mode == "merge":
                existing = self.recall(mem.get("value", ""), category=mem.get("category"), project=mem.get("project"), profile=mem.get("profile"), limit=1)
                if existing:
                    skipped += 1
                else:
                    self.remember(
                        mem.get("value", ""),
                        category=mem.get("category", "general"),
                        key_override=mem.get("key", ""),
                        confidence=mem.get("confidence", 1.0),
                        source=mem.get("source", "explicit_user"),
                        project=mem.get("project", ""),
                        profile=mem.get("profile", "jarvis"),
                        importance=mem.get("importance", 0.5),
                        tags=mem.get("tags", []),
                        memory_type=mem.get("memory_type", "fact"),
                        related_ids=mem.get("related_ids", []),
                    )
                    imported += 1
            else:
                skipped += 1
        return {"imported": imported, "skipped": skipped}

    def get_related_memories(self, memory_id: str, limit: int = 10) -> list[dict]:
        mem = self.get_memory_by_id(memory_id)
        if not mem:
            return []
        related_ids = mem.get("related_ids", []) or []
        related = []
        for rid in related_ids[:limit]:
            row = self.get_memory_by_id(rid)
            if row:
                related.append(row)
        project = mem.get("project")
        category = mem.get("category")
        profile = mem.get("profile")
        query = mem.get("value", "")[:32]
        if len(related) < limit:
            for row in self.recall(query=query, category=category, project=project, profile=profile, limit=limit - len(related)):
                if row["id"] != memory_id and row["id"] not in [r["id"] for r in related]:
                    related.append(row)
        return related[:limit]

    def _string_similarity(self, a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        set_a = set(a.split())
        set_b = set(b.split())
        if not set_a or not set_b:
            return 0.0
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / len(union)

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
                """
                INSERT INTO tasks (
                    id, description, status, created_at, updated_at, result,
                    task_type, complexity, priority, agent, skill, project,
                    dependencies, progress, error, retry_count, max_retries,
                    requires_approval, risk_level, metadata, started_at, completed_at,
                    elapsed_seconds, pid, checkpoints, logs, artifacts, parent_task_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    task.get("description", ""),
                    task.get("status", "pending"),
                    task["created_at"],
                    task["updated_at"],
                    task.get("result"),
                    task.get("task_type", "general"),
                    task.get("complexity", "moderate"),
                    task.get("priority", "normal"),
                    task.get("agent", ""),
                    task.get("skill", ""),
                    task.get("project", ""),
                    json.dumps(task.get("dependencies", [])),
                    task.get("progress", 0.0),
                    task.get("error", ""),
                    task.get("retry_count", 0),
                    task.get("max_retries", 3),
                    1 if task.get("requires_approval") else 0,
                    task.get("risk_level", "medium"),
                    json.dumps(task.get("metadata", {})),
                    task.get("started_at"),
                    task.get("completed_at"),
                    task.get("elapsed_seconds", 0.0),
                    task.get("pid"),
                    json.dumps(task.get("checkpoints", [])),
                    json.dumps(task.get("logs", [])),
                    json.dumps(task.get("artifacts", [])),
                    task.get("parent_task_id", ""),
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
            return [self._parse_task_row(row) for row in rows]

    def _parse_task_row(self, row) -> dict:
        data = dict(row)
        for key in ("dependencies", "metadata", "checkpoints", "logs", "artifacts"):
            value = data.get(key)
            if isinstance(value, str):
                try:
                    data[key] = json.loads(value)
                except Exception:
                    data[key] = [] if key != "metadata" else {}
        for key in ("requires_approval",):
            if key in data:
                data[key] = bool(data[key])
        return data

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

    # ---------------------------------------------------------------- workflows
    def add_workflow(self, workflow: dict) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO workflows (
                    workflow_id, name, description, trigger, steps, variables,
                    permissions, status, enabled, created_at, updated_at,
                    last_run, next_run, tags, project
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    workflow.get("workflow_id", str(uuid.uuid4())[:8]),
                    workflow.get("name", ""),
                    workflow.get("description", ""),
                    json.dumps(workflow.get("trigger", {})),
                    json.dumps(workflow.get("steps", [])),
                    json.dumps(workflow.get("variables", {})),
                    json.dumps(workflow.get("permissions", {})),
                    workflow.get("status", "draft"),
                    1 if workflow.get("enabled") else 0,
                    workflow.get("created_at", datetime.utcnow().isoformat()),
                    workflow.get("updated_at", datetime.utcnow().isoformat()),
                    workflow.get("last_run"),
                    workflow.get("next_run"),
                    json.dumps(workflow.get("tags", [])),
                    workflow.get("project"),
                ),
            )
            conn.commit()
        return workflow

    def get_workflow(self, workflow_id: str) -> dict | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM workflows WHERE workflow_id = ?", (workflow_id,)).fetchone()
            if not row:
                return None
            data = dict(row)
            for key in ("trigger", "steps", "variables", "permissions", "tags"):
                value = data.get(key)
                if isinstance(value, str):
                    try:
                        data[key] = json.loads(value)
                    except Exception:
                        data[key] = [] if key == "steps" else {} if key in ("trigger", "variables", "permissions") else []
            data["enabled"] = bool(data.get("enabled", 0))
            return data

    def get_workflows(self, status: str | None = None, limit: int = 50) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if status:
                rows = conn.execute(
                    "SELECT * FROM workflows WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM workflows ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            results = []
            for row in rows:
                data = dict(row)
                for key in ("trigger", "steps", "variables", "permissions", "tags"):
                    value = data.get(key)
                    if isinstance(value, str):
                        try:
                            data[key] = json.loads(value)
                        except Exception:
                            data[key] = [] if key == "steps" else {} if key in ("trigger", "variables", "permissions") else []
                data["enabled"] = bool(data.get("enabled", 0))
                results.append(data)
            return results

    def update_workflow(self, workflow_id: str, updates: dict) -> dict | None:
        existing = self.get_workflow(workflow_id)
        if not existing:
            return None
        updates["updated_at"] = datetime.utcnow().isoformat()
        allowed = {
            "name", "description", "trigger", "steps", "variables",
            "permissions", "status", "enabled", "last_run", "next_run",
            "tags", "project",
        }
        set_clause = ", ".join(f"{k} = ?" for k in updates if k in allowed)
        values = []
        for key in allowed:
            if key in updates:
                value = updates[key]
                if key in ("trigger", "steps", "variables", "permissions", "tags"):
                    value = json.dumps(value)
                elif key == "enabled":
                    value = 1 if value else 0
                values.append(value)
        values.append(workflow_id)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(f"UPDATE workflows SET {set_clause} WHERE workflow_id = ?", values)
            conn.commit()
        return self.get_workflow(workflow_id)

    def delete_workflow(self, workflow_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM workflows WHERE workflow_id = ?", (workflow_id,))
            conn.commit()
            return cursor.rowcount > 0

    def add_workflow_run(self, run: dict) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO workflow_runs (run_id, workflow_id, status, started_at, finished_at, duration_seconds, steps, errors, result)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.get("run_id", str(uuid.uuid4())[:8]),
                    run.get("workflow_id", ""),
                    run.get("status", "running"),
                    run.get("started_at", datetime.utcnow().isoformat()),
                    run.get("finished_at"),
                    run.get("duration_seconds", 0.0),
                    json.dumps(run.get("steps", [])),
                    json.dumps(run.get("errors", [])),
                    json.dumps(run.get("result")) if run.get("result") is not None else None,
                ),
            )
            conn.commit()
        return run

    def get_workflow_runs(self, workflow_id: str, limit: int = 50) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM workflow_runs WHERE workflow_id = ? ORDER BY started_at DESC LIMIT ?",
                (workflow_id, limit),
            ).fetchall()
            results = []
            for row in rows:
                data = dict(row)
                for key in ("steps", "errors", "result"):
                    value = data.get(key)
                    if isinstance(value, str):
                        try:
                            data[key] = json.loads(value)
                        except Exception:
                            data[key] = [] if key in ("steps", "errors") else None
                results.append(data)
            return results

    def add_workflow_approval(self, approval: dict) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO workflow_approvals (approval_id, workflow_id, run_id, step_id, action, arguments, risk_level, status, created_at, resolved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    approval.get("approval_id", str(uuid.uuid4())[:8]),
                    approval.get("workflow_id", ""),
                    approval.get("run_id", ""),
                    approval.get("step_id", ""),
                    approval.get("action", ""),
                    json.dumps(approval.get("arguments", {})),
                    approval.get("risk_level", "medium"),
                    approval.get("status", "pending"),
                    approval.get("created_at", datetime.utcnow().isoformat()),
                    approval.get("resolved_at"),
                ),
            )
            conn.commit()
        return approval

    def get_workflow_approvals(self, status: str | None = None) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if status:
                rows = conn.execute(
                    "SELECT * FROM workflow_approvals WHERE status = ? ORDER BY created_at DESC",
                    (status,),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM workflow_approvals ORDER BY created_at DESC").fetchall()
            results = []
            for row in rows:
                data = dict(row)
                value = data.get("arguments")
                if isinstance(value, str):
                    try:
                        data["arguments"] = json.loads(value)
                    except Exception:
                        data["arguments"] = {}
                results.append(data)
            return results

    def update_workflow_approval(self, approval_id: str, updates: dict) -> dict | None:
        updates["resolved_at"] = datetime.utcnow().isoformat()
        allowed = {"status", "resolved_at"}
        set_clause = ", ".join(f"{k} = ?" for k in updates if k in allowed)
        values = [updates[k] for k in allowed if k in updates]
        values.append(approval_id)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(f"UPDATE workflow_approvals SET {set_clause} WHERE approval_id = ?", values)
            conn.commit()
            if cursor.rowcount == 0:
                return None
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM workflow_approvals WHERE approval_id = ?", (approval_id,)).fetchone()
            if not row:
                return None
            data = dict(row)
            value = data.get("arguments")
            if isinstance(value, str):
                try:
                    data["arguments"] = json.loads(value)
                except Exception:
                    data["arguments"] = {}
            return data

    def add_workflow_audit(self, workflow_id: str, event: str, detail: dict | None = None, run_id: str | None = None) -> dict:
        audit_id = str(uuid.uuid4())[:8]
        timestamp = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO workflow_audit (audit_id, workflow_id, run_id, event, detail, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                (audit_id, workflow_id, run_id, event, json.dumps(detail or {}), timestamp),
            )
            conn.commit()
        return {"audit_id": audit_id, "event": event, "timestamp": timestamp}

    def get_workflow_audit(self, workflow_id: str | None = None, limit: int = 100) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if workflow_id:
                rows = conn.execute(
                    "SELECT * FROM workflow_audit WHERE workflow_id = ? ORDER BY timestamp DESC LIMIT ?",
                    (workflow_id, limit),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM workflow_audit ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
            results = []
            for row in rows:
                data = dict(row)
                value = data.get("detail")
                if isinstance(value, str):
                    try:
                        data["detail"] = json.loads(value)
                    except Exception:
                        data["detail"] = {}
                results.append(data)
            return results

    # ---------------------------------------------------------------- ideas
    def add_idea(self, title: str, description: str = "", tags: list[str] | None = None, status: str = "idea", project: str = "", profile: str = "jarvis") -> dict:
        idea_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO ideas (id, title, description, tags, status, project, profile, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (idea_id, title, description, json.dumps(tags or []), status, project, profile, timestamp, timestamp),
            )
            conn.commit()
        return {"id": idea_id, "title": title, "description": description, "tags": tags or [], "status": status, "project": project, "profile": profile, "created_at": timestamp, "updated_at": timestamp}

    def get_ideas(self, status: str | None = None, project: str | None = None, profile: str | None = None, limit: int = 50) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            sql = "SELECT * FROM ideas WHERE 1=1"
            params = []
            if status:
                sql += " AND status = ?"
                params.append(status)
            if project:
                sql += " AND project = ?"
                params.append(project)
            if profile:
                sql += " AND profile = ?"
                params.append(profile)
            sql += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
            results = []
            for row in rows:
                data = dict(row)
                if isinstance(data.get("tags"), str):
                    try:
                        data["tags"] = json.loads(data["tags"])
                    except Exception:
                        data["tags"] = []
                results.append(data)
            return results

    def update_idea(self, idea_id: str, updates: dict) -> dict | None:
        timestamp = datetime.utcnow().isoformat()
        allowed = {"title", "description", "tags", "status", "project", "profile"}
        filtered = {k: v for k, v in updates.items() if k in allowed}
        if not filtered:
            return self.get_idea(idea_id)
        if "tags" in filtered and isinstance(filtered["tags"], list):
            filtered["tags"] = json.dumps(filtered["tags"])
        filtered["updated_at"] = timestamp
        set_clause = ", ".join(f"{k} = ?" for k in filtered)
        values = list(filtered.values()) + [idea_id]
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(f"UPDATE ideas SET {set_clause} WHERE id = ?", values)
            conn.commit()
            if cursor.rowcount == 0:
                return None
        return self.get_idea(idea_id)

    def get_idea(self, idea_id: str) -> dict | None:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM ideas WHERE id = ?", (idea_id,)).fetchone()
            if not row:
                return None
            data = dict(row)
            if isinstance(data.get("tags"), str):
                try:
                    data["tags"] = json.loads(data["tags"])
                except Exception:
                    data["tags"] = []
            return data

    def delete_idea(self, idea_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM ideas WHERE id = ?", (idea_id,))
            conn.commit()
            return cursor.rowcount > 0

    # ---------------------------------------------------------------- error memories
    def add_error_memory(self, error_signature: str, resolution: str, category: str = "other", project: str = "", profile: str = "jarvis", confidence: float = 1.0) -> dict:
        error_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO error_memories (id, error_signature, resolution, category, project, profile, confidence, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (error_id, error_signature, resolution, category, project, profile, confidence, timestamp, timestamp),
            )
            conn.commit()
        return {"id": error_id, "error_signature": error_signature, "resolution": resolution, "category": category, "project": project, "profile": profile, "confidence": confidence, "created_at": timestamp, "updated_at": timestamp}

    def get_error_memories(self, project: str | None = None, category: str | None = None, profile: str | None = None, limit: int = 50) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            sql = "SELECT * FROM error_memories WHERE 1=1"
            params = []
            if project:
                sql += " AND project = ?"
                params.append(project)
            if category:
                sql += " AND category = ?"
                params.append(category)
            if profile:
                sql += " AND profile = ?"
                params.append(profile)
            sql += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

    def search_error_memories(self, error_signature: str, limit: int = 10) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM error_memories WHERE error_signature LIKE ? ORDER BY created_at DESC LIMIT ?",
                (f"%{error_signature}%", limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def delete_error_memory(self, error_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM error_memories WHERE id = ?", (error_id,))
            conn.commit()
            return cursor.rowcount > 0


from memory.store import MemoryStore  # noqa: E402

MemoryStore.register(SQLiteMemory)
