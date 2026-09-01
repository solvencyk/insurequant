# -*- coding: utf-8 -*-
"""kics_restatement_ledger.json — 교보 2026.1Q 10칸을 as_restated 채택으로 등재한다."""
import json, shutil
from pathlib import Path
from datetime import datetime
import sys
sys.stdout.reconfigure(encoding="utf-8")

P = Path(__file__).resolve().parents[2] / "data" / "_gold" / "kics_restatement_ledger.json"
d = json.loads(P.read_text(encoding="utf-8"))

REASON = ("owner 결정 2026-09-01: \"매번 덮어쓰라는 건 아니지만 이번처럼 교보생명 틀린 부분이 "
          "딱 명확히 발견된 거면 안 고칠 이유가 없다\". 39사 전수 스캔에서 2026.1Q→2Q 구간의 "
          "재작성사는 교보 한 곳뿐이고(830칸 비교·미비교 0칸), 발행사가 2026.2Q 공시본에 "
          "사유까지 직접 적었다. 반영 스크립트: scripts/fix_20260901_kyobo_2026q1_adopt_restated.py")

n = 0
for k, e in d["entries"].items():
    if e.get("company") == "KR0073" and e.get("quarter") == "2026.1Q":
        e["adopted_basis"] = "as_restated"
        e["adopted_by"] = "owner 2026-09-01"
        e["adopted_reason"] = REASON
        e["adopted_scope"] = ("적용전(`값`) 컬럼만. 2026.2Q 공시본의 경과조치 표(공통TFI·②·③)에는 "
                              "직전분기 칸이 없어 발행사가 **재작성된 적용후 수치를 공시하지 않았다** "
                              "(parsed MD L463-540 실측). `값_적용후` 는 원공시본 그대로 둔다 — "
                              "없는 숫자를 유도해 채우지 않는다.")
        n += 1

d["_policy"] = ("이 저장소의 K-ICS 마스터는 기본적으로 각 분기의 **원공시본(as_filed)** 을 담는다. "
                "다만 기준은 **건별**로 정할 수 있다 — 엔트리에 `adopted_basis: \"as_restated\"` 가 "
                "있으면 그 셀은 재작성값이 정답이고, 게이트가 검사하는 방향이 뒤집힌다(원공시로 "
                "되돌아가면 KICS_RESTATEMENT_MASTER_REVERTED_TO_FILED = RED). 전면 채택하지 않는 "
                "이유는 `_severity_rationale` 참조.")
d["_policy_decisions"] = [{
    "date": "2026-09-01",
    "by": "owner",
    "scope": "KR0073 2026.1Q · 적용전 10칸 + 파생 item27/28",
    "decision": "as_restated 채택",
    "quote": "매번 덮어쓰라는건 아니지만 이번처럼 교보생명 틀린 부분이 딱 명확히 발견된거면 안고칠 이유가 없지",
    "note": ("전면 정책 변경이 아니다. '명확히 확인된 건은 고친다'는 건별 판단이며, 기본값은 "
             "as_filed 그대로다. 과거 122칸(_history_probe)은 육안 대조를 안 한 미검증 census 라 "
             "채택 대상이 아니다."),
}]

bak = P.with_suffix(f".json.bak_{datetime.now():%Y%m%d_%H%M%S}_adopt")
shutil.copy2(P, bak)
P.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"as_restated 채택 등재: {n}칸 / 백업 {bak.name}")
