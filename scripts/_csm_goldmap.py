# -*- coding: utf-8 -*-
"""Generate the CSM waterfall coverage + gold-needed map (docs/csm_coverage_goldmap.md).
Categorizes every (company, quarter) by detection confidence using gold validation +
continuity heuristics (within-year 기초 constant under YTD; year-boundary 기말≈기초)."""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
rows = json.loads((ROOT / "data/dart/viz/csm_waterfall_master_diag.json").read_text(encoding="utf-8"))

by, names, sb = defaultdict(dict), {}, {}
for r in rows:
    by[(r["원수사명"], r["공시분기"])][r["항목번호"]] = r["값"]
    names[r["원수사명"]] = r["티커"]
    sb[r["원수사명"]] = r["생손보여부"]

QS = [f"{y}.{q}Q" for y in (2023, 2024, 2025, 2026) for q in (1, 2, 3, 4)]
QS = [q for q in QS if q != "2026.2Q"][:13]  # 2023.1Q .. 2026.1Q

GOLD = {  # company -> {quarter: gold 기초(억)}
    "메리츠화재": {"2025.4Q": 111878.9}, "KB손해보험": {"2025.4Q": 88204.8},
    "삼성화재": {"2025.4Q": 140739.1}, "한화손해보험": {"2025.4Q": 38032.2},
    "한화생명": {"2025.4Q": 91091.4, "2024.4Q": 92384.88},
    "삼성생명": {"2025.4Q": 129020.2, "2024.4Q": 122473.72},
}

def gname(part):
    for n in names:
        if part in n:
            return n
    return None

companies = sorted(by, key=lambda k: k[0])
comp_names = sorted({n for n, _q in by})

lines = []
lines.append("# CSM Waterfall — Coverage & Gold-Needed Map")
lines.append("")
lines.append("Generated from `data/dart/viz/csm_waterfall_master_diag.json`.")
lines.append("Value = 기초 CSM (item 1), 억원, 별도(separate)·원수(issued) basis.")
lines.append("")
lines.append("Confidence is judged by gold validation + continuity (under YTD disclosure,")
lines.append("기초 is constant within a fiscal year; 기말[Q4,N] should ~ 기초[Q1,N+1]).")
lines.append("")

# --- gold validation summary
lines.append("## 1. Gold-validated (hand-built answer sheets) — ALL PASS")
lines.append("")
lines.append("| Company | Quarter | Gold 기초(억) | Parser 기초(억) | Status |")
lines.append("|---|---|---|---|---|")
for part, qg in GOLD.items():
    n = gname(part) or part
    for q, g in qg.items():
        v = by.get((n, q), {}).get(1)
        ok = v is not None and abs(v - g) <= max(1.0, abs(g) * 0.002)
        lines.append(f"| {part} | {q} | {g} | {v} | {'OK' if ok else 'FAIL'} |")
lines.append("")

