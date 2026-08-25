# -*- coding: utf-8 -*-
"""전 회사·전 분기 시뮬레이션: 단위판별 패치 전/후 waterfall_for_dir 결과 전건 diff (read-only).

`inbox/parser/20260825T0800Z` 수정(scripts/build_csm_waterfall_master.py 의
`_detect_unit_udiv` 신설 + `waterfall_for_dir` 배선) 이 8개 기지 MISMATCH 버킷을
바로잡으면서 다른 294개 버킷을 건드리지 않는지 302개 raw 디렉터리 전수로 확인한다.

OLD 최종환산은 패치 전 3줄 휴리스틱을 이 스크립트 안에 그대로 재현한다(별도 모듈
스냅샷을 import 하지 않음 — 로직이 3줄뿐이라 재현이 더 안전하고 감사하기 쉽다).
NEW 는 패치된 실제 `waterfall_for_dir`(`_detect_unit_udiv` 사용)를 그대로 호출한다.

main() 은 호출하지 않는다 — 파일을 전혀 쓰지 않는다(diag/cov 갱신 없음).

usage:
    python scripts/_probes/probe_20260825b_csm_unit_fix_simulation.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import build_csm_waterfall_master as bcm  # noqa: E402  (main() 미호출)


def old_vals(rd: Path, name: str, anchor):
    """패치 전 waterfall_for_dir 재현 (최종환산만 old 휴리스틱, 나머지는 동일 코드 재사용)."""
    blocks = bcm.blocks_for_dir(rd, name)
    if not blocks:
        return None, None
    m = re.match(r"(KR\d+)_", rd.name)
    wf, src = bcm.waterfall(blocks, anchor, m.group(1) if m else None)
    if not wf:
        return None, src
    if (wf.get(2) or 0) < 0:
        nb = bcm._annual_newbiz_from_detail(blocks)
        if nb is not None:
            wf = {**wf, 2: nb}
            src = (src or "") + "+nb"
    mag = max((abs(v) for v in wf.values() if v is not None), default=0.0)
    udiv = 1_000_000.0 if mag > 1e10 else (1_000.0 if mag > 1e8 else 1.0)
    if udiv != 1.0:
        wf = {no: (v / udiv if v is not None else None) for no, v in wf.items()}
    clo = wf.get(6) or 0
    assum = clo - ((wf.get(1) or 0) + (wf.get(2) or 0) + (wf.get(3) or 0) + (wf.get(5) or 0))
    vals = {1: wf.get(1), 2: wf.get(2), 3: wf.get(3), 4: assum, 5: wf.get(5), 6: wf.get(6)}
    return {no: (round(v / 100, 1) if v is not None else None) for no, v in vals.items()}, src


def main() -> int:
    dirs_by_kr: dict[str, list[Path]] = {}
    for d in sorted(ROOT.glob("data/dart/FY*_Q*/raw/*")):
        if not d.is_dir() or not any(d.glob("*.xml")):
            continue
        m = re.match(r"(KR\d+)_", d.name)
        if not m:
            continue
        dirs_by_kr.setdefault(m.group(1), []).append(d)

    def qkey(rd):
        m = re.search(r"FY(\d{4})_Q(\d)", str(rd))
        return (int(m.group(1)), int(m.group(2))) if m else (0, 0)

    # company display names from META (same source main() uses)
    names = {kr: nm for kr, (nm, _t, _sb) in bcm.META.items()}

    t0 = time.time()
    same = changed = new_blank = both_none = 0
    changes = []
    ambiguous = []
    magfallback = []
    n_dirs = 0
    for kr, dirs in sorted(dirs_by_kr.items()):
        dirs = sorted(dirs, key=qkey)
        name = names.get(kr, kr)
        # Two INDEPENDENT anchor passes (old-world anchors feed old-world Q1-3 picks;
        # new-world anchors feed new-world Q1-3 picks) -- mirrors what main() would
        # actually do pre- and post-patch, so a shifted Q4 udiv can also legitimately
        # shift which Q1-3 candidate the (untouched) internal anchor-comparison sites
        # select, and that shows up as a CHANGED bucket instead of being masked by
        # reusing one pass's anchors for both worlds.
        annual_open_old, annual_close_old = {}, {}
        annual_open_new, annual_close_new = {}, {}
        for rd in dirs:
            q = bcm.quarter_from(rd)
            if q and q.endswith("4Q"):
                av, _ = old_vals(rd, name, None)
                if av:
                    if av.get(1) is not None:
                        annual_open_old[int(q[:4])] = av[1]
                    if av.get(6) is not None:
                        annual_close_old[int(q[:4])] = av[6]
                bv, _ = bcm.waterfall_for_dir(rd, name, None)
                if bv:
                    if bv.get(1) is not None:
                        annual_open_new[int(q[:4])] = bv[1]
                    if bv.get(6) is not None:
                        annual_close_new[int(q[:4])] = bv[6]
        for rd in dirs:
            n_dirs += 1
            q = bcm.quarter_from(rd)
            if not q:
                continue
            y = int(q[:4])
            anchor_old = None if q.endswith("4Q") else (
                annual_open_old.get(y) or annual_close_old.get(y - 1))
            anchor_new = None if q.endswith("4Q") else (
                annual_open_new.get(y) or annual_close_new.get(y - 1))
            ov, osrc = old_vals(rd, name, anchor_old)
            nv, nsrc = bcm.waterfall_for_dir(rd, name, anchor_new)
            if ov is None and nv is None:
                both_none += 1
                continue
            if ov == nv:
                same += 1
            else:
                changed += 1
                if ov is not None and nv is None:
                    new_blank += 1
                changes.append((kr, name, q, ov, nv, osrc, nsrc))
            utag = (nsrc or "").rsplit("+u:", 1)[-1] if nsrc and "+u:" in nsrc else None
            if utag == "ambiguous":
                ambiguous.append((kr, name, q, osrc, nsrc))
            if utag == "mag":
                magfallback.append((kr, name, q, osrc, nsrc))

    print(f"dirs walked: {n_dirs}  companies: {len(dirs_by_kr)}  ({time.time()-t0:.0f}s)")
    print(f"same={same}  changed={changed}  both_none={both_none}  "
          f"(new_blank_within_changed={new_blank})")
    print()
    print("=" * 100)
    print(f"CHANGED buckets ({len(changes)}):")
    print("=" * 100)
    for kr, name, q, ov, nv, osrc, nsrc in changes:
        o6 = ov.get(6) if ov else None
        n6 = nv.get(6) if nv else None
        print(f"  {kr} {name} {q}  기말(억) old={o6} new={n6}  "
              f"old_src={osrc}  new_src={nsrc}")
    print()
    print(f"ambiguous-tag buckets (blanked, {len(ambiguous)}):")
    for row in ambiguous:
        print("   ", row)
    print(f"mag-fallback-tag buckets (no literal evidence at all, {len(magfallback)}):")
    for row in magfallback:
        print("   ", row)
    return 0


if __name__ == "__main__":
    sys.exit(main())
