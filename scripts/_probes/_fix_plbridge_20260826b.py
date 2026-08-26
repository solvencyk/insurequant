#!/usr/bin/env python3
"""pl_bridge 등재부: 메리츠 2024.1Q 종결 삭제 + 2023.2Q 신규 등재(사유 확정)."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")
P = ROOT / "data/_gold/pl_bridge_baseline.json"
d = json.loads(P.read_text(encoding="utf-8"))
ent = d["entries"]
k_out = "메리츠화재해상보험|2024.1Q|보험손익(dual)"
assert k_out in ent
ent.pop(k_out)
k_in = "메리츠화재해상보험|2023.2Q|보험손익(dual)"
ent[k_in] = {
    "class": "tier1_tier2_basis_split",
    "reason": ("2026-08-26 (inbox/parser/20260826T0730Z §3, 목차 오검출 경계 정정): Tier-2 는 이제 "
               "별도(OFS)를 읽는데 Tier-1 이 같은 분기에서 연결(CFS)이라 브릿지가 두 기준을 비교한다. "
               "메리츠 FY2023 분기는 DART FS-API 가 status 013(무자료)이라 Tier-1 이 HTML 폴백으로 "
               "떨어지는데 `extract_tier1` 에는 basis 필터가 없다. 실측: 별도 pool 만으로 "
               "extract_tier1 을 돌리면 이 필링은 `{}` 를 낸다(별도 섹션에 인식 가능한 포괄손익계산서가 "
               "없음) — 즉 item1 을 별도로 옮기면 값이 통째로 사라진다. 같은 정정이 2024.1Q·2024.2Q "
               "브릿지는 -975.6/-795.6 -> -0.6 으로 닫았다(그 분기는 FS-API 별도 item1 이 있다). "
               "item14(일반손익)의 새 값이 별도라 더 옳고, 잔차는 그 기준 불일치의 크기다. "
               "route: Tier-1 basis 필터 신설(전 회사 census 선행) 또는 FY2023 분기 FS-API 백필."),
    "route": "parser/ifrs17",
    "lhs": 822607.0,
    "diff": 825.4,
    "first_seen": "2026-08-26",
}
if isinstance(d.get("_counts"), dict):
    d["_counts"]["entries"] = len(ent)
d["_round_20260826_toc"] = (
    "2026-08-26 2차(목차 경계 정정): 메리츠 2024.1Q 삭제 — 그 줄의 사유가 '경계가 안 잡힌다' 였는데 "
    "잡히게 되자 브릿지가 -0.6 으로 닫혔다(2024.2Q 도 같이 닫혔고 그쪽은 원래 등재부에 없었다). "
    "메리츠 2023.2Q 신규 등재 — 위 사유 참조(Tier-1/Tier-2 기준 분리). 2023.1Q 은 잔차 362.2 로 "
    "게이트 허용 안이라 등재하지 않았다(같은 원인).")
P.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print("pl_bridge entries:", len(ent))
