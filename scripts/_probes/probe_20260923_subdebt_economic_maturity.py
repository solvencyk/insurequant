# -*- coding: utf-8 -*-
"""후순위채 경제적 만기 해석 2안 전수 시뮬레이션 (owner 질의 2026-09-23).

질의: 한화생명 '후순위사채(외화) 제2회'가 기본자본·보완자본 인정액 둘 다 0인 이유.

현행(A안) = build_capital_securities_recognition.economic_maturity:
    경제적 만기 = min(콜, 법정만기)  -- 콜이 있으면 무조건 콜
대안(B안) = [별표22] Ⅲ.3.다.(2)①ㄱ 문언 그대로:
    '상환촉진 유인이 있는' 콜만 경제적 만기. step_up 플래그가 원천에 없으므로
    스텝업이 확인되지 않은 후순위채는 계약상 만기를 경제적 만기로 본다.

두 안의 보완자본 인정액을 회사별로 대조해 owner 판단 자료를 만든다. 파일은 안 쓴다.
"""
from __future__ import annotations

import io
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

_ORIG_STDOUT = sys.stdout
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.build_capital_securities_recognition import tier2_recognition_rate  # noqa: E402

# 빌더는 import 시점에 sys.stdout 을 자기 TextIOWrapper 로 갈아치운다. 그 래퍼를 그냥
# 버리면 GC 되면서 __del__ 이 원본 버퍼까지 닫아 버린다 — 강한 참조를 남겨 둔다.
_builder_wrapper = sys.stdout   # noqa: F841  (살려 둬야 버퍼가 안 닫힌다)
sys.stdout = _ORIG_STDOUT
sys.stdout.reconfigure(encoding="utf-8")

AS_OF = date(2026, 6, 30)
bonds = json.loads((ROOT / "data/bonds/capital_securities_fy2026h1.json").read_text(encoding="utf-8"))
cur = {r["원보험사코드"] + "|" + (r["구분"] or ""): r
       for r in json.loads((ROOT / "kics_capital_securities.json").read_text(encoding="utf-8"))["rows"]}


def rate_legal(b):
    """B안: 콜을 무시하고 법정만기로만 체감."""
    return tier2_recognition_rate({"call_date": None, "legal_maturity": b.get("legal_maturity"),
                                   "outstanding_mn": b.get("outstanding_mn")}, AS_OF)


per = defaultdict(lambda: {"out": 0.0, "a": 0.0, "b": 0.0})
moved = []
for c in bonds["companies"]:
    for b in c.get("bonds") or []:
        if (b.get("outstanding_mn") or 0) <= 0 or b.get("tier") == "hybrid":
            continue
        out = b["outstanding_mn"] / 100.0
        ra = tier2_recognition_rate(b, AS_OF)
        rb = rate_legal(b)
        per[c["company"]]["out"] += out
        per[c["company"]]["a"] += out * ra
        per[c["company"]]["b"] += out * rb
        if abs(ra - rb) > 1e-9:
            moved.append((c["company"], b["name"][:40], out, ra, rb,
                          b.get("call_date"), b.get("legal_maturity"), b.get("call_source")))

print(f"후순위채 {sum(1 for _ in moved)}건이 두 안에서 다르다 (전체 "
      f"{sum(1 for c in bonds['companies'] for b in (c.get('bonds') or []) if (b.get('outstanding_mn') or 0) > 0 and b.get('tier') != 'hybrid')}건)\n")
print(f"{'회사':<12}{'채권':<42}{'잔액억':>10}{'A율':>6}{'B율':>6}  콜/법정만기")
for co, nm, out, ra, rb, cd, lm, cs in sorted(moved, key=lambda x: -x[2]):
    print(f"{co:<12}{nm:<42}{out:>10,.0f}{ra:>6.1f}{rb:>6.1f}  {cd} / {lm}  [{cs}]")

ta = sum(v["a"] for v in per.values())
tb = sum(v["b"] for v in per.values())
to = sum(v["out"] for v in per.values())
print(f"\n합계  잔액 {to:,.0f}억 · A안(현행) 인정 {ta:,.0f}억 · B안 인정 {tb:,.0f}억 · 차 {tb-ta:+,.0f}억")
print(f"\n{'회사':<14}{'잔액':>10}{'A안':>10}{'B안':>10}{'차이':>10}")
for co, v in sorted(per.items(), key=lambda x: -(x[1]["b"] - x[1]["a"])):
    if abs(v["b"] - v["a"]) < 1:
        continue
    print(f"{co:<14}{v['out']:>10,.0f}{v['a']:>10,.0f}{v['b']:>10,.0f}{v['b']-v['a']:>+10,.0f}")
