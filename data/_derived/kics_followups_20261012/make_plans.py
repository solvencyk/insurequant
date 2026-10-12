"""make_plans.py (parser-kics, ticket 20261012T1030Z) -- builds the cell-level plans from the LIVE master + the source readings below.
Writes data/_derived/kics_followups_20261012/plans/*.json (plans only; the master is NOT touched).  Each plan records base_sha =
sha256 of the master bytes it was built against; apply_plan.py refuses to apply on a different master.

Plans
  pacific_tfi_zero      (ticket item 1) KR1107 2025.3Q / 2026.2Q items 47-54: 16 new rows.  Source = the printed '(1) 공통적용 경과조치 관련
                        - 해당사항 없음' table, every cell prints the number 0 (53/54 post cells are diagonal-slashed = no post column value).
                        Convention of the 89 existing reinsurer rows for items 53/54: post key present and equal to the pre value -> '0'/'0'.
  axa_2024_3q_latest    (ticket item 2) KR0049 2024.3Q 4 cells -> the FY2024_Q4 (latest) disclosure's prior-quarter column (owner rule 2026-10-09).
  munich_A_50_52_only   (ticket item 3, SIMULATION ONLY - not applied) KR1101 2026.2Q items 50, 52 as printed (p17), 51 left blank.
  munich_B_derived_51   (ticket item 3, SIMULATION ONLY - not applied) = A + item 51 = 0 derived from 52 - 50 (51 is printed blank, NOT a dash).
"""
import copy
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_followups_20261012")
from lib import *  # noqa: F401,F403,E402

utf8_stdout()
rows = read_rows()
base_sha = sha_file(MASTER)
idx = index_rows(rows)
PLANS.mkdir(parents=True, exist_ok=True)

# --only name[,name]: (re)build just these plans.  Required, so that a re-run after the master changed cannot silently overwrite the plans
# that were already applied (their applied form is kept in applied_*.json).
ONLY = [x for x in (sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else []) if x]
if not ONLY:
    raise SystemExit("usage: make_plans.py --only pacific_tfi_zero,axa_2024_3q_latest,munich_A_50_52_only,munich_B_derived_51 (any subset)")


def emit(name, obj):
    if name in ONLY:
        write_json_lf(PLANS / f"{name}.json", obj)


def template(code, q, item):
    r = rows[idx[(code, q, item)]]
    return {k: r[k] for k in ROW_KEYS if k in r}


def new_row(tpl, q, item_value, post_value):
    r = dict(tpl)
    r["공시분기"] = q
    r["값"] = item_value
    if post_value is None:
        r.pop("값_적용후", None)
    else:
        r["값_적용후"] = post_value
    return {k: r[k] for k in ROW_KEYS if k in r}


# ---------------------------------------------------------------- (1) Pacific KR1107 2025.3Q / 2026.2Q
PAC_SRC = {
    "2025.3Q": ("data/disclosure/FY2025_Q3/raw/KR1107_퍼시픽라이프리.pdf p22 (md_inbox/FY2025_Q3/KR1107_퍼시픽라이프리.md lines 420-437)", "2025.2Q"),
    "2026.2Q": ("data/disclosure/FY2026_Q2/raw/KR1107_퍼시픽라이프리.pdf p25 (md_inbox/FY2026_Q2/KR1107_퍼시픽라이프리.md)", "2026.1Q"),
}
inserts = []
for q, (src, prev_q) in PAC_SRC.items():
    anchor = ("KR1107", prev_q, 54) if q == "2026.2Q" else ("KR1107", "2025.2Q", 54)
    for item in range(47, 55):
        tpl = template("KR1107", prev_q if q == "2026.2Q" else "2025.2Q", item)
        row = new_row(tpl, q, "0", "0")
        inserts.append({
            "after": list(anchor), "row": row,
            "src": src + " - '(1) 공통적용 경과조치 관련 - 해당사항 없음' table (unit 백만원): every cell prints the number 0",
            "note": "as printed (0); 53/54 post cell is diagonal-slashed in print -> post mirrored to pre = 0 (reinsurer convention, 89/89 existing rows)" if item in (53, 54) else "as printed (0 / 0)",
        })
        anchor = ("KR1107", q, item)
emit("pacific_tfi_zero", {
    "name": "pacific_tfi_zero", "task": "20261012T1030Z item 1 (KR1107)", "base_sha": base_sha,
    "note": "KR1107 is a non-applier of every transition measure (sidecar TFI/TAC/TIR/TER/TIRR/PCA_DEFER = X, not in FSS 붙임-1 registry); the filer prints a nil-return table of zeros",
    "edits": [], "inserts": inserts})

