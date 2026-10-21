"""Read-only: build candidate gold files (scenarios) from the live gold + raw-verified vectors.

Scenarios (written under sim/):
  gold_R.json   restated-vintage blocks for 2023.1Q-2024.2Q (ticket E1-E4) + 2026.1Q separate (E5)
  gold_E5.json  2026.1Q separate only
  gold_O.json   as-originally-reported: delete the stale mixed-vintage gold cells (2023.3Q I1/I4, 2023.4Q I1/I4/I6,
                2024.1Q I1/I4, 2024.2Q I1/I4) so the builder diag flows through; + E5
Also writes sim/ledger_unpinned_<scn>.json = gold_overlay_ledger.json with the pins removed for KR0073 CSM cells that
stop being masked under that scenario.
"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
EV = ROOT / "data" / "_derived" / "kyobo_csm_basis_fix_20261021"
SIM = EV / "sim"
sys.stdout.reconfigure(encoding="utf-8")

CODE = "KR0073"
vec = json.load(open(EV / "csm_vectors_raw.json", encoding="utf-8"))

R_SRC = {
    "2023.1Q": "2023.1Q@FY2024_Q1prior",
    "2023.2Q": "2023.2Q@FY2024_Q2prior",
    "2023.3Q": "2023.3Q@FY2024_Q3prior",
    "2023.4Q": "2023.4Q@FY2024_Q4prior",
    "2024.1Q": "2024.1Q@FY2025_Q1prior",
    "2024.2Q": "2024.2Q@FY2025_Q2prior",
}
R = {q: vec[sid]["vec_eok"] for q, sid in R_SRC.items()}

# E5: separate basis, but keep I1 = 65109.6 (= master 2025.4Q close; gold open pin) and let I4 be the residual
e5 = vec["2026.1Q@FY2026_Q1sep_cur_3blk"]["vec_eok"]
E5_I1 = 65109.6
E5 = [E5_I1, e5[1], e5[2], None, e5[4], e5[5]]
E5[3] = round(E5[5] - E5[0] - E5[1] - E5[2] - E5[4], 2)
E5V = {"2026.1Q": E5}


def load(p):
    return json.load(open(p, encoding="utf-8"))


def save(obj, p):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def set_entries(gold, quarter_vec, why):
    """Update/append KR0073 gold entries so every item of the quarters in quarter_vec is a gold cell with the new value."""
    idx = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): i for i, e in enumerate(gold["set"])}
    for q, v in quarter_vec.items():
        for item, val in enumerate(v, start=1):
            k = (CODE, item, q)
            if k in idx:
                e = gold["set"][idx[k]]
                e["값"] = val
                e["why"] = why
                e.pop("note", None)
            else:
                gold["set"].append({"원보험사코드": CODE, "항목번호": item, "공시분기": q, "값": val, "why": why})
    return gold


def delete_entries(gold, keys):
    keep = []
    for e in gold["set"]:
        if (e["원보험사코드"], e["항목번호"], e["공시분기"]) in keys:
            continue
        keep.append(e)
    gold["set"] = keep
    return gold


def unpin(ledger, gold_new, diag_by):
    """remove ledger pins of KR0073 CSM cells that are no longer masked (gold != diag within 0.05) or no longer in gold."""
    out = copy.deepcopy(ledger)
    gidx = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in gold_new["set"]}
    removed = []
    for k in list(out["entries"]):
        p = k.split("|")
        if p[0] != "CSM" or p[1] != CODE:
            continue
        q, item = p[2], int(p[3])
        g = gidx.get((CODE, item, q))
        s = diag_by.get((CODE, item, q))
        masked = g is not None and s is not None and abs(round(g["값"] - s, 9)) <= 0.05
        if not masked:
            removed.append(k)
            del out["entries"][k]
    return out, removed


def pin_new_masked(ledger, gold_new, diag_by, note):
    """add ledger pins for KR0073 CSM gold cells that are masked (|gold-src| <= 0.05) but not pinned yet."""
    out = copy.deepcopy(ledger)
    added = []
    for e in gold_new["set"]:
        if e["원보험사코드"] != CODE:
            continue
        k = (CODE, e["항목번호"], e["공시분기"])
        key = f"CSM|{CODE}|{e['공시분기']}|{e['항목번호']}"
        s_ = diag_by.get(k)
        if s_ is None or key in out["entries"]:
            continue
        d = round(abs(e["값"] - s_), 9)
        if d <= 0.05:
            out["entries"][key] = {
                "overlay": "CSM",
                "verdict": "SAME_EXACT" if d <= 0.005 else "SAME_AT_1DP",
                "gold": e["값"],
                "src": s_,
                "source_file": "data/dart/viz/csm_waterfall_master_diag.json",
                "note": note,
            }
            added.append(key)
    return out, added


def main():
    gold0 = load(ROOT / "data/_gold/user_csm_cells.json")
    ledger0 = load(ROOT / "data/_gold/gold_overlay_ledger.json")
    diag = load(ROOT / "data/dart/viz/csm_waterfall_master_diag.json")
    diag_by = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in diag}

    why_R = ("2026-10-21 parser/ifrs17 ticket 20261021T1310Z (KR0073 CSM basis/vintage fix): restated-vintage separate block = latest filing prior-period column "
             "(FY2024 Q1/Q2/Q3/annual 'prior' tables for 2023.x; FY2025 Q1/Q2 for 2024.1Q/2Q); raw lines in data/_derived/kyobo_csm_basis_fix_20261021/csm_vectors_raw.txt")
    why_E5 = ("2026-10-21 parser/ifrs17 ticket 20261021T1310Z: 2026.1Q separate-basis (OFS) sum of the 3 sub-tables (유배당+무배당+변액) from FY2026_Q1 20260813001077.xml "
              "L43617/L43934/L44251; item1 stays 65109.6 (= master 2025.4Q close), item4 = residual; consolidated sums had been mixed in")

    cands = {}
    g = copy.deepcopy(gold0)
    set_entries(g, R, why_R)
    set_entries(g, E5V, why_E5)
    cands["R"] = g

    g = copy.deepcopy(gold0)
    set_entries(g, E5V, why_E5)
    cands["E5"] = g

    g = copy.deepcopy(gold0)
    stale = {(CODE, 1, "2023.3Q"), (CODE, 4, "2023.3Q"), (CODE, 1, "2023.4Q"), (CODE, 4, "2023.4Q"), (CODE, 6, "2023.4Q"),
             (CODE, 1, "2024.1Q"), (CODE, 4, "2024.1Q"), (CODE, 1, "2024.2Q"), (CODE, 4, "2024.2Q")}
    delete_entries(g, stale)
    set_entries(g, E5V, why_E5)
    cands["O"] = g

    # SAFE = E5 (2026.1Q separate sums) + E1 basis fix (2023.3Q / 2023.4Q opening = separate-basis printed opening);
    # item4 = residual over the master cells that remain (diag 1dp for untouched items), 2dp.
    g = copy.deepcopy(gold0)
    why_E1_3Q = ("2026-10-21 parser/ifrs17 ticket 20261021T1310Z E1: 2023.3Q opening was the CONSOLIDATED Q1/Q2 opening 46,967.3 (gold 2026-06-16) next to separate-basis flows; "
                 "replaced by the SEPARATE-basis printed opening of the same FY2023 Q3 filing (20231114002973.xml L50538 = 5,362,754 mn); item4 = residual over the block "
                 "(filing 추정치 변동 L50593 = (247,136) mn -> -2471.36; difference = 1dp rounding of items 3/6)")
    why_E1_4Q = ("2026-10-21 parser/ifrs17 ticket 20261021T1310Z E1: 2023.4Q opening was the CONSOLIDATED 46,967.3 (gold 2026-06-16); replaced by the SEPARATE-basis printed opening of the "
                 "FY2023 annual (20240329003502.xml L62689 = 5,533,766 mn) that also prints items 2/3/5. Close stays the FY2024 restated comparative 58,249.2 (continuity rule: FY2024 openings are 58,249.2), "
                 "so item4 = residual absorbs the vintage re-basing (original close 61,153.81 -> 58,249.23 = -2,904.58) on top of the printed 추정치 변동 (-18,116.75). R-vector not applicable (PL item4 pair open)")
    set_q = {"2023.3Q": {1: 53627.54}, "2023.4Q": {1: 55337.66}}
    idx = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): i for i, e in enumerate(g["set"])}
    for q, d in set_q.items():
        for item, val in d.items():
            e = g["set"][idx[(CODE, item, q)]]
            e["값"] = val
            e["why"] = why_E1_3Q if q == "2023.3Q" else why_E1_4Q
    # residuals (master cells after change: gold where present else diag)
    def cell(item, q):
        k = (CODE, item, q)
        if k in idx:
            return g["set"][idx[k]]["값"]
        return diag_by[k]
    for q, why in (("2023.3Q", why_E1_3Q), ("2023.4Q", why_E1_4Q)):
        i4 = round(cell(6, q) - cell(1, q) - cell(2, q) - cell(3, q) - cell(5, q), 2)
        g["set"][idx[(CODE, 4, q)]]["값"] = i4
        g["set"][idx[(CODE, 4, q)]]["why"] = why
        print(f"[SAFE] {q} item4 residual = {i4}")
    set_entries(g, E5V, why_E5)
    cands["SAFE"] = g

    for name, gd in cands.items():
        save(gd, SIM / f"gold_{name}.json")
        led, removed = unpin(ledger0, gd, diag_by)
        led, added = pin_new_masked(led, gd, diag_by,
                                    "2026-10-21 parser/ifrs17 ticket 20261021T1310Z (KR0073 CSM basis/vintage fix): masked gold cell pinned (gold equals the builder diag within 1dp; "
                                    "gold carries the 2dp printed value). GOLD_OVERLAY_DRIFT RED if the builder source stops reproducing it.")
        save(led, SIM / f"ledger_{name}.json")
        print(f"[{name}] gold entries {len(gold0['set'])} -> {len(gd['set'])}; ledger pins removed: {len(removed)} {removed[:2]}...; pins added: {len(added)} {added}")
    print("R vectors:", json.dumps(R, ensure_ascii=False))
    print("E5 vector:", E5)


if __name__ == "__main__":
    main()
