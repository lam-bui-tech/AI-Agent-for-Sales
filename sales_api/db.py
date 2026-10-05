import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

DB_PATH = Path(__file__).parent.parent / "data" / "sales.db"

def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Leads Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel TEXT NOT NULL,
        channel_user_id TEXT,
        name TEXT,
        phone TEXT NOT NULL,
        product_skus TEXT,
        budget_vnd INTEGER,
        needs_summary TEXT,
        consent_to_contact BOOLEAN NOT NULL DEFAULT 1,
        status TEXT NOT NULL DEFAULT 'new',
        created_at TEXT NOT NULL
    );
    """)
    
    # 2. Handoff Tickets Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS handoff_tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id TEXT UNIQUE NOT NULL,
        conversation_id TEXT NOT NULL,
        reason TEXT NOT NULL,
        priority TEXT NOT NULL DEFAULT 'medium',
        summary TEXT NOT NULL,
        suggested_next_action TEXT,
        status TEXT NOT NULL DEFAULT 'open',
        created_at TEXT NOT NULL
    );
    """)
    
    # 3. Audit Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tool_name TEXT NOT NULL,
        input_payload TEXT,
        output_payload TEXT,
        execution_time_ms REAL,
        success BOOLEAN NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL
    );
    """)
    
    conn.commit()
    conn.close()

def log_audit(tool_name: str, input_data: Any, output_data: Any, duration_ms: float = 0.0, success: bool = True):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO audit_logs (tool_name, input_payload, output_payload, execution_time_ms, success, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            tool_name,
            json.dumps(input_data, ensure_ascii=False) if not isinstance(input_data, str) else input_data,
            json.dumps(output_data, ensure_ascii=False) if not isinstance(output_data, str) else output_data,
            duration_ms,
            1 if success else 0,
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging audit: {e}")

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)
