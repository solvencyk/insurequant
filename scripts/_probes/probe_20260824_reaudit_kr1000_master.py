"""READ-ONLY. KR1000(코리안리) 면제 재감사용 마스터 셀 덤프.

kics_disclosure.json 에서 한 회사의 tier2/bridge 관련 항목을 분기별로 뽑아
적용전(`값`)·적용후(`값_적용후`) 두 컬럼을 다 인쇄하고, 축 A(`2_tier1_bridge`)·
축 B(`3_tier2_composition`)·축 F(`51_tfi_tier2_composition`) 를 손으로 재계산한다.
마스터는 읽기만 한다.

사용:
  probe_20260824_reaudit_kr1000_master.py [--code KR1000] --out <utf8 파일>
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "kics_disclosure.json"

K_CODE = "원보험사코드"
K_ITEM = "항목번호"
K_NAME = "항목명"
K_Q = "공시분기"
K_PRE = "값"
K_POST = "값_적용후"

ITEMS = [1, 2, 3, 4, 12, 13, 14, 15, 27, 28, 47, 48, 49, 50, 51, 52, 53, 54]


def num(v):
    if v is None:
        return None
    s = str(v).replace(",", "").replace("△", "-").strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def main() -> None:
    out_path = None
    if "--out" in sys.argv:
        out_path = sys.argv[sys.argv.index("--out") + 1]
    code = "KR1000"
    if "--code" in sys.argv:
        code = sys.argv[sys.argv.index("--code") + 1]
    recs = json.load(io.open(MASTER, encoding="utf-8"))
    rows = [r for r in recs if r.get(K_CODE) == code]
    buf: list[str] = ["%s records: %d" % (code, len(rows))]

    labels: dict[int, str] = {}
    for r in rows:
        n = r.get(K_ITEM)
        if n is not None and n not in labels:
            labels[n] = str(r.get(K_NAME) or "")
    buf.append("--- item labels present (%d) ---" % len(labels))
    for n in sorted(labels):
        buf.append("  item%-4s %s" % (n, labels[n]))

    quarters = sorted({r.get(K_Q) for r in rows if r.get(K_Q)})
    buf.append("--- quarters (%d): %s" % (len(quarters), quarters))
    for q in quarters:
        buf.append("=" * 78)
        buf.append("QUARTER %s" % q)
        by_item = {r.get(K_ITEM): r for r in rows if r.get(K_Q) == q}
        for n in ITEMS:
            r = by_item.get(n)
            if r is None:
                buf.append("  item%-3d  ---absent---" % n)
                continue
            buf.append("  item%-3d  pre=%-14s post=%-14s  %s" % (
                n, r.get(K_PRE), r.get(K_POST), str(r.get(K_NAME) or "")[:44]))
        # --- hand recomputation of the three axes, both columns -------------
        for tag, key in (("PRE ", K_PRE), ("POST", K_POST)):
            g = {n: num((by_item.get(n) or {}).get(key)) for n in ITEMS}
            i2, i3, i4, i12, i13 = g[2], g[3], g[4], g[12], g[13]
            i47, i48, i49, i51 = g[47], g[48], g[49], g[51]
            line = ["  [%s]" % tag]
            if None not in (i3, i47, i48, i49):
                exc_excl = min(i47, i48) + i49
                exc_incl = min(i47 - i49, i48) + i49
                line.append(
                    "B: i3=%.2f  min(47,48)+49=%.2f (d=%.2f)  min(47-49,48)+49=%.2f (d=%.2f)  i47=%.2f (d=%.2f)"
                    % (i3, exc_excl, i3 - exc_excl, exc_incl, i3 - exc_incl, i47, i3 - i47))
            if None not in (i51, i47, i48, i49):
                e_excl = min(i47, i48) + i49
                e_incl = min(i47 - i49, i48) + i49
                line.append(
                    "  F: i51=%.2f  min(47,48)+49=%.2f (d=%.2f)  min(47-49,48)+49=%.2f (d=%.2f)  i47=%.2f (d=%.2f)"
                    % (i51, e_excl, i51 - e_excl, e_incl, i51 - e_incl, i47, i51 - i47))
            if None not in (i2, i4, i12, i13):
                raw_excl = max(0.0, i47 - i48) if None not in (i47, i48) else 0.0
                raw_incl = max(0.0, (i47 - i49) - i48) if None not in (i47, i48, i49) else 0.0
                for nm, raw in (("EXCL", raw_excl), ("INCL", raw_incl), ("exc0", 0.0)):
                    exc = min(raw, max(0.0, i12))
                    exp = i4 - (i12 - exc) - i13
                    line.append("  A(%s): exc=%.2f expected=%.2f actual=%.2f diff=%.2f"
                                % (nm, exc, exp, i2, i2 - exp))
            buf.append("\n".join(line))
    text = "\n".join(buf)
    if out_path:
        io.open(out_path, "w", encoding="utf-8").write(text)
        print("written", out_path)
    else:
        print(text)


if __name__ == "__main__":
    main()
