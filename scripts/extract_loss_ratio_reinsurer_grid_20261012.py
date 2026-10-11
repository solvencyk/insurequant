#!/usr/bin/env python3
"""Cell-grid reader for the reinsurer 「② 위험보험료 대비 예상보험금」 tables (ticket 20261012T0100Z).

Why: reinsurer filings draw this table as a fully ruled grid whose cells wrap digits across lines
("1,3" / "51"), stack vertical labels ("무 배 당 사 망"), split rows across page breaks and print the year caption
split from its brackets. The generic coordinate parser in extract_loss_ratio.py cannot read those, so this module reads the
RULED GRID instead: cell boxes come from the table borders (thin black filled rects), a cell's text = every word whose
centre lies inside the box, concatenated in reading order with spaces removed. Nothing here writes data/loss_ratio/.

API: read_pdf_B(pdf_path, pages) -> list[dict] long rows (same fields the extractor emits for the B table, see ROW KEYS).
The module is a library; run extract_loss_ratio_reinsurer_grid_20261012.py --selftest <pdf> <page> to print rows for a page.
"""
from __future__ import annotations

import io
import re
import sys
from collections import defaultdict
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import extract_loss_ratio as X  # noqa: E402  (nz, parse_num, is_dash, canon_period, metric_of ... reused unchanged)

PERIODS = ["1년", "2년", "3년", "4년", "5년", "6년", "7년", "8년", "9년", "10년",
           "11~15년", "16~20년", "21~25년", "26~30년", "30년 이후", "현재가치"]
NCOL = len(PERIODS)


def _merge(segs: list[tuple[float, float, float]], tol: float = 0.8) -> list[tuple[float, float, float]]:
    """(pos, a0, a1) collinear pieces -> merged. pos clustered within tol."""
    segs = sorted(segs)
    out: list[list[float]] = []
    for pos, a0, a1 in segs:
        if out and abs(out[-1][0] - pos) <= tol and a0 <= out[-1][2] + tol:
            out[-1][2] = max(out[-1][2], a1)
            out[-1][1] = min(out[-1][1], a0)
        else:
            merged = False
            for o in reversed(out[-8:]):
                if abs(o[0] - pos) <= tol and a0 <= o[2] + tol and a1 >= o[1] - tol:
                    o[1], o[2] = min(o[1], a0), max(o[2], a1)
                    merged = True
                    break
            if not merged:
                out.append([pos, a0, a1])
    return [(o[0], o[1], o[2]) for o in out]


def rules_of(page) -> tuple[list, list]:
    """-> (H=[(y,x0,x1)], V=[(x,y0,y1)]) from table borders: thin dark filled rects, dark stroked lines and stroked rect edges."""
    H, V = [], []

    def add_seg(x0, y0, x1, y1):
        if abs(y1 - y0) <= 0.8 and abs(x1 - x0) >= 2.0:
            H.append(((y0 + y1) / 2, min(x0, x1), max(x0, x1)))
        elif abs(x1 - x0) <= 0.8 and abs(y1 - y0) >= 2.0:
            V.append(((x0 + x1) / 2, min(y0, y1), max(y0, y1)))

    for d in page.get_drawings():
        t = d.get("type")
        fill, color = d.get("fill"), d.get("color")
        dark_fill = bool(fill) and max(fill) <= 0.45
        dark_stroke = bool(color) and max(color) <= 0.45 and "s" in (t or "")
        if not (dark_fill or dark_stroke):
            continue
        for it in d["items"]:
            if it[0] == "re":
                r = it[1]
                w, h = r.x1 - r.x0, r.y1 - r.y0
                if dark_fill and h <= 1.3 and w >= 2.0:
                    H.append(((r.y0 + r.y1) / 2, r.x0, r.x1))
                elif dark_fill and w <= 1.3 and h >= 2.0:
                    V.append(((r.x0 + r.x1) / 2, r.y0, r.y1))
                elif dark_stroke:
                    add_seg(r.x0, r.y0, r.x1, r.y0)
                    add_seg(r.x0, r.y1, r.x1, r.y1)
                    add_seg(r.x0, r.y0, r.x0, r.y1)
                    add_seg(r.x1, r.y0, r.x1, r.y1)
            elif it[0] == "l" and dark_stroke:
                add_seg(it[1].x, it[1].y, it[2].x, it[2].y)
    return _merge(H), _merge(V)


