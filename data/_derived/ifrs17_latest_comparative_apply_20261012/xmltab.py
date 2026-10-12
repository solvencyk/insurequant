"""Independent raw-XML table reader used ONLY for the direct-verification evidence of the 2026-10-12 latest-comparative apply.

It does not use any production extractor or scorer: it parses the DART filing XML with lxml (HTML parser, huge_tree) and yields every <TABLE>
with the XML source line of the table and of every row, the last preceding <P> text (caption candidates), the unit text seen before the table
and the printed cell strings.  Matching is done by the caller on PRINTED tokens (never on parsed numbers produced by the pipeline).
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parents[3]
DART = ROOT / "data" / "dart"

NUM_RE = re.compile(r"^\(?-?\d[\d,]*(\.\d+)?\)?$")


@dataclass
class Row:
    cells: list[str]
    line: int


@dataclass
class Table:
    index: int
    line: int
    caption: str
    captions: list[str]          # the last few <P> texts before the table (closest last)
    unit: str                    # "(단위 : ...)" text seen closest before the table
    rows: list[Row] = field(default_factory=list)


def _text(el) -> str:
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


def printed_to_float(s: str):
    """'(1,234)' -> -1234.0 ; '-' / '' -> None ; '1,234.5' -> 1234.5"""
    t = s.strip().replace("\xa0", "").replace(" ", "")
    if t in ("", "-", "–", "—"):
        return None
    neg = t.startswith("(") and t.endswith(")")
    t2 = t.strip("()").replace(",", "")
    if t2.startswith("△") or t2.startswith("▲"):
        neg, t2 = True, t2[1:]
    try:
        v = float(t2)
    except ValueError:
        return None
    return -v if neg else v


@lru_cache(maxsize=16)
def load_tables(xml_path: str) -> tuple:
    parser = etree.HTMLParser(encoding="utf-8", huge_tree=True, recover=True)
    tree = etree.parse(str(xml_path), parser)
    root = tree.getroot()
    out: list[Table] = []
    last_p: list[str] = []
    unit = ""
    idx = 0
    for el in root.iter():
        if not isinstance(el.tag, str):
            continue
        tag = el.tag.lower()
        if tag == "p":
            t = _text(el)
            if not t:
                continue
            if "단위" in t and len(t) < 60:
                unit = t
            last_p.append(t)
            last_p = last_p[-6:]
        elif tag == "table":
            rows = []
            for tr in el.iter():
                if (tr.tag or "").lower() != "tr":
                    continue
                cells = [_text(c) for c in tr if (c.tag or "").lower() in ("th", "td", "te")]
                if cells:
                    rows.append(Row(cells, getattr(tr, "sourceline", 0) or 0))
            if not rows:
                continue
            tb = Table(index=idx, line=getattr(el, "sourceline", 0) or 0, caption=last_p[-1] if last_p else "",
                       captions=list(last_p), unit=unit, rows=rows)
            # tables that carry the unit inside the first row
            for r in rows[:2]:
                for c in r.cells:
                    if "단위" in c and len(c) < 40:
                        tb.unit = c
            out.append(tb)
            idx += 1
    return tuple(out)


def find_xml(kr: str, fy_q: str) -> list[Path]:
    """Main filing XML(s) of a company in data/dart/FY####_Q#/raw/KR####_*/ (largest first)."""
    base = DART / fy_q / "raw"
    res = []
    for d in sorted(base.glob(f"{kr}_*")):
        xs = sorted(d.glob("**/*.xml"), key=lambda p: p.stat().st_size, reverse=True)
        res.extend(xs)
    return res


def tokens_equal(printed: str, value: float, scale: float, tol: float = 0.51) -> bool:
    """True if the printed token (in the filing's unit) equals `value` (in master unit) when multiplied by `scale`
    (filing-unit amount per master-unit) within `tol` filing units (default: rounding of the last printed digit)."""
    v = printed_to_float(printed)
    if v is None:
        return False
    return abs(v - value * scale) <= tol


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    p = Path(sys.argv[1])
    ts = load_tables(str(p))
    print(len(ts), "tables")
    pat = re.compile(sys.argv[2]) if len(sys.argv) > 2 else None
    for t in ts:
        if pat and not (pat.search(t.caption) or any(pat.search(c) for c in t.captions)):
            continue
        print(f"--- table #{t.index} line {t.line} unit={t.unit!r} caption={t.caption[:90]!r}")
        for r in t.rows[:int(sys.argv[3]) if len(sys.argv) > 3 else 6]:
            print("   L%-6d" % r.line, r.cells[:8])
