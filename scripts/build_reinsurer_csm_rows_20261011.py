# -*- coding: utf-8 -*-
"""Reinsurer branches (KR1101~KR1107): staging tables -> master rows for CSM_amortization / CSM_sensitivity.

Input : data/_derived/reinsurer_ifrs17_csm_20261011/tables.json  (scripts/extract_reinsurer_csm_tables_20261011.py)
Output: data/_derived/reinsurer_ifrs17_csm_20261011/rows_amortization.json
        data/_derived/reinsurer_ifrs17_csm_20261011/rows_sensitivity.json
        data/_derived/reinsurer_ifrs17_csm_20261011/rows_waterfall.json   (needs audit_tables.json, see the extract script)
        data/_derived/reinsurer_ifrs17_csm_20261011/build_report.json   (decisions, conflicts, checks)
No master is touched here; load_reinsurer_csm_masters_20261011.py applies the rows (guarded, additive).

Rules applied (owner decisions 2026-10-09/10, docs/archive/handoff_20261008_reinsurer_pipeline.md section 7):
  1. same (company, year) in several filings that really differ -> take the LATEST filing's prior-year column,
     both values are recorded in build_report.json;
  2. a pure rounding difference is no conflict -> take the more precise value (백만원 print beats 억원 integer);
  3. nothing is guessed: a cell that cannot be read with its sign is left empty and says why in 비고.

Run:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/build_reinsurer_csm_rows_20261011.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "data" / "_derived" / "reinsurer_ifrs17_csm_20261011"
sys.stdout.reconfigure(encoding="utf-8")

CODES = ["KR1101", "KR1102", "KR1103", "KR1104", "KR1105", "KR1106", "KR1107"]
FILINGS = ["FY2024_Q4", "FY2025_Q4"]            # oldest first
UNIT_FACTOR = {"억원": 1.0, "백만원": 0.01, "천원": 0.00001}
DASHES = {"-", "\u2013", "\u2014", "\u2212", "\uff0d"}
SUM_TOL = {"억원": 4.0, "백만원": 3.0}          # printed units: |sum(buckets) - total| allowed (cell rounding)
P462_TOL_EOK = 3.0
# KR1103 (제네럴재보험) prints every sensitivity figure as a positive number, also in the 2023/2024/2025 tables,
# although the same document prints negatives in parentheses elsewhere. The direction of CSM / profit effect is
# therefore not printed -> values stay empty and the printed magnitudes go to 비고 (rule: no guessed signs).
UNSIGNED_SENS = {"KR1103"}
# KR1106 (스코리) prints the 당기손익 column as a LOSS AMOUNT (+ = loss). Proof is in the table itself: for every
# row of every KR1106 table (FY2024 and FY2025 filings) 이행현금흐름 + 보험계약마진 - 당기손익 + 기타포괄손익 = 0
# (+-2) holds, while the usual 이행현금흐름 + 보험계약마진 + 당기손익 + 기타포괄손익 = 0 fails by up to 1,720
# (s15_identity_audit.py). The master stores the effect on profit (loss = negative), so the printed sign is reversed.
PL_SIGN_REVERSED = {"KR1106": "원문 당기손익은 손실=(+) 표기라 부호 반전 적재(이행현금흐름+CSM-당기손익+OCI=0 확인)"}
# extra 비고 text for a (company, year) table that the reader should treat with care
SENS_EXTRA_FLAGS = {
    ("KR1107", 2024): "FY2025 공시 전기 열의 행 배열이 FY2024 원본과 한 행 어긋나 보임(해지율 상승·하락 부호가 당기와 반대, 사업비 행 0) — 규칙대로 최신 공시 채택, 검증 대상",
}
RESID_TOL = 2.0          # four printed integers can be off by 0.5 each
# tables that are printed but not usable: (code, year) -> reason. They are listed in build_report.json, not loaded.
SKIP_SENS = {
    ("KR1104", 2023): "FY2024 공시 2023 열: 당기손익·기타포괄손익이 이행현금흐름 변동보다 크고(예 사망률 +4.35 대 -20.70) "
                      "어느 부호 규약으로도 항등식이 안 닫히며 기준 CSM 261.75 도 4-6-2 의 254.77 과 다르다",
}


def tok_to_num(s: str):
    t = s.strip().replace("\u3000", "")
    if t in DASHES:
        return None, "dash"
    t2 = t.replace("\u2212", "-").replace("\u2013", "-")
    neg = False
    if t2.startswith("(") and t2.endswith(")"):
        neg, t2 = True, t2[1:-1]
    elif t2.startswith("-"):
        neg, t2 = True, t2[1:]
    t2 = t2.replace(",", "")
    if not re.fullmatch(r"\d+(\.\d+)?", t2):
        return None, None
    v = float(t2)
    if v == 0.0 and neg:
        return 0.0, "neg0"
    return (-v if neg else v), ""


def r2(x):
    return None if x is None else round(x + 0.0, 2)


def load_meta():
    rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    meta = {}
    for r in rows:
        c = r.get("원보험사코드")
        if c in CODES and c not in meta:
            meta[c] = (r["원수사명"], r["티커"], r["생손보여부"])
    return meta


# ============================================================================================
# 4-6-3 (2)  CSM amortization
# ============================================================================================
def nums_of(toks):
    out = []
    for t in toks:
        v, f = tok_to_num(t)
        if f is None:
            return None
        out.append(0.0 if v is None else v)
    return out


def pick_total(tb):
    """-> (printed numbers list, method) for a table with a printed 합계 row, or (None, reason)."""
    tr = tb.get("total_row")
    if not tr:
        return None, "no_total_row"
    tol = SUM_TOL.get(tb["unit"], 4.0)
    for key in ("A", "B"):
        toks = tr.get(key)
        if not toks or len(toks) not in (14, 15, 16):
            continue
        x = nums_of(toks)
        if x is None:
            continue
        if abs(sum(x[:-1]) - x[-1]) <= tol:
            return (x, toks), f"row_{key}"
    return None, "total_row_failed_checks"


def sched_from_tables(tbs, filing, year):
    """One schedule (company-year) from the tables of that year in one filing.
    Several segments (생명/손해) -> bucket-wise sum; no printed 합계 -> sum of the portfolio rows."""
    unit = next((t["unit"] for t in tbs if t["unit"]), None)
    if unit is None:
        return {"error": "unit not found", "unit": None}
    for t in tbs:
        t["unit"] = t["unit"] or unit
    parts, methods, pages = [], [], []
    for tb in tbs:
        got, how = pick_total(tb)
        if got is None and how == "no_total_row":
            rows = [d for d in tb["data_rows"] if len(d["toks"]) == 16 and nums_of(d["toks"]) is not None]
            if not rows:
                return None
            x = [sum(c) for c in zip(*[nums_of(d["toks"]) for d in rows])]
            if abs(sum(x[:-1]) - x[-1]) > SUM_TOL.get(unit, 4.0) + 1:
                return {"error": "row sum fails identity", "unit": unit}
            parts.append(x)
            methods.append(f"sum_of_{len(rows)}_rows")
            pages.append([d["page"] for d in rows][0])
        elif got is None:
            return {"error": how, "unit": unit}
        else:
            parts.append(got[0])
            methods.append(how)
            pages.append(tb["total_row"]["page"])
    n = {len(p) for p in parts}
    if len(n) != 1:
        return {"error": "segment bucket structure differs", "unit": unit}
    x = [sum(c) for c in zip(*parts)]
    f = UNIT_FACTOR[unit]
    ntok = len(x)
    return {"filing": filing, "year": year, "unit": unit, "methods": methods, "pages": sorted(set(pages)),
            "segments": [tb["segment"] for tb in tbs], "n_buckets": ntok - 1,
            "printed": x, "y": [r2(v * f) for v in x[:10]], "total_eok": r2(x[-1] * f),
            "sum_diff_printed": round(sum(x[:-1]) - x[-1], 3)}


def p462_csm(tbs, year):
    """CSM (일반모형 + 변동수수료) total of the 4-6-2 합계 row(s) in 억원, summed over segments."""
    tot, parts = 0.0, 0
    for tb in tbs:
        tr = tb.get("total_row")
        if not tr:
            continue
        toks = tr["toks"]
        if len(toks) < 3:
            continue
        f = UNIT_FACTOR[tb["unit"]]
        v = tok_to_num(toks[2])[0]
        if v is None:
            continue
        csm = v
        if len(toks) >= 6:                       # 변동수수료접근법 CSM column
            vv = tok_to_num(toks[5])[0]
            if vv:
                csm += vv
        tot += csm * f
        parts += 1
    return (r2(tot) if parts == len(tbs) and parts else None)


def has_decimals(v) -> bool:
    return v is not None and abs(v - round(v)) > 1e-9


def cell_rel(x, y):
    """older value x vs newer value y -> 'same' | 'round' (one is the rounded print of the other) | 'diff'.

    A blank/dash against 0 is the same nil. Two integers (or two decimal prints) that differ are a real difference.
    """
    if x is None and y is None:
        return "same"
    if x is None or y is None:
        other = y if x is None else x
        return "same" if abs(other) < 1e-9 else "diff"
    if abs(x - y) < 1e-9:
        return "same"
    if has_decimals(x) != has_decimals(y) and abs(x - y) <= 0.5 + 1e-9:
        return "round"
    return "diff"


def compare_lists(xs, ys):
    """-> ('same'|'rounding'|'conflict', [(idx, old, new), ...] of the cells that are not 'same'/nil)"""
    rel = [(i, x, y, cell_rel(x, y)) for i, (x, y) in enumerate(zip(xs, ys))]
    bad = [(i, x, y) for i, x, y, r in rel if r == "diff"]
    if bad:
        return "conflict", bad
    rnd = [(i, x, y) for i, x, y, r in rel if r == "round"]
    if rnd:
        return "rounding", rnd
    return "same", []


def same_or_rounding(a, b):
    """schedules a (older filing) and b (newer)"""
    return compare_lists(a["y"] + [a["total_eok"]], b["y"] + [b["total_eok"]])


def precision_score(vals):
    return sum(1 for v in vals if has_decimals(v))


def build_amort(T, meta, report):
    rows, prov = [], []
    amort = T["amort"]
    for code in CODES:
        cands = {}                                   # year -> [sched (oldest filing first)]
        for fy in FILINGS:
            doc = amort.get(f"{code}|{fy}", {})
            years = sorted({t["year"] for t in doc.get("tables", []) if t["year"]})
            for y in years:
                tbs = [t for t in doc["tables"] if t["year"] == y and (t.get("total_row") or t.get("data_rows"))]
                if not tbs:
                    continue
                s = sched_from_tables(tbs, fy, y)
                if s is None:
                    report["amort_unreadable"].append({"code": code, "filing": fy, "year": y})
                    continue
                if "error" in s:
                    report["amort_unreadable"].append({"code": code, "filing": fy, "year": y, "error": s["error"]})
                    continue
                s["pdf"] = doc["pdf"]
                cands.setdefault(y, []).append(s)
        for y in sorted(cands):
            cs = cands[y]
            chosen, note, conflict = cs[-1], None, None
            if len(cs) >= 2:
                kind, diffs = same_or_rounding(cs[0], cs[-1])
                if kind == "same":
                    note = "다른 공시와 동일"
                elif kind == "rounding":
                    old_s, new_s = cs[0]["y"] + [cs[0]["total_eok"]], cs[-1]["y"] + [cs[-1]["total_eok"]]
                    chosen = cs[0] if precision_score(old_s) > precision_score(new_s) else cs[-1]
                    note = "반올림 차이(상충 아님): 더 정밀한 값 채택"
                else:
                    conflict = {"older": cs[0]["filing"], "newer": cs[-1]["filing"], "diffs": diffs,
                                "older_y": cs[0]["y"], "older_total": cs[0]["total_eok"],
                                "newer_y": cs[-1]["y"], "newer_total": cs[-1]["total_eok"]}
                    note = "공시 간 상충: 최신 공시 전기 칸 채택"
                    report["amort_conflicts"].append({"code": code, "year": y, **conflict})
            # cross-check with 4-6-2 (prefer the newest filing that has the year)
            chk = None
            for fy in reversed(FILINGS):
                doc = T["p462"].get(f"{code}|{fy}", {})
                tbs = [t for t in doc.get("tables", []) if t["year"] == y]
                v = p462_csm([t for t in tbs if t.get("total_row")][: (2 if code == "KR1102" else 1)], y) if tbs else None
                if v is not None:
                    chk = {"filing": fy, "csm_eok": v, "diff": r2(chosen["total_eok"] - v)}
                    break
            nm, tk, sb = meta[code]
            q = f"{y}.4Q"
            for i in range(10):
                rows.append({"원보험사코드": code, "원수사명": nm, "티커": tk, "생손보여부": sb,
                             "공시분기": q, "경과차년": i + 1, "상각액": chosen["y"][i]})
            prov.append({"code": code, "quarter": q, "filing": chosen["filing"], "pdf": chosen["pdf"],
                         "pages": chosen["pages"], "unit": chosen["unit"], "methods": chosen["methods"],
                         "segments": chosen["segments"], "total_eok": chosen["total_eok"],
                         "sum_diff_printed": chosen["sum_diff_printed"], "decision": note,
                         "p462_check": chk, "tail_buckets_in_filing": chosen["n_buckets"] - 10,
                         "precision": "억원 정수 공시" if chosen["unit"] == "억원" else "백만원 공시(억원 환산 소수 2자리)"})
            if chk is not None and abs(chk["diff"]) > max(P462_TOL_EOK, 0.001 * chosen["total_eok"]):
                report["amort_p462_mismatch"].append({"code": code, "quarter": q, "amort_total": chosen["total_eok"], **chk})
    return rows, prov


# ============================================================================================
# 4-6-5 (1)  sensitivity
# ============================================================================================
STD_LEVEL = ["3.27% 증가", "3.40% 증가", "2.62% 증가", "4.19% 증가", "9.16% 증가", "9.16% 감소", "2.62% 증가", "0.26%p 증가"]
RISK_ORDER = ["사망률", "장해질병(정액보상)", "장해질병(실손보상)", "장기재물기타", "해지율(상승)", "해지율(하락)",
              "사업비(수준)", "사업비(인플레이션)"]


def sens_grid(tb):
    """-> dict(slots=[8 x dict(vals=[fcf,csm,pl,oci], states=[...]) | None], merged={(1,2):bool,(6,7):bool}, errors=[...])"""
    a = tb.get("row_centers") or []
    if len(a) != 8:
        return {"error": f"row_centers={len(a)}"}
    cols = tb["cols"]
    nmain = min(3, len(cols))
    main = [(ci, y, t) for ci in range(nmain) for (y, t) in cols[ci]["toks"]]
    oci = [(y, t) for (y, t) in cols[3]["toks"]] if len(cols) >= 4 else []
    bounds = row_bounds(a)                                                    # row k spans [bounds[k], bounds[k+1])
    groups = []
    for ci, y, t in sorted(main, key=lambda m: m[1]):
        if groups and y - groups[-1]["y"] <= 12 and not any(m[0] == ci for m in groups[-1]["m"]):
            groups[-1]["m"].append((ci, y, t))
            groups[-1]["y"] = sum(m[1] for m in groups[-1]["m"]) / len(groups[-1]["m"])
        else:
            groups.append({"y": y, "m": [(ci, y, t)], "o": []})
    for y, t in oci:
        near = min(groups, key=lambda g: abs(g["y"] - y), default=None)
        if near is not None and abs(near["y"] - y) <= 30 and not near["o"]:
            near["o"].append((y, t))
        else:
            groups.append({"y": y, "m": [], "o": [(y, t)]})
    groups.sort(key=lambda g: g["y"])

    def row_of(y):
        for k in range(8):
            if bounds[k] <= y < bounds[k + 1]:
                return k
        return None

    def assign_by_geometry():
        slot_g, merged, errors, used = [None] * 8, {}, [], set()
        for (i, j) in ((1, 2), (6, 7)):
            lo, hi = bounds[i], bounds[j + 1]
            gs = [g for g in groups if lo <= g["y"] < hi]
            if len(gs) == 1:                                  # one value block for the pair = merged cell
                slot_g[i] = slot_g[j] = gs[0]
                merged[(i, j)] = True
                used.add(id(gs[0]))
            elif len(gs) == 2:
                merged[(i, j)] = False
                slot_g[i], slot_g[j] = gs[0], gs[1]
                used.update(id(g) for g in gs)
            elif len(gs) == 0:
                merged[(i, j)] = False
            else:
                merged[(i, j)] = False
                errors.append(f"pair {(i, j)}: {len(gs)} groups")
        for k in (0, 3, 4, 5):
            for g in groups:
                if id(g) not in used and row_of(g["y"]) == k:
                    if slot_g[k] is None:
                        slot_g[k] = g
                        used.add(id(g))
                    else:
                        errors.append(f"slot {k}: two groups")
        for g in groups:
            if id(g) not in used:
                errors.append(f"unassigned group y={g['y']:.1f} {[m[2] for m in g['m']]} {[o[1] for o in g['o']]}")
        return slot_g, merged, errors

    slot_g, merged, errors = assign_by_geometry()
    how = "geometry"
    if errors:                                                # fallback: by group count (8 = all separate, 6 = both pairs merged)
        n = len(groups)
        if n == 8:
            slot_g, merged, errors, how = list(groups), {(1, 2): False, (6, 7): False}, [], "count8"
        elif n == 6:
            slot_g = [groups[0], groups[1], groups[1], groups[2], groups[3], groups[4], groups[5], groups[5]]
            merged, errors, how = {(1, 2): True, (6, 7): True}, [], "count6"

    def cell(g, idx):
        if g is None:
            return None, "blank"
        if idx < 3:
            for ci, y, t in g["m"]:
                if ci == idx:
                    v, f = tok_to_num(t)
                    return v, ("dash" if f == "dash" else ("neg0" if f == "neg0" else "num"))
            return None, "blank"
        if g["o"]:
            v, f = tok_to_num(g["o"][0][1])
            return v, ("dash" if f == "dash" else ("neg0" if f == "neg0" else "num"))
        return None, "blank"

    slots = []
    for k in range(8):
        g = slot_g[k]
        vals, states = [], []
        for idx in range(4):
            v, st = cell(g, idx)
            if len(cols) < 4 and idx == 3:
                st = "nocol"
            vals.append(v)
            states.append(st)
        slots.append({"vals": vals, "states": states})
    for (i, j) in ((1, 2), (6, 7)):                         # the same 4 values printed on both rows = one merged cell
        if not merged.get((i, j)) and slots[i]["vals"] == slots[j]["vals"] and any(v is not None for v in slots[i]["vals"]):
            merged[(i, j)] = True
    return {"slots": slots, "merged": {f"{i}{j}": v for (i, j), v in merged.items()}, "errors": errors, "how": how}


def row_bounds(a):
    """row k spans [b[k], b[k+1]) -- midpoints between the row centres, ends extended by half a pitch"""
    b = [a[0] - (a[1] - a[0]) / 2.0] + [(a[k - 1] + a[k]) / 2.0 for k in range(1, 8)] + [a[7] + (a[7] - a[6]) / 2.0]
    return b


def level_text(tb, k):
    """shock level of row k as printed (first pct token inside the row span); falls back to the standard text."""
    bounds = row_bounds(tb["row_centers"])
    toks = [t for y, t in tb.get("pcts", []) if bounds[k] <= y < bounds[k + 1]]
    if not toks:
        return STD_LEVEL[k], False
    t = toks[0]
    base = STD_LEVEL[k]
    # e.g. '3.27%' -> add direction word of the standard text; keep the printed number
    num = re.match(r"^\d+(\.\d+)?%p?", t).group(0)
    word = "" if num.endswith("p") and k == 7 else " " + base.split(" ")[-1]
    return (num + word).replace("%p 증가", "%p 증가"), True


def sens_candidates(T, code):
    out = {}
    for fy in FILINGS:
        doc = T["sens"].get(f"{code}|{fy}", {})
        for tb in doc.get("tables", []):
            if not tb["year"] or not tb.get("cols") or len(tb.get("labels", [])) != 8:
                continue
            g = sens_grid(tb)
            if "error" in g:
                continue
            unit = tb["unit"] or next((t["unit"] for t in doc["tables"] if t["unit"]), None)
            out.setdefault(tb["year"], []).append({"filing": fy, "pdf": doc["pdf"], "tb": tb, "grid": g, "unit": unit})
    return out


def grid_numbers(c):
    f = UNIT_FACTOR[c["unit"]]
    res = []
    for s in c["grid"]["slots"]:
        res.append([None if v is None else r2(v * f) for v in s["vals"]])
    return res


def compare_sens(a, b):
    """-> kind in same|rounding|conflict, list of (slot, col, old, new) that differ.

    Blank vs '-' vs 0 count as the same nil. Merged cells repeat their value on both rows, so a table that
    prints the value on both rows is compared with a table that prints it once on the pair's first row only
    when the second row is empty on one side."""
    ga, gb = grid_numbers(a), grid_numbers(b)
    ma, mb = a["grid"]["merged"], b["grid"]["merged"]
    xs, ys, idx = [], [], []
    for k in range(8):
        pair = {2: "12", 7: "67"}.get(k)
        if pair and bool(ma.get(pair)) != bool(mb.get(pair)):
            continue            # one side prints the pair as ONE merged cell: slot k is only a copy of slot k-1
        for ci in range(4):
            xs.append(ga[k][ci])
            ys.append(gb[k][ci])
            idx.append((k, ci))
    kind, bad = compare_lists(xs, ys)
    return kind, [(idx[i][0], idx[i][1], x, y) for i, x, y in bad]


def amort_note_in_definition(foot: str) -> bool:
    return "상각" in (foot or "")


def sens_rows_for(code, year, c, meta, conflict_note, extra_flags):
    nm, tk, sb = meta[code]
    f = UNIT_FACTOR[c["unit"]]
    tb, g = c["tb"], c["grid"]
    fy_label = "FY" + c["filing"][2:6]
    unit_label = "억원 정수" if c["unit"] == "억원" else "백만원"
    base_note = f"재보사 경영공시 {fy_label} 4-6-5 ①({unit_label}); 자본영향=당기손익+기타포괄손익(세전)"
    if amort_note_in_definition(tb.get("footnote")) and re.search(r"상각[^.]{0,20}(변동|감소|포함)", tb.get("footnote", "")):
        base_note += "; 당기손익 정의에 CSM 상각 변동 포함(원문 주2)"
    q, asof = f"{year}.4Q", f"{year}-12-31"
    slots = g["slots"]
    rows = []

    def build_row(k_list, label, level, merged_note):
        # values come from the first slot of the group
        k = k_list[0]
        s = slots[k]
        flags = []
        vals = s["vals"]
        st = s["states"]
        fcf, csm, pl, oci = [None if v is None else r2(v * f) for v in vals]
        for nm_, v_, st_ in (("이행현금흐름", fcf, st[0]), ("보험계약마진", csm, st[1]), ("당기손익", pl, st[2]), ("기타포괄손익", oci, st[3])):
            if st_ == "neg0":
                flags.append(f"원문 {nm_} (0)=소수 반올림된 음수")
        if all(x in ("dash", "blank", "nocol") for x in st[:3]) and all(x in ("dash", "blank", "nocol") for x in st):
            flags.append("원문 공란/'-' (값 없음)")
        unsigned_note = None
        if code in PL_SIGN_REVERSED and pl is not None:
            pl = 0.0 if pl == 0 else r2(-pl)
            flags.append(PL_SIGN_REVERSED[code])
        if code in UNSIGNED_SENS:
            parts_ = [("이행현금흐름", fcf), ("보험계약마진", csm), ("당기손익", pl)]
            shown = "·".join(f"{n_} {v_:g}" for n_, v_ in parts_ if v_ is not None)
            unsigned_note = ("원문 부호 미표기(모든 값이 양수로 인쇄돼 방향 미확정, 값 비움): " + shown) if shown else None
            csm, pl, oci = None, None, None
        # equity effect
        eq = None
        if code in UNSIGNED_SENS:
            eq = None
        elif st[2] in ("num", "neg0") and st[3] in ("num", "neg0", "dash"):
            eq = r2((pl or 0.0) + (oci or 0.0))
        elif st[2] == "dash" and st[3] in ("num", "neg0"):
            eq = r2(oci or 0.0)
        # the issuer's own table identity 이행현금흐름 + CSM + 당기손익 + 기타포괄손익 = 0 (after the sign reversal); a residual
        # beyond the rounding of four printed integers is the issuer's inconsistency: load as printed, say so in the note
        if code not in UNSIGNED_SENS and None not in (fcf, csm, pl) and st[3] != "nocol":
            resid = fcf + csm + pl + (oci or 0.0)
            if abs(resid) > RESID_TOL:
                flags.append(f"발행사 표 항등식 잔차 {resid:+g}(이행현금흐름+CSM+당기손익+기타포괄손익, 공시 그대로 적재)")
        note = base_note
        if unsigned_note:
            note += f"; {unsigned_note}"
        elif fcf is not None:
            note += f"; 원문 이행현금흐름 변동 {fcf:g}"
        if st[3] == "nocol":
            note += "; 원문에 기타포괄손익 열 없음(자본영향 미산출)"
        if merged_note:
            note += f"; {merged_note}"
        if flags:
            note += "; " + "; ".join(flags)
        if conflict_note:
            note += f"; {conflict_note}"
        for e in extra_flags:
            note += f"; {e}"
        return {"원보험사코드": code, "원수사명": nm, "티커": tk, "생손보여부": sb, "공시분기": q, "기준일": asof,
                "순번": 0, "위험구분": label, "충격수준": level,
                "CSM변동": csm, "당기손익영향": pl, "자본영향": eq, "비고": note}

    lv = [level_text(tb, k)[0] for k in range(8)]
    rows.append(build_row([0], RISK_ORDER[0], lv[0], None))
    if g["merged"].get("12"):
        rows.append(build_row([1], "장해질병(정액보상+실손보상)", f"정액 {lv[1].replace(' 증가', '')} & 실손 {lv[2]}",
                              "병합셀: 정액·실손 합산 1행"))
    else:
        rows.append(build_row([1], RISK_ORDER[1], lv[1], None))
        rows.append(build_row([2], RISK_ORDER[2], lv[2], None))
    rows.append(build_row([3], RISK_ORDER[3], lv[3], None))
    rows.append(build_row([4], RISK_ORDER[4], lv[4], None))
    rows.append(build_row([5], RISK_ORDER[5], lv[5], None))
    if g["merged"].get("67"):
        rows.append(build_row([6], "사업비(수준+인플레이션)", f"수준 {lv[6]} / 인플레이션 {lv[7].replace(' 증가', '')}",
                              "병합셀: 수준·인플레이션 합산 1행"))
    else:
        rows.append(build_row([6], RISK_ORDER[6], lv[6], None))
        rows.append(build_row([7], RISK_ORDER[7], lv[7], None))
    for i, r in enumerate(rows, 1):
        r["순번"] = i
    return rows


def build_sens(T, meta, report):
    out, prov = [], []
    for code in CODES:
        cands = sens_candidates(T, code)
        for year in sorted(cands):
            cs = cands[year]
            if (code, year) in SKIP_SENS:
                report.setdefault("sens_skipped", []).append({"code": code, "year": year, "reason": SKIP_SENS[(code, year)]})
                continue
            chosen, cnote, extra = cs[-1], None, ([SENS_EXTRA_FLAGS[(code, year)]] if (code, year) in SENS_EXTRA_FLAGS else [])
            if len(cs) >= 2:
                kind, diffs = compare_sens(cs[0], cs[-1])
                if kind == "same":
                    pass
                elif kind == "rounding":
                    sa = [v for r in grid_numbers(cs[0]) for v in r]
                    sb_ = [v for r in grid_numbers(cs[-1]) for v in r]
                    chosen = cs[0] if precision_score(sa) > precision_score(sb_) else cs[-1]
                else:
                    cnote = "공시 간 상충: 최신 공시 전기 칸 채택(옛 값은 FY%s 공시)" % cs[0]["filing"][2:6]
                    report["sens_conflicts"].append({
                        "code": code, "year": year, "older": cs[0]["filing"], "newer": cs[-1]["filing"],
                        "n_diffs": len(diffs), "diffs": [(RISK_ORDER[d[0]], ["이행현금흐름", "보험계약마진", "당기손익", "기타포괄손익"][d[1]], d[2], d[3]) for d in diffs][:40]})
            if chosen["grid"]["errors"]:
                report["sens_grid_errors"].append({"code": code, "year": year, "filing": chosen["filing"], "errors": chosen["grid"]["errors"]})
            rows = sens_rows_for(code, year, chosen, meta, cnote, extra)
            out.extend(rows)
            prov.append({"code": code, "quarter": f"{year}.4Q", "filing": chosen["filing"], "pdf": chosen["pdf"],
                         "page": chosen["tb"].get("page"), "unit": chosen["unit"], "merged": chosen["grid"]["merged"],
                         "base": chosen["tb"].get("base"), "decision": cnote or "단일 원천 또는 동일 값",
                         "footnote": chosen["tb"].get("footnote", "")[:400], "n_rows": len(rows)})
    return out, prov


# ============================================================================================
# CSM_waterfall  (audit-report roll-forward, 수재 일반모형)
# ============================================================================================
WF_NAMES = {1: "기초 CSM", 2: "신계약 CSM", 3: "이자 부리", 4: "가정 및 경험 조정", 5: "CSM 상각", 6: "기말 CSM"}
WF_TOL_EOK = 2e-5            # 1 천원 = 1e-5 억원; two prints of the same figure may differ by a unit rounding
# company-years that are NOT loaded although the audit report prints them, with the reason (reported, not hidden)
WF_SKIP = {
    ("KR1107", 2023): "2023.1.1 영업양수도 개시연도: 기초 0 이고 이전 유입 약 1,069억이 어느 항목에도 없어 잔차(가정 및 경험 조정)가 "
                      "가정 변동이 아닌 포트폴리오 이전분을 담게 된다",
}


def wf_values(t):
    f = t["factor_to_eok"]
    if f is None or t.get("open") is None or t.get("close") is None:
        return None
    new = sum(t["new"]) if t["new"] else None
    amort = sum(t["amort"]) if t["amort"] else None
    inter = t.get("interest")
    if new is None or amort is None or inter is None:
        return None
    return {"open": t["open"] * f, "new": new * f, "interest": inter * f, "amort": amort * f, "close": t["close"] * f}


def wf_partial(t):
    f = t["factor_to_eok"]
    if f is None:
        return {}
    out = {}
    for k, key in (("open", "open"), ("close", "close"), ("interest", "interest")):
        if t.get(key) is not None:
            out[k] = t[key] * f
    if t["new"]:
        out["new"] = sum(t["new"]) * f
    if t["amort"]:
        out["amort"] = sum(t["amort"]) * f
    return out


def build_wf(meta, report):
    path = STAGE / "audit_tables.json"
    if not path.exists():
        return [], []
    A = json.loads(path.read_text(encoding="utf-8"))["tables"]
    rows, prov = [], []
    for code in CODES:
        by_year = {}
        for t in A:
            if t["code"] == code and t["year"] and t["year"] >= 2023:
                by_year.setdefault(t["year"], []).append(t)
        for year in sorted(by_year):
            cs = sorted(by_year[year], key=lambda t: t["filing"])           # oldest filing first
            if (code, year) in WF_SKIP:
                report.setdefault("wf_skipped", []).append({"code": code, "year": year, "reason": WF_SKIP[(code, year)]})
                continue
            full = [(t, wf_values(t)) for t in cs if wf_values(t) is not None]
            if not full:
                report.setdefault("wf_unreadable", []).append({"code": code, "year": year})
                continue
            chosen_t, chosen_v = full[-1]
            note = None
            others = [t for t in cs if t is not chosen_t and wf_partial(t)]
            if others:
                older = others[0]
                po = wf_partial(older)
                diffs = {k: (po[k], chosen_v[k]) for k in po if k in chosen_v and abs(po[k] - chosen_v[k]) > WF_TOL_EOK}
                if diffs:
                    note = "공시 간 상충: 최신 공시 전기 칸 채택"
                    report.setdefault("wf_conflicts", []).append({
                        "code": code, "year": year, "older": older["filing"], "newer": chosen_t["filing"],
                        "diffs_eok": {k: [round(a, 5), round(b, 5)] for k, (a, b) in diffs.items()}})
                else:
                    note = "다른 공시와 동일"
            v = chosen_v
            resid = v["close"] - v["open"] - v["new"] - v["interest"] - v["amort"]
            vals = {1: v["open"], 2: v["new"], 3: v["interest"], 4: resid, 5: v["amort"], 6: v["close"]}
            nm, tk, sb = meta[code]
            q = f"{year}.4Q"
            for k in range(1, 7):
                rows.append({"원보험사코드": code, "원수사명": nm, "티커": tk, "생손보여부": sb, "항목번호": k,
                             "항목명": WF_NAMES[k], "공시분기": q, "값": round(vals[k], 5),
                             "값_당분기": round(vals[6], 5) if k == 6 else None})
            # check against 4-6-2 (newest filing that has the year)
            chk = None
            for fy in reversed(FILINGS):
                doc = report["_T"]["p462"].get(f"{code}|{fy}", {})
                tbs = [t for t in doc.get("tables", []) if t["year"] == year and t.get("total_row")]
                val = p462_csm(tbs[: (2 if code == "KR1102" else 1)], year) if tbs else None
                if val is not None:
                    chk = {"filing": fy, "csm_eok": val, "diff": r2(v["close"] - val)}
                    break
            if chk is not None and abs(chk["diff"]) > max(3.0, 0.002 * abs(v["close"])):
                report.setdefault("wf_p462_mismatch", []).append({"code": code, "quarter": q, "audit_close": r2(v["close"]), **chk})
            expl = None
            if chosen_t["adj"]:
                expl = round(sum(chosen_t["adj"]) * chosen_t["factor_to_eok"], 5)
            prov.append({"code": code, "quarter": q, "filing": chosen_t["filing"], "pdf": chosen_t["pdf"], "pages": chosen_t["pages"],
                         "unit": chosen_t["unit"], "unit_source": chosen_t.get("unit_source"), "decision": note,
                         "item4_residual_eok": round(resid, 5), "explicit_csm_adjusting_rows_eok": expl,
                         "interest_row": chosen_t["interest_key"], "p462_check": chk,
                         "amort_abs_eok": round(abs(v["amort"]), 5)})
    # continuity: closing of year y vs opening of y+1 as loaded
    by = {(r["원보험사코드"], r["공시분기"], r["항목번호"]): r["값"] for r in rows}
    for code in CODES:
        for y in range(2023, 2026):
            c, o = by.get((code, f"{y}.4Q", 6)), by.get((code, f"{y + 1}.4Q", 1))
            if c is not None and o is not None and abs(c - o) > max(0.005 * abs(c), 2.0):
                report.setdefault("wf_continuity_break", []).append({"code": code, "year": y, "close": c, "next_open": o})
    return rows, prov


def main() -> int:
    T = json.loads((STAGE / "tables.json").read_text(encoding="utf-8"))
    meta = load_meta()
    report = {"amort_conflicts": [], "amort_unreadable": [], "amort_p462_mismatch": [],
              "sens_conflicts": [], "sens_grid_errors": []}
    report["_T"] = T
    arows, aprov = build_amort(T, meta, report)
    srows, sprov = build_sens(T, meta, report)
    wrows, wprov = build_wf(meta, report)
    report.pop("_T")
    report["wf_provenance"] = wprov
    report["amort_provenance"] = aprov
    report["sens_provenance"] = sprov
    (STAGE / "rows_amortization.json").write_text(json.dumps(arows, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    (STAGE / "rows_sensitivity.json").write_text(json.dumps(srows, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    if wrows:
        (STAGE / "rows_waterfall.json").write_text(json.dumps(wrows, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    (STAGE / "build_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(f"amortization rows {len(arows)} ({len(aprov)} company-quarters); sensitivity rows {len(srows)} ({len(sprov)} company-quarters)")
    print("amort conflicts", len(report["amort_conflicts"]), "| unreadable", len(report["amort_unreadable"]),
          "| p462 mismatch", len(report["amort_p462_mismatch"]))
    print("sens conflicts", len(report["sens_conflicts"]), "| grid errors", len(report["sens_grid_errors"]))
    print(f"waterfall rows {len(wrows)} ({len(wprov)} company-quarters) | conflicts {len(report.get('wf_conflicts', []))} | "
          f"p462 mismatch {len(report.get('wf_p462_mismatch', []))} | continuity breaks {len(report.get('wf_continuity_break', []))} | "
          f"skipped {len(report.get('wf_skipped', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