def cluster(vals: list[float], tol: float = 1.2) -> list[float]:
    vals = sorted(vals)
    out: list[list[float]] = []
    for v in vals:
        if out and v - out[-1][-1] <= tol:
            out[-1].append(v)
        else:
            out.append([v])
    return [sum(c) / len(c) for c in out]


class Word:
    __slots__ = ("x0", "y0", "x1", "y1", "t")

    def __init__(self, x0, y0, x1, y1, t):
        self.x0, self.y0, self.x1, self.y1, self.t = x0, y0, x1, y1, t

    @property
    def xc(self):
        return (self.x0 + self.x1) / 2

    @property
    def yc(self):
        return (self.y0 + self.y1) / 2


def words_of(page) -> list[Word]:
    out = []
    seen = set()
    for x0, y0, x1, y1, t, *_ in page.get_text("words"):
        t = t.replace("　", " ").replace(" ", " ").strip()
        if not t:
            continue
        k = (t, round(x0, 0), round(y0, 0))
        if k in seen:
            continue
        seen.add(k)
        out.append(Word(x0, y0, x1, y1, t))
    return out


def join_words(ws: list[Word]) -> str:
    ws = sorted(ws, key=lambda w: (round(w.yc / 2.5), w.x0))
    return "".join(w.t for w in ws).replace(" ", "")


def cell_text(ws: list[Word], x0: float, x1: float, y0: float, y1: float) -> str:
    return join_words([w for w in ws if x0 <= w.xc < x1 and y0 <= w.yc < y1])


def page_grids(page) -> list[dict]:
    """Ruled data grids on a page (tables stacked vertically are separated by gaps in their vertical rules).
    Each: dict(cols=[(x0,x1)*16], label_cols=[(x0,x1)...] (last one = metric column), H, top, bottom)."""
    H, V = rules_of(page)
    Vl = sorted([v for v in V if v[2] - v[1] >= 12], key=lambda v: v[1])
    groups: list[list] = []
    for v in Vl:
        if groups and v[1] <= groups[-1][-1][2] + 3 and v[1] <= max(x[2] for x in groups[-1]) + 3:
            groups[-1].append(v)
        else:
            groups.append([v])
    out = []
    for gr in groups:
        xs = cluster([v[0] for v in gr], 1.5)
        if len(xs) < NCOL + 2:
            continue
        data_x = xs[-(NCOL + 1):]
        label_x = xs[:-NCOL]
        cols = list(zip(data_x[:-1], data_x[1:]))
        label_cols = list(zip(label_x[:-1], label_x[1:]))
        if not label_cols:
            continue
        out.append({"cols": cols, "label_cols": label_cols, "H": H, "top": min(v[1] for v in gr), "bottom": max(v[2] for v in gr)})
    out.sort(key=lambda g: g["top"])
    return out


def row_bounds(H, x0: float, x1: float, top: float, bottom: float, cover: float = 0.6) -> list[float]:
    """y positions of horizontal rules covering >= cover of [x0,x1]; plus top/bottom."""
    ys = [top]
    for y, a0, a1 in H:
        if y < top - 1 or y > bottom + 1:
            continue
        ov = min(a1, x1) - max(a0, x0)
        if ov >= cover * (x1 - x0):
            ys.append(y)
    ys.append(bottom)
    return cluster(ys, 1.5)


def _metric(txt: str):
    t = X.nz(txt)
    if t.startswith("예상") or re.search(r"^보험금\(A\)|^험금\(A\)", t):
        return "예상보험금"
    if t.startswith("위험") or "험료(B)" in t:
        return "위험보험료"
    if t.startswith("비율") or "(A/B)" in t:
        return "비율"
    return None


_YEAR_LINE = re.compile(r"^[<\[(]?(20\d\d)년[>\])]?$")
_SEG_LINE = re.compile(r"^\[([^\]\d]{2,14})\]$")


def _lines(ws: list[Word], tol: float = 3.0) -> list[tuple[float, str]]:
    """page words -> [(y, text-without-spaces)] grouped by y, x order."""
    ws = sorted(ws, key=lambda w: (w.yc, w.x0))
    out: list[list[Word]] = []
    for w in ws:
        if out and abs(out[-1][0].yc - w.yc) <= tol:
            out[-1].append(w)
        else:
            out.append([w])
    res = []
    for ln in out:
        ln.sort(key=lambda w: w.x0)
        res.append((sum(w.yc for w in ln) / len(ln), "".join(w.t for w in ln).replace(" ", "")))
    return res


