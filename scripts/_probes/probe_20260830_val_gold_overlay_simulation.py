"""gold 오버레이 축(CHECK 6)의 **전 버킷 양방향 시뮬레이션** (validation, 2026-08-30).

룰을 배선하기 전에 닫힘/깨짐 두 방향을 다 재라는 저장소 규칙(1건 고치려다 129건 깨뜨릴
뻔한 실측이 있다)에 따른 전수 측정. 읽기 전용 — 아무것도 안 쓴다.

A. **닫힘 방향** — 박제된 마스크 칸 전부에 대해 소스를 한 칸씩 흔들고
   `GOLD_OVERLAY_DRIFT` RED 가 그 칸에서 나오는지 센다. 탐지율이 100% 가 아니면
   그만큼이 여전히 마스크다.
B. **허용오차가 밴드가 아닌지** — 같은 칸을 tol 안(0.004)으로만 흔들면 RED 가 없어야 한다.
   (있으면 반올림에 과민, 없으면 정상)
C. **깨짐 방향 1** — 박제 안 된 칸(LOAD_BEARING 등)을 흔들면 새 RED 이 나오면 안 된다
   (그 칸은 애초에 gold 가 정답이고 빌더는 이미 다르다 = 오탐 원천).
D. **깨짐 방향 2** — 등재부를 통째로 비우면 RED 0 · YELLOW 는 마스크 칸 수 만큼.
   즉 "박제를 지우면 검사가 사라지는" 게 아니라 "보호 안 됨"이 열거된다.
E. **게이트 전체 델타** — 이 축을 켠 게이트와 이 축의 finding 을 뺀 게이트의
   RED/YELLOW 를 대조해 다른 축을 건드리지 않았음을 확인한다.

실행:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe \
      scripts/_probes/probe_20260830_val_gold_overlay_simulation.py
"""
from __future__ import annotations

import copy
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_data_contract as G      # noqa: E402


class _Env:
    def __init__(self, overlays, ledger):
        self.gold_overlays = overlays
        self.gold_overlay_ledger = ledger


def run(overlays, ledger):
    res = G.GateResult()
    G.check_gold_overlay(res, _Env(overlays, ledger))
    return res


def src_index(rows):
    return {(r.get("원보험사코드"), r.get("항목번호"), r.get("공시분기")): j
            for j, r in enumerate(rows)}


def mutate(overlays, i, row_j, delta):
    out = list(overlays)
    oid, gold_doc, src_rows, path, err = overlays[i]
    rows = copy.deepcopy(src_rows)
    rows[row_j]["값"] = rows[row_j]["값"] + delta
    out[i] = (oid, gold_doc, rows, path, err)
    return out


