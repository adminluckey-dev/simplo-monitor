#!/usr/bin/env python3
"""Simplo System — NX Witness camera monitoring dashboard."""

from __future__ import annotations

import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from auth_users import (
    MENU_OPTIONS,
    SESSION_COOKIE,
    authenticate,
    create_session,
    delete_user,
    destroy_session,
    get_user,
    get_user_by_session,
    init_auth_db,
    list_users,
    session_cookie_header,
    upsert_user,
)
from auto_wo_settings import (
    load_settings as load_auto_wo_settings,
    save_settings as save_auto_wo_settings,
)
from history import (
    ASSET_CATEGORIES,
    add_log,
    compute_statistik,
    count_assets,
    create_pm_service_record,
    create_work_order,
    delete_asset,
    delete_pm_schedule,
    delete_pm_service_record,
    delete_technician,
    delete_work_order,
    enrich_device_meta,
    get_all_device_meta,
    get_asset,
    get_device_meta,
    get_open_abnormal_started_at,
    get_pm_schedule,
    get_technician,
    get_work_order,
    init_db,
    list_assets,
    list_devices_in_logs,
    list_pm_schedules,
    list_pm_service_records,
    list_technicians,
    list_work_orders,
    merge_assets_with_live,
    latest_work_order_created_at_for_asset,
    open_work_order_asset_ids,
    open_work_order_technician_ids,
    query_logs,
    seed_assets_from_devices,
    seed_demo_if_empty,
    update_work_order_email_status,
    upsert_asset,
    upsert_pm_schedule,
    upsert_technician,
)
from notify_settings import (
    load_settings as load_notify_settings,
    public_settings as public_notify_settings,
    save_settings as save_notify_settings,
    send_email,
    send_test_email,
    send_test_telegram,
)


def _format_wo_email(wo: dict) -> tuple[str, str, str]:
    site = CONFIG.get("site_site") or CONFIG.get("site_name") or "CMMS"
    subject = f"[Work Order {wo['wo_number']}] {site} — {wo['work_date']} {wo['work_time']}"
    asset_lines = []
    for a in wo.get("assets") or []:
        asset_lines.append(
            f"- {a.get('name') or a.get('id')} ({a.get('category') or '-'})"
            f" | Lokasi: {a.get('location') or '-'} | IP: {a.get('ip') or '-'}"
        )
    tech_lines = []
    for t in wo.get("technicians") or []:
        tech_lines.append(
            f"- {t.get('name') or t.get('id')} | HP: {t.get('phone') or '-'} | Email: {t.get('email') or '-'}"
        )
    notes = wo.get("notes") or "-"
    text = (
        f"WORK ORDER / PERINTAH KERJA\n"
        f"Nomor    : {wo['wo_number']}\n"
        f"Lokasi   : {site}\n"
        f"Kategori : {wo.get('category') or '-'}\n"
        f"Tanggal  : {wo['work_date']}\n"
        f"Waktu    : {wo['work_time']}\n"
        f"\nAset yang dikerjakan:\n"
        + ("\n".join(asset_lines) if asset_lines else "-")
        + "\n\nTeknisi ditugaskan:\n"
        + ("\n".join(tech_lines) if tech_lines else "-")
        + f"\n\nCatatan:\n{notes}\n"
        + "\n--\nDikirim otomatis oleh Simplo Monitor\n"
    )
    html_assets = "".join(
        f"<li><strong>{a.get('name') or a.get('id')}</strong> "
        f"({a.get('category') or '-'}) — {a.get('location') or '-'} / {a.get('ip') or '-'}</li>"
        for a in (wo.get("assets") or [])
    ) or "<li>-</li>"
    html_techs = "".join(
        f"<li><strong>{t.get('name') or t.get('id')}</strong> — {t.get('phone') or '-'} / {t.get('email') or '-'}</li>"
        for t in (wo.get("technicians") or [])
    ) or "<li>-</li>"
    html = f"""
    <div style="font-family:Segoe UI,Arial,sans-serif;color:#1a2433;line-height:1.5">
      <h2 style="margin:0 0 8px;color:#0048a8">Work Order {wo['wo_number']}</h2>
      <p style="margin:0 0 16px;color:#6b7a8d">{site}</p>
      <table style="border-collapse:collapse;margin-bottom:16px">
        <tr><td style="padding:4px 12px 4px 0;color:#6b7a8d">Kategori</td><td><strong>{wo.get('category') or '-'}</strong></td></tr>
        <tr><td style="padding:4px 12px 4px 0;color:#6b7a8d">Tanggal</td><td><strong>{wo['work_date']}</strong></td></tr>
        <tr><td style="padding:4px 12px 4px 0;color:#6b7a8d">Waktu</td><td><strong>{wo['work_time']}</strong></td></tr>
      </table>
      <h3 style="margin:0 0 8px;font-size:15px">Aset yang dikerjakan</h3>
      <ul style="margin:0 0 16px;padding-left:18px">{html_assets}</ul>
      <h3 style="margin:0 0 8px;font-size:15px">Teknisi ditugaskan</h3>
      <ul style="margin:0 0 16px;padding-left:18px">{html_techs}</ul>
      <h3 style="margin:0 0 8px;font-size:15px">Catatan</h3>
      <p style="margin:0 0 16px;white-space:pre-wrap">{notes}</p>
      <p style="margin:0;color:#6b7a8d;font-size:12px">Dikirim otomatis oleh Simplo Monitor</p>
    </div>
    """
    return subject, text, html


def _email_work_order_to_technicians(wo: dict) -> dict:
    sent: list[str] = []
    skipped: list[str] = []
    errors: list[str] = []
    subject, text, html = _format_wo_email(wo)
    for tech in wo.get("technicians") or []:
        email = str(tech.get("email") or "").strip()
        name = tech.get("name") or tech.get("id")
        if not email:
            skipped.append(str(name))
            continue
        try:
            send_email(
                to_emails=[email],
                subject=subject,
                body_text=text,
                body_html=html,
            )
            sent.append(email)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{name} <{email}>: {exc}")
    status_parts = []
    if sent:
        status_parts.append(f"terkirim:{len(sent)}")
    if skipped:
        status_parts.append(f"tanpa email:{len(skipped)}")
    if errors:
        status_parts.append(f"gagal:{len(errors)}")
    email_status = ", ".join(status_parts) if status_parts else "tidak ada penerima"
    update_work_order_email_status(wo["id"], email_status)
    return {
        "sent_to": sent,
        "skipped": skipped,
        "errors": errors,
        "email_status": email_status,
    }


def _queue_work_order_email(wo_id: str) -> None:
    """Mark email as queued and send in a background thread."""
    update_work_order_email_status(wo_id, "mengirim…")

    def runner() -> None:
        try:
            wo = get_work_order(wo_id)
            if not wo:
                return
            _email_work_order_to_technicians(wo)
        except Exception as exc:  # noqa: BLE001
            update_work_order_email_status(wo_id, f"gagal email: {exc}")

    threading.Thread(
        target=runner,
        name=f"wo-email-{wo_id[:8]}",
        daemon=True,
    ).start()


