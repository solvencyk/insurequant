# -*- coding: utf-8 -*-
"""공시표가 **직전 분기 것**인지를 재는 탐지기 (K-ICS 경과조치 블록 items 47~54).

## 왜 만들었나

2026-09-01 롯데손해(KR0003) 2026.1Q 에서 TFI 표가 통째로 직전 분기(2025.4Q) 기준값으로
인쇄된 것이 발견됐다. 그런데 **그것을 잡은 룰은 없었다** — `48_tier2_limit`(item48 =
item14_적용전 x 50%)이 잔차를 냈고, 사람이 그 잔차의 원인을 손으로 파고들어서야
"직전분기 SCR 기준" 임을 알아냈다. `TIER2_LIMIT_STALE` 은 그 뒤에 예외 등재부에
붙인 **라벨**이지 탐지기가 아니다.

즉 이 저장소에는 **"이 표가 어느 분기 것인가"를 보는 검사가 없었다.** `48_tier2_limit`
잔차는 발행사 총괄표/세부표 불일치로도 나므로, 다음에 같은 일이 생기면
`_TIER2_ISSUER_INCONSISTENT` 에 "발행사 불일치" 로 등재되고 **원인이 영구히 묻힌다.**
스테일 표는 발행사 불일치와 달리 **고칠 수 있는 결함**(원천 선택·파싱)이라 구분이 중요하다.

## 무엇을 재나

지문 A — `item48` 이 **직전분기** SCR 의 50% 와 맞고 **당분기** SCR 의 50% 와는 어긋난다.
  item48 은 한도 산식이 하나뿐이라 어느 분기 SCR 을 썼는지 역산할 수 있다. 이 블록에서
  분기를 특정할 수 있는 유일한 칸이다.
지문 B — `items 47~54` 중 값이 있는 칸이 **전부** 직전분기와 같은데 SCR 은 바뀌었다.
  한도 산식이 없는 칸까지 포함해 표 통째 재탕을 잡는다.

둘 다 **SCR(item14)이 실제로 바뀐 (회사,분기)에서만** 판정한다. SCR 이 그대로면 값이 같은
것이 정상이라 판별 근거가 없다.

## 전수 census (2026-09-01, 25,329 레코드 / 전 회사 x 13분기, 적용전·적용후 두 열)

    지문 A : 1 건 (KR0003 2026.1Q, 적용전)   지문 B : 0 건

오탐 0. 알려진 1건은 아래 `_KNOWN` 에 결정과 함께 등재돼 있고, **그 밖의 히트가 나오면
exit code 1** 로 push 를 막는다. 새 스테일 표를 발행사 불일치로 오등재하는 경로를 닫는 것이
이 스크립트의 목적이다.
"""
from __future__ import annotations

import json
import pathlib
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
MASTER = ROOT / "kics_disclosure.json"

TOL = 0.5
TFI_ITEMS = range(47, 55)

# 알려진 히트 = 이미 조사가 끝나 owner 결정이 붙은 것. 여기 없는 히트는 blocking.
#
# 2026-09-11 (inbox 20260911T1407Z__ifrs17-session, REOPEN 조사): KR0003 2026.1Q 항목이
# 빠졌다 -- 새 세션이 "왜 없지"로 헤매지 않도록 이력을 남긴다. 이 파일을 만든
# 2026-09-01 census 시점엔 이 히트가 실재했다(owner 결정 = 원공시 그대로 유지). 그런데
# 2026-09-03 발행사가 원문을 재제출했다(구본 886,240B "최종 제출_20260528" -> 신본
# 1,927,066B "재제출", commit 66cfa0b) -- TFI 표(item47~52) 6칸을 재파싱해 정정한 결과
# 더 이상 전기(2025.4Q) 재게시가 아니게 됐고, 같은 커밋이
# `kics_json_rules._TIER2_ISSUER_INCONSISTENT[('KR0003','2026.1Q')]` 등재도 함께 뺐다.
#
# 회귀(탐지기가 죽음)가 아니라 데이터가 정말 바뀐 것이라는 증거 두 가지:
#   1) `detect()` 를 재제출 직전 스냅샷(git show 7c33aae:kics_disclosure.json, 66cfa0b 의
#      부모 커밋)에 돌리면 **지금도** fingerprint A 가 그대로 잡힌다
#      (scripts/_probes/probe_20260911_ticket3_stale_detector_proof.py, 세션 로컬).
#   2) 현재 마스터는 이 히트를 포함해 전사 히트가 **0건**이다 -- 대체 등재할 "다른 살아있는
#      히트"가 없다.
# 그래서 "탐지기가 여전히 잡는다"는 이제 라이브 데이터가 아니라
# `tests/test_stale_quarter_tables.py::test_the_kr0003_2026q1_regression_pattern_would_still_be_caught`
# 가 이 정확한 과거 패턴(item48 = 직전분기 SCR x 50%)을 사본에 합성 주입해 증명한다.
_KNOWN: dict[tuple[str, str, str], str] = {}


