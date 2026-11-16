#!/usr/bin/env python3
"""Add a white outline (stroke) around the blue 'Simplo System' text in the
logo PNG. Pure stdlib (zlib/struct) — no PIL/numpy needed.

Only blue-ish, opaque pixels are treated as the wordmark, so the white stroke
appears only around 'Simplo' + 'System' and not around the black 'powered by
smartnet vinveltama' text or the orange hexagon. Transparent background is
preserved.
"""

from __future__ import annotations

import struct
import sys
import zlib

SRC = "/home/admincmms/Pictures/Logo Simplo X SVT.png"
DST = "/home/admincmms/simplo-monitor/static/img/logo.png"
STROKE = 1  # outline radius in source pixels


def read_png_rgba(path: str) -> tuple[int, int, bytearray]:
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    pos = 8
    width = height = 0
    idat = bytearray()
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        ctype = data[pos + 4 : pos + 8]
        chunk = data[pos + 8 : pos + 8 + length]
        pos += 12 + length  # length + type + data + crc
        if ctype == b"IHDR":
            width, height, bit_depth, color_type = struct.unpack(">IIBB", chunk[:10])
            if bit_depth != 8 or color_type != 6:
                raise ValueError(f"need 8-bit RGBA, got depth={bit_depth} type={color_type}")
            if chunk[12] != 0:
                raise ValueError("interlaced PNG not supported")
        elif ctype == b"IDAT":
            idat += chunk
        elif ctype == b"IEND":
            break

    raw = zlib.decompress(bytes(idat))
    bpp = 4
    stride = width * bpp
    out = bytearray(width * height * bpp)
    prev = bytearray(stride)
    rpos = 0
    for y in range(height):
        ftype = raw[rpos]
        rpos += 1
        line = bytearray(raw[rpos : rpos + stride])
        rpos += stride
        if ftype == 1:  # Sub
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif ftype == 2:  # Up
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ftype == 3:  # Average
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif ftype == 4:  # Paeth
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        elif ftype != 0:
            raise ValueError(f"bad filter {ftype}")
        out[y * stride : y * stride + stride] = line
        prev = line
    return width, height, out


def write_png_rgba(path: str, width: int, height: int, pix: bytearray) -> None:
    stride = width * 4
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter: None
        raw += pix[y * stride : y * stride + stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(ctype: bytes, body: bytes) -> bytes:
        return (
            struct.pack(">I", len(body))
            + ctype
            + body
            + struct.pack(">I", zlib.crc32(ctype + body) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", comp))
        f.write(chunk(b"IEND", b""))


def build_blue_mask(width: int, height: int, pix: bytearray) -> bytearray:
    mask = bytearray(width * height)
    for i in range(width * height):
        r = pix[i * 4]
        g = pix[i * 4 + 1]
        b = pix[i * 4 + 2]
        a = pix[i * 4 + 3]
        if a > 40 and b > 80 and (b - r) > 25 and (b - g) > 15:
            mask[i] = 1
    return mask


def dilate(mask: bytearray, width: int, height: int, r: int) -> bytearray:
    # Horizontal pass using per-row prefix sums.
    horiz = bytearray(width * height)
    for y in range(height):
        base = y * width
        pref = [0] * (width + 1)
        for x in range(width):
            pref[x + 1] = pref[x] + mask[base + x]
        for x in range(width):
            lo = x - r if x - r > 0 else 0
            hi = x + r if x + r < width - 1 else width - 1
            if pref[hi + 1] - pref[lo] > 0:
                horiz[base + x] = 1
    # Vertical pass using per-column prefix sums.
    out = bytearray(width * height)
    for x in range(width):
        pref = [0] * (height + 1)
        for y in range(height):
            pref[y + 1] = pref[y] + horiz[y * width + x]
        for y in range(height):
            lo = y - r if y - r > 0 else 0
            hi = y + r if y + r < height - 1 else height - 1
            if pref[hi + 1] - pref[lo] > 0:
                out[y * width + x] = 1
    return out


def main() -> int:
    width, height, pix = read_png_rgba(SRC)
    mask = build_blue_mask(width, height, pix)
    stroke = dilate(mask, width, height, STROKE)

    # Compose original OVER a white stroke layer (white where stroke, else clear).
    out = bytearray(width * height * 4)
    for i in range(width * height):
        oa = pix[i * 4 + 3]
        sa = 255 if stroke[i] else 0
        if oa == 255:
            out[i * 4] = pix[i * 4]
            out[i * 4 + 1] = pix[i * 4 + 1]
            out[i * 4 + 2] = pix[i * 4 + 2]
            out[i * 4 + 3] = 255
            continue
        if sa == 0 and oa == 0:
            continue  # fully transparent
        # 'over': orig over white stroke
        oaf = oa / 255.0
        saf = sa / 255.0
        out_a = oaf + saf * (1 - oaf)
        if out_a <= 0:
            continue
        for c in range(3):
            oc = pix[i * 4 + c]
            sc = 255  # white
            val = (oc * oaf + sc * saf * (1 - oaf)) / out_a
            out[i * 4 + c] = int(val + 0.5)
        out[i * 4 + 3] = int(out_a * 255 + 0.5)

    write_png_rgba(DST, width, height, out)
    print(f"wrote {DST} ({width}x{height}), stroke radius {STROKE}px")
    return 0


if __name__ == "__main__":
    sys.exit(main())
