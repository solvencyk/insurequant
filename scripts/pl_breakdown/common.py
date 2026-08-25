"""Label, number and quarter helpers shared across the PL extractor."""
# Split out of scripts/build_pl_breakdown.py on 2026-07-21. Behaviour unchanged;
# the golden gate (tests/test_pl_breakdown_golden.py) pins the builder output.
import os
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


# --------------------------------------------------------------------------- #
# 별도(OFS)/연결(CFS) basis tagging (2026-08-26, inbox/parser/20260825T1415Z
# follow-up).  A DART filing's main body XML embeds BOTH bases (연결 first, 별도
# second -- DART's standard ATOC template: "N. 연결재무제표" / "N+1. 연결재무제표
# 주석" / "N+2. 재무제표" / "N+3. 재무제표 주석"), and 사업보고서 filings ALSO carry
# them as separate _00760.xml(별도)/_00761.xml(연결) audit-report attachments.  A
# handler that scans `tables` for a caption/row match without a basis check will
# silently pick whichever occurrence comes first in the combined list -- which,
# because 연결 precedes 별도 in document order, is 연결 (see 삼성생명/신한라이프
# item4 -- confirmed against raw via XBRL ConsolidatedMember/SeparateMember tags
# and the ATOC line-position split).  These helpers let a handler prefer 별도
# without hardcoding a company code.
_OFS_TITLE_RE = re.compile(r'<TITLE\s+ATOC="Y"[^>]*\bENG="([^"]*)"', re.IGNORECASE)


def _ofs_line_boundary(path):
    """Line number (1-indexed) where the 별도(separate/OFS) financial statements begin in
    a DART filing's main body XML, or None when not determinable.  Only trusted when a
    PRECEDING '...Consolidated financial statements' ATOC marker was also seen (a
    both-basis filing) -- a lone OFS marker, or no ATOC markers at all (older filings,
    pre-2024ish templates), returns None so callers treat basis as unknown rather than
    guessing.  ATOC markers inside note cross-references (prose like '...5.재무제표
    주석...부분을 참고') are excluded via the ATOC="Y"-attribute + ENG-attribute
    requirement -- those only appear on the real TOC-registered section titles."""
    try:
        cfs_seen = False
        with open(path, encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f, 1):
                if 'ATOC="Y"' not in line or "financial statements" not in line.lower():
                    continue
                m = _OFS_TITLE_RE.search(line)
                if not m:
                    continue
                eng = m.group(1).lower()
                if "notes" in eng:
                    continue
                if "consolidated" in eng:
                    cfs_seen = True
                elif ("separate" in eng or "non-consolidated" in eng) and cfs_seen:
                    return i
    except OSError:
        return None
    return None


def _tag_basis(tables, path):
    """Attach `._basis` ('OFS' | 'CFS' | None) to each ExtractedTable in-place (dataclass,
    so a new attribute is safe) based on its source file.  `_00760.xml`/`_00761.xml` are
    DART's single-basis audit-report attachments (별도/연결 respectively); a main-body XML
    is split by `_ofs_line_boundary`.  None ('unknown') means "no ATOC split found in this
    file" -- callers must treat that as "don't filter" so older/simpler filings (where the
    split does not apply, or there is only one basis to begin with) keep their existing
    behaviour instead of losing their only source."""
    name = os.path.basename(str(path))
    if name.endswith("_00760.xml"):
        for t in tables:
            t._basis = "OFS"
        return tables
    if name.endswith("_00761.xml"):
        for t in tables:
            t._basis = "CFS"
        return tables
    boundary = _ofs_line_boundary(path)
    for t in tables:
        t._basis = None if boundary is None else ("OFS" if t.line_no >= boundary else "CFS")
    return tables


def _prefer_ofs(tables):
    """Drop CFS(연결)-tagged tables when at least one OFS(별도)-tagged candidate exists in
    the same `tables` pool; a no-op when basis is unknown (None) everywhere, so filings
    without a detectable ATOC split are unaffected (existing behaviour preserved)."""
    if any(getattr(t, "_basis", None) == "OFS" for t in tables):
        return [t for t in tables if getattr(t, "_basis", None) != "CFS"]
    return tables
