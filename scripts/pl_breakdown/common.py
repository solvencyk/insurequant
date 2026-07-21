"""Label, number and quarter helpers shared across the PL extractor."""
# Split out of scripts/build_pl_breakdown.py on 2026-07-21. Behaviour unchanged;
# the golden gate (tests/test_pl_breakdown_golden.py) pins the builder output.
import re

from scripts.build_net_income_breakdown import to_num


def _norm(s):
    return (s or "").replace("　", "").replace("\xa0", " ").strip()


def _label(r, i=0):
    return _norm(r[i]) if len(r) > i else ""


def _row_nums(r):
    """Numeric cells of a row, in document order ('-'/blank skipped)."""
    out = []
    for c in r:
        v = to_num(c)
        if v is not None:
            out.append(v)
    return out


def _quarter_from_path(p):
    m = re.search(r"FY(\d{4})_Q(\d)", str(p))
    return f"{m.group(1)}.{m.group(2)}Q" if m else None


def _quarter_sort_key(q):
    m = re.match(r"(\d{4})\.(\d)Q", q)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)
