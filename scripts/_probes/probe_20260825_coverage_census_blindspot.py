# -*- coding: utf-8 -*-
"""완결성 census 의 사각을 실측한다 (read-only).

`scripts/validate_master_tables.py::coverage_holes(idx, key_items, active_min=7)` 는
"핵심항목 보유 분기 < 7" 인 회사를 struct(미공시)로 분류해 **검사에서 뺀다**. 즉

  * 적게 있을수록 검사에서 빠지고,
  * **0분기인 회사는 `if not present: continue` 로 조기 탈출해 struct 목록에조차 안 뜬다.**

정당 미공시 레지스트리(`data/_gold/user_csm_cells.json::exclude_companies`)는 이미 존재하는데
게이트가 그걸 **참조하지 않는다** — "명시 사유로 등재"가 아니라 "조용히 사라진다".

이 스크립트는 그 셋을 한 화면에 세운다:
  1. 게이트가 실제로 읽는 경로 (PL 축이 배포본이 아니다)
  2. struct 로 빠진 회사 + 마스터에 행이 0개라 목록에조차 없는 회사
  3. 레지스트리 등재분과 그 참조 여부
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_master_tables as vmt  # noqa: E402

WF_ITEMS = ["기초CSM", "신계약CSM", "이자부리", "가정및경험조정", "CSM상각", "기말CSM"]
PL_ITEMS = ["보험손익", "생명장기 손익", "당기순이익"]


def main() -> int:
    wf = vmt.load_long(vmt.WF_PATH)
    pl = vmt.load_long(vmt.PL_PATH)
    gold = json.loads((ROOT / "data/_gold/user_csm_cells.json").read_text(encoding="utf-8"))
    excl = gold.get("exclude_companies", {})
    src = (ROOT / "scripts/validate_master_tables.py").read_text(encoding="utf-8")

    print("=" * 92)
    print("1. 게이트가 읽는 경로")
    print("=" * 92)
    print(f"  WF_PATH = {vmt.WF_PATH}   <- 배포본")
    print(f"  PL_PATH = {vmt.PL_PATH}   <- 배포본 아님 (PL_breakdown.json 이 배포본)")

    _, _, wf_s = vmt.coverage_holes(wf, WF_ITEMS)
    _, _, pl_s = vmt.coverage_holes(pl, PL_ITEMS)

    print()
    print("=" * 92)
    print(f"2. active_min=7 미만이라 검사에서 빠진 회사   CSM={len(wf_s)}  PL={len(pl_s)}")
    print("=" * 92)
    print("  [CSM]")
    for co, n in sorted(wf_s):
        print(f"    {co:22s} 보유분기={n}")
    print("  [PL]")
    for co, n in sorted(pl_s):
        print(f"    {co:22s} 보유분기={n}")

    wf_cos = {co for (co, _) in wf}
    pl_cos = {co for (co, _) in pl}
    ghost = sorted(pl_cos - wf_cos)
    print()
    print("=" * 92)
    print(f"3. CSM 마스터에 행이 0개 -> struct 목록에조차 안 뜨는 회사 = {len(ghost)}")
    print("=" * 92)
    for co in ghost:
        print(f"    {co}")

    print()
    print("=" * 92)
    print("4. 정당 미공시 레지스트리")
    print("=" * 92)
    for code, why in excl.items():
        print(f"    {code}: {why[:110]}...")
    print(f"\n  validate_master_tables.py 가 'exclude_companies' 를 참조하는가: "
          f"{'YES' if 'exclude_companies' in src else 'NO'}")
    print("  -> NO 면, 위 3번 회사들은 '정당 미공시로 등재됐다'가 아니라 "
          "'룰이 순회조차 안 한다'가 정확한 서술이다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
