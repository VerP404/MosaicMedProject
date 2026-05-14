from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


def _default_db_path() -> Path:
    # Отдельная БД для очереди бота (не смешивать со справочником dn_catalog.sqlite)
    env = (os.environ.get("DASH_DN_BOT_TASKS_SQLITE") or "").strip()
    if env:
        return Path(env).resolve()
    # apps/dash_dn/data/
    base = Path(__file__).resolve().parents[1] / "data"
    return (base / "bot_tasks.sqlite").resolve()


def get_db_path() -> Path:
    return _default_db_path()


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    p = (db_path or get_db_path()).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | None = None) -> None:
    with connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bot_task (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              created_at INTEGER NOT NULL,
              created_by TEXT,
              talon_id TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              status TEXT NOT NULL,
              attempt INTEGER NOT NULL DEFAULT 0,
              locked_at INTEGER,
              locked_by TEXT,
              finished_at INTEGER,
              last_error TEXT,
              result_json TEXT,
              artifact_dir TEXT
            );
            """
        )
        # Backward compatible migration: add finished_at if DB was created earlier.
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(bot_task)").fetchall()}
        if "finished_at" not in cols:
            conn.execute("ALTER TABLE bot_task ADD COLUMN finished_at INTEGER;")
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_bot_task_status_created
            ON bot_task(status, created_at);
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS bot_task_event (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              task_id INTEGER NOT NULL,
              ts INTEGER NOT NULL,
              level TEXT NOT NULL,
              message TEXT NOT NULL,
              FOREIGN KEY(task_id) REFERENCES bot_task(id)
            );
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_bot_task_event_task_ts
            ON bot_task_event(task_id, ts);
            """
        )


@dataclass(frozen=True)
class ExpectedService:
    code: str
    begin_date: str
    end_date: str
    qty: str | int | float


@dataclass(frozen=True)
class TaskPayload:
    talon_id: str
    expected_services: list[ExpectedService]
    # MVP: только add/update, не удаляем лишние услуги
    mode: str = "add_update"
    context: dict[str, Any] | None = None

    def to_json(self) -> str:
        d = asdict(self)
        return json.dumps(d, ensure_ascii=False)


def _now_ts() -> int:
    return int(time.time())


def add_event(conn: sqlite3.Connection, task_id: int, level: str, message: str) -> None:
    conn.execute(
        "INSERT INTO bot_task_event(task_id, ts, level, message) VALUES(?, ?, ?, ?)",
        (int(task_id), _now_ts(), str(level), str(message)),
    )


def enqueue_tasks(
    payloads: Iterable[TaskPayload],
    *,
    created_by: str | None = None,
    artifact_dir: str | None = None,
    db_path: Path | None = None,
) -> list[int]:
    ids: list[int] = []
    with connect(db_path) as conn:
        init_db(db_path)
        for p in payloads:
            cur = conn.execute(
                """
                INSERT INTO bot_task(created_at, created_by, talon_id, payload_json, status, artifact_dir)
                VALUES(?, ?, ?, ?, 'queued', ?)
                """,
                (_now_ts(), created_by, str(p.talon_id), p.to_json(), artifact_dir),
            )
            task_id = int(cur.lastrowid)
            add_event(conn, task_id, "info", "queued")
            ids.append(task_id)
        conn.commit()
    return ids


def talons_in_queue(
    talon_ids: Iterable[str],
    *,
    statuses: tuple[str, ...] = ("queued", "running"),
    db_path: Path | None = None,
) -> set[str]:
    """Возвращает множество talon_id, которые уже есть в очереди в указанных статусах."""
    ids = sorted({str(t).strip() for t in talon_ids if str(t).strip()})
    if not ids:
        return set()
    with connect(db_path) as conn:
        init_db(db_path)
        placeholders = ",".join(["?"] * len(ids))
        st_place = ",".join(["?"] * len(statuses))
        rows = conn.execute(
            f"""
            SELECT DISTINCT talon_id
            FROM bot_task
            WHERE talon_id IN ({placeholders})
              AND status IN ({st_place})
            """,
            [*ids, *list(statuses)],
        ).fetchall()
    return {str(r["talon_id"]) for r in rows if r["talon_id"] is not None}


