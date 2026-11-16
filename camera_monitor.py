"""Direct CCTV IP reachability probe (bypass NX) for early offline detection."""

from __future__ import annotations

import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

# Common camera / NVR service ports (Hikvision, Dahua, RTSP, HTTP).
_CAMERA_PORTS = (80, 554, 8000, 443, 37777, 8080)


def _tcp_open(ip: str, port: int, timeout: float) -> bool:
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except OSError:
        return False


def probe_camera_ip(
    ip: str,
    *,
    timeout: float = 0.7,
    ports: tuple[int, ...] = _CAMERA_PORTS,
) -> dict[str, Any]:
    """Fast check whether a camera IP answers on any common port."""
    ip = str(ip or "").strip()
    result: dict[str, Any] = {
        "ip": ip,
        "reachable": False,
        "port": None,
        "latency_ms": None,
        "method": "tcp",
        "checked_ports": list(ports),
    }
    if not ip:
        result["error"] = "ip kosong"
        return result

    t0 = time.monotonic()
    # Probe ports concurrently; first success wins.
    with ThreadPoolExecutor(max_workers=min(6, len(ports))) as pool:
        futs = {pool.submit(_tcp_open, ip, port, timeout): port for port in ports}
        for fut in as_completed(futs):
            port = futs[fut]
            try:
                ok = fut.result()
            except Exception:  # noqa: BLE001
                ok = False
            if ok:
                result["reachable"] = True
                result["port"] = port
                result["latency_ms"] = round((time.monotonic() - t0) * 1000, 1)
                # Cancel remaining work by shutting down — as_completed will finish
                # queued checks but we return immediately for speed of caller merge.
                return result

    result["latency_ms"] = round((time.monotonic() - t0) * 1000, 1)
    return result


def probe_cameras(
    devices: list[dict[str, Any]],
    *,
    timeout: float = 0.7,
    max_workers: int = 16,
) -> dict[str, dict[str, Any]]:
    """Probe all CCTV devices that have an IP. Returns map device_id -> probe."""
    targets: list[tuple[str, str]] = []
    for d in devices:
        category = str(d.get("category") or d.get("type") or "")
        if category != "CCTV":
            continue
        ip = str(d.get("ip") or "").strip()
        device_id = str(d.get("id") or "").strip()
        if ip and device_id:
            targets.append((device_id, ip))

    out: dict[str, dict[str, Any]] = {}
    if not targets:
        return out

    with ThreadPoolExecutor(max_workers=min(max_workers, len(targets))) as pool:
        futs = {
            pool.submit(probe_camera_ip, ip, timeout=timeout): device_id
            for device_id, ip in targets
        }
        for fut in as_completed(futs):
            device_id = futs[fut]
            try:
                out[device_id] = fut.result()
            except Exception as exc:  # noqa: BLE001
                out[device_id] = {
                    "ip": "",
                    "reachable": False,
                    "error": str(exc),
                    "method": "tcp",
                }
    return out


def apply_cctv_attention_rules(devices: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Mark online CCTV as attention (yellow) when not recording or schedule off."""
    updated: list[dict[str, Any]] = []
    for d in devices:
        item = dict(d)
        category = str(item.get("category") or item.get("type") or "")
        if category != "CCTV":
            updated.append(item)
            continue
        if not item.get("online") or item.get("health") == "issue":
            updated.append(item)
            continue

        recording = bool(item.get("recording"))
        schedule_enabled = bool(item.get("schedule_enabled"))
        if recording and schedule_enabled:
            item["health"] = "healthy"
        else:
            item["health"] = "attention"
            reasons: list[str] = []
            if not recording:
                reasons.append("Tidak merekam")
            if not schedule_enabled:
                reasons.append("Jadwal nonaktif")
            # Keep Offline/IP notes intact; otherwise show clear attention reason.
            status = str(item.get("status_raw") or "")
            if status and ("Offline" in status or status.startswith("IP OK")):
                pass
            elif reasons:
                item["status_raw"] = " · ".join(reasons)
        updated.append(item)
    return updated


def apply_direct_cctv_status(
    devices: list[dict[str, Any]],
    *,
    timeout: float = 0.7,
) -> list[dict[str, Any]]:
    """Override device health using direct IP probe for early offline detection.

    - IP unreachable → force offline / issue (even if NX still says Online)
    - Inventory-only ("Not monitored") with IP up → treat as online
    - NX offline but IP up → keep caution (attention) and note IP OK
    """
    probes = probe_cameras(devices, timeout=timeout)
    if not probes:
        return apply_cctv_attention_rules(devices)

    updated: list[dict[str, Any]] = []
    for d in devices:
        item = dict(d)
        device_id = str(item.get("id") or "")
        probe = probes.get(device_id)
        if not probe:
            updated.append(item)
            continue

        item["direct_ip"] = probe
        nx_online = bool(item.get("online"))
        nx_status = str(item.get("status_raw") or "")
        reachable = bool(probe.get("reachable"))

        if not reachable:
            item["online"] = False
            item["health"] = "issue"
            if nx_online:
                item["status_raw"] = f"Offline (IP) · NX {nx_status or 'Online'}"
            elif nx_status in {"", "Not monitored", "Unknown"}:
                item["status_raw"] = "Offline (IP)"
            elif "Offline (IP)" not in nx_status:
                item["status_raw"] = f"Offline (IP) · NX {nx_status}"
        else:
            # IP reachable
            if nx_status == "Not monitored" or item.get("server_id") == "inventory":
                item["online"] = True
                item["status_raw"] = "Online (IP)"
                item["recording"] = bool(item.get("recording"))
                # health decided by attention rules (recording/schedule)
            elif not nx_online:
                # NX slow/offline but camera still answers — early soft signal
                item["online"] = True
                item["status_raw"] = f"IP OK · NX {nx_status or 'Offline'}"
            # else: keep NX online/recording status; attach probe only

        updated.append(item)
    return apply_cctv_attention_rules(updated)
