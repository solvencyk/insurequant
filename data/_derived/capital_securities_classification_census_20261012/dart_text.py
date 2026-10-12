"""dart_text.py (parser-kics, ticket 20261012T1230Z) -- helper + CLI, READ ONLY.

Plain-text view of a DART XML report (사업보고서/반기보고서 body or note file) so the issuer's own wording about 신종자본증권 / 후순위채
(스텝업, 기본자본/보완자본, 이자지급 재량, 콜옵션 ...) can be searched and quoted with a file + line position.

CLI:  dart_text.py XML_PATH [--kw "regex"] [--near "regex"] [--window 0] [--max 60] [--width 400]
  --kw      regex a line must match (default: 신종자본증권|자본으로 인정|자본인정)
  --near    second regex that must ALSO match within the same line (e.g. "스텝|step|기본자본|보완자본|금리")
  --window  also print N lines before/after each hit
Output: "LINE_NO | text" (text cut to --width).  Line numbers are those of the plain-text conversion (rows = table rows, cells joined by ' | ').
"""
from __future__ import annotations

import html
import io
import re
import sys
from pathlib import Path

_TAG_ROW_END = re.compile(r"</(?:TR|P|TITLE|SECTION-\d|LIBRARY|BODY|COVER|TABLE|TABLE-GROUP)>", re.I)
_TAG_CELL_END = re.compile(r"</(?:TD|TH|TE|TU)>", re.I)
_TAG_ANY = re.compile(r"<[^>]+>")
_WS = re.compile(r"[ \t 　]+")


def read_xml(path) -> str:
    raw = Path(path).read_bytes()
    for enc in ("utf-8", "cp949", "euc-kr"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def to_lines(xml: str) -> list[str]:
    s = _TAG_CELL_END.sub(" | ", xml)
    s = _TAG_ROW_END.sub("\n", s)
    s = re.sub(r"<BR\s*/?>", "\n", s, flags=re.I)
    s = _TAG_ANY.sub("", s)
    s = html.unescape(s)
    out = []
    for ln in s.split("\n"):
        ln = _WS.sub(" ", ln).strip(" |")
        if ln:
            out.append(ln)
    return out


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
    a = sys.argv[1:]
    path = a[0]
    kw = re.compile(a[a.index("--kw") + 1] if "--kw" in a else r"신종자본증권|자본으로 인정|자본인정")
    near = re.compile(a[a.index("--near") + 1]) if "--near" in a else None
    window = int(a[a.index("--window") + 1]) if "--window" in a else 0
    mx = int(a[a.index("--max") + 1]) if "--max" in a else 60
    width = int(a[a.index("--width") + 1]) if "--width" in a else 400
    lines = to_lines(read_xml(path))
    print(f"# {path} | {len(lines)} lines")
    n = 0
    last = -10
    for i, ln in enumerate(lines):
        if kw.search(ln) and (near is None or near.search(ln)):
            lo, hi = max(0, i - window), min(len(lines), i + window + 1)
            if lo <= last:
                lo = last + 1
            for j in range(lo, hi):
                print(f"{j + 1:>6} | {lines[j][:width]}")
            if window:
                print("   ---")
            last = hi - 1
            n += 1
            if n >= mx:
                print(f"# (stopped after {mx} hits)")
                break
    print(f"# hits shown: {n}")


if __name__ == "__main__":
    main()
