"""a11: owner-decision support (read-only) - companies whose printed '(기발행 후순위채무)' item54 EXCEEDS the bond
ledger's pre-2023 subordinated balance (a2), with the tier2 value if only the ledger-legacy part were exempt.

The adopted memo rule (decision ②) re-reads item54 as new debt only when the ledger has NO pre-2023 subordinated
debt (DB생명·미래에셋). a3 shows 메리츠 and 흥국생명 print post-2023 issues into the same row as well (item54
jumps by the issue amount in the issue quarter). This prints, per company, deployed value vs the value with
exempt = min(item54, ledger legacy balance). Nothing is written to the masters.

Run (repo root):
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_utilization_apply_20261012/a11_legacy_row_overreach_alt.py
Output: a11_legacy_row_overreach_alt.txt (same folder)
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "scripts"))
import capital_utilization_rules as R  # noqa: E402

Q = "2026.2Q"


def main() -> int:
    records = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
    ledger = R.load_ledger()
    pre, post, names = R.load_disclosure(records, Q)
    t2 = {r["code"]: r for r in json.loads((REPO / "kics_tier2_utilization.json").read_text(encoding="utf-8"))["results"]}
    out = ["code name | item54 | ledger legacy sub | excess | deployed rule/num/pct | alt num/pct (exempt = ledger legacy)"]
    for code in sorted(pre):
        i54 = pre[code].get(54) or 0.0
        leg = (ledger.get(code) or {}).get("sub_legacy") or 0.0
        if i54 <= R.TOL or leg <= R.TOL or i54 - leg <= R.TOL:
            continue
        row = t2[code]
        excess = i54 - leg
        alt = None if row.get("numerator_eok") is None else round(row["numerator_eok"] + excess, 2)
        alt_pct = R.pct(alt, row.get("tier2_limit_eok"))
        out.append(f"{code} {str(names.get(code))[:10]:10s} | {i54:,.2f} | {leg:,.2f} | {excess:+,.2f} | "
                   f"{row.get('rule')} {row.get('numerator_eok')} {row.get('utilization_pct')}% | {alt} {alt_pct}%")
    txt = "\n".join(out) + "\n"
    (HERE / "a11_legacy_row_overreach_alt.txt").write_text(txt, encoding="utf-8")
    print(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
