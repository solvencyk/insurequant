# -*- coding: utf-8 -*-
"""pl_bridge_baseline.json 의 _round_20260825c 노트가 Bash heredoc 경유로 깨져 들어갔다
(한글이 cp949/다른 인코딩으로 오염) -- Write 도구로 작성한 이 파일(보장된 UTF-8)에서
다시 써넣는다."""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
p = Path("data/_gold/pl_bridge_baseline.json")
d = json.loads(p.read_text(encoding="utf-8"))

d["_round_20260825c"] = (
    "inbox/parser/20260825T1120Z iter2 재확인(validation) 반영: DB생명보험 2023.1Q는 "
    "issuer_structural_residual 이 기각되고 raw 부모/자식행 오선택으로 재분류되어 item1 "
    "이 정정되었다(같은 버그가 item17/18/19 에도 전이돼 있어 같이 정정 -- item1 만 "
    "고치면 '영업이익=보험손익+투자손익' 등식이 item8 만큼 새로 깨졌기 때문). DB생명보험 "
    "2023.2Q(이 티켓 범위 밖, pre_existing 으로 별도 등재돼 있던 셀)도 동일 메커니즘을 "
    "독립 발견해 같이 정정. 둘 다 raw 인용(data/_gold/user_pl_cells.json) + "
    "PL_breakdown.json 셀단위 패치(scripts/_probes/"
    "patch_20260825b_kr0082_pl_bridge_full.py -- 값 9셀 + 당분기 캐스케이드 14셀, 다른 "
    "회사 0건 확인) 후 검증 재확인: pl_bridge fail 16(이 라운드 시작 시점, 5건은 아직 "
    "미종결)에서 이 2건만 FIXED?, 신규 실패 0건. issuer_structural_residual 분류명은 "
    "이 삭제로 등재부에서 완전히 소멸(다른 엔트리 미사용, grep 0건 확인)."
)

p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
print("rewritten note, first 80 chars:", d["_round_20260825c"][:80])
