# -*- coding: utf-8 -*-
"""d16: independent spot check (no scripts/ or src/ imports): is the FS-API prior-column value of the closing buckets printed in the later filing's XML?
For each bucket: items 17,22,24,25,31 (mn) -> look for the printed number in 원 / 천원 / 백만원 form inside the later filing's XML files (not _00761)."""
import json, sys, glob, re
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant"); OUT = ROOT / "data/_derived/remaining_20261022/d_census"
rows = json.loads((OUT / "d6_rows.json").read_text(encoding="utf-8")); disp = json.loads((OUT / "d9_disposition.json").read_text(encoding="utf-8"))
targets = [r for r in rows if r["scope"] == "A51" and disp[f"{r['code']}|{r['q']}"].get("pl_adoptable")]
cache = {}
res = []
for r in targets:
    fy = f"FY{int(r['q'][:4]) + 1}_Q{r['q'][5]}"
    files = sorted(glob.glob(str(ROOT / f"data/dart/{fy}/raw/{r['code']}_*/*.xml")) + glob.glob(str(ROOT / f"data/dart/{fy}/raw/{r['code']}_*/xml/*.xml")))
    files = [f for f in files if not f.endswith("_00761.xml")]
    texts = []
    for f in files:
        if f not in cache: cache[f] = Path(f).read_text(encoding="utf-8", errors="replace")
        texts.append(cache[f])
    blob = "\n".join(texts)
    found = {}
    for i in (17, 22, 24, 25, 31):
        v = r["its"].get(str(i), {}).get("prior")
        if v is None: continue
        forms = {"won": f"{abs(round(v * 1e6)):,}", "thou": f"{abs(round(v * 1e3)):,}", "mn": f"{abs(round(v)):,}"}
        hit = [u for u, s in forms.items() if len(s) >= 7 and s in blob]
        found[i] = hit or ["-"]
    res.append((r["name"], r["q"], fy, len(files), found))
lines = [f"{n} {q} later={fy} files={nf} " + " ".join(f"i{i}:{'/'.join(h)}" for i, h in f.items()) for n, q, fy, nf, f in res]
tot = sum(1 for *_, f in res for h in f.values()); ok = sum(1 for *_, f in res for h in f.values() if h != ["-"])
lines.append(f"printed prior value found in later-filing XML: {ok}/{tot} cells (units: won/thou/mn; numbers < 7 chars not accepted)")
(OUT / "d16_xml_spotcheck.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
