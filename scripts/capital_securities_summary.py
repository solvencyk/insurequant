# -*- coding: utf-8 -*-
"""신종자본증권·후순위채 요약 셀(K-ICS 소진율 도넛 밑 큰 셀)용 값 - 순수 함수.

입력은 `data/bonds/capital_securities_fy2026h1.json` 의 회사별 `bonds[]` (DART 사채 단위, 단위 백만원).
`kics_tier{1,2}_utilization.json` 회사 행마다 같은 값으로 `securities_summary` 를 더한다
(`scripts/apply_disclosure_utilization.py` 가 이 모듈을 불러 쓴다 - 산식을 두 곳에 두지 않는다).

    securities_summary = {
      "as_of": "2026-06-30",                      # 분기말(= 콜 도래 판정 기준일)
      "hybrid" | "subordinated": None 또는 {
        "latest_coupon_pct":    잔액이 남은 증권 중 발행일이 가장 늦은 증권의 쿠폰(%). 같은 날 여러 건이면 잔액이 큰 쪽.
                                그 증권의 쿠폰이 원천에 없으면 null (이전 증권으로 대신하지 않는다)
        "latest_issue_date":    그 증권의 발행일 (툴팁용)
        "issued_since_2023_eok": 발행일 >= 2023-01-01 인 증권의 잔액 합 / 100 (억원, 정수 반올림). 없으면 0
        "next_call_date":       콜 미경과(past_call_outstanding=false)이고 콜일 >= as_of 인 증권 중 가장 이른 콜일
        "next_call_eok":        그 콜일 증권 잔액 합 / 100 (같은 날 여러 건이면 합). 해당 없으면 둘 다 null
        "next_call_estimated":  그 콜일이 원문 공시가 아니라 발행일+5년 등 추정이면 true
        "balance_as_of":        그 tier 잔액 중 가장 오래된 기준일 (회사 단위 갱신 시차를 숨기지 않는다)
      }

해당 tier 에 잔액이 남은 증권이 하나도 없으면 그 tier 객체 전체가 null. 발행일을 모르는 증권은 최근 발행·2023년
이후 합계에서 빠진다(추측하지 않는다). 외화 증권은 파일의 원화환산 `*_mn` 을 그대로 쓴다.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BONDS_PATH = ROOT / "data" / "bonds" / "capital_securities_fy2026h1.json"
SINCE = "2023-01-01"                 # K-ICS 시행일: 인정한도 계산이 세는 발행분의 시작
MN_PER_EOK = 100.0                   # 백만원 -> 억원
TIERS = (("hybrid", "hybrid"), ("subordinated", "subordinated"))   # (출력 키, 원천 tier 값)
_QEND = {"1Q": (3, 31), "2Q": (6, 30), "3Q": (9, 30), "4Q": (12, 31)}


def quarter_end(quarter: str) -> str:
    y, q = quarter.split(".")
    m, d = _QEND[q]
    return f"{int(y):04d}-{m:02d}-{d:02d}"


def eok(mn: float) -> int:
    """백만원 -> 억원, 정수 반올림(0.5 는 올림)."""
    return int(math.floor(mn / MN_PER_EOK + 0.5))


def _outstanding(b: dict) -> float:
    return float(b.get("outstanding_mn") or 0.0)


def summarize_tier(bonds: list[dict], tier: str, as_of: str) -> dict | None:
    live = [b for b in bonds if b.get("tier") == tier and _outstanding(b) > 0]
    if not live:
        return None
    dated = [b for b in live if b.get("issue_date")]
    latest_coupon = latest_date = None
    if dated:
        last = max(dated, key=lambda b: (b["issue_date"], _outstanding(b)))
        latest_date = last["issue_date"]
        latest_coupon = last.get("coupon_pct")
    since = sum(_outstanding(b) for b in dated if b["issue_date"] >= SINCE)
    callable_ = [b for b in live if not b.get("past_call_outstanding") and b.get("call_date") and b["call_date"] >= as_of]
    next_date = next_eok = None
    next_est = None
    if callable_:
        next_date = min(b["call_date"] for b in callable_)
        same = [b for b in callable_ if b["call_date"] == next_date]
        next_eok = eok(sum(_outstanding(b) for b in same))
        next_est = any((b.get("call_source") or "disclosed") != "disclosed" for b in same)
    return {
        "latest_coupon_pct": latest_coupon,
        "latest_issue_date": latest_date,
        "issued_since_2023_eok": eok(since),
        "next_call_date": next_date,
        "next_call_eok": next_eok,
        "next_call_estimated": next_est,
        "balance_as_of": min((b.get("as_of") or "") for b in live) or None,
    }


def summarize_company(bonds: list[dict], as_of: str) -> dict:
    out = {"as_of": as_of}
    for key, tier in TIERS:
        out[key] = summarize_tier(bonds, tier, as_of)
    return out


def load_bonds(path: Path = BONDS_PATH) -> dict[str, list[dict]]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    return {c["code"]: c.get("bonds") or [] for c in doc["companies"]}


def summaries_by_code(quarter: str, path: Path = BONDS_PATH) -> dict[str, dict]:
    as_of = quarter_end(quarter)
    return {code: summarize_company(bonds, as_of) for code, bonds in load_bonds(path).items()}


def empty_summary(quarter: str) -> dict:
    """원천에 회사 자체가 없을 때(있을 수 없지만) - 값 없음을 명시한다."""
    return {"as_of": quarter_end(quarter), "hybrid": None, "subordinated": None}