def _merge_notify_for_test(body: dict) -> dict:
    """Merge request body onto saved settings in-memory (does not persist)."""
    current = load_notify_settings()
    email_in = body.get("email") if isinstance(body.get("email"), dict) else {}
    tg_in = body.get("telegram") if isinstance(body.get("telegram"), dict) else {}

    email = dict(current.get("email") or {})
    for key, val in email_in.items():
        if key == "smtp_password" and (
            not str(val or "").strip() or str(val).strip() == "********"
        ):
            continue
        email[key] = val

    telegram = dict(current.get("telegram") or {})
    for key, val in tg_in.items():
        if key == "bot_token" and (
            not str(val or "").strip() or str(val).strip() == "********"
        ):
            continue
        telegram[key] = val

    return {"email": email, "telegram": telegram}
from camera_monitor import apply_direct_cctv_status
from nx_client import NxClient, normalize_device
from pdf_report import build_incident_pdf
from router_monitor import probe_router

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip("'").strip('"')
        os.environ.setdefault(key, val)


load_env(ROOT / ".env")

CONFIG = {
    "nx_host": os.environ.get("NX_HOST", "https://127.0.0.1:7001"),
    "nx_username": os.environ.get("NX_USERNAME", "admin"),
    "nx_password": os.environ.get("NX_PASSWORD", ""),
    "app_host": os.environ.get("APP_HOST", "0.0.0.0"),
    "app_port": int(os.environ.get("APP_PORT", "8080")),
    "site_name": os.environ.get("SITE_NAME", "Simplo System"),
    "site_site": os.environ.get("SITE_SITE", "Menara Kirana"),
    "site_org": os.environ.get("SITE_ORG", "MK Manajemen Gedung"),
    "poll_seconds": int(os.environ.get("POLL_SECONDS", "10")),
    "demo_fallback": os.environ.get("DEMO_FALLBACK", "true").lower()
    in {"1", "true", "yes"},
    "router_enabled": os.environ.get("ROUTER_MONITOR", "true").lower()
    in {"1", "true", "yes"},
    "router_ip": os.environ.get("ROUTER_IP", "192.168.1.1"),
    "router_username": os.environ.get("ROUTER_USERNAME", ""),
    "router_password": os.environ.get("ROUTER_PASSWORD", ""),
    "router_name": os.environ.get("ROUTER_NAME", "WIFI-GW-01"),
    "router_location": os.environ.get("ROUTER_LOCATION", "Gateway WiFi CMMS"),
}

_cache_lock = threading.Lock()
_cache: dict = {
    "devices": [],
    "updated_at": None,
    "source": "none",
    "error": None,
    "events": [],  # recent status-change events for detail timeline
    "router": None,
}
_prev_status: dict[str, str] = {}
_prev_health: dict[str, str] = {}
_seen_devices: set[str] = set()
_router_fail_streak = 0
_router_last_good: dict | None = None
_router_api_cache: dict = {"at": 0.0, "data": {}}
_ROUTER_API_TTL_SECONDS = 30.0
_auto_wo_lock = threading.Lock()
_auto_wo_busy = False


init_db()
init_auth_db()
seed_demo_if_empty()

_AUTH_PUBLIC_EXACT = {
    "/login",
    "/login.html",
    "/api/auth/login",
    "/api/health",
}
_AUTH_PUBLIC_PREFIXES = ("/static/",)


def demo_devices() -> list[dict]:
    samples = [
        ("CCTV-L01-04", "Lobby Utama", "issue", False, False, "Hikvision", "DS-2CD2143"),
        ("CCTV-P02-11", "Parkir Basement B2", "issue", False, False, "Hikvision", "DS-2CD2143"),
        ("NVR-RK-01", "Ruang Server Lt.2", "attention", True, False, "Network Optix", "NX Server"),
        ("ACS-G01-02", "Gate Lobby", "attention", True, False, "Hikvision", "DS-K2602"),
        ("CCTV-R03-07", "Rooftop Area A", "attention", True, False, "Dahua", "IPC-HFW2431"),
        ("ALM-F01-03", "Panel Fire Lt.1", "attention", True, False, "Bosch", "FPA-5000"),
    ]
    healthy = [
        ("CCTV-L01-01", "Lobby Utara"),
        ("CCTV-L01-02", "Lobby Selatan"),
        ("CCTV-L01-03", "Resepsionis"),
        ("CCTV-L02-01", "Koridor Lt.2 A"),
        ("CCTV-L02-02", "Koridor Lt.2 B"),
        ("CCTV-L02-03", "Lift Lobby Lt.2"),
        ("CCTV-L03-01", "Koridor Lt.3 A"),
        ("CCTV-L03-02", "Koridor Lt.3 B"),
        ("CCTV-P01-01", "Parkir P1 Entry"),
        ("CCTV-P01-02", "Parkir P1 Exit"),
        ("CCTV-P02-01", "Basement Ramp"),
        ("CCTV-P02-02", "Basement Corner"),
        ("ACS-G01-01", "Main Entrance"),
        ("ACS-G02-01", "Staff Entrance"),
        ("ALM-F02-01", "Panel Fire Lt.2"),
        ("CCTV-R01-01", "Rooftop North"),
        ("CCTV-R01-02", "Rooftop South"),
        ("CCTV-M01-01", "Meeting Room A"),
    ]
    devices = []
    for name, loc, health, online, recording, vendor, model in samples:
        devices.append(
            {
                "id": name.lower().replace("-", ""),
                "name": name,
                "location": loc,
                "type": "CCTV"
                if name.startswith("CCTV") or name.startswith("NVR")
                else ("Access" if name.startswith("ACS") else "Alarm"),
                "vendor": vendor,
                "model": model,
                "ip": f"192.168.10.{len(devices)+10}",
                "mac": "",
                "status_raw": "Offline"
                if health == "issue"
                else ("Online" if not recording else "Recording"),
                "online": online,
                "recording": recording,
                "schedule_enabled": True,
                "health": health,
                "server_id": "local",
            }
        )
    for i, (name, loc) in enumerate(healthy):
        devices.append(
            {
                "id": f"demo{i}",
                "name": name,
                "location": loc,
                "type": "CCTV"
                if name.startswith("CCTV")
                else ("Access" if name.startswith("ACS") else "Alarm"),
                "vendor": "Hikvision",
                "model": "DS-2CD2143",
                "ip": f"192.168.10.{50+i}",
                "mac": "",
                "status_raw": "Recording",
                "online": True,
                "recording": True,
                "schedule_enabled": True,
                "health": "healthy",
                "server_id": "local",
            }
        )
    return devices


