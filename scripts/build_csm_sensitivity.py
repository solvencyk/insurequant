# -*- coding: utf-8 -*-
"""IFRS17 가정민감도(ΔCSM) 마스터 빌더 -> CSM_sensitivity.json

owner 상시 규칙: **화면에 있는 그래프는 전부 마스터 테이블에 담는다.**
`IFRS17.html` "7) 민감도(ΔCSM)" 패널이 `data/dart/viz/sensitivity_heatmap.json` 을 그리는데,
2026-08-30 실측 결과 **이 패널만 대응 마스터 시트가 없었다.** 마스터 xlsx 의 `금리민감도`
시트는 이름이 비슷하지만 다른 표다 — 그쪽은 `kics_rate_sensitivity.json`(K-ICS 지급여력비율의
금리 −100bp~+100bp 민감도)이고, 이 파일은 IFRS17 보험가정(사망률·장해질병·해지율·사업비)
충격에 대한 CSM/손익 민감도다. 둘을 같은 것으로 보고 넘어가 이 시트가 1년 가까이 비어 있었다.

**소스는 화면이 읽는 바로 그 파일이다**(`CLAUDE.md` 불변식 1: 게이트가 검사하는 파일 =
사용자가 보는 파일). 별도 재추출 경로를 만들면 화면과 마스터가 갈라진다.

스키마(다른 시트와 같은 long-format):
    원보험사코드 · 원수사명 · 티커 · 생손보여부 · 공시분기 · 기준일 ·
    위험구분 · 충격수준 · CSM변동 · 당기손익영향 · 자본영향 · 비고
단위는 다른 마스터와 같은 **억원**(패널이 이미 억원으로 정규화해 싣는다).

민감도표가 없는 회사도 **행을 남긴다**(값 null + 비고). 이 저장소 규칙상 결측을 조용히
빼면 census 가 그 회사를 아예 못 본다.

실행:
    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/build_csm_sensitivity.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")

SRC = ROOT / "data" / "dart" / "viz" / "sensitivity_heatmap.json"
OUT = ROOT / "CSM_sensitivity.json"

# 패널 쪽 회사명 -> 마스터의 `원수사명`. 같은 별칭 집합이
# viz_build_ifrs17_panels._CSM_NAME_ALIAS / validate_live_artifacts.COMPANY_ALIAS 에도 있다.
# (이 표기 차이 때문에 2026-08-30 에 에이아이지의 단위 가드가 조용히 꺼져 있었다.)
NAME_ALIAS = {
    "미래에셋생명": "미래에셋생명보험",
    "삼성생명": "삼성생명보험",
    "코리안리": "코리안리재보험",
    "아이비케이연금보험": "IBK연금보험",
    "케이비라이프생명보험": "KB라이프생명",
    "에이아이지손해보험": "AIG손해보험",
    "엠지손해보험": "예별손해보험",
}


def company_meta() -> dict:
    """{원수사명: (원보험사코드, 티커, 생손보여부)} — 기존 마스터에서 그대로 가져온다.
    여기서 회사 목록을 새로 타이핑하면 그 순간부터 다른 시트와 갈라진다."""
    meta: dict = {}
    for name in ("CSM_waterfall.json", "kics_disclosure.json", "IFRS17_BS.json"):
        p = ROOT / name
        if not p.exists():
            continue
        for r in json.loads(p.read_text(encoding="utf-8")):
            nm = r.get("원수사명")
            if nm and nm not in meta:
                meta[nm] = (r.get("원보험사코드"), r.get("티커"), r.get("생손보여부"))
    return meta


def quarter_of(as_of: str | None, period: str | None) -> str | None:
    """'2025-12-31' -> '2025.4Q'. 없으면 period('FY2025')에서 4Q 로 떨어뜨린다."""
    if as_of and len(as_of) >= 10:
        y, m = as_of[:4], as_of[5:7]
        qn = {"03": 1, "06": 2, "09": 3, "12": 4}.get(m)
        if qn:
            return f"{y}.{qn}Q"
    if period and period.startswith("FY") and period[2:6].isdigit():
        return f"{period[2:6]}.4Q"
    return None


def main() -> int:
    doc = json.loads(SRC.read_text(encoding="utf-8"))
    meta = company_meta()
    rows, unmatched = [], []
    n_scen = n_stub = 0

    for c in sorted(doc.get("companies", []), key=lambda x: str(x.get("company"))):
        raw_name = str(c.get("company") or "")
        name = NAME_ALIAS.get(raw_name, raw_name)
        code, ticker, sb = meta.get(name, (None, None, None))
        if code is None:
            unmatched.append(raw_name)
        quarter = quarter_of(c.get("as_of"), c.get("period"))
        base = {
            "원보험사코드": code, "원수사명": name, "티커": ticker, "생손보여부": sb,
            "공시분기": quarter, "기준일": c.get("as_of"),
        }
        scens = c.get("scenarios") or []
        if not scens:
            rows.append({**base, "위험구분": None, "충격수준": None,
                         "CSM변동": None, "당기손익영향": None, "자본영향": None,
                         "비고": f"민감도표 미수록 (status={c.get('status')}"
                                 f"{'; ' + str(c.get('note')) if c.get('note') else ''})"})
            n_stub += 1
            continue
        for s in scens:
            note = None
            if c.get("unit_source") == "suspect":
                note = "단위 미해결로 값 보류 (빌더 sanity 가드)"
            elif s.get("disclosed_as"):
                note = f"원문 표기: {s['disclosed_as']}"
            rows.append({**base,
                         "위험구분": s.get("risk"), "충격수준": s.get("shock"),
                         "CSM변동": s.get("csm_delta"),
                         "당기손익영향": s.get("pl_impact"),
                         "자본영향": s.get("equity_impact"),
                         "비고": note})
            n_scen += 1

    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(rows)} rows "
          f"({n_scen} 시나리오 + {n_stub} 미수록 stub, 회사 {len(doc.get('companies', []))})")
    if unmatched:
        print(f"  ⚠ 마스터 회사 메타를 못 찾음: {unmatched} — NAME_ALIAS 를 갱신해라")
    quarters = sorted({r["공시분기"] for r in rows if r["공시분기"]})
    print(f"  공시분기: {quarters}")
    return 1 if unmatched else 0


if __name__ == "__main__":
    raise SystemExit(main())
