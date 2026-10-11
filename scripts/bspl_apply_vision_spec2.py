#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3 (B3/B5): second-generation vision-spec builder -- per-load closure, prior-column (R1) loads, zero-proofs, cross-filing agreement.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_vision_spec2.py <transcription.json> [--spec out.json] [--holds holds.json]

A transcription (UTF-8 JSON) is ONE balance sheet of ONE filing read from a rendered image: every printed line, current + prior-year-end column, in the printed unit.
{
 "code": "KR1105", "quarter": "2026.2Q"  (the filing's quarter), "pdf": "...", "page": 41, "dpi": 170, "unit": "천원", "scale": 0.001, "read_by": "...",
 "cols": ["2026-06-30", "2025-12-31"],
 "lines":  {"자산총계": [cur, prior], ...},
 "sums":   [[total, [parts], note, [0, 1]]],                    # closure identities; the 4th element (optional) = the columns it is checked in (default both)
 "loads":  [{"col": 0, "quarter": "2026.2Q", "map": {"20": "보험계약부채"}, "closure": ["부채총계"]},              # own column
            {"col": 1, "quarter": "2025.4Q", "map": {"13": "..."}, "closure": ["자산총계", "부채총계"], "cross": "KR1105_2026.1Q.json"},  # prior-year-end column (R1)
            {"col": 0, "quarter": "2024.2Q", "zero": {"11": "당기손익-공정가치측정금융자산"}, "closure": ["자산총계"]}],      # line absent + closed asset side -> 0
 "anchors": [{"col": 1, "quarter": "2024.4Q", "items": [13, 15], "lines": {"13": "...", "10": "..."}, "tol_mn": 0.0015}],  # master cells the column must reproduce
 "agree":  [{"with": "KR1105_2026.1Q.json", "col": 1, "col_with": 1}],        # another transcription (independent read) must print the same numbers in that column
 "note":   "extra basis text"
}
A load is emitted only if (1) every closure total it names closes in its column, (2) all anchors of that column reproduce the master, (3) every `agree` entry matches.  A failing load is
reported as HOLD (with the numbers) and written to --holds; it never aborts the others.  Cells already in the master are untouched (a differing value is reported as CONFLICT).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
NAMES = {10: "현금및현금성자산", 11: "당기손익-공정가치측정금융자산", 12: "기타포괄손익-공정가치측정금융자산", 13: "상각후원가측정금융자산", 14: "재보험계약자산", 15: "유형자산",
         20: "보험계약부채", 21: "재보험계약부채", 22: "투자계약부채", 23: "차입부채", 24: "기타부채", 30: "자본금", 31: "이익잉여금", 4: "기타포괄손익누계액"}


def fmt(v):
    return "None" if v is None else f"{v:,}"


def main():
    src = Path(sys.argv[1])
    t = json.loads(src.read_text(encoding="utf-8"))
    bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
    mv = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in bs}
    code, fq, scale = t["code"], t["quarter"], float(t["scale"])
    lines, unit = t["lines"], t["unit"]
    tol_units = float(t.get("tol_units", 0.0015 / scale + 0.5)) if unit != "억원" else None
    cols = t.get("cols", ["당기", "전기말"])
    pdf = ROOT / t["pdf"]
    sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
    pdfname = Path(t["pdf"]).name

    # ---- closure results per (total, col) ----
    clos = {}
    for entry in t.get("sums", []):
        total, parts, note = entry[0], entry[1], entry[2]
        for col in (entry[3] if len(entry) > 3 else (0, 1)):
            if lines[total][col] is None or any(lines[p][col] is None for p in parts):
                clos[(total, col)] = (None, note, None, None)
                continue
            s = sum(lines[p][col] for p in parts)
            tol = max(0.5, 0.5 * len(parts) + 0.5) if unit == "억원" else tol_units
            diff = s - lines[total][col]
            clos[(total, col)] = (abs(diff) <= tol, note, diff, tol)
    print(f"== {src.name}: {code} filing {fq} p{t['page']} unit {unit}  cols {cols}")
    for (total, col), (ok, note, diff, tol) in sorted(clos.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        print(f"  closure col{col} {total:<12} {'OK' if ok else ('n/a' if ok is None else 'FAIL')}  diff {diff if diff is None else format(diff, '+,')} (tol {tol})  {note}")

    # ---- anchors per column ----
    anchor_ok = {0: True, 1: True}
    for an in t.get("anchors", []):
        col, aq = an.get("col", 1), an["quarter"]
        lmap = {int(k): v for k, v in an.get("lines", {}).items()}
        for it in an["items"]:
            item = int(it)
            lname = lmap.get(item) or next((v for k, v in t.get("loads_map_all", {}).items() if int(k) == item), None)
            if lname is None:
                for ld in t.get("loads", []):
                    if str(item) in ld.get("map", {}):
                        lname = ld["map"][str(item)]
                        break
            if lname is None:
                print(f"  anchor {aq} item {item}: no line name")
                anchor_ok[col] = False
                continue
            pv = lines[lname][col]
            am = mv.get((code, item, aq))
            if am is None:
                print(f"  anchor {aq} item {item}: master blank -> cannot calibrate")
                anchor_ok[col] = False
                continue
            diff = pv * scale - am
            if an.get("tol_mn") is not None:
                tol = float(an["tol_mn"])
            else:
                tol = (1.0 if item in (1, 2, 3) else 0.5) * scale + 0.0015
            ok = abs(diff) <= tol
            print(f"  anchor col{col} {aq} item {item:>2} [{lname}] {pv} -> {pv * scale:,.3f} vs master {am:,.3f}  diff {diff:+.3f} (tol {tol:.3f}) {'OK' if ok else 'FAIL'}")
            if not ok:
                anchor_ok[col] = False

    # ---- agree with another transcription ----
    agree_ok, agree_msg = {0: True, 1: True}, {0: [], 1: []}
    for ag in t.get("agree", []):
        other = json.loads((src.parent / ag["with"]).read_text(encoding="utf-8"))
        col, colw = ag.get("col", 1), ag.get("col_with", 1)
        bad, n = [], 0
        for name, vals in lines.items():
            if name in other["lines"] and vals[col] is not None and other["lines"][name][colw] is not None:
                n += 1
                if abs(vals[col] - other["lines"][name][colw]) > 0:
                    bad.append((name, vals[col], other["lines"][name][colw]))
        missing = [nm for nm in lines if nm not in other["lines"]]
        print(f"  agree col{col} with {ag['with']} col{colw}: {n} common lines, {len(bad)} differ" + (f" {bad}" if bad else ""))
        if bad or n < 10:
            agree_ok[col] = False
        agree_msg[col].append(f"{ag['with']} 의 같은 열과 공통 {n}개 줄이 전부 일치")

    # ---- loads ----
    cells, holds = [], []
    for ld in t.get("loads", []):
        col, q = ld.get("col", 0), ld["quarter"]
        why = []
        for total in ld.get("closure", []):
            ok, note, diff, tol = clos.get((total, col), (None, "no check", None, None))
            if ok is not True:
                why.append(f"closure col{col} {total}: diff {diff if diff is None else format(diff, '+,')} (tol {tol}) {note}")
        if not anchor_ok[col]:
            why.append(f"anchor col{col} failed")
        if not agree_ok[col]:
            why.append(f"agree col{col} failed")
        items = [(int(k), v, False) for k, v in ld.get("map", {}).items()] + [(int(k), v, True) for k, v in ld.get("zero", {}).items()]
        if not items:
            continue
        for item, lname, is_zero in items:
            key = f"{code}|{item}|{q}"
            if is_zero:
                val, cur = 0.0, None
            else:
                cur = lines[lname][col]
                if cur is None:
                    why.append(f"line {lname} col{col} not printed")
                val = None if cur is None else round(cur * scale, 6)
            if why:
                holds.append({"key": key, "item": item, "quarter": q, "line": lname, "reason": "; ".join(why), "pdf": t["pdf"], "page": t["page"],
                              "value_read": val})
                print(f"  HOLD {key:<18} {lname}: " + "; ".join(why))
                continue
            if (code, item, q) in mv:
                ex = mv[(code, item, q)]
                tag = "same" if abs(ex - val) <= 0.0015 else "CONFLICT"
                print(f"  item {item}: master already {ex} (statement {val}) -> untouched [{tag}]")
                continue
            prec = "원 단위" if unit == "원" else f"±{0.5 * scale:,.4f}백만원(표시 단위 {unit} 반올림)"
            sums_note = "; ".join(clos[(tot, col)][1] for tot in ld.get("closure", []) if (tot, col) in clos)
            if col == 0 and t.get("source_kind") == "text":
                where = f"{code} {q} 정기경영공시 {pdfname} p{t['page']} 재무상태표(단위 {unit}; 텍스트층 판독) {cols[0]} 열"
            elif col == 0:
                where = f"{code} {q} 정기경영공시 {pdfname} p{t['page']} 재무상태표(8-1, 단위 {unit}; 표가 이미지 쪽이라 텍스트층에 없어 렌더링 {t.get('dpi', '')}dpi 판독) {cols[0]} 열"
            else:
                where = (f"{code} {q} = 재보사 최신 공시({fq} 정기경영공시 {pdfname} p{t['page']})의 재무상태표(8-1, 단위 {unit}; 이미지 쪽, 렌더링 {t.get('dpi', '')}dpi 판독) "
                         f"전기말({cols[1]}) 열 [R1: owner 2026-10-09 재보사 최신 공시 전기 칸 채택]")
            anc = [an for an in t.get("anchors", []) if an.get("col", 1) == col]
            anc_txt = ""
            if anc:
                anc_txt = " 보정: " + "; ".join(f"같은 열의 {len(a['items'])}개 줄(항목 {','.join(str(i) for i in a['items'])})이 마스터 {a['quarter']} 값을 {'표시 단위 반올림' if a.get('tol_mn') is None else '±' + str(a['tol_mn']) + '백만원'} 안에서 재현" for a in anc) + "."
            if is_zero:
                side, tot_name = ("부채", "부채총계") if item >= 20 else ("자산", "자산총계")
                basis = (f"신규 2026-10-11(round 3, B3): {where} 에는 「{NAMES[item]}」 줄이 없다. {side} 줄을 모두 열거했고 그 합이 {tot_name}로 닫히므로({sums_note}) 이 항목은 0 이다(폐합 증명).{anc_txt} "
                         f"{t.get('note', '')} {t.get('read_by', '')} (inbox/parser/20261011T1130Z B3)")
                method = f"round3_fill:{'pdf_text' if t.get('source_kind') == 'text' else 'vision_8-1'}:zero_closure{'_prior' if col == 1 else ''}"
                line = NAMES[item]
            else:
                basis = (f"신규 2026-10-11(round 3, B3): {where} 「{lname}」 {fmt(cur)} {unit} = {val:,.6f}백만원, 정밀도 {prec}. 판독 검산: {sums_note}.{anc_txt}"
                         + (" 교차: " + "; ".join(agree_msg[col]) + "." if agree_msg[col] and col == 1 else "")
                         + f" {t.get('note', '')} {t.get('read_by', '')} (inbox/parser/20261011T1130Z B3)")
                method = f"round3_fill:{'pdf_text' if t.get('source_kind') == 'text' else 'vision_8-1'}{'_prior' if col == 1 else ''}:{lname}"
                line = NAMES[item]
            cells.append({"key": key, "item": item, "quarter": q, "action": "add", "old": None, "new": val, "line": line, "pdf": t["pdf"], "page": t["page"], "pdf_sha256": sha,
                          "basis": " ".join(basis.split()), "method": method, "scale": f"{unit} -> 백만원"})
            print(f"  LOAD {key:<18} {val:>16,.3f}  ({'zero-proof' if is_zero else lname}; col{col})")
    if "--spec" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--spec") + 1])
        d = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {"cells": []}
        have = {c["key"] for c in d["cells"]}
        d["cells"] += [c for c in cells if c["key"] not in have]
        out.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("spec ->", out, f"({len(d['cells'])} cells)")
    if "--holds" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--holds") + 1])
        d = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {"holds": []}
        have = {h["key"] + "|" + h.get("reason", "")[:40] for h in d["holds"]}
        d["holds"] += [h for h in holds if h["key"] + "|" + h.get("reason", "")[:40] not in have]
        out.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("holds ->", out, f"({len(d['holds'])})")


if __name__ == "__main__":
    main()
