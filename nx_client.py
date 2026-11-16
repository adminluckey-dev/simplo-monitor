"""NX Witness REST API client (session bearer token)."""

from __future__ import annotations

import threading
import time
from typing import Any
from urllib.parse import urljoin

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class NxClientError(Exception):
    pass


class NxClient:
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        api_version: str = "v3",
        verify_ssl: bool = False,
        timeout: float = 15.0,
    ) -> None:
        self.base = host.rstrip("/")
        self.username = username
        self.password = password
        self.api_version = api_version
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self._token: str | None = None
        self._token_expires_at = 0.0
        self._lock = threading.Lock()
        self.session = requests.Session()

    def _url(self, path: str) -> str:
        return urljoin(self.base + "/", path.lstrip("/"))

    def login(self, force: bool = False) -> str:
        with self._lock:
            now = time.time()
            if (
                not force
                and self._token
                and now < self._token_expires_at - 60
            ):
                return self._token

            payload = {
                "username": self.username,
                "password": self.password,
                "setCookie": False,
            }
            # Prefer v3; fall back to v1 if needed
            last_error: Exception | None = None
            for ver in (self.api_version, "v3", "v1"):
                try:
                    resp = self.session.post(
                        self._url(f"/rest/{ver}/login/sessions"),
                        json=payload,
                        verify=self.verify_ssl,
                        timeout=self.timeout,
                    )
                    if resp.status_code >= 400:
                        last_error = NxClientError(
                            f"Login failed ({resp.status_code}): {resp.text[:300]}"
                        )
                        continue
                    data = resp.json()
                    token = data.get("token")
                    if not token:
                        last_error = NxClientError(f"No token in login response: {data}")
                        continue
                    expires = float(data.get("expiresInS") or 3600)
                    self._token = token
                    self._token_expires_at = now + expires
                    self.api_version = ver
                    return token
                except requests.RequestException as exc:
                    last_error = exc
            raise NxClientError(str(last_error) if last_error else "Login failed")

    def _headers(self) -> dict[str, str]:
        token = self.login()
        return {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        resp = self.session.get(
            self._url(path),
            headers=self._headers(),
            params=params,
            verify=self.verify_ssl,
            timeout=self.timeout,
        )
        if resp.status_code == 401:
            self.login(force=True)
            resp = self.session.get(
                self._url(path),
                headers=self._headers(),
                params=params,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
        if resp.status_code >= 400:
            raise NxClientError(f"GET {path} -> {resp.status_code}: {resp.text[:400]}")
        if not resp.content:
            return None
        return resp.json()

    def list_devices(self) -> list[dict[str, Any]]:
        """Return camera/devices with status + schedule fields."""
        fields = (
            "id,name,url,status,model,vendor,mac,serverId,"
            "schedule,logicalId,group,type,physicalId"
        )
        data = self.get(
            f"/rest/{self.api_version}/devices",
            params={"_with": fields},
        )
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            # older wrappers
            for key in ("reply", "devices", "items"):
                if isinstance(data.get(key), list):
                    return data[key]
        return []

    def system_info(self) -> dict[str, Any]:
        try:
            info = self.get(f"/rest/{self.api_version}/system/info")
            return info if isinstance(info, dict) else {}
        except NxClientError:
            # public endpoint often works without auth
            resp = self.session.get(
                self._url("/rest/v3/system/info"),
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()


def normalize_device(raw: dict[str, Any]) -> dict[str, Any]:
    """Map NX device payload to dashboard-friendly shape."""
    status_raw = str(raw.get("status") or "Unknown")
    status_l = status_raw.lower()

    # NX: Offline | Online | Recording | Unauthorized | ...
    is_online = status_l in {"online", "recording"}
    is_recording = status_l == "recording"

    schedule = raw.get("schedule") or {}
    schedule_enabled = bool(schedule.get("isEnabled"))

    # CCTV: sehat hanya jika online + merekam + jadwal aktif.
    # Tidak merekam ATAU jadwal nonaktif → perlu perhatian (kuning).
    if not is_online:
        health = "issue"
    elif is_recording and schedule_enabled:
        health = "healthy"
    else:
        health = "attention"

    name = raw.get("name") or "Unnamed"
    url = raw.get("url") or ""
    ip = url
    if "://" in url:
        ip = url.split("://", 1)[1].split("/", 1)[0].split(":", 1)[0]

    vendor = raw.get("vendor") or ""
    model = raw.get("model") or ""
    type_hint = "CCTV"
    blob = f"{name} {vendor} {model}".lower()
    if any(k in blob for k in ("access", "door", "reader", "acs")):
        type_hint = "Access"
    elif any(k in blob for k in ("alarm", "sensor", "intrusion")):
        type_hint = "Alarm"

    return {
        "id": str(raw.get("id") or "").strip("{}"),
        "name": name,
        "location": raw.get("group") or raw.get("logicalId") or "",
        "type": type_hint,
        "vendor": vendor,
        "model": model,
        "ip": ip,
        "mac": raw.get("mac") or raw.get("physicalId") or "",
        "status_raw": status_raw,
        "online": is_online,
        "recording": is_recording,
        "schedule_enabled": schedule_enabled,
        "health": health,
        "server_id": str(raw.get("serverId") or "").strip("{}"),
    }
