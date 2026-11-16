# Simplo Monitor — NX Witness Camera Dashboard

Dashboard web untuk menampilkan status kamera dari **NX Witness** (online/offline + recording).

## Fitur

- Indikator **online / offline** dari status perangkat NX Witness
- Indikator **recording aktif** (status `Recording`) vs online tanpa rekam
- Grid perangkat + statistik + panel detail (layout sesuai mockup Simplo)
- Auto-refresh tiap 30 detik (konfigurasi di `.env`)
- Mode demo jika kredensial NX belum diisi / gagal login

## Persyaratan

- Python 3.10+
- Paket `python3-requests` (sudah ada di server ini)
- NX Witness Media Server (port 7001)

## Setup

```bash
cd /home/admincmms/simplo-monitor
cp .env.example .env
nano .env   # isi NX_PASSWORD
./start.sh
```

Buka: **http://192.168.100.224:8080** atau **http://localhost:8080**

## Konfigurasi `.env`

| Key | Keterangan |
|-----|------------|
| `NX_HOST` | URL NX Witness, default `https://127.0.0.1:7001` |
| `NX_USERNAME` | User NX, default `admin` |
| `NX_PASSWORD` | Password admin NX Witness |
| `APP_PORT` | Port dashboard, default `8080` |
| `POLL_SECONDS` | Interval refresh, default `30` |
| `DEMO_FALLBACK` | `true` = tampilkan data demo jika NX gagal |

## API yang dipakai

- `POST /rest/v3/login/sessions` — autentikasi bearer token
- `GET /rest/v3/devices?_with=id,name,status,url,model,vendor,schedule,...` — daftar kamera + status

### Mapping status

| Status NX | Online | Recording | Kartu |
|-----------|--------|-----------|-------|
| `Recording` | ya | ya | Hijau (Sehat) |
| `Online` + jadwal rekam aktif | ya | tidak | Oranye (Perhatian) |
| `Offline` / lainnya | tidak | tidak | Merah (Gangguan) |

## Endpoint lokal

- `GET /api/status` — payload dashboard
- `GET /api/refresh` — paksa tarik ulang dari NX (+ probe router)
- `GET /api/router` — status gateway WiFi/LTE saja
- `GET /api/health` — healthcheck

## Monitoring router (192.168.1.1)

Perangkat **Network** `WIFI-GW-01` dipantau tiap siklus poll:

- Ping gateway + latency
- HTTP UI admin (judul/server lighttpd)
- MAC dari ARP
- Status internet (ICMP ke 8.8.8.8 / 1.1.1.1 + DNS)
- Opsional: detail API admin jika `ROUTER_USERNAME` / `ROUTER_PASSWORD` diisi
