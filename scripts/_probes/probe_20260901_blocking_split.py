# -*- coding: utf-8 -*-
"""53 RED 을 (제외분 / tier2면제 / life8면제 / blocking) 으로 완전분할."""
import json, sys
from pathlib import Path
ROOT = Path(r"C:/Users/sangwook.cho/Desktop/insurequant")
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT/"scripts"))
import validate_kics_disclosure as V

rep = json.loads((ROOT/"artifacts/kics_validation/report_latest.json").read_text(encoding="utf-8"))
fs = rep["findings"]
recs = json.loads((ROOT/"kics_disclosure.json").read_text(encoding="utf-8"))
if isinstance(recs, dict): recs = recs.get("records") or recs.get("data") or []

acc, red, review, det = V._tier2_issuer_inconsistent(recs, fs)
accids = {id(f) for f in acc}

print("== _LIFE8_ISSUER_INCONSISTENT registry ==")
for k, v in V._LIFE8_ISSUER_INCONSISTENT.items():
    print("  ", k, v)
l8, l8red = None, None
try:
    l8 = V._life8_issuer_inconsistent(recs, fs)
    print("  life8 recheck ->", type(l8), (len(l8) if hasattr(l8,'__len__') else l8))
except Exception as e:
    print("  (no _life8_issuer_inconsistent callable:", e, ")")

EXCL = {("KR0029","2025.2Q"),("KR0029","2025.3Q"),("KR0104","2026.2Q")}
reds = [f for f in fs if f.get("status")=="RED"]
print(f"\n== 53 RED 완전분할 ==")
buckets = {"제외분(다른에이전트/기등재)":[], "tier2면제MATCH":[], "life8면제":[], "BLOCKING(내몫)":[]}
L8KEYS = set(V._LIFE8_ISSUER_INCONSISTENT)
for f in reds:
    c, q, r = f.get("원보험사코드"), f.get("공시분기"), f.get("rule")
    if (c,q) in EXCL: buckets["제외분(다른에이전트/기등재)"].append(f)
    elif id(f) in accids: buckets["tier2면제MATCH"].append(f)
    elif r == "8_life" and (c,q) in L8KEYS: buckets["life8면제"].append(f)
    else: buckets["BLOCKING(내몫)"].append(f)
for k, v in buckets.items():
    print(f"\n--- {k}: {len(v)} ---")
    for f in sorted(v, key=lambda x:(str(x.get('rule')),str(x.get('원보험사코드')),str(x.get('공시분기')))):
        print(f"   {f.get('rule'):28s} {f.get('원보험사코드')} {str(f.get('원수사명'))[:14]:16s} {f.get('공시분기')} diff={f.get('diff')}")
print("\n합계 검산:", sum(len(v) for v in buckets.values()), "== 53")