def page_events(ws: list[Word], table_top: float | None):
    """caption events above/outside the table: [(y, kind, value)] kind in year|seg|unit."""
    ev = []
    for y, t in _lines(ws):
        m = _YEAR_LINE.match(t)
        if m:
            ev.append((y, "year", int(m.group(1))))
            continue
        m = _SEG_LINE.match(t)
        if m:
            ev.append((y, "seg", m.group(1)))
            continue
        u = X.parse_unit(t)
        if u and len(t) < 30:
            ev.append((y, "unit", u))
    return ev


def read_page(page, state: dict, pno: int) -> None:
    """Append logical rows to state['rows']; state carries year/seg/unit across pages.
    A row whose metric cell is empty and that is not a header interval, when it is the first data interval of a page that
    continues an earlier page, is a page-break fragment of the previous row: its text is appended cell by cell."""
    grids = page_grids(page)
    ws = words_of(page)
    if not grids:
        state.setdefault("nogrid", []).append(pno)
        return
    for g in grids:
        _read_grid(g, ws, state, pno)
    state["lastpage"] = pno


def _read_grid(g: dict, ws: list[Word], state: dict, pno: int) -> None:
    cols, lcols, H = g["cols"], g["label_cols"], g["H"]
    mcol = lcols[-1]
    labcols = lcols[:-1]
    ys = row_bounds(H, cols[0][0], cols[-1][1], g["top"], g["bottom"], cover=0.7)
    ev = page_events(ws, g["top"])
    lab_bounds = [row_bounds(H, c[0], c[1], g["top"], g["bottom"], cover=0.6) for c in labcols]
    mcol_txt = " ".join(cell_text(ws, mcol[0], mcol[1], a_, b_) for a_, b_ in zip(ys[:-1], ys[1:]))
    if "예정유지비" in mcol_txt:            # the neighbouring 「예정유지비 대비 …」 table has the same shape - not this table
        state.setdefault("skipped_grids", []).append(pno)
        return
    prev = state["rows"][-1] if state["rows"] else None
    seen_data = False
    first_spans = None
    for a, b in zip(ys[:-1], ys[1:]):
        if b - a < 2:
            continue
        mid = (a + b) / 2
        mtxt = cell_text(ws, mcol[0], mcol[1], a, b)
        vals = [cell_text(ws, c[0], c[1], a, b) for c in cols]
        metric = _metric(mtxt)
        for y, kind, val in ev:
            if y < a - 0.5 and (pno, y, kind) not in state.setdefault("_ev_done", set()):
                state[kind] = val
                state["_ev_done"].add((pno, y, kind))
        if metric is None:
            header_like = ("경과" in mtxt) or sum(1 for v in vals if v and X.canon_period(v)) >= 3
            if header_like:
                state.setdefault("headers", []).append((pno, vals))
                continue
            if not seen_data and prev is not None and prev["page"] < pno:
                for ci, c in enumerate(labcols):
                    prev["label_cont"][ci] += cell_text(ws, c[0], c[1], a, b)
                for j, v in enumerate(vals):
                    prev["vals"][j] += v
                prev["mtxt"] += mtxt
                state.setdefault("page_cont", set()).add(pno)
            elif any(vals) or mtxt:
                state.setdefault("unplaced", []).append((pno, round(a), mtxt, [v for v in vals if v][:4]))
            seen_data = True
            continue
        seen_data = True
        labels, spans = [], []
        for ci, c in enumerate(labcols):
            bnds = lab_bounds[ci]
            lo = max([y for y in bnds if y <= mid + 0.01] or [g["top"]])
            hi = min([y for y in bnds if y > mid] or [g["bottom"]])
            labels.append(cell_text(ws, c[0], c[1], lo, hi + 0.01))
            spans.append(lo)
        if first_spans is None:
            first_spans = list(spans)
        row = {"page": pno, "y": mid, "metric": metric, "mtxt": mtxt, "labels": labels, "vals": vals, "first_spans": first_spans,
               "year": state.get("year"), "seg": state.get("seg"), "unit": state.get("unit"),
               "label_cont": [""] * len(labcols), "lab_span": spans, "top": g["top"]}
        state["rows"].append(row)
        prev = row


def read_pdf(pdf_path: str, pages: list[int], year0: int | None = None):
    """-> state dict (rows, page_cont, unplaced, nogrid, headers...) for the given page list (read in order)."""
    doc = fitz.open(pdf_path)
    state: dict = {"rows": [], "year": year0}
    for p in pages:
        read_page(doc[p - 1], state, p)
    state["npages"] = doc.page_count
    return state


