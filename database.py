"""database.py — SQLite persistence for the AI Email Auto-Responder.
Author: Avatar Putra Sigit | GitHub: qurrrrsebastian-prog
"""
import os
import sqlite3
from datetime import datetime
from typing import List, Optional

import pandas as pd

DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")

DEFAULT_TEMPLATES = [
    ("Quotation Follow-up", "Terima kasih atas ketertarikan Anda. Terlampir "
     "penawaran kami. Kami siap menjadwalkan survei lokasi kapan saja."),
    ("Site Visit Offer", "Untuk memberikan estimasi yang akurat, kami "
     "menawarkan survei lokasi gratis. Mohon informasikan waktu yang sesuai."),
]


def get_connection() -> sqlite3.Connection:
    """Return a SQLite connection with row access by name."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables and seed default reply templates."""
    conn = get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS email_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT,
            sender_email TEXT, subject TEXT, incoming_email TEXT,
            analysis_json TEXT, tone_used TEXT, context_used TEXT, draft_reply TEXT);
        CREATE TABLE IF NOT EXISTS context_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT, profile_name TEXT UNIQUE,
            context_text TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS reply_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, body TEXT);
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, user TEXT,
            action TEXT, details TEXT);
        """
    )
    for name, body in DEFAULT_TEMPLATES:
        conn.execute("INSERT OR IGNORE INTO reply_templates (name, body) VALUES (?, ?)",
                     (name, body))
    conn.commit()
    conn.close()


def add_log(action: str, details: str = "", user: str = "anonymous") -> None:
    """Append an entry to the audit log."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO audit_log (timestamp, user, action, details) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(timespec="seconds"), user, action, details),
    )
    conn.commit()
    conn.close()


# --------------------------------------------------------------------------- #
# Email sessions
# --------------------------------------------------------------------------- #
def add_session(sender_email: str, subject: str, incoming_email: str,
                analysis_json: str, tone_used: str, context_used: str,
                draft_reply: str) -> int:
    """Persist a processed email session and return its id."""
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO email_sessions
           (timestamp, sender_email, subject, incoming_email, analysis_json,
            tone_used, context_used, draft_reply)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (datetime.now().isoformat(timespec="seconds"), sender_email, subject,
         incoming_email, analysis_json, tone_used, context_used, draft_reply),
    )
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid


def get_sessions(limit: int = 300) -> pd.DataFrame:
    """Return email sessions, newest first."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM email_sessions ORDER BY id DESC LIMIT ?", conn, params=[limit])
    conn.close()
    return df


def clear_sessions() -> None:
    """Delete all email sessions."""
    conn = get_connection()
    conn.execute("DELETE FROM email_sessions")
    conn.commit()
    conn.close()


# --------------------------------------------------------------------------- #
# Context profiles
# --------------------------------------------------------------------------- #
def get_context_profiles() -> List[dict]:
    """Return all custom context profiles."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM context_profiles ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_context_profile(name: str, text: str) -> None:
    """Insert or update a context profile by name."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO context_profiles (profile_name, context_text, created_at)
           VALUES (?, ?, ?)
           ON CONFLICT(profile_name) DO UPDATE SET context_text=excluded.context_text""",
        (name, text, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()


def delete_context_profile(profile_id: int) -> None:
    """Delete a context profile by id."""
    conn = get_connection()
    conn.execute("DELETE FROM context_profiles WHERE id = ?", (profile_id,))
    conn.commit()
    conn.close()


# --------------------------------------------------------------------------- #
# Reply templates
# --------------------------------------------------------------------------- #
def get_templates() -> List[dict]:
    """Return all reply templates."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM reply_templates ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_template(name: str, body: str) -> None:
    """Insert or update a reply template by name."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO reply_templates (name, body) VALUES (?, ?)
           ON CONFLICT(name) DO UPDATE SET body=excluded.body""",
        (name, body),
    )
    conn.commit()
    conn.close()


def delete_template(template_id: int) -> None:
    """Delete a reply template by id."""
    conn = get_connection()
    conn.execute("DELETE FROM reply_templates WHERE id = ?", (template_id,))
    conn.commit()
    conn.close()
