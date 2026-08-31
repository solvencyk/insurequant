# -*- coding: utf-8 -*-
"""Isolate the effect of exactly the 8 TFI cells this session is responsible for
(KR0005 items 47,48,49,50,51,53,54 + KR0075 items 50,51), independent of
whatever else changed in the live master from concurrent activity today.

Method: take the CURRENT live master (= "after", already contains this
session's values, confirmed byte-identical by a prior probe) and build a
"reverted" scratch copy that undoes ONLY those 8 cells (item48 back to its
prior contaminated value, the other 7 rows deleted entirely = "before").
Running the gate on both isolates exactly this session's contribution,
because every other concurrent change is identical in both copies.
Writes to scripts/_probes/ only -- never touches the live root file.
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
PY = r"C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
MASTER = ROOT / "kics_disclosure.json"
REVERTED = ROOT / "scripts" / "_probes" / "_scratch_kics_disclosure_20260831_REVERTED.json"

rows = json.loads(MASTER.read_text(encoding="utf-8"))

TO_DELETE = [("KR0005", 47), ("KR0005", 49), ("KR0005", 50), ("KR0005", 51),
             ("KR0005", 53), ("KR0005", 54), ("KR0075", 50), ("KR0075", 51)]
TO_REVERT_VALUE = {("KR0005", 48): ("29380", None)}  # (값, 값_적용후) contaminated originals

kept = []
n_deleted = 0
n_reverted = 0
for r in rows:
    code = r.get("원보험사코드")
    q = r.get("공시분기")
    item = r.get("항목번호")
    if q == "2026.2Q" and (code, item) in TO_DELETE:
        n_deleted += 1
        continue
    if q == "2026.2Q" and (code, item) in TO_REVERT_VALUE:
        v, vp = TO_REVERT_VALUE[(code, item)]
        r = dict(r)
        r["값"] = v
        if vp is None:
            r.pop("값_적용후", None)
        else:
            r["값_적용후"] = vp
        n_reverted += 1
    kept.append(r)

print(f"reverted (simulated BEFORE): deleted {n_deleted} rows, reverted {n_reverted} row-values "
      f"({len(rows)} -> {len(kept)})")
REVERTED.write_text(json.dumps(kept, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print("\n=== gate on REVERTED (true BEFORE this session's 8 cells) ===")
before = subprocess.run([PY, str(ROOT / "scripts" / "validate_kics_disclosure.py"),
                          "--master", str(REVERTED)],
                         cwd=str(ROOT), capture_output=True, encoding="utf-8", errors="replace")
print(f"exit_code={before.returncode}")

print("\n=== gate on LIVE (true AFTER, current master) ===")
after = subprocess.run([PY, str(ROOT / "scripts" / "validate_kics_disclosure.py")],
                        cwd=str(ROOT), capture_output=True, encoding="utf-8", errors="replace")
print(f"exit_code={after.returncode}")

for tag, proc in (("BEFORE(reverted)", before), ("AFTER(live)", after)):
    for line in proc.stdout.splitlines():
        if line.strip().startswith("Status counts"):
            print(f"{tag}: {line.strip()}")

# find the report files each run just wrote (newest 2 in artifacts dir)
reports = sorted((ROOT / "artifacts" / "kics_validation").glob("report_2*.json"),
                  key=lambda p: p.stat().st_mtime)
before_report, after_report = reports[-2], reports[-1]
print(f"\nbefore_report={before_report.name}  after_report={after_report.name}")

bdata = json.loads(before_report.read_text(encoding="utf-8"))
adata = json.loads(after_report.read_text(encoding="utf-8"))


def key(f):
    return (f.get("원보험사코드") or f.get("code"), f.get("공시분기") or f.get("quarter"),
            f.get("rule"), f.get("항목번호") or f.get("item"), f.get("status"))


def bucket_findings(d, codes):
    return [f for f in d.get("findings", [])
            if (f.get("원보험사코드") or f.get("code")) in codes
            and (f.get("공시분기") or f.get("quarter")) == "2026.2Q"]


for code in ("KR0005", "KR0075"):
    bf = bucket_findings(bdata, {code})
    af = bucket_findings(adata, {code})
    b_by_rule = {}
    a_by_rule = {}
    for f in bf:
        b_by_rule.setdefault(f.get("rule"), []).append(f.get("status"))
    for f in af:
        a_by_rule.setdefault(f.get("rule"), []).append(f.get("status"))
    print(f"\n=== {code} 2026.2Q findings by rule ===")
    all_rules = sorted(set(b_by_rule) | set(a_by_rule))
    for rule in all_rules:
        bcnt = {}
        for s in b_by_rule.get(rule, []):
            bcnt[s] = bcnt.get(s, 0) + 1
        acnt = {}
        for s in a_by_rule.get(rule, []):
            acnt[s] = acnt.get(s, 0) + 1
        if bcnt != acnt:
            print(f"  {rule}: BEFORE={bcnt} -> AFTER={acnt}  <<< CHANGED")
        else:
            print(f"  {rule}: {acnt} (unchanged)")

# whole-file drift check: any (code,quarter,rule,status) combination outside
# KR0005/KR0075 2026.2Q that differs between before/after reports
print("\n=== whole-file drift check (outside KR0005/KR0075 2026.2Q) ===")


def sig(d):
    out = {}
    for f in d.get("findings", []):
        c = f.get("원보험사코드") or f.get("code")
        q = f.get("공시분기") or f.get("quarter")
        if (c, q) in {("KR0005", "2026.2Q"), ("KR0075", "2026.2Q")}:
            continue
        k = (c, q, f.get("rule"), f.get("항목번호") or f.get("item"))
        out[k] = f.get("status")
    return out


bsig, asig = sig(bdata), sig(adata)
diff_keys = [k for k in (set(bsig) | set(asig)) if bsig.get(k) != asig.get(k)]
print(f"out-of-scope status changes: {len(diff_keys)}")
for k in diff_keys[:20]:
    print(f"  {k}: {bsig.get(k)} -> {asig.get(k)}")