def resolve_groups(state: dict) -> list[dict]:
    """logical rows -> groups of (예상보험금, 위험보험료, 비율) with full labels.
    Label cells that start on the top rule of a page that begins with a page-break fragment continue the previous page's
    cell (prefix = previous row's full label). Empty top cells without a fragment inherit (flag 'label_inherited')."""
    rows = state["rows"]
    pcont = state.get("page_cont", set())
    prev = None
    for r in rows:
        r["full"], r["raw"], r["lflags"] = [], [], []
        for ci, txt in enumerate(r["labels"]):
            at_top = abs(r["lab_span"][ci] - r["first_spans"][ci]) <= 1.0
            same_table = prev is not None and prev["year"] == r["year"] and prev["seg"] == r["seg"]
            if prev is not None and r["page"] != prev["page"] and at_top and same_table:
                if r["metric"] != "예상보험금" and prev["metric"] != "비율":
                    raw = prev["raw"][ci] + txt          # the same (A/B/ratio) group continues on the next page: its label cell continues too
                elif txt == "":
                    raw = prev["raw"][ci]
                    r["lflags"].append(f"label_inherited:c{ci}")
                else:
                    raw = txt
            elif prev is not None and r["page"] == prev["page"] and abs(r["lab_span"][ci] - prev["lab_span"][ci]) < 0.5:
                raw = prev["raw"][ci]            # same cell, later row
            else:
                raw = txt
            r["raw"].append(raw)
            r["full"].append(raw + r["label_cont"][ci])   # a row cut by the page break gets its own tail appended
        prev = r
    # a row cut by a page break keeps its own cell; later rows of the same cell read prev["full"] (already contains cont)
    groups: list[dict] = []
    cur = None
    for r in rows:
        if r["metric"] == "예상보험금" or cur is None or r["metric"] in [x["metric"] for x in cur["rows"]]:
            cur = {"rows": [r]}
            groups.append(cur)
        else:
            cur["rows"].append(r)
    return groups


def _num(txt: str):
    """-> (value|None, dec, dash, bad)."""
    t = txt.strip().replace("%", "")
    if not t:
        return (None, 0, False, False)
    if X.is_dash(t):
        return (None, 0, True, False)
    r = X.parse_num(t)
    if r is None:
        return (None, 0, False, True)
    return (r[0], r[1], False, False)


def _tens_blocks(groups: list[dict]) -> set:
    """(year, seg) blocks whose A/B amounts are (almost) all multiples of 10 -> printed rounded to 10억원."""
    cnt: dict = {}
    for g in groups:
        for r in g["rows"]:
            if r["metric"] == "비율":
                continue
            k = (r["year"], r["seg"])
            for v in r["vals"]:
                n, dec, dash, bad = _num(v)
                if n is None or n == 0 or dec != 0:
                    continue
                c = cnt.setdefault(k, [0, 0])
                c[1] += 1
                if abs(n) % 10 == 0:
                    c[0] += 1
    return {k for k, (z, n) in cnt.items() if n >= 40 and z / n >= 0.97}


