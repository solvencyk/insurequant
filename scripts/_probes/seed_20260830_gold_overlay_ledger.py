"""`data/_gold/gold_overlay_ledger.json` 을 현재 실측으로 박제한다 (validation, 2026-08-30).

## 무엇을 박제하나

`scripts/validate_data_contract.py` CHECK 6(gold 오버레이) 이 **마스크**로 판정한 셀 —
빌더 fresh 소스가 이미 gold 와 같은 값을 내고 있어서, gold 를 지워도 화면이 안 바뀌는 칸이다.
그 칸은 지금 안전해 보이지만 **보호가 아니라 은폐**다: 밑에서 빌더가 회귀해도 gold 가 덮어써
화면은 옳고 모든 게이트가 clean 을 찍는다. 그래서 셀 단위로 (판정, 소스값) 을 박제하고,
게이트가 매 실행 재검산해 판정이 마스크를 벗으면 `GOLD_OVERLAY_DRIFT` RED 를 낸다.

**통째 면제가 아니다.** 여기 있는 줄은 "이 칸은 검사하지 마라"가 아니라 "이 칸은 이 상태였다"
이고, 상태가 바뀌면 막힌다. 박제되지 않은 마스크 칸은 게이트가 `GOLD_OVERLAY_NEWLY_REDUNDANT`
YELLOW 로 매 실행 열거한다(= 보호받지 않는 칸이 조용히 늘지 않는다).

## 언제 다시 돌리나

  · 파서가 gold 밑의 소스를 정당하게 고쳐 `GOLD_OVERLAY_PIN_MOVED` 가 뜰 때 (재박제)
  · owner 가 gold 를 추가·삭제해 `NEWLY_REDUNDANT` / `LEDGER_STALE` 이 뜰 때
  · `GOLD_OVERLAY_DRIFT` RED 가 떴는데 **조사 결과 빌더 쪽이 옳다고 확정된** 경우
    (그때는 gold 줄을 지우는 것이 먼저다 — 재박제로 RED 를 덮지 마라)

실행:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe \
      scripts/_probes/seed_20260830_gold_overlay_ledger.py [--apply]
"""
from __future__ import annotations

import json
import shutil
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_data_contract as G      # noqa: E402

NOTE = ("2026-08-30 최초 박제 (inbox/validation/20260830T0710Z). 이 칸들은 gold 를 지워도 "
        "화면이 안 바뀐다 — 즉 gold 가 빌더를 **가리고** 있다. 판정이 마스크를 벗으면 "
        "GOLD_OVERLAY_DRIFT RED.")


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    apply = "--apply" in argv

    env = G.Env()
    entries, pop = {}, {}
    for oid, gold_doc, src_rows, src_path, err in env.gold_overlays:
        if err:
            print(f"[!] {oid}: 소스를 못 읽는다 ({src_path}: {err}) — 박제하지 않는다")
            return 2
        rows = G.gold_overlay_census(oid, gold_doc.get("set", []), src_rows)
        tally = Counter(r["verdict"] for r in rows)
        pop[oid] = {"gold_cells": len(rows), **{k: tally[k] for k in sorted(tally)}}
        for r in rows:
            if r["verdict"] not in G._GOLD_MASKED:
                continue
            entries[r["key"]] = {
                "overlay": oid,
                "verdict": r["verdict"],
                "gold": r["gold"],
                "src": r["src"],
                "source_file": src_path,
                "note": NOTE,
            }
        print(f"{oid}: {len(rows)} gold cells -> masked "
              f"{tally['SAME_EXACT'] + tally['SAME_AT_1DP']} "
              f"(SAME_EXACT={tally['SAME_EXACT']} SAME_AT_1DP={tally['SAME_AT_1DP']}), "
              f"LOAD_BEARING={tally['LOAD_BEARING']} ROW_ABSENT={tally['ROW_ABSENT_IN_SOURCE']} "
              f"NULL_IN_SOURCE={tally['NULL_IN_SOURCE']} GOLD_SUPPRESSES={tally['GOLD_SUPPRESSES']}")

    doc = {
        "_what": ("gold 오버레이가 빌더 소스를 덮고 있는 **마스크 칸**의 셀 단위 박제부. "
                  "build_root_masters 의 _apply_csm_overrides / _apply_pl_overrides 는 gold 를 "
                  "소스와 비교하지 않고 무조건 UPSERT 한다 — 그래서 gold 밑에서 빌더가 회귀해도 "
                  "화면은 옳고 게이트는 clean 을 찍었다(2026-08-30 이전 전 저장소 대조기 0건). "
                  "여기 있는 줄은 면제가 아니라 상태 박제이고, 판정이 바뀌면 게이트가 막는다."),
        "_gate": "scripts/validate_data_contract.py::check_gold_overlay (CHECK 6)",
        "_reseed": "scripts/_probes/seed_20260830_gold_overlay_ledger.py --apply",
        "_basis": ("비교 기준은 빌더의 **fresh 소스 파일**이다. _additive_merge 의 루트 마스터 "
                   "폴백은 직전 실행의 gold 값을 되먹이므로 기준으로 쓰면 검사가 자기 자신을 "
                   "확인하게 된다. PL 의 _zero_other_expense(item16→null)도 같은 이유로 "
                   "재현하지 않는다 — 감시 대상은 '파서가 아직 이 값을 원문에서 뽑는가' 다."),
        "_tolerance": {"exact": G.GOLD_OVERLAY_TOL_EXACT, "round": G.GOLD_OVERLAY_TOL_ROUND,
                       "basis": ("CSM: 소스(csm_waterfall_master_diag)는 소수 1자리, gold 는 2자리라 "
                                 "'재현'의 상한이 ±0.05 다. PL(백만원): 실측 |diff| 가 0.0317 과 "
                                 "18.0 사이에서 완전히 갈린다 — 0.05 는 그 빈 구간 안이다.")},
        "_measured_at": "2026-08-30 (validation, inbox/validation/20260830T0710Z)",
        "_population": pop,
        "entries": dict(sorted(entries.items())),
    }
    print(f"\n박제 대상 {len(entries)}칸")
    if not apply:
        print("(dry-run — 쓰지 않았다. --apply 로 실행)")
        return 0
    if G.GOLD_OVERLAY_LEDGER.exists():
        shutil.copy2(G.GOLD_OVERLAY_LEDGER,
                     G.GOLD_OVERLAY_LEDGER.with_suffix(".json.bak_20260830_reseed"))
    G.GOLD_OVERLAY_LEDGER.write_text(json.dumps(doc, ensure_ascii=False, indent=2),
                                     encoding="utf-8")
    print(f"wrote {G.GOLD_OVERLAY_LEDGER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
