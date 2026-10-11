#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PROPOSAL (not applied): master BS cells of KR0070 / KR0079 at 2023.1Q / 2023.2Q are CONSOLIDATED (CFS) values; the SEPARATE (OFS) values are in the DART
report's 요약별도재무상태표.  Lists master vs DART-OFS for items 1,2,3,4,10,15,20,21,24,30,31 (백만원)."""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402

SPECS = [("KR0070", "2023.1Q", "FY2023_Q1", 3745), ("KR0070", "2023.2Q", "FY2023_Q2", 3780), ("KR0079", "2023.1Q", "FY2023_Q1", 3223), ("KR0079", "2023.2Q", "FY2023_Q2", 4285)]
LABEL_ITEM = {"자산총계": 1, "부채총계": 2, "자본총계": 3, "기타포괄손익누계액": 4, "현금및현금성자산": 10, "유형자산": 15, "보험계약부채": 20, "재보험계약부채": 21, "기타부채": 24, "자본금": 30, "이익잉여금": 31}
bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
mv = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in bs if r["값"] is not None}

def num(s):
    s = str(s).strip().replace(",", "")
    if s in ("", "-"):
        return 0.0
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    v = float(s)
    return -v if neg else v

out = []
for code, q, fy, line in SPECS:
    d = sorted((ROOT / "data" / "dart" / fy / "raw").glob(f"{code}_*"))[0]
    xml = (sorted(d.glob("xml/*.xml")) or sorted(d.glob("*.xml")))[0]
    for t in _iter_tables_with_context(xml):
        if t.line_no != line:
            continue
        for r in t.rows:
            lab = re.sub(r"[\s\[\]]", "", r[0])
            if lab in LABEL_ITEM:
                it = LABEL_ITEM[lab]
                v = num(r[1])
                m = mv.get((code, it, q))
                out.append({"key": f"{code}|{it}|{q}", "label": r[0], "dart_ofs_mn": v, "master_mn": m, "diff_mn": None if m is None else round(m - v, 3),
                            "rel_pct": None if not m else round(100 * (m - v) / v, 3) if v else None})
        break
Path(ROOT / "data/_derived/bspl_followup_20261011/proposed_bs_corrections_cfs_to_ofs_kr0070_kr0079.json").write_text(
    json.dumps({"_note": "PROPOSAL ONLY -- not applied (this ticket allows no change of existing BS cells besides items 1 and 2). master = consolidated (CFS) table of the DART report, correct basis = separate (OFS) 요약별도재무상태표. 백만원.",
                "rows": out}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
for o in out:
    flag = "" if o["diff_mn"] in (0.0, None) and abs(o["diff_mn"] or 0) < 1 else "  <== DIFF"
    print(f"{o['key']:<16} {o['label']:<22} dart_ofs {o['dart_ofs_mn']:>14,.0f}  master {('-' if o['master_mn'] is None else format(o['master_mn'], ',.1f')):>14}  diff {o['diff_mn']} ({o['rel_pct']}%)" + flag)
