"""Read-only: show the 4 Kyobo Tier-2 note tables of a filing, their header, and the numeric cells of the rows the handler reads.

Usage: python probe_picks.py <quarter e.g. 2024.4Q> [<quarter> ...]
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import plib  # noqa: E402

C = plib.C
sys.stdout.reconfigure(encoding="utf-8")
ROWS = {
    "rev": ["당기손익에인식한보험계약마진", "비금융위험에대한위험조정변동", "발생한보험서비스비용"],
    "cost": ["실제보험금", "실제계약유지비용", "실제투자관리비", "보험계약에대한보험비용"],
    "rerev": ["발생재보험금"],
    "recost": ["보험계약마진상각", "위험조정변동", "비금융위험에대한위험조정", "예상재보험금"],
}
for q in sys.argv[1:]:
    tables = plib.parse_tables(plib.raw_dirs(q))
    print("=" * 110)
    print(f"{q}: dirs={[Path(d).name for d in plib.raw_dirs(q)]}  tables={len(tables)}")
    picks = plib.kyobo_picks(tables)
    for k, t in picks.items():
        if t is None:
            print(f"  [{k}] NOT FOUND")
            continue
        hdr = " / ".join("|".join(str(c) for c in row)[:90] for row in (t.header or [])[:3])
        print(f"  [{k}] caption={t.caption[:90]!r} basis={getattr(t, 'basis', None)} start_line={getattr(t, 'line_no', None)}")
        print(f"        header: {hdr[:230]}")
        for r in t.rows:
            lf = C._life_label_flat(r)
            nums = C._row_nums(r)
            for lab in ROWS[k]:
                if lab in lf and nums:
                    print(f"        row {lf[:40]:40s} nums={nums}")
                    break
