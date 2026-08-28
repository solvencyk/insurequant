"""Direct row-by-row comparison of the ACT4 row ('발생한 보험금 및 기타 보험서비스비용') and
its neighbours, between 2026.2Q (known good, gate-verified production value) and 2025.4Q
(the anomaly). Prints EVERY row of both tables with an explicit column-triple grouping so the
LRC_손실요소외/손실요소/LIC column position can be read off directly, not inferred. Read-only.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _tag_basis, _prefer_ofs, _iter_tables_by_basis  # noqa: E402
from scripts.pl_breakdown.companies import _MA_ACT4_ROW  # noqa: E402
from scripts.pl_breakdown.tier1 import _header_blob  # noqa: E402


def show(t, label):
    print(f"\n{'='*100}\n{label} (line={t.line_no}, n_rows={len(t.rows)})")
    for r in t.rows:
        lab = r[0] if r else ""
        lab2 = r[1] if len(r) > 1 else ""
        vals = r[2:] if len(lab2) > 0 and any(c.strip() for c in r[2:3]) else r[1:]
        # print raw + grouped-by-3 view
        print(f"  [{lab!r} | {lab2!r}]")
        data = r[2:]
        groups = [data[i:i+3] for i in range(0, len(data), 3)]
        print(f"    triples: {groups}")


XML_GOOD = ROOT / "data/dart/FY2026_Q2/raw/KR0079_미래에셋생명/20260814004054.xml"
tables_good = list(_iter_tables_with_context(XML_GOOD))
t_act_good = next(t for t in tables_good if t.line_no == 43595)
show(t_act_good, "2026.2Q ACT table (KNOWN GOOD, production-verified item6=-18120.139965)")

D = ROOT / "data/dart/FY2025_Q4/raw/KR0079_미래에셋생명_20260318001664"
from scripts.build_pl_breakdown import _xmls_in  # noqa: E402
xmls = _xmls_in(str(D))
tables_bad = []
for x in xmls:
    tables_bad.extend(_tag_basis(list(_iter_tables_by_basis(Path(x), _iter_tables_with_context)), x))
ofs_bad = _prefer_ofs(tables_bad)
act_cands = [t for t in ofs_bad
             if "사망보험" in _header_blob(t) and "건강보험" in _header_blob(t)
             and any(_MA_ACT4_ROW in "".join(r[:2]) for r in t.rows)]
for i, t in enumerate(act_cands):
    show(t, f"2025.4Q ACT candidate #{i} (anomaly)")
