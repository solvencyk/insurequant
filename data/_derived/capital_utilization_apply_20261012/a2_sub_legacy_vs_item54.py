"""a2: '(기발행 후순위채무)' item54 vs the bond ledger's subordinated rows by issue date (read-only).

Why: the memo's R-rule pre-check only re-reads item54 as 'new debt mislabelled' when the ledger has NO pre-2023
subordinated debt at all (DB생명·미래에셋). This dump measures, for every company with item54 > 0 in 2026.2Q,
how item54 compares with the ledger's pre-2023 and 2023+ subordinated balances, and lists each subordinated bond.

Run (repo root):
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_utilization_apply_20261012/a2_sub_legacy_vs_item54.py
Output: a2_sub_legacy_vs_item54.txt (same folder)
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
Q = "2026.2Q"


def f(v):
    try:
        return float(str(v).replace(",", "").replace("△", "-"))
    except (TypeError, ValueError):
        return None


def main() -> int:
    kics = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
    it: dict[str, dict] = {}
    for r in kics:
        if r.get("공시분기") == Q and r.get("항목번호") in (47, 53, 54):
            e = it.setdefault(r["원보험사코드"], {"name": r.get("원수사명")})
            e[r["항목번호"]] = (f(r.get("값")), f(r.get("값_적용후")))
    cs = json.loads((REPO / "kics_capital_securities.json").read_text(encoding="utf-8"))
    subs: dict[str, list] = {}
    for r in cs["rows"]:
        if r.get("종류") != "신종자본증권":
            subs.setdefault(r["원보험사코드"], []).append(r)
    out = ["code name | item54(pre) | ledger sub <2023 | ledger sub 2023+ | item54 - legacy | verdict"]
    for code in sorted(it):
        e = it[code]
        i54 = (e.get(54) or (None, None))[0]
        if not i54 or i54 <= 2:
            continue
        rows = subs.get(code, [])
        leg = sum((r.get("잔액_억") or 0) for r in rows if (r.get("발행일") or "") < "2023-01-01")
        new = sum((r.get("잔액_억") or 0) for r in rows if (r.get("발행일") or "") >= "2023-01-01")
        gap = i54 - leg
        verdict = "item54 <= ledger legacy (+2 tol)" if gap <= 2 else (
            "ledger has NO legacy sub -> printed row = new debt (memo rule)" if leg <= 2 else
            "item54 EXCEEDS ledger legacy -> row likely includes 2023+ debt or ledger dates/balances differ")
        out.append(f"{code} {str(e['name'])[:10]:10s} | {i54:,.2f} | {leg:,.2f} | {new:,.2f} | {gap:+,.2f} | {verdict}")
        for r in sorted(rows, key=lambda x: x.get("발행일") or ""):
            out.append(f"      {r.get('발행일')} bal={r.get('잔액_억')} face={r.get('액면가_억')} call={r.get('콜만기도래일')} "
                       f"mat={r.get('법정만기일')} 경과조치={r.get('경과조치')} 보완인정={r.get('보완자본인정액_억')} | {r.get('구분')}")
    txt = "\n".join(out) + "\n"
    (HERE / "a2_sub_legacy_vs_item54.txt").write_text(txt, encoding="utf-8")
    print(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