# --- per company continuity classification
def classify(n):
    series = {q: by.get((n, q), {}).get(1) for q in QS if (n, q) in by}
    vals = [v for v in series.values() if v is not None]
    if not vals:
        return "no-data", []
    med = sorted(vals)[len(vals)//2]
    issues = []
    # garbage: any quarter < 25% of median magnitude (or wrong sign vs median)
    for q, v in series.items():
        if v is None:
            continue
        if abs(med) > 1000 and abs(v) < 0.25 * abs(med):
            issues.append(f"{q}={v} (<<median {med:.0f})")
    # within-year non-constant
    yr = defaultdict(dict)
    for q, v in series.items():
        if v is not None:
            yr[q[:4]][q] = v
    maxdev = 0.0
    for y, om in yr.items():
        vv = list(om.values())
        if len(vv) >= 2 and max(abs(x) for x in vv) > 1:
            dev = (max(vv) - min(vv)) / max(abs(max(vv)), abs(min(vv)), 1)
            maxdev = max(maxdev, dev)
    if issues:
        return "BROKEN", issues
    if maxdev > 0.15:
        return "wobble-large", [f"within-year dev {maxdev*100:.0f}%"]
    if maxdev > 0.02:
        return "wobble-minor", [f"within-year dev {maxdev*100:.0f}%"]
    return "consistent", []

cats = defaultdict(list)
for n in comp_names:
    c, det = classify(n)
    cats[c].append((n, det))

gold_names = {gname(p) for p in GOLD}
lines.append("## 2. Classification (non-gold companies are UNVALIDATED — continuity only)")
lines.append("")
order = ["BROKEN", "wobble-large", "wobble-minor", "consistent", "no-data"]
labelmap = {
    "BROKEN": "BROKEN — wrong/garbage detection, NEEDS GOLD or extractor fix",
    "wobble-large": "Large wobble (>15% within-year) — likely 별도/연결 or restatement; verify w/ gold",
    "wobble-minor": "Minor wobble (2-15%) — probably 별도/연결 quarterly-vs-annual; low priority",
    "consistent": "Consistent (<2% within-year) — looks good (unvalidated unless gold)",
    "no-data": "No CSM detected (PAA-only or format unsupported)",
}
for cat in order:
    if not cats[cat]:
        continue
    lines.append(f"### {labelmap[cat]}")
    lines.append("")
    for n, det in sorted(cats[cat]):
        tag = " [GOLD]" if n in gold_names else ""
        d = ("; ".join(det)) if det else ""
        lines.append(f"- **{n}**{tag} ({sb.get(n,'')}) {d}")
    lines.append("")

# --- explicit gold-needed list
lines.append("## 3. GOLD-NEEDED list (please hand-build answer sheets for these)")
lines.append("")
lines.append("Priority — these are wrong or unverifiable at specific quarters:")
lines.append("")
need = []
for n, det in cats["BROKEN"]:
    need.append((n, "BROKEN", "; ".join(det)))
for n, det in cats["wobble-large"]:
    need.append((n, "large-wobble", "; ".join(det)))
for n, _ in cats["wobble-minor"]:
    if n not in gold_names:
        need.append((n, "minor-wobble", "optional"))
lines.append("| Company | Issue | Detail |")
lines.append("|---|---|---|")
for n, kind, d in need:
    lines.append(f"| {n} | {kind} | {d} |")
lines.append("")
lines.append("Known specific defects (diagnosed):")
lines.append("- **삼성생명 2025.1Q** = 70,969억 (should be ~129,020). Cause: 2025.1Q table")
lines.append("  extraction truncated the caption ('상품라인'/'출재' markers lost), so per-segment")
lines.append("  sum + 출재 exclusion don't fire; one segment (건강 7,096,915백만) is picked instead.")
lines.append("  원수 별도 segments sum = 4,760,509+7,096,915+1,044,599 = 12,902,023백만 ~ gold.")
lines.append("  Fix needs the table extractor to preserve parent-caption context.")
lines.append("- **DB손해보험 2025** (all quarters) collapsed 122K->17K (Q1=-96.6 garbage).")
lines.append("  FY2025 filing uses a structure the detector misreads. 2023-2024 OK (~116-122K).")
lines.append("- **롯데손해보험 2025** Q1/Q4 garbage (134.7 / 60.5). 동양생명 2025.2Q = 0.")
lines.append("")

# --- full matrix
lines.append("## 4. Full 기초(억) matrix (company x quarter)")
lines.append("")
lines.append("| Company | " + " | ".join(q[2:] for q in QS) + " |")
lines.append("|" + "---|" * (len(QS) + 1))
for n in comp_names:
    cells = []
    for q in QS:
        v = by.get((n, q), {}).get(1)
        cells.append("" if v is None else f"{v:.0f}")
    lines.append(f"| {n} | " + " | ".join(cells) + " |")
lines.append("")

(ROOT / "docs" / "csm_coverage_goldmap.md").write_text("\n".join(lines), encoding="utf-8")
print("wrote docs/csm_coverage_goldmap.md")
print(f"BROKEN: {[n for n,_ in cats['BROKEN']]}")
print(f"large-wobble: {[n for n,_ in cats['wobble-large']]}")
print(f"minor-wobble: {[n for n,_ in cats['wobble-minor']]}")
print(f"consistent: {[n for n,_ in cats['consistent']]}")
print(f"no-data: {[n for n,_ in cats['no-data']]}")
