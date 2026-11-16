"""Persistent incident / disruption history for Simplo Monitor."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "incident_log.db"

_lock = threading.RLock()


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS incident_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    device_name TEXT NOT NULL,
                    location TEXT,
                    ip TEXT,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    status_from TEXT,
                    status_to TEXT,
                    title TEXT NOT NULL,
                    detail TEXT NOT NULL,
                    source TEXT
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_logs_ts ON incident_logs(ts)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_logs_device ON incident_logs(device_id)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS device_meta (
                    device_id TEXT PRIMARY KEY,
                    installation_date TEXT,
                    warranty_end_date TEXT,
                    maintenance_end_date TEXT,
                    location_detail TEXT,
                    updated_at TEXT NOT NULL
                )
                """
            )
            _ensure_column(conn, "device_meta", "location_detail", "TEXT")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS assets (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'CCTV',
                    location TEXT DEFAULT '',
                    location_detail TEXT DEFAULT '',
                    ip TEXT DEFAULT '',
                    vendor TEXT DEFAULT '',
                    model TEXT DEFAULT '',
                    mac TEXT DEFAULT '',
                    monitor_enabled INTEGER NOT NULL DEFAULT 1,
                    installation_date TEXT DEFAULT '',
                    warranty_end_date TEXT DEFAULT '',
                    maintenance_end_date TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_assets_category ON assets(category)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS technicians (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    phone TEXT DEFAULT '',
                    email TEXT DEFAULT '',
                    telegram_id TEXT DEFAULT '',
                    skills TEXT DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_technicians_name ON technicians(name)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS work_orders (
                    id TEXT PRIMARY KEY,
                    wo_number TEXT NOT NULL UNIQUE,
                    work_date TEXT NOT NULL,
                    work_time TEXT NOT NULL,
                    category TEXT DEFAULT '',
                    asset_ids TEXT NOT NULL DEFAULT '[]',
                    technician_ids TEXT NOT NULL DEFAULT '[]',
                    notes TEXT DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'open',
                    email_status TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            _ensure_column(conn, "work_orders", "category", "TEXT DEFAULT ''")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_work_orders_date ON work_orders(work_date)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pm_schedules (
                    id TEXT PRIMARY KEY,
                    asset_id TEXT NOT NULL UNIQUE,
                    interval_days INTEGER NOT NULL,
                    next_due_date TEXT NOT NULL,
                    last_service_date TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_pm_schedules_due ON pm_schedules(next_due_date)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pm_service_records (
                    id TEXT PRIMARY KEY,
                    schedule_id TEXT NOT NULL,
                    asset_id TEXT NOT NULL,
                    service_date TEXT NOT NULL,
                    technician_id TEXT DEFAULT '',
                    notes TEXT DEFAULT '',
                    next_due_after TEXT DEFAULT '',
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_pm_records_schedule ON pm_service_records(schedule_id, service_date)"
            )
            conn.commit()
        finally:
            conn.close()


ASSET_CATEGORIES = ("Network", "CCTV", "Access", "Alarm")

PM_INTERVAL_PRESETS: dict[int, str] = {
    30: "Bulanan",
    90: "Triwulan",
    180: "Semester",
    365: "Tahunan",
}


def _ensure_column(
    conn: sqlite3.Connection, table: str, column: str, decl: str
) -> None:
    cols = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")


def _normalize_text(value: Any, *, max_len: int = 500) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if len(text) > max_len:
        raise ValueError(f"teks terlalu panjang (maks {max_len} karakter)")
    return text


def _normalize_date(value: Any) -> str:
    """Accept YYYY-MM-DD (or empty). Reject other formats."""
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    try:
        datetime.strptime(text[:10], "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"tanggal tidak valid: {text}") from exc
    return text[:10]


def date_status(end_date: str | None, *, today: datetime | None = None) -> str:
    """Return active | expired | unset based on end date (inclusive)."""
    if not end_date:
        return "unset"
    try:
        end = datetime.strptime(str(end_date)[:10], "%Y-%m-%d").date()
    except ValueError:
        return "unset"
    current = (today or datetime.now()).date()
    return "active" if current <= end else "expired"


def enrich_device_meta(device: dict[str, Any], meta: dict[str, Any] | None = None) -> dict[str, Any]:
    m = meta or {}
    install = m.get("installation_date") or ""
    warranty = m.get("warranty_end_date") or ""
    maintenance = m.get("maintenance_end_date") or ""
    location_detail = m.get("location_detail") or ""
    device["installation_date"] = install
    device["warranty_end_date"] = warranty
    device["maintenance_end_date"] = maintenance
    device["location_detail"] = location_detail
    device["warranty_status"] = date_status(warranty)
    device["maintenance_status"] = date_status(maintenance)
    return device


def get_device_meta(device_id: str) -> dict[str, Any]:
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT * FROM device_meta WHERE device_id = ?",
                (device_id,),
            ).fetchone()
        finally:
            conn.close()
    if not row:
        return {
            "device_id": device_id,
            "installation_date": "",
            "warranty_end_date": "",
            "maintenance_end_date": "",
            "location_detail": "",
            "updated_at": None,
        }
    keys = row.keys()
    return {
        "device_id": row["device_id"],
        "installation_date": row["installation_date"] or "",
        "warranty_end_date": row["warranty_end_date"] or "",
        "maintenance_end_date": row["maintenance_end_date"] or "",
        "location_detail": (row["location_detail"] if "location_detail" in keys else "") or "",
        "updated_at": row["updated_at"],
    }


def get_all_device_meta() -> dict[str, dict[str, Any]]:
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute("SELECT * FROM device_meta").fetchall()
        finally:
            conn.close()
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        keys = row.keys()
        out[row["device_id"]] = {
            "device_id": row["device_id"],
            "installation_date": row["installation_date"] or "",
            "warranty_end_date": row["warranty_end_date"] or "",
            "maintenance_end_date": row["maintenance_end_date"] or "",
            "location_detail": (row["location_detail"] if "location_detail" in keys else "") or "",
            "updated_at": row["updated_at"],
        }
    return out


def upsert_device_meta(
    device_id: str,
    *,
    installation_date: Any = None,
    warranty_end_date: Any = None,
    maintenance_end_date: Any = None,
    location_detail: Any = None,
) -> dict[str, Any]:
    if not device_id or not str(device_id).strip():
        raise ValueError("device_id wajib diisi")

    current = get_device_meta(device_id)
    install = (
        _normalize_date(installation_date)
        if installation_date is not None
        else current["installation_date"]
    )
    warranty = (
        _normalize_date(warranty_end_date)
        if warranty_end_date is not None
        else current["warranty_end_date"]
    )
    maintenance = (
        _normalize_date(maintenance_end_date)
        if maintenance_end_date is not None
        else current["maintenance_end_date"]
    )
    loc_detail = (
        _normalize_text(location_detail)
        if location_detail is not None
        else current["location_detail"]
    )
    stamp = datetime.now().isoformat(timespec="seconds")

    with _lock:
        conn = _connect()
        try:
            conn.execute(
                """
                INSERT INTO device_meta (
                    device_id, installation_date, warranty_end_date,
                    maintenance_end_date, location_detail, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(device_id) DO UPDATE SET
                    installation_date = excluded.installation_date,
                    warranty_end_date = excluded.warranty_end_date,
                    maintenance_end_date = excluded.maintenance_end_date,
                    location_detail = excluded.location_detail,
                    updated_at = excluded.updated_at
                """,
                (device_id, install, warranty, maintenance, loc_detail, stamp),
            )
            conn.commit()
        finally:
            conn.close()

    return {
        "device_id": device_id,
        "installation_date": install,
        "warranty_end_date": warranty,
        "maintenance_end_date": maintenance,
        "location_detail": loc_detail,
        "warranty_status": date_status(warranty),
        "maintenance_status": date_status(maintenance),
        "updated_at": stamp,
    }


def _normalize_category(value: Any) -> str:
    text = str(value or "").strip()
    for cat in ASSET_CATEGORIES:
        if text.lower() == cat.lower():
            return cat
    raise ValueError(
        f"kategori tidak valid (pilih: {', '.join(ASSET_CATEGORIES)})"
    )


def _row_to_asset(row: sqlite3.Row) -> dict[str, Any]:
    warranty = row["warranty_end_date"] or ""
    maintenance = row["maintenance_end_date"] or ""
    return {
        "id": row["id"],
        "name": row["name"] or "",
        "category": row["category"] or "CCTV",
        "location": row["location"] or "",
        "location_detail": row["location_detail"] or "",
        "ip": row["ip"] or "",
        "vendor": row["vendor"] or "",
        "model": row["model"] or "",
        "mac": row["mac"] or "",
        "monitor_enabled": bool(row["monitor_enabled"]),
        "installation_date": row["installation_date"] or "",
        "warranty_end_date": warranty,
        "maintenance_end_date": maintenance,
        "warranty_status": date_status(warranty),
        "maintenance_status": date_status(maintenance),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_assets(*, enabled_only: bool = False) -> list[dict[str, Any]]:
    sql = "SELECT * FROM assets"
    params: list[Any] = []
    if enabled_only:
        sql += " WHERE monitor_enabled = 1"
    sql += " ORDER BY category ASC, name COLLATE NOCASE ASC"
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(sql, params).fetchall()
        finally:
            conn.close()
    return [_row_to_asset(r) for r in rows]


def get_asset(asset_id: str) -> dict[str, Any] | None:
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT * FROM assets WHERE id = ?", (asset_id,)
            ).fetchone()
        finally:
            conn.close()
    return _row_to_asset(row) if row else None


def count_assets() -> int:
    with _lock:
        conn = _connect()
        try:
            row = conn.execute("SELECT COUNT(*) AS n FROM assets").fetchone()
        finally:
            conn.close()
    return int(row["n"] if row else 0)


def upsert_asset(payload: dict[str, Any], *, asset_id: str | None = None) -> dict[str, Any]:
    import uuid

    current = get_asset(asset_id) if asset_id else None
    if asset_id and not current:
        raise ValueError("aset tidak ditemukan")

    new_id = asset_id or str(payload.get("id") or "").strip() or uuid.uuid4().hex
    if not asset_id and get_asset(new_id):
        raise ValueError("ID perangkat sudah dipakai")

    name = _normalize_text(payload.get("name"), max_len=120)
    if not name:
        raise ValueError("nama perangkat wajib diisi")
    category = _normalize_category(
        payload.get("category") or (current or {}).get("category") or "CCTV"
    )

    def field(key: str, *, date: bool = False, max_len: int = 200) -> str:
        if key in payload:
            raw = payload.get(key)
            return _normalize_date(raw) if date else _normalize_text(raw, max_len=max_len)
        if current:
            return current.get(key) or ""
        return ""

    location = field("location", max_len=200)
    location_detail = field("location_detail", max_len=500)
    ip = field("ip", max_len=80)
    vendor = field("vendor", max_len=80)
    model = field("model", max_len=80)
    mac = field("mac", max_len=80)
    installation_date = field("installation_date", date=True)
    warranty_end_date = field("warranty_end_date", date=True)
    maintenance_end_date = field("maintenance_end_date", date=True)

    if "monitor_enabled" in payload:
        monitor_enabled = 1 if payload.get("monitor_enabled") in (True, 1, "1", "true", "yes") else 0
    else:
        monitor_enabled = 1 if not current or current.get("monitor_enabled", True) else 0

    stamp = datetime.now().isoformat(timespec="seconds")
    created_at = (current or {}).get("created_at") or stamp

    with _lock:
        conn = _connect()
        try:
            conn.execute(
                """
                INSERT INTO assets (
                    id, name, category, location, location_detail, ip, vendor, model, mac,
                    monitor_enabled, installation_date, warranty_end_date,
                    maintenance_end_date, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    category = excluded.category,
                    location = excluded.location,
                    location_detail = excluded.location_detail,
                    ip = excluded.ip,
                    vendor = excluded.vendor,
                    model = excluded.model,
                    mac = excluded.mac,
                    monitor_enabled = excluded.monitor_enabled,
                    installation_date = excluded.installation_date,
                    warranty_end_date = excluded.warranty_end_date,
                    maintenance_end_date = excluded.maintenance_end_date,
                    updated_at = excluded.updated_at
                """,
                (
                    new_id,
                    name,
                    category,
                    location,
                    location_detail,
                    ip,
                    vendor,
                    model,
                    mac,
                    monitor_enabled,
                    installation_date,
                    warranty_end_date,
                    maintenance_end_date,
                    created_at,
                    stamp,
                ),
            )
            # Keep legacy device_meta in sync for older readers.
            conn.execute(
                """
                INSERT INTO device_meta (
                    device_id, installation_date, warranty_end_date,
                    maintenance_end_date, location_detail, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(device_id) DO UPDATE SET
                    installation_date = excluded.installation_date,
                    warranty_end_date = excluded.warranty_end_date,
                    maintenance_end_date = excluded.maintenance_end_date,
                    location_detail = excluded.location_detail,
                    updated_at = excluded.updated_at
                """,
                (
                    new_id,
                    installation_date,
                    warranty_end_date,
                    maintenance_end_date,
                    location_detail,
                    stamp,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    asset = get_asset(new_id)
    if not asset:
        raise RuntimeError("gagal menyimpan aset")
    return asset


def delete_asset(asset_id: str) -> bool:
    with _lock:
        conn = _connect()
        try:
            cur = conn.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
            conn.execute("DELETE FROM device_meta WHERE device_id = ?", (asset_id,))
            # Hapus jadwal PM & service record terkait asset
            rows = conn.execute(
                "SELECT id FROM pm_schedules WHERE asset_id = ?", (asset_id,)
            ).fetchall()
            for row in rows:
                conn.execute(
                    "DELETE FROM pm_service_records WHERE schedule_id = ?",
                    (row["id"],),
                )
            conn.execute("DELETE FROM pm_schedules WHERE asset_id = ?", (asset_id,))
            conn.commit()
            deleted = cur.rowcount > 0
        finally:
            conn.close()
    return deleted


def seed_assets_from_devices(devices: list[dict[str, Any]]) -> int:
    """Import live devices into assets inventory (skip existing ids)."""
    if not devices:
        return 0
    added = 0
    for d in devices:
        device_id = str(d.get("id") or "").strip()
        if not device_id:
            continue
        if get_asset(device_id):
            continue
        category = str(d.get("type") or "CCTV")
        if category not in ASSET_CATEGORIES:
            category = "Network" if d.get("server_id") == "router" else "CCTV"
        meta = get_device_meta(device_id)
        upsert_asset(
            {
                "id": device_id,
                "name": d.get("name") or device_id,
                "category": category,
                "location": d.get("location") or "",
                "location_detail": meta.get("location_detail") or "",
                "ip": d.get("ip") or "",
                "vendor": d.get("vendor") or "",
                "model": d.get("model") or "",
                "mac": d.get("mac") or "",
                "monitor_enabled": True,
                "installation_date": meta.get("installation_date") or "",
                "warranty_end_date": meta.get("warranty_end_date") or "",
                "maintenance_end_date": meta.get("maintenance_end_date") or "",
            },
            asset_id=None,
        )
        added += 1
    return added


def merge_assets_with_live(live_devices: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Build dashboard device list from asset inventory + live monitoring status.
    Only monitored assets are returned.
    """
    assets = list_assets(enabled_only=True)
    if not assets:
        return live_devices

    live_by_id = {str(d.get("id")): d for d in live_devices if d.get("id")}
    live_by_ip = {
        str(d.get("ip")).strip(): d
        for d in live_devices
        if str(d.get("ip") or "").strip()
    }

    merged: list[dict[str, Any]] = []
    for asset in assets:
        live = live_by_id.get(asset["id"])
        if not live and asset.get("ip"):
            live = live_by_ip.get(asset["ip"])

        if live:
            item = dict(live)
            item["id"] = asset["id"]
            item["name"] = asset["name"] or live.get("name") or asset["id"]
            item["type"] = asset["category"]
            item["location"] = asset["location"] or live.get("location") or ""
            if asset.get("ip"):
                item["ip"] = asset["ip"]
            if asset.get("vendor"):
                item["vendor"] = asset["vendor"]
            if asset.get("model"):
                item["model"] = asset["model"]
            if asset.get("mac"):
                item["mac"] = asset["mac"]
        else:
            item = {
                "id": asset["id"],
                "name": asset["name"],
                "location": asset["location"],
                "type": asset["category"],
                "vendor": asset["vendor"],
                "model": asset["model"],
                "ip": asset["ip"],
                "mac": asset["mac"],
                "status_raw": "Not monitored",
                "online": False,
                "recording": False,
                "schedule_enabled": False,
                "health": "issue",
                "server_id": "inventory",
                "internet_ok": False,
            }

        item["location_detail"] = asset.get("location_detail") or ""
        item["installation_date"] = asset.get("installation_date") or ""
        item["warranty_end_date"] = asset.get("warranty_end_date") or ""
        item["maintenance_end_date"] = asset.get("maintenance_end_date") or ""
        item["warranty_status"] = asset.get("warranty_status") or "unset"
        item["maintenance_status"] = asset.get("maintenance_status") or "unset"
        item["category"] = asset["category"]
        item["managed"] = True
        merged.append(item)
    return merged


def _normalize_skills(value: Any) -> list[str]:
    if value is None:
        return []
    items: list[str]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
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
        raise ValueError("keahlian tidak valid")

    skills: list[str] = []
    for item in items:
        if item is None or str(item).strip() == "":
            continue
        cat = _normalize_category(item)
        if cat not in skills:
            skills.append(cat)
    return skills


def _row_to_technician(row: sqlite3.Row) -> dict[str, Any]:
    try:
        skills = json.loads(row["skills"] or "[]")
        if not isinstance(skills, list):
            skills = []
    except json.JSONDecodeError:
        skills = []
    normalized = []
    for s in skills:
        try:
            normalized.append(_normalize_category(s))
        except ValueError:
            continue
    return {
        "id": row["id"],
        "name": row["name"] or "",
        "phone": row["phone"] or "",
        "email": row["email"] or "",
        "telegram_id": row["telegram_id"] or "",
        "skills": normalized,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_technicians() -> list[dict[str, Any]]:
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT * FROM technicians ORDER BY name COLLATE NOCASE ASC"
            ).fetchall()
        finally:
            conn.close()
    return [_row_to_technician(r) for r in rows]


def get_technician(tech_id: str) -> dict[str, Any] | None:
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT * FROM technicians WHERE id = ?", (tech_id,)
            ).fetchone()
        finally:
            conn.close()
    return _row_to_technician(row) if row else None


def upsert_technician(
    payload: dict[str, Any], *, tech_id: str | None = None
) -> dict[str, Any]:
    import uuid

    current = get_technician(tech_id) if tech_id else None
    if tech_id and not current:
        raise ValueError("teknisi tidak ditemukan")

    new_id = tech_id or str(payload.get("id") or "").strip() or uuid.uuid4().hex
    if not tech_id and get_technician(new_id):
        raise ValueError("ID teknisi sudah dipakai")

    name = _normalize_text(payload.get("name"), max_len=120)
    if not name:
        raise ValueError("nama teknisi wajib diisi")

    def field(key: str, *, max_len: int = 120) -> str:
        if key in payload:
            return _normalize_text(payload.get(key), max_len=max_len)
        if current:
            return current.get(key) or ""
        return ""

    phone = field("phone", max_len=40)
    email = field("email", max_len=120)
    telegram_id = field("telegram_id", max_len=80)
    if "skills" in payload or not current:
        skills = _normalize_skills(payload.get("skills"))
    else:
        skills = list(current.get("skills") or [])
    if not skills:
        raise ValueError("pilih minimal satu keahlian")

    stamp = datetime.now().isoformat(timespec="seconds")
    created_at = (current or {}).get("created_at") or stamp
    skills_json = json.dumps(skills, ensure_ascii=False)

    with _lock:
        conn = _connect()
        try:
            conn.execute(
                """
                INSERT INTO technicians (
                    id, name, phone, email, telegram_id, skills, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    phone = excluded.phone,
                    email = excluded.email,
                    telegram_id = excluded.telegram_id,
                    skills = excluded.skills,
                    updated_at = excluded.updated_at
                """,
                (
                    new_id,
                    name,
                    phone,
                    email,
                    telegram_id,
                    skills_json,
                    created_at,
                    stamp,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    tech = get_technician(new_id)
    if not tech:
        raise RuntimeError("gagal menyimpan teknisi")
    return tech


def delete_technician(tech_id: str) -> bool:
    with _lock:
        conn = _connect()
        try:
            cur = conn.execute("DELETE FROM technicians WHERE id = ?", (tech_id,))
            conn.commit()
            deleted = cur.rowcount > 0
        finally:
            conn.close()
    return deleted


def _parse_id_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if text.startswith("["):
            try:
                parsed = json.loads(text)
                value = parsed if isinstance(parsed, list) else []
            except json.JSONDecodeError:
                value = [p.strip() for p in text.replace(";", ",").split(",")]
        else:
            value = [p.strip() for p in text.replace(";", ",").split(",")]
    if not isinstance(value, (list, tuple, set)):
        raise ValueError("daftar id tidak valid")
    out: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text and text not in out:
            out.append(text)
    return out


def _normalize_time(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError("waktu wajib diisi")
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).strftime("%H:%M")
        except ValueError:
            continue
    raise ValueError("waktu tidak valid (format HH:MM)")


def _next_wo_number(conn: sqlite3.Connection, work_date: str) -> str:
    prefix = f"WO-{work_date.replace('-', '')}-"
    row = conn.execute(
        """
        SELECT wo_number FROM work_orders
        WHERE wo_number LIKE ?
        ORDER BY wo_number DESC LIMIT 1
        """,
        (f"{prefix}%",),
    ).fetchone()
    seq = 1
    if row and row["wo_number"]:
        tail = str(row["wo_number"]).split("-")[-1]
        try:
            seq = int(tail) + 1
        except ValueError:
            seq = 1
    return f"{prefix}{seq:03d}"


def _row_to_work_order(row: sqlite3.Row) -> dict[str, Any]:
    asset_ids = _parse_id_list(row["asset_ids"])
    tech_ids = _parse_id_list(row["technician_ids"])
    assets = []
    for aid in asset_ids:
        asset = get_asset(aid)
        if asset:
            assets.append(
                {
                    "id": asset["id"],
                    "name": asset["name"],
                    "category": asset["category"],
                    "location": asset["location"],
                    "ip": asset["ip"],
                }
            )
        else:
            assets.append({"id": aid, "name": aid, "category": "", "location": "", "ip": ""})
    technicians = []
    for tid in tech_ids:
        tech = get_technician(tid)
        if tech:
            technicians.append(
                {
                    "id": tech["id"],
                    "name": tech["name"],
                    "phone": tech["phone"],
                    "email": tech["email"],
                    "telegram_id": tech["telegram_id"],
                }
            )
        else:
            technicians.append(
                {"id": tid, "name": tid, "phone": "", "email": "", "telegram_id": ""}
            )
    keys = row.keys()
    return {
        "id": row["id"],
        "wo_number": row["wo_number"],
        "work_date": row["work_date"] or "",
        "work_time": row["work_time"] or "",
        "category": (row["category"] if "category" in keys else "") or "",
        "asset_ids": asset_ids,
        "technician_ids": tech_ids,
        "assets": assets,
        "technicians": technicians,
        "notes": row["notes"] or "",
        "status": row["status"] or "open",
        "email_status": row["email_status"] or "",
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_work_orders(*, limit: int = 200) -> list[dict[str, Any]]:
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                """
                SELECT * FROM work_orders
                ORDER BY work_date DESC, work_time DESC, created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        finally:
            conn.close()
    return [_row_to_work_order(r) for r in rows]


def get_work_order(wo_id: str) -> dict[str, Any] | None:
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT * FROM work_orders WHERE id = ?", (wo_id,)
            ).fetchone()
        finally:
            conn.close()
    return _row_to_work_order(row) if row else None


def create_work_order(payload: dict[str, Any]) -> dict[str, Any]:
    import uuid

    work_date = _normalize_date(payload.get("work_date"))
    if not work_date:
        raise ValueError("tanggal wajib diisi")
    work_time = _normalize_time(payload.get("work_time"))
    category = _normalize_category(payload.get("category"))
    asset_ids = _parse_id_list(payload.get("asset_ids"))
    technician_ids = _parse_id_list(payload.get("technician_ids"))
    notes = _normalize_text(payload.get("notes"), max_len=2000)

    if not asset_ids:
        raise ValueError("pilih minimal satu asset")
    if not technician_ids:
        raise ValueError("pilih minimal satu teknisi")

    for aid in asset_ids:
        asset = get_asset(aid)
        if not asset:
            raise ValueError(f"asset tidak ditemukan: {aid}")
        if asset.get("category") != category:
            raise ValueError(
                f"asset {asset.get('name') or aid} bukan kategori {category}"
            )
    for tid in technician_ids:
        tech = get_technician(tid)
        if not tech:
            raise ValueError(f"teknisi tidak ditemukan: {tid}")
        if category not in (tech.get("skills") or []):
            raise ValueError(
                f"teknisi {tech.get('name') or tid} tidak punya keahlian {category}"
            )

    wo_id = uuid.uuid4().hex
    stamp = datetime.now().isoformat(timespec="seconds")

    with _lock:
        conn = _connect()
        try:
            wo_number = _next_wo_number(conn, work_date)
            conn.execute(
                """
                INSERT INTO work_orders (
                    id, wo_number, work_date, work_time, category, asset_ids, technician_ids,
                    notes, status, email_status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open', '', ?, ?)
                """,
                (
                    wo_id,
                    wo_number,
                    work_date,
                    work_time,
                    category,
                    json.dumps(asset_ids, ensure_ascii=False),
                    json.dumps(technician_ids, ensure_ascii=False),
                    notes,
                    stamp,
                    stamp,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    wo = get_work_order(wo_id)
    if not wo:
        raise RuntimeError("gagal membuat work order")
    return wo


def update_work_order_email_status(wo_id: str, email_status: str) -> None:
    stamp = datetime.now().isoformat(timespec="seconds")
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                """
                UPDATE work_orders
                SET email_status = ?, updated_at = ?
                WHERE id = ?
                """,
                (_normalize_text(email_status, max_len=1000), stamp, wo_id),
            )
            conn.commit()
        finally:
            conn.close()


def delete_work_order(wo_id: str) -> bool:
    with _lock:
        conn = _connect()
        try:
            cur = conn.execute("DELETE FROM work_orders WHERE id = ?", (wo_id,))
            conn.commit()
            deleted = cur.rowcount > 0
        finally:
            conn.close()
    return deleted


def list_open_work_orders(*, limit: int = 500) -> list[dict[str, Any]]:
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                """
                SELECT * FROM work_orders
                WHERE status = 'open'
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        finally:
            conn.close()
    return [_row_to_work_order(r) for r in rows]


def open_work_order_asset_ids() -> set[str]:
    ids: set[str] = set()
    for wo in list_open_work_orders():
        for aid in wo.get("asset_ids") or []:
            ids.add(str(aid))
    return ids


def open_work_order_technician_ids() -> set[str]:
    ids: set[str] = set()
    for wo in list_open_work_orders():
        for tid in wo.get("technician_ids") or []:
            ids.add(str(tid))
    return ids


def latest_work_order_created_at_for_asset(asset_id: str) -> datetime | None:
    """Newest work order created_at that includes this asset (any status)."""
    if not asset_id:
        return None
    needle = str(asset_id)
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                """
                SELECT created_at, asset_ids FROM work_orders
                ORDER BY created_at DESC
                LIMIT 500
                """
            ).fetchall()
        finally:
            conn.close()
    for row in rows:
        if needle in _parse_id_list(row["asset_ids"]):
            return _parse_ts(row["created_at"] or "")
    return None


def _add_days(date_str: str, days: int) -> str:
    base = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
    return (base + timedelta(days=int(days))).isoformat()


def _normalize_interval_days(value: Any) -> int:
    try:
        days = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("interval hari tidak valid") from exc
    if days < 1 or days > 3650:
        raise ValueError("interval hari harus antara 1–3650")
    return days


def interval_label(days: int) -> str:
    return PM_INTERVAL_PRESETS.get(int(days), f"{int(days)} hari")


def pm_due_status(next_due_date: str, *, active: bool = True, today: datetime | None = None) -> str:
    if not active:
        return "inactive"
    if not next_due_date:
        return "unset"
    try:
        due = datetime.strptime(str(next_due_date)[:10], "%Y-%m-%d").date()
    except ValueError:
        return "unset"
    current = (today or datetime.now()).date()
    if due < current:
        return "overdue"
    if due <= current + timedelta(days=7):
        return "due_soon"
    return "ok"


def _row_to_pm_schedule(row: sqlite3.Row) -> dict[str, Any]:
    asset = get_asset(row["asset_id"])
    interval_days = int(row["interval_days"] or 0)
    next_due = row["next_due_date"] or ""
    active = bool(row["active"])
    contract_end = (asset or {}).get("maintenance_end_date") or ""
    contract_status = date_status(contract_end)
    return {
        "id": row["id"],
        "asset_id": row["asset_id"],
        "asset": asset,
        "interval_days": interval_days,
        "interval_label": interval_label(interval_days),
        "next_due_date": next_due,
        "last_service_date": row["last_service_date"] or "",
        "notes": row["notes"] or "",
        "active": active,
        "due_status": pm_due_status(next_due, active=active),
        "contract_end_date": contract_end,
        "contract_status": contract_status,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def list_pm_schedules(*, limit: int = 500) -> list[dict[str, Any]]:
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                """
                SELECT * FROM pm_schedules
                ORDER BY
                  CASE WHEN active = 1 THEN 0 ELSE 1 END,
                  next_due_date ASC,
                  created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        finally:
            conn.close()
    return [_row_to_pm_schedule(r) for r in rows]


def get_pm_schedule(schedule_id: str) -> dict[str, Any] | None:
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT * FROM pm_schedules WHERE id = ?", (schedule_id,)
            ).fetchone()
        finally:
            conn.close()
    return _row_to_pm_schedule(row) if row else None


def get_pm_schedule_by_asset(asset_id: str) -> dict[str, Any] | None:
    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT * FROM pm_schedules WHERE asset_id = ?", (asset_id,)
            ).fetchone()
        finally:
            conn.close()
    return _row_to_pm_schedule(row) if row else None


def upsert_pm_schedule(
    payload: dict[str, Any], *, schedule_id: str | None = None
) -> dict[str, Any]:
    import uuid

    current = get_pm_schedule(schedule_id) if schedule_id else None
    if schedule_id and not current:
        raise ValueError("jadwal PM tidak ditemukan")

    asset_id = _normalize_text(
        payload.get("asset_id") if "asset_id" in payload else (current or {}).get("asset_id"),
        max_len=80,
    )
    if not asset_id:
        raise ValueError("asset wajib dipilih")
    asset = get_asset(asset_id)
    if not asset:
        raise ValueError("asset tidak ditemukan")

    existing = get_pm_schedule_by_asset(asset_id)
    if existing and (not current or existing["id"] != current["id"]):
        raise ValueError(f"asset {asset.get('name') or asset_id} sudah punya jadwal PM")

    if "interval_days" in payload or not current:
        interval_days = _normalize_interval_days(
            payload.get("interval_days") if "interval_days" in payload else None
        )
    else:
        interval_days = int(current["interval_days"])

    if "next_due_date" in payload or not current:
        next_due = _normalize_date(payload.get("next_due_date"))
        if not next_due:
            raise ValueError("jadwal berikutnya wajib diisi")
    else:
        next_due = current["next_due_date"]

    notes = (
        _normalize_text(payload.get("notes"), max_len=2000)
        if "notes" in payload
        else (current or {}).get("notes") or ""
    )

    if "active" in payload:
        active = 1 if payload.get("active") in (True, 1, "1", "true", "yes") else 0
    else:
        active = 1 if not current or current.get("active", True) else 0

    last_service = (current or {}).get("last_service_date") or ""
    if "last_service_date" in payload:
        last_service = _normalize_date(payload.get("last_service_date"))

    new_id = schedule_id or uuid.uuid4().hex
    stamp = datetime.now().isoformat(timespec="seconds")
    created_at = (current or {}).get("created_at") or stamp

    with _lock:
        conn = _connect()
        try:
            conn.execute(
                """
                INSERT INTO pm_schedules (
                    id, asset_id, interval_days, next_due_date, last_service_date,
                    notes, active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    asset_id = excluded.asset_id,
                    interval_days = excluded.interval_days,
                    next_due_date = excluded.next_due_date,
                    last_service_date = excluded.last_service_date,
                    notes = excluded.notes,
                    active = excluded.active,
                    updated_at = excluded.updated_at
                """,
                (
                    new_id,
                    asset_id,
                    interval_days,
                    next_due,
                    last_service,
                    notes,
                    active,
                    created_at,
                    stamp,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    saved = get_pm_schedule(new_id)
    if not saved:
        raise RuntimeError("gagal menyimpan jadwal PM")
    return saved


def delete_pm_schedule(schedule_id: str) -> bool:
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "DELETE FROM pm_service_records WHERE schedule_id = ?", (schedule_id,)
            )
            cur = conn.execute("DELETE FROM pm_schedules WHERE id = ?", (schedule_id,))
            conn.commit()
            deleted = cur.rowcount > 0
        finally:
            conn.close()
    return deleted


def _row_to_pm_record(row: sqlite3.Row) -> dict[str, Any]:
    tech_id = row["technician_id"] or ""
    tech = get_technician(tech_id) if tech_id else None
    return {
        "id": row["id"],
        "schedule_id": row["schedule_id"],
        "asset_id": row["asset_id"],
        "service_date": row["service_date"] or "",
        "technician_id": tech_id,
        "technician": tech,
        "notes": row["notes"] or "",
        "next_due_after": row["next_due_after"] or "",
        "created_at": row["created_at"],
    }


def list_pm_service_records(schedule_id: str, *, limit: int = 200) -> list[dict[str, Any]]:
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                """
                SELECT * FROM pm_service_records
                WHERE schedule_id = ?
                ORDER BY service_date DESC, created_at DESC
                LIMIT ?
                """,
                (schedule_id, limit),
            ).fetchall()
        finally:
            conn.close()
    return [_row_to_pm_record(r) for r in rows]


def create_pm_service_record(schedule_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    import uuid

    schedule = get_pm_schedule(schedule_id)
    if not schedule:
        raise ValueError("jadwal PM tidak ditemukan")

    service_date = _normalize_date(payload.get("service_date"))
    if not service_date:
        raise ValueError("tanggal service wajib diisi")

    technician_id = _normalize_text(payload.get("technician_id"), max_len=80)
    if technician_id:
        tech = get_technician(technician_id)
        if not tech:
            raise ValueError("teknisi tidak ditemukan")

    notes = _normalize_text(payload.get("notes"), max_len=2000)
    next_due_after = _add_days(service_date, int(schedule["interval_days"]))

    # Cap ke akhir kontrak hanya jika kontrak masih berlaku setelah tanggal service
    contract_end = schedule.get("contract_end_date") or ""
    if (
        contract_end
        and contract_end >= service_date
        and next_due_after > contract_end
    ):
        next_due_after = contract_end

    record_id = uuid.uuid4().hex
    stamp = datetime.now().isoformat(timespec="seconds")

    with _lock:
        conn = _connect()
        try:
            conn.execute(
                """
                INSERT INTO pm_service_records (
                    id, schedule_id, asset_id, service_date, technician_id,
                    notes, next_due_after, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    schedule_id,
                    schedule["asset_id"],
                    service_date,
                    technician_id,
                    notes,
                    next_due_after,
                    stamp,
                ),
            )
            conn.execute(
                """
                UPDATE pm_schedules
                SET last_service_date = ?, next_due_date = ?, updated_at = ?
                WHERE id = ?
                """,
                (service_date, next_due_after, stamp, schedule_id),
            )
            conn.commit()
        finally:
            conn.close()

    with _lock:
        conn = _connect()
        try:
            row = conn.execute(
                "SELECT * FROM pm_service_records WHERE id = ?", (record_id,)
            ).fetchone()
        finally:
            conn.close()
    if not row:
        raise RuntimeError("gagal menyimpan service record")
    return _row_to_pm_record(row)


def delete_pm_service_record(record_id: str) -> bool:
    with _lock:
        conn = _connect()
        try:
            cur = conn.execute(
                "DELETE FROM pm_service_records WHERE id = ?", (record_id,)
            )
            conn.commit()
            deleted = cur.rowcount > 0
        finally:
            conn.close()
    return deleted


def get_open_issue_started_at(device_id: str) -> datetime | None:
    """Return start time of the currently open issue incident, if any."""
    return get_open_abnormal_started_at(device_id, "issue")


def get_open_abnormal_started_at(
    device_id: str, health: str
) -> datetime | None:
    """Return start time of the current open issue/attention condition."""
    if not device_id:
        return None
    health = str(health or "").strip().lower()
    if health not in {"issue", "attention"}:
        return None

    with _lock:
        conn = _connect()
        try:
            if health == "issue":
                started = conn.execute(
                    """
                    SELECT ts FROM incident_logs
                    WHERE device_id = ?
                      AND event_type = 'started'
                      AND IFNULL(severity, '') != 'attention'
                    ORDER BY ts DESC, id DESC
                    LIMIT 1
                    """,
                    (device_id,),
                ).fetchone()
                if not started:
                    return None
                started_ts = started["ts"]
                resolved = conn.execute(
                    """
                    SELECT 1 FROM incident_logs
                    WHERE device_id = ?
                      AND event_type = 'resolved'
                      AND ts > ?
                    LIMIT 1
                    """,
                    (device_id, started_ts),
                ).fetchone()
                if resolved:
                    return None
                return _parse_ts(started_ts)

            # attention: started via attention_started, or issue→attention resolve
            started = conn.execute(
                """
                SELECT ts, event_type, severity FROM incident_logs
                WHERE device_id = ?
                  AND (
                    event_type = 'attention_started'
                    OR (event_type = 'resolved' AND IFNULL(severity, '') = 'attention')
                  )
                ORDER BY ts DESC, id DESC
                LIMIT 1
                """,
                (device_id,),
            ).fetchone()
            if not started:
                return None
            started_ts = started["ts"]
            # Attention ends when resolved to healthy, or escalates to issue
            ended = conn.execute(
                """
                SELECT 1 FROM incident_logs
                WHERE device_id = ?
                  AND ts > ?
                  AND (
                    event_type = 'attention_resolved'
                    OR (
                      event_type = 'started'
                      AND IFNULL(severity, '') != 'attention'
                    )
                  )
                LIMIT 1
                """,
                (device_id, started_ts),
            ).fetchone()
            if ended:
                return None
            return _parse_ts(started_ts)
        finally:
            conn.close()


def add_log(
    *,
    device_id: str,
    device_name: str,
    location: str,
    ip: str,
    event_type: str,
    severity: str,
    status_from: str,
    status_to: str,
    title: str,
    detail: str,
    source: str = "nx",
    ts: str | None = None,
) -> dict[str, Any]:
    stamp = ts or datetime.now().isoformat(timespec="seconds")
    with _lock:
        conn = _connect()
        try:
            cur = conn.execute(
                """
                INSERT INTO incident_logs (
                    ts, device_id, device_name, location, ip,
                    event_type, severity, status_from, status_to,
                    title, detail, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    stamp,
                    device_id,
                    device_name,
                    location or "",
                    ip or "",
                    event_type,
                    severity,
                    status_from or "",
                    status_to or "",
                    title,
                    detail,
                    source,
                ),
            )
            conn.commit()
            row_id = cur.lastrowid
        finally:
            conn.close()
    return {
        "id": row_id,
        "ts": stamp,
        "device_id": device_id,
        "device_name": device_name,
        "location": location or "",
        "ip": ip or "",
        "event_type": event_type,
        "severity": severity,
        "status_from": status_from or "",
        "status_to": status_to or "",
        "title": title,
        "detail": detail,
        "source": source,
    }


def query_logs(
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    device_id: str | None = None,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []

    if date_from:
        clauses.append("ts >= ?")
        params.append(f"{date_from}T00:00:00")
    if date_to:
        clauses.append("ts <= ?")
        params.append(f"{date_to}T23:59:59")
    if device_id:
        clauses.append("device_id = ?")
        params.append(device_id)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"""
        SELECT * FROM incident_logs
        {where}
        ORDER BY ts DESC, id DESC
        LIMIT ?
    """
    params.append(limit)

    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(sql, params).fetchall()
        finally:
            conn.close()
    return [dict(r) for r in rows]


def list_devices_in_logs() -> list[dict[str, str]]:
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                """
                SELECT device_id, MAX(device_name) AS device_name
                FROM incident_logs
                GROUP BY device_id
                ORDER BY device_name COLLATE NOCASE
                """
            ).fetchall()
        finally:
            conn.close()
    return [{"id": r["device_id"], "name": r["device_name"]} for r in rows]


def count_logs() -> int:
    with _lock:
        conn = _connect()
        try:
            row = conn.execute("SELECT COUNT(*) AS c FROM incident_logs").fetchone()
            return int(row["c"] if row else 0)
        finally:
            conn.close()


def _parse_ts(value: str) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.strptime(text[:26], fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _event_to_state(event_type: str, severity: str) -> str:
    """Map an incident log row to the health state *after* the event."""
    if event_type == "started":
        return "issue" if severity != "attention" else "attention"
    if event_type == "attention_started":
        return "attention"
    if event_type == "resolved":
        return "healthy" if severity == "healthy" else "attention"
    if event_type == "attention_resolved":
        return "healthy"
    if severity in {"healthy", "attention", "issue"}:
        return severity
    return "healthy"


def _initial_state(logs_before: list[dict[str, Any]]) -> str:
    if not logs_before:
        return "healthy"
    last = logs_before[-1]
    return _event_to_state(last.get("event_type", ""), last.get("severity", ""))


def _clip_interval(
    start: datetime, end: datetime, range_start: datetime, range_end: datetime
) -> tuple[datetime, datetime] | None:
    a = max(start, range_start)
    b = min(end, range_end)
    if b <= a:
        return None
    return a, b


def _build_segments_for_device(
    logs: list[dict[str, Any]],
    *,
    range_start: datetime,
    range_end: datetime,
) -> list[dict[str, Any]]:
    chronological = sorted(
        (row for row in logs if _parse_ts(row.get("ts") or "")),
        key=lambda r: (_parse_ts(r["ts"]), r.get("id") or 0),
    )
    before = [r for r in chronological if _parse_ts(r["ts"]) < range_start]
    in_range = [
        r for r in chronological if range_start <= _parse_ts(r["ts"]) <= range_end
    ]

    state = _initial_state(before)
    cursor = range_start
    segments: list[dict[str, Any]] = []

    def close_until(when: datetime, next_state: str) -> None:
        nonlocal state, cursor
        clipped = _clip_interval(cursor, when, range_start, range_end)
        if clipped:
            a, b = clipped
            seconds = (b - a).total_seconds()
            if seconds > 0:
                segments.append(
                    {
                        "start": a.isoformat(timespec="seconds"),
                        "end": b.isoformat(timespec="seconds"),
                        "state": state,
                        "seconds": round(seconds, 1),
                    }
                )
        state = next_state
        cursor = when

    for row in in_range:
        ts = _parse_ts(row["ts"])
        if ts is None:
            continue
        close_until(ts, _event_to_state(row.get("event_type", ""), row.get("severity", "")))

    close_until(range_end, state)
    return segments


def _merge_adjacent(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not segments:
        return []
    merged = [dict(segments[0])]
    for seg in segments[1:]:
        prev = merged[-1]
        if prev["state"] == seg["state"] and prev["end"] == seg["start"]:
            prev["end"] = seg["end"]
            prev["seconds"] = round(prev["seconds"] + seg["seconds"], 1)
        else:
            merged.append(dict(seg))
    return merged


def _sum_by_state(segments: list[dict[str, Any]]) -> dict[str, float]:
    totals = {"healthy": 0.0, "attention": 0.0, "issue": 0.0}
    for seg in segments:
        key = seg["state"] if seg["state"] in totals else "healthy"
        totals[key] += float(seg["seconds"])
    return totals


def _daily_buckets(
    segments: list[dict[str, Any]],
    *,
    range_start: datetime,
    range_end: datetime,
) -> list[dict[str, Any]]:
    day = range_start.date()
    end_day = range_end.date()
    buckets: list[dict[str, Any]] = []
    while day <= end_day:
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time()).replace(microsecond=0)
        day_start = max(day_start, range_start)
        day_end = min(day_end, range_end)
        totals = {"healthy": 0.0, "attention": 0.0, "issue": 0.0}
        for seg in segments:
            a = _parse_ts(seg["start"])
            b = _parse_ts(seg["end"])
            if a is None or b is None:
                continue
            clipped = _clip_interval(a, b, day_start, day_end)
            if not clipped:
                continue
            ca, cb = clipped
            totals[seg["state"] if seg["state"] in totals else "healthy"] += (
                cb - ca
            ).total_seconds()
        span = max((day_end - day_start).total_seconds(), 1.0)
        healthy_pct = round((totals["healthy"] / span) * 100, 1)
        buckets.append(
            {
                "date": day.isoformat(),
                "healthy_seconds": round(totals["healthy"], 1),
                "attention_seconds": round(totals["attention"], 1),
                "issue_seconds": round(totals["issue"], 1),
                "healthy_pct": healthy_pct,
                "uptime_pct": round(
                    ((totals["healthy"] + totals["attention"]) / span) * 100, 1
                ),
            }
        )
        day += timedelta(days=1)
    return buckets


def compute_statistik(
    *,
    date_from: str,
    date_to: str,
    device_id: str | None = None,
    device_catalog: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Derive healthy%/uptime timeline from incident transition logs."""
    range_start = datetime.fromisoformat(f"{date_from}T00:00:00")
    range_end = datetime.fromisoformat(f"{date_to}T23:59:59")
    if range_end < range_start:
        range_start, range_end = range_end, range_start

    catalog = {d["id"]: d.get("name") or d["id"] for d in (device_catalog or [])}
    for d in list_devices_in_logs():
        catalog.setdefault(d["id"], d["name"])

    if device_id:
        target_ids = [device_id]
        if device_id not in catalog:
            catalog[device_id] = device_id
    else:
        target_ids = sorted(catalog.keys(), key=lambda i: catalog[i].lower())

    # Load all logs up to range end (includes lookback for initial state).
    raw_logs = query_logs(date_to=date_to, device_id=device_id, limit=50000)
    logs_by_device: dict[str, list[dict[str, Any]]] = {did: [] for did in target_ids}
    for row in raw_logs:
        did = row.get("device_id")
        if did in logs_by_device:
            logs_by_device[did].append(row)
        elif not device_id and did:
            # Include devices that only appear in logs
            logs_by_device.setdefault(did, []).append(row)
            catalog.setdefault(did, row.get("device_name") or did)

    if not device_id:
        target_ids = sorted(logs_by_device.keys(), key=lambda i: catalog.get(i, i).lower())

    per_device: list[dict[str, Any]] = []
    all_segments: list[dict[str, Any]] = []
    aggregate = {"healthy": 0.0, "attention": 0.0, "issue": 0.0}

    for did in target_ids:
        segs = _merge_adjacent(
            _build_segments_for_device(
                logs_by_device.get(did, []),
                range_start=range_start,
                range_end=range_end,
            )
        )
        totals = _sum_by_state(segs)
        span = sum(totals.values()) or 1.0
        healthy_pct = round((totals["healthy"] / span) * 100, 1)
        uptime_pct = round(((totals["healthy"] + totals["attention"]) / span) * 100, 1)
        downtime_pct = round((totals["issue"] / span) * 100, 1)
        for key in aggregate:
            aggregate[key] += totals[key]
        device_row = {
            "id": did,
            "name": catalog.get(did, did),
            "healthy_pct": healthy_pct,
            "uptime_pct": uptime_pct,
            "downtime_pct": downtime_pct,
            "healthy_seconds": round(totals["healthy"], 1),
            "attention_seconds": round(totals["attention"], 1),
            "issue_seconds": round(totals["issue"], 1),
            "segments": segs,
        }
        per_device.append(device_row)
        for seg in segs:
            all_segments.append({**seg, "device_id": did, "device_name": device_row["name"]})

    total_span = sum(aggregate.values()) or 1.0
    healthy_pct = round((aggregate["healthy"] / total_span) * 100, 1)
    uptime_pct = round(
        ((aggregate["healthy"] + aggregate["attention"]) / total_span) * 100, 1
    )
    downtime_pct = round((aggregate["issue"] / total_span) * 100, 1)

    # Daily buckets: average across devices (equal weight per device-day).
    daily_map: dict[str, dict[str, float]] = {}
    daily_counts: dict[str, int] = {}
    for device in per_device:
        for bucket in _daily_buckets(
            device["segments"], range_start=range_start, range_end=range_end
        ):
            key = bucket["date"]
            slot = daily_map.setdefault(
                key,
                {"healthy": 0.0, "attention": 0.0, "issue": 0.0, "healthy_pct": 0.0},
            )
            slot["healthy"] += bucket["healthy_seconds"]
            slot["attention"] += bucket["attention_seconds"]
            slot["issue"] += bucket["issue_seconds"]
            slot["healthy_pct"] += bucket["healthy_pct"]
            daily_counts[key] = daily_counts.get(key, 0) + 1

    daily: list[dict[str, Any]] = []
    for key in sorted(daily_map.keys()):
        slot = daily_map[key]
        n = max(daily_counts.get(key, 1), 1)
        span = slot["healthy"] + slot["attention"] + slot["issue"] or 1.0
        daily.append(
            {
                "date": key,
                "healthy_seconds": round(slot["healthy"], 1),
                "attention_seconds": round(slot["attention"], 1),
                "issue_seconds": round(slot["issue"], 1),
                "healthy_pct": round(slot["healthy_pct"] / n, 1),
                "uptime_pct": round(
                    ((slot["healthy"] + slot["attention"]) / span) * 100, 1
                ),
            }
        )

    # Timeline for chart: single-device segments, or aggregated daily for "all".
    timeline_segments = (
        per_device[0]["segments"]
        if device_id and per_device
        else [
            {
                "start": f"{b['date']}T00:00:00",
                "end": f"{b['date']}T23:59:59",
                "state": (
                    "issue"
                    if b["issue_seconds"] >= b["healthy_seconds"]
                    and b["issue_seconds"] >= b["attention_seconds"]
                    else "attention"
                    if b["attention_seconds"] > b["healthy_seconds"]
                    else "healthy"
                ),
                "seconds": round(
                    b["healthy_seconds"] + b["attention_seconds"] + b["issue_seconds"],
                    1,
                ),
                "healthy_pct": b["healthy_pct"],
                "healthy_seconds": b["healthy_seconds"],
                "attention_seconds": b["attention_seconds"],
                "issue_seconds": b["issue_seconds"],
            }
            for b in daily
        ]
    )

    return {
        "filters": {
            "from": date_from,
            "to": date_to,
            "device": device_id or "all",
        },
        "summary": {
            "healthy_pct": healthy_pct,
            "uptime_pct": uptime_pct,
            "downtime_pct": downtime_pct,
            "healthy_seconds": round(aggregate["healthy"], 1),
            "attention_seconds": round(aggregate["attention"], 1),
            "issue_seconds": round(aggregate["issue"], 1),
            "device_count": len(per_device),
            "range_seconds": round((range_end - range_start).total_seconds(), 1),
        },
        "daily": daily,
        "timeline": timeline_segments,
        "devices": [{"id": k, "name": v} for k, v in sorted(catalog.items(), key=lambda x: x[1].lower())],
        "per_device": [
            {k: v for k, v in d.items() if k != "segments"} for d in per_device
        ],
        "segments": all_segments if device_id else [],
    }


def seed_demo_if_empty() -> None:
    """Seed sample history so Laporan is usable before real events occur."""
    if count_logs() > 0:
        return
    now = datetime.now()
    samples = [
        (
            -2,
            "08:12:00",
            "cctvl0104",
            "CCTV-L01-04",
            "Lobby Utama",
            "192.168.10.10",
            "started",
            "issue",
            "Recording",
            "Offline",
            "Gangguan dimulai",
            "Kamera terdeteksi Offline. Tidak ada stream dari NX Witness. Kemungkinan putus jaringan atau kamera mati.",
        ),
        (
            -2,
            "08:45:00",
            "cctvl0104",
            "CCTV-L01-04",
            "Lobby Utama",
            "192.168.10.10",
            "resolved",
            "healthy",
            "Offline",
            "Recording",
            "Gangguan berakhir — status normal",
            "Kamera kembali Online & Recording. Durasi gangguan sekitar 33 menit.",
        ),
        (
            -1,
            "14:20:00",
            "cctvp0211",
            "CCTV-P02-11",
            "Parkir Basement B2",
            "192.168.10.11",
            "started",
            "issue",
            "Recording",
            "Offline",
            "Gangguan dimulai",
            "Kamera Offline. Status NX: Offline. Recording berhenti otomatis.",
        ),
        (
            -1,
            "16:05:00",
            "nvrrk01",
            "NVR-RK-01",
            "Ruang Server Lt.2",
            "192.168.10.12",
            "started",
            "attention",
            "Recording",
            "Online",
            "Perhatian dimulai",
            "Perangkat online tetapi tidak merekam meski jadwal rekam aktif.",
        ),
        (
            0,
            "09:15:00",
            "nvrrk01",
            "NVR-RK-01",
            "Ruang Server Lt.2",
            "192.168.10.12",
            "resolved",
            "healthy",
            "Online",
            "Recording",
            "Perhatian berakhir — status normal",
            "Recording aktif kembali sesuai jadwal.",
        ),
    ]
    for day_offset, clock, did, name, loc, ip, etype, sev, sfrom, sto, title, detail in samples:
        ts = (now + timedelta(days=day_offset)).strftime(f"%Y-%m-%dT{clock}")
        add_log(
            device_id=did,
            device_name=name,
            location=loc,
            ip=ip,
            event_type=etype,
            severity=sev,
            status_from=sfrom,
            status_to=sto,
            title=title,
            detail=detail,
            source="demo",
            ts=ts,
        )
