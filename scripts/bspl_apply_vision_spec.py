#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3 (B3/B5): turn a visually transcribed balance sheet into BS `add` cells -- with closure checks and year-end anchor calibration.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_vision_spec.py <transcription.json> [--spec out.json] [--no-anchor-ok]

Transcription file (UTF-8 JSON), one balance sheet of one filing, read from a rendered page image (190-240 dpi crops, see scripts/bspl_apply_render.py):
{
 "code": "KR0049", "quarter": "2024.3Q", "pdf": "data/disclosure/FY2024_Q3/raw/KR0049_..._v20251020.pdf", "page": 25, "unit": "억원" | "천원" | "원" | "백만원",
 "read_by": "text of the how it was read",
 "lines": {"자산총계": [cur, prior], "운용자산": [cur, prior], ...},       # every printed line, current and prior-year-end column, in the printed unit
 "sums":   [["total", ["part1","part2",...], "sum lines must equal this total"], ...],
 "map":    {"14": "재보험계약자산", "15": "유형자산"},                      # master item -> printed line (cells to load when blank in the master)
 "anchor": {"quarter": "2023.4Q", "items": [14, 15, 12, 1]},               # master year-end cells that the PRIOR column must reproduce (tolerance = rounding of the unit)
 "scale":  100.0                                                          # printed unit -> 백만원 (억원 100, 천원 0.001, 원 1e-6, 백만원 1)
}
Checks (all must pass or nothing is produced): every `sums` entry closes within the unit rounding (1 unit per summed part, 0.5 minimum), the anchor items reproduce the master's
year-end cells within 0.5 unit (+0.0015 백만원), and each mapped value sits in the printed line.  Output cells are `add` cells for bspl_apply_bs_fix.py.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
TOL_UNIT = 0.5                     # half a printed unit (rounding of a single printed number)


def main():
    src = Path(sys.argv[1])
    t = json.loads(src.read_text(encoding="utf-8"))
    bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
    mv = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in bs}
    code, q, scale = t["code"], t["quarter"], float(t["scale"])
    unit_mn = scale                                    # 1 printed unit in 백만원
    lines = t["lines"]
    ok = True
    # ---- closure checks ----
    for total, parts, note in t.get("sums", []):
        for col, cname in ((0, "cur"), (1, "prior")):
            if lines[total][col] is None or any(lines[p][col] is None for p in parts):
                continue
            s = sum(lines[p][col] for p in parts)
            tol = max(TOL_UNIT, 0.5 * len(parts) + 0.5) if t["unit"] in ("억원",) else 0.0015 / unit_mn + 0.5
            if abs(s - lines[total][col]) > tol:
                print(f"  CLOSURE FAIL [{cname}] {total}: sum({'+'.join(parts)}) = {s} vs {lines[total][col]}  ({note})")
                ok = False
    # ---- anchor calibration ----
    anc = t.get("anchor")
    mapped = {int(k): v for k, v in t["map"].items()}
    if anc:
        aq = anc["quarter"]
        for it in anc["items"]:
            item = int(it)
            lname = mapped.get(item) or t.get("anchor_lines", {}).get(str(item))
            if lname is None:
                print(f"  anchor item {item}: no line name")
                ok = False
                continue
            pv = lines[lname][1]
            am = mv.get((code, item, aq))
            if am is None:
                print(f"  anchor item {item}: master {aq} blank")
                ok = False
                continue
            diff = pv * unit_mn - am
            tol = (1.0 if item in (1, 2, 3) else TOL_UNIT) * unit_mn + 0.0015      # printed totals may be off by one unit (sum of rounded parts)
            print(f"  anchor {aq} item {item:>2} [{lname}] prior {pv} -> {pv * unit_mn:,.3f} vs master {am:,.3f}  diff {diff:+.3f} (tol {tol:.3f}) {'OK' if abs(diff) <= tol else 'FAIL'}")
            if abs(diff) > tol:
                ok = False
    if not ok:
        print("NOT LOADABLE (a check failed)")
        sys.exit(2)
    # ---- cells ----
    pdf = ROOT / t["pdf"]
    sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
    cells = []
    for item, lname in sorted(mapped.items()):
        cur = lines[lname][0]
        if cur is None:
            continue
        val = round(cur * unit_mn, 6)
        if (code, item, q) in mv:
            print(f"  item {item}: master already {mv[(code, item, q)]} (statement {val}) -> untouched")
            continue
        names = {10: "현금및현금성자산", 11: "당기손익-공정가치측정금융자산", 12: "기타포괄손익-공정가치측정금융자산", 13: "상각후원가측정금융자산", 14: "재보험계약자산",
                 15: "유형자산", 20: "보험계약부채", 21: "재보험계약부채", 22: "투자계약부채", 23: "차입부채", 24: "기타부채", 30: "자본금", 31: "이익잉여금", 4: "기타포괄손익누계액"}
        prec = f"±{TOL_UNIT * unit_mn:,.1f}백만원(표시 단위 {t['unit']} 반올림)" if t["unit"] in ("억원",) else "원 단위"
        basis = (f"신규 2026-10-11(round 3, B3): {code} {q} 정기경영공시 {Path(t['pdf']).name} p{t['page']} 재무상태표(8-1, 단위 {t['unit']}; 표가 이미지 쪽이라 텍스트층에 없어 렌더링 {t.get('dpi', '')}dpi 판독) "
                 f"「{lname}」 {cur:,} {t['unit']} = {val:,.6f}백만원, 정밀도 {prec}. 판독 검산: " +
                 "; ".join(f"{n}" for _tot, _parts, n in t.get("sums", [])) +
                 (f". 보정: 같은 표 전기말 열의 {len(anc['items'])}개 줄이 마스터 {anc['quarter']} 값을 표시 단위 반올림 안에서 재현" if anc else "") +
                 f". {t.get('read_by', '')} (inbox/parser/20261011T1130Z B3)")
        cells.append({"key": f"{code}|{item}|{q}", "item": item, "quarter": q, "action": "add", "old": None, "new": val, "line": names[item], "pdf": t["pdf"], "page": t["page"],
                      "pdf_sha256": sha, "basis": basis, "method": f"round3_fill:vision_8-1:{lname}", "scale": f"{t['unit']} -> 백만원"})
    for c in cells:
        print(f"  LOAD {c['key']:<18} {c['new']:>16,.3f}")
    if "--spec" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--spec") + 1])
        d = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {"cells": []}
        keys = {c["key"] for c in d["cells"]}
        d["cells"] += [c for c in cells if c["key"] not in keys]
        out.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("spec ->", out, f"({len(d['cells'])} cells)")


if __name__ == "__main__":
    main()
