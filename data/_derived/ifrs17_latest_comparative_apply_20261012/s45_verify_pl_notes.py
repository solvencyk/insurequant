"""Read-only INDEPENDENT re-derivation of the PL LOB legs (items 2..14) of the planned blocks from the PRINTED 별도 prior-period note tables of the later filing.

Not the production reader: own table selection (prior-period marker, 별도 = no 생명 column / last copy), own '-' = 0 positional parsing
(the production `_row_nums` drops '-' cells which is the NEW-03 defect), own formulas written from the documented item definitions:
  4 = |CSM amortisation| (발행 장기)            5 = |RA release| (발행 장기)
  6 = expected claims (발행 보험수익 leg) - incurred claims (발행 보험비용 leg)   [장기 column]
  9 = -(reinsurance CSM amortisation)         10 = -(reinsurance RA)
  11 = incurred recoveries (재보험수익 leg) - expected recoveries (재보험비용 leg)
  3 = 장기 보험수익 total - 장기 보험서비스비용 total        8 = 장기 재보험수익 total - 장기 재보험비용 total        2 = 3 + 8
  7 = 3 - (4+5+6)      12 = 8 - (9+10+11)
  13 / 14 = (보험수익 - 보험서비스비용) + (재보험수익 - 재보험비용) of the 자동차 / 일반 column
Output evidence_pl_notes.json / .txt  (derived value vs plan value per item, with the printed tokens and XML lines)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import xmltab as X  # noqa: E402

ROOT = X.ROOT
plan = json.loads((HERE / "plan_diff.json").read_text(encoding="utf-8"))
plan_by = {}
for c in plan["PL"]:
    plan_by[(c["code"], c["quarter"], c["item"])] = c
live = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"] for r in json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))}


def norm(s: str) -> str:
    return re.sub(r"\s+", "", s or "")


def num(c: str) -> float:
    """positional parse: '-' / '' -> 0.0 ; '(1,234)' -> -1234"""
    v = X.printed_to_float(c)
    return 0.0 if v is None else v


def is_prior_marker(t) -> bool:
    if not t.rows or not t.rows[0].cells:
        return False
    f = norm(t.rows[0].cells[0])
    return len(t.rows) <= 2 and any(p in f for p in ("전분기", "전반기", "전기")) and "당" not in f


def later_xml(code, quarter):
    y = int(quarter[:4]) + 1
    base = ROOT / "data/dart" / f"FY{y}_Q{quarter[5]}" / "raw"
    for d in sorted(base.glob(f"{code}_*")):
        xs = sorted(d.glob("*.xml"), key=lambda p: p.stat().st_size, reverse=True)
        if xs:
            return xs[0]


def lob_cols(t, paired):
    """-> {lob: column index (1-based into cells, after the label)} of the CUMULATIVE value for 장기/일반/자동차/합계 from the header rows."""
    hdr = [norm(c) for c in t.rows[0].cells]
    lobs = []
    for c in hdr[1:]:
        for k in ("장기", "일반", "자동차", "생명", "합계"):
            if k == c or (k in c and len(c) <= len(k) + 2):
                lobs.append(k)
                break
    cols = {}
    for i, lob in enumerate(lobs):
        cols[lob] = (2 * i + 2) if paired else (i + 1)
    return cols


def rows_of(t):
    return [(norm(r.cells[0]), r.cells, r.line) for r in t.rows if r.cells]


def find_row(rows, *needles, start=0, stop=None, exact=False):
    for k in range(start, len(rows) if stop is None else stop):
        lab, cells, line = rows[k]
        if any((lab == norm(n)) if exact else (norm(n) in lab) for n in needles):
            return k, cells, line
    return None


def val(cells, col):
    return num(cells[col]) if col < len(cells) else 0.0


# ------------------------------------------------------------------ family S : 삼성화재 (rows grouped by section labels)
def derive_samsung(xml: Path, paired: bool):
    tabs = X.load_tables(str(xml))
    cand = []
    for i, t in enumerate(tabs):
        if not t.rows or not t.rows[0].cells:
            continue
        hb = norm("".join(t.rows[0].cells))
        if hb.startswith("구분") and "장기" in hb and "자동차" in hb and "일반" in hb and "생명" not in hb and "주요보종별" in norm(" ".join(t.captions)):
            cand.append(i)
    # in document order the file holds [연결 당 , 연결 전 , 별도 당 , 별도 전] x 2 legs-tables -> the LAST four; priors are the 2nd/4th ... pick prior by marker/caption chain
    priors = [i for i in cand if "전" in norm(tabs[i].captions[-1]) and "당" not in norm(tabs[i].captions[-1])
              or ("전" in norm(" ".join(tabs[i].captions[-3:-1])) and False)]
    # simpler and explicit: the prior tables are the odd ones of each (current, prior) pair
    pairs = [(cand[k], cand[k + 1]) for k in range(0, len(cand) - 1, 2)]
    sep_pairs = pairs[len(pairs) // 2:]            # second half = 별도 notes
    prior_tabs = [tabs[b] for (_a, b) in sep_pairs]  # [REV+RECOST table, COST+REREV table]
    out = {"tables": [(t.index, t.line) for t in prior_tabs]}
    if len(prior_tabs) != 2:
        out["error"] = f"expected 2 prior 별도 tables, found {len(prior_tabs)}"
        return out
    t_rev, t_cost = prior_tabs
    cols = lob_cols(t_rev, paired)
    rr = rows_of(t_rev)
    rc = rows_of(t_cost)
    k_re, _, _ = find_row(rr, "재보험비용", exact=True)
    k_rv, _, _ = find_row(rr, "보험수익", exact=True)
    rev_rows = rr[k_rv:k_re]
    recost_rows = rr[k_re:]
    k_c, _, _ = find_row(rc, "보험서비스비용", exact=True)
    k_rr, _, _ = find_row(rc, "재보험수익", exact=True)
    cost_rows = rc[k_c:k_rr]
    rerev_rows = rc[k_rr:]
    j = cols["장기"]
    tok = {}

    def pick(rows, name, col, key, exact=False):
        r = find_row(rows, name, exact=exact)
        if r is None:
            return 0.0
        _, cells, line = r
        tok[key] = (cells[col] if col < len(cells) else "", line, cells[0])
        return num(cells[col]) if col < len(cells) else 0.0

    csm = abs(pick(rev_rows, "보험계약마진상각", j, "rev_csm"))
    ra = abs(pick(rev_rows, "위험조정의변동", j, "rev_ra"))
    exp = pick(rev_rows, "예상보험금및보험서비스비용", j, "rev_exp")
    act = pick(cost_rows, "발생보험금및발생보험서비스비용", j, "cost_act")
    re_csm = pick(recost_rows, "보험계약마진상각", j, "recost_csm")
    re_ra = pick(recost_rows, "위험조정의변동", j, "recost_ra")
    re_exp = pick(recost_rows, "예상출재보험금", j, "recost_exp")
    re_act = pick(rerev_rows, "발생출재보험금", j, "rerev_act")

    def total(rows, col, key):
        r = find_row(rows, "합계", exact=True)
        tok[key] = (r[1][col] if r and col < len(r[1]) else "", r[2] if r else None, "합계")
        return num(r[1][col]) if r and col < len(r[1]) else 0.0

    res = {}
    for lob in ("장기", "자동차", "일반"):
        c = cols[lob]
        res[lob] = (total(rev_rows, c, f"rev_total_{lob}"), total(cost_rows, c, f"cost_total_{lob}"),
                    total(rerev_rows, c, f"rerev_total_{lob}"), total(recost_rows, c, f"recost_total_{lob}"))
    it = {4: csm, 5: ra, 6: exp - act, 9: -re_csm, 10: -re_ra, 11: re_act - re_exp}
    it[3] = res["장기"][0] - res["장기"][1]
    it[8] = res["장기"][2] - res["장기"][3]
    it[2] = it[3] + it[8]
    it[7] = it[3] - (it[4] + it[5] + it[6])
    it[12] = it[8] - (it[9] + it[10] + it[11])
    for lob, n in (("자동차", 13), ("일반", 14)):
        a, b, c_, d = res[lob]
        it[n] = (a - b) + (c_ - d)
    out["items"] = it
    out["tokens"] = tok
    return out


# ------------------------------------------------------------------ family D : DB손해보험 (<원수>/<수재> sections, one table per leg)
def derive_db(xml: Path, paired: bool):
    tabs = X.load_tables(str(xml))
    legs = {"REV": [], "COST": [], "REREV": [], "RECOST": []}
    for i, t in enumerate(tabs):
        if not t.rows or not t.rows[0].cells:
            continue
        hb = norm("".join(t.rows[0].cells))
        if not (hb.startswith("구분") and "장기" in hb and "자동차" in hb and "일반" in hb and "생명" not in hb):
            continue
        cap = norm(" ".join(t.captions[-3:]))
        # leg by the sub-caption that is closest: find which of 6-1..6-4 captions the table sits under -> use the LAST such mention in captions
        mm = re.findall(r"6-([1-4])당", cap)
        if not mm:
            continue
        leg = {"1": "REV", "2": "COST", "3": "REREV", "4": "RECOST"}[mm[0] if False else mm[-1]]
        legs[leg].append((i, t))
    out = {"tables": {}}
    sel = {}
    for leg, lst in legs.items():
        # 연결 copy carries 생명; here only no-생명 (별도) tables are collected, in pairs (current, prior)
        pr = [(i, t) for (i, t) in lst if i > 0 and is_prior_marker(tabs[i - 1])]
        if not pr:
            out["error"] = f"no prior table for leg {leg}"
            return out
        i, t = pr[-1]
        sel[leg] = t
        out["tables"][leg] = (t.index, t.line)
    cols = lob_cols(sel["REV"], paired)
    j = cols["장기"]
    tok = {}

    def sec_rows(t):
        return rows_of(t)

    def pick(leg, names, col, key):
        rows = sec_rows(sel[leg])
        tot = 0.0
        for nm in names:
            r = find_row(rows, nm)
            if r is not None:
                tot += num(r[1][col]) if col < len(r[1]) else 0.0
                tok[f"{key}:{nm}"] = (r[1][col] if col < len(r[1]) else "", r[2], r[1][0])
        return tot

    csm = abs(pick("REV", ["보험계약마진상각"], j, "rev_csm"))
    ra = abs(pick("REV", ["위험조정상각"], j, "rev_ra"))
    exp = pick("REV", ["예상보험금", "예상유지비", "예상손해조사비", "예상투자관리비"], j, "rev_exp")
    act = pick("COST", ["발생보험금", "발생직접유지비", "손해조사비", "투자관리비"], j, "cost_act")
    re_csm = pick("RECOST", ["보험계약마진상각"], j, "recost_csm")
    re_ra = pick("RECOST", ["위험조정상각"], j, "recost_ra")
    re_exp = pick("RECOST", ["예상출재보험금"], j, "recost_exp")
    re_act = pick("REREV", ["발생출재보험금"], j, "rerev_act")

    def grand(leg, col, key):
        rows = sec_rows(sel[leg])
        g = None
        for r in rows:
            if r[0] == "합계":
                g = r
        if g is None:
            for r in rows:
                if r[0] in ("소계", "합계"):
                    g = r
                    break
        tok[key] = (g[1][col] if g and col < len(g[1]) else "", g[2] if g else None, g[0] if g else "")
        return num(g[1][col]) if g and col < len(g[1]) else 0.0

    res = {}
    for lob in ("장기", "자동차", "일반"):
        c = cols[lob]
        res[lob] = (grand("REV", c, f"rev_total_{lob}"), grand("COST", c, f"cost_total_{lob}"),
                    grand("REREV", c, f"rerev_total_{lob}"), grand("RECOST", c, f"recost_total_{lob}"))
    it = {4: csm, 5: ra, 6: exp - act, 9: -re_csm, 10: -re_ra, 11: re_act - re_exp}
    it[3] = res["장기"][0] - res["장기"][1]
    it[8] = res["장기"][2] - res["장기"][3]
    it[2] = it[3] + it[8]
    it[7] = it[3] - (it[4] + it[5] + it[6])
    it[12] = it[8] - (it[9] + it[10] + it[11])
    for lob, n in (("자동차", 13), ("일반", 14)):
        a, b, c_, d = res[lob]
        it[n] = (a - b) + (c_ - d)
    out["items"] = it
    out["tokens"] = tok
    return out


if __name__ == "__main__":
    lines = []
    allres = {}
    for kr, quarters, fn in (("KR0008", ["2023.1Q", "2023.2Q", "2023.3Q"], derive_samsung), ("KR0011", ["2023.1Q", "2023.2Q", "2023.3Q"], derive_db)):
        for q in quarters:
            xml = later_xml(kr, q)
            paired = q[5] != "1"
            r = fn(xml, paired)
            allres[f"{kr}|{q}"] = r
            lines.append(f"=== {kr} {q} <- {xml.name} paired={paired} tables={r.get('tables')} {r.get('error', '')}")
            if "items" in r:
                for n in sorted(r["items"]):
                    d = r["items"][n]
                    p = plan_by.get((kr, q, n))
                    lv = live.get((kr, q, n))
                    if p is not None:
                        ok = abs(d - p["new"]) <= 1.01
                        lines.append(f"  item {n:>2}: derived {d:>14,.1f}  plan new {p['new']:>16,.3f}  {'OK ' if ok else 'DIFF'} (live old {p['old']})")
                    else:
                        ok = lv is not None and abs(d - lv) <= 1.01
                        lines.append(f"  item {n:>2}: derived {d:>14,.1f}  not in plan, live {lv}  {'same' if ok else 'DIFFERS FROM LIVE'}")
    (HERE / "evidence_pl_notes.json").write_text(json.dumps(allres, ensure_ascii=False, indent=1, default=str), encoding="utf-8", newline="\n")
    (HERE / "evidence_pl_notes.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))
