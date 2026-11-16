"""CMMS user accounts, sessions, and role/menu access."""

from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "incident_log.db"

_lock = threading.RLock()

ROLES = ("administrator", "operator")

MENU_OPTIONS: tuple[tuple[str, str], ...] = (
    ("dashboard", "Dashboard"),
    ("assets", "Manajemen Asset"),
    ("wo", "Work Order"),
    ("pm", "Jadwal PM"),
    ("team", "Tim Teknisi"),
    ("statistik", "Statistik"),
    ("report", "Laporan"),
    ("notify", "Setting Notifikasi"),
    ("users", "User Management"),
)

MENU_KEYS = tuple(k for k, _ in MENU_OPTIONS)
ALL_MENUS = list(MENU_KEYS)
OPERATOR_MENU_KEYS = tuple(k for k in MENU_KEYS if k != "users")

SESSION_DAYS = 7
SESSION_COOKIE = "cmms_session"
PBKDF2_ROUNDS = 120_000


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _normalize_text(value: Any, *, max_len: int = 120) -> str:
    return str(value or "").strip()[:max_len]


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ROUNDS,
    )
    return f"pbkdf2_sha256${PBKDF2_ROUNDS}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, rounds_s, salt, digest_hex = str(stored or "").split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        rounds = int(rounds_s)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            rounds,
        )
        return secrets.compare_digest(digest.hex(), digest_hex)
    except (TypeError, ValueError):
        return False


def _normalize_role(value: Any) -> str:
    role = str(value or "").strip().lower()
    if role in {"admin", "administrator"}:
        return "administrator"
    if role == "operator":
        return "operator"
    raise ValueError("role harus administrator atau operator")


def _normalize_menus(value: Any, *, role: str) -> list[str]:
    if role == "administrator":
        return list(ALL_MENUS)
    if value is None:
        items: list[Any] = []
    elif isinstance(value, str):
        text = value.strip()
        if text.startswith("["):
            try:
                parsed = json.loads(text)
                items = list(parsed) if isinstance(parsed, list) else []
            except json.JSONDecodeError:
                items = [p.strip() for p in text.replace(";", ",").split(",")]
        else:
            items = [p.strip() for p in text.replace(";", ",").split(",")]
    elif isinstance(value, (list, tuple, set)):
        items = list(value)
    else:
        items = []
    out: list[str] = []
    for item in items:
        key = str(item or "").strip()
        if key in OPERATOR_MENU_KEYS and key not in out:
            out.append(key)
    if not out:
        raise ValueError("pilih minimal satu menu untuk operator")
    return out


def init_auth_db() -> None:
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    full_name TEXT DEFAULT '',
                    role TEXT NOT NULL DEFAULT 'operator',
                    menus TEXT NOT NULL DEFAULT '[]',
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    token TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)"
            )
            conn.commit()

            row = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()
            if int(row["c"] if row else 0) == 0:
                stamp = datetime.now().isoformat(timespec="seconds")
                conn.execute(
                    """
                    INSERT INTO users (
                        id, username, password_hash, full_name, role, menus,
                        active, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
                    """,
                    (
                        uuid.uuid4().hex,
                        "admin",
                        hash_password("admin1234"),
                        "Administrator",
                        "administrator",
                        json.dumps(ALL_MENUS, ensure_ascii=False),
                        stamp,
                        stamp,
                    ),
                )
                conn.commit()
        finally:
            conn.close()


def _row_to_user(row: sqlite3.Row, *, include_sensitive: bool = False) -> dict[str, Any]:
    role = row["role"] or "operator"
    try:
        menus = json.loads(row["menus"] or "[]")
        if not isinstance(menus, list):
            menus = []
    except json.JSONDecodeError:
        menus = []
    if role == "administrator":
        menus = list(ALL_MENUS)
    else:
        menus = [m for m in menus if m in OPERATOR_MENU_KEYS]
    data = {
        "id": row["id"],
        "username": row["username"],
        "full_name": row["full_name"] or "",
        "role": role,
        "menus": menus,
        "active": bool(row["active"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
    if include_sensitive:
        data["password_hash"] = row["password_hash"]
    return data


def public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user["id"],
        "username": user["username"],
        "full_name": user.get("full_name") or "",
        "role": user["role"],
        "menus": list(user.get("menus") or []),
        "active": bool(user.get("active", True)),
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at"),
    }


def list_users() -> list[dict[str, Any]]:
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT * FROM users ORDER BY username COLLATE NOCASE ASC"
            ).fetchall()
        finally:
            conn.close()
    return [public_user(_row_to_user(r)) for r in rows]


def get_user(user_id: str) -> dict[str, Any] | None:
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()
        finally:
            conn.close()
    return _row_to_user(row) if row else None


def get_user_by_username(username: str) -> dict[str, Any] | None:
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ? COLLATE NOCASE",
                (_normalize_text(username, max_len=80),),
            ).fetchone()
        finally:
            conn.close()
    return _row_to_user(row, include_sensitive=True) if row else None


