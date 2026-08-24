#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""일반 이상치 발견(discovery) — **손으로 돌리는 독립 스크립트** (2026-08-25 분리).

## 왜 게이트에서 내려왔나

이 스캐너(구 `validate_data_contract` CHECK 5)와 그 뒤의 트리아지는 2026-06-16 에
`discovery → triage → enforce` 퍼널로 설계됐고, 게이트가 매 실행 돌렸다. 실측하니:

  · YELLOW 224건(PEER_OUTLIER 147 · COHORT_ZERO 77) = data-contract 게이트 YELLOW 297건의 **75.4%**
  · RED **0건** — 설계상 YELLOW 전용이라 push 를 막은 적이 구조적으로 없다
  · 리뷰 큐 83건(REAL 77 · UNCERTAIN 6)이 매 실행 재생성되는데, 마지막으로 데이터 수정을
    낳은 것은 **2026-06-19/20 라운드**다(교보생명 원수예실차 4분기 · BNP파리바카디프 단위오류
    1.77조 · 코리안리 중복 43 · 교보라이프플래닛 보험금융손익). 그 이후 두 달간 0건.

owner: *"씰데없는 룰들은 좀 쳐내"*, *"실질 검증은 산술적으로 닫히는 거에서 다 걸린다."*

**지운 게 아니다.** 발견 능력은 2026-06 에 실제로 9칸을 잡았고, 다시 필요해지는 국면
(새 마스터 온보딩 · 새 분기 대량 적재 · 파서 대개편 직후)이 있다. 그때 이걸 돌린다.

## 되살리는 법

`scripts/validate_data_contract.py` 의 `run_gate()` 에서 주석 처리된
`# check_generic_anomalies(res, env)` 줄의 주석을 풀면 원상복귀다.
그 경우 `tests/test_push_gate_wiring.py` 의 `DATA_CONTRACT_CHECKS` 선언도 같이 고쳐야 한다.

## 쓰는 법

    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/scan_generic_anomalies.py

산출(종전과 동일 경로 — publishing §3 LLM-skeptic 이 그대로 읽는다):
    data/_derived/anomaly_triage.json        리뷰 큐 전문(real / uncertain / noise / owner_confirmed)
    data/_derived/anomaly_skeptic_input.json REAL + UNCERTAIN (skeptic 입력)

`--no-write` 를 주면 파일을 안 쓰고 화면 요약만 낸다.
"""
from __future__ import annotations

import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import validate_data_contract as dc            # noqa: E402
import triage_anomaly_candidates as triage     # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="일반 이상치 발견 + 트리아지 (게이트 밖)")
    ap.add_argument("--no-write", action="store_true", help="리뷰 큐 파일을 쓰지 않는다")
    a = ap.parse_args(argv)

    print("=" * 78)
    print("GENERIC ANOMALY DISCOVERY  (게이트에서 분리된 발견 레이어 — push 를 막지 않는다)")
    print("=" * 78)

    # --- (a) 발견: 코호트에서 학습한 metric-agnostic 스캔 -------------------
    env = dc.Env()
    res = dc.GateResult()
    dc.check_generic_anomalies(res, env)
    by_rule = Counter(f.rule for f in res.findings)
    print(f"\n[a] 스캔  후보 {len(res.findings)}건  (RED={len(res.red)} YELLOW={len(res.yellow)})")
    for rule, n in sorted(by_rule.items(), key=lambda kv: -kv[1]):
        print(f"      {n:5d}  {rule}")
    for f in res.findings[:8]:
        print(f"      · [{f.master}] {f.rule}  {f.company or '-'} {f.quarter or '-'}")
        print(f"          {f.message}")
    if len(res.findings) > 8:
        print(f"      ...+{len(res.findings) - 8}건 (전문은 아래 트리아지 산출에)")

    # --- (b) 정밀화: 코호트가 아니라 **그 회사 자신의 이력**으로 판정 --------
    real, noise, uncertain, confirmed = triage.triage()
    print(f"\n[b] 트리아지  REAL={len(real)} UNCERTAIN={len(uncertain)} "
          f"NOISE(자동억제)={len(noise)} OWNER_CONFIRMED(억제)={len(confirmed)}")

    skeptic_input = real + uncertain
    if not a.no_write:
        out_dir = ROOT / "data" / "_derived"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "anomaly_triage.json").write_text(
            json.dumps({"real": real, "uncertain": uncertain, "noise_count": len(noise),
                        "owner_confirmed": confirmed}, ensure_ascii=False, indent=2),
            encoding="utf-8")
        (out_dir / "anomaly_skeptic_input.json").write_text(
            json.dumps(skeptic_input, ensure_ascii=False, indent=2), encoding="utf-8")
        print("      → data/_derived/anomaly_triage.json")
        print(f"      → data/_derived/anomaly_skeptic_input.json ({len(skeptic_input)}건)")
    else:
        print("      (--no-write: 파일 안 씀)")

    print("\n다음 단계(publishing §3): LLM-skeptic 이 REAL/UNCERTAIN 을 "
          "추출·단위오류(→parser) vs 실제 경제적 사건(→없음) 으로 분류한다.")
    print("이 스크립트는 **push 를 막지 않는다** — 판정은 사람/LLM 이 한다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
