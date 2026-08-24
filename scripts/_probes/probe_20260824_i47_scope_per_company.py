"""item47(보완자본 한도 적용 전)의 **스코프**가 회사별로 갈리는지 전수 판정.

두 읽기:
  EXCL : item47 은 채무성 자본만. 보완자본 = min(i47, i48) + i49          [현행 CAPPED/UNCAPPED]
  INCL : item47 이 item49(해약환급금 초과분)를 포함. 보완자본 = min(i47 - i49, i48) + i49

회사별로 어느 읽기가 자기 분기 전부를 재현하는지 센다. 갈리면 스코프는 회사 속성이고,
안 갈리면 내 KR0068 읽기가 틀린 것이다. (적용전 컬럼만 본다 — 적용후는 경과조치가 섞인다.)
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.solvency.validation.kics_json_rules import (  # noqa: E402
    KEY_CODE, KEY_NAME, KEY_ITEM, KEY_QUARTER, KEY_VALUE, TIER2_ZERO_EPS,
)

OUT = ROOT / "artifacts" / "validation" / "probe_20260824_i47_scope.txt"
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


def main():
    rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    buckets: dict[tuple[str, str], dict] = {}
    for r in rows:
        code, q = r.get(KEY_CODE), r.get(KEY_QUARTER)
        if not code or not q:
            continue
        b = buckets.setdefault((code, q), {"name": r.get(KEY_NAME), "v": {}})
        try:
            it = int(r.get(KEY_ITEM))
        except (TypeError, ValueError):
            continue
        v = num(r.get(KEY_VALUE))
        if v is not None:
            b["v"][it] = v

    per: dict[str, dict] = defaultdict(
        lambda: {"name": "", "n": 0, "excl": 0, "incl": 0, "both": 0, "neither": 0,
                 "bind_excl": 0, "bind_incl": 0, "q": []})
    for (code, q), b in sorted(buckets.items()):
        v = b["v"]
        i3, i47, i48, i49 = v.get(3), v.get(47), v.get(48), v.get(49)
        if None in (i3, i47, i48, i49):
            continue
        if max(abs(i47), abs(i48), abs(i49)) <= TIER2_ZERO_EPS:
            continue
        e_ok = abs(i3 - (min(i47, i48) + i49)) <= TOL or abs(i3 - i47) <= TOL
        i_ok = abs(i3 - (min(i47 - i49, i48) + i49)) <= TOL
        p = per[code]
        p["name"] = b["name"]
        p["n"] += 1
        if e_ok and i_ok:
            p["both"] += 1
        elif e_ok:
            p["excl"] += 1
        elif i_ok:
            p["incl"] += 1
        else:
            p["neither"] += 1
        if i47 - i48 > TOL:
            p["bind_excl"] += 1
        if (i47 - i49) - i48 > TOL:
            p["bind_incl"] += 1
        p["q"].append((q, i3, i47, i48, i49, e_ok, i_ok))

    lines = ["=== item47 스코프 회사별 판정 (적용전 컬럼, TFI_NA 제외) ===",
             "EXCL=현행 읽기만 성립 · INCL=해약환급금 포함 읽기만 성립 · BOTH=둘 다 · NEITHER=둘 다 실패",
             "",
             f"{'code':<7}{'name':<14}{'n':>4}{'EXCL':>6}{'INCL':>6}{'BOTH':>6}{'NEITHER':>8}"
             f"{'bind_E':>8}{'bind_I':>8}  verdict"]
    tot = defaultdict(int)
    for code, p in sorted(per.items()):
        if p["incl"] > 0 and p["excl"] == 0:
            verdict = "INCL-only"
        elif p["excl"] > 0 and p["incl"] == 0:
            verdict = "EXCL-only"
        elif p["excl"] and p["incl"]:
            verdict = "MIXED(!!)"
        else:
            verdict = "ambiguous(BOTH/NEITHER only)"
        tot[verdict] += 1
        lines.append(
            f"{code:<7}{str(p['name'])[:13]:<14}{p['n']:>4}{p['excl']:>6}{p['incl']:>6}"
            f"{p['both']:>6}{p['neither']:>8}{p['bind_excl']:>8}{p['bind_incl']:>8}  {verdict}")
    lines.append("")
    lines.append("=== verdict 집계 ===")
    for k, n in sorted(tot.items()):
        lines.append(f"  {k:<32} {n} 사")

    lines.append("")
    lines.append("=== INCL-only / MIXED 회사 분기 상세 ===")
    for code, p in sorted(per.items()):
        if not (p["incl"] > 0):
            continue
        lines.append(f"-- {code} {p['name']}")
        for (q, i3, i47, i48, i49, e_ok, i_ok) in p["q"]:
            lines.append(
                f"   {q:<8} i3={i3:>12,.2f} i47={i47:>12,.2f} i48={i48:>12,.2f} "
                f"i49={i49:>12,.2f}  i47-i49={i47 - i49:>12,.2f}  "
                f"EXCL={'Y' if e_ok else 'n'} INCL={'Y' if i_ok else 'n'}  "
                f"excess_INCL={max(0.0, (i47 - i49) - i48):>10,.2f}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
