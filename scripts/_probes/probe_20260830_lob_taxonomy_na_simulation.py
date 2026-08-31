#!/usr/bin/env python3
"""LOB_LEG_NA 등재부 + 2g LOB_TAXONOMY_NA 룰 전 버킷 시뮬레이션 (2026-08-30).

티켓: inbox/validation/20260830T0200Z__orchestrator__KR1000__lob_taxonomy_exception.md

세 가지를 실측한다 —

  A. **회귀 0**: 등재를 붙이기 전/후로 leg-coverage 판정(닫힘/깨짐/좌변없음, 회사·분기 집합)이
     한 건도 안 바뀌는지. 등재는 면제가 아니므로 **판정은 그대로여야 한다**.
  B. **반증가능**: 등재한 셀(코리안리재보험 item13)에 값을 넣으면 STALE 이 뜨는지.
     안 뜨면 그 등재부는 죽은 등재부(=면제)다.
  C. **dangling**: 등재부에만 있고 마스터에 없는 회사를 넣으면 DANGLE 이 뜨는지.

실행:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe \
      scripts/_probes/probe_20260830_lob_taxonomy_na_simulation.py
"""
from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_master_tables as V  # noqa: E402


def legcov_signature(pl, extra_lob, unknown_hyphen):
    """leg-coverage 판정 지문 — 등재 전/후가 같아야 한다."""
    with contextlib.redirect_stdout(io.StringIO()):
        pb_pass, pb_fail, pb_skip, zleg, zero0 = V._check_pl_bridge(
            pl, extra_lob, unknown_hyphen)
    return {
        "pass": pb_pass,
        "skip": pb_skip,
        "fail": sorted((c, q, lab) for c, q, lab, _l, _d in pb_fail),
        "zleg": sorted((c, q) for c, q, *_r in zleg),
        "zero0": sorted(zero0),
    }


def main() -> int:
    pl = V.load_long(V.PL_PATH)
    extra_lob, unknown_hyphen = V.load_pl_extra_lob(V.PL_PATH)
    print(f"버킷 수 = {len(pl)}  (회사 {len({c for c, _q in pl})}사)")

    # ---- A. 등재 유무로 판정이 바뀌는가 (바뀌면 안 된다) ----
    live = dict(V.LOB_LEG_NA)
    sig_with = legcov_signature(pl, extra_lob, unknown_hyphen)
    V.LOB_LEG_NA.clear()
    sig_without = legcov_signature(pl, extra_lob, unknown_hyphen)
    V.LOB_LEG_NA.update(live)
    same = sig_with == sig_without
    print(f"\nA. 등재 전/후 leg-coverage 판정 동일: {same}")
    print(f"   pass={sig_with['pass']} skip={sig_with['skip']} "
          f"fail={len(sig_with['fail'])} zleg={len(sig_with['zleg'])} "
          f"zero0={len(sig_with['zero0'])}")
    if not same:
        for k in sig_with:
            if sig_with[k] != sig_without[k]:
                print(f"   !! {k} 이 움직였다: {sig_without[k]} -> {sig_with[k]}")

    # ---- B. 등재부는 반증가능한가 ----
    na, stale, dangle = V._check_lob_taxonomy(pl, quiet=True)
    print(f"\nB. 현행: N/A={len(na)} STALE={len(stale)} DANGLE={len(dangle)}")
    mutated = {k: dict(m) for k, m in pl.items()}
    target = next((k for k in sorted(mutated) if k[0] == "코리안리재보험"), None)
    assert target, "코리안리재보험 버킷이 마스터에 없다 — 등재부가 이미 dangling"
    mutated[target]["자동차손익"] = 12345.0
    na2, stale2, dangle2 = V._check_lob_taxonomy(mutated, quiet=True)
    print(f"   item13 에 12345.0 주입 -> N/A={len(na2)} STALE={len(stale2)} "
          f"DANGLE={len(dangle2)}  탐지={'YES' if stale2 else 'NO (죽은 등재부!)'}")
    for row in stale2:
        print(f"     LOBSTALE {row}")

    # ---- C. dangling 등재 ----
    V.LOB_LEG_NA["없는회사보험"] = {"자동차손익": "시뮬레이션용"}
    _na3, _s3, dangle3 = V._check_lob_taxonomy(pl, quiet=True)
    V.LOB_LEG_NA.pop("없는회사보험")
    print(f"\nC. 마스터에 없는 회사 등재 -> DANGLE={dangle3}  "
          f"탐지={'YES' if dangle3 else 'NO'}")

    ok = same and bool(stale2) and bool(dangle3) and not stale and not dangle
    print(f"\n결론: {'PASS' if ok else 'FAIL'} "
          "(회귀 0 + 반증가능 + 현행 등재 무결)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