def _describe_issue(d: dict) -> str:
    if d.get("type") == "Network" or d.get("server_id") == "router":
        r = d.get("router") or {}
        parts = [
            f"Status: {d.get('status_raw') or '-'}.",
            f"Router: {'Online' if d.get('online') else 'Offline'}.",
            f"Internet: {'Terhubung' if d.get('internet_ok') else 'Terputus'}.",
        ]
        if r.get("ping_ms") is not None:
            parts.append(f"Latency router: {r['ping_ms']} ms.")
        if r.get("internet_latency_ms") is not None:
            parts.append(f"Latency internet: {r['internet_latency_ms']} ms.")
        if r.get("http_ok") is False:
            parts.append("UI admin router tidak merespons.")
        if r.get("ssid"):
            parts.append(f"SSID: {r['ssid']}.")
        if d.get("ip"):
            parts.append(f"IP gateway: {d['ip']}.")
        if d.get("mac"):
            parts.append(f"MAC: {d['mac']}.")
        if not d.get("online"):
            parts.append("Gateway tidak terjangkau — periksa WiFi/power router.")
        elif not d.get("internet_ok"):
            parts.append(
                "Gateway online tetapi tidak ada koneksi internet (ICMP/DNS gagal)."
            )
        return " ".join(parts)

    parts = [
        f"Status NX: {d.get('status_raw') or '-'}.",
        f"Koneksi: {'Online' if d.get('online') else 'Offline'}.",
        f"Recording: {'Aktif' if d.get('recording') else 'Tidak aktif'}.",
    ]
    if d.get("online") and not d.get("recording"):
        parts.append("Kamera online tetapi tidak merekam.")
    if d.get("online") and not d.get("schedule_enabled"):
        parts.append("Jadwal rekam tidak aktif.")
    if d.get("schedule_enabled") and d.get("online") and not d.get("recording"):
        parts.append("Jadwal rekam aktif tetapi kamera tidak merekam.")
    if not d.get("online"):
        parts.append(
            "Tidak ada stream dari perangkat. Periksa jaringan, power, atau kredensial kamera."
        )
    if d.get("ip"):
        parts.append(f"IP: {d['ip']}.")
    if d.get("location"):
        parts.append(f"Lokasi/group: {d['location']}.")
    return " ".join(parts)


def _log_health_transition(
    d: dict,
    prev_health: str | None,
    source: str,
    *,
    initial: bool = False,
    prev_status_raw: str | None = None,
) -> dict | None:
    """Write persistent incident history + return timeline event if any."""
    health = d.get("health") or "healthy"
    name = d.get("name") or "Unknown"
    loc = d.get("location") or ""
    ip = d.get("ip") or ""
    status = d.get("status_raw") or ""

    if initial:
        if health == "issue":
            row = add_log(
                device_id=d["id"],
                device_name=name,
                location=loc,
                ip=ip,
                event_type="started",
                severity="issue",
                status_from="Unknown",
                status_to=status,
                title="Gangguan terdeteksi saat monitoring dimulai",
                detail=_describe_issue(d),
                source=source,
            )
            return {
                "device_id": d["id"],
                "device_name": name,
                "time": datetime.now().strftime("%H:%M"),
                "tone": "red",
                "text": row["title"],
            }
        if health == "attention":
            row = add_log(
                device_id=d["id"],
                device_name=name,
                location=loc,
                ip=ip,
                event_type="attention_started",
                severity="attention",
                status_from="Unknown",
                status_to=status,
                title="Perhatian terdeteksi saat monitoring dimulai",
                detail=_describe_issue(d),
                source=source,
            )
            return {
                "device_id": d["id"],
                "device_name": name,
                "time": datetime.now().strftime("%H:%M"),
                "tone": "orange",
                "text": row["title"],
            }
        return None

    if not prev_health or prev_health == health:
        return None

    # Issue started
    if health == "issue" and prev_health != "issue":
        row = add_log(
            device_id=d["id"],
            device_name=name,
            location=loc,
            ip=ip,
            event_type="started",
            severity="issue",
            status_from=prev_status_raw or prev_health or "",
            status_to=status,
            title="Gangguan dimulai",
            detail=(
                f"Status berubah dari '{prev_status_raw or prev_health}' menjadi gangguan. "
                + _describe_issue(d)
            ),
            source=source,
        )
        return {
            "device_id": d["id"],
            "device_name": name,
            "time": datetime.now().strftime("%H:%M"),
            "tone": "red",
            "text": f"Gangguan dimulai ({status})",
        }

    # Issue resolved -> normal/attention
    if prev_health == "issue" and health != "issue":
        recovered = "normal" if health == "healthy" else "perhatian"
        row = add_log(
            device_id=d["id"],
            device_name=name,
            location=loc,
            ip=ip,
            event_type="resolved",
            severity="healthy" if health == "healthy" else "attention",
            status_from=prev_status_raw or "Offline",
            status_to=status,
            title="Gangguan berakhir — status kembali "
            + ("normal" if health == "healthy" else "perhatian"),
            detail=(
                f"Perangkat pulih dari gangguan ke kondisi {recovered}. "
                f"Status NX sekarang: {status}. "
                + _describe_issue(d)
            ),
            source=source,
        )
        return {
            "device_id": d["id"],
            "device_name": name,
            "time": datetime.now().strftime("%H:%M"),
            "tone": "green" if health == "healthy" else "orange",
            "text": row["title"],
        }

    # Attention started (not from issue — issue path handled above)
    if health == "attention" and prev_health == "healthy":
        row = add_log(
            device_id=d["id"],
            device_name=name,
            location=loc,
            ip=ip,
            event_type="attention_started",
            severity="attention",
            status_from=prev_status_raw or prev_health or "",
            status_to=status,
            title="Perhatian dimulai",
            detail=_describe_issue(d),
            source=source,
        )
        return {
            "device_id": d["id"],
            "device_name": name,
            "time": datetime.now().strftime("%H:%M"),
            "tone": "orange",
            "text": f"Perhatian dimulai ({status})",
        }

    # Attention resolved to healthy
    if prev_health == "attention" and health == "healthy":
        row = add_log(
            device_id=d["id"],
            device_name=name,
            location=loc,
            ip=ip,
            event_type="attention_resolved",
            severity="healthy",
            status_from=prev_status_raw or "Online",
            status_to=status,
            title="Perhatian berakhir — status normal",
            detail=(
                f"Kondisi perhatian selesai. Status NX: {status}. "
                + _describe_issue(d)
            ),
            source=source,
        )
        return {
            "device_id": d["id"],
            "device_name": name,
            "time": datetime.now().strftime("%H:%M"),
            "tone": "green",
            "text": row["title"],
        }

    return None