def active_talons(
    *,
    statuses: tuple[str, ...] = ("queued", "running"),
    db_path: Path | None = None,
) -> set[str]:
    """Все talon_id в активных статусах (без IN по списку, быстрее для больших выборок)."""
    with connect(db_path) as conn:
        init_db(db_path)
        st_place = ",".join(["?"] * len(statuses))
        rows = conn.execute(
            f"SELECT DISTINCT talon_id FROM bot_task WHERE status IN ({st_place})",
            list(statuses),
        ).fetchall()
    return {str(r["talon_id"]) for r in rows if r["talon_id"] is not None}


def list_tasks(
    *,
    status: str | None = None,
    limit: int = 200,
    db_path: Path | None = None,
) -> list[dict[str, Any]]:
    with connect(db_path) as conn:
        q = "SELECT * FROM bot_task"
        params: list[Any] = []
        if status:
            q += " WHERE status = ?"
            params.append(status)
        q += " ORDER BY created_at DESC LIMIT ?"
        params.append(int(limit))
        rows = conn.execute(q, params).fetchall()
    return [dict(r) for r in rows]


def claim_next_task(
    *,
    worker_id: str,
    db_path: Path | None = None,
) -> dict[str, Any] | None:
    """Атомарно «захватывает» задачу из очереди.

    SQLite не поддерживает SELECT ... FOR UPDATE, поэтому делаем UPDATE с условием.
    """
    with connect(db_path) as conn:
        init_db(db_path)
        row = conn.execute(
            "SELECT id FROM bot_task WHERE status = 'queued' ORDER BY created_at LIMIT 1"
        ).fetchone()
        if not row:
            return None
        task_id = int(row["id"])
        cur = conn.execute(
            """
            UPDATE bot_task
               SET status = 'running',
                   attempt = attempt + 1,
                   locked_at = ?,
                   locked_by = ?
             WHERE id = ? AND status = 'queued'
            """,
            (_now_ts(), worker_id, task_id),
        )
        if cur.rowcount != 1:
            return None
        add_event(conn, task_id, "info", f"running by {worker_id}")
        conn.commit()
        task = conn.execute("SELECT * FROM bot_task WHERE id = ?", (task_id,)).fetchone()
        return dict(task) if task else None


def mark_task_succeeded(
    task_id: int,
    *,
    result: dict[str, Any] | None = None,
    artifact_dir: str | None = None,
    db_path: Path | None = None,
) -> None:
    with connect(db_path) as conn:
        res_json = json.dumps(result or {}, ensure_ascii=False)
        conn.execute(
            """
            UPDATE bot_task
               SET status = 'succeeded',
                   finished_at = ?,
                   last_error = NULL,
                   result_json = ?,
                   artifact_dir = COALESCE(?, artifact_dir)
             WHERE id = ?
            """,
            (_now_ts(), res_json, artifact_dir, int(task_id)),
        )
        add_event(conn, int(task_id), "info", "succeeded")
        conn.commit()


def mark_task_failed(
    task_id: int,
    *,
    error: str,
    result: dict[str, Any] | None = None,
    artifact_dir: str | None = None,
    db_path: Path | None = None,
) -> None:
    with connect(db_path) as conn:
        res_json = json.dumps(result or {}, ensure_ascii=False)
        conn.execute(
            """
            UPDATE bot_task
               SET status = 'failed',
                   finished_at = ?,
                   last_error = ?,
                   result_json = ?,
                   artifact_dir = COALESCE(?, artifact_dir)
             WHERE id = ?
            """,
            (_now_ts(), str(error), res_json, artifact_dir, int(task_id)),
        )
        add_event(conn, int(task_id), "error", f"failed: {error}")
        conn.commit()


