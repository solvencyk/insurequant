"""Label, number and quarter helpers shared across the PL extractor."""
# Split out of scripts/build_pl_breakdown.py on 2026-07-21. Behaviour unchanged;
# the golden gate (tests/test_pl_breakdown_golden.py) pins the builder output.
import os
import re
import tempfile
from pathlib import Path

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

# Korean section headings -- the fallback when the ENG-attribute scan finds nothing.
# Two templates need it (measured 2026-08-26 across 삼성생명's 13 filings: the ENG path
# located the boundary in 6, the text scan locates it in 12):
#   - 분기/반기보고서 whose <TITLE ATOC="Y"> carries no ENG attribute at all
#     ("2. 연결재무제표" ... "4. 재무제표"),
#   - the 2026+ plain-HTML export with ZERO <TITLE> tags, where the same headings survive
#     as ordinary paragraphs ("2-1. 연결 재무상태표" ... "4-1. 재무상태표").
# Markup is stripped before matching so both forms hit the same two patterns.  The trailing
# `$` on the OFS pattern is what keeps "5. 재무제표 주석" and prose like "…재무제표 재작성"
# out -- only the statements section itself starts the 별도 half.
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_CFS_HEAD_RE = re.compile(r"^\d+(-\d+)?\.\s*연결\s*재무(제표|상태표)")
_OFS_HEAD_RE = re.compile(r"^\d+(-\d+)?\.\s*재무(제표|상태표)\s*$")

# lxml's HTMLParser -- the parser src.ifrs17.csm_extractor uses -- caps element.sourceline
# at 2**16-1: every element past that line reports exactly 65535.  Measured on 삼성생명
# 2025.2Q (main body 209,875 lines): 79,836 elements come back saturated while the 별도
# section starts at line 101,480, so `line_no >= boundary` is false for EVERY table and the
# whole filing reads 연결.  etree.XMLParser(recover=True) does NOT saturate on the same file
# (max sourceline 209,871) -- the cap is specific to the HTML parser path.  When the
# boundary sits past the cap the line comparison carries no information, so callers must
# split the file instead of trusting it: see `_basis_sections`.
_SOURCELINE_CAP = 65535


def _plain(line):
    """Markup-stripped, whitespace-collapsed text of one raw line."""
    return _WS_RE.sub(" ", _TAG_RE.sub(" ", line)).strip()


def _ofs_line_boundary(path):
    """Line number (1-indexed) where the 별도(separate/OFS) financial statements begin in
    a DART filing's main body XML, or None when not determinable.  Only trusted when a
    PRECEDING 연결 statements marker was also seen (a both-basis filing) -- a lone OFS
    marker, or no markers at all (older/simpler filings), returns None so callers treat
    basis as unknown rather than guessing.  ATOC markers inside note cross-references
    (prose like '...5.재무제표 주석...부분을 참고') are excluded by the ATOC="Y"+ENG
    attribute requirement on the English path and by the `$`-anchored heading pattern on
    the Korean one -- neither matches a sentence."""
    try:
        cfs_seen = False
        kr_cfs_seen = False
        kr_hit = None
        with open(path, encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f, 1):
                if 'ATOC="Y"' in line and "financial statements" in line.lower():
                    m = _OFS_TITLE_RE.search(line)
                    if m:
                        eng = m.group(1).lower()
                        if "notes" not in eng:
                            if "consolidated" in eng:
                                cfs_seen = True
                            elif ("separate" in eng or "non-consolidated" in eng) and cfs_seen:
                                return i
                # Korean fallback -- scanned in the same pass so the file is read once.
                if kr_hit is None and "재무" in line:
                    t = _plain(line)
                    if _CFS_HEAD_RE.match(t):
                        kr_cfs_seen = True
                    elif kr_cfs_seen and _OFS_HEAD_RE.match(t):
                        kr_hit = i
    except OSError:
        return None
    return kr_hit


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
        pre = getattr(t, "_basis_from_split", None)
        if pre is not None:                      # came from _iter_tables_by_basis
            t._basis = pre
        elif boundary is None or boundary > _SOURCELINE_CAP:
            t._basis = None                      # unknown: line_no cannot decide (see cap)
        else:
            t._basis = "OFS" if t.line_no >= boundary else "CFS"
    return tables


def _iter_tables_by_basis(path, extract):
    """Yield the tables of one filing with `._basis_from_split` set where position alone
    cannot decide it.  `extract(path)` is the caller's own table iterator (the PL builder
    and the CSM builder use different ones); it must yield objects carrying `.line_no`.

    Below the sourceline cap this is a pass-through -- `_tag_basis` resolves basis from
    `line_no` exactly as before, so nothing changes for the filings that already worked.
    Past the cap `line_no` is saturated and useless, so the file is physically cut at the
    boundary and each half extracted on its own; the halves are then labelled outright.
    Cutting mid-document is safe for these inputs because the extractors parse with
    `recover=True` (a fragment without its <html>/<body> wrapper still parses); the only
    loss is the caption context of the first table in the tail, which sits right under the
    section heading anyway."""
    boundary = _ofs_line_boundary(path)
    if boundary is None or boundary <= _SOURCELINE_CAP:
        for t in extract(path):
            t._basis_from_split = None
            yield t
        return
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
    for part, basis in ((lines[:boundary - 1], "CFS"), (lines[boundary - 1:], "OFS")):
        fh = tempfile.NamedTemporaryFile("w", suffix=".xml", delete=False, encoding="utf-8")
        try:
            fh.write("".join(part))
            fh.close()
            for t in extract(Path(fh.name)):
                t._basis_from_split = basis
                yield t
        finally:
            try:
                os.unlink(fh.name)
            except OSError:
                pass


def _prefer_ofs(tables):
    """Drop CFS(연결)-tagged tables when at least one OFS(별도)-tagged candidate exists in
    the same `tables` pool; a no-op when basis is unknown (None) everywhere, so filings
    without a detectable ATOC split are unaffected (existing behaviour preserved)."""
    if any(getattr(t, "_basis", None) == "OFS" for t in tables):
        return [t for t in tables if getattr(t, "_basis", None) != "CFS"]
    return tables
