# -*- coding: utf-8 -*-
"""신설 커버리지 룰 `PL_BUCKET_ABSENT_VS_WATERFALL` 전 버킷 시뮬레이션 + 변이시험.

게이트를 고치기 **전에** 돌린다(저장소 관행: 1건 고치려다 129건 깨뜨릴 뻔한 전례).
닫힘/깨짐 양방향을 다 본다:
  · 평시  — 라이브 마스터에서 RED 0 · baseline YELLOW 12 여야 한다.
  · M1 baseline 줄 삭제        -> 그 버킷이 RED 로 살아나야 한다(면제가 죽은 채로 안 남는다).
  · M2 baseline 박제값 변조    -> DRIFT RED.
  · M3 PL 버킷이 생김          -> INERT(지우라고 말해야 한다).
  · M4 새 결손(PL 버킷 삭제)    -> RED (baseline 에 없으니 차단).
  · M5 스코프 누출 — 룰이 baseline 밖 회사·분기를 건드리지 않는지.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_master_tables import CSM_AMORT_MIN_EOK, load_long  # noqa: E402

PIN_TOL_ABS, PIN_TOL_REL = 0.5, 0.05
BASELINE = ROOT / "data" / "_gold" / "pl_amort_coverage_baseline.json"


def rule(pl: dict, wf: dict, entries: dict) -> list[tuple[str, str, str, str]]:
    """(severity, rule, company, quarter) 목록. 게이트에 넣을 로직과 동일하게 유지할 것."""
    out, seen = [], set()
    for (co, q), wfm in sorted(wf.items()):
        amort = wfm.get("CSM상각")
        if not isinstance(amort, (int, float)) or abs(amort) < CSM_AMORT_MIN_EOK:
            continue
        if (co, q) in pl:
            continue
        key = f"{co}|{q}"
        seen.add(key)
        e = entries.get(key)
        if e is None:
            out.append(("RED", "PL_BUCKET_ABSENT_VS_WATERFALL", co, q))
            continue
        pinned = e.get("wf_amort_eok")
        tol = max(PIN_TOL_ABS, PIN_TOL_REL * abs(pinned)) if isinstance(pinned, (int, float)) else 0
        if not isinstance(pinned, (int, float)) or abs(abs(amort) - pinned) > tol:
            out.append(("RED", "PL_BUCKET_ABSENT_BASELINE_DRIFT", co, q))
        else:
            out.append(("YELLOW", "PL_BUCKET_ABSENT_BASELINE", co, q))
    for key in sorted(k for k in entries if k not in seen):
        co, _, q = key.partition("|")
        out.append(("YELLOW", "PL_BUCKET_ABSENT_BASELINE_INERT", co, q))
    return out


def summarize(tag: str, f: list) -> dict:
    red = [x for x in f if x[0] == "RED"]
    print(f"  {tag:44s} RED={len(red):2d} YELLOW={len(f) - len(red):2d}"
          + ("   " + ", ".join(f"{r}/{c} {q}" for _s, r, c, q in red[:4]) if red else ""))
    return {"red": len(red), "yellow": len(f) - len(red)}


def main() -> None:
    pl = load_long("PL_breakdown.json")
    wf = load_long("CSM_waterfall.json")
    entries = json.loads(BASELINE.read_text(encoding="utf-8"))["entries"] \
        if BASELINE.exists() else {}
    print(f"baseline entries = {len(entries)}   PL={len(pl)} WF={len(wf)}\n")

    print("[평시]")
    base = summarize("live", rule(pl, wf, entries))

    print("\n[변이시험]")
    k0 = "삼성화재해상보험|2023.1Q"
    e1 = copy.deepcopy(entries)
    e1.pop(k0, None)
    m1 = summarize(f"M1 baseline 삭제({k0})", rule(pl, wf, e1))

    e2 = copy.deepcopy(entries)
    if k0 in e2:
        e2[k0]["wf_amort_eok"] = 1.0
    m2 = summarize("M2 baseline 박제값 변조", rule(pl, wf, e2))

    pl3 = copy.deepcopy(pl)
    pl3[("삼성화재해상보험", "2023.1Q")] = {"원수CSM상각": 376038.0}
    m3 = summarize("M3 PL 버킷이 생김 -> INERT", rule(pl3, wf, entries))

    pl4 = copy.deepcopy(pl)
    victim = None
    for (co, q), m in sorted(pl.items()):
        w = wf.get((co, q)) or {}
        a = w.get("CSM상각")
        if isinstance(a, (int, float)) and abs(a) >= CSM_AMORT_MIN_EOK and f"{co}|{q}" not in entries:
            victim = (co, q)
            break
    if victim:
        pl4.pop(victim)
    m4 = summarize(f"M4 새 결손({victim[0]} {victim[1]})", rule(pl4, wf, entries))

    print("\n[검증]")
    ok = True

    def chk(cond, msg):
        nonlocal ok
        print(("  PASS  " if cond else "  FAIL  ") + msg)
        ok = ok and cond

    chk(base["red"] == 0, f"평시 RED=0 (실측 {base['red']}) — 배포를 막지 않는다")
    chk(base["yellow"] == 12, f"평시 baseline YELLOW=12 (실측 {base['yellow']}) — 12건이 보인다")
    chk(m1["red"] == 1, f"M1 baseline 줄을 지우면 RED 로 살아난다 (실측 {m1['red']})")
    chk(m2["red"] == 1, f"M2 박제값을 흔들면 DRIFT RED (실측 {m2['red']})")
    chk(m3["red"] == 0 and m3["yellow"] == 12,
        f"M3 값이 채워지면 INERT 로 남아 지우라고 말한다 (RED {m3['red']} / Y {m3['yellow']})")
    chk(m4["red"] == 1, f"M4 새 결손은 baseline 밖이라 차단한다 (실측 {m4['red']})")

    scope = {(c, q) for _s, _r, c, q in rule(pl, wf, entries)}
    keys = {tuple(k.split("|")) for k in entries}
    chk(scope == keys, f"M5 룰이 baseline 스코프 밖으로 새지 않는다 (룰 {len(scope)} / 등재 {len(keys)})")

    print("\n" + ("ALL PASS" if ok else "FAILURES ABOVE"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
