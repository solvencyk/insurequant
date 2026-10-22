# -*- coding: utf-8 -*-
"""d13: restatement note text per company (read-only).  For each company of the universe, find the first note paragraph that
announces a financial-statement restatement ('재작성' + '재무제표') in the FY2024 annual (restates 2023) and FY2025 annual report (restates 2024),
plus the interim filings FY2024_Q1..Q3 / FY2025_Q1..Q3 (restate the prior-year comparatives).  Output d13_restate_notes.json / .txt"""
import json, re, sys, glob
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant"); OUT = ROOT / "data/_derived/remaining_20261022/d_census"
rows = json.loads((OUT / "d6_rows.json").read_text(encoding="utf-8"))
codes = sorted({r["code"] for r in rows})
names = {r["code"]: r["name"] for r in rows}
TAG = re.compile(r"<[^>]+>")
PAT = re.compile(r"재무제표\s*재작성|재작성\s*재무제표|전기\s*재무제표의\s*재작성|재작성")
out = {}
for code in codes:
    out[code] = {}
    for fy in ("FY2024_Q1", "FY2024_Q2", "FY2024_Q3", "FY2024_Q4", "FY2025_Q1", "FY2025_Q2", "FY2025_Q3", "FY2025_Q4", "FY2026_Q1", "FY2026_Q2"):
        files = sorted(glob.glob(str(ROOT / f"data/dart/{fy}/raw/{code}_*/*.xml")) + glob.glob(str(ROOT / f"data/dart/{fy}/raw/{code}_*/xml/*.xml")))
        files = [f for f in files if not f.endswith("_00761.xml")]
        best = None
        for f in files:
            txt = Path(f).read_text(encoding="utf-8", errors="replace")
            for m in re.finditer(r"<P[^>]*>(.{0,1500}?)</P>", txt, re.S):
                t = TAG.sub("", m.group(1)); t = re.sub(r"\s+", " ", t).strip()
                if "재작성" in t and "재작성 등 유의사항" not in t and "재작성등" not in t.replace(" ", "") and ("보험금융" in t or "오류" in t or "질의회신" in t or "기타포괄손익" in t) and ("수정" in t or "오류" in t or "재작성되" in t or "재작성하" in t) and len(t) > 80:
                    best = (Path(f).name, t[:520]); break
            if best: break
        out[code][fy] = best
(OUT / "d13_restate_notes.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
lines = []
for code in codes:
    lines.append(f"## {names[code]}")
    for fy, b in out[code].items():
        lines.append(f"  {fy}: " + ("-" if not b else f"[{b[0]}] {b[1]}"))
(OUT / "d13_restate_notes.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("done", sum(1 for c in codes for v in out[c].values() if v), "hits")