def queue_stats(*, db_path: Path | None = None) -> dict[str, Any]:
    """Короткая статистика по очереди/воркерам для UI."""
    init_db(db_path)
    with connect(db_path) as conn:
        # totals by status
        rows = conn.execute("SELECT status, COUNT(*) AS c FROM bot_task GROUP BY status").fetchall()
        by_status = {str(r["status"]): int(r["c"]) for r in rows}

        # per-worker: completed and avg seconds
        workers = conn.execute(
            """
            SELECT locked_by AS worker,
                   SUM(CASE WHEN status='running' THEN 1 ELSE 0 END) AS running,
                   SUM(CASE WHEN status='queued' THEN 1 ELSE 0 END) AS queued,
                   SUM(CASE WHEN status='succeeded' THEN 1 ELSE 0 END) AS succeeded,
                   SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) AS failed,
                   AVG(CASE
                         WHEN finished_at IS NOT NULL AND locked_at IS NOT NULL AND status IN ('succeeded','failed')
                         THEN (finished_at - locked_at)
                         ELSE NULL
                       END) AS avg_sec
            FROM bot_task
            GROUP BY locked_by
            ORDER BY worker
            """
        ).fetchall()
        per_worker: list[dict[str, Any]] = []
        for r in workers:
            w = (r["worker"] or "").strip() or "(неизвестно)"
            per_worker.append(
                {
                    "worker": w,
                    "running": int(r["running"] or 0),
                    "queued": int(r["queued"] or 0),
                    "succeeded": int(r["succeeded"] or 0),
                    "failed": int(r["failed"] or 0),
                    "avg_sec": float(r["avg_sec"]) if r["avg_sec"] is not None else None,
                }
            )
        return {"by_status": by_status, "per_worker": per_worker}


def cancel_queued(*, db_path: Path | None = None) -> int:
    """Отменяет все queued-задачи (воркер их больше не возьмёт)."""
    with connect(db_path) as conn:
        init_db(db_path)
        cur = conn.execute("UPDATE bot_task SET status = 'cancelled' WHERE status = 'queued'")
        n = int(cur.rowcount or 0)
        if n:
            # Добавим событие только для первых N задач: иначе слишком шумно.
            rows = conn.execute(
                "SELECT id FROM bot_task WHERE status = 'cancelled' ORDER BY created_at DESC LIMIT 50"
            ).fetchall()
            for r in rows:
                add_event(conn, int(r["id"]), "info", "cancelled")
        conn.commit()
        return n


def purge_tasks(*, statuses: list[str] | None = None, db_path: Path | None = None) -> int:
    """Удаляет задачи (и события) из БД. Осторожно: необратимо."""
    with connect(db_path) as conn:
        init_db(db_path)
        if statuses:
            placeholders = ",".join(["?"] * len(statuses))
            ids = [
                int(r["id"])
                for r in conn.execute(
                    f"SELECT id FROM bot_task WHERE status IN ({placeholders})", list(statuses)
                ).fetchall()
            ]
        else:
            ids = [int(r["id"]) for r in conn.execute("SELECT id FROM bot_task").fetchall()]
        if not ids:
            return 0
        placeholders = ",".join(["?"] * len(ids))
        conn.execute(f"DELETE FROM bot_task_event WHERE task_id IN ({placeholders})", ids)
        cur = conn.execute(f"DELETE FROM bot_task WHERE id IN ({placeholders})", ids)
        conn.commit()
        return int(cur.rowcount or 0)


def requeue_stuck_running(*, older_than_seconds: int = 300, db_path: Path | None = None) -> int:
    """Возвращает зависшие running задачи обратно в queued (разлочивает).

    Критерий "зависла": locked_at старше чем now - older_than_seconds.
    """
    cutoff = _now_ts() - int(older_than_seconds)
    with connect(db_path) as conn:
        init_db(db_path)
        rows = conn.execute(
            """
            SELECT id FROM bot_task
             WHERE status = 'running'
               AND locked_at IS NOT NULL
               AND locked_at < ?
            """,
            (cutoff,),
        ).fetchall()
        ids = [int(r["id"]) for r in rows]
        if not ids:
            return 0
        placeholders = ",".join(["?"] * len(ids))
        conn.execute(
            f"""
            UPDATE bot_task
               SET status='queued',
                   locked_at=NULL,
                   locked_by=NULL,
                   last_error=NULL
             WHERE id IN ({placeholders})
            """,
            ids,
        )
        for tid in ids[:50]:
            add_event(conn, tid, "warning", "requeued stuck running")
        conn.commit()
        return len(ids)

