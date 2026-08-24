# -*- coding: utf-8 -*-
"""Read-only: cross-quarter identity sweep for KR0003 / KR0004 + pin-vs-live check.

Tests, for EVERY quarter of the two issuers (not just the exempted ones):
  A  bridge      : item2  == item4 - item12 - item13            (한도초과 = 0 for both issuers)
  B  composition : item3  == min(47,48) + 49   /  INCL: min(47-49,48)+49
  C  tfi split   : item52 == item50 + item51
  D  tfi comp    : item51 == min(47,48) + 49
  E  sub-debt id : item3  == item13 + item54     (보완자본 = 재분류 + 후순위채무)
  F  limit       : item48 == item14 * 0.5
Then compares every ledger pin against the live rule output.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

CODES = ("KR0003", "KR0004")
SCOPE = {"KR0003": "EXCL", "KR0004": "INCL"}


def f(v):
    if v is None or v == "":
        return None
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


def main() -> None:
    rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    grid: dict[tuple[str, str], dict[int, dict]] = {}
    for r in rows:
        c = r.get("원보험사코드")
        if c not in CODES:
            continue
        try:
            it = int(r.get("항목번호"))
        except (TypeError, ValueError):
            continue
        grid.setdefault((c, r.get("공시분기")), {})[it] = r

    def g(k, it, post=False):
        r = grid.get(k, {}).get(it)
        return None if r is None else f(r.get("값_적용후" if post else "값"))

    print("=" * 118)
    print("IDENTITY SWEEP  (blank = an input is missing; residual = actual - expected)")
    print("=" * 118)
    hdr = (f"{'bucket':<18}{'A bridge':>11}{'B comp':>11}{'C split':>11}"
           f"{'D tfiComp':>11}{'E i13+i54':>11}{'F limit':>11}")
    for c in CODES:
        print(f"\n--- {c}  (item47 scope = {SCOPE[c]}) ---")
        print(hdr)
        for k in sorted(x for x in grid if x[0] == c):
            i2, i3, i4, i12, i13, i14 = (g(k, n) for n in (2, 3, 4, 12, 13, 14))
            i47, i48, i49, i50, i51, i52, i54 = (g(k, n) for n in (47, 48, 49, 50, 51, 52, 54))

            def show(x):
                return "     ." if x is None else f"{x:>10.2f}"

            a = None if None in (i2, i4, i12, i13) else i2 - (i4 - i12 - i13)
            if None in (i3, i47, i48, i49):
                b = None
            else:
                debt = i47 - i49 if SCOPE[c] == "INCL" else i47
                b = i3 - (min(debt, i48) + i49)
            cc = None if None in (i50, i51, i52) else i52 - (i50 + i51)
            if None in (i51, i47, i48, i49):
                d = None
            else:
                debt = i47 - i49 if SCOPE[c] == "INCL" else i47
                d = i51 - (min(debt, i48) + i49)
            e = None if None in (i3, i13, i54) else i3 - (i13 + i54)
            ff = None if None in (i48, i14) else i48 - i14 * 0.5
            print(f"{k[1]:<18}{show(a)}{show(b)}{show(cc)}{show(d)}{show(e)}{show(ff)}")

    # ---- missing-cell census for the TFI block ----
    print("\n" + "=" * 118)
    print("TFI BLOCK MISSING-CELL CENSUS (items 47-54, 값 / 값_적용후)")
    print("=" * 118)
    for c in CODES:
        for k in sorted(x for x in grid if x[0] == c):
            miss_pre = [n for n in range(47, 55) if g(k, n) is None]
            miss_post = [n for n in range(47, 55) if g(k, n, post=True) is None]
            if miss_pre or miss_post:
                print(f"  {k[0]} {k[1]:<10} 값 결측={miss_pre}   값_적용후 결측={miss_post}")

    # ---- pins vs live ----
    print("\n" + "=" * 118)
    print("LEDGER PIN vs LIVE RULE OUTPUT")
    print("=" * 118)
    from src.solvency.validation.kics_json_rules import run_validation
    from validate_kics_disclosure import _load_tfi_applicability

    res = run_validation(rows, tfi_applicability=_load_tfi_applicability())
    findings = res["findings"] if isinstance(res, dict) else res
    live = {(x["원보험사코드"], x["공시분기"], x["rule"]): (x["status"], x.get("diff"))
            for x in findings}

    ledger = json.loads((ROOT / "data" / "_gold" / "kics_exemption_provenance.json")
                        .read_text(encoding="utf-8"))
    for e in ledger["entries"]:
        if e.get("company") not in CODES or e.get("registry") != "_TIER2_ISSUER_INCONSISTENT":
            continue
        q = e["quarter"]
        print(f"\n  {e['company']} {q}  status={e.get('status')}  tol={e.get('pin_tolerance')}")
        for pin, val in (e.get("expected_residual") or {}).items():
            rule = pin.split("|")[0]
            col = pin.split("|")[1] if "|" in pin else ""
            key = (e["company"], q, rule if col != "적용후" or rule.endswith("_post")
                   else rule + "_post")
            st, dv = live.get(key, ("<no finding>", None))
            if val is None:
                ok = "OK(non-numeric pin)" if st == "RED" else f"!! status={st}"
                print(f"      {pin:<40} pin=None        live={st:<8} diff={dv}   {ok}")
            else:
                delta = None if dv is None else abs(dv - val)
                ok = "OK" if (delta is not None and delta <= (e.get("pin_tolerance") or 0.01)) \
                    else "!! DRIFT"
                print(f"      {pin:<40} pin={val:<12} live={st:<8} diff={dv}   Δ={delta}  {ok}")


if __name__ == "__main__":
    main()
