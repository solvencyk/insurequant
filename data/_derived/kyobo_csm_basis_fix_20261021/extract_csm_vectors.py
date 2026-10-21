"""Read-only: extract KR0073 CSM roll-forward vectors (CSM subtotal column) from DART XML tables.

For every spec (filing file + <TABLE> start line(s)) it reads the CSM-subtotal column of the 22-4/17-4 table
('보험료배분접근법을 적용한 보험계약 이외의 보험계약부채(자산)의 요소별 변동내역') and records, in 백만원 with the raw line
number of each value cell:
    open  (1. 기초)            est (2.(1) 추정치 변동)      loss (2.(2) 손실부담)     new (2.(3) 최초 인식)
    release (3.(1) CSM 상각)   fin (6. 보험금융손익)         other (7. 기타)           close (8. 기말)
and checks open+est+loss+new+release+fin+other-close == 0 (exact integer 백만원) plus the residual vs the master item-4
convention (item4 = close-open-new-fin-release, 억원 2-decimals).

Usage:  python extract_csm_vectors.py [out_json]
Specs are defined in SPECS below; 3-block specs (유배당/무배당/변액) list three table start lines that are summed.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from xmltab import parse_tables, num  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
DART = ROOT / "data" / "dart"
K = "KR0073_교보생명보험"

F = {
    "FY2023_Q1": DART / "FY2023_Q1/raw" / K / "xml/20230515002764.xml",
    "FY2023_Q2": DART / "FY2023_Q2/raw" / K / "xml/20230814002761.xml",
    "FY2023_Q3": DART / "FY2023_Q3/raw" / K / "xml/20231114002973.xml",
    "FY2023_Q4": DART / "FY2023_Q4/raw" / (K + "_20240329003502") / "xml/20240329003502.xml",
    "FY2023_Q4_sepaudit": DART / "FY2023_Q4/raw" / (K + "_20240329003502") / "xml/20240329003502_00760.xml",
    "FY2024_Q1": DART / "FY2024_Q1/raw" / K / "20240516001553.xml",
    "FY2024_Q2": DART / "FY2024_Q2/raw" / K / "20240814004365.xml",
    "FY2024_Q3": DART / "FY2024_Q3/raw" / K / "20241114003039.xml",
    "FY2024_Q4": DART / "FY2024_Q4/raw" / (K + "_20250331004015") / "xml/20250331004015.xml",
    "FY2024_Q4_sepaudit": DART / "FY2024_Q4/raw" / (K + "_20250331004015") / "xml/20250331004015_00760.xml",
    "FY2025_Q1": DART / "FY2025_Q1/raw" / K / "xml/20250515002967.xml",
    "FY2025_Q2": DART / "FY2025_Q2/raw" / K / "xml/20250814004112.xml",
    "FY2025_Q3": DART / "FY2025_Q3/raw" / K / "20251114002942.xml",
    "FY2025_Q4": DART / "FY2025_Q4/raw" / (K + "_20260331004015") / "20260331004015.xml",
    "FY2026_Q1": DART / "FY2026_Q1/raw" / K / "xml/20260813001077.xml",
    "FY2026_Q2": DART / "FY2026_Q2/raw" / K / "20260814004024.xml",
}

# (spec_id, period, vintage, file_key, [table start lines], note)
SPECS = [
    # --- 2023 original filings, separate notes, current-period tables
    ("2023.1Q@FY2023_Q1", "2023.1Q", "orig", "FY2023_Q1", [38188], "별도 당분기"),
    ("2023.2Q@FY2023_Q2", "2023.2Q", "orig", "FY2023_Q2", [42048], "별도 당반기"),
    ("2023.3Q@FY2023_Q3", "2023.3Q", "orig", "FY2023_Q3", [50494], "별도 당분기"),
    ("2023.4Q@FY2023_Q4", "2023.4Q", "orig", "FY2023_Q4", [62645], "별도 당기"),
    ("2023.4Q@FY2023_Q4sepaudit", "2023.4Q", "orig", "FY2023_Q4_sepaudit", [], "별도 감사보고서 당기 (auto)"),
    # --- 2023 restated comparatives (FY2024 filings, separate notes, prior-period tables)
    ("2023.1Q@FY2024_Q1prior", "2023.1Q", "restated", "FY2024_Q1", [46646], "별도 전분기"),
    ("2023.2Q@FY2024_Q2prior", "2023.2Q", "restated", "FY2024_Q2", [49774], "별도 전반기"),
    ("2023.3Q@FY2024_Q3prior", "2023.3Q", "restated", "FY2024_Q3", [48440], "별도 전분기"),
    ("2023.4Q@FY2024_Q4prior", "2023.4Q", "restated", "FY2024_Q4", [64473], "별도 전기"),
    # --- 2024 originals (current period tables) and restated comparatives (FY2025 prior tables)
    ("2024.1Q@FY2024_Q1", "2024.1Q", "orig", "FY2024_Q1", [46330], "별도 당분기"),
    ("2024.2Q@FY2024_Q2", "2024.2Q", "orig", "FY2024_Q2", [49458], "별도 당반기"),
    ("2024.3Q@FY2024_Q3", "2024.3Q", "orig", "FY2024_Q3", [48124], "별도 당분기"),
    ("2024.4Q@FY2024_Q4", "2024.4Q", "orig", "FY2024_Q4", [64157], "별도 당기"),
    ("2024.1Q@FY2025_Q1prior", "2024.1Q", "restated", "FY2025_Q1", [45341], "별도 전분기"),
    ("2024.2Q@FY2025_Q2prior", "2024.2Q", "restated", "FY2025_Q2", [48355], "별도 전반기"),
    ("2024.3Q@FY2025_Q3prior", "2024.3Q", "restated", "FY2025_Q3", [41094], "별도 전분기"),
    ("2024.4Q@FY2025_Q4prior_3blk", "2024.4Q", "restated2", "FY2025_Q4", [59722, 60038, 60354], "별도 전기 3블록"),
    ("2024.4Q@FY2025_Q4prior_CONS_3blk", "2024.4Q", "restated2_CONS", "FY2025_Q4", [26083, 26399, 26715], "연결 전기 3블록 (basis check of the earlier dry-run candidate)"),
    ("2024.4Q@FY2025_Q4cur_SEP_3blk_unused", "2025.4Q", "orig", "FY2025_Q4", [58772, 59088, 59404], "별도 당기 3블록 (2025.4Q, continuity context)"),
    # --- 2025 current (for continuity context)
    ("2025.1Q@FY2025_Q1", "2025.1Q", "orig", "FY2025_Q1", [45025], "별도 당분기"),
    # --- 2026
    ("2026.1Q@FY2026_Q1sep_cur_3blk", "2026.1Q", "orig", "FY2026_Q1", [43617, 43934, 44251], "별도 당분기 3블록"),
    ("2026.1Q@FY2026_Q1cons_cur_3blk", "2026.1Q", "orig_CONS", "FY2026_Q1", [20658, 20974, 21290], "연결 당분기 3블록"),
    ("2025.1Q@FY2026_Q1sep_prior_3blk", "2025.1Q", "restated", "FY2026_Q1", [44568, 44885, 45202], "별도 전분기 3블록"),
    ("2026.2Q@FY2026_Q2sep_cur_3blk", "2026.2Q", "orig", "FY2026_Q2", [40060, 40345, 40630], "별도 당반기 3블록"),
]

LABELS = [
    ("open", re.compile(r"^1\. 기초 보험계약자산 및 부채")),
    ("est", re.compile(r"^\(1\) 보험계약마진을 조정하는 추정치의 변동분")),
    ("loss", re.compile(r"^\(2\) 손실부담계약집합의 손실")),
    ("new", re.compile(r"^\(3\) 최초 인식한 계약의 효과")),
    ("release", re.compile(r"^\(1\) 서비스 이전을 반영하기 위해 당기손익으로 인식한 보험계약마진")),
    ("fin", re.compile(r"^6\. 보험금융손익")),
    ("other", re.compile(r"^7\. 기타")),
    ("close", re.compile(r"^8\. \S*말 보험계약자산 및 부채")),
]


def csm_col(tab):
    """1-based index into cells[1:] of the CSM total column."""
    for _, cells, _ in tab["header_rows"]:
        if "소계" in cells:
            k = cells.index("소계")
            return 2 + (k + 1)
    return 3


# open/close redundancy: some filings leave the '1. 기초' / '8. 기말' header rows blank (values only on the 순부채 row)
ALT = {
    "open": [re.compile(r"^기초 보험계약순부채\(자산\)"), re.compile(r"^\(2\) 기초보험계약부채")],
    "close": [re.compile(r"^\S*말 보험계약순부채\(자산\)"), re.compile(r"^\(2\) \S*말보험계약부채")],
}


def read_vec(tab):
    col = csm_col(tab)
    out = {"csm_col": col, "unit": tab["unit"], "table": (tab["start"], tab["end"]), "alt_checks": {}}
    for key, rx in LABELS:
        found = None
        for ln, cells, cl in tab["rows"]:
            if rx.search(cells[0]) and len(cells) > col:
                found = {"v": num(cells[col]), "txt": cells[col], "line": cl[col], "tr": ln, "label": cells[0]}
                break
        if key in ALT:
            alts = []
            for arx in ALT[key]:
                for ln, cells, cl in tab["rows"]:
                    if arx.search(cells[0]) and len(cells) > col:
                        alts.append({"v": num(cells[col]), "txt": cells[col], "line": cl[col], "tr": ln, "label": cells[0]})
                        break
            vals = [a["v"] for a in alts if a["v"] is not None]
            if found is None or found["v"] is None:
                # header row blank -> take first non-empty redundant row
                found = next((a for a in alts if a["v"] is not None), found)
            out["alt_checks"][key] = {
                "used": found["label"] if found else None,
                "all_equal": (len(set(vals + ([found["v"]] if found and found["v"] is not None else []))) <= 1),
                "alts": [(a["label"], a["txt"], a["line"]) for a in alts],
            }
        if found is not None:
            out[key] = found
    return out


def sum_vecs(vecs):
    tot = {}
    for key, _ in LABELS:
        vals = [v[key]["v"] for v in vecs if key in v and v[key]["v"] is not None]
        tot[key] = sum(vals) if vals else None
    return tot


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else None
    cache = {}
    results = {}
    lines_out = []

    def emit(s=""):
        lines_out.append(s)
        print(s)

    for sid, period, vint, fkey, starts, note in SPECS:
        if not starts:
            continue
        path = F[fkey]
        if fkey not in cache:
            cache[fkey] = parse_tables(str(path))[0]
        tabs = {t["start"]: t for t in cache[fkey]}
        vecs = []
        missing = [s for s in starts if s not in tabs]
        if missing:
            emit(f"!! {sid}: no table at {missing}")
            continue
        for s in starts:
            vecs.append(read_vec(tabs[s]))
        tot = sum_vecs(vecs)
        # closure: open + est + loss + new + release + fin + other == close
        g = lambda k: (tot[k] or 0)
        gap = g("open") + g("est") + g("loss") + g("new") + g("release") + g("fin") + g("other") - g("close")
        eok = lambda x: round(x / 100.0, 2)
        i1, i2, i3, i5, i6 = eok(g("open")), eok(g("new")), eok(g("fin")), eok(g("release")), eok(g("close"))
        i4 = round(i6 - i1 - i2 - i3 - i5, 2)
        est_other = eok(g("est") + g("loss") + g("other"))
        emit("=" * 100)
        emit(f"{sid}  period={period} vintage={vint}  file={path.name}  tables={starts}  [{note}]")
        emit(f"  unit(s): {[v['unit'] for v in vecs]}  csm_col={[v['csm_col'] for v in vecs]}")
        for k in ("open", "est", "loss", "new", "release", "fin", "other", "close"):
            parts = []
            for v in vecs:
                if k in v:
                    lbl = v[k]["label"]
                    tag = "" if (k not in ("open", "close") or lbl.startswith(("1.", "8."))) else f"[{lbl}]"
                    parts.append(f"{v[k]['txt']}@L{v[k]['line']}{tag}")
                else:
                    parts.append("MISSING")
            emit(f"  {k:8s} sum={tot[k]!s:>12}  <- " + " + ".join(parts))
        for v in vecs:
            for k, ac in v["alt_checks"].items():
                if not ac["all_equal"]:
                    emit(f"  !! {k}: redundant rows disagree: {ac}")
        emit(f"  closure gap (open+est+loss+new+release+fin+other-close, 백만원) = {gap}")
        emit(f"  vector 억원 [I1..I6] = [{i1}, {i2}, {i3}, {i4}, {i5}, {i6}]  (I4 = residual; est+loss+other 억 = {est_other}; I4-est_other = {round(i4 - est_other, 2)})")
        results[sid] = {
            "period": period, "vintage": vint, "file": str(path.relative_to(ROOT)).replace("\\", "/"),
            "tables": starts, "note": note,
            "mn": {k: tot[k] for k, _ in LABELS},
            "cells": [{k: {"txt": v[k]["txt"], "line": v[k]["line"]} for k, _ in LABELS if k in v} for v in vecs],
            "closure_gap_mn": gap,
            "vec_eok": [i1, i2, i3, i4, i5, i6],
            "est_other_eok": est_other,
        }
    if out_path:
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        with open(out_path.replace(".json", ".txt"), "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines_out) + "\n")


if __name__ == "__main__":
    main()
