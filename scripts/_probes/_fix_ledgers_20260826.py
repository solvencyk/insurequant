#!/usr/bin/env python3
"""basis 수정 후 등재부 3곳 정리 — 셀/줄 단위, 나머지 무접촉."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")

# 1) PL gold: 한화손해 2023.1Q item20 override 제거 (근거였던 결함이 고쳐졌다)
P = ROOT / "data/_gold/user_pl_cells.json"
d = json.loads(P.read_text(encoding="utf-8"))
before = len(d["set"])
kept = [e for e in d["set"]
        if not (e.get("원보험사코드") == "KR0002" and e.get("공시분기") == "2023.1Q"
                and e.get("항목번호") == 20)]
assert len(kept) == before - 1, (before, len(kept))
d["set"] = kept
P.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"1) user_pl_cells.json: {before} -> {len(kept)} (한화손해 2023.1Q item20 제거)")

# 2) pl_bridge_baseline: 메리츠 2023.4Q 는 고쳐졌다 -> 줄 삭제
P = ROOT / "data/_gold/pl_bridge_baseline.json"
d = json.loads(P.read_text(encoding="utf-8"))
k = "메리츠화재해상보험|2023.4Q|보험손익(dual)"
assert k in d["entries"], list(d["entries"])
d["entries"].pop(k)
if isinstance(d.get("_counts"), dict):
    d["_counts"]["entries"] = len(d["entries"])
d["_round_20260826_basis"] = (
    "2026-08-26 (inbox/parser/20260826T0500Z ② 후속, basis 필터 배선): "
    "메리츠화재|2023.4Q|보험손익(dual) 삭제 — 그 줄의 사유가 '_prefer_ofs 후보가 없다(ATOC 마커 부재)' "
    "였는데, 별도 경계 탐지를 ENG 속성에서 텍스트 제목으로 넓히자 이 필링에서 경계가 잡혀 후보가 생겼고 "
    "브릿지가 닫혔다. 같은 class 인 2024.1Q 는 아직 경계가 안 잡혀 유지한다. "
    "한화손해|2023.1Q|세전이익 은 등재하지 않았다 — data/_gold/user_pl_cells.json 의 item20 override"
    "(2026-08-15, HTML 폴백이 26.27백만을 내던 시절의 임시값)가 stale 해서 생긴 것이라 그 override 를 "
    "지워 해소했다. 중간산출은 이미 124,237.65 로 항등식이 닫힌다.")
P.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"2) pl_bridge_baseline.json: 메리츠 2023.4Q 삭제, 남은 {len(d['entries'])}건")

# 3) csm_amort_identity_ledger: 삼성생명 5분기 종결 -> 줄 삭제
P = ROOT / "data/_gold/csm_amort_identity_ledger.json"
d = json.loads(P.read_text(encoding="utf-8"))
ent = d["entries"]
gone = [k for k in list(ent) if k.startswith("삼성생명보험|")]
assert len(gone) == 5, gone
for k in gone:
    ent.pop(k)
d["_measured_at"] = ("2026-08-26 (parser-ifrs17, basis 필터 배선 — 삼성생명 5분기 종결. "
                     "PL 이 연결을 물던 원인 2종을 고쳤다: 별도 경계 탐지가 ENG 속성에만 의존 / "
                     "lxml HTMLParser sourceline 65,535 포화. inbox/parser/20260826T0500Z ② 참조)")
d["_population"] = {"compared_buckets": 346, "within_identity": 340, "ledgered": len(ent)}
P.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"3) csm_amort_identity_ledger.json: 삼성생명 5건 삭제, 남은 {len(ent)}건 -> {sorted(ent)}")
