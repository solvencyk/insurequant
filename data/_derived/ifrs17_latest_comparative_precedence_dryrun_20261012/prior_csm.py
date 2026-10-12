"""Read-only library: extract the PRIOR-period (comparative) CSM roll-forward from a later DART filing.

It re-uses the production builder (scripts/build_csm_waterfall_master.py) functions UNCHANGED: blocks_for_dir -> waterfall ->
unit detection.  Only the block list handed to waterfall() differs: it contains the later filing's PRIOR-period blocks, renamed so
the builder's own "drop prior copies" filters do not discard them.  Nothing is written anywhere.

A block is labelled PRIOR when (first match wins)
  1. builder flags: _is_prior_caption(caption) or _is_prior_header(block)            -> 'prior'
  2. a marker block ("<전분기>", "<전반기>", "<전기>", "<당분기>", ...) precedes it in document order (same source file)
  3. no marker, no flag: blocks sharing (source, caption, header) in document order alternate current, prior, current, prior...
     (kept only when the group has an even size >= 2)
Everything else is 'current' / 'unknown' and dropped.
"""
from __future__ import annotations

import copy
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import build_csm_waterfall_master as B  # noqa: E402

_MARK_PRIOR = ("<전분기>", "<전반기>", "<전기>", "<전분기말>", "<전반기말>", "<전기말>", "<전분기>", "전분기", "전반기", "전기")
_MARK_CUR = ("<당분기>", "<당반기>", "<당기>", "<당분기말>", "<당반기말>", "<당기말>", "당분기", "당반기", "당기")


def _marker_kind(b) -> str | None:
    rows = b.get("rows") or []
    if not rows or len(rows) > 2 or b.get("header"):
        return None
    first = rows[0][0] if rows[0] else ""
    if not isinstance(first, str):
        return None
    f = re.sub(r"\s", "", first)
    if f.startswith("<전") or f in ("전기", "전분기", "전반기"):
        return "prior"
    if f.startswith("<당") or f in ("당기", "당분기", "당반기"):
        return "current"
    return None


def label_blocks(blocks):
    """Return [(block, label)] in document order; label in {'prior','current','unknown','marker'}."""
    ordered = sorted(blocks, key=lambda x: (x.get("_src", ""), x.get("line_no") or 0))
    out, state, last_src = [], None, None
    for b in ordered:
        src = b.get("_src", "")
        if src != last_src:
            state, last_src = None, src
        mk = _marker_kind(b)
        if mk:
            state = mk
            out.append((b, "marker"))
            continue
        cap = b.get("caption") or ""
        if B._is_prior_caption(cap) or B._is_prior_header(b):
            out.append((b, "prior"))
        elif state:
            out.append((b, state))
        else:
            out.append((b, "unknown"))
    # rule 3: alternate within identical (src, caption, header) groups when nothing else labelled them
    groups = {}
    for idx, (b, lab) in enumerate(out):
        if lab == "unknown":
            key = (b.get("_src", ""), B._ns(b.get("caption") or ""), str(b.get("header")))
            groups.setdefault(key, []).append(idx)
    for key, idxs in groups.items():
        if len(idxs) >= 2 and len(idxs) % 2 == 0:
            for k, idx in enumerate(idxs):
                out[idx] = (out[idx][0], "current" if k % 2 == 0 else "prior")
    return out


def _as_current(b):
    """Copy of a prior block with the period words neutralised so the builder's prior filters keep it."""
    nb = copy.deepcopy(b)
    cap = nb.get("caption") or ""
    cap = re.sub(r"전분기", "당분기", cap)
    cap = re.sub(r"전반기", "당반기", cap)
    cap = re.sub(r"제\s*(\d+)\s*\(\s*전\s*\)\s*기", r"제\1(당)기", cap)
    cap = re.sub(r"^(\s*[\(\d\)\.\-\s]*)전기", r"\1당기", cap)
    nb["caption"] = cap
    hdr = []
    for row in nb.get("header") or []:
        hdr.append([("당기" if (isinstance(c, str) and c.strip() in ("전기", "전분기", "전반기")) else c) for c in row])
    if hdr:
        nb["header"] = hdr
    # row labels: the closing row of a prior table reads '전분기말 ...' / '전반기말 ...' / '전기말 ...' - the builder's stage patterns only know the current words
    rows = []
    for row in nb.get("rows") or []:
        row = list(row)
        for i in range(min(2, len(row))):
            c = row[i]
            if isinstance(c, str):
                c2 = re.sub(r"^(\s*)전(분기|반기|기)말", r"\1당\2말", c)
                c2 = re.sub(r"^(\s*)전(분기|반기|기)(\s)", r"\1당\2\3", c2)
                row[i] = c2
        rows.append(row)
    nb["rows"] = rows
    return nb