def to_long(groups: list[dict], meta_row: dict, pdf_rel: str, npages: int, year_default: int | None = None) -> tuple[list[dict], list[str]]:
    out: list[dict] = []
    notes: list[str] = []
    tens = _tens_blocks(groups)
    seen_labels: dict = {}
    for gi, g in enumerate(groups):
        if not any(v for r in g["rows"] for v in r["vals"]):
            notes.append(f"blank group (nothing printed) p{g['rows'][0]['page']} {g['rows'][0]['full']}")
            continue
        mets = [r["metric"] for r in g["rows"]]
        a_row = g["rows"][0]
        full = g["rows"][-1]["full"]
        gub_raw = full[0] if full else ""
        pf_raw = full[1] if len(full) > 1 else ""
        if mets != ["예상보험금", "위험보험료", "비율"]:
            notes.append(f"group{gi}@p{a_row['page']} metrics {mets} label {full}")
        if len(full) == 1:                         # single label column: the portfolio itself
            gub_raw, pf_raw = "", full[0]
        if X.nz(gub_raw) == "합계" or (not gub_raw and X.nz(pf_raw) == "합계"):
            gub, pf_c, pf_o = "합계", "합계", None
        else:
            gk = re.sub(r"[-\s]", "", gub_raw).lower()
            if gk in ("nonpar", "directpar", "indirectpar"):
                gub = X.canon_gubun(gub_raw)
            else:
                gub = gub_raw
                notes.append(f"unrecognised 구분 label {gub_raw!r} p{a_row['page']}")
            pf_c, pf_o = X.canon_portfolio(pf_raw), pf_raw
        flags_g: list[str] = []
        lk = (a_row["year"], a_row["seg"], gub, pf_c)
        if lk in seen_labels and gub != "합계":
            alt = {"유배당기타": "무배당기타", "무배당기타": "유배당기타"}.get(pf_c)
            notes.append(f"duplicate label {lk} at p{a_row['page']} (first at p{seen_labels[lk]})" + (f" -> relabelled {alt}" if alt else ""))
            if alt:
                pf_c = alt
                flags_g.append(f"라벨보정:{pf_o}->{alt}(같은 구분에 같은 라벨 2회 인쇄)")
        seen_labels[lk] = a_row["page"]
        for r in g["rows"]:
            for j, per in enumerate(PERIODS):
                v, dec, dash, bad = _num(r["vals"][j])
                yr_eff = r["year"] if r["year"] is not None else year_default
                if (r["year"], r["seg"]) in tens and r["metric"] != "비율" and dec == 0 and v is not None:
                    dec = -1
                if bad:
                    notes.append(f"bad number p{r['page']} {gub}/{pf_c}/{r['metric']}/{per}: {r['vals'][j]!r}")
                d = dict(meta_row)
                d.update({"기준연도": yr_eff, "구분": gub, "구분_원문": gub_raw, "포트폴리오": pf_c, "포트폴리오_원문": pf_o,
                          "경과기간": per, "지표": r["metric"], "값": v, "_dec": dec, "dash": dash, "bad": bad,
                          "단위": "%" if r["metric"] == "비율" else (r["unit"] or "억원"), "_page": a_row["page"] if r is a_row else r["page"],
                          "사업구분": r["seg"], "출처": {"file": pdf_rel, "page": r["page"]}, "추출방식": "text",
                          "원천위치": "본문" if r["page"] <= max(1, npages * 0.8) else "뒤쪽사본"})
                fl = list(r["lflags"]) + flags_g
                if r["year"] is None and year_default is not None:
                    fl.append("year_from_disclosure(연도 캡션 없음 - 공시 당해연도로 둠)")
                if (r["year"], r["seg"]) in tens and r["metric"] != "비율":
                    fl.append("10억원 단위 반올림 인쇄(전 칸 끝자리 0)")
                if fl:
                    d["플래그"] = fl
                out.append(d)
    return out, notes


def check_long(rows: list[dict]) -> dict:
    """identity check reusing the extractor's rule (ratio vs A/B within printed rounding, 합계 = sum of portfolios), per (year, seg)."""
    stats = {}
    keyset = sorted({(r["기준연도"], r.get("사업구분")) for r in rows}, key=str)
    for yr, seg in keyset:
        sub = [dict(r, 부문=seg) for r in rows if r["기준연도"] == yr and r.get("사업구분") == seg]
        st = X.check_B_rows(sub)
        stats[(yr, seg)] = st
    return stats


def selftest(pdf: str, pages: list[int]):
    st = read_pdf(pdf, pages)
    groups = resolve_groups(st)
    longrows, notes = to_long(groups, {}, pdf, st["npages"])
    print("nogrid", st.get("nogrid"), "unplaced", st.get("unplaced"), "page_cont", st.get("page_cont"))
    for g in groups:
        a = g["rows"][0]
        print(a["page"], a["year"], a["seg"], a["unit"], [r["metric"] for r in g["rows"]], a["full"], a["lflags"])
    print("notes", notes)
    for (yr, seg), s in check_long(longrows).items():
        print(yr, seg, {k: s[k] for k in ("ratio_checked", "ratio_fail", "total_checked", "total_fail", "dup_keys", "missing_cols")}, s["fails"][:6])


if __name__ == "__main__":
    if sys.stdout.encoding is None or "utf" not in sys.stdout.encoding.lower():
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if len(sys.argv) >= 4 and sys.argv[1] == "--selftest":
        a = sys.argv[3]
        pgs = []
        for part in a.split(","):
            if "-" in part:
                s, e = part.split("-")
                pgs += list(range(int(s), int(e) + 1))
            else:
                pgs.append(int(part))
        selftest(sys.argv[2], pgs)
