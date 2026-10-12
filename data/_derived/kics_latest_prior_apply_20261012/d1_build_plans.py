"""d1_build_plans.py -- build the FINAL apply plans (plans/<block>.json) for the 16 blocks that pass every ticket criterion.

Input  : the dry-run plan (primary 값 edits + post mirrors), the live master, the dry-run raw core extraction (own / F+1 / F+2 prints).
Output : plans/<block>.json with EXPLICIT edits (primary, post_mirror, derived_ratio 27/28 recomputed with the existing formula),
         each edit = {code, q, item, field, old, new, kind, src, col}.  `old` is the guard value, `new` the value to write; reverting
         a block = write `old` back (apply_master.py --revert).
Read-only on the repo master.
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_20261012")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_precedence_dryrun_20261012")
from lib_apply import *  # noqa: F401,F403,E402

utf8_stdout()
import harness as dryh  # noqa: E402  (dry-run harness: apply_plan() gives the derived 27/28 edits)

rows = read_rows()
live_sha = sha_file(MASTER)
core = read_json(DRY / "core_extract_all.json")
QS = [f"{y}.{q}Q" for y in (2023, 2024, 2025, 2026) for q in (1, 2, 3, 4)][:14]
NAMES = {}
for r in rows:
    NAMES.setdefault(r["원보험사코드"], r["원수사명"])
ITEM_NAME = {}
for r in rows:
    if isinstance(r["항목번호"], int) and r["항목번호"] <= 28:
        ITEM_NAME.setdefault(r["항목번호"], r["항목명"])


def qadd(q, n):
    i = QS.index(q) + n
    return QS[i] if 0 <= i < len(QS) else None


def per(q):
    return f"FY{q[:4]}_Q{q[5]}"


def printed(code, filing_q, col, item):
    rec = core.get(f"{per(filing_q)}|{code}") if filing_q else None
    if not rec:
        return None
    if rec["status"] not in ("OK", "VISION_ONLY"):
        return None
    v = rec["cols"].get(col, {}).get(str(item))
    return None if v is None else v[0]


def pages_of(code, filing_q):
    rec = core.get(f"{per(filing_q)}|{code}") if filing_q else None
    if not rec or not rec.get("pdf"):
        return None
    return {"pdf": rec["pdf"], "pdf_pages": rec.get("pages")}


# --- own-filing prints that the table extractor could not read, read directly in the PDF (text layer or 100-150dpi render) -----------
# value = what the own filing prints for that quarter ('-' = printed dash = 0).  Source: b1_pdf_rows.txt (text) and the viewed renders in img/.
OWN_DIRECT = {
    ("KR0003", "2023.4Q", 4): (2481, "FY2023_Q4/raw/KR0003_롯데손해보험_amended.pdf p41", "text layer + render: issuer typo, prints 2,481 where the six components sum to 24,808"),
    ("KR0004", "2023.1Q", 5): (1211, "FY2023_Q1/raw/KR0004_예별손해보험.pdf p9", "text layer + 100dpi render"),
    ("KR0004", "2023.1Q", 6): (36, "FY2023_Q1/raw/KR0004_예별손해보험.pdf p9", "text layer + 100dpi render"),
    ("KR0004", "2023.1Q", 11): (3823, "FY2023_Q1/raw/KR0004_예별손해보험.pdf p9", "text layer + 100dpi render"),
    ("KR0009", "2023.1Q", 1): (133398, "FY2023_Q1/raw/KR0009_현대해상.pdf p9", "text layer + 100dpi render"),
    ("KR0009", "2023.1Q", 2): (73537, "FY2023_Q1/raw/KR0009_현대해상.pdf p9", "text layer + 100dpi render"),
    ("KR0009", "2023.1Q", 3): (59861, "FY2023_Q1/raw/KR0009_현대해상.pdf p9", "text layer + 100dpi render"),
    ("KR0009", "2023.1Q", 4): (127231, "FY2023_Q1/raw/KR0009_현대해상.pdf p9", "text layer + 100dpi render"),
    ("KR0009", "2023.1Q", 6): (4983, "FY2023_Q1/raw/KR0009_현대해상.pdf p9", "text layer + 100dpi render"),
    ("KR0009", "2023.1Q", 11): (48867, "FY2023_Q1/raw/KR0009_현대해상.pdf p9", "text layer + 100dpi render"),
    ("KR0009", "2023.1Q", 13): (53694, "FY2023_Q1/raw/KR0009_현대해상.pdf p9", "text layer + 100dpi render"),
    ("KR0009", "2023.1Q", 15): (98852, "FY2023_Q1/raw/KR0009_현대해상.pdf p9", "text layer + 100dpi render"),
    ("KR0049", "2025.1Q", 3): (2331, "FY2025_Q1/raw/KR0049_악사손해보험.pdf p16 (printed p15)", "image-only page, 110dpi render viewed"),
    ("KR0049", "2026.1Q", 4): (3820, "FY2026_Q1/raw/KR0049_악사손해보험.pdf p16 (printed p15)", "image-only page, 110dpi render viewed"),
    ("KR0071", "2024.4Q", 4): (33924, "FY2024_Q4/raw/KR0071_흥국생명보험.pdf p48", "scanned page (all 538 pages image-only), 150dpi render viewed"),
    ("KR0072", "2025.2Q", 12): ("-", "FY2025_Q2/raw/KR0072_케이디비생명보험.pdf p19", "text layer row: dash, dash, dash"),
    ("KR0080", "2026.1Q", 3): (4280, "FY2026_Q1/raw/KR0080_에이아이에이생명보험.pdf p18", "vector/image page, 150dpi render viewed"),
}
# classification of the primary (전/값) cells: R = restatement (own filing = master old value, later filings print the new value)
#   C = master correction (own filing already prints the new value, the master held a derived/mis-read number)
#   T = own-filing typo (own filing prints a typo, master held the component sum, later filings print the new value)
CLASS = {("KR0003", "2023.4Q", 4): "T", ("KR0049", "2025.1Q", 3): "C", ("KR0049", "2026.1Q", 4): "C",
         ("KR0071", "2024.4Q", 4): "C", ("KR0080", "2026.1Q", 3): "C"}
# pages where the 100dpi/150dpi renders were viewed (flag-carrying blocks) -- recorded in applied_blocks.csv
VIEWED = {
    "KR0003_2025.1Q": ["FY2025_Q1 p18", "FY2025_Q2 p20", "FY2025_Q3 p20"],
    "KR0003_2023.4Q": ["FY2023_Q4(amended) p41"],
    "KR0004_2023.1Q": ["FY2023_Q1 p9", "FY2023_Q2 p11", "FY2023_Q3 p11"],
    "KR0009_2023.1Q": ["FY2023_Q1 p9", "FY2023_Q2 p10", "FY2023_Q3(amended) p12"],
    "KR0049_2025.1Q": ["FY2025_Q1 p16 (printed 15)"],
    "KR0049_2026.1Q": ["FY2026_Q1 p16 (printed 15)"],
    "KR0050_2025.3Q": ["FY2025_Q3 p17", "FY2025_Q4 p53", "FY2026_Q1 p17"],
    "KR0071_2024.4Q": ["FY2024_Q4 p48"],
    "KR0080_2026.1Q": ["FY2026_Q1 p18"],
}

final = {}
for bid in APPLIED:
    code, q = bid.split("_")
    plan = read_json(DRY / "plans" / f"{bid}.json")
    cand, n, derived = dryh.apply_plan(rows, plan)
    edits = []
    for e in plan["edits"]:
        kind = "primary" if e["field"] == "값" else "post_mirror"
        edits.append({"code": code, "q": q, "item": e["item"], "field": e["field"], "old": e["old"], "new": e["new"], "kind": kind,
                      "src": e["src"], "col": e["col"]})
    for d in derived:
        assert d["code"] == code and d["q"] == q
        edits.append({"code": code, "q": q, "item": d["item"], "field": d["field"], "old": d["old"], "new": d["new"],
                      "kind": "derived_ratio", "src": "recomputed with the existing derived formula (recalc_kics_derived.py: item27 = 1/14, item28 = 2/14, 28후 = 2후/14후)",
                      "col": d["why"]})
    # guard check against the live master right now
    probe = copy.deepcopy(rows)
    apply_to_rows(probe, edits)
    q1, q2 = qadd(q, 1), qadd(q, 2)
    ev = []
    for e in [x for x in edits if x["kind"] == "primary"]:
        it = e["item"]
        own = printed(code, q, "cur", it)
        own_src = pages_of(code, q)
        if (code, q, it) in OWN_DIRECT:
            ov, osrc, how = OWN_DIRECT[(code, q, it)]
            own, own_how = ov, f"{osrc} [{how}]"
        else:
            own_how = (f"{own_src['pdf'].split('data/disclosure/')[-1]} p{'+'.join(map(str, own_src['pdf_pages'] or []))} [extractor + text layer]" if own_src else None)
        f1 = printed(code, q1, "prev", it) if q1 else None
        f2 = printed(code, q2, "prev2", it) if q2 else None
        s1, s2 = pages_of(code, q1), pages_of(code, q2)
        ev.append({"item": it, "item_name": ITEM_NAME.get(it), "master_old": e["old"], "new": e["new"],
                   "class": CLASS.get((code, q, it), "R"),
                   "own_print": own, "own_src": own_how,
                   "f1_print": f1, "f1_src": (f"{s1['pdf'].split('data/disclosure/')[-1]} p{'+'.join(map(str, s1['pdf_pages'] or []))} (prev col)" if s1 else None),
                   "f2_print": f2, "f2_src": (f"{s2['pdf'].split('data/disclosure/')[-1]} p{'+'.join(map(str, s2['pdf_pages'] or []))} (prev2 col)" if s2 else None)})
    out = {"name": bid, "code": code, "company": NAMES[code], "quarter": q, "base_sha": live_sha, "edits": edits, "inserts": [],
           "latest_label": plan["latest_label"], "latest_src": plan["latest_src"], "dryrun_flags": plan.get("flags"),
           "viewed_pages": VIEWED.get(bid, []), "evidence": ev}
    final[bid] = out
    write_json_lf(PLANS / f"{bid}.json", out)
    print(f"{bid}: edits={len(edits)} (primary {sum(e['kind']=='primary' for e in edits)}, post_mirror {sum(e['kind']=='post_mirror' for e in edits)}, "
          f"derived {sum(e['kind']=='derived_ratio' for e in edits)})  guard vs live master OK")

tot = sum(len(v["edits"]) for v in final.values())
print("blocks", len(final), "cells", tot, "| live master sha", live_sha[:12])