_SHORT_PRIOR_CAP = re.compile(r"^[\s\(\)\d\.\-가-힣]{0,6}(전분기|전반기|전기)\s*$")


def short_prior_blocks(rd, name, have):
    """Prior-period tables whose own caption is only '나. 전분기' / '(2) 전반기' / '전기': the production extractor drops them because the short
    enumerator carries no measurement keyword (현대해상, 미래에셋 ...).  Re-read them straight from the filing: a table with such a caption whose
    header equals that of the nearest preceding table that WAS extracted inherits that table's caption (prefixed '전분기 ').
    `have` = set of (src, line_no) already present."""
    from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: PLC0415
    from scripts.pl_breakdown.common import _iter_tables_by_basis, _tag_basis  # noqa: PLC0415
    out = []
    xmls = {}
    for x in list(rd.glob("*.xml")) + list(rd.glob("xml/*.xml")) + list(rd.glob("extracted/*.xml")):
        if x.name.endswith("_00761.xml"):
            continue
        xmls.setdefault(x.name, x)
    for x in sorted(xmls.values()):
        try:
            tabs = _tag_basis(list(_iter_tables_by_basis(x, lambda p: list(_iter_tables_with_context(p)))), x)
        except Exception:
            continue
        ofs = [t for t in tabs if getattr(t, "_basis", None) == "OFS"]
        pool = ofs or tabs
        prev = None
        for t in pool:
            cap = (getattr(t, "caption", "") or "")
            # the nearest preceding table WITH a header must itself be an extracted measurement block (so this is its prior-period twin)
            if (_SHORT_PRIOR_CAP.match(cap.strip()) and (x.name, t.line_no) not in have and prev is not None
                    and (x.name, prev.line_no) in have and t.header):
                if [c for r in t.header for c in r] == [c for r in prev.header for c in r]:
                    out.append({"caption": "전분기 " + (getattr(prev, "caption", "") or ""), "header": [list(r) for r in t.header],
                                "rows": [list(r) for r in t.rows], "line_no": t.line_no, "_src": x.name, "block_type": "short_prior",
                                "footnotes": [], "score": 0})
            if t.header:
                prev = t
    return out


def prior_blocks(rd, name):
    blocks = B.blocks_for_dir(rd, name)
    have = {(b.get("_src", ""), b.get("line_no")) for b in blocks}
    try:
        extra = short_prior_blocks(rd, name, have)
    except Exception:
        extra = []
    for e in extra:
        nb = B.normalize_block_header(e)
        nb["_src"] = e["_src"]
        nb["basis"] = B._block_basis(e["_src"])
        blocks.append(nb)
    lab = label_blocks(blocks)
    pri = [_as_current(b) for b, l in lab if l == "prior"]
    cur = [b for b, l in lab if l == "current"]
    return pri, cur, blocks, lab


def stages_to_eok(wf, rd):
    """Same tail as waterfall_for_dir: unit detection -> 백만원 -> item 4 residual -> 억원 (1 dp), returns ({1..6}, tag)."""
    if not wf:
        return None, None
    mag = max((abs(v) for v in wf.values() if v is not None), default=0.0)
    udiv, utag = B._detect_unit_udiv(rd, mag)
    if udiv is None:
        return None, f"u:{utag}"
    if udiv != 1.0:
        wf = {no: (v / udiv if v is not None else None) for no, v in wf.items()}
    clo = wf.get(6) or 0
    assum = clo - ((wf.get(1) or 0) + (wf.get(2) or 0) + (wf.get(3) or 0) + (wf.get(5) or 0))
    vals = {1: wf.get(1), 2: wf.get(2), 3: wf.get(3), 4: assum, 5: wf.get(5), 6: wf.get(6)}
    return {no: (round(v / 100, 1) if v is not None else None) for no, v in vals.items()}, f"u:{utag}"


def prior_waterfall(rd, name, anchor=None):
    """(vals_eok{1..6} | None, src, n_prior_blocks)"""
    pri, cur, blocks, lab = prior_blocks(rd, name)
    if not pri:
        return None, "no-prior-blocks", 0
    # runaway guard: the builder's per-cluster search is a cartesian product over opening clusters (explodes beyond ~16 candidate blocks)
    nvec = 0
    for b in pri:
        try:
            if B.block_stages(b) or B.pattern2_stages(b):
                nvec += 1
        except Exception:
            pass
    if nvec > 16:
        return None, f"too-many-prior-blocks({nvec})", len(pri)
    m = re.match(r"(KR\d+)_", rd.name)
    wf, src = B.waterfall(pri, anchor, m.group(1) if m else None)
    if not wf:
        return None, src or "none", len(pri)
    vals, tag = stages_to_eok(wf, rd)
    return vals, f"{src}+{tag}", len(pri)


def current_waterfall(rd, name, anchor=None):
    """Same call as the builder (for self-test)."""
    return B.waterfall_for_dir(rd, name, anchor)
