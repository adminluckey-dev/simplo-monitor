"""Notification settings (Gmail SMTP + Telegram bot) for Simplo Monitor."""

from __future__ import annotations

import json
import smtplib
import ssl
import threading
import urllib.error
import urllib.parse
import urllib.request
from email.message import EmailMessage
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SETTINGS_PATH = ROOT / "data" / "notify_settings.json"

_lock = threading.Lock()

DEFAULTS: dict[str, Any] = {
    "email": {
        "enabled": False,
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_user": "",
        "smtp_password": "",
        "from_name": "Simplo Monitor",
        "from_email": "",
        "to_emails": "",
        "use_tls": True,
    },
    "telegram": {
        "enabled": False,
        "bot_token": "",
        "chat_ids": "",
    },
}


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, val in overlay.items():
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], val)
        else:
            out[key] = val
    return out


def _defaults_copy() -> dict[str, Any]:
    return json.loads(json.dumps(DEFAULTS))


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
    return _deep_merge(_defaults_copy(), raw)


def save_settings(data: dict[str, Any]) -> dict[str, Any]:
    current = load_settings()
    incoming = data if isinstance(data, dict) else {}

    email_in = incoming.get("email") if isinstance(incoming.get("email"), dict) else {}
    tg_in = incoming.get("telegram") if isinstance(incoming.get("telegram"), dict) else {}

    email = dict(current["email"])
    for key in (
        "enabled",
        "smtp_host",
        "smtp_port",
        "smtp_user",
        "from_name",
        "from_email",
        "to_emails",
        "use_tls",
    ):
        if key in email_in:
            email[key] = email_in[key]

    # Keep existing password when UI sends blank (masked / unchanged).
    if "smtp_password" in email_in:
        pwd = str(email_in.get("smtp_password") or "")
        if pwd.strip() and pwd.strip() != "********":
            email["smtp_password"] = pwd.strip()

    email["enabled"] = bool(email.get("enabled"))
    email["use_tls"] = bool(email.get("use_tls", True))
    try:
        email["smtp_port"] = int(email.get("smtp_port") or 587)
    except (TypeError, ValueError) as exc:
        raise ValueError("smtp_port harus angka") from exc
    email["smtp_host"] = str(email.get("smtp_host") or "smtp.gmail.com").strip()
    email["smtp_user"] = str(email.get("smtp_user") or "").strip()
    email["from_name"] = str(email.get("from_name") or "Simplo Monitor").strip()
    email["from_email"] = str(email.get("from_email") or "").strip()
    email["to_emails"] = str(email.get("to_emails") or "").strip()

    telegram = dict(current["telegram"])
    for key in ("enabled", "chat_ids"):
        if key in tg_in:
            telegram[key] = tg_in[key]
    if "bot_token" in tg_in:
        token = str(tg_in.get("bot_token") or "")
        if token.strip() and token.strip() != "********":
            telegram["bot_token"] = token.strip()

    telegram["enabled"] = bool(telegram.get("enabled"))
    telegram["chat_ids"] = str(telegram.get("chat_ids") or "").strip()

    saved = {"email": email, "telegram": telegram}
    with _lock:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(
            json.dumps(saved, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        try:
            SETTINGS_PATH.chmod(0o600)
        except OSError:
            pass
    return saved


def public_settings(settings: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return settings safe for UI (secrets masked)."""
    s = settings or load_settings()
    email = dict(s.get("email") or {})
    telegram = dict(s.get("telegram") or {})
    has_email_password = bool(str(email.get("smtp_password") or "").strip())
    has_bot_token = bool(str(telegram.get("bot_token") or "").strip())
    email["smtp_password"] = "********" if has_email_password else ""
    email["has_password"] = has_email_password
    telegram["bot_token"] = "********" if has_bot_token else ""
    telegram["has_token"] = has_bot_token
    return {"email": email, "telegram": telegram}


def _split_list(value: str) -> list[str]:
    parts: list[str] = []
    for chunk in str(value or "").replace(";", ",").split(","):
        item = chunk.strip()
        if item:
            parts.append(item)
    return parts


def send_email(
    *,
    to_emails: list[str] | str,
    subject: str,
    body_text: str,
    body_html: str | None = None,
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Send email via configured Gmail/SMTP settings."""
    s = (settings or load_settings()).get("email") or {}
    host = str(s.get("smtp_host") or "").strip()
    port = int(s.get("smtp_port") or 587)
    user = str(s.get("smtp_user") or "").strip()
    password = str(s.get("smtp_password") or "").strip()
    from_email = str(s.get("from_email") or user).strip()
    from_name = str(s.get("from_name") or "Simplo Monitor").strip()
    use_tls = bool(s.get("use_tls", True))
    to_list = (
        _split_list(to_emails)
        if isinstance(to_emails, str)
        else [str(x).strip() for x in to_emails if str(x).strip()]
    )

    if not host:
        raise ValueError("SMTP host wajib diisi (Setting Notifikasi)")
    if not user or not password:
        raise ValueError("Email pengirim dan app password wajib diisi (Setting Notifikasi)")
    if not from_email:
        raise ValueError("From email wajib diisi (Setting Notifikasi)")
    if not to_list:
        raise ValueError("Penerima email wajib diisi")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = ", ".join(to_list)
    msg.set_content(body_text)
    if body_html:
        msg.add_alternative(body_html, subtype="html")

    context = ssl.create_default_context()
    if use_tls:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls(context=context)
            smtp.ehlo()
            smtp.login(user, password)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP_SSL(host, port, timeout=30, context=context) as smtp:
            smtp.login(user, password)
            smtp.send_message(msg)

    return {"ok": True, "sent_to": to_list}


def send_test_email(settings: dict[str, Any] | None = None) -> dict[str, Any]:
    s = (settings or load_settings()).get("email") or {}
    to_list = _split_list(str(s.get("to_emails") or ""))
    return send_email(
        to_emails=to_list,
        subject="[Simplo Monitor] Tes notifikasi email",
        body_text=(
            "Ini adalah pesan tes dari Simplo Monitor.\n"
            "Jika Anda menerima email ini, konfigurasi Gmail/SMTP sudah benar.\n"
        ),
        settings=settings,
    )


def send_test_telegram(settings: dict[str, Any] | None = None) -> dict[str, Any]:
    s = (settings or load_settings()).get("telegram") or {}
    token = str(s.get("bot_token") or "").strip()
    chat_ids = _split_list(str(s.get("chat_ids") or ""))
    if not token:
        raise ValueError("Bot token Telegram wajib diisi")
    if not chat_ids:
        raise ValueError("Chat ID Telegram wajib diisi")

    text = (
        "🔔 *Tes notifikasi Simplo Monitor*\n"
        "Jika Anda menerima pesan ini, konfigurasi bot Telegram sudah benar."
    )
    sent: list[str] = []
    errors: list[str] = []
    for chat_id in chat_ids:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = urllib.parse.urlencode(
            {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            if not body.get("ok"):
                errors.append(f"{chat_id}: {body.get('description') or 'gagal'}")
            else:
                sent.append(chat_id)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            try:
                err_json = json.loads(detail)
                detail = err_json.get("description") or detail
            except json.JSONDecodeError:
                pass
            errors.append(f"{chat_id}: {detail}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{chat_id}: {exc}")

    if not sent:
        raise ValueError("; ".join(errors) or "Gagal mengirim ke Telegram")
    result: dict[str, Any] = {"ok": True, "sent_to": sent}
    if errors:
        result["warnings"] = errors
    return result
