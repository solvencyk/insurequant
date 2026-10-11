#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3 (A3): build the BS spec that moves ABL생명 KR0070 / 미래에셋생명 KR0079 2023.1Q·2023.2Q master cells from the consolidated (CFS)
full balance sheet of the DART report to the separate (OFS) one.  Read-only except the output spec.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_make_spec_cfs_ofs.py [out.json]

For every (company, quarter) the DART body XML holds two full balance sheets (연결 then 별도, same line set).  The one whose asset total equals the master's
item 1 is the CFS table (the master was filled from it because FS-API returns status 013 for these two half-years and the XML fallback picked the
first full table).  For each master item: master == CFS and OFS differs -> `replace` by the OFS line; master blank and the OFS line exists -> `add`
(items 4, 14, 31 only: the lines the builder's label matcher could not read); master == CFS == OFS -> untouched; anything else is reported, not changed.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
import bspl_apply_xmlbs as X  # noqa: E402
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "_derived" / "bspl_apply_20261011" / "spec_A3_cfs_to_ofs.json"
TARGETS = [("KR0070", "2023.1Q"), ("KR0070", "2023.2Q"), ("KR0079", "2023.1Q"), ("KR0079", "2023.2Q")]
FILLABLE = {4, 14, 31}
ITEMS = [1, 2, 3, 4, 10, 11, 12, 13, 14, 15, 20, 21, 22, 23, 24, 30, 31]
NAMES = {1: "자산총계", 2: "부채총계", 3: "자본총계", 4: "기타포괄손익누계액", 10: "현금및현금성자산", 11: "당기손익-공정가치측정금융자산",
         12: "기타포괄손익-공정가치측정금융자산", 13: "상각후원가측정금융자산", 14: "재보험계약자산", 15: "유형자산", 20: "보험계약부채", 21: "재보험계약부채",
         22: "투자계약부채", 23: "차입부채", 24: "기타부채", 30: "자본금", 31: "이익잉여금"}


def full_tables(xml: Path):
    res = []
    for t in _iter_tables_with_context(xml):
        if len(t.rows) < 28 or not X.bs_like(t):
            continue
        lines = X.table_lines(t)
        iv = X.item_values(lines)
        a = iv.get(1)
        if a is None:
            continue
        unit = 1e-6 if abs(a) >= 1e10 else 1.0
        res.append({"line": t.line_no, "iv": {k: v * unit for k, v in iv.items()}, "unit": "원" if unit < 1 else "백만원"})
    return res


TOT = {}


def main():
    bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
    mv = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in bs}
    cells, notes = [], []
    for code, q in TARGETS:
        files = X.xml_files(code, q)
        assert len(files) == 1, files
        xml = files[0]
        sha = hashlib.sha256(xml.read_bytes()).hexdigest()
        tabs = full_tables(xml)
        m1 = mv[(code, 1, q)]
        cfs = [t for t in tabs if abs(t["iv"][1] - m1) < 0.6]
        ofs = [t for t in tabs if abs(t["iv"][1] - m1) >= 0.6 and 0.9 < t["iv"][1] / m1 < 1.1]
        # the summary table rounds to 백만원 (diff < 0.6 too): keep the table that reproduces the master total most exactly / has the most lines
        cfs.sort(key=lambda t: (abs(t["iv"][1] - m1), -len(t["iv"])))
        ofs.sort(key=lambda t: -len(t["iv"]))
        assert len(cfs) >= 1 and len(ofs) >= 1, (code, q, [(t["line"], t["iv"].get(1)) for t in tabs])
        cfs, ofs = cfs[0], ofs[0]
        # identity of the OFS table
        o = ofs["iv"]
        assert abs(o[1] - o[2] - o[3]) < 0.01, (code, q, o[1], o[2], o[3])
        rel = xml.relative_to(ROOT).as_posix()
        TOT[(code, q)] = (o[1], o[2], o[3])
        for item in ITEMS:
            m = mv.get((code, item, q))
            ov, cv = o.get(item), cfs["iv"].get(item)
            if ov is None:
                if m is not None and (cv is None or abs(cv - m) < 0.6):
                    notes.append(f"{code} {q} item {item}: OFS line not found, master {m} kept")
                continue
            if m is None:
                if item in FILLABLE:
                    cells.append(("add", code, q, item, None, ov, cfs["line"], ofs["line"], ofs["unit"], rel, sha))
                else:
                    notes.append(f"{code} {q} item {item}: master blank, OFS {ov:,.3f} found but not in the fill set -> reported only")
                continue
            if cv is not None and abs(cv - m) < 0.6:
                if abs(ov - m) >= 0.6:
                    cells.append(("replace", code, q, item, m, ov, cfs["line"], ofs["line"], ofs["unit"], rel, sha))
            else:
                notes.append(f"{code} {q} item {item}: master {m:,.3f} is neither CFS {cv} nor equal OFS {ov:,.3f} -> reported only")
    out = []
    for act, code, q, item, old, new, cl, ol, unit, rel, sha in cells:
        tot = TOT[(code, q)]
        scale = "원 -> 백만원" if unit == "원" else "백만원 -> 백만원"
        verb = (f"마스터 옛 값 {old:,.6f}백만원은 같은 보고서의 연결 재무상태표(line {cl}) 값이다" if act == "replace"
                else "마스터가 비어 있던 칸(연결·별도 표의 라벨 「재보험자산」·「연결~」 접두 때문에 빌더 라벨 매처가 못 읽음)")
        basis = (f"{'정정' if act == 'replace' else '신규'} 2026-10-11(round 3, A3): {verb}. 17BS 마스터는 별도(OFS) 고정인데 이 분기는 FS-API 가 status 013 이라 "
                 f"본문 XML 폴백이 연결표를 집었다(상장사 23사×2분기 전수에서 연결 혼입은 ABL생명·미래에셋생명뿐 — scripts/bspl_followup_dart_basis_verdict.py). "
                 f"정정값 = {rel} 의 별도 재무상태표(line {ol}, {unit}) 「{NAMES[item]}」 {new:,.6f}백만원. 같은 표에서 자산총계 {tot[0]:,.3f} = 부채총계 {tot[1]:,.3f} + "
                 f"자본총계 {tot[2]:,.3f}(백만원)이 닫히고 같은 보고서의 요약별도재무상태표 총계와 일치한다. 계보: DART 분기보고서 본문 XML.")
        out.append({"key": f"{code}|{item}|{q}", "item": item, "quarter": q, "action": act, "old": old, "new": round(new, 6), "line": NAMES[item],
                    "pdf": rel, "page": ol, "pdf_sha256": sha, "basis": basis, "method": "round3_fix:dart_xml_separate_full_bs", "scale": scale})
    OUT.write_text(json.dumps({"_what": "A3 CFS -> OFS for KR0070/KR0079 2023.1Q/2Q", "cells": out}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    for c in out:
        print(f"{c['action']:<8} {c['key']:<20} {('(blank)' if c['old'] is None else format(c['old'], ',.6f')):>20} -> {c['new']:>20,.6f}   (xml table line {c['page']})")
    print(f"{len(out)} cells -> {OUT}")
    for n in notes:
        print("NOTE:", n)


if __name__ == "__main__":
    main()
