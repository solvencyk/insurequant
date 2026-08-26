# -*- coding: utf-8 -*-
"""사각 12버킷 + 악사 RED 1건의 원천에 **PL Tier-2 노트가 실재하는지** 전수 확인.

정본 행 라벨은 '당기손익으로 인식한 보험계약마진 금액' 이다 — 악사 2024.4Q(추출 성공)의
PL `원수CSM상각` 이 이 행의 장기 컬럼과 원 단위까지 일치하는 것으로 소스를 특정했다.
캡션 번호는 필링마다 흔들린다(악사 2023 = '(5) 보험손익 상세내역', 2024 = '(6) ...').
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_master_tables import load_long  # noqa: E402

ROW = "당기손익으로 인식한 보험계약마진 금액"
CAPTION = re.compile(r"\(\d+\)\s*보험\s*손익\s*상세\s*내역")

# (회사, 분기) -> raw 디렉터리 (FY 디렉터리 안에서 코드 prefix 로 찾는다)
CODE = {
    "삼성화재해상보험": "KR0008", "NH농협손해보험": "KR0032", "롯데손해보험": "KR0003",
    "케이디비생명보험": "KR0072", "에이아이에이생명보험": "KR0080",
    "아이엠라이프생명보험": "KR0076", "하나손해보험": "KR0050",
    "교보라이프플래닛생명보험": "KR1010", "악사손해보험": "KR0049",
}
FY = {"1Q": "Q1", "2Q": "Q2", "3Q": "Q3", "4Q": "Q4"}

TARGETS = [
    ("삼성화재해상보험", "2023.1Q"), ("NH농협손해보험", "2023.1Q"),
    ("롯데손해보험", "2023.1Q"), ("케이디비생명보험", "2023.1Q"),
    ("에이아이에이생명보험", "2023.4Q"), ("에이아이에이생명보험", "2024.4Q"),
    ("아이엠라이프생명보험", "2024.4Q"), ("아이엠라이프생명보험", "2025.4Q"),
    ("하나손해보험", "2023.4Q"), ("하나손해보험", "2024.4Q"), ("하나손해보험", "2025.4Q"),
    ("교보라이프플래닛생명보험", "2023.4Q"), ("악사손해보험", "2023.4Q"),
    # 대조군 — PL Tier-2 추출이 성공한 버킷
    ("악사손해보험", "2024.4Q"), ("교보라이프플래닛생명보험", "2024.4Q"),
    ("에이아이에이생명보험", "2025.4Q"),
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
    out = []
    for co, q in TARGETS:
        yr, qq = q.split(".")
        fy = ROOT / "data" / "dart" / f"FY{yr}_{FY[qq]}" / "raw"
        pre = CODE[co]
        xmls = sorted(x for sub in fy.glob(f"{pre}_*") for x in sub.rglob("*.xml")) if fy.exists() else []
        m = pl.get((co, q))
        w = wf.get((co, q)) or {}
        best = {"row_hits": 0, "caption": None, "file": None}
        for x in xmls:
            t = _flat(x)
            if not t:
                continue
            hits = t.count(ROW)
            cap = CAPTION.search(t)
            if hits > best["row_hits"]:
                best = {"row_hits": hits, "caption": cap.group(0) if cap else None,
                        "file": x.name}
        rec = {
            "company": co, "quarter": q,
            "pl_bucket": m is not None,
            "pl_amort": (m or {}).get("원수CSM상각"),
            "wf_amort_eok": w.get("CSM상각"),
            "raw_xml_count": len(xmls),
            "tier2_row_hits": best["row_hits"],
            "tier2_caption": best["caption"],
            "file": best["file"],
        }
        out.append(rec)
        flag = "NOTE-PRESENT" if best["row_hits"] else "note-absent "
        print(f"{flag}  {co:22s} {q}  PL버킷={'Y' if rec['pl_bucket'] else 'N'} "
              f"상각={str(rec['pl_amort'])[:12]:>12s}  행히트={best['row_hits']:2d}  "
              f"캡션={best['caption']}  {best['file']}")

    p = ROOT / "data" / "_derived" / "pl_tier2_note_in_raw_20260826.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {p}")


if __name__ == "__main__":
    main()