# ---------------------------------------------------------------- (2) AXA KR0049 2024.3Q - latest disclosure's prior column
AXA_P39 = "data/disclosure/FY2024_Q4/raw/KR0049_악사손해보험.pdf p39 (printed folio 38) [경과조치 적용 전 지급여력비율 세부], column 당분기-1분기 (= 2024.3Q)"
AXA_P36 = "data/disclosure/FY2024_Q4/raw/KR0049_악사손해보험.pdf p36 [지급여력비율 총괄], 경과조치후 지급여력비율, column 당분기-1분기 (= 2024.3Q); same value in FY2025_Q1 doc 당분기-2분기"


def edit(item, field, new, src, note):
    r = rows[idx[("KR0049", "2024.3Q", item)]]
    return {"code": "KR0049", "q": "2024.3Q", "item": item, "field": field, "old": r.get(field, "<nokey>"), "new": new, "src": src, "note": note}


axa_edits = [
    edit(3, "값", "2325", AXA_P39, "보완자본 printed 2,325 (master held the identity value 5554-3228 = 2326); new site edition p14/p15 also 2,325 (2,325.41)"),
    edit(3, "값_적용후", "2325", AXA_P39 + " (post follows pre: 경과조치 후 지급여력금액 5,554 = 전 5,554, TFI table 후 열 보완자본 2,325.41)", "post mirrors the pre cell"),
    edit(4, "값", "5215", AXA_P39, "Ⅰ. 건전성감독기준 재무상태표 상의 순자산 printed 5,215 (master held 5216 = sum of items 5-11)"),
    edit(27, "값_적용후", "286.5", AXA_P36, "경과조치후 지급여력비율 printed 286.5 (master held the derived 5554/1939*100 = 286.43630737); neighbours store the printed value"),
]
emit("axa_2024_3q_latest", {
    "name": "axa_2024_3q_latest", "task": "20261012T1030Z item 2 (KR0049)", "base_sha": base_sha,
    "note": "owner rule 2026-10-09: when disclosures conflict adopt the latest disclosure's prior-quarter column (FY2024_Q4 doc, 당분기-1분기)",
    "edits": axa_edits, "inserts": []})

# ---------------------------------------------------------------- (3) Munich KR1101 2026.2Q (simulation plans)
MUC_SRC = "data/disclosure/FY2026_Q2/raw/KR1101_뮌헨재보험.pdf p17 '(1) 공통적용 경과조치 관련' (백만원): 지급여력금액 271,642/271,642, 기본자본 271,642/271,642; 보완자본 and the 6 memo rows are BLANK (no dash)"
tplm = {it: template("KR1101", "2026.1Q", it) for it in (50, 51, 52)}
anchor = ("KR1101", "2026.1Q", 54)
muc_rows = []
for it, val in ((50, "2716.42"), (52, "2716.42")):
    muc_rows.append({"after": None, "row": new_row(tplm[it], "2026.2Q", val, val), "src": MUC_SRC, "note": "as printed"})
muc_rows_b = [muc_rows[0],
              {"after": None, "row": new_row(tplm[51], "2026.2Q", "0", "0"), "src": MUC_SRC + " ; item 51 = 52 - 50 = 0 DERIVED (identity within the same table), not printed", "note": "derived, owner decision needed"},
              muc_rows[1]]


def chain(rs):
    a = anchor
    out = []
    for r in rs:
        r = copy.deepcopy(r)
        r["after"] = list(a)
        out.append(r)
        a = key(r["row"])
    return out


emit("munich_A_50_52_only", {"name": "munich_A_50_52_only", "task": "20261012T1030Z item 3 (KR1101) SIMULATION ONLY", "base_sha": base_sha,
                                                    "note": "NOT applied", "edits": [], "inserts": chain(muc_rows)})
emit("munich_B_derived_51", {"name": "munich_B_derived_51", "task": "20261012T1030Z item 3 (KR1101) SIMULATION ONLY", "base_sha": base_sha,
                                                    "note": "NOT applied", "edits": [], "inserts": chain(muc_rows_b)})

print("base_sha", base_sha)
for n in [x for x in ("pacific_tfi_zero", "axa_2024_3q_latest", "munich_A_50_52_only", "munich_B_derived_51") if x in ONLY]:
    p = load_plan(n)
    print(f"{n}: edits={len(p['edits'])} inserts={len(p['inserts'])}")
    for e in p["edits"]:
        print(f"   EDIT {e['code']} {e['q']} item{e['item']} {e['field']}: {e['old']!r} -> {e['new']!r}")
    for i in p["inserts"][:3]:
        print(f"   INS after={i['after']} row={i['row']}")
    if len(p["inserts"]) > 3:
        print(f"   ... {len(p['inserts']) - 3} more inserts")
