# -*- coding: utf-8 -*-
"""kics_capital_securities_timeline.json - 신종자본증권·후순위채 발행 내역(채권 단위, 분류 없음).

K-ICS 화면의 「자본성증권 발행현황」 누적 막대(발행일 기준, 아래 신종자본증권 + 위 후순위채)의 원천이다.
owner 지시(2026-10-12): 시점별 잔액을 DART 에서 새로 뽑지 않고, 이미 있는 채권 단위 자료만 쓴다.

입력  data/bonds/capital_securities_fy2026h1.json  (회사별 bonds[]; 큼직한 셀용 securities_summary 와 같은 입력)
출력  kics_capital_securities_timeline.json (루트, 배포 파일)

    {"generated": "YYYY-MM-DD", "unit": "억원", "source": "...",
     "securities": {"<회사코드>": [ {"tier": "hybrid"|"subordinated", "issue_date", "call_date"|null,
                                     "coupon_pct"|null, "face_eok", "outstanding_eok", "as_of"} , ... ]}}

* tier 는 원천의 `tier` 그대로(hybrid = 신종자본증권, subordinated = 후순위채). 기본자본/보완자본 판단·인정액 필드 없음.
* 단위 억원 = 백만원 / 100 (소수 둘째 자리). face_eok = 발행 권면(`face_amount_mn`), outstanding_eok = 그 as_of 의 잔액.
* as_of 는 채권별 잔액 기준일(회사마다 2025-12-31 또는 2026-06-30). 원천에 발행일이 없는 증권은 막대에 놓을 수 없어 뺀다.
* 이미 상환돼 잔액 0 인 증권도 발행 내역이라 싣는다(outstanding_eok = 0). 원천에 한 번도 오른 적 없는 과거 상환 증권은 없다.
* 회사코드는 JSON 키로만 쓴다(화면 노출 금지 규약).

실행: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/build_capital_securities_timeline.py
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "bonds" / "capital_securities_fy2026h1.json"
OUT = ROOT / "kics_capital_securities_timeline.json"
MN_PER_EOK = 100.0
TIERS = ("hybrid", "subordinated")
SOURCE_TEXT = ("data/bonds/capital_securities_fy2026h1.json (DART 사업·반기보고서 채권 단위, 회사별 최신 기준일). "
               "발행일이 없는 증권은 제외, 상환돼 잔액 0 인 증권은 포함")


def eok(mn) -> float | None:
    return None if mn is None else round(float(mn) / MN_PER_EOK, 2)


def bond_record(bond: dict, company_as_of: str | None) -> dict | None:
    """원천 채권 한 건 -> 출력 한 건. 막대에 놓을 수 없으면(tier·발행일·금액 없음) None."""
    if bond.get("tier") not in TIERS or not bond.get("issue_date"):
        return None
    face = bond.get("face_amount_mn")
    out = bond.get("outstanding_mn")
    if face is None and out is None:
        return None
    # 권면이 비어 있으면 잔액으로 대신하지 않고 그 채권은 뺀다(추측 금지)
    if face is None:
        return None
    return {
        "tier": bond["tier"],
        "issue_date": bond["issue_date"],
        "call_date": bond.get("call_date") or None,
        "coupon_pct": bond.get("coupon_pct"),
        "face_eok": eok(face),
        "outstanding_eok": eok(out or 0.0),
        "as_of": bond.get("as_of") or company_as_of,
    }


def build(src: dict, generated: str) -> dict:
    securities: dict[str, list[dict]] = {}
    for c in src["companies"]:
        recs = [r for r in (bond_record(b, c.get("as_of")) for b in c.get("bonds") or []) if r]
        if recs:
            recs.sort(key=lambda r: (r["issue_date"], r["tier"], r["face_eok"]))
            securities[c["code"]] = recs
    return {"generated": generated, "unit": "억원", "source": SOURCE_TEXT, "securities": securities}


def main() -> int:
    src = json.loads(SRC.read_text(encoding="utf-8"))
    doc = build(src, date.today().isoformat())
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    n = sum(len(v) for v in doc["securities"].values())
    by = {t: sum(1 for v in doc["securities"].values() for r in v if r["tier"] == t) for t in TIERS}
    print(f"wrote {OUT.name}: companies={len(doc['securities'])} bonds={n} {by}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
