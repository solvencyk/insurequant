# -*- coding: utf-8 -*-
"""PL Tier-2 노트 실재 확인 — 캡션·행라벨 변형을 다 태운 판별기 (validation, 2026-08-26).

실측으로 확인된 소스 표는 회사·필링마다 이름이 다르다:
  · 악사(손보, 감사보고서)  '(5)/(6) 보험손익 상세내역'          행 '당기손익으로 인식한 보험계약마진 금액'
  · 삼성화재(손보, 분기보고) '(10) 주요 보종별 보험수익 및 재보험비용의 내역' 행 '보험계약마진 상각'
캡션 번호와 '당분기/당반기' 어미가 흔들리므로 **캡션 번호로 찾으면 안 된다**. 여기서는
행 라벨 + 보종 헤더('장기 자동차 일반' / '자동차 일반 장기')로 판별한다.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_master_tables import load_long  # noqa: E402

CAPTIONS = [r"보험손익\s*상세\s*내역", r"보종별\s*보험수익", r"계약유형별",
            r"보험수익\s*및\s*재보험비용의\s*내역", r"유형별\s*보험수익"]
ROWS = ["당기손익으로 인식한 보험계약마진 금액", "보험계약마진 상각", "보험계약마진상각"]
HEADERS = [r"구\s*분\s*장기\s*자동차\s*일반", r"구\s*분\s*자동차\s*일반\s*장기"]

CODE = {
    "삼성화재해상보험": "KR0008", "NH농협손해보험": "KR0032", "롯데손해보험": "KR0003",
    "케이디비생명보험": "KR0072", "에이아이에이생명보험": "KR0080",
    "아이엠라이프생명보험": "KR0076", "하나손해보험": "KR0050",
    "교보라이프플래닛생명보험": "KR1010", "악사손해보험": "KR0049",
}
FYQ = {"1Q": "Q1", "2Q": "Q2", "3Q": "Q3", "4Q": "Q4"}

TARGETS = [
    ("삼성화재해상보험", "2023.1Q", "사각"), ("NH농협손해보험", "2023.1Q", "사각"),
    ("롯데손해보험", "2023.1Q", "사각"), ("케이디비생명보험", "2023.1Q", "사각"),
    ("에이아이에이생명보험", "2023.4Q", "사각"), ("에이아이에이생명보험", "2024.4Q", "사각"),
    ("아이엠라이프생명보험", "2024.4Q", "사각"), ("아이엠라이프생명보험", "2025.4Q", "사각"),
    ("하나손해보험", "2023.4Q", "사각"), ("하나손해보험", "2024.4Q", "사각"),
    ("하나손해보험", "2025.4Q", "사각"), ("교보라이프플래닛생명보험", "2023.4Q", "사각"),
    ("악사손해보험", "2023.4Q", "RED"),
    # 대조군 (Tier-2 추출 성공) — 판별기가 이 셋에서 반드시 양성이어야 한다
    ("악사손해보험", "2024.4Q", "대조군"), ("교보라이프플래닛생명보험", "2024.4Q", "대조군"),
    ("에이아이에이생명보험", "2025.4Q", "대조군"), ("삼성화재해상보험", "2023.2Q", "대조군"),
    ("롯데손해보험", "2023.2Q", "대조군"), ("케이디비생명보험", "2023.2Q", "대조군"),
    ("NH농협손해보험", "2023.2Q", "대조군"),
]


def _flat(p: Path) -> str:
    b = p.read_bytes()
    for enc in ("utf-8", "cp949", "euc-kr"):
        try:
            return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", b.decode(enc)))
        except Exception:
            continue
    return ""


def main() -> None:
    pl = load_long("PL_breakdown.json")
    wf = load_long("CSM_waterfall.json")
    rows = []
    for co, q, kind in TARGETS:
        yr, qq = q.split(".")
        d = ROOT / "data" / "dart" / f"FY{yr}_{FYQ[qq]}" / "raw"
        xmls = sorted(x for sub in d.glob(f"{CODE[co]}_*") for x in sorted(sub.rglob("*.xml"))) \
            if d.exists() else []
        agg = {"caption": 0, "row": 0, "header": 0, "chars": 0, "files": len(xmls),
               "cap_hit": None, "row_hit": None}
        for x in xmls:
            t = _flat(x)
            agg["chars"] = max(agg["chars"], len(t))
            for c in CAPTIONS:
                n = len(re.findall(c, t))
                if n:
                    agg["caption"] += n
                    agg["cap_hit"] = agg["cap_hit"] or c
            for r in ROWS:
                n = t.count(r)
                if n:
                    agg["row"] += n
                    agg["row_hit"] = agg["row_hit"] or r
            for h in HEADERS:
                agg["header"] += len(re.findall(h, t))
        m = pl.get((co, q))
        w = wf.get((co, q)) or {}
        present = agg["caption"] > 0 and agg["row"] > 0
        rows.append({"company": co, "quarter": q, "kind": kind,
                     "pl_bucket": m is not None,
                     "pl_amort": (m or {}).get("원수CSM상각"),
                     "wf_amort_eok": w.get("CSM상각"),
                     "note_present": present, **agg})
        tag = "NOTE-PRESENT" if present else "NOTE-ABSENT "
        print(f"{tag} [{kind:4s}] {co:22s} {q}  PL={'Y' if m is not None else 'N'}  "
              f"cap={agg['caption']:2d} row={agg['row']:3d} hdr={agg['header']:2d} "
              f"files={agg['files']}  cap_hit={agg['cap_hit']}  row_hit={agg['row_hit']}")

    p = ROOT / "data" / "_derived" / "pl_tier2_note_generalized_20260826.json"
    p.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {p}")

    ctrl = [r for r in rows if r["kind"] == "대조군"]
    bad = [r for r in ctrl if not r["note_present"]]
    print(f"\n대조군 {len(ctrl)}건 중 판별기 음성 {len(bad)}건"
          + ("  <- 판별기 미교정" if bad else "  (교정 OK)"))
    for r in bad:
        print(f"    {r['company']} {r['quarter']}")


if __name__ == "__main__":
    main()
