"""Minimal PDF report generator (no third-party deps)."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def _esc(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("\r", "")
        .replace("\n", " ")
    )


def _latin(text: str) -> str:
    """Map common Indonesian/Unicode chars to Latin-1-ish PDF-safe text."""
    repl = {
        "—": "-",
        "–": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "•": "-",
        "·": "-",
        "°": " deg",
        "…": "...",
    }
    out = []
    for ch in str(text or ""):
        if ch in repl:
            out.append(repl[ch])
        elif ord(ch) < 128:
            out.append(ch)
        else:
            # drop unsupported glyphs rather than crash PDF
            try:
                ch.encode("latin-1")
                out.append(ch)
            except UnicodeEncodeError:
                out.append("?")
    return "".join(out)


def build_incident_pdf(
    logs: list[dict[str, Any]],
    *,
    site_name: str,
    site_site: str,
    date_from: str,
    date_to: str,
    device_label: str,
) -> bytes:
    title = _latin(f"Laporan Histori Gangguan - {site_name}")
    subtitle = _latin(f"Lokasi: {site_site}")
    filt = _latin(
        f"Filter tanggal: {date_from or '-'} s/d {date_to or '-'} | Device: {device_label or 'Semua'}"
    )
    generated = _latin(
        f"Dibuat: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total: {len(logs)} entri"
    )

    lines: list[str] = [title, subtitle, filt, generated, ""]
    if not logs:
        lines.append(_latin("Tidak ada data gangguan pada filter ini."))
    else:
        for i, row in enumerate(logs, 1):
            ts = _latin(str(row.get("ts") or ""))
            name = _latin(str(row.get("device_name") or ""))
            loc = _latin(str(row.get("location") or "-"))
            etype = str(row.get("event_type") or "")
            kind = {
                "started": "GANGGUAN MULAI",
                "resolved": "KEMBALI NORMAL",
                "attention_started": "PERHATIAN MULAI",
                "attention_resolved": "PERHATIAN SELESAI",
                "detected": "TERDETEKSI",
            }.get(etype, etype.upper())
            title_row = _latin(str(row.get("title") or ""))
            detail = _latin(str(row.get("detail") or ""))
            sfrom = _latin(str(row.get("status_from") or "-"))
            sto = _latin(str(row.get("status_to") or "-"))
            ip = _latin(str(row.get("ip") or "-"))
            lines.append(_latin(f"{i}. [{kind}] {ts}"))
            lines.append(_latin(f"   Device : {name}"))
            lines.append(_latin(f"   Lokasi : {loc} | IP: {ip}"))
            lines.append(_latin(f"   Status : {sfrom} -> {sto}"))
            lines.append(_latin(f"   Judul  : {title_row}"))
            # wrap detail
            wrapped = _wrap(detail, 92)
            for w in wrapped:
                lines.append(_latin(f"   Detail : {w}" if w == wrapped[0] else f"           {w}"))
            lines.append("")

    return _render_text_pdf(lines)


def _wrap(text: str, width: int) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    rows: list[str] = []
    cur = words[0]
    for w in words[1:]:
        if len(cur) + 1 + len(w) <= width:
            cur = f"{cur} {w}"
        else:
            rows.append(cur)
            cur = w
    rows.append(cur)
    return rows


def _render_text_pdf(lines: list[str], *, font_size: int = 10) -> bytes:
    """Build a simple multi-page PDF using Helvetica."""
    page_w, page_h = 595, 842  # A4
    margin_x = 40
    top_y = page_h - 50
    line_h = font_size + 4
    max_lines = int((top_y - 40) / line_h)

    pages: list[list[str]] = []
    buf: list[str] = []
    for line in lines:
        buf.append(line)
        if len(buf) >= max_lines:
            pages.append(buf)
            buf = []
    if buf or not pages:
        pages.append(buf)

    objects: list[bytes] = []
    # 1: catalog, 2: pages, 3: font, then content streams + page objs
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    # placeholder for pages obj
    objects.append(b"")  # index 1 -> obj 2
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    page_obj_nums: list[int] = []
    content_objs: list[tuple[int, bytes]] = []

    for page_lines in pages:
        content_parts = [
            "BT",
            f"/F1 {font_size} Tf",
            f"{margin_x} {top_y} Td",
            f"{line_h} TL",
        ]
        for i, line in enumerate(page_lines):
            safe = _esc(_latin(line))
            if i == 0:
                content_parts.append(f"({safe}) Tj")
            else:
                content_parts.append(f"T* ({safe}) Tj")
        content_parts.append("ET")
        stream = "\n".join(content_parts).encode("latin-1", errors="replace")
        content_objs.append((0, stream))  # num filled later

    # Assign object numbers
    # obj1 catalog, obj2 pages, obj3 font
    next_id = 4
    page_defs: list[tuple[int, int]] = []  # page_obj, content_obj
    for i, (_, stream) in enumerate(content_objs):
        content_id = next_id
        page_id = next_id + 1
        next_id += 2
        content_objs[i] = (content_id, stream)
        page_defs.append((page_id, content_id))
        page_obj_nums.append(page_id)

    kids = " ".join(f"{n} 0 R" for n in page_obj_nums)
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_obj_nums)} >>".encode()

    # Build final object list in order by number
    obj_map: dict[int, bytes] = {
        1: objects[0],
        2: objects[1],
        3: objects[2],
    }
    for page_id, content_id in page_defs:
        stream = next(s for cid, s in content_objs if cid == content_id)
        obj_map[content_id] = (
            f"<< /Length {len(stream)} >>\nstream\n".encode()
            + stream
            + b"\nendstream"
        )
        obj_map[page_id] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_w} {page_h}] "
            f"/Contents {content_id} 0 R /Resources << /Font << /F1 3 0 R >> >> >>"
        ).encode()

    # Serialize
    out = bytearray(b"%PDF-1.4\n")
    offsets = {0: 0}
    for obj_num in sorted(obj_map):
        offsets[obj_num] = len(out)
        out.extend(f"{obj_num} 0 obj\n".encode())
        out.extend(obj_map[obj_num])
        out.extend(b"\nendobj\n")

    xref_pos = len(out)
    max_obj = max(obj_map)
    out.extend(f"xref\n0 {max_obj + 1}\n".encode())
    out.extend(b"0000000000 65535 f \n")
    for i in range(1, max_obj + 1):
        out.extend(f"{offsets[i]:010d} 00000 n \n".encode())
    out.extend(
        f"trailer\n<< /Size {max_obj + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode()
    )
    return bytes(out)
