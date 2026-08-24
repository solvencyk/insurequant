# -*- coding: utf-8 -*-
"""Extract the TFI table's own '기본자본'/'보완자본' parent rows for Korean Re (KR1000),
anchored relative to the already-validated item47 ('보완자본 한도 적용 전') position —
adapted copy of scripts/fix_20260821_tier2_limit_lines.py::extract_tier2's page-finding +
line-building logic (not importing, since we need the intermediate line-index where item47
was found, which that function doesn't expose). Read-only. 2026-08-22."""
import io
import re
import sys
from pathlib import Path

import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

ZERO = {"-", "─", "–", "—", "ㅡ", "", "0"}
NUMRE = re.compile(r"^\(?-?[\d,]+(\.\d+)?\)?%?$")
DECOR = {"·", "‧", "∙", "(", ")", "%", "(%)", "|", ",", " "}


def _num(tok):
    t = str(tok).strip().replace(" ", "").replace("%", "")
    if t in ZERO:
        return None if t == "" else 0.0
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


def _collect_values(lines, start, need=2):
    vals = []
    j = start
    while j < len(lines) and len(vals) < need:
        toks = lines[j].split()
        stop = False
        for tok in toks:
            if len(vals) >= need:
                break
            t = tok.strip()
            if t in DECOR or t == "":
                continue
            if NUMRE.match(t) or t in ZERO:
                vals.append(_num(t))
                continue
            stop = True
            break
        if stop:
            return vals, j
        j += 1
    return vals, j


def norm(s):
    return s.replace(" ", "")


def extract(pdf):
    doc = fitz.open(pdf)
    try:
        page_texts = [doc[i].get_text() for i in range(doc.page_count)]
    finally:
        doc.close()
    matched = {i for i, t in enumerate(page_texts)
               if "공통적용" in t and "보완자본" in t and "한도" in t}
    if not matched:
        return None
    include = set(matched)
    for i in matched:
        if i + 1 < len(page_texts):
            include.add(i + 1)
    lines = []
    for i in sorted(include):
        lines.extend(x.strip() for x in page_texts[i].splitlines())

    if norm("보완자본 한도 적용 전") in {norm(l) for l in lines}:
        idx = next(i for i, l in enumerate(lines) if norm(l) == norm("보완자본 한도 적용 전"))
        if idx + 1 < len(lines) and norm(lines[idx + 1]) == norm("보완자본 한도 적용 전"):
            deduped = []
            for l in lines:
                if deduped and deduped[-1].strip() == l.strip():
                    continue
                deduped.append(l)
            lines = deduped

    target47 = norm("보완자본 한도 적용 전")
    k = 0
    pos47 = None
    while k < len(lines):
        if norm(lines[k]) == target47:
            pos47 = k
            break
        k += 1
    if pos47 is None:
        return {"error": "item47 라벨 못 찾음"}

    # backward-scan from pos47 for nearest 기본자본/보완자본 labels (parent rows)
    result = {}
    j = pos47 - 1
    want = ["보완자본", "기본자본"]
    while j >= 0 and want:
        s = norm(lines[j])
        if want and s == want[0]:
            label = want.pop(0)
            vals, _ = _collect_values(lines, j + 1, need=2)
            if len(vals) == 1:
                vals = [vals[0], vals[0]]
            result[label] = vals if vals else None
        j -= 1

    # forward from pos47: capture 47/48/49 values too for cross-check
    vals47, nxt = _collect_values(lines, pos47 + 1, need=2)
    if len(vals47) == 1:
        vals47 = [vals47[0], vals47[0]]
    result["item47"] = vals47
    return result


quarters = ["2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q"]
periods = ["FY2023_Q2", "FY2023_Q3", "FY2023_Q4", "FY2024_Q1", "FY2024_Q2", "FY2024_Q3", "FY2024_Q4"]
for q, p in zip(quarters, periods):
    pdf = ROOT / "data/disclosure" / p / "raw" / "KR1000_코리안리.pdf"
    r = extract(pdf)
    print(q, r)
