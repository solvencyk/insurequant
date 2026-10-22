# -*- coding: utf-8 -*-
"""d13b: second pass for companies without a hit in d13: look for the policy-change / error-correction wording
('체계적' + '배분' + '변경'|'정정'|'소급', or '오류' + ('비교표시'|'전기')) in the annual/interim filings FY2024_Q1..FY2025_Q4. Output d13b_restate_notes2.txt"""
import json, re, sys, glob
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant"); OUT = ROOT / "data/_derived/remaining_20261022/d_census"
rows = json.loads((OUT / "d6_rows.json").read_text(encoding="utf-8"))
names = {r["code"]: r["name"] for r in rows}
first = json.loads((OUT / "d13_restate_notes.json").read_text(encoding="utf-8"))
TAG = re.compile(r"<[^>]+>")
todo = sys.argv[1:] or [c for c in names if not any(v for v in first[c].values())]
lines = []
for code in sorted(todo):
    lines.append(f"## {names[code]} ({code})")
    for fy in ("FY2024_Q1", "FY2024_Q2", "FY2024_Q3", "FY2024_Q4", "FY2025_Q1", "FY2025_Q2", "FY2025_Q3", "FY2025_Q4"):
        files = sorted(glob.glob(str(ROOT / f"data/dart/{fy}/raw/{code}_*/*.xml")) + glob.glob(str(ROOT / f"data/dart/{fy}/raw/{code}_*/xml/*.xml")))
        files = [f for f in files if not f.endswith("_00761.xml")]
        hit = None
        for f in files:
            txt = Path(f).read_text(encoding="utf-8", errors="replace")
            for m in re.finditer(r"<P[^>]*>(.{0,2500}?)</P>", txt, re.S):
                t = re.sub(r"\s+", " ", TAG.sub("", m.group(1))).strip()
                if len(t) < 80: continue
                a = ("체계적" in t and "배분" in t and ("변경" in t or "정정" in t or "소급" in t) and "보험금융" in t)
                b = ("오류" in t and ("비교표시" in t or "전기" in t or "전분기" in t) and ("재작성" in t or "수정" in t))
                if a or b:
                    hit = (Path(f).name, t[:480]); break
            if hit: break
        lines.append(f"  {fy}: " + ("-" if not hit else f"[{hit[0]}] {hit[1]}"))
(OUT / ("d13b_restate_notes2_%s.txt" % ("custom" if len(sys.argv) > 1 else "auto"))).write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(l[:300] for l in lines))
