"""KR0079 -- direct header-row comparison between the 2026.2Q ACT (rollforward) table
(known-good, production-verified) and the 2025.4Q attachment ACT candidates, to settle
whether the LRC_no-loss-component/LIC column order is genuinely reversed in the attachment
XML, or whether this is just a THEAD-vs-inferred-header artifact. Read-only.

inbox/parser/20260829T1800Z step 1: "열 위치가 정말 반대인지 확정해라. 헤더 행을 직접 읽어서
다른 분기와 대조해라."
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _tag_basis, _prefer_ofs, _iter_tables_by_basis  # noqa: E402
from scripts.pl_breakdown.companies import _MA_ACT4_ROW, _MA_EXP4_ROW  # noqa: E402
from scripts.pl_breakdown.tier1 import _header_blob  # noqa: E402


def dump_table_full(t, label):
    print(f"\n{'='*100}\n{label}  (line={t.line_no})")
    print(f"caption={t.caption!r}")
    print(f"header rows ({len(t.header)}):")
    for hr in t.header:
        print(f"  {hr}")
    print(f"first 3 body rows:")
    for r in t.rows[:3]:
        print(f"  {r}")


# ---- 2026.2Q known-good (single main xml, no attachment split) ----
XML_GOOD = ROOT / "data/dart/FY2026_Q2/raw/KR0079_미래에셋생명/20260814004054.xml"
tables_good = list(_iter_tables_with_context(XML_GOOD))
t_act_good = next(t for t in tables_good if t.line_no == 43595)
t_exp_good = next(t for t in tables_good if t.line_no == 48560)
dump_table_full(t_act_good, "2026.2Q ACT (rollforward, KNOWN GOOD, main xml)")
dump_table_full(t_exp_good, "2026.2Q EXP (P&L note, KNOWN GOOD, main xml)")

# ---- 2025.4Q attachment candidates ----
D = ROOT / "data/dart/FY2025_Q4/raw/KR0079_미래에셋생명_20260318001664"
from scripts.build_pl_breakdown import _xmls_in  # noqa: E402
xmls = _xmls_in(str(D))
tables_bad = []
per_file_counts = {}
for x in xmls:
    ts = _tag_basis(list(_iter_tables_by_basis(Path(x), _iter_tables_with_context)), x)
    per_file_counts[Path(x).name] = len(ts)
    tables_bad.extend(ts)
print(f"\nper-file table counts: {per_file_counts}")
ofs_bad = _prefer_ofs(tables_bad)

act_cands = [t for t in ofs_bad
             if "사망보험" in _header_blob(t) and "건강보험" in _header_blob(t)
             and any(_MA_ACT4_ROW in "".join(r[:2]) for r in t.rows)]
exp_cands = [t for t in ofs_bad
             if "사망보험" in _header_blob(t) and "건강보험" in _header_blob(t)
             and any(_MA_ACT4_ROW not in "".join(r[:2]) and _MA_EXP4_ROW.split("에")[0][:10] in "".join(r[:2]) for r in t.rows)]

for i, t in enumerate(act_cands):
    dump_table_full(t, f"2025.4Q ACT candidate #{i} (attachment)")

# ---- also dump which source file each 2025.4Q candidate physically came from ----
print(f"\n{'='*100}\nsource-file attribution (which of the 3 xml files each ACT candidate's table object came from):")
for i, t in enumerate(act_cands):
    # re-derive by checking membership in tables_bad per file
    for x in xmls:
        ts = _tag_basis(list(_iter_tables_by_basis(Path(x), _iter_tables_with_context)), x)
        if t in ts:
            print(f"  ACT#{i}: {Path(x).name}")