def _count_active_admins(*, exclude_id: str | None = None) -> int:
    with _lock:
        conn = _connect()
        try:
            if exclude_id:
                row = conn.execute(
                    """
                    SELECT COUNT(*) AS c FROM users
                    WHERE role = 'administrator' AND active = 1 AND id != ?
                    """,
                    (exclude_id,),
                ).fetchone()
            else:
                row = conn.execute(
                    """
                    SELECT COUNT(*) AS c FROM users
                    WHERE role = 'administrator' AND active = 1
                    """
                ).fetchone()
        finally:
            conn.close()
    return int(row["c"] if row else 0)


def upsert_user(
    payload: dict[str, Any], *, user_id: str | None = None
) -> dict[str, Any]:
    current = get_user(user_id) if user_id else None
    if user_id and not current:
        raise ValueError("user tidak ditemukan")

    new_id = user_id or uuid.uuid4().hex
    username = _normalize_text(
        payload.get("username") if "username" in payload or not current else current["username"],
        max_len=80,
    ).lower()
    if not username:
        raise ValueError("username wajib diisi")
    if " " in username:
        raise ValueError("username tidak boleh mengandung spasi")

    existing = get_user_by_username(username)
    if existing and existing["id"] != new_id:
        raise ValueError("username sudah dipakai")

    full_name = _normalize_text(
        payload.get("full_name")
        if "full_name" in payload or not current
        else current.get("full_name"),
        max_len=120,
    )
    role = _normalize_role(
        payload.get("role") if "role" in payload or not current else current["role"]
    )
    if "menus" in payload or not current or role != current.get("role"):
        menus = _normalize_menus(payload.get("menus"), role=role)
    else:
        menus = _normalize_menus(current.get("menus"), role=role)

    active = bool(current.get("active", True)) if current else True
    if "active" in payload:
        active = bool(payload.get("active"))

    if current and current["role"] == "administrator" and (
        role != "administrator" or not active
    ):
        if _count_active_admins(exclude_id=new_id) < 1:
            raise ValueError("harus ada minimal satu administrator aktif")

    password = str(payload.get("password") or "")
    if not current:
        if len(password) < 6:
            raise ValueError("password minimal 6 karakter")
        password_hash = hash_password(password)
    elif password.strip():
        if len(password) < 6:
            raise ValueError("password minimal 6 karakter")
        password_hash = hash_password(password)
    else:
        # keep existing hash
        raw = get_user_by_username(current["username"])
        password_hash = (raw or {}).get("password_hash") or ""
        if not password_hash:
            raise ValueError("password wajib diisi")

    stamp = datetime.now().isoformat(timespec="seconds")
    created_at = (current or {}).get("created_at") or stamp
    menus_json = json.dumps(menus, ensure_ascii=False)

    with _lock:
        conn = _connect()
        try:
            conn.execute(
                """
                INSERT INTO users (
                    id, username, password_hash, full_name, role, menus,
                    active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    username = excluded.username,
                    password_hash = excluded.password_hash,
                    full_name = excluded.full_name,
                    role = excluded.role,
                    menus = excluded.menus,
                    active = excluded.active,
                    updated_at = excluded.updated_at
                """,
                (
                    new_id,
                    username,
                    password_hash,
                    full_name,
                    role,
                    menus_json,
                    1 if active else 0,
                    created_at,
                    stamp,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    user = get_user(new_id)
    if not user:
        raise RuntimeError("gagal menyimpan user")
    return public_user(user)


def delete_user(user_id: str) -> bool:
    user = get_user(user_id)
    if not user:
        return False
    if user["role"] == "administrator" and _count_active_admins(exclude_id=user_id) < 1:
        raise ValueError("tidak bisa menghapus administrator terakhir")
    with _lock:
        conn = _connect()
        try:
            conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            cur = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            deleted = cur.rowcount > 0
        finally:
            conn.close()
    return deleted


def authenticate(username: str, password: str) -> dict[str, Any] | None:
    user = get_user_by_username(username)
    if not user or not user.get("active"):
        return None
    if not verify_password(password, user.get("password_hash") or ""):
        return None
    return public_user(user)


def create_session(user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    now = datetime.now()
    expires = now + timedelta(days=SESSION_DAYS)
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                """
                INSERT INTO sessions (token, user_id, created_at, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    token,
                    user_id,
                    now.isoformat(timespec="seconds"),
                    expires.isoformat(timespec="seconds"),
                ),
            )
            conn.commit()
        finally:
            conn.close()
    return token


def destroy_session(token: str | None) -> None:
    if not token:
        return
    with _lock:
        conn = _connect()
        try:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
        finally:
            conn.close()


def get_user_by_session(token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    now = datetime.now().isoformat(timespec="seconds")
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                """
                SELECT u.* FROM sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.token = ? AND s.expires_at >= ? AND u.active = 1
                """,
                (token, now),
            ).fetchone()
            if not row:
                conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
                conn.commit()
                return None
        finally:
            conn.close()
    return public_user(_row_to_user(row))


def user_can_access_menu(user: dict[str, Any] | None, menu: str) -> bool:
    if not user:
        return False
    if user.get("role") == "administrator":
        return True
    return menu in (user.get("menus") or [])


def session_cookie_header(token: str, *, clear: bool = False) -> str:
    if clear:
        return f"{SESSION_COOKIE}=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"
    max_age = SESSION_DAYS * 24 * 3600
    return (
        f"{SESSION_COOKIE}={token}; Path=/; Max-Age={max_age}; HttpOnly; SameSite=Lax"
    )
