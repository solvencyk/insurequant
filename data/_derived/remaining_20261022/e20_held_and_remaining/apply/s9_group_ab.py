#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 9: KR0082 2023.1Q / 2023.2Q (owner gold overlap) and KR0032 2023.1Q: original-vintage print (old layout) versus gold / master versus latest comparative -> s9_group_ab.txt (read-only)"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import e20_oldlayout as OL  # noqa: E402
import e20_read as R  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ROOT = R.X.ROOT
live = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
M = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in live}
gold = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
G = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold["set"]}
L = []

for q, ofy, lfy, caption in (("2023.1Q", "FY2023_Q1", "FY2024_Q1", r"분 기 포 괄 손 익 계 산 서"), ("2023.2Q", "FY2023_Q2", "FY2024_Q2", r"반 기 포 괄 손 익 계 산 서")):
    code = "KR0082"
    p = R.X.main_xml(code, ofy)
    s4 = R.X.find_titles(R.X.load_lines(p), r"^<TITLE[^>]*>4\. 재무제표")
    cap, rows = OL.read_table(p, caption.replace(" ", " "), start_after=s4[0])
    g_cum = 0 if ofy == "FY2023_Q1" else 1
    L.append(f"===== {code} {q} original {R.X.rel(p)} caption L{cap} (data table rows {len(rows)})")
    want = {"I. 보험서비스손익": "parent 보험서비스손익 (item 1)", "1. 보험손익": "child 보험손익", "(3) 기타사업비": "item 16", "II. 투자손익": "item 18 (gross)", "III. 보험금융손익": "item 19"}
    vals = {}
    for r in rows:
        nl = OL.norm_label(r["label"])
        for k, desc in want.items():
            if nl == OL.norm_label(k):
                v, ln, txt = OL.group_value(r["cells"], g_cum)
                vals[k] = (v, ln, txt)
                L.append(f"   [{r['label'].strip()}] cum-current = {txt} @L{ln}  -> {v / 1e6 if v is not None else None} mn   ({desc})")
    o1 = vals["I. 보험서비스손익"][0] / 1e6
    o16 = vals["(3) 기타사업비"][0] / 1e6
    o18 = vals["II. 투자손익"][0] / 1e6
    o19 = vals["III. 보험금융손익"][0] / 1e6
    o17 = o18 + o19
    orig = {1: o1, 16: o16, 17: o17, 18: o18, 19: o19}
    # later
    sl = R.Stmt(code, lfy)
    vl = R.read_vector(sl, "prior", "cum")
    L.append(f"   later {sl.rel} fmt={sl.fmt} unit={sl.unit}")
    for it in (1, 16, 17, 18, 19, 20, 21, 22, 23, 24):
        g = G.get((code, it, q))
        m = M.get((code, it, q))
        o = orig.get(it)
        l = vl[it]["val"]
        L.append(f"   i{it:>2} master={m}  gold={'-' if g is None else g['값']}  gold.was={'-' if g is None else g.get('was')}  orig_print={o}  later_prior={l:.6f}  "
                 f"gold==orig {'-' if (g is None or o is None) else abs(g['값'] - o) <= 2e-5}  gold==later {'-' if g is None else abs(g['값'] - l) <= 2e-5}  later-master={'-' if m is None else format(l - m, '+.6f')}")
        if it in (1, 16, 17, 18):
            L.append("        later parts: " + " || ".join(f"[{pp.label}] L{pp.line} {pp.printed} sign{pp.sign}" for pp in vl[it]["parts"]))
text = "\n".join(L)
(HERE / "s9_group_ab.txt").write_text(text + "\n", encoding="utf-8", newline="\n")
print(len(text))