def _track_events(devices: list[dict], source: str = "nx") -> None:
    global _prev_status, _prev_health, _seen_devices
    now = datetime.now().strftime("%H:%M")
    events = list(_cache.get("events") or [])
    for d in devices:
        key = d["id"]
        cur = f"{d['status_raw']}|{d['recording']}"
        prev = _prev_status.get(key)
        prev_health = _prev_health.get(key)
        first_seen = key not in _seen_devices
        prev_status_raw = (prev or "|").split("|", 1)[0] if prev else None

        if first_seen:
            _seen_devices.add(key)
            _prev_status[key] = cur
            _prev_health[key] = d.get("health") or "healthy"
            ev = _log_health_transition(d, None, source, initial=True)
            if ev:
                events.insert(0, ev)
            continue

        if prev != cur or prev_health != d.get("health"):
            if prev != cur:
                events.insert(
                    0,
                    {
                        "device_id": key,
                        "device_name": d["name"],
                        "time": now,
                        "tone": "red"
                        if not d["online"]
                        else ("green" if d["recording"] else "orange"),
                        "text": f"Status berubah: {prev_status_raw} → {d['status_raw']}",
                    },
                )
            ev = _log_health_transition(
                d, prev_health, source, prev_status_raw=prev_status_raw
            )
            if ev:
                if not events or events[0].get("text") != ev.get("text"):
                    events.insert(0, ev)
            _prev_status[key] = cur
            _prev_health[key] = d.get("health") or "healthy"
    _cache["events"] = events[:80]


def fetch_devices() -> tuple[list[dict], str, str | None]:
    password = CONFIG["nx_password"]
    if not password or password.startswith("ganti_"):
        if CONFIG["demo_fallback"]:
            return demo_devices(), "demo", "NX_PASSWORD belum diisi — menampilkan data demo"
        return [], "none", "NX_PASSWORD belum dikonfigurasi di file .env"

    client = NxClient(
        CONFIG["nx_host"],
        CONFIG["nx_username"],
        password,
    )
    try:
        raw = client.list_devices()
        devices = [normalize_device(d) for d in raw]
        # Prefer cameras / video devices; keep all if empty filter
        cams = [d for d in devices if d.get("type") != "unknown"]
        return cams, "nx", None
    except Exception as exc:  # noqa: BLE001
        if CONFIG["demo_fallback"]:
            return demo_devices(), "demo", f"Gagal koneksi NX: {exc}"
        return [], "error", str(exc)


def _merge_cached_router_api(device: dict) -> dict:
    """Reuse recently scraped router API fields on quick probes."""
    cached = _router_api_cache.get("data") or {}
    if not cached:
        return device
    router = dict(device.get("router") or {})
    for key, val in cached.items():
        if key.startswith("api") or key in {"api_ok", "api_error"}:
            continue
        if router.get(key) in (None, "", [], {}):
            router[key] = val
    if cached.get("mac_addr") and not device.get("mac"):
        device["mac"] = str(cached["mac_addr"]).lower()
    device["router"] = router
    return device


def _store_router_api_cache(device: dict) -> None:
    router = device.get("router") or {}
    if not router:
        return
    # Keep detail fields that come from admin API scrape.
    keep_keys = (
        "ssid",
        "wifi_ssids",
        "wifi_band",
        "wifi_encryption",
        "sw_version",
        "hw_version",
        "baseband_version",
        "imei",
        "imsi",
        "iccid",
        "msisdn",
        "sim_status",
        "pin_status",
        "network_name",
        "roaming",
        "sys_mode",
        "data_mode",
        "rssi",
        "active_clients",
        "active_lan_clients",
        "active_wifi_24g",
        "wan_ip",
        "wan_connected",
        "mac_addr",
        "api_ok",
    )
    data = {k: router.get(k) for k in keep_keys if router.get(k) not in (None, "", [], {})}
    if data:
        _router_api_cache["at"] = time.time()
        _router_api_cache["data"] = data


