# -*- coding: utf-8 -*-
"""_TIER2_ISSUER_INCONSISTENT 를 현재 마스터 + 리포트 findings 에 대고 import 재검산."""
import json, sys, collections
from pathlib import Path
ROOT = Path(r"C:/Users/sangwook.cho/Desktop/insurequant")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import validate_kics_disclosure as V

rep = json.loads((ROOT / "artifacts/kics_validation/report_latest.json").read_text(encoding="utf-8"))
print("report source =", rep.get("source"), "| generated_at =", rep.get("generated_at"))
fs = rep["findings"]

# 마스터 로드 — 게이트가 쓰는 것과 같은 경로
src = ROOT / "kics_disclosure.json"
recs = json.loads(src.read_text(encoding="utf-8"))
if isinstance(recs, dict):
    recs = recs.get("records") or recs.get("data") or []
print("master rows =", len(recs))

acc, red, review, detail = V._tier2_issuer_inconsistent(recs, fs)
print("\n== recheck ==")
print("accepted(면제로 차단제외) =", len(acc))
print("RED(면제 자체가 깨짐)      =", len(red))
print("review(INERT)             =", len(review))
for r in red:
    print("  RED:", r.get("rule"), r.get("code"), r.get("quarter"), r.get("axis") or r.get("item"), "|", str(r.get("detail"))[:160])
for r in review:
    print("  REVIEW:", r.get("rule"), r.get("code"), r.get("quarter"), r.get("axis"), "|", str(r.get("detail"))[:140])

print("\n== pinned residual vs actual (MATCH 판정) ==")
for (c, nm, q, rule, pinned, actual, delta) in detail:
    verd = "MATCH" if (delta is not None and abs(delta) <= V._TIER2_PIN_TOL) or (pinned is None and actual is None) else "DRIFT"
    print(f"  {verd:5s} {c} {q:8s} {rule:26s} pinned={pinned} actual={actual} delta={delta}")

# 41건 중 accepted 로 덮인 것
EXCL = {("KR0029","2025.2Q"),("KR0029","2025.3Q"),("KR0104","2026.2Q")}
reds41 = [f for f in fs if f.get("status")=="RED" and (f.get("원보험사코드"), f.get("공시분기")) not in EXCL]
accset = {(id(f)) for f in acc}
covered, uncovered = [], []
for f in reds41:
    (covered if id(f) in accset else uncovered).append(f)
print(f"\n41건 중 면제커버 {len(covered)} / 미커버 {len(uncovered)}")
print("\n-- 미커버(blocking 후보) --")
for f in sorted(uncovered, key=lambda x:(str(x.get("rule")), str(x.get("원보험사코드")), str(x.get("공시분기")))):
    print(f"  {f.get('rule'):26s} {f.get('원보험사코드')} {f.get('원수사명')} {f.get('공시분기')} diff={f.get('diff')} | {str(f.get('detail'))[:130]}")
