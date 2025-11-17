import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any

DB_PATH = Path("data/audit.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        step_index INTEGER NOT NULL,
        name TEXT,
        tool TEXT,
        input_json TEXT,
        output_json TEXT,
        duration REAL,
        created_at TEXT
    )
    """)
    conn.commit()
    conn.close()

def save_audit_step(run_id, step_index, name, tool, input_obj, output_obj, duration, created_at):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO audit_steps (run_id, step_index, name, tool, input_json, output_json, duration, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_id,
        step_index,
        name,
        tool,
        json.dumps(input_obj),
        json.dumps(output_obj),
        duration,
        created_at
    ))
    conn.commit()
    conn.close()

def get_trace(run_id):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM audit_steps WHERE run_id = ? ORDER BY step_index", (run_id,))
    rows = cur.fetchall()
    conn.close()
    output = []
    for r in rows:
        output.append({
            "step_index": r["step_index"],
            "name": r["name"],
            "tool": r["tool"],
            "input": json.loads(r["input_json"]),
            "output": json.loads(r["output_json"]),
            "duration": r["duration"],
            "created_at": r["created_at"]
        })
    return output

def list_runs(limit=20):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT run_id, MAX(created_at) as last_at, MAX(step_index) as steps FROM audit_steps GROUP BY run_id ORDER BY last_at DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return [{"run_id": r["run_id"], "last_at": r["last_at"], "steps": r["steps"]} for r in rows]

init_db()
