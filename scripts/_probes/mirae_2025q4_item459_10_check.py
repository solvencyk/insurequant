"""Check whether item4/5/9/10's source table (CSM/RA 구성요소별 조정내역 note, Era-1
"단위:백만원" per-product format, extract_tier2_miraeasset()) is ALSO duplicated with a
shift defect somewhere else in this filing, the way the 18-1 rollforward note is. If the
production code's matched table (first one satisfying the cue) is the SHIFTED copy, item4/5/
9/10 for 2025.4Q could be silently wrong even though they're currently non-zero/populated.
Read-only.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.pl_breakdown.common import _tag_basis, _prefer_ofs, _iter_tables_by_basis, to_num  # noqa: E402
from scripts.pl_breakdown.companies import _MA_CSM_KEYS, _MA_RA_KEYS, _ma_block_val  # noqa: E402
from scripts.build_pl_breakdown import _xmls_in  # noqa: E402

D = ROOT / "data/dart/FY2025_Q4/raw/KR0079_미래에셋생명_20260318001664"
xmls = _xmls_in(str(D))
tables = []
for x in xmls:
    tables.extend(_tag_basis(list(_iter_tables_by_basis(Path(x), _iter_tables_with_context)), x))
ofs_tables = _prefer_ofs(tables)
print(f"total tables (all 3 files, all bases): {len(tables)}  ofs-only: {len(ofs_tables)}")


def hb(t):
    return " ".join(" ".join(h) for h in t.header).replace(" ", "")


def has_amort(t):
    flat = " ".join(
        (r[0] if r else "") + (r[1] if len(r) > 1 else "") for r in t.rows
    ).replace(" ", "")
    return any(k in flat for k in _MA_CSM_KEYS)


# reproduce the EXACT Era-1 matching loop from extract_tier2_miraeasset, but instrument it
# to show ALL matches (not just the accumulated result) with their table identity + which
# basis-tag + fingerprint, to spot duplicates.
matches = []
for t in ofs_tables:
    h = hb(t)
    if "단위:백만원" not in h or not has_amort(t):
        continue
    is_recost = "재보험서비스비용" in h
    is_rev = ("보험수익" in h) and not is_recost
    if not (is_rev or is_recost):
        continue
    fp = tuple(to_num(c) for r in t.rows for c in r if to_num(c) is not None)
    matches.append((t, is_recost, fp))

print(f"\nEra-1 matches (단위:백만원 + CSM-key + 보험수익/재보험서비스비용 cue): {len(matches)}")
seen_fp = {}
for i, (t, is_recost, fp) in enumerate(matches):
    dup_of = seen_fp.get(fp)
    seen_fp.setdefault(fp, i)
    kind = "재보험비용" if is_recost else "보험수익"
    c = _ma_block_val(t, _MA_CSM_KEYS, last_only=True)
    a = _ma_block_val(t, _MA_RA_KEYS, last_only=True)
    print(f"  match#{i}: line={t.line_no} kind={kind} caption={t.caption[:40]!r} "
          f"n_rows={len(t.rows)} CSM(last_only)={c} RA(last_only)={a} "
          f"{'DUP of match#'+str(dup_of) if dup_of is not None else '(unique fingerprint)'}")
    if i < 3 or dup_of is not None:
        for r in t.rows:
            lab = (r[0] if r else "")
            if any(k.replace(" ", "") in lab.replace(" ", "") for k in _MA_CSM_KEYS + _MA_RA_KEYS) or "합계" in lab or "계" == lab.strip():
                print(f"      row: {r}")
