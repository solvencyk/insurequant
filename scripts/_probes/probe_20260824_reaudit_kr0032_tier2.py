# -*- coding: utf-8 -*-
"""Read-only: KR0032 tier2 composition + tier1 bridge, every quarter, BOTH columns.

Tests the three competing readings of item47 (보완자본 한도 적용 전):
  A  EXCL  : 보완자본 == min(47, 48) + 49              (current rule)
  B  INCL  : 보완자본 == min(47 - 49, 48) + 49         (the 2026-08-24 한화생명 fix)
  C  +SUB  : 보완자본 == min(47 + 54, 48) + 49         (the registry's 'second reading')

If C were this issuer's convention it must hold in the issuer's OTHER quarters too;
a per-company scope vote is exactly what rescued KR0068. Also reports the tier1 bridge.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "validation" / "reaudit_20260824_kr0032_tier2.txt"
K_CODE, K_NO, K_Q, K_V, K_VA = "원보험사코드", "항목번호", "공시분기", "값", "값_적용후"

recs = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
b = {}
for r in recs:
    if r[K_CODE] == "KR0032":
        b.setdefault(r[K_Q], {})[r[K_NO]] = (r.get(K_V), r.get(K_VA))


def num(x):
    if x is None:
        return None
    try:
        return float(str(x).replace(",", ""))
    except ValueError:
        return None


buf = ["KR0032 NH농협손해보험 — tier2 composition, three readings of item47", ""]
for col_idx, col in ((0, "값 (적용전)"), (1, "값_적용후")):
    buf.append("=" * 118)
    buf.append("COLUMN %s" % col)
    buf.append("%-9s %10s %10s %10s %10s %10s | %11s %11s %11s"
               % ("quarter", "i3보완자본", "i47", "i48한도", "i49", "i54후순위",
                  "A resid", "B resid", "C resid"))
    for q in sorted(b):
        d = b[q]

        def g(n):
            return num(d.get(n, (None, None))[col_idx])

        # tier2 target: prefer the TFI 보완자본 row (item51); fall back to headline item3
        tgt = g(51) if g(51) is not None else g(3)
        i47, i48, i49, i54 = g(47), g(48), g(49), g(54)
        if tgt is None or i47 is None or i48 is None or i49 is None:
            buf.append("%-9s %10s  (inputs missing: %s)"
                       % (q, "-" if tgt is None else "%.2f" % tgt,
                          [n for n in (51, 47, 48, 49) if g(n) is None]))
            continue
        a = tgt - (min(i47, i48) + i49)
        bb = tgt - (min(i47 - i49, i48) + i49)
        cc = (tgt - (min(i47 + i54, i48) + i49)) if i54 is not None else None
        buf.append("%-9s %10.2f %10.2f %10.2f %10.2f %10s | %11.2f %11.2f %11s"
                   % (q, tgt, i47, i48, i49,
                      "-" if i54 is None else "%.2f" % i54,
                      a, bb, "-" if cc is None else "%.2f" % cc))
    buf.append("")

buf.append("=" * 118)
buf.append("READING SCORECARD (|resid| <= 2.0 counts as closing)")
for col_idx, col in ((0, "값 (적용전)"), (1, "값_적용후")):
    score = {"A": 0, "B": 0, "C": 0, "n": 0}
    for q in sorted(b):
        d = b[q]

        def g(n):
            return num(d.get(n, (None, None))[col_idx])

        tgt = g(51) if g(51) is not None else g(3)
        i47, i48, i49, i54 = g(47), g(48), g(49), g(54)
        if tgt is None or None in (i47, i48, i49):
            continue
        score["n"] += 1
        if abs(tgt - (min(i47, i48) + i49)) <= 2.0:
            score["A"] += 1
        if abs(tgt - (min(i47 - i49, i48) + i49)) <= 2.0:
            score["B"] += 1
        if i54 is not None and abs(tgt - (min(i47 + i54, i48) + i49)) <= 2.0:
            score["C"] += 1
    buf.append("  %-12s buckets=%d   A(EXCL current)=%d   B(INCL hanwha-fix)=%d   C(+item54)=%d"
               % (col, score["n"], score["A"], score["B"], score["C"]))
buf.append("")

buf.append("=" * 118)
buf.append("TIER1 BRIDGE  item2 =?= item4 - (item12 - excess) - item13, excess = max(0, i47-i48)")
buf.append("%-9s %10s %10s %10s %10s %10s %11s"
           % ("quarter", "i2기본자본", "i4순자산", "i12불인정", "i13재분류", "excess", "resid"))
for q in sorted(b):
    d = b[q]

    def g(n):
        return num(d.get(n, (None, None))[0])

    i2, i4, i12, i13, i47, i48 = g(2), g(4), g(12), g(13), g(47), g(48)
    if None in (i2, i4, i13):
        buf.append("%-9s  inputs missing" % q)
        continue
    i12 = 0.0 if i12 is None else i12
    exc = max(0.0, (i47 or 0.0) - (i48 or 0.0))
    exc = min(exc, i12)
    exp = i4 - (i12 - exc) - i13
    buf.append("%-9s %10.2f %10.2f %10.2f %10.2f %10.2f %11.2f"
               % (q, i2, i4, i12, i13, exc, i2 - exp))
buf.append("")
buf.append("counterfactual for 2024.3Q using the Ⅲ재분류 figure the ISSUER ITSELF restated")
buf.append("in its next filing (FY2024_Q4 raw p43, 2024년 3분기 column: 9,390 not 8,867):")
d = b["2024.3Q"]
i2 = num(d[2][0]); i4 = num(d[4][0]); i13 = num(d[13][0])
buf.append("   as filed 2024.3Q : %.0f - 0 - %.0f = %.0f   vs 기본자본 %.0f  -> resid %+.0f"
           % (i4, i13, i4 - i13, i2, i2 - (i4 - i13)))
buf.append("   restated (9,390) : %.0f - 0 - 9390 = %.0f   vs 기본자본 %.0f  -> resid %+.0f"
           % (i4, i4 - 9390, i2, i2 - (i4 - 9390)))
i47 = num(d[47][0]); i49 = num(d[49][0]); i54 = num(d[54][0])
buf.append("   and the restated 9,390 is reproduced by i49 + (i47 - i54) = %.2f + (%.2f - %.2f)"
           " = %.2f" % (i49, i47, i54, i49 + i47 - i54))
buf.append("")
buf.append("same relation Ⅲ재분류 =?= i49 + (i47 - i54) on every KR0032 quarter:")
for q in sorted(b):
    d = b[q]
    i13 = num(d.get(13, (None,))[0]) if 13 in d else None
    i47 = num(d.get(47, (None,))[0]) if 47 in d else None
    i49 = num(d.get(49, (None,))[0]) if 49 in d else None
    i54 = num(d.get(54, (None,))[0]) if 54 in d else None
    if None in (i13, i47, i49, i54):
        buf.append("   %-9s inputs missing" % q)
        continue
    pred = i49 + (i47 - i54)
    buf.append("   %-9s Ⅲ재분류=%9.2f   i49+(i47-i54)=%9.2f   diff=%+9.2f"
               % (q, i13, pred, i13 - pred))

OUT.write_text("\n".join(buf), encoding="utf-8")
print("wrote", OUT)