def fetch_router_device(*, quick: bool = True) -> dict | None:
    """Probe router with hysteresis: one failed poll does not flip to Offline."""
    global _router_fail_streak, _router_last_good
    if not CONFIG["router_enabled"]:
        return None
    include_api = (time.time() - float(_router_api_cache.get("at") or 0)) >= _ROUTER_API_TTL_SECONDS
    try:
        device = probe_router(
            ip=CONFIG["router_ip"],
            username=CONFIG["router_username"],
            password=CONFIG["router_password"],
            name=CONFIG["router_name"],
            location=CONFIG["router_location"],
            quick=quick,
            include_api=include_api,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[router] probe error: {exc}", flush=True)
        device = {
            "id": f"router-{CONFIG['router_ip'].replace('.', '-')}",
            "name": CONFIG["router_name"],
            "location": CONFIG["router_location"],
            "type": "Network",
            "vendor": "LTE Wireless Router",
            "model": "Probe error",
            "ip": CONFIG["router_ip"],
            "mac": "",
            "status_raw": "Error",
            "online": False,
            "recording": False,
            "schedule_enabled": False,
            "health": "issue",
            "server_id": "router",
            "internet_ok": False,
            "admin_url": f"http://{CONFIG['router_ip']}/",
            "router": {"api_ok": False, "api_error": str(exc)},
        }

    if include_api:
        _store_router_api_cache(device)
    else:
        device = _merge_cached_router_api(device)

    # Recover immediately; require 2 consecutive offline/unreachable polls
    # before publishing Offline (absorbs brief WiFi blips on the CMMS host).
    if device.get("online"):
        _router_fail_streak = 0
        _router_last_good = device
        return device

    _router_fail_streak += 1
    if _router_fail_streak < 2 and _router_last_good is not None:
        held = dict(_router_last_good)
        held_router = dict(held.get("router") or {})
        held_router["probe_held"] = True
        held_router["probe_fail_streak"] = _router_fail_streak
        held["router"] = held_router
        return held

    return device


def _pick_free_technician(category: str, busy_tech_ids: set[str]) -> dict | None:
    candidates = [
        t
        for t in list_technicians()
        if category in (t.get("skills") or []) and t.get("id") not in busy_tech_ids
    ]
    candidates.sort(key=lambda t: (t.get("name") or "").lower())
    return candidates[0] if candidates else None


def process_auto_work_orders(devices: list[dict]) -> None:
    """Create WO for assets in gangguan/perhatian longer than configured delay."""
    global _auto_wo_busy
    settings = load_auto_wo_settings()
    delay_minutes = int(settings.get("delay_minutes") or 0)
    if delay_minutes <= 0:
        return
    try:
        cooldown_minutes = int(settings.get("cooldown_minutes", 60))
    except (TypeError, ValueError):
        cooldown_minutes = 60
    if cooldown_minutes < 0:
        cooldown_minutes = 0

    with _auto_wo_lock:
        if _auto_wo_busy:
            return
        _auto_wo_busy = True

    try:
        now = datetime.now()
        threshold = timedelta(minutes=delay_minutes)
        cooldown = timedelta(minutes=cooldown_minutes) if cooldown_minutes > 0 else None
        busy_assets = open_work_order_asset_ids()
        busy_techs = open_work_order_technician_ids()

        for d in devices:
            health = str(d.get("health") or "")
            # Trigger on gangguan (issue) and perlu perhatian (attention)
            if health not in {"issue", "attention"}:
                continue
            status_raw = str(d.get("status_raw") or "")
            if status_raw == "Not monitored":
                continue
            asset_id = str(d.get("id") or "")
            if not asset_id or asset_id in busy_assets:
                continue
            if not get_asset(asset_id):
                continue

            if cooldown is not None:
                last_wo_at = latest_work_order_created_at_for_asset(asset_id)
                if last_wo_at and now - last_wo_at < cooldown:
                    continue

            started_at = get_open_abnormal_started_at(asset_id, health)
            if not started_at:
                continue
            if now - started_at < threshold:
                continue

            category = str(d.get("category") or d.get("type") or "").strip()
            if category not in ASSET_CATEGORIES:
                continue

            tech = _pick_free_technician(category, busy_techs)
            if not tech:
                print(
                    f"[auto-wo] skip {d.get('name') or asset_id}: "
                    f"tidak ada teknisi bebas untuk {category}",
                    flush=True,
                )
                continue

            kondisi = "gangguan" if health == "issue" else "perlu perhatian"
            notes = (
                f"Auto Generate WO — {kondisi} terdeteksi sejak "
                f"{started_at.isoformat(timespec='seconds')} "
                f"({status_raw or health}). "
                f"Ambang: {delay_minutes} menit · Jeda: {cooldown_minutes} menit."
            )
            try:
                wo = create_work_order(
                    {
                        "category": category,
                        "work_date": now.strftime("%Y-%m-%d"),
                        "work_time": now.strftime("%H:%M"),
                        "asset_ids": [asset_id],
                        "technician_ids": [tech["id"]],
                        "notes": notes,
                    }
                )
            except ValueError as exc:
                print(
                    f"[auto-wo] gagal buat WO untuk {d.get('name') or asset_id}: {exc}",
                    flush=True,
                )
                continue

            busy_assets.add(asset_id)
            busy_techs.add(str(tech["id"]))
            _queue_work_order_email(wo["id"])
            print(
                f"[auto-wo] {wo.get('wo_number')} dibuat ({kondisi}) untuk "
                f"{d.get('name') or asset_id} → {tech.get('name') or tech['id']}",
                flush=True,
            )
    finally:
        with _auto_wo_lock:
            _auto_wo_busy = False


def refresh_cache() -> None:
    t0 = time.monotonic()
    with ThreadPoolExecutor(max_workers=2) as pool:
        nx_fut = pool.submit(fetch_devices)
        router_fut = pool.submit(fetch_router_device, quick=True)
        devices, source, error = nx_fut.result()
        router = router_fut.result()
    if router:
        # Keep router first so it is easy to spot on the dashboard
        devices = [router] + [d for d in devices if d.get("id") != router["id"]]

    # Bootstrap inventory once so existing deployments keep working.
    # After that, add/remove only via Manajemen Asset (or Impor Live).
    if count_assets() == 0 and devices:
        try:
            seed_assets_from_devices(devices)
        except Exception as exc:  # noqa: BLE001
            print(f"[assets] seed error: {exc}", flush=True)

    devices = merge_assets_with_live(devices)
    try:
        devices = apply_direct_cctv_status(devices, timeout=0.7)
    except Exception as exc:  # noqa: BLE001
        print(f"[cctv-ip] probe error: {exc}", flush=True)

    with _cache_lock:
        _track_events(devices, source=source)
        _cache["devices"] = devices
        _cache["updated_at"] = datetime.now().isoformat(timespec="seconds")
        _cache["source"] = source
        _cache["error"] = error
        _cache["router"] = router

    # Don't block the poll loop / API refresh on auto-WO creation.
    def _auto_wo_job(devs: list[dict]) -> None:
        try:
            process_auto_work_orders(devs)
        except Exception as exc:  # noqa: BLE001
            print(f"[auto-wo] error: {exc}", flush=True)

    threading.Thread(
        target=_auto_wo_job,
        args=(list(devices),),
        name="auto-wo",
        daemon=True,
    ).start()
    elapsed = time.monotonic() - t0
    if elapsed > CONFIG["poll_seconds"]:
        print(f"[poll] refresh took {elapsed:.2f}s", flush=True)


def _device_catalog() -> list[dict[str, str]]:
    with _cache_lock:
        live = list(_cache["devices"])
    devices_map = {d["id"]: d["name"] for d in live}
    for d in list_devices_in_logs():
        devices_map.setdefault(d["id"], d["name"])
    return [{"id": k, "name": v} for k, v in sorted(devices_map.items(), key=lambda x: x[1].lower())]


def _report_query_from_params(qs: dict) -> dict:
    today = datetime.now().date()
    date_from = (qs.get("from") or [None])[0] or (today - timedelta(days=7)).isoformat()
    date_to = (qs.get("to") or [None])[0] or today.isoformat()
    device_id = (qs.get("device") or [None])[0] or ""
    if device_id in {"", "all", "*"}:
        device_id = None
    logs = query_logs(date_from=date_from, date_to=date_to, device_id=device_id)
    devices = _device_catalog()
    return {
        "filters": {
            "from": date_from,
            "to": date_to,
            "device": device_id or "all",
        },
        "devices": devices,
        "logs": logs,
        "count": len(logs),
    }


def _statistik_query_from_params(qs: dict) -> dict:
    today = datetime.now().date()
    date_from = (qs.get("from") or [None])[0] or (today - timedelta(days=7)).isoformat()
    date_to = (qs.get("to") or [None])[0] or today.isoformat()
    device_id = (qs.get("device") or [None])[0] or ""
    if device_id in {"", "all", "*"}:
        device_id = None
    return compute_statistik(
        date_from=date_from,
        date_to=date_to,
        device_id=device_id,
        device_catalog=_device_catalog(),
    )


def summarize(devices: list[dict]) -> dict:
    total = len(devices)
    healthy = sum(1 for d in devices if d["health"] == "healthy")
    attention = sum(1 for d in devices if d["health"] == "attention")
    issue = sum(1 for d in devices if d["health"] == "issue")
    online = sum(1 for d in devices if d["online"])
    recording = sum(1 for d in devices if d["recording"])
    pct = round((healthy / total) * 100) if total else 0
    return {
        "total": total,
        "healthy": healthy,
        "healthy_pct": pct,
        "attention": attention,
        "issue": issue,
        "online": online,
        "recording": recording,
        "offline": total - online,
    }


def build_payload() -> dict:
    with _cache_lock:
        devices = [dict(d) for d in _cache["devices"]]
        updated_at = _cache["updated_at"]
        source = _cache["source"]
        error = _cache["error"]
        events = list(_cache["events"])
        router = _cache.get("router")
    meta_map = get_all_device_meta()
    for device in devices:
        enrich_device_meta(device, meta_map.get(device.get("id") or ""))
    return {
        "meta": {
            "site_name": CONFIG["site_name"],
            "site_site": CONFIG["site_site"],
            "site_org": CONFIG["site_org"],
            "poll_seconds": CONFIG["poll_seconds"],
            "updated_at": updated_at,
            "source": source,
            "error": error,
            "nx_host": CONFIG["nx_host"],
            "router_ip": CONFIG["router_ip"],
            "router_monitor": CONFIG["router_enabled"],
        },
        "summary": summarize(devices),
        "devices": devices,
        "router": router,
        "events": events,
    }


MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".json": "application/json; charset=utf-8",
}


