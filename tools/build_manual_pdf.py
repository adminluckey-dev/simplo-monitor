"""Render MANUAL.md into a plain A4 PDF next to the project root."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pdf_report import _render_text_pdf, _wrap  # noqa: E402

WIDTH = 92


def _clean(text: str) -> str:
    text = text.replace("`", "")
    text = text.replace("**", "")
    text = text.replace("—", "-")
    text = text.replace("–", "-")
    return text.strip()


def _emit(lines: list[str], text: str, *, indent: str = "") -> None:
    body = _clean(text)
    if not body:
        lines.append("")
        return
    wrapped = _wrap(body, WIDTH - len(indent))
    for i, row in enumerate(wrapped):
        lines.append((indent if i == 0 else " " * len(indent)) + row)


def markdown_to_lines(md: str) -> list[str]:
    lines: list[str] = [
        "SIMPLO MONITOR (CMMS)",
        "Panduan Pengguna",
        "",
    ]
    in_table = False
    for raw in md.splitlines():
        line = raw.rstrip()
        if line.startswith("|"):
            cells = [_clean(c) for c in line.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            in_table = True
            _emit(lines, "  |  ".join(cells), indent="  ")
            continue
        if in_table:
            lines.append("")
            in_table = False
        if not line.strip():
            if lines and lines[-1] != "":
                lines.append("")
            continue
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            if lines and lines[-1] != "":
                lines.append("")
            _emit(lines, line[3:].upper())
            lines.append("")
            continue
        if line.startswith("### "):
            _emit(lines, line[4:])
            continue
        if line.startswith("- "):
            _emit(lines, line[2:], indent="  - ")
            continue
        numbered = re.match(r"^(\d+)\.\s+(.*)$", line)
        if numbered:
            _emit(lines, numbered.group(2), indent=f"  {numbered.group(1)}. ")
            continue
        _emit(lines, line)
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def main() -> None:
    source = ROOT / "MANUAL.md"
    target = ROOT / "Panduan-Pengguna-Simplo-Monitor.pdf"
    lines = markdown_to_lines(source.read_text(encoding="utf-8"))
    target.write_bytes(_render_text_pdf(lines, font_size=11))
    print(target)


if __name__ == "__main__":
    main()
