"""스코프 인식 한도초과 정의의 전수 시뮬레이션 (룰 편집 전 필수 단계).

발견: `item47(보완자본 한도 적용 전)` 의 **스코프가 회사마다 다르다.**
  EXCL 사 : item47 = 채무성 자본만. 공시 보완자본 item3 = min(i47, i48) + i49
  INCL 사 : item47 이 item49(해약환급금 초과분)를 포함. item3 = min(i47 - i49, i48) + i49

현행 룰은 EXCL 만 알고, INCL 사의 "한도 미구속" 분기를 `UNCAPPED`(= 한도로 안 자름)라는
**별개 관행**으로 취급한다. 그러나 INCL 로 읽으면 그 분기들은 한도가 그냥 안 걸린 것이고,
한도가 걸리는 분기에서는 EXCL 과 값이 우연히 일치해 `CAPPED` 로 오분류된다.
그때 한도초과가 `i47 - i48`(과대) 로 계산된다 — KR0068 2025.2Q 가 그 유일 사례.

여기서는 스코프를 버킷/회사 단위로 판정한 뒤 한도초과를 다시 계산하고,
다리(2_tier1_bridge) 성적을 현행과 **양방향으로** 센다. 룰 파일은 건드리지 않는다.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.solvency.validation.kics_json_rules import (  # noqa: E402
    KEY_CODE, KEY_NAME, KEY_ITEM, KEY_QUARTER, KEY_VALUE, KEY_VALUE_POST,
    TIER2_ZERO_EPS,
)

OUT = ROOT / "artifacts" / "validation" / "probe_20260824_scope_aware_bridge.txt"
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


def readings(src):
    i3, i47, i48, i49 = src.get(3), src.get(47), src.get(48), src.get(49)
    if None in (i3, i47, i48, i49):
        return None
    excl_ok = abs(i3 - (min(i47, i48) + i49)) <= TOL
    incl_ok = abs(i3 - (min(i47 - i49, i48) + i49)) <= TOL
    return i3, i47, i48, i49, excl_ok, incl_ok


def main():
    buckets = load()

    # --- 1단계: 회사별 스코프 투표 (모호하지 않은 버킷만, 적용전+적용후) ----
    vote: dict[str, Counter] = defaultdict(Counter)
    for (code, q), b in buckets.items():
        for dest in ("pre", "post"):
            r = readings(b[dest])
            if r is None:
                continue
            i3, i47, i48, i49, e, i = r
            if max(abs(i47), abs(i48), abs(i49)) <= TIER2_ZERO_EPS:
                continue
            if e and not i:
                vote[code]["EXCL"] += 1
            elif i and not e:
                vote[code]["INCL"] += 1

    scope_of = {}
    for code, c in vote.items():
        if c["INCL"] and not c["EXCL"]:
            scope_of[code] = "INCL"
        elif c["EXCL"] and not c["INCL"]:
            scope_of[code] = "EXCL"
        else:
            scope_of[code] = "CONFLICT"

    lines = ["=== 1단계: 회사별 item47 스코프 투표 (모호 버킷 제외) ===",
             f"{'code':<7}{'name':<15}{'EXCL표':>7}{'INCL표':>7}  scope"]
    for code in sorted(vote):
        c = vote[code]
        nm = next((b["name"] for (cc, _), b in buckets.items() if cc == code), "")
        lines.append(f"{code:<7}{str(nm)[:14]:<15}{c['EXCL']:>7}{c['INCL']:>7}  {scope_of[code]}")
    lines.append("")
    agg = Counter(scope_of.values())
    lines.append(f"집계: {dict(agg)}")
    lines.append("")

    # --- 2단계: 다리 전수 재계산 -------------------------------------------
    bridge = Counter()
    fixes, breaks = [], []
    for (code, q), b in sorted(buckets.items()):
        for post in (False, True):
            src = b["post"] if post else b["pre"]
            col = "적용후" if post else "적용전"
            tag = f"{code} {str(b['name'])[:10]:<11} {q:<8} {col}"
            i2, i4, i12, i13 = src.get(2), src.get(4), src.get(12), src.get(13)
            if None in (i2, i4, i12, i13):
                continue
            r = readings(src)
            if r is None:
                continue
            i3, i47, i48, i49, excl_ok, incl_ok = r

            # 현행
            uncapped_cur = abs(i3 - i47) <= TOL
            raw_cur = max(0.0, i47 - i48) if excl_ok else 0.0
            if not excl_ok and uncapped_cur:
                raw_cur = 0.0
            exc_cur = min(raw_cur, max(0.0, i12))
            d_cur = i2 - (i4 - (i12 - exc_cur) - i13)

            # 제안: 버킷 자신의 재현으로 스코프 결정, 모호하면 회사 투표
            if incl_ok and not excl_ok:
                scope = "INCL"
            elif excl_ok and not incl_ok:
                scope = "EXCL"
            elif excl_ok and incl_ok:
                scope = scope_of.get(code, "EXCL")
                if scope == "CONFLICT":
                    scope = "EXCL"
            else:
                scope = None  # NEITHER — 별도 축이 RED

            if scope == "INCL":
                raw_new = max(0.0, (i47 - i49) - i48)
            elif scope == "EXCL":
                raw_new = max(0.0, i47 - i48)
            else:
                raw_new = 0.0
            exc_new = min(raw_new, max(0.0, i12))
            d_new = i2 - (i4 - (i12 - exc_new) - i13)

            ok_cur, ok_new = abs(d_cur) <= TOL, abs(d_new) <= TOL
            bridge[f"cur={'OK' if ok_cur else 'RED'} new={'OK' if ok_new else 'RED'}"] += 1
            if not ok_cur and ok_new:
                fixes.append(f"{tag} scope={scope:<5} diff {d_cur:>12,.2f} -> {d_new:>10,.2f} "
                             f"exc {exc_cur:>10,.2f} -> {exc_new:>10,.2f}")
            if ok_cur and not ok_new:
                breaks.append(f"{tag} scope={scope:<5} diff {d_cur:>10,.2f} -> {d_new:>12,.2f} "
                              f"exc {exc_cur:>10,.2f} -> {exc_new:>10,.2f}")

    lines.append("=== 2단계: 다리(2_tier1_bridge) 교차표 — 현행 vs 스코프인식 ===")
    for k, v in sorted(bridge.items()):
        lines.append(f"  {k:<24} {v}")
    lines.append("")
    lines.append(f"=== 새로 닫히는 칸 = {len(fixes)} ===")
    lines.extend("  " + s for s in fixes)
    lines.append("")
    lines.append(f"=== 새로 깨지는 칸 = {len(breaks)} ===")
    lines.extend("  " + s for s in breaks)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
