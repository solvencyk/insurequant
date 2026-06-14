# -*- coding: utf-8 -*-
"""Reshape parsed viz data into the project's tidy long schema (the same shape as
kics_disclosure.json and the user's CSM_waterfall.xlsx / CSM_amortization.xlsx /
PL_breakdown.xlsx templates):

  {원보험사코드, 원수사명, 티커, 생손보여부, 항목번호, 항목명, 공시분기, 값}
  (CSM_amortization uses 경과차년 + 상각액 instead of 항목번호/항목명/값.)

Sources (all 억원; CSM waterfall is 백만원 in source → ÷100):
  - CSM_waterfall    ← data/dart/viz/csm_waterfall_history.json (13Q × stages)
  - CSM_amortization ← data/dart/viz/csm_amort_schedule.json    (yearly y1..y10)
  - PL_breakdown     ← data/dart/viz/net_income_breakdown.json  (tier1 + tier2 LOB)

Company meta (코드/티커/생손보여부) is looked up from kics_disclosure.json by 원수사명.
값 = null where the metric is not parsed for that company/period.
Outputs: CSM_waterfall.json / CSM_amortization.json / PL_breakdown.json (repo root).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")


def L(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def W(name: str, rows: list[dict]):
    (ROOT / name).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  wrote {name}: {len(rows)} rows, 값 filled={sum(1 for r in rows if r.get('값') is not None or r.get('상각액') is not None)}")


def num(v):
    return None if v is None else round(float(v), 1)


# --- company meta from kics master (원수사명 -> code/ticker/생손보) -------------
kics = L("kics_disclosure.json")
META: dict[str, tuple] = {}
for r in kics:
    nm = r.get("원수사명")
    if nm and nm not in META:
        META[nm] = (r.get("원보험사코드"), r.get("티커"), r.get("생손보여부"))


# DART corp_name (short form, as in csm_waterfall_history.json "company") → kics 원수사명.
# Inverse of scripts/ifrs17_batch_all.NAME_ALIASES + the trailing-"보험"-drop fallback, so the
# short name resolves to a 원보험사코드/티커 instead of None (broke the CSM↔PL join).
DART_NAME_TO_KICS = {
    "삼성생명": "삼성생명보험",
    "미래에셋생명": "미래에셋생명보험",
    "코리안리": "코리안리재보험",
    "케이비라이프생명보험": "KB라이프생명",
}

# kics_disclosure.json에 없는 회사(감사보고서-only 등)의 (코드, 티커, 생손보) fallback.
# 정본 코드 매핑: scripts/_dart_path_helpers.py. AIA는 kics 미수록 → 코드 공란이던 것 보강(owner 지시 2026-06-11).
NAME_CODE_FALLBACK = {
    "에이아이에이생명보험": ("KR0080", None, "생명보험"),
}


def meta(name: str) -> tuple:
    canon = DART_NAME_TO_KICS.get(name, name)
    if canon in META:
        return META[canon]
    if name in NAME_CODE_FALLBACK:
        return NAME_CODE_FALLBACK[name]
    if canon in NAME_CODE_FALLBACK:
        return NAME_CODE_FALLBACK[canon]
    sb = "생명보험" if any(k in name for k in ("생명", "라이프")) else (
        "손해보험" if any(k in name for k in ("손해", "화재", "해상", "코리안리")) else None)
    return (None, None, sb)


def base(name: str) -> dict:
    code, ticker, sb = meta(name)
    canon = DART_NAME_TO_KICS.get(name, name)        # disclosure 원수사명 for a clean PL join
    return {"원보험사코드": code, "원수사명": canon, "티커": ticker, "생손보여부": sb}


def fy_to_q(fy) -> str | None:
    if not fy:
        return None
    s = str(fy)
    if "." in s and s.endswith("Q"):
        return s
    if "FY" in s:
        return s.replace("FY", "")[:4] + ".4Q"
    for y in ("2023", "2024", "2025", "2026"):
        if y in s:
            return y + ".4Q"
    return None


# === 1) CSM_waterfall ========================================================
WF_ITEMS = [(1, "기초 CSM", "opening"), (2, "신계약 CSM", "new_business"),
            (3, "이자 부리", "interest"), (4, "가정 및 경험 조정", "assumption"),
            (5, "CSM 상각", "amortization"), (6, "기말 CSM", "closing")]
hist = L("data/dart/viz/csm_waterfall_history.json")
wf_rows = []
for c in hist.get("companies", []):
    nm = c.get("company")
    b = base(nm)
    for period, snap in (c.get("periods") or {}).items():
        stages = (snap or {}).get("stages") or {}
        for no, label, key in WF_ITEMS:
            v = (stages.get(key) or {}).get("value_mn_krw")
            wf_rows.append({**b, "항목번호": no, "항목명": label, "공시분기": period,
                            "값": num(v / 100) if v is not None else None})

# === 2) CSM_amortization =====================================================
am = L("data/dart/viz/csm_amort_schedule.json")
am_period = fy_to_q(am.get("period")) or am.get("period")
am_rows = []
for c in am.get("companies", []):
    nm = c.get("company")
    b = base(nm)
    yearly = (c.get("yearly") or {})
    for yr in range(1, 11):
        v = yearly.get(f"y{yr}")
        am_rows.append({**b, "공시분기": am_period, "경과차년": yr, "상각액": num(v)})

# === 3) PL_breakdown (17 items, 보험손익 breakdown.xlsx gold structure) =======
ni = L("data/dart/viz/net_income_breakdown.json")
PL_LABELS = {1: "보험손익", 2: "장기 손익", 3: "CSM상각", 4: "RA(위험조정변동)",
             5: "예실차 등", 6: "자동차손익", 7: "일반손익", 8: "기타영업수익",
             9: "기타사업비용", 10: "투자손익", 11: "투자이익", 12: "보험금융손익",
             13: "영업이익", 14: "영업외손익", 15: "세전이익", 16: "법인세", 17: "당기순이익"}
pl_rows = []
pl_tie = pl_total = 0
for c in ni.get("companies", []):
    nm = c.get("company")
    b = base(nm)
    period = fy_to_q(c.get("tier1_fy")) or fy_to_q(c.get("tier2_fy"))
    t1 = c.get("tier1") or {}
    lob = c.get("tier2_lob") or {}
    jang = lob.get("장기") or {}
    g = lambda d, k: d.get(k)
    # 보험금융손익 = (보험금융수익+재보험금융수익) − (보험금융비용+재보험금융비용)
    fin_parts = [g(t1, k) for k in ("보험금융수익", "재보험금융수익", "보험금융비용", "재보험금융비용")]
    bofin = (None if all(x is None for x in fin_parts)
             else (g(t1, "보험금융수익") or 0) + (g(t1, "재보험금융수익") or 0)
                  - (g(t1, "보험금융비용") or 0) - (g(t1, "재보험금융비용") or 0))
    inv = g(t1, "투자손익")
    invprofit = None if inv is None or bofin is None else inv - bofin   # 투자이익
    jpl, csm, ra = g(jang, "보험손익"), g(jang, "csm_상각"), g(jang, "ra_변동")
    yesil = None if jpl is None or csm is None or ra is None else jpl - (csm + ra)  # 예실차 등
    vals = {1: g(t1, "보험손익"), 2: jpl, 3: csm, 4: ra, 5: yesil,
            6: g(lob.get("자동차") or {}, "보험손익"), 7: g(lob.get("일반") or {}, "보험손익"),
            8: g(t1, "기타영업수익"), 9: g(t1, "기타사업비용"), 10: inv, 11: invprofit,
            12: bofin, 13: g(t1, "영업이익"), 14: g(t1, "영업외"),
            15: g(t1, "세전이익"), 16: g(t1, "법인세"), 17: g(t1, "당기순이익")}
    for no in sorted(PL_LABELS):
        pl_rows.append({**b, "항목번호": no, "항목명": PL_LABELS[no],
                        "공시분기": period, "값": num(vals.get(no))})
    # verification: 보험손익 ≈ 장기+자동차+일반+기타영업수익−기타사업비용 (gold-sheet identity)
    seg = [vals[k] for k in (2, 6, 7)]
    oth_inc = vals[8] if vals[8] is not None else 0.0   # 기타영업수익 line absent (메리츠) = 0
    if vals[1] is not None and all(x is not None for x in seg) and vals[9] is not None:
        pl_total += 1
        recon = seg[0] + seg[1] + seg[2] + oth_inc - vals[9]
        if abs(recon - vals[1]) <= max(50.0, abs(vals[1]) * 0.02):
            pl_tie += 1

print("building tidy exports:")
W("CSM_waterfall.json", wf_rows)
W("CSM_amortization.json", am_rows)
W("PL_breakdown.json", pl_rows)
print(f"  PL 검증 (보험손익 = 장기+자동차+일반+기타영업수익−기타사업비용): {pl_tie}/{pl_total} tie")
print(f"meta matched companies: {len(META)} in kics master")