def main() -> int:
    env = G.Env()
    overlays = env.gold_overlays
    ledger = env.gold_overlay_ledger or {}
    pins = ledger.get("entries", {})

    base = run(overlays, ledger)
    print(f"기준선: RED={len(base.red)} YELLOW={len(base.yellow)}  박제 {len(pins)}칸")
    assert not base.red, "기준선에 RED 이 있다 — 시뮬레이션 전제가 깨졌다"

    cens = {}
    for i, (oid, gold_doc, src_rows, _p, _e) in enumerate(overlays):
        cens[i] = (oid, G.gold_overlay_census(oid, gold_doc.get("set", []), src_rows),
                   src_index(src_rows))

    # --- A. 닫힘 방향: 박제된 마스크 칸 전수 ---------------------------------
    # 소스가 null 인 박제 칸(gold 도 null = 오버레이가 무의미)은 **건너뛰지 않는다** —
    # SKIP-on-missing 이 이 저장소의 검증 무력화 패턴이다. 그런 칸은 "소스가 값을 얻으면"
    # 을 변이로 삼는다(파서가 그 셀을 뽑기 시작한 상황 = gold 의 null 억제를 재검토해야 한다).
    tried = hit = null_cases = 0
    misses = []
    for i, (oid, rows, idx) in cens.items():
        for r in rows:
            if r["key"] not in pins:
                continue
            j = idx[(r["company"], r["item"], r["quarter"])]
            if isinstance(r["src"], (int, float)):
                mut = mutate(overlays, i, j, max(10.0, abs(r["src"]) * 0.30))  # tol의 200배 이상
            else:
                null_cases += 1
                mut = list(overlays)
                _o, _g, _s, _p, _e = overlays[i]
                srows = copy.deepcopy(_s)
                srows[j]["값"] = 12345.0
                mut[i] = (_o, _g, srows, _p, _e)
            res = run(mut, ledger)
            tried += 1
            if any(f.rule == "GOLD_OVERLAY_DRIFT" and f.company == r["company"]
                   and f.quarter == r["quarter"] for f in res.red):
                hit += 1
            else:
                misses.append(r["key"])
    rate = 100.0 * hit / tried if tried else 0.0
    print(f"\nA. 닫힘 — 박제 마스크 칸 변이시험: 시도 {tried} · 탐지 {hit} ({rate:.1f}%) "
          f"(그중 소스가 null→값을 얻는 변이 {null_cases}건)")
    if misses:
        print(f"   [!] 미탐지 {len(misses)}: {misses[:10]}")

    # --- B. tol 안 변이는 조용해야 한다 --------------------------------------
    # 주입 크기는 **셀별 잔여 여유의 절반**이다. 고정폭(예 0.004)을 쓰면 이미 경계(|d|=0.05)에
    # 붙어 있는 칸이 밖으로 밀려나 RED 가 나고, 그걸 "과민"으로 오독하게 된다 — 실측으로
    # 그 함정을 밟았다(CSM 2칸). 여유가 0 인 칸은 애초에 흔들 수 없으므로 따로 센다.
    inner = no_room = tested = 0
    for i, (oid, rows, idx) in cens.items():
        for r in rows:
            if r["key"] not in pins or not isinstance(r["src"], (int, float)):
                continue
            d = round(abs(r["src"] - r["gold"]), 9) if isinstance(r["gold"], (int, float)) else 0.0
            room = G.GOLD_OVERLAY_TOL_ROUND - d
            if room <= 1e-9:
                no_room += 1
                continue
            j = idx[(r["company"], r["item"], r["quarter"])]
            res = run(mutate(overlays, i, j, room * 0.5), ledger)
            tested += 1
            inner += len([f for f in res.red if f.rule == "GOLD_OVERLAY_DRIFT"])
    print(f"B. 허용오차 — 잔여 여유의 절반만큼 변이({tested}칸, 여유 0 인 경계칸 {no_room}개 제외): "
          f"신규 DRIFT RED {inner}건 (0 이어야 정상 = 밴드가 아니라 반올림 폭)")

    # --- C. 깨짐 1: 박제 안 된 칸을 흔들어도 RED 이 없어야 한다 ---------------
    unp_tried = unp_red = 0
    for i, (oid, rows, idx) in cens.items():
        for r in rows:
            if r["key"] in pins or not isinstance(r["src"], (int, float)):
                continue
            j = idx[(r["company"], r["item"], r["quarter"])]
            res = run(mutate(overlays, i, j, max(10.0, abs(r["src"]) * 0.30)), ledger)
            unp_tried += 1
            unp_red += len(res.red)
    print(f"C. 깨짐 1 — 박제 안 된 칸 전수 변이: 시도 {unp_tried} · 신규 RED {unp_red}건 "
          f"(0 이어야 정상 — 그 칸은 gold 가 정답이고 빌더는 이미 다르다)")

    # --- D. 깨짐 2: 등재부를 비우면 ------------------------------------------
    empty = run(overlays, {**ledger, "entries": {}})
    ct = Counter(f.rule for f in empty.yellow)
    print(f"D. 깨짐 2 — 등재부 전삭제: RED={len(empty.red)} (0 이어야 한다) · "
          f"NEWLY_REDUNDANT={ct['GOLD_OVERLAY_NEWLY_REDUNDANT']} "
          f"(= 마스크 칸 수 {len(pins)} 와 같아야 한다)")

    # --- E. 게이트 전체 델타 --------------------------------------------------
    full = G.run_gate(G.Env())
    mine = [f for f in full.findings if f.rule.startswith("GOLD_OVERLAY_")]
    print(f"E. 게이트 전체: RED={len(full.red)} YELLOW={len(full.yellow)} · "
          f"이 축이 만든 finding {len(mine)}건 "
          f"({Counter(f.rule for f in mine)}) · 이 축을 뺀 나머지 "
          f"RED={len([f for f in full.red if not f.rule.startswith('GOLD_OVERLAY_')])} "
          f"YELLOW={len([f for f in full.yellow if not f.rule.startswith('GOLD_OVERLAY_')])}")

    ok = (not misses) and inner == 0 and unp_red == 0 and not empty.red \
        and ct["GOLD_OVERLAY_NEWLY_REDUNDANT"] == len(pins) and not full.red
    print("\n" + ("ALL PASS" if ok else "FAIL — 위 항목 확인"))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
