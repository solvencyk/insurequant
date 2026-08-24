"""KR0068 2025.2Q — 한도초과 정의 전수 시뮬레이션 (반증 쿼리).

가설 H: `item47(보완자본 한도 적용 전)` 이 `item49(해약환급금 부족분 상당액 중 해약환급금
상당액 초과분)` 를 **포함**하고, 한도는 채무성 부분(`item47 - item49`)에만 걸린다.
  → 구성식  보완자본 = min(item47 - item49, item48) + item49        (식 C)
  → 한도초과 = max(0, (item47 - item49) - item48)                    (식 C')

현행:
  → 구성식  CAPPED: min(item47, item48) + item49  |  UNCAPPED: item47   (식 A / 식 B)
  → 한도초과 = max(0, item47 - item48), CAPPED 일 때만, item12 로 클램프

두 정의를 **같은 데이터에 나란히 걸어** 닫힘/깨짐 양방향을 센다. 룰은 건드리지 않는다.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.solvency.validation.kics_json_rules import (  # noqa: E402
    KEY_CODE, KEY_NAME, KEY_ITEM, KEY_QUARTER, KEY_VALUE, KEY_VALUE_POST,
    TIER2_ZERO_EPS,
)

OUT = ROOT / "artifacts" / "validation" / "probe_20260824_excess_convention_sim.txt"
TOL = 2.0


def num(x):
    if x is None:
        return None
    s = str(x).strip().replace(",", "")
    if s in ("", "-", "N/A", "None", "nan"):
        return None
    neg = False
    if s and s[0] in "△∆":
        neg, s = True, s[1:]
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def load():
    rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    buckets: dict[tuple[str, str], dict] = {}
    for r in rows:
        code, q = r.get(KEY_CODE), r.get(KEY_QUARTER)
        if not code or not q:
            continue
        b = buckets.setdefault((code, q), {"name": r.get(KEY_NAME), "pre": {}, "post": {}})
        try:
            it = int(r.get(KEY_ITEM))
        except (TypeError, ValueError):
            continue
        for key, dest in ((KEY_VALUE, "pre"), (KEY_VALUE_POST, "post")):
            v = num(r.get(key))
            if v is not None:
                b[dest][it] = v
    return buckets


def main():
    buckets = load()
    lines: list[str] = []

    comp = Counter()          # 구성식 A/B/C 성립 교차표
    bridge = Counter()        # 다리 현행 vs C 성립 교차표
    c_breaks: list[str] = []  # C 로 바꾸면 새로 깨지는 구성식 칸
    c_fixes: list[str] = []   # C 로 바꾸면 새로 닫히는 다리 칸
    c_bridge_breaks: list[str] = []

    for (code, q), b in sorted(buckets.items()):
        v14_pre = b["pre"].get(14)
        for post in (False, True):
            src = b["post"] if post else b["pre"]
            col = "적용후" if post else "적용전"
            tag = f"{code} {str(b['name'])[:10]:<11} {q:<8} {col}"
            i3, i47, i48, i49 = src.get(3), src.get(47), src.get(48), src.get(49)

            # ---- 구성식 축 -------------------------------------------------
            if None not in (i3, i47, i48, i49):
                tfi_na = (max(abs(i47), abs(i48), abs(i49)) <= TIER2_ZERO_EPS
                          and v14_pre is not None and abs(v14_pre) > 1.0)
                a_ok = abs(i3 - (min(i47, i48) + i49)) <= TOL
                b_ok = abs(i3 - i47) <= TOL
                c_ok = abs(i3 - (min(i47 - i49, i48) + i49)) <= TOL
                if tfi_na:
                    comp["TFI_NA"] += 1
                else:
                    cur_ok = a_ok or b_ok
                    comp[f"cur={'OK' if cur_ok else 'NEITHER'} C={'OK' if c_ok else 'NG'}"] += 1
                    if cur_ok and not c_ok:
                        c_breaks.append(
                            f"{tag} i3={i3:,.2f} i47={i47:,.2f} i48={i48:,.2f} i49={i49:,.2f} "
                            f"A={'Y' if a_ok else 'n'} B={'Y' if b_ok else 'n'} "
                            f"C_exp={min(i47 - i49, i48) + i49:,.2f}")

            # ---- 다리 축 ---------------------------------------------------
            i2, i4, i12, i13 = src.get(2), src.get(4), src.get(12), src.get(13)
            if None in (i2, i4, i12, i13) or None in (i47, i48, i49, i3):
                continue
            capped_cur = abs(i3 - (min(i47, i48) + i49)) <= TOL
            uncapped_cur = abs(i3 - i47) <= TOL
            if capped_cur:
                raw_exc = max(0.0, i47 - i48)
            else:
                raw_exc = 0.0
            exc_cur = min(raw_exc, max(0.0, i12))
            d_cur = i2 - (i4 - (i12 - exc_cur) - i13)

            exc_c = max(0.0, (i47 - i49) - i48)
            exc_c = min(exc_c, max(0.0, i12))
            d_c = i2 - (i4 - (i12 - exc_c) - i13)

            ok_cur, ok_c = abs(d_cur) <= TOL, abs(d_c) <= TOL
            bridge[f"cur={'OK' if ok_cur else 'RED'} C={'OK' if ok_c else 'RED'}"] += 1
            if not ok_cur and ok_c:
                c_fixes.append(f"{tag} diff_cur={d_cur:>12,.2f} -> diff_C={d_c:>10,.2f} "
                               f"exc_cur={exc_cur:,.2f} exc_C={exc_c:,.2f} i12={i12:,.2f}")
            if ok_cur and not ok_c:
                c_bridge_breaks.append(f"{tag} diff_cur={d_cur:>10,.2f} -> diff_C={d_c:>12,.2f} "
                                       f"exc_cur={exc_cur:,.2f} exc_C={exc_c:,.2f} i12={i12:,.2f}")

    lines.append("=== 구성식 (item3 재현) 교차표 ===")
    for k, v in sorted(comp.items()):
        lines.append(f"  {k:<28} {v}")
    lines.append("")
    lines.append(f"=== C 로 바꾸면 새로 깨지는 구성식 칸 = {len(c_breaks)} ===")
    lines.extend("  " + s for s in c_breaks[:80])
    lines.append("")
    lines.append("=== 다리 (2_tier1_bridge) 교차표 ===")
    for k, v in sorted(bridge.items()):
        lines.append(f"  {k:<28} {v}")
    lines.append("")
    lines.append(f"=== C 로 바꾸면 새로 닫히는 다리 칸 = {len(c_fixes)} ===")
    lines.extend("  " + s for s in c_fixes[:80])
    lines.append("")
    lines.append(f"=== C 로 바꾸면 새로 깨지는 다리 칸 = {len(c_bridge_breaks)} ===")
    lines.extend("  " + s for s in c_bridge_breaks[:120])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
