"""p_lotte: prototype of the Tier-2 PRIOR-column reader for 롯데손해보험 (KR0003).
Three production layouts exist (combined-caption / caption-stripped combined / per-segment split); each is re-implemented here with a
`prior` switch (the only change vs production: take the 전기/전분기 table of the pair instead of the first).  Production helpers
(_lotte_from_sections, _lotte_lob_pos, _LOTTE_SEC) are called unchanged.  Fidelity: prior=False on the ORIGINAL filing must reproduce the master.
READ-ONLY."""
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import fsapi as F  # noqa: E402
import prod as P  # noqa: E402
import mlib as M  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
C = P.C
_norm, _row_nums, _is_rollforward = C._norm, C._row_nums, C._is_rollforward
CODE = "KR0003"


def combined(tables, prior):
    """legacy combined-caption note: candidate tables = caption mentions 보험손익 + 장기/일반/자동차 header; production keeps the FIRST per caption.
    prior=True keeps the SECOND per caption (the 전기/전분기 twin)."""
    def is_cand(t):
        cap = (t.caption or "")
        if "보험손익" not in cap or _is_rollforward(t):
            return False
        h = " ".join(" ".join(_norm(c) for c in hr) for hr in t.header)
        return all(k in h for k in ("장기", "일반", "자동차"))
    seen, pick = {}, []
    for t in tables:
        if not is_cand(t):
            continue
        k = t.caption or ""
        seen[k] = seen.get(k, 0) + 1
        if seen[k] == (2 if prior else 1):
            pick.append(t)
    sect = {}
    for t in pick:
        section = None
        for r in t.rows:
            lab0 = _norm(r[0])
            nums = _row_nums(r)
            sk = C._LOTTE_SEC.get(lab0)
            if sk is not None and not nums:
                section = sk
                continue
            if section is None or not nums:
                continue
            sect.setdefault(section, []).append((lab0.replace(" ", ""), nums))
    if not all(k in sect for k in ("rev", "cost", "re_rev", "re_cost")):
        return {}, None
    # reuse the production assembler by feeding it section lists in its (rows, pos) form
    pos = C._lotte_lob_pos(pick[0])
    s2 = {}
    for sec, items in sect.items():
        rows = [[lab] + [f"{v}" for v in nums] for lab, nums in items]
        s2.setdefault(sec, []).append((rows, pos))
    return C._lotte_from_sections(s2), [t.line_no for t in pick]


def bycontent(tables, prior):
    """caption-stripped combined single table (content identified); production takes the first, prior=True the second."""
    n = 0
    for t in tables:
        if _is_rollforward(t) or not t.rows:
            continue
        labs0 = {_norm(r[0]) for r in t.rows if not _row_nums(r)}
        if not ({"보험수익", "보험비용", "재보험수익", "재보험비용"} <= labs0):
            continue
        pos = C._lotte_lob_pos(t)
        if pos is None:
            continue
        n += 1
        if n != (2 if prior else 1):
            continue
        sect, section, buf = {}, None, []
        for r in t.rows:
            sk = C._LOTTE_SEC.get(_norm(r[0]))
            if sk and not _row_nums(r):
                if section is not None:
                    sect.setdefault(section, []).append((buf, pos))
                section, buf = sk, []
                continue
            if section is not None:
                buf.append(r)
        if section is not None:
            sect.setdefault(section, []).append((buf, pos))
        if not all(sect.get(k) for k in ("rev", "cost", "re_rev", "re_cost")):
            return {}, None
        return C._lotte_from_sections(sect), [t.line_no]
    return {}, None


def split(tables, prior):
    """per-segment split layout: keep the tables whose period marker is current (production) or prior (prior=True)."""
    def subhead_leg(s):
        s = s.replace(" ", "")
        if "재보험비용의보험서비스비용분석공시" in s:
            return "re_rev"
        if "재보험비용분석공시" in s:
            return "re_cost"
        if "재보험수익분석공시" in s:
            return "re_rev"
        if "보험서비스비용분석공시" in s and "재보험" not in s:
            return "cost"
        if "보험수익분석공시" in s:
            return "rev"
        return None
    sect, cur, cur_ok, lines = {}, None, True, []
    for t in tables:
        if not t.rows:
            continue
        r0 = " ".join(_norm(c) for c in t.rows[0])
        lg = subhead_leg(r0)
        if lg is not None:
            cur, cur_ok = lg, ("전분기" not in r0 and "전반기" not in r0)
            continue
        r0c = r0.replace(" ", "")
        if r0c.startswith(("당분기", "당반기")):
            cur_ok = True
            continue
        if r0c.startswith(("전분기", "전반기", "전기")):
            cur_ok = False
            continue
        if cur is None or _is_rollforward(t):
            continue
        if cur_ok == prior:           # production: keep cur_ok True ; prior: keep cur_ok False
            continue
        pos = C._lotte_lob_pos(t)
        if pos is None:
            continue
        sect.setdefault(cur, []).append((t.rows, pos))
        lines.append(t.line_no)
    if not all(sect.get(k) for k in ("rev", "cost", "re_rev", "re_cost")):
        return {}, None
    return C._lotte_from_sections(sect), lines


def run(tables, prior):
    for name, fn in (("combined", combined), ("bycontent", bycontent), ("split", split2)):
        out, lines = fn(tables, prior)
        if out and any(out.get(i) is not None for i in (4, 5, 6)):
            return name, out, lines
    return None, {}, None




def split2(tables, prior):
    """bounded split-layout reader: a leg (subhead) collects the LOB tables that follow the matching period marker CONSECUTIVELY;
    the streak ends at the first non-LOB table, a new subhead or the opposite marker (DART prints 전기말/전반기 markers for ~60 unrelated notes)."""
    def subhead_leg(s):
        s = s.replace(" ", "")
        if "재보험비용의보험서비스비용분석공시" in s:
            return "re_rev"
        if "재보험비용분석공시" in s:
            return "re_cost"
        if "재보험수익분석공시" in s:
            return "re_rev"
        if "보험서비스비용분석공시" in s and "재보험" not in s:
            return "cost"
        if "보험수익분석공시" in s:
            return "rev"
        return None
    sect, cur, state, streak, lines = {}, None, None, False, []
    for t in tables:
        if not t.rows:
            continue
        r0 = " ".join(_norm(c) for c in t.rows[0])
        lg = subhead_leg(r0)
        if lg is not None:
            cur = lg
            # a subhead naming the prior period flips the state like a marker
            state = "prior" if ("전분기" in r0 or "전반기" in r0) else "cur"
            streak = False
            continue
        r0c = r0.replace(" ", "")
        if r0c.startswith(("당분기", "당반기")):
            state, streak = "cur", False
            continue
        if r0c.startswith(("전분기", "전반기", "전기")):
            state, streak = "prior", False
            continue
        if cur is None or _is_rollforward(t):
            continue
        pos = C._lotte_lob_pos(t)
        if pos is None:
            if streak:                 # a non-LOB table ends this leg's streak
                cur, state, streak = None, None, False
            continue
        if state == ("prior" if prior else "cur"):
            sect.setdefault(cur, []).append((t.rows, pos))
            lines.append(t.line_no)
            streak = True
    if not all(sect.get(k) for k in ("rev", "cost", "re_rev", "re_cost")):
        return {}, None
    return C._lotte_from_sections(sect), lines
