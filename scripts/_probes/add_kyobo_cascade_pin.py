# -*- coding: utf-8 -*-
"""등재부에 교보 2026.1Q 채택 연쇄(19_market) 기대잔차를 박제한다."""
import json, shutil, sys
from pathlib import Path
from datetime import datetime
sys.stdout.reconfigure(encoding="utf-8")
P = Path(__file__).resolve().parents[2] / "data" / "_gold" / "kics_restatement_ledger.json"
d = json.loads(P.read_text(encoding="utf-8"))
d["_adoption_cascades"] = [{
    "_what": ("재작성 **채택의 연쇄**로 설명되는 룰엔진 RED 의 기대잔차 박제. 통째 skip 이 "
              "아니다 — 게이트가 매 실행 실측 잔차와 대조하고, 어긋나면 RED, RED 이 사라지면 "
              "등재가 무용해졌다고 알린다."),
    "company": "KR0073",
    "company_name": "교보생명보험",
    "quarter": "2026.1Q",
    "rule": "19_market",
    "expected_residual": 779.1579604734579,
    "tol": 0.5,
    "why": ("발행사가 item19(시장위험액)를 54,674 → 55,453 으로 재작성해 인쇄했지만, 그 세부 "
            "36~40(금리·주식·부동산·외환·자산집중)의 2026.1Q 값은 **재공시하지 않았다** — "
            "2026.2Q 공시본의 `② 금리위험액 현황` 표(parsed MD L608-634)는 당분기 단일 컬럼이고, "
            "경과조치 ②③ 표(L463-540)에도 직전분기 칸이 없다. 즉 마스터의 36~40 은 2026.1Q "
            "원공시본 값이고 item19 만 재작성값이라, sqrt(V'·MARKET_M·V)=54,673.84 vs "
            "item19=55,453 로 **정확히 채택 델타(+779)만큼** 벌어진다. 우리 데이터 결함이 아니라 "
            "owner 채택 결정의 산술적 귀결이다."),
    "alternative_rejected": ("item19 만 원공시로 되돌리는 안은 더 나쁘다 — item15 = "
                             "(17+18+19+20+21) - 16 이 -779 만큼 깨지고, item14 = item15 - "
                             "item22 + item23 까지 연쇄로 깨진다. 세부를 비례배분해 채우는 안은 "
                             "'원문에 없는 숫자를 지어내는 것'이라 금지다."),
    "adopted_by": "owner 2026-09-01",
    "clears_when": ("발행사가 36~40 의 재작성값을 공시하거나, 이 버킷의 adopted_basis 를 "
                    "as_filed 로 되돌리면 이 등재를 풀어야 한다."),
}]
bak = P.with_suffix(f".json.bak_{datetime.now():%Y%m%d_%H%M%S}_cascade")
shutil.copy2(P, bak)
P.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"채택 연쇄 등재 1건 / 백업 {bak.name}")
