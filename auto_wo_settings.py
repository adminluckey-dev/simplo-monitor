"""Auto Generate Work Order settings for Simplo Monitor."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SETTINGS_PATH = ROOT / "data" / "auto_wo_settings.json"

_lock = threading.Lock()

DEFAULTS: dict[str, Any] = {
    # 0 / kosong = nonaktif. Nilai > 0 = menit sejak gangguan sebelum auto-WO.
    "delay_minutes": 0,
    # Jeda antar auto-WO untuk asset yang sama (hindari duplikasi intermittent).
    "cooldown_minutes": 60,
}


def _defaults_copy() -> dict[str, Any]:
    return dict(DEFAULTS)


def _parse_minutes(value: Any, *, field: str, default: int, allow_zero: bool = True) -> int:
    if value is None or str(value).strip() == "":
        return default
    try:
        minutes = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} harus angka (menit)") from exc
    if minutes < 0:
        raise ValueError(f"{field} tidak boleh negatif")
    if minutes > 10080:
        raise ValueError(f"{field} maksimal 10080 (7 hari)")
    if not allow_zero and minutes == 0:
        raise ValueError(f"{field} harus lebih dari 0")
    return minutes


def load_settings() -> dict[str, Any]:
    with _lock:
        if not SETTINGS_PATH.exists():
            return _defaults_copy()
        try:
            raw = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return _defaults_copy()
    if not isinstance(raw, dict):
        return _defaults_copy()
    out = _defaults_copy()
    try:
        if "delay_minutes" in raw:
            out["delay_minutes"] = _parse_minutes(
                raw.get("delay_minutes"), field="delay_minutes", default=0
            )
        if "cooldown_minutes" in raw:
            out["cooldown_minutes"] = _parse_minutes(
                raw.get("cooldown_minutes"), field="cooldown_minutes", default=60
            )
    except ValueError:
        return _defaults_copy()
    return out


def save_settings(data: dict[str, Any]) -> dict[str, Any]:
    incoming = data if isinstance(data, dict) else {}
    current = load_settings()

    if "delay_minutes" in incoming:
        delay = _parse_minutes(
            incoming.get("delay_minutes"), field="delay_minutes", default=0
        )
    else:
        delay = int(current.get("delay_minutes") or 0)

    if "cooldown_minutes" in incoming:
        raw_cool = incoming.get("cooldown_minutes")
        if raw_cool is None or str(raw_cool).strip() == "":
            cooldown = 60
        else:
            cooldown = _parse_minutes(
                raw_cool, field="cooldown_minutes", default=60
            )
    else:
        cooldown = int(current.get("cooldown_minutes") or 60)

    saved = {"delay_minutes": delay, "cooldown_minutes": cooldown}
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        SETTINGS_PATH.write_text(
            json.dumps(saved, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        try:
            SETTINGS_PATH.chmod(0o600)
        except OSError:
            pass
    return saved
