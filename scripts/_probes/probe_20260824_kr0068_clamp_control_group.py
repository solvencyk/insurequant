"""KR0068 2025.2Q tier1_bridge 잔차 조사 — §4-1 클램프 대조군 전수.

발주: inbox/validation/20260824T0410Z__validation__KR0068_2025.2Q__tier1_bridge_residual_unexplained.md

목적: 클램프(한도초과 근사치 > item12)가 발동하는 모든 (회사,분기,컬럼)을 전수로 뽑고,
클램프 후 다리가 닫히는 칸과 안 닫히는 칸을 나란히 놓는다. 한화생명이 어느 축에서
다른지 특정하기 위한 대조군.

읽기 전용. 마스터에 쓰지 않는다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.solvency.validation.kics_json_rules import (  # noqa: E402
    KEY_CODE, KEY_NAME, KEY_ITEM, KEY_QUARTER, KEY_VALUE, KEY_VALUE_POST,
    TIER2_ZERO_EPS,
)

OUT = ROOT / "artifacts" / "validation" / "probe_20260824_kr0068_clamp.txt"
TOL = 2.0


def num(x):
    if x is None:
        return None
    s = str(x).strip().replace(",", "")
    if s in ("", "-", "N/A", "None", "nan"):
        return None
    neg = False
    if s.startswith("△") or s.startswith("∆"):
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
        code = r.get(KEY_CODE)
        q = r.get(KEY_QUARTER)
        if not code or not q:
            continue
        b = buckets.setdefault((code, q), {"name": r.get(KEY_NAME), "pre": {}, "post": {}})
        try:
            it = int(r.get(KEY_ITEM))
        except (TypeError, ValueError):
            continue
        pre = num(r.get(KEY_VALUE))
        post = num(r.get(KEY_VALUE_POST))
        if pre is not None:
            b["pre"][it] = pre
        if post is not None:
            b["post"][it] = post
    return buckets


def branch_of(src, v14_pre, target=3):
    i3, i47, i48, i49 = src.get(target), src.get(47), src.get(48), src.get(49)
    if None in (i3, i47, i48, i49):
        return "INPUT_MISSING", None
    capped = abs(i3 - (min(i47, i48) + i49)) <= TOL
    uncapped = abs(i3 - i47) <= TOL
    if capped and uncapped:
        return "BOTH", max(0.0, i47 - i48)
    if capped:
        return "CAPPED", max(0.0, i47 - i48)
    if uncapped:
        return "UNCAPPED", 0.0
    if (max(abs(i47), abs(i48), abs(i49)) <= TIER2_ZERO_EPS
            and v14_pre is not None and abs(v14_pre) > 1.0):
        i13 = src.get(13)
        if i13 is None:
            return "TFI_NA_NO_INPUT", 0.0
        if abs(i3 - i13) <= TOL:
            return "TFI_NA_OK", 0.0
        return "TFI_NA_RED", 0.0
    return "NEITHER", None


def main():
    buckets = load()
    lines = []
    clamp_rows = []
    all_bridge = []
    for (code, q), b in sorted(buckets.items()):
        v14_pre = b["pre"].get(14)
        for post in (False, True):
            src = b["post"] if post else b["pre"]
            col = "적용후" if post else "적용전"
            br, exc = branch_of(src, v14_pre)
            i2, i4, i12, i13 = src.get(2), src.get(4), src.get(12), src.get(13)
            if None in (i2, i4, i12, i13):
                continue
            raw_exc = exc if br in ("CAPPED", "BOTH") else 0.0
            clamped = min(raw_exc, max(0.0, i12))
            exp_clamped = i4 - (i12 - clamped) - i13
            exp_raw = i4 - (i12 - raw_exc) - i13
            diff_clamped = i2 - exp_clamped
            diff_raw = i2 - exp_raw
            rec = dict(code=code, name=b["name"], q=q, col=col, branch=br,
                       i2=i2, i4=i4, i12=i12, i13=i13,
                       i47=src.get(47), i48=src.get(48), i49=src.get(49),
                       i3=src.get(3), i51=src.get(51),
                       raw_exc=raw_exc, clamped=clamped,
                       diff_clamped=diff_clamped, diff_raw=diff_raw)
            all_bridge.append(rec)
            if raw_exc > clamped + 1e-9:
                clamp_rows.append(rec)

    lines.append("=== CLAMP FIRES (raw_exc > item12) — 전수 ===")
    lines.append(f"total clamp cells = {len(clamp_rows)}")
    lines.append("")
    hdr = ("code  name           quarter   col      branch    "
           "item12      raw_exc     ratio  diff_clamped  diff_raw   item47      item48      item49")
    lines.append(hdr)
    for r in clamp_rows:
        ratio = (r["raw_exc"] / r["i12"]) if r["i12"] else float("inf")
        lines.append(
            f"{r['code']} {str(r['name'])[:12]:<14} {r['q']:<9} {r['col']:<8} {r['branch']:<9} "
            f"{r['i12']:>11,.2f} {r['raw_exc']:>11,.2f} {ratio:>6.2f} "
            f"{r['diff_clamped']:>13,.2f} {r['diff_raw']:>10,.2f} "
            f"{(r['i47'] or 0):>11,.2f} {(r['i48'] or 0):>11,.2f} {(r['i49'] or 0):>11,.2f}"
        )

    lines.append("")
    lines.append("=== KR0068 13 quarters full table (item47/48/49/51/3 + bridge) ===")
    lines.append("quarter   col      branch    item3        item47       item48       item49       "
                 "item51       i47-i48      i2          i4           i12         i13         diff")
    for r in all_bridge:
        if r["code"] != "KR0068":
            continue
        gap = (r["i47"] - r["i48"]) if (r["i47"] is not None and r["i48"] is not None) else None
        lines.append(
            f"{r['q']:<9} {r['col']:<8} {r['branch']:<9} "
            f"{(r['i3'] if r['i3'] is not None else float('nan')):>12,.2f} "
            f"{(r['i47'] if r['i47'] is not None else float('nan')):>12,.2f} "
            f"{(r['i48'] if r['i48'] is not None else float('nan')):>12,.2f} "
            f"{(r['i49'] if r['i49'] is not None else float('nan')):>12,.2f} "
            f"{(r['i51'] if r['i51'] is not None else float('nan')):>12,.2f} "
            f"{(gap if gap is not None else float('nan')):>12,.2f} "
            f"{r['i2']:>11,.2f} {r['i4']:>12,.2f} {r['i12']:>11,.2f} {r['i13']:>11,.2f} "
            f"{r['diff_clamped']:>11,.2f}"
        )

    lines.append("")
    lines.append("=== KR0068 all items present, 2025.2Q (pre / post) ===")
    b = buckets.get(("KR0068", "2025.2Q"))
    if b:
        keys = sorted(set(b["pre"]) | set(b["post"]))
        for k in keys:
            lines.append(f"  item{k:<3} pre={b['pre'].get(k)!r:<16} post={b['post'].get(k)!r}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