class Handler(BaseHTTPRequestHandler):
    server_version = "SimploMonitor/1.0"

    def log_message(self, fmt: str, *args) -> None:  # quieter logs
        sys_stderr = __import__("sys").stderr
        sys_stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    def _send(
        self,
        code: int,
        body: bytes,
        content_type: str,
        *,
        headers: list[tuple[str, str]] | None = None,
    ) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for key, val in headers or []:
            self.send_header(key, val)
        self.end_headers()
        self.wfile.write(body)

    def _json(
        self,
        code: int,
        obj: object,
        *,
        cookies: list[str] | None = None,
    ) -> None:
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        headers = [("Set-Cookie", c) for c in (cookies or [])]
        self._send(code, data, "application/json; charset=utf-8", headers=headers)

    def _redirect(self, location: str, *, cookies: list[str] | None = None) -> None:
        headers = [("Location", location)]
        for c in cookies or []:
            headers.append(("Set-Cookie", c))
        self._send(302, b"", "text/plain; charset=utf-8", headers=headers)

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        if not raw:
            return {}
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"JSON tidak valid: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("body harus berupa objek JSON")
        return data

    def _cookies(self) -> dict[str, str]:
        raw = self.headers.get("Cookie") or ""
        out: dict[str, str] = {}
        for part in raw.split(";"):
            if "=" not in part:
                continue
            key, _, val = part.strip().partition("=")
            if key:
                out[key] = val
        return out

    def _session_token(self) -> str | None:
        token = self._cookies().get(SESSION_COOKIE) or ""
        return token or None

    def _current_user(self) -> dict | None:
        return get_user_by_session(self._session_token())

    def _is_public_path(self, path: str) -> bool:
        if path in _AUTH_PUBLIC_EXACT:
            return True
        return any(path.startswith(prefix) for prefix in _AUTH_PUBLIC_PREFIXES)

    def _require_login(self, path: str) -> dict | None:
        """Return current user, or send 401/redirect and return None."""
        if self._is_public_path(path):
            return {"_public": True}
        user = self._current_user()
        if user:
            return user
        if path.startswith("/api/"):
            self._json(401, {"ok": False, "error": "login diperlukan"})
            return None
        self._redirect("/login")
        return None

    def _require_admin(self, user: dict) -> bool:
        if user.get("role") == "administrator":
            return True
        self._json(403, {"ok": False, "error": "hanya administrator"})
        return False

    def do_PUT(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        user = self._require_login(path)
        if user is None:
            return
        if path.startswith("/api/users/"):
            if user.get("_public") or not self._require_admin(user):
                return
            user_id = unquote(path[len("/api/users/") :])
            if not user_id or "/" in user_id:
                return self._json(400, {"ok": False, "error": "user id tidak valid"})
            try:
                body = self._read_json_body()
                saved = upsert_user(body, user_id=user_id)
            except ValueError as exc:
                return self._json(400, {"ok": False, "error": str(exc)})
            return self._json(200, {"ok": True, "user": saved})
        if path.startswith("/api/assets/"):
            asset_id = unquote(path[len("/api/assets/") :])
            if not asset_id or "/" in asset_id:
                return self._json(400, {"error": "asset id tidak valid"})
            try:
                body = self._read_json_body()
                saved = upsert_asset(body, asset_id=asset_id)
            except ValueError as exc:
                return self._json(400, {"error": str(exc)})
            return self._json(200, {"ok": True, "asset": saved})
        if path.startswith("/api/technicians/"):
            tech_id = unquote(path[len("/api/technicians/") :])
            if not tech_id or "/" in tech_id:
                return self._json(400, {"error": "technician id tidak valid"})
            try:
                body = self._read_json_body()
                saved = upsert_technician(body, tech_id=tech_id)
            except ValueError as exc:
                return self._json(400, {"error": str(exc)})
            return self._json(200, {"ok": True, "technician": saved})
        if path.startswith("/api/pm-schedules/"):
            schedule_id = unquote(path[len("/api/pm-schedules/") :])
            if not schedule_id or "/" in schedule_id:
                return self._json(400, {"ok": False, "error": "jadwal id tidak valid"})
            try:
                body = self._read_json_body()
                saved = upsert_pm_schedule(body, schedule_id=schedule_id)
            except ValueError as exc:
                return self._json(400, {"ok": False, "error": str(exc)})
            return self._json(200, {"ok": True, "schedule": saved})
        if path == "/api/settings/notifications":
            try:
                body = self._read_json_body()
                saved = save_notify_settings(body)
            except ValueError as exc:
                return self._json(400, {"error": str(exc)})
            return self._json(200, {"ok": True, "settings": public_notify_settings(saved)})
        if path == "/api/settings/auto-wo":
            try:
                body = self._read_json_body()
                saved = save_auto_wo_settings(body)
            except ValueError as exc:
                return self._json(400, {"ok": False, "error": str(exc)})
            return self._json(200, {"ok": True, "settings": saved})
        self._json(404, {"error": "not found"})

    def do_DELETE(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        user = self._require_login(path)
        if user is None:
            return
        if path.startswith("/api/users/"):
            if user.get("_public") or not self._require_admin(user):
                return
            user_id = unquote(path[len("/api/users/") :])
            if not user_id or "/" in user_id:
                return self._json(400, {"ok": False, "error": "user id tidak valid"})
            if user_id == user.get("id"):
                return self._json(400, {"ok": False, "error": "tidak bisa menghapus akun sendiri"})
            try:
                if not delete_user(user_id):
                    return self._json(404, {"ok": False, "error": "user tidak ditemukan"})
            except ValueError as exc:
                return self._json(400, {"ok": False, "error": str(exc)})
            return self._json(200, {"ok": True})
        if path.startswith("/api/assets/"):
            asset_id = unquote(path[len("/api/assets/") :])
            if not asset_id or "/" in asset_id:
                return self._json(400, {"error": "asset id tidak valid"})
            if not delete_asset(asset_id):
                return self._json(404, {"error": "aset tidak ditemukan"})
            return self._json(200, {"ok": True})
        if path.startswith("/api/technicians/"):
            tech_id = unquote(path[len("/api/technicians/") :])
            if not tech_id or "/" in tech_id:
                return self._json(400, {"error": "technician id tidak valid"})
            if not delete_technician(tech_id):
                return self._json(404, {"error": "teknisi tidak ditemukan"})
            return self._json(200, {"ok": True})
        if path.startswith("/api/work-orders/"):
            wo_id = unquote(path[len("/api/work-orders/") :])
            if not wo_id or "/" in wo_id:
                return self._json(400, {"error": "work order id tidak valid"})
            if not delete_work_order(wo_id):
                return self._json(404, {"error": "work order tidak ditemukan"})
            return self._json(200, {"ok": True})
        if path.startswith("/api/pm-schedules/"):
            rest = unquote(path[len("/api/pm-schedules/") :])
            parts = [p for p in rest.split("/") if p]
            if len(parts) == 3 and parts[1] == "records":
                if not delete_pm_service_record(parts[2]):
                    return self._json(404, {"ok": False, "error": "service record tidak ditemukan"})
                return self._json(200, {"ok": True})
            if len(parts) == 1:
                if not delete_pm_schedule(parts[0]):
                    return self._json(404, {"ok": False, "error": "jadwal PM tidak ditemukan"})
                return self._json(200, {"ok": True})
            return self._json(400, {"ok": False, "error": "path tidak valid"})
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/auth/login":
            try:
                body = self._read_json_body()
            except ValueError as exc:
                return self._json(400, {"ok": False, "error": str(exc)})
            user = authenticate(str(body.get("username") or ""), str(body.get("password") or ""))
            if not user:
                return self._json(401, {"ok": False, "error": "username atau password salah"})
            token = create_session(user["id"])
            return self._json(
                200,
                {"ok": True, "user": user},
                cookies=[session_cookie_header(token)],
            )
        if path == "/api/auth/logout":
            destroy_session(self._session_token())
            return self._json(
                200,
                {"ok": True},
                cookies=[session_cookie_header("", clear=True)],
            )

        user = self._require_login(path)
        if user is None:
            return
        if path == "/api/users":
            if user.get("_public") or not self._require_admin(user):
                return
            try:
                body = self._read_json_body()
                saved = upsert_user(body)
            except ValueError as exc:
                return self._json(400, {"ok": False, "error": str(exc)})
            return self._json(201, {"ok": True, "user": saved})
        if path == "/api/assets":
            try:
                body = self._read_json_body()
                saved = upsert_asset(body)
            except ValueError as exc:
                return self._json(400, {"error": str(exc)})
            return self._json(201, {"ok": True, "asset": saved})
        if path == "/api/technicians":
            try:
                body = self._read_json_body()
                saved = upsert_technician(body)
            except ValueError as exc:
                return self._json(400, {"error": str(exc)})
            return self._json(201, {"ok": True, "technician": saved})
        if path == "/api/work-orders":
            try:
                body = self._read_json_body()
                wo = create_work_order(body)
            except ValueError as exc:
                return self._json(400, {"ok": False, "error": str(exc)})
            _queue_work_order_email(wo["id"])
            wo = get_work_order(wo["id"]) or wo
            return self._json(
                201,
                {
                    "ok": True,
                    "work_order": wo,
                    "email": {"queued": True, "email_status": wo.get("email_status") or "mengirim…"},
                },
            )
        if path == "/api/pm-schedules":
            try:
                body = self._read_json_body()
                saved = upsert_pm_schedule(body)
            except ValueError as exc:
                return self._json(400, {"ok": False, "error": str(exc)})
            return self._json(201, {"ok": True, "schedule": saved})
        if path.startswith("/api/pm-schedules/") and path.endswith("/records"):
            rest = unquote(path[len("/api/pm-schedules/") : -len("/records")]).rstrip("/")
            if not rest or "/" in rest:
                return self._json(400, {"ok": False, "error": "jadwal id tidak valid"})
            try:
                body = self._read_json_body()
                record = create_pm_service_record(rest, body)
                schedule = get_pm_schedule(rest)
            except ValueError as exc:
                return self._json(400, {"ok": False, "error": str(exc)})
            return self._json(
                201,
                {"ok": True, "record": record, "schedule": schedule},
            )
        if path.startswith("/api/work-orders/") and path.endswith("/resend-email"):
            wo_id = unquote(path[len("/api/work-orders/") : -len("/resend-email")])
            wo_id = wo_id.rstrip("/")
            if not wo_id or "/" in wo_id:
                return self._json(400, {"ok": False, "error": "work order id tidak valid"})
            wo = get_work_order(wo_id)
            if not wo:
                return self._json(404, {"ok": False, "error": "work order tidak ditemukan"})
            _queue_work_order_email(wo_id)
            wo = get_work_order(wo_id) or wo
            return self._json(
                200,
                {
                    "ok": True,
                    "work_order": wo,
                    "email": {"queued": True, "email_status": wo.get("email_status") or "mengirim…"},
                },
            )
        if path == "/api/assets/import-live":
            with _cache_lock:
                live = list(_cache["devices"])
            # Re-fetch raw live devices for import (before inventory filter)
            raw_devices, _, _ = fetch_devices()
            router = fetch_router_device()
            if router:
                raw_devices = [router] + [
                    d for d in raw_devices if d.get("id") != router["id"]
                ]
            try:
                added = seed_assets_from_devices(raw_devices or live)
            except ValueError as exc:
                return self._json(400, {"ok": False, "error": str(exc)})
            return self._json(
                200,
                {"ok": True, "added": added, "assets": list_assets()},
            )
        if path == "/api/settings/notifications/test-email":
            try:
                body = self._read_json_body()
                merged = _merge_notify_for_test(body) if body else load_notify_settings()
                result = send_test_email(merged)
            except ValueError as exc:
                return self._json(400, {"ok": False, "error": str(exc)})
            except Exception as exc:  # noqa: BLE001
                return self._json(500, {"ok": False, "error": str(exc)})
            return self._json(200, result)
        if path == "/api/settings/notifications/test-telegram":
            try:
                body = self._read_json_body()
                merged = _merge_notify_for_test(body) if body else load_notify_settings()
                result = send_test_telegram(merged)
            except ValueError as exc:
                return self._json(400, {"ok": False, "error": str(exc)})
            except Exception as exc:  # noqa: BLE001
                return self._json(500, {"ok": False, "error": str(exc)})
            return self._json(200, result)
        self._json(404, {"error": "not found"})

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path in {"/login", "/login.html"}:
            if self._current_user():
                return self._redirect("/")
            return self._serve_file(STATIC / "login.html")
        if path.startswith("/static/"):
            rel = path[len("/static/") :]
            return self._serve_file(STATIC / rel)
        if path == "/api/auth/me":
            user = self._current_user()
            if not user:
                return self._json(401, {"ok": False, "error": "login diperlukan"})
            return self._json(
                200,
                {
                    "ok": True,
                    "user": user,
                    "menu_options": [{"id": k, "label": lab} for k, lab in MENU_OPTIONS],
                },
            )
        if path == "/api/health":
            return self._json(
                200,
                {
                    "ok": True,
                    "source": _cache.get("source"),
                    "updated_at": _cache.get("updated_at"),
                    "error": _cache.get("error"),
                },
            )

        user = self._require_login(path)
        if user is None:
            return

        if path in {"/", "/index.html"}:
            return self._serve_file(STATIC / "index.html")
        if path == "/api/users":
            if not self._require_admin(user):
                return
            return self._json(
                200,
                {
                    "ok": True,
                    "users": list_users(),
                    "menu_options": [
                        {"id": k, "label": lab}
                        for k, lab in MENU_OPTIONS
                        if k != "users"
                    ],
                    "roles": ["administrator", "operator"],
                },
            )
        if path.startswith("/api/users/"):
            if not self._require_admin(user):
                return
            user_id = unquote(path[len("/api/users/") :])
            if not user_id or "/" in user_id:
                return self._json(400, {"ok": False, "error": "user id tidak valid"})
            found = get_user(user_id)
            if not found:
                return self._json(404, {"ok": False, "error": "user tidak ditemukan"})
            return self._json(200, {"ok": True, "user": found})
        if path == "/api/settings/notifications":
            return self._json(200, {"ok": True, "settings": public_notify_settings()})
        if path == "/api/settings/auto-wo":
            return self._json(200, {"ok": True, "settings": load_auto_wo_settings()})
        if path == "/api/assets":
            return self._json(
                200,
                {
                    "ok": True,
                    "categories": list(ASSET_CATEGORIES),
                    "assets": list_assets(),
                },
            )
        if path.startswith("/api/assets/"):
            asset_id = unquote(path[len("/api/assets/") :])
            if not asset_id or "/" in asset_id:
                return self._json(400, {"error": "asset id tidak valid"})
            asset = get_asset(asset_id)
            if not asset:
                return self._json(404, {"error": "aset tidak ditemukan"})
            return self._json(200, {"ok": True, "asset": asset})
        if path == "/api/technicians":
            return self._json(
                200,
                {
                    "ok": True,
                    "skill_options": list(ASSET_CATEGORIES),
                    "technicians": list_technicians(),
                },
            )
        if path.startswith("/api/technicians/"):
            tech_id = unquote(path[len("/api/technicians/") :])
            if not tech_id or "/" in tech_id:
                return self._json(400, {"error": "technician id tidak valid"})
            tech = get_technician(tech_id)
            if not tech:
                return self._json(404, {"error": "teknisi tidak ditemukan"})
            return self._json(200, {"ok": True, "technician": tech})
        if path == "/api/work-orders":
            return self._json(200, {"ok": True, "work_orders": list_work_orders()})
        if path.startswith("/api/work-orders/"):
            wo_id = unquote(path[len("/api/work-orders/") :])
            if not wo_id or "/" in wo_id:
                return self._json(400, {"error": "work order id tidak valid"})
            wo = get_work_order(wo_id)
            if not wo:
                return self._json(404, {"error": "work order tidak ditemukan"})
            return self._json(200, {"ok": True, "work_order": wo})
        if path == "/api/pm-schedules":
            return self._json(200, {"ok": True, "schedules": list_pm_schedules()})
        if path.startswith("/api/pm-schedules/"):
            rest = unquote(path[len("/api/pm-schedules/") :])
            parts = [p for p in rest.split("/") if p]
            if len(parts) == 2 and parts[1] == "records":
                schedule = get_pm_schedule(parts[0])
                if not schedule:
                    return self._json(404, {"ok": False, "error": "jadwal PM tidak ditemukan"})
                return self._json(
                    200,
                    {
                        "ok": True,
                        "schedule": schedule,
                        "records": list_pm_service_records(parts[0]),
                    },
                )
            if len(parts) == 1:
                schedule = get_pm_schedule(parts[0])
                if not schedule:
                    return self._json(404, {"ok": False, "error": "jadwal PM tidak ditemukan"})
                return self._json(200, {"ok": True, "schedule": schedule})
            return self._json(400, {"ok": False, "error": "path tidak valid"})
        if path == "/api/status":
            return self._json(200, build_payload())
        if path == "/api/refresh":
            refresh_cache()
            return self._json(200, build_payload())
        if path == "/api/router":
            router = fetch_router_device()
            return self._json(
                200,
                {
                    "ok": bool(router),
                    "router": router,
                    "updated_at": datetime.now().isoformat(timespec="seconds"),
                },
            )
        if path == "/api/reports":
            return self._json(200, _report_query_from_params(qs))
        if path == "/api/statistik":
            return self._json(200, _statistik_query_from_params(qs))
        if path in {"/api/reports/export.pdf", "/api/reports.pdf"}:
            data = _report_query_from_params(qs)
            device_id = data["filters"]["device"]
            if device_id and device_id != "all":
                device_label = next(
                    (d["name"] for d in data["devices"] if d["id"] == device_id),
                    device_id,
                )
            else:
                device_label = "Semua"
            pdf = build_incident_pdf(
                data["logs"],
                site_name=CONFIG["site_name"],
                site_site=CONFIG["site_site"],
                date_from=data["filters"]["from"],
                date_to=data["filters"]["to"],
                device_label=device_label,
            )
            filename = (
                f"laporan-gangguan-{data['filters']['from']}_{data['filters']['to']}.pdf"
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Length", str(len(pdf)))
            self.send_header(
                "Content-Disposition", f'attachment; filename="{filename}"'
            )
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(pdf)
            return

        prefix = "/api/devices/"
        suffix = "/meta"
        if path.startswith(prefix) and path.endswith(suffix):
            device_id = unquote(path[len(prefix) : -len(suffix)])
            if not device_id or "/" in device_id:
                return self._json(400, {"error": "device_id tidak valid"})
            meta = get_device_meta(device_id)
            return self._json(
                200,
                {
                    "ok": True,
                    "meta": enrich_device_meta({"id": device_id}, meta),
                },
            )

        self._json(404, {"error": "not found"})

    def _serve_file(self, file_path: Path) -> None:
        # prevent path traversal
        try:
            resolved = file_path.resolve()
            if not str(resolved).startswith(str(STATIC.resolve())):
                self._json(403, {"error": "forbidden"})
                return
        except OSError:
            self._json(404, {"error": "not found"})
            return
        if not resolved.is_file():
            # allow index at STATIC/index.html when path is absolute check
            if file_path == STATIC / "index.html" and (STATIC / "index.html").is_file():
                resolved = STATIC / "index.html"
            else:
                self._json(404, {"error": "not found"})
                return
        ext = resolved.suffix.lower()
        ctype = MIME.get(ext, "application/octet-stream")
        self._send(200, resolved.read_bytes(), ctype)


def poll_loop(stop_event: threading.Event) -> None:
    while not stop_event.is_set():
        started = time.monotonic()
        try:
            refresh_cache()
        except Exception as exc:  # noqa: BLE001
            print(f"[poll] error: {exc}", flush=True)
        # Keep wall-clock interval ≈ poll_seconds (don't add wait on top of slow refresh).
        remaining = CONFIG["poll_seconds"] - (time.monotonic() - started)
        if remaining > 0:
            stop_event.wait(remaining)


def main() -> None:
    print(
        f"Simplo Monitor starting on http://{CONFIG['app_host']}:{CONFIG['app_port']}",
        flush=True,
    )
    print(f"NX host: {CONFIG['nx_host']}  user: {CONFIG['nx_username']}", flush=True)
    refresh_cache()
    stop = threading.Event()
    t = threading.Thread(target=poll_loop, args=(stop,), daemon=True)
    t.start()
    server = ThreadingHTTPServer((CONFIG["app_host"], CONFIG["app_port"]), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down…", flush=True)
    finally:
        stop.set()
        server.server_close()


if __name__ == "__main__":
    main()