def _f(v):
    if v is None:
        return None
    s = str(v).replace(",", "").replace("△", "-").strip()
    if s in ("", "-", "None"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _prev(q: str) -> str:
    y, n = q.split(".")
    y, n = int(y), int(n[0])
    return f"{y - 1}.4Q" if n == 1 else f"{y}.{n - 1}Q"


def detect(records: list[dict]) -> list[dict]:
    by: dict[tuple[str, str, str], dict[int, float]] = defaultdict(dict)
    names: dict[str, str] = {}
    for r in records:
        code, q = r["원보험사코드"], r["공시분기"]
        names[code] = r.get("원수사명", code)
        for col in ("값", "값_적용후"):
            v = _f(r.get(col))
            if v is not None:
                by[(code, q, col)][r["항목번호"]] = v

    hits: list[dict] = []
    for (code, q, col), items in sorted(by.items()):
        prev = by.get((code, _prev(q), col))
        if not prev:
            continue
        i14, p14 = items.get(14), prev.get(14)
        if i14 is None or p14 is None or abs(i14 - p14) <= TOL:
            continue  # SCR 이 안 바뀌면 어느 분기 표인지 판별 불가

        i48 = items.get(48)
        if i48 is not None and abs(i48 - p14 * 0.5) <= TOL and abs(i48 - i14 * 0.5) > TOL:
            hits.append({
                "fingerprint": "A", "code": code, "name": names[code], "quarter": q,
                "column": col, "item48": i48,
                "expected_this_quarter": round(i14 * 0.5, 2),
                "expected_prev_quarter": round(p14 * 0.5, 2),
                "why": "item48 이 직전분기 SCR 의 50% 와 일치한다 = 한도표가 직전분기 것",
            })

        cur = {k: items[k] for k in TFI_ITEMS if k in items}
        if len(cur) >= 3 and all(
            k in prev and abs(v - prev[k]) <= TOL for k, v in cur.items()
        ):
            hits.append({
                "fingerprint": "B", "code": code, "name": names[code], "quarter": q,
                "column": col, "matched_cells": len(cur),
                "why": "47~54 값칸이 전부 직전분기와 동일한데 SCR 은 바뀌었다 = 표 통째 재탕",
            })
    return hits


def main() -> int:
    if not MASTER.exists():
        print(f"[stale-quarter] SKIP — {MASTER.name} 없음 (slim 워크트리)")
        return 0
    records = json.loads(MASTER.read_text(encoding="utf-8"))
    hits = detect(records)

    known, unknown = [], []
    for h in hits:
        (known if (h["code"], h["quarter"], h["column"]) in _KNOWN else unknown).append(h)

    print(f"[stale-quarter] 히트 {len(hits)}건 — 등재 {len(known)} · 미등재 {len(unknown)}")
    for h in known:
        print(f"  KNOWN  [{h['fingerprint']}] {h['code']} {h['name']} {h['quarter']} ({h['column']})")
    for h in unknown:
        print(f"  RED    [{h['fingerprint']}] {h['code']} {h['name']} {h['quarter']} ({h['column']})")
        print(f"         {h['why']}")
        for k in ("item48", "expected_this_quarter", "expected_prev_quarter", "matched_cells"):
            if k in h:
                print(f"         {k} = {h[k]}")

    if unknown:
        print()
        print("[stale-quarter] RED — 직전분기 표가 새로 들어왔다. 발행사 불일치로 등재하지 말고")
        print("                원천(어느 분기 PDF·어느 페이지)을 먼저 확인할 것. 스테일 표는")
        print("                발행사 불일치와 달리 고칠 수 있는 결함이다.")
        return 1
    print("[stale-quarter] GREEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
