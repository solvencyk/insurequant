# -*- coding: utf-8 -*-
"""Parse every 선택적용 경과조치 table out of a 정기경영공시 raw PDF (fitz text layer).

fitz emits these tables as  label / 적용전 / 적용후  on consecutive lines. Each table block
starts at a "지급여력비율" line and covers one 경과조치 (①자본감소분 ②장수·사업비·해지·대재해
③주식 ④금리 — some filings merge ③④ into one "주식위험 또는 금리위험" table).

usage: parse_transition_tables.py <period> <KRcode>
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]

ZERO = {"-", "─", "–", "—", "", "0"}
NUMRE = re.compile(r"^\(?-?[\d,]+(\.\d+)?\)?%?$")

# canonical label -> matcher (whitespace-stripped 'contains')
LABELS = [
    ("비율", "지급여력비율"),
    ("가용자본", "지급여력금액"),
    ("기본자본", "기본자본"),
    ("보완자본", "보완자본"),
    ("기준금액", "지급여력기준금액"),
    ("기본요구자본", "기본요구자본"),
    ("생명장기", "생명·장기손해보험위험액"),
    ("사망", "사망위험"),
    ("장수", "장수위험"),
    ("장해질병", "장해·질병위험"),
    ("장기재물", "장기재물·기타위험"),
    ("해지", "해지위험"),
    ("사업비", "사업비위험"),
    ("생명대재해", "대재해위험"),
    ("일반손해", "일반손해보험위험액"),
    ("보험가격", "보험가격및준비금위험"),
    ("일반대재해", "대재해위험"),
    ("시장", "시장위험액"),
    ("금리", "금리위험"),
    ("주식", "주식위험"),
    ("부동산", "부동산위험"),
    ("외환", "외환위험"),
    ("자산집중", "자산집중위험"),
    ("신용", "신용위험액"),
    ("운영", "운영위험액"),
    ("법인세", "법인세조정액"),
    ("기타요구자본", "기타요구자본"),
]
ORDER = [k for k, _ in LABELS]


def _num(tok):
    t = str(tok).strip().replace(" ", "").replace("%", "")
    if t in ZERO:
        return 0.0 if t != "" else None
    for ch in ("△", "▲", "▽", "▼", "−"):
        t = t.replace(ch, "-")
    m = re.fullmatch(r"\((-?[\d,]+(?:\.\d+)?)\)", t)
    if m:
        t = "-" + m.group(1)
    t = t.replace(",", "").lstrip("+")
    try:
        return float(t)
    except ValueError:
        return None


def _label_of(line: str, seen: set[str]) -> str | None:
    s = line.strip().lstrip("Ⅰ Ⅱ Ⅲ①②③④ .·-").replace(" ", "")
    if not s:
        return None
    for key, pat in LABELS:
        if s == pat or s == pat.replace("위험액", "위험") or s.rstrip("()1+2+3") == pat:
            if key == "생명대재해" and "생명장기" not in seen:
                continue
            if key == "일반대재해" and "일반손해" not in seen:
                continue
            if key in seen:
                continue
            return key
    return None


def parse(period: str, code: str):
    raw = REPO / "data" / "disclosure" / period / "raw"
    pdfs = sorted(raw.glob(f"{code}_*.pdf"))
    if not pdfs:
        return None, []
    am = [p for p in pdfs if "_amended" in p.name]
    pdf = max(am or pdfs, key=lambda p: p.stat().st_size)
    doc = fitz.open(pdf)
    lines: list[str] = []
    try:
        for i in range(doc.page_count):
            t = doc[i].get_text()
            if "경과조치" not in t or "기본요구자본" not in t:
                continue
            lines.extend(x.strip() for x in t.splitlines())
    finally:
        doc.close()

    tables, cur, seen = [], None, set()
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.replace(" ", "")
        if s.startswith("지급여력비율"):
            if cur:
                tables.append(cur)
            cur, seen = {}, set()
        key = _label_of(line, seen) if cur is not None else None
        if key:
            vals = []
            j = i + 1
            while j < len(lines) and len(vals) < 2:
                t = lines[j].replace(" ", "")
                if t == "":
                    j += 1
                    continue
                if NUMRE.match(t) or t in ZERO:
                    vals.append(_num(t))
                    j += 1
                    continue
                break
            if len(vals) == 2:
                cur[key] = (vals[0], vals[1])
                seen.add(key)
                i = j
                continue
        i += 1
    if cur:
        tables.append(cur)
    tables = [t for t in tables if "기본요구자본" in t or "생명장기" in t or "시장" in t]
    return pdf.name, tables


if __name__ == "__main__":
    fn, tabs = parse(sys.argv[1], sys.argv[2])
    print(f"# {fn}  tables={len(tabs)}")
    for n, t in enumerate(tabs, 1):
        changed = [k for k, (a, b) in t.items()
                   if a is not None and b is not None and abs(a - b) > 0.5
                   and k not in ("비율", "기본자본", "보완자본")]
        print(f"\n-- table {n}  변경항목: {changed}")
        for k in ORDER:
            if k in t:
                a, b = t[k]
                mark = "  <<" if (a is not None and b is not None and abs(a - b) > 0.5) else ""
                print(f"     {k:<12} 전={a!s:>14} 후={b!s:>14}{mark}")
