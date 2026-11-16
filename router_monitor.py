"""Monitor WiFi/LTE router gateway: reachability + internet status."""

from __future__ import annotations

import hashlib
import http.client
import os
import re
import socket
import subprocess
import time
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import quote


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def _md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _run(cmd: list[str], timeout: float = 6.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def ping_host(host: str, count: int = 2, timeout_s: float = 2.0) -> dict[str, Any]:
    """ICMP ping; returns reachable, loss%, avg_ms."""
    try:
        proc = _run(
            [
                "ping",
                "-c",
                str(count),
                "-W",
                str(max(1, int(timeout_s))),
                host,
            ],
            timeout=timeout_s * count + 3,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        reachable = proc.returncode == 0
        loss = 100.0
        avg_ms: float | None = None
        m_loss = re.search(r"(\d+(?:\.\d+)?)% packet loss", out)
        if m_loss:
            loss = float(m_loss.group(1))
        m_rtt = re.search(
            r"rtt min/avg/max/[^\s=]+\s*=\s*([\d.]+)/([\d.]+)/([\d.]+)",
            out,
        )
        if m_rtt:
            avg_ms = float(m_rtt.group(2))
        elif reachable:
            m_time = re.search(r"time[=<]([\d.]+)\s*ms", out)
            if m_time:
                avg_ms = float(m_time.group(1))
        return {
            "reachable": reachable and loss < 100,
            "loss_pct": loss,
            "avg_ms": avg_ms,
            "raw_ok": reachable,
        }
    except (subprocess.TimeoutExpired, OSError) as exc:
        return {
            "reachable": False,
            "loss_pct": 100.0,
            "avg_ms": None,
            "error": str(exc),
        }


def ping_host_reliable(
    host: str,
    *,
    count: int = 2,
    timeout_s: float = 2.0,
    retries: int = 2,
    retry_delay: float = 0.5,
) -> dict[str, Any]:
    """Ping with short retries to absorb transient WiFi blips."""
    last: dict[str, Any] = {
        "reachable": False,
        "loss_pct": 100.0,
        "avg_ms": None,
    }
    for attempt in range(max(1, retries)):
        last = ping_host(host, count=count, timeout_s=timeout_s)
        if last.get("reachable"):
            last["attempts"] = attempt + 1
            return last
        if attempt + 1 < retries:
            time.sleep(retry_delay)
    last["attempts"] = retries
    return last


def arp_mac(ip: str) -> str:
    try:
        proc = _run(["ip", "neigh", "show", ip], timeout=3)
        m = re.search(r"lladdr\s+([0-9a-fA-F:]{11,17})", proc.stdout or "")
        if m:
            return m.group(1).lower()
    except (subprocess.TimeoutExpired, OSError):
        pass
    return ""


def http_probe(ip: str, timeout: float = 4.0) -> dict[str, Any]:
    """Probe router admin UI over HTTP."""
    result: dict[str, Any] = {
        "ok": False,
        "status": None,
        "title": "",
        "server": "",
        "url": f"http://{ip}/",
        "latency_ms": None,
    }
    try:
        t0 = time.monotonic()
        conn = http.client.HTTPConnection(ip, timeout=timeout)
        conn.request("GET", "/", headers={"User-Agent": "SimploMonitor/1.0"})
        resp = conn.getresponse()
        body = resp.read(65536)
        result["latency_ms"] = round((time.monotonic() - t0) * 1000, 1)
        result["status"] = resp.status
        result["server"] = resp.getheader("Server") or ""
        result["ok"] = 200 <= resp.status < 400
        text = body.decode("utf-8", errors="ignore")
        m = re.search(r"<title[^>]*>([^<]+)</title>", text, re.I)
        if m:
            result["title"] = m.group(1).strip()
        conn.close()
    except (OSError, http.client.HTTPException) as exc:
        result["error"] = str(exc)
    return result


def dns_ok(name: str = "www.google.com", timeout: float = 3.0) -> bool:
    try:
        old = socket.getdefaulttimeout()
        socket.setdefaulttimeout(timeout)
        try:
            socket.getaddrinfo(name, 443, proto=socket.IPPROTO_TCP)
            return True
        finally:
            socket.setdefaulttimeout(old)
    except OSError:
        return False


def check_internet(
    targets: list[str] | None = None,
    *,
    quick: bool = False,
) -> dict[str, Any]:
    if quick:
        targets = targets or ["8.8.8.8"]
        probes = [
            {"host": host, **ping_host_reliable(host, count=1, timeout_s=1.0, retries=1)}
            for host in targets
        ]
        dns = dns_ok(timeout=1.5)
    else:
        targets = targets or ["8.8.8.8", "1.1.1.1"]
        probes = []
        for host in targets:
            p = ping_host_reliable(host, count=2, timeout_s=2.0, retries=2)
            probes.append({"host": host, **p})
        dns = dns_ok()
        if not dns:
            # One more DNS attempt — resolver blips are common on WiFi CPE
            time.sleep(0.3)
            dns = dns_ok()
    reachable = [p for p in probes if p.get("reachable")]
    icmp_ok = bool(reachable)
    # ICMP alone is enough to treat internet as up; DNS failure is soft (attention).
    ok = icmp_ok
    avg = None
    if reachable:
        vals = [p["avg_ms"] for p in reachable if p.get("avg_ms") is not None]
        if vals:
            avg = round(sum(vals) / len(vals), 1)
    return {
        "ok": ok,
        "icmp_ok": icmp_ok,
        "dns_ok": dns,
        "avg_ms": avg,
        "probes": probes,
    }


def _create_xml(obj_path: str, obj_method: str) -> str:
    parts = [
        '<?xml version="1.0" encoding="US-ASCII"?>',
        "<RGW>",
        "<param>",
        "<method>call</method>",
        "<session>000</session>",
        f"<obj_path>{obj_path}</obj_path>",
        f"<obj_method>{obj_method}</obj_method>",
        "</param>",
        "</RGW>",
    ]
    return "".join(parts)


def _hex_js(value: int) -> str:
    """Match router JS hex() helper used for Digest nc counter."""
    digits = "0123456789ABCDEF"
    out = digits[value & 15]
    while value > 15:
        value >>= 4
        out = digits[value & 15] + out
    return out


def _nc_str(count: int) -> str:
    return ("0000000000" + _hex_js(count))[-8:]


class RouterApiClient:
    """Digest + XML API client for NotionI / Marvell LTE CPE (realm Highwmg)."""

    URI = "/cgi/xml_action.cgi"

    def __init__(
        self,
        ip: str,
        username: str,
        password: str,
        timeout: float = 8.0,
    ) -> None:
        self.ip = ip
        self.username = username
        self.password = password
        self.timeout = timeout
        self.realm = ""
        self.nonce = ""
        self.qop = "auth"
        self._nc = 1
        self._ha1 = ""
        self.logged_in = False
        self.last_error = ""

    def _auth_header(self, method: str) -> str:
        cnonce = _md5(f"{time.time()}{os.getpid()}{self._nc}")[:16]
        nc = _nc_str(self._nc)
        ha2 = _md5(f"{method}:{self.URI}")
        response = _md5(
            f"{self._ha1}:{self.nonce}:{nc}:{cnonce}:{self.qop}:{ha2}"
        )
        self._nc += 1
        return (
            f'Digest username="{self.username}", realm="{self.realm}", '
            f'nonce="{self.nonce}", uri="{self.URI}", response="{response}", '
            f'qop={self.qop}, nc={nc}, cnonce="{cnonce}"'
        )

    def login(self) -> bool:
        self.logged_in = False
        self.last_error = ""
        conn = http.client.HTTPConnection(self.ip, timeout=self.timeout)
        try:
            conn.request(
                "GET",
                "/login.cgi",
                headers={
                    "Expires": "-1",
                    "Cache-Control": "no-store, no-cache, must-revalidate",
                    "Pragma": "no-cache",
                },
            )
            resp = conn.getresponse()
            resp.read()
            www = resp.getheader("WWW-Authenticate") or ""
            m_realm = re.search(r'realm="([^"]+)"', www)
            m_nonce = re.search(r'nonce="([^"]+)"', www)
            m_qop = re.search(r'qop="([^"]+)"', www)
            if not (m_realm and m_nonce):
                self.last_error = f"Challenge digest tidak valid: {www!r}"
                return False
            self.realm = m_realm.group(1)
            self.nonce = m_nonce.group(1)
            self.qop = m_qop.group(1) if m_qop else "auth"
            self._nc = 1
            self._ha1 = _md5(f"{self.username}:{self.realm}:{self.password}")

            # Query-string digest (same as doLogin)
            cnonce = _md5(f"login{time.time()}{os.getpid()}")[:16]
            nc = _nc_str(self._nc)
            ha2 = _md5(f"GET:{self.URI}")
            digest_res = _md5(
                f"{self._ha1}:{self.nonce}:{nc}:{cnonce}:{self.qop}:{ha2}"
            )
            url = (
                f"/login.cgi?Action=Digest&username={quote(self.username)}"
                f"&realm={quote(self.realm)}&nonce={quote(self.nonce)}"
                f"&response={digest_res}&qop={self.qop}"
                f"&cnonce={cnonce}&nc={nc}&temp=marvell"
            )
            # Authorization header uses a fresh cnonce (same as authentication())
            auth = self._auth_header("GET")
            conn.request(
                "GET",
                url,
                headers={
                    "Authorization": auth,
                    "Expires": "-1",
                    "Cache-Control": "no-store, no-cache, must-revalidate",
                    "Pragma": "no-cache",
                },
            )
            resp2 = conn.getresponse()
            resp2.read()
            www2 = resp2.getheader("WWW-Authenticate") or ""
            # Success: WWW-Authenticate: status=0,space=0
            m_status = re.search(r"status=(\d+)", www2)
            status_code = m_status.group(1) if m_status else ""
            if status_code == "0":
                self.logged_in = True
                return True
            if status_code == "5":
                space = re.search(r"space=(\d+)", www2)
                wait = space.group(1) if space else "?"
                self.last_error = (
                    f"Akun terkunci sementara (tunggu ~{wait}s). "
                    "Terlalu banyak percobaan login gagal."
                )
            elif status_code:
                left = max(0, 5 - int(status_code))
                self.last_error = (
                    f"Login gagal (status={status_code}), sisa percobaan ~{left}"
                )
            else:
                self.last_error = (
                    f"Login gagal HTTP {resp2.status}, header={www2!r}"
                )
            return False
        except (OSError, http.client.HTTPException) as exc:
            self.last_error = str(exc)
            return False
        finally:
            conn.close()

    def call(self, obj_path: str, obj_method: str) -> ET.Element | None:
        if not self.logged_in and not self.login():
            return None
        auth = self._auth_header("POST")
        # Match browser XML serializer: space after XML declaration
        xml_body = (
            '<?xml version="1.0" encoding="US-ASCII"?> '
            "<RGW><param><method>call</method><session>000</session>"
            f"<obj_path>{obj_path}</obj_path>"
            f"<obj_method>{obj_method}</obj_method>"
            "</param></RGW>"
        )
        conn = http.client.HTTPConnection(self.ip, timeout=self.timeout)
        try:
            conn.request(
                "POST",
                "/xml_action.cgi?method=set",
                body=xml_body.encode("utf-8"),
                headers={
                    "Authorization": auth,
                    "Content-Type": "application/xml",
                    "csrftoken": "hfiehifejfklihefiuehflejhfueihfeuihfeui",
                },
            )
            resp = conn.getresponse()
            data = resp.read()
            if resp.status == 401:
                self.logged_in = False
                self.last_error = "Sesi API berakhir (401)"
                return None
            try:
                root = ET.fromstring(data)
            except ET.ParseError:
                self.last_error = f"XML parse error: {data[:120]!r}"
                return None
            # error_cause=5 often means method not permitted / unsupported,
            # not necessarily a dead session (other calls may still work).
            err = _xml_text(root, "error_cause")
            if err:
                return None
            return root
        except (OSError, http.client.HTTPException) as exc:
            self.last_error = str(exc)
            return None
        finally:
            conn.close()


def _xml_text(root: ET.Element | None, tag: str) -> str:
    if root is None:
        return ""
    node = root.find(f".//{tag}")
    return (node.text or "").strip() if node is not None else ""


def _data_mode_label(code: str) -> str:
    return {
        "1": "GPRS",
        "2": "EDGE",
        "3": "UMTS",
        "9": "HSUPA",
        "10": "HSDPA",
        "11": "HSPA",
        "14": "LTE",
        "15": "HSPAP",
        "16": "GSM",
        "17": "TD_SCDMA",
        "19": "4G+",
    }.get(code, code or "—")


def _parse_wifi_ssids(wifi: ET.Element | None) -> list[dict[str, str]]:
    if wifi is None:
        return []
    ssids: list[dict[str, str]] = []
    for band_tag, band_name in (("wifi_if_24G", "2.4G"), ("wifi_if_5G", "5G")):
        for iface in wifi.findall(f".//{band_tag}"):
            switch = (iface.findtext("switch") or "").strip()
            for child in list(iface):
                if not (child.tag or "").startswith("ssid"):
                    continue
                name = (child.findtext("ssid") or "").strip()
                if not name:
                    continue
                disabled = (child.findtext("disabled") or "0").strip()
                ssids.append(
                    {
                        "band": band_name,
                        "ssid": name,
                        "enabled": "no" if disabled == "1" else "yes",
                        "hidden": (child.findtext("hidden") or "0").strip(),
                        "encryption": (child.findtext("encryption") or "").strip(),
                        "radio": "on" if switch == "1" else "off",
                    }
                )
    return ssids


def fetch_router_api_details(ip: str, username: str, password: str) -> dict[str, Any]:
    """Best-effort enrichment via router XML API (needs valid credentials)."""
    out: dict[str, Any] = {"api_ok": False}
    if not username or not password:
        return out
    client = RouterApiClient(ip, username, password)
    if not client.login():
        out["api_error"] = client.last_error or "Login router gagal (kredensial / digest)"
        return out
    out["api_ok"] = True

    # Methods known to work on this firmware/account. Others often return
    # error_cause=5 (unsupported / not permitted) and are skipped.
    clients = client.call("statistics", "get_active_clients_num")
    if clients is not None:
        out["active_clients"] = _xml_text(clients, "active_clients_num")
        out["active_lan_clients"] = _xml_text(clients, "active_lan_clients_num")
        out["active_wifi_24g"] = _xml_text(clients, "active_2.4g_wifi_clients_num")
        out["active_wifi_5g"] = _xml_text(clients, "active_5g_wifi_clients_num")
        out["active_wifi_ssid1"] = _xml_text(clients, "active_wifi_ssid1_num")

    link = client.call("cm", "get_link_context")
    if link is not None:
        out["imei"] = _xml_text(link, "IMEI")
        out["imsi"] = _xml_text(link, "IMSI")
        out["msisdn"] = _xml_text(link, "MSISDN")
        out["network_name"] = _xml_text(link, "network_name") or _xml_text(
            link, "roaming_network_name"
        )
        out["roaming"] = _xml_text(link, "roaming") == "1" or _xml_text(
            link, "roaming_status"
        ) == "1"
        out["sys_mode"] = _xml_text(link, "sys_mode")
        out["data_mode"] = _xml_text(link, "data_mode")
        out["data_mode_label"] = _data_mode_label(out["data_mode"])
        out["rssi"] = _xml_text(link, "rssi")
        out["reg_status"] = _xml_text(link, "RegStatus")
        statuses = [
            (n.text or "").strip()
            for n in link.findall(".//connection_status")
        ]
        out["pdp_statuses"] = statuses
        out["wan_connected"] = any(s == "1" for s in statuses)
        apns = []
        for item in link.findall(".//contextlist/Item") or link.findall(".//Item"):
            apn = (item.findtext("lte_apn") or item.findtext("apn") or "").strip()
            st = (item.findtext("connection_status") or "").strip()
            if apn or st:
                apns.append(
                    {
                        "apn": apn,
                        "status": {
                            "0": "disconnect",
                            "1": "connected",
                            "2": "connecting",
                        }.get(st, st),
                    }
                )
        out["apns"] = apns

    wan_cfg = client.call("cm", "get_wan_configs")
    if wan_cfg is not None:
        out["wan_proto"] = _xml_text(wan_cfg, "proto")
        out["dial_switch"] = _xml_text(wan_cfg, "dial_switch")
        out["profile_name"] = _xml_text(wan_cfg, "actived_profile1") or _xml_text(
            wan_cfg, "pdp_name"
        )
        out["apn_config"] = _xml_text(wan_cfg, "apn") or _xml_text(wan_cfg, "lte_apn")
        out["ip_type"] = _xml_text(wan_cfg, "ip_type")
        out["mtu"] = _xml_text(wan_cfg, "mtu")
        if not out.get("apns") and out.get("apn_config"):
            out["apns"] = [{"apn": out["apn_config"], "status": "configured"}]

    sim = client.call("sim", "get_sim_status")
    if sim is not None:
        sim_status = _xml_text(sim, "sim_status")
        out["sim_status"] = {
            "0": "Tidak ada SIM",
            "1": "SIM terpasang",
            "2": "Error SIM",
            "3": "Unknown",
        }.get(sim_status, sim_status or "—")
        pin_status = _xml_text(sim, "pin_status")
        out["pin_status"] = {
            "2": "Perlu PIN",
            "3": "Perlu PUK",
            "5": "Ready",
        }.get(pin_status, pin_status or "—")

    # Optional enrichment — ignore failures (many return error_cause=5)
    for path, method, handler in (
        ("version", "get_version", "version"),
        ("router", "router_get_lan_ip", "lan"),
        ("router", "get_router_runtime", "runtime"),
        ("wireless", "wifi_get_detail", "wifi"),
        ("cm", "get_iccid", "iccid"),
        ("router", "get_eth_type", "eth"),
        ("router", "get_work_mode", "workmode"),
        ("network.interface.wan", "status", "wan_status"),
    ):
        root = client.call(path, method)
        if root is None:
            continue
        if handler == "version":
            out["mac_addr"] = _xml_text(root, "mac_addr")
            out["sw_version"] = _xml_text(root, "sw_version")
            out["hw_version"] = _xml_text(root, "hdware_ver")
            out["baseband_version"] = _xml_text(root, "baseband_version")
        elif handler == "lan":
            out["lan_ip"] = _xml_text(root, "lan_ip")
            out["lan_netmask"] = _xml_text(root, "lan_netmask")
        elif handler == "runtime":
            days = _xml_text(root, "run_days") or "0"
            hours = _xml_text(root, "run_hours") or "0"
            mins = _xml_text(root, "run_min") or "0"
            secs = _xml_text(root, "run_sec") or "0"
            try:
                out["uptime"] = (
                    f"{int(days)} hari {int(hours):02d}:{int(mins):02d}:{int(secs):02d}"
                )
            except ValueError:
                out["uptime"] = f"{days}d {hours}:{mins}:{secs}"
        elif handler == "wifi":
            ssids = _parse_wifi_ssids(root)
            out["wifi_ssids"] = ssids
            if ssids:
                preferred = next(
                    (s for s in ssids if s.get("enabled") == "yes" and s.get("ssid")),
                    ssids[0],
                )
                out["ssid"] = preferred.get("ssid") or ""
                out["wifi_band"] = preferred.get("band") or ""
                out["wifi_encryption"] = preferred.get("encryption") or ""
        elif handler == "iccid":
            out["iccid"] = _xml_text(root, "iccid") or _xml_text(root, "ICCID")
        elif handler == "eth":
            out["eth_type"] = _xml_text(root, "eth_type")
            out["wan_ip"] = _xml_text(root, "ipaddr")
            out["wan_gateway"] = _xml_text(root, "gateway")
            out["wan_netmask"] = _xml_text(root, "netmask")
            out["wan_dns"] = _xml_text(root, "dns")
        elif handler == "workmode":
            out["workmode"] = _xml_text(root, "workmode")
        elif handler == "wan_status":
            addr = root.find(".//ipv4-address/default/address")
            mask = root.find(".//ipv4-address/default/mask")
            if addr is not None and (addr.text or "").strip():
                out["wan_ip"] = (addr.text or "").strip()
            if mask is not None and (mask.text or "").strip():
                out["wan_netmask"] = (mask.text or "").strip()

    # Interpret cellular vs uplink: no SIM but internet OK ⇒ likely Ethernet/upstream WAN
    if out.get("sim_status") == "Tidak ada SIM":
        out["uplink_note"] = (
            "SIM tidak terpasang — uplink kemungkinan Ethernet/WAN lain "
            "(internet tetap terpantau via ICMP/DNS)"
        )
    elif out.get("sys_mode") == "0" and out.get("wan_connected") is False:
        out["uplink_note"] = "Cellular no service / WAN PDP tidak connected"

    return out


def _sys_mode_label(code: str) -> str:
    return {"0": "No service", "1": "2G/3G", "2": "LTE"}.get(code, code or "—")


def probe_router(
    ip: str | None = None,
    username: str | None = None,
    password: str | None = None,
    name: str | None = None,
    location: str | None = None,
    *,
    quick: bool = False,
    include_api: bool = True,
) -> dict[str, Any]:
    """Collect router device details + internet status for the dashboard.

    quick=True uses short timeouts for frequent dashboard polling.
    include_api=False skips the heavier router admin API scrape.
    """
    ip = ip or _env("ROUTER_IP", "192.168.1.1")
    username = username if username is not None else _env("ROUTER_USERNAME")
    password = password if password is not None else _env("ROUTER_PASSWORD")
    name = name or _env("ROUTER_NAME", "WIFI-GW-01")
    location = location or _env("ROUTER_LOCATION", "Gateway WiFi CMMS")

    if quick:
        ping = ping_host_reliable(ip, count=1, timeout_s=1.0, retries=1, retry_delay=0.15)
        mac = arp_mac(ip)
        http_info = http_probe(ip, timeout=2.0)
        internet = check_internet(quick=True)
    else:
        ping = ping_host_reliable(ip, count=2, timeout_s=2.0, retries=3)
        mac = arp_mac(ip)
        # Always probe admin UI — ICMP can flake on WiFi while HTTP still works.
        http_info = http_probe(ip)
        if not http_info.get("ok") and not ping.get("reachable"):
            time.sleep(0.4)
            http_info = http_probe(ip)
        internet = check_internet()

    api: dict[str, Any] = {}
    if (
        include_api
        and (ping.get("reachable") or http_info.get("ok"))
        and username
        and password
    ):
        try:
            api = fetch_router_api_details(ip, username, password)
        except Exception as exc:  # noqa: BLE001
            api = {"api_ok": False, "api_error": str(exc)}

    if api.get("mac_addr") and not mac:
        mac = str(api["mac_addr"]).lower()

    vendor = "NotionI / LTE CPE"
    model = http_info.get("title") or "LTE Wireless Router"
    if api.get("hw_version"):
        model = f"{model} · HW {api['hw_version']}"
    if api.get("sw_version"):
        model = f"{model}" if api.get("hw_version") else model
        # Keep model readable; FW shown in detail panel

    http_ok = bool(http_info.get("ok"))
    online = bool(ping.get("reachable")) or http_ok
    internet_ok = bool(internet.get("ok"))

    if not online:
        health = "issue"
        status_raw = "Offline"
    elif not internet.get("icmp_ok"):
        health = "issue"
        status_raw = "No Internet"
    elif not internet.get("dns_ok"):
        health = "attention"
        status_raw = "Internet ICMP OK / DNS Gagal"
    elif not http_ok:
        health = "attention"
        status_raw = "Online (UI Admin Down)"
    else:
        health = "healthy"
        status_raw = "Online + Internet"

    if api.get("api_ok") and api.get("wan_connected") is False and not internet_ok:
        status_raw = "WAN Disconnected"
        health = "issue"

    ssid_list = api.get("wifi_ssids") or []
    ssid_label = api.get("ssid") or _env("ROUTER_SSID", "CMMS")
    if len(ssid_list) > 1:
        names = [s.get("ssid") for s in ssid_list if s.get("ssid")]
        if names:
            ssid_label = " / ".join(dict.fromkeys(names))

    device = {
        "id": f"router-{ip.replace('.', '-')}",
        "name": name,
        "location": location,
        "type": "Network",
        "vendor": vendor,
        "model": model,
        "ip": ip,
        "mac": mac,
        "status_raw": status_raw,
        "online": online,
        "recording": internet_ok,  # reuse badge slot → shown as NET in UI
        "schedule_enabled": False,
        "health": health,
        "server_id": "router",
        "internet_ok": internet_ok,
        "admin_url": f"http://{ip}/",
        "router": {
            "ping_ms": ping.get("avg_ms"),
            "ping_loss_pct": ping.get("loss_pct"),
            "http_ok": http_ok,
            "http_status": http_info.get("status"),
            "http_title": http_info.get("title") or "",
            "http_server": http_info.get("server") or "",
            "http_latency_ms": http_info.get("latency_ms"),
            "internet_ok": internet_ok,
            "internet_icmp_ok": internet.get("icmp_ok"),
            "internet_dns_ok": internet.get("dns_ok"),
            "internet_latency_ms": internet.get("avg_ms"),
            "internet_probes": internet.get("probes") or [],
            "ssid": ssid_label,
            "wifi_ssids": ssid_list,
            "wifi_band": api.get("wifi_band") or "",
            "wifi_encryption": api.get("wifi_encryption") or "",
            "sw_version": api.get("sw_version") or "",
            "hw_version": api.get("hw_version") or "",
            "baseband_version": api.get("baseband_version") or "",
            "imei": api.get("imei") or "",
            "imsi": api.get("imsi") or "",
            "iccid": api.get("iccid") or "",
            "msisdn": api.get("msisdn") or "",
            "sim_status": api.get("sim_status") or "",
            "pin_status": api.get("pin_status") or "",
            "network_name": api.get("network_name") or "",
            "roaming": bool(api.get("roaming")),
            "sys_mode": _sys_mode_label(str(api.get("sys_mode") or "")),
            "data_mode": api.get("data_mode_label") or "",
            "rssi": api.get("rssi") or "",
            "active_clients": api.get("active_clients") or "",
            "active_lan_clients": api.get("active_lan_clients") or "",
            "active_wifi_24g": api.get("active_wifi_24g") or "",
            "active_wifi_5g": api.get("active_wifi_5g") or "",
            "uptime": api.get("uptime") or "",
            "wan_connected": api.get("wan_connected"),
            "wan_proto": api.get("wan_proto") or "",
            "dial_switch": api.get("dial_switch") or "",
            "apn_config": api.get("apn_config") or "",
            "profile_name": api.get("profile_name") or "",
            "wan_ip": api.get("wan_ip") or "",
            "wan_gateway": api.get("wan_gateway") or "",
            "wan_dns": api.get("wan_dns") or "",
            "workmode": api.get("workmode") or "",
            "uplink_note": api.get("uplink_note") or "",
            "apns": api.get("apns") or [],
            "api_ok": bool(api.get("api_ok")),
            "api_error": api.get("api_error") or "",
            "lan_ip": api.get("lan_ip") or ip,
            "lan_netmask": api.get("lan_netmask") or "",
        },
    }
    return device
