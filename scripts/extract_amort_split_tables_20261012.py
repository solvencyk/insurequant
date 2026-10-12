# -*- coding: utf-8 -*-
"""Read the SPLIT CSM-amortisation tables (and Hanwha Life's separate-basis table) straight from the raw DART XML and stage the master cells to fix.

Ticket : inbox/parser/20261012T1020Z__orchestrator__MULTI_2023.4Q-2026.2Q__ifrs17_owner_followups_20261012.md item 6 (owner decision (15)).
Why    : the annual CSM schedule note of Lina / AIA / Chubb / MetLife / BNP Cardif is printed as TWO tables (front: 1~8 years | back: 9~10 years, 11~15 ... 30+, total).
         The panel builder reads only the front table, so CSM_amortization.json 2025.4Q holds y1..y8 and blank y9/y10 for AIA, Chubb, MetLife and BNP Cardif
         (Lina's 2025.4Q was already completed from the disclosure PDF).  Hanwha Life's master rows come from the CONSOLIDATED table (88,752억) although the
         master's closing CSM (87,136.5억) is on the separate basis.

What it does (read-only on the repository; writes staging files into data/_derived/ifrs17_owner_followups_20261012/):
  * for every company: finds the issued-contract schedule tables of the SEPARATE filing (<rcept>_00760.xml) and of the consolidated filing if one exists,
    pairs front/back tables in document order (first pair = current year-end, second pair = prior year-end; the same rule the 2026-10-11 twin fix proved on 64 pairs),
  * identities: row-wise  sum(front y1..y8) + sum(back buckets) == back total  for every portfolio row; current total / unit == master closing CSM 2025.4Q (item 6);
    prior total / unit == master closing CSM 2024.4Q where the master has it; separate == consolidated for the numbers,
  * stages amort_split_spec.json (cells to write, old-value guards) and amort_split_evidence.json / .md (all numbers, the identity table).

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/extract_amort_split_tables_20261012.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from viz_build_ifrs17_panels import _year_bucket_cell, parse_num  # noqa: E402

OUT = ROOT / "data" / "_derived" / "ifrs17_owner_followups_20261012"
RAW = ROOT / "data" / "dart" / "FY2025_Q4" / "raw"
QUARTER = "2025.4Q"
# company -> separate xml, consolidated xml (None if the company has only one filing), unit divisor to 억원
SOURCES = [
    dict(code="KR0080", name="에이아이에이생명보험", kind="split",
         sep=RAW / "KR0080_에이아이에이생명보험_20260407002100" / "20260407002100_00760.xml",
         con=RAW / "KR0080_에이아이에이생명보험_20260407002101" / "20260407002101_00761.xml", div=100.0, unit="백만원"),
    dict(code="KR0100", name="처브라이프생명보험", kind="split",
         sep=RAW / "KR0100_처브라이프생명보험_20260408003172" / "20260408003172_00760.xml", con=None, div=100.0, unit="백만원"),
    dict(code="KR0095", name="메트라이프생명보험", kind="split",
         sep=RAW / "KR0095_메트라이프생명보험_20260403003824" / "20260403003824_00760.xml",
         con=RAW / "KR0095_메트라이프생명보험_20260403003825" / "20260403003825_00761.xml", div=1e5, unit="천원"),
    dict(code="KR0075", name="비엔피파리바카디프생명보험", kind="split",
         sep=RAW / "KR0075_비엔피파리바카디프생명보험_20260406004430" / "20260406004430_00760.xml", con=None, div=1e5, unit="천원"),
    dict(code="KR0074", name="라이나생명보험", kind="split",
         sep=RAW / "KR0074_라이나생명보험_20260406004538" / "20260406004538_00760.xml",
         con=RAW / "KR0074_라이나생명보험_20260406004539" / "20260406004539_00761.xml", div=1e5, unit="천원"),
]
HANWHA = dict(code="KR0068", name="한화생명", sep=RAW / "KR0068_한화생명_20260316001304" / "20260316001304_00760.xml",
              con=RAW / "KR0068_한화생명_20260316001304" / "20260316001304_00761.xml", div=100.0, unit="백만원")


def compact(s: str) -> str:
    return re.sub(r"\s+", "", s or "")


def flat_header(t) -> list[str]:
    cells = [c for r in t.header for c in r]
    return cells


def value_cells(row: list[str], n: int) -> list[str]:
    """the last n cells of a body row (the leading 1-2 cells are the 구분/포트폴리오 labels)"""
    return row[-n:]


def issued(t) -> bool:
    cap = t.caption or ""
    return "재보험" not in cap and "출재" not in cap


def classify(t) -> str | None:
    """'front' (header 1년..8년), 'back' (header 9년, 10년, ... 합계/계) or None"""
    hdr = flat_header(t)
    keys = [_year_bucket_cell(c) for c in hdr]
    keys = [k for k in keys]
    if keys[-8:] == ["y1", "y2", "y3", "y4", "y5", "y6", "y7", "y8"] and len(hdr) <= 10:
        return "front"
    if "y9" in keys and "y10" in keys and keys[-1] == "total" and "y1" not in keys:
        return "back"
    return None


def table_rows(t, n_cols: int) -> list[tuple[str, list[float]]]:
    out = []
    for r in t.rows:
        if len(r) < n_cols + 1:
            continue
        label = compact(r[-(n_cols + 1)]) if len(r) >= n_cols + 1 else ""
        vals = []
        for c in r[-n_cols:]:
            v = parse_num(c)
            vals.append(0.0 if v is None else float(v))
        out.append((label, vals))
    return out


def find_pairs(xml: Path) -> list[dict]:
    """document-order list of (front, back) pairs of the ISSUED-contract schedule"""
    fronts, backs = [], []
    for t in _iter_tables_with_context(xml):
        if not issued(t):
            continue
        k = classify(t)
        if k == "front":
            fronts.append(t)
        elif k == "back":
            backs.append(t)
    pairs = []
    for f in fronts:
        b = next((x for x in backs if x.line_no > f.line_no), None)
        if b is not None and b.line_no < f.line_no + 500:
            pairs.append(dict(front=f, back=b))
    return pairs


def schedule(pair: dict) -> dict:
    f, b = pair["front"], pair["back"]
    fh, bh = flat_header(f), flat_header(b)
    fkeys = [_year_bucket_cell(c) for c in fh][-8:]
    bkeys = [_year_bucket_cell(c) for c in bh][-8:]
    assert fkeys == [f"y{i}" for i in range(1, 9)], fkeys
    assert bkeys[:2] == ["y9", "y10"] and bkeys[-1] == "total", bkeys
    frows = table_rows(f, 8)
    brows = table_rows(b, 8)
    assert len(frows) == len(brows), (len(frows), len(brows))
    rows = []
    for (fl, fv), (bl, bv) in zip(frows, brows):
        # the two halves spell a few labels differently ('유배당연금저축' / '유배당연금·저축'): compare without the middle dot
        assert fl.replace("·", "").replace(",", "") == bl.replace("·", "").replace(",", ""), (fl, bl)
        part = fv + bv[:-1]                 # y1..y8, y9, y10, 11-15, 16-20, 21-25, 26-30, 30+
        total = bv[-1]
        rows.append(dict(label=fl, y1_y8=fv, back=bv[:-1], total=total, row_sum=sum(part), row_gap=sum(part) - total))
    tot = next((r for r in rows if r["label"] == "합계"), None)
    assert tot is not None, "no 합계 row"
    return dict(front_line=f.line_no, back_line=b.line_no, front_caption=f.caption[:120], back_header=bh, rows=rows, total_row=tot)


def hanwha_schedule(xml: Path) -> list[dict]:
    """Hanwha Life separate: ONE wide table, header in the first body row, columns 1년 이하 .. 9~10년, 11~15 ... 30년 초과, 합계"""
    out = []
    for t in _iter_tables_with_context(xml):
        if "발행한 보험계약" not in (t.caption or "") or "보험계약마진" not in (t.caption or ""):
            continue
        rows = t.rows
        if not rows or "1년" not in "".join(rows[0]):
            continue
        hdr = rows[0]
        ncol = len(hdr) - 1
        body = []
        for r in rows[1:]:
            if len(r) < ncol:
                continue
            vals = [0.0 if parse_num(c) is None else float(parse_num(c)) for c in r[-ncol:]]
            lab = compact(r[-ncol - 1]) if len(r) > ncol else ""
            body.append((lab, vals))
        tot = next((v for l, v in body if l == "합계"), None)
        out.append(dict(line=t.line_no, caption=t.caption[:160], header=hdr, total=tot, body=body))
    return out


def main() -> int:
    wf = json.loads((ROOT / "CSM_waterfall.json").read_bytes().decode("utf-8"))
    close = {(r["원보험사코드"], r["공시분기"]): r["값"] for r in wf if r["항목번호"] == 6}
    # idempotent: once scripts/load_amort_split_tables_20261012.py has run, the "old" cells are the PRE-APPLY bytes it backed up
    bk = ROOT / "data" / "_derived" / "ifrs17_owner_followups_backup_20261012" / "CSM_amortization.json.pre_amort_split"
    am = json.loads((bk if bk.exists() else ROOT / "CSM_amortization.json").read_bytes().decode("utf-8"))
    master = {}
    for r in am:
        master.setdefault((r["원보험사코드"], r["공시분기"]), {})[r["경과차년"]] = r["상각액"]

    evidence, spec_cells, problems = [], [], []
    for s in SOURCES:
        ev = dict(code=s["code"], name=s["name"], unit=s["unit"], sep_xml=str(s["sep"].relative_to(ROOT)).replace("\\", "/"),
                  con_xml=None if s["con"] is None else str(s["con"].relative_to(ROOT)).replace("\\", "/"))
        sp = find_pairs(s["sep"])
        if len(sp) < 1:
            problems.append(f"{s['code']}: no front/back pair found in the separate filing")
            continue
        cur = schedule(sp[0])
        prior = schedule(sp[1]) if len(sp) > 1 else None
        div = s["div"]
        tot_cur = cur["total_row"]
        close_cur = close.get((s["code"], QUARTER))
        close_prior = close.get((s["code"], "2024.4Q"))
        ev["pairs_found"] = len(sp)
        ev["current"] = dict(front_line=cur["front_line"], back_line=cur["back_line"], rows=cur["rows"])
        ev["prior"] = None if prior is None else dict(front_line=prior["front_line"], back_line=prior["back_line"], total_row=prior["total_row"])
        ev["identity_current_total_eok"] = round(tot_cur["total"] / div, 5)
        ev["master_closing_csm_2025.4Q"] = close_cur
        ev["rel_diff_current_total_vs_closing"] = None if not close_cur else (tot_cur["total"] / div - close_cur) / close_cur
        if prior is not None:
            ev["identity_prior_total_eok"] = round(prior["total_row"]["total"] / div, 5)
            ev["master_closing_csm_2024.4Q"] = close_prior
            ev["rel_diff_prior_total_vs_closing"] = None if not close_prior else (prior["total_row"]["total"] / div - close_prior) / close_prior
        # row-wise identity
        worst = max(abs(r["row_gap"]) for r in cur["rows"])
        ev["row_identity_worst_abs_gap_in_unit"] = worst
        if worst > 3.0:
            problems.append(f"{s['code']}: row identity gap {worst} (unit {s['unit']}) > 3")
        if close_cur is None or abs(tot_cur["total"] / div - close_cur) > max(0.06, 0.0005 * close_cur):
            problems.append(f"{s['code']}: current total {tot_cur['total'] / div:.4f}억 != master closing CSM {close_cur}")
        # consolidated equality
        if s["con"] is not None:
            cp = find_pairs(s["con"])
            if cp:
                ccur = schedule(cp[0])
                same_total = [abs(a - b) < 0.5 for a, b in zip(tot_cur["y1_y8"] + tot_cur["back"], ccur["total_row"]["y1_y8"] + ccur["total_row"]["back"])]
                ev["consolidated"] = dict(front_line=ccur["front_line"], back_line=ccur["back_line"], total_equal_to_separate=bool(all(same_total)),
                                          total_eok=round(ccur["total_row"]["total"] / div, 5),
                                          all_rows_equal=bool(all(
                                              all(abs(x - y) < 0.5 for x, y in zip(r1["y1_y8"] + r1["back"] + [r1["total"]], r2["y1_y8"] + r2["back"] + [r2["total"]]))
                                              for r1, r2 in zip(cur["rows"], ccur["rows"])) and len(cur["rows"]) == len(ccur["rows"])))
            else:
                ev["consolidated"] = dict(note="no front/back pair found")
        # cells
        m = master.get((s["code"], QUARTER), {})
        y = [v / div for v in tot_cur["y1_y8"] + tot_cur["back"][:2]]          # y1..y10 (억원)
        cells = []
        for k in range(1, 11):
            new = round(y[k - 1], 1)
            old = m.get(k)
            cells.append(dict(경과차년=k, old=old, new=new, exact_eok=round(y[k - 1], 5)))
        # front values must equal what the master already holds (same table)
        for c in cells[:8]:
            if s["code"] != "KR0074" and (c["old"] is None or abs(c["old"] - c["new"]) > 0.05):
                problems.append(f"{s['code']} y{c['경과차년']}: master {c['old']} != table {c['new']}")
        if s["code"] == "KR0074":
            for c in cells:
                if c["old"] is None or abs(c["old"] - c["exact_eok"]) > 6e-5:
                    problems.append(f"{s['code']} y{c['경과차년']}: master {c['old']} != DART table {c['exact_eok']} (Lina is expected to be complete already)")
        ev["cells"] = cells
        ev["y11plus_eok"] = round(sum(tot_cur["back"][2:]) / div, 5)
        evidence.append(ev)
        if s["code"] != "KR0074":
            spec_cells.append(dict(code=s["code"], name=s["name"], source="separate filing back table (9년·10년 columns)", cells=[c for c in cells if c["old"] is None]))

    # ---- Hanwha Life: separate-basis table instead of the consolidated one ----
    h = HANWHA
    hs = hanwha_schedule(h["sep"])
    hc = hanwha_schedule(h["con"])
    hev = dict(code=h["code"], name=h["name"], unit=h["unit"], sep_xml=str(h["sep"].relative_to(ROOT)).replace("\\", "/"),
               con_xml=str(h["con"].relative_to(ROOT)).replace("\\", "/"))
    hev["separate_tables"] = [dict(line=t["line"], caption=t["caption"], total=t["total"]) for t in hs]
    hev["consolidated_tables"] = [dict(line=t["line"], caption=t["caption"], total=t["total"]) for t in hc]
    cur_s = hs[0] if hs else None
    close_cur = close.get((h["code"], QUARTER))
    if cur_s is None or cur_s["total"] is None:
        problems.append("KR0068: no separate-basis schedule table found")
    else:
        div = h["div"]
        tot = cur_s["total"]                 # 1년 이하 .. 9~10년 (10 cols), 11~15, 16~20, 21~25, 26~30, 30초과, 합계
        parts = tot[:-1]
        hev["current_separate_line"] = cur_s["line"]
        hev["current_separate_total_eok"] = round(tot[-1] / div, 5)
        hev["parts_sum_gap_in_unit"] = round(sum(parts) - tot[-1], 3)
        hev["master_closing_csm_2025.4Q"] = close_cur
        hev["rel_diff_separate_total_vs_closing"] = None if not close_cur else (tot[-1] / div - close_cur) / close_cur
        if abs(sum(parts) - tot[-1]) > 3 or close_cur is None or abs(tot[-1] / div - close_cur) > max(0.06, 0.0005 * close_cur):
            problems.append(f"KR0068: separate total {tot[-1] / div} vs closing {close_cur} / parts gap {sum(parts) - tot[-1]}")
        m = master.get((h["code"], QUARTER), {})
        cells = []
        for k in range(1, 11):
            new = round(tot[k - 1] / div, 1)
            cells.append(dict(경과차년=k, old=m.get(k), new=new, exact_eok=round(tot[k - 1] / div, 5)))
        # the OLD master values must be the consolidated table's (guard)
        ccur = next((t for t in hc if t["total"] is not None and abs(t["total"][-1] / div - 88752.04) < 1.0), None)
        if ccur is None:
            problems.append("KR0068: consolidated table with total 88,752억 not found (cannot prove the old values)")
        else:
            hev["consolidated_current_line"] = ccur["line"]
            hev["consolidated_current_total_eok"] = round(ccur["total"][-1] / div, 5)
            for c in cells:
                oldc = round(ccur["total"][c["경과차년"] - 1] / div, 1)
                if c["old"] is None or abs(c["old"] - oldc) > 0.05:
                    problems.append(f"KR0068 y{c['경과차년']}: master {c['old']} != consolidated table {oldc}")
        hev["cells"] = cells
        hev["y11plus_eok"] = round(sum(parts[10:]) / div, 5)
        spec_cells.append(dict(code=h["code"], name=h["name"], source="separate filing single wide table (replaces the consolidated table the panel picked)",
                               cells=[c for c in cells if c["old"] is None or abs(c["old"] - c["new"]) > 1e-9]))
    evidence.append(hev)

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "amort_split_evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    spec = dict(quarter=QUARTER, master="CSM_amortization.json", rounding="round(eok, 1) like build_tidy_exports.num", companies=spec_cells, problems=problems)
    (OUT / "amort_split_spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

    print("== staged cells ==")
    for sc in spec_cells:
        print(f"{sc['code']} {sc['name']}: {len(sc['cells'])} cells")
        for c in sc["cells"]:
            print(f"    y{c['경과차년']:>2}: {c['old']} -> {c['new']}   (exact {c['exact_eok']})")
    print("== identities ==")
    for ev in evidence:
        if ev["code"] == "KR0068":
            print(f"{ev['code']}: separate total {ev.get('current_separate_total_eok')} vs closing {ev.get('master_closing_csm_2025.4Q')} (rel {ev.get('rel_diff_separate_total_vs_closing'):.6f}); parts-sum gap {ev.get('parts_sum_gap_in_unit')}")
            continue
        print(f"{ev['code']}: current total {ev['identity_current_total_eok']} vs closing {ev['master_closing_csm_2025.4Q']} (rel {ev['rel_diff_current_total_vs_closing']:.6f}); "
              f"prior total {ev.get('identity_prior_total_eok')} vs 2024.4Q closing {ev.get('master_closing_csm_2024.4Q')}; row gap worst {ev['row_identity_worst_abs_gap_in_unit']} {ev['unit']}; "
              f"consolidated {ev.get('consolidated', {}).get('total_equal_to_separate')}/{ev.get('consolidated', {}).get('all_rows_equal')}")
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print("   ", p)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
