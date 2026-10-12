"""c4_evidence_from_dart.py (parser-kics, ticket 20261012T1230Z) -- READ ONLY.

For every 신종자본증권 in the inventory (c1) find the issuer's own wording in the local DART dumps (c3 dart_sections/*.txt, 사업보고서 / 반기보고서
"자본으로 인정되는 채무증권의 발행" sections and the 신종자본증권 notes):
  - locate the bond by its 발행일 (any of: 2024년 07월 17일 / 2024.07.17 / 2024-07-17 / 2024.7.17 ...), newest report first
  - take the text window from that date line to the next bond's 발행일 label (max 60 lines)
  - report: coupon / rate-adjustment sentence and every sentence containing a step-up marker (스텝업|Step-up|금리상향|가산금리 ... 가산)
Output: census_evidence_dart.csv (utf-8-sig) + census_evidence_dart.json.  The classification and grade are decided in c7 from the evidence table c6 (this file is only the quote finder).

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_securities_classification_census_20261012/c4_evidence_from_dart.py
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
HERE = Path(__file__).resolve().parent
SEC = HERE / "dart_sections"
inv = json.loads((HERE / "census_inventory.json").read_text(encoding="utf-8"))["rows"]

STEP = re.compile(r"스텝\s*업|st[ea]p[\s-]*up|setp[\s-]*up|금리\s*상향|상향\s*조정|가산금리[^.]{0,40}가산|가산한\s*금리|\+\s*1\.00\s*%", re.I)
RESET = re.compile(r"이자율[^.]{0,20}조정|기준금리[^.]{0,30}조정|재설정|재산정")


def date_patterns(iso):
    y, m, d = iso.split("-")
    mi, di = int(m), int(d)
    return [
        f"{y}년\\s*0?{mi}월\\s*0?{di}일", f"{y}\\s*[.\\-/]\\s*0?{mi}\\s*[.\\-/]\\s*0?{di}(?!\\d)", f"{y}-{m}-{d}",
    ]


def load_dump(fn):
    lines = []
    sec = False
    for ln in fn.read_text(encoding="utf-8").splitlines():
        if ln.startswith("## SECTION") or ln.startswith("## NOTE HITS"):
            sec = True
            continue
        if sec and " | " in ln:
            no, txt = ln.split(" | ", 1)
            try:
                lines.append((int(no.strip()), txt.strip()))
            except ValueError:
                pass
    return lines


dumps = {}
for fn in sorted(SEC.glob("*.txt")):
    code = fn.name.split("_")[0]
    period = "_".join(fn.name.split("_")[1:3])
    dumps.setdefault(code, []).append((period, fn, load_dump(fn)))
for code in dumps:
    dumps[code].sort(key=lambda t: t[0], reverse=True)  # newest period first (FY2026_Q2 > FY2025_Q4 ...)

out = []
for r in inv:
    if r["tier"] != "hybrid" or not r["issue_date"]:
        continue
    found = None
    for period, fn, lines in dumps.get(r["code"], []):
        pats = [re.compile(p) for p in date_patterns(r["issue_date"])]
        for i, (no, txt) in enumerate(lines):
            if any(p.search(txt) for p in pats) and len(txt) < 80:
                # window: this line .. next "발행일" label (or 60 lines)
                j = i + 1
                while j < len(lines) and j - i < 70 and not re.match(r"^발행일\s*\|?\s*$", lines[j][1]) and not re.match(r"^구\s*분\s*\|?\s*$", lines[j][1]):
                    j += 1
                found = (period, fn.name, lines[i:j])
                break
        if found:
            break
    row = {"code": r["code"], "company": r["company"], "issue_date": r["issue_date"], "name": r["name"][:50], "face_eok": r["face_eok"],
           "coupon_inventory": r["coupon_pct"], "report": None, "line_from": None, "line_to": None, "step_marker_sentences": "", "reset_sentences": "", "window_text": ""}
    if found:
        period, fname, win = found
        txts = [t for _, t in win]
        joined = " / ".join(txts)
        row.update({"report": f"{period} {fname}", "line_from": win[0][0], "line_to": win[-1][0], "window_text": joined[:1500]})
        steps = [t for t in txts if STEP.search(t)]
        resets = [t for t in txts if RESET.search(t) and not STEP.search(t)]
        row["step_marker_sentences"] = " || ".join(s[:420] for s in steps)
        row["reset_sentences"] = " || ".join(s[:300] for s in resets[:2])
    out.append(row)

with open(HERE / "census_evidence_dart.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0]))
    w.writeheader()
    w.writerows(out)
(HERE / "census_evidence_dart.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
nf = [o for o in out if not o["report"]]
print("hybrids:", len(out), "| located in a DART dump:", len(out) - len(nf), "| not located:", len(nf))
for o in out:
    st = "STEP" if o["step_marker_sentences"] else ("reset-only" if o["reset_sentences"] else ("located-no-wording" if o["report"] else "NOT LOCATED"))
    print(f"{o['code']} {o['issue_date']} {o['face_eok']!s:>8} {st:<18} {o['report'] or ''}")
