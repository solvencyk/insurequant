# -*- coding: utf-8 -*-
"""k01: prove that  (post-load files)  minus  (pre-load backup)  is KDB (KR0072) only.

Read-only.  Usage:
    python k01_prove_kdb_only.py [CUR_ROOT] [TAG]
CUR_ROOT = directory that holds the "current" (post-load) copies under the repo-relative
paths; default is the live working tree.  TAG is appended to the output file names.
The "old" side is always the pre-load backup folder written by the KDB loader.
"""
import collections
import difflib
import hashlib
import json
import os
import sys

REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
E23 = REPO + "/data/_derived/remaining_20261022/e23_d1_d3"
BK = E23 + "/backup_before_apply/kr0072_kdb_load2"
EVD = E23 + "/kdb_restore"
CODE = "KR0072"

CUR = sys.argv[1] if len(sys.argv) > 1 else REPO
TAG = sys.argv[2] if len(sys.argv) > 2 else ""

LOG = []
RESULTS = []          # (name, ok, detail)


def say(line=""):
    LOG.append(line)


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    say("%s  %s%s" % ("PASS" if ok else "FAIL", name, (" :: " + detail) if detail else ""))
    return bool(ok)


def canon(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rd_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def rd_text(path):
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def keyed(rows, kf):
    """key -> row, with an occurrence counter so duplicate keys cannot hide a change."""
    out = collections.OrderedDict()
    seen = collections.Counter()
    dups = 0
    for r in rows:
        k = kf(r)
        seen[k] += 1
        if seen[k] > 1:
            dups += 1
        out[k + (seen[k],)] = r
    return out, dups


def analyze(old_rows, new_rows, kf, code_pos=0):
    """cell-level diff of two row lists.  Returns a dict of facts."""
    old, d_old = keyed(old_rows, kf)
    new, d_new = keyed(new_rows, kf)
    added = [k for k in new if k not in old]
    removed = [k for k in old if k not in new]
    changed = collections.OrderedDict()
    for k, nr in new.items():
        orow = old.get(k)
        if orow is None:
            continue
        if canon(orow) != canon(nr):
            if isinstance(orow, dict) and isinstance(nr, dict):
                fields = {}
                for f in sorted(set(orow) | set(nr)):
                    a = orow.get(f, "<absent>")
                    b = nr.get(f, "<absent>")
                    if canon(a) != canon(b):
                        fields[f] = (a, b)
                changed[k] = fields
            else:
                changed[k] = {"(row)": (orow, nr)}
    touched = list(changed) + added + removed
    non_kdb_touched = [k for k in touched if k[code_pos] != CODE]
    old_seq = [k for k in old if k[code_pos] != CODE]
    new_seq = [k for k in new if k[code_pos] != CODE]
    return dict(n_old=len(old_rows), n_new=len(new_rows), dups_old=d_old, dups_new=d_new,
                added=added, removed=removed, changed=changed,
                non_kdb_touched=non_kdb_touched,
                non_kdb_order_same=(old_seq == new_seq),
                non_kdb_count=len(old_seq),
                old=old, new=new)


def top_level(old, new):
    ok, nk = set(old), set(new)
    return dict(added=sorted(nk - ok), removed=sorted(ok - nk),
                changed=sorted(k for k in ok & nk if canon(old[k]) != canon(new[k])),
                order_same=([k for k in old if k in nk] == [k for k in new if k in ok]))


def by_quarter(keys, qpos):
    c = collections.Counter(k[qpos] for k in keys)
    return dict(sorted(c.items()))


# --------------------------------------------------------------------------- files
FILES_CHANGED = [
    "PL_breakdown.json", "CSM_waterfall.json", "PL_breakdown_provenance.json",
    "CSM_waterfall_provenance.json", "data/_gold/user_pl_cells.json",
    "data/_gold/user_csm_cells.json", "data/_gold/gold_overlay_ledger.json",
    "tests/test_rule_coverage_manifest.py", "tests/fixtures/master_tables_golden.json",
    "tests/fixtures/builder_input_fingerprints.json", "data/_derived/qoq_warn.json",
    "data/_derived/pl_oci_vs_bs_aoci_warn.json",
]
FILES_SAME = [
    "tests/fixtures/pl_breakdown_golden.json", "tests/fixtures/viz_ifrs17_panels_golden.json",
    "tests/fixtures/viz_csm_waterfall_golden.json", "data/dart/viz/csm_continuity_validation.json",
    "NB_CSM_multiple.json", "data/dart/viz/pl_breakdown_master.json",
    "scripts/validate_master_tables.py",
]


def P(root, rel):
    path = root + "/" + rel
    if root == CUR and not os.path.exists(path):
        # CUR may be a folder that holds only the 12 changed files (the post-load snapshot);
        # the 7 files the load never touched are then read from the live tree.
        return REPO + "/" + rel
    return path


def main():
    say("k01 prove-KDB-only  CUR_ROOT=%s  BACKUP=%s" % (CUR, BK))
    say("")
    # ------------------------------------------------------------------ A. hashes
    say("== A. byte hashes (backup vs current)")
    for rel in FILES_CHANGED + FILES_SAME:
        a, b = sha256(P(BK, rel)), sha256(P(CUR, rel))
        say("   %-52s backup %s  current %s  %s" % (rel, a[:12], b[:12], "equal" if a == b else "DIFFERENT"))
    for rel in FILES_SAME:
        check("A unchanged file is byte-identical: " + rel, sha256(P(BK, rel)) == sha256(P(CUR, rel)))
    say("")

    # ------------------------------------------------------------------ B. PL_breakdown
    say("== B. PL_breakdown.json (cell = code, item, quarter)")
    kf = lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"])
    bpl = rd_json(P(BK, "PL_breakdown.json"))
    cpl = rd_json(P(CUR, "PL_breakdown.json"))
    kdb_name = next(r["원수사명"] for r in cpl if r["원보험사코드"] == CODE)
    say("   KDB display name = %s" % kdb_name)
    r = analyze(bpl, cpl, kf)
    check("B1 no duplicate cell keys", r["dups_old"] == 0 and r["dups_new"] == 0, "dups old %d new %d" % (r["dups_old"], r["dups_new"]))
    check("B2 row count unchanged (no rows added/removed)", not r["added"] and not r["removed"] and r["n_old"] == r["n_new"],
          "rows %d -> %d, added %d removed %d" % (r["n_old"], r["n_new"], len(r["added"]), len(r["removed"])))
    check("B3 every changed cell is KR0072", not r["non_kdb_touched"], "non-KDB touched: %d" % len(r["non_kdb_touched"]))
    fields = sorted(set(f for fs in r["changed"].values() for f in fs))
    check("B4 only fields 값 / 값_당분기 changed", set(fields) <= {"값", "값_당분기"}, "fields changed: %s" % fields)
    check("B5 non-KDB rows identical and in the same order", r["non_kdb_order_same"], "non-KDB rows %d" % r["non_kdb_count"])
    val_ch = [k for k, fs in r["changed"].items() if "값" in fs]
    dan_ch = [k for k, fs in r["changed"].items() if "값_당분기" in fs]
    say("   KR0072 cells with 값 changed: %d  by quarter %s" % (len(val_ch), by_quarter(val_ch, 2)))
    say("   KR0072 cells with 값_당분기 changed: %d  by quarter %s" % (len(dan_ch), by_quarter(dan_ch, 2)))
    say("   KR0072 cells with 값 AND 값_당분기 changed: %d ; only 값_당분기 (followed): %d" % (
        len(set(val_ch) & set(dan_ch)), len(set(dan_ch) - set(val_ch))))
    check("B6 CLAIM loader: PL 값 65 (1Q 19, 2Q 24, 3Q 16, 4Q 6)",
          len(val_ch) == 65 and by_quarter(val_ch, 2) == {"2023.1Q": 19, "2023.2Q": 24, "2023.3Q": 16, "2023.4Q": 6})
    check("B7 CLAIM loader: PL 값_당분기 81 (63 with 값 + 18 followed)",
          len(dan_ch) == 81 and len(set(val_ch) & set(dan_ch)) == 63 and len(set(dan_ch) - set(val_ch)) == 18)
    check("B8 all changed KDB cells are FY2023 quarters", all(k[2].startswith("2023.") for k in r["changed"]),
          "quarters %s" % by_quarter(r["changed"], 2))
    pl_res = r
    # self-test of the checker: a mutated non-KDB cell must be caught
    mut = json.loads(json.dumps(cpl))
    for row in mut:
        if row["원보험사코드"] != CODE and isinstance(row.get("값"), (int, float)):
            row["값"] = row["값"] + 1
            break
    rm = analyze(bpl, mut, kf)
    check("B9 self-test: a mutated non-KDB cell is detected by the checker", len(rm["non_kdb_touched"]) == 1,
          "detected %d" % len(rm["non_kdb_touched"]))
    say("")

    # ------------------------------------------------------------------ C. CSM_waterfall
    say("== C. CSM_waterfall.json (cell = code, item, quarter)")
    bcs = rd_json(P(BK, "CSM_waterfall.json"))
    ccs = rd_json(P(CUR, "CSM_waterfall.json"))
    r = analyze(bcs, ccs, kf)
    check("C1 no duplicate cell keys", r["dups_old"] == 0 and r["dups_new"] == 0)
    check("C2 row count unchanged", not r["added"] and not r["removed"] and r["n_old"] == r["n_new"],
          "rows %d -> %d" % (r["n_old"], r["n_new"]))
    check("C3 every changed cell is KR0072", not r["non_kdb_touched"], "non-KDB touched: %d" % len(r["non_kdb_touched"]))
    fields = sorted(set(f for fs in r["changed"].values() for f in fs))
    check("C4 only fields 값 / 값_당분기 changed", set(fields) <= {"값", "값_당분기"}, "fields changed: %s" % fields)
    check("C5 non-KDB rows identical and in the same order", r["non_kdb_order_same"], "non-KDB rows %d" % r["non_kdb_count"])
    val_ch = [k for k, fs in r["changed"].items() if "값" in fs]
    dan_ch = [k for k, fs in r["changed"].items() if "값_당분기" in fs]
    say("   KR0072 cells with 값 changed: %d  by quarter %s" % (len(val_ch), by_quarter(val_ch, 2)))
    say("   KR0072 cells with 값_당분기 changed: %d  by quarter %s" % (len(dan_ch), by_quarter(dan_ch, 2)))
    check("C6 CLAIM loader: CSM 값 20 (1Q 6, 2Q 6, 3Q 6, 4Q 2)",
          len(val_ch) == 20 and by_quarter(val_ch, 2) == {"2023.1Q": 6, "2023.2Q": 6, "2023.3Q": 6, "2023.4Q": 2})
    check("C7 CLAIM loader: CSM 값_당분기 23", len(dan_ch) == 23, "measured %d" % len(dan_ch))
    check("C8 all changed KDB cells are FY2023 quarters", all(k[2].startswith("2023.") for k in r["changed"]),
          "quarters %s" % by_quarter(r["changed"], 2))
    cs_res = r
    say("")

    # ------------------------------------------------------------------ D. provenance (PL)
    say("== D. PL_breakdown_provenance.json (cells = company_code, quarter, item_block)")
    pkf = lambda c: (c.get("company_code"), c.get("quarter"), c.get("item_block"))
    bpp = rd_json(P(BK, "PL_breakdown_provenance.json"))
    cpp = rd_json(P(CUR, "PL_breakdown_provenance.json"))
    t = top_level(bpp, cpp)
    say("   top-level: added %s  removed %s  changed %s  order_same %s" % (t["added"], t["removed"], t["changed"], t["order_same"]))
    check("D1 top level: only the KDB merge note was added, only `cells` changed",
          t["added"] == ["merge_note_20261023_e23_kr0072_kdb"] and not t["removed"] and t["changed"] == ["cells"] and t["order_same"])
    r = analyze(bpp["cells"], cpp["cells"], pkf)
    check("D2 cells: nothing added/removed, count unchanged", not r["added"] and not r["removed"] and r["n_old"] == r["n_new"],
          "cells %d -> %d" % (r["n_old"], r["n_new"]))
    check("D3 every changed cell block is KR0072", not r["non_kdb_touched"], "non-KDB touched %d" % len(r["non_kdb_touched"]))
    check("D4 non-KDB cell blocks identical and in the same order", r["non_kdb_order_same"], "non-KDB blocks %d" % r["non_kdb_count"])
    say("   KR0072 blocks changed: %s" % sorted((k[1], k[2]) for k in r["changed"]))
    check("D5 CLAIM loader: 5 KR0072 blocks replaced (2023.1Q contract_notes + income_statement, 2023.2Q/3Q/4Q income_statement)",
          sorted((k[1], k[2]) for k in r["changed"]) == sorted([("2023.1Q", "contract_notes"), ("2023.1Q", "income_statement"),
                                                               ("2023.2Q", "income_statement"), ("2023.3Q", "income_statement"),
                                                               ("2023.4Q", "income_statement")]))
    prov_pl_res = r
    say("")

    # ------------------------------------------------------------------ E. provenance (CSM)
    say("== E. CSM_waterfall_provenance.json")
    bcp = rd_json(P(BK, "CSM_waterfall_provenance.json"))
    ccp = rd_json(P(CUR, "CSM_waterfall_provenance.json"))
    t = top_level(bcp, ccp)
    say("   top-level: added %s  removed %s  changed %s  order_same %s" % (t["added"], t["removed"], t["changed"], t["order_same"]))
    check("E1 top level: only the KDB CSM merge note was added, only `cells` changed",
          t["added"] == ["merge_note_20261023_e23_kr0072_kdb_csm"] and not t["removed"] and t["changed"] == ["cells"] and t["order_same"])
    r = analyze(bcp["cells"], ccp["cells"], pkf)
    check("E2 cells: nothing added/removed, count unchanged", not r["added"] and not r["removed"] and r["n_old"] == r["n_new"],
          "cells %d -> %d" % (r["n_old"], r["n_new"]))
    check("E3 every changed cell block is KR0072", not r["non_kdb_touched"], "non-KDB touched %d" % len(r["non_kdb_touched"]))
    check("E4 non-KDB cell blocks identical and in the same order", r["non_kdb_order_same"], "non-KDB blocks %d" % r["non_kdb_count"])
    for k, fs in r["changed"].items():
        say("   changed block %s %s: %s" % (k[1], k[2], {f: v for f, v in fs.items()}))
    check("E5 CLAIM loader: 2023.3Q owner_override added, 2023.4Q cleared",
          sorted((k[1], tuple(sorted(fs))) for k, fs in r["changed"].items()) != [] and
          set(k[1] for k in r["changed"]) == {"2023.3Q", "2023.4Q"}, "changed quarters %s" % sorted(set(k[1] for k in r["changed"])))
    prov_cs_res = r
    say("")

    # ------------------------------------------------------------------ F. user_pl_cells
    say("== F. data/_gold/user_pl_cells.json")
    bg = rd_json(P(BK, "data/_gold/user_pl_cells.json"))
    cg = rd_json(P(CUR, "data/_gold/user_pl_cells.json"))
    t = top_level(bg, cg)
    say("   top-level: added %s  removed %s  changed %s" % (t["added"], t["removed"], t["changed"]))
    check("F1 top level: no key added/removed, only `set` and `set_dangi` changed",
          not t["added"] and not t["removed"] and t["changed"] == ["set", "set_dangi"] and t["order_same"])
    gkf = lambda e: (e["원보험사코드"], e["항목번호"], e["공시분기"])
    r = analyze(bg["set"], cg["set"], gkf)
    check("F2 set: no duplicate cell keys", r["dups_old"] == 0 and r["dups_new"] == 0)
    check("F3 set: no entry removed", not r["removed"], "removed %d" % len(r["removed"]))
    check("F4 set: every added/changed entry is KR0072", not r["non_kdb_touched"], "non-KDB touched %d" % len(r["non_kdb_touched"]))
    check("F5 set: non-KDB entries identical and in the same order", r["non_kdb_order_same"], "non-KDB entries %d" % r["non_kdb_count"])
    check("F6 CLAIM loader: set 1379 -> 1440 (61 new + 4 replaced)",
          r["n_old"] == 1379 and r["n_new"] == 1440 and len(r["added"]) == 61 and len(r["changed"]) == 4,
          "%d -> %d, added %d, changed %d" % (r["n_old"], r["n_new"], len(r["added"]), len(r["changed"])))
    gset_res = r
    check("F7 null_dangi identical (whole dict)", canon(bg["null_dangi"]) == canon(cg["null_dangi"]))
    sb, sc = bg["set_dangi"], cg["set_dangi"]
    t2 = top_level(sb, sc)
    say("   set_dangi top-level: added %s removed %s changed %s" % (t2["added"], t2["removed"], t2["changed"]))
    check("F8 set_dangi: only the KDB doc key added, only `cells` changed",
          t2["added"] == ["_doc_e23_kr0072_20261023"] and not t2["removed"] and t2["changed"] == ["cells"] and t2["order_same"])
    skf = lambda e: (e[0], e[1], e[2])
    r = analyze(sb["cells"], sc["cells"], skf)
    check("F9 set_dangi.cells: nothing removed/changed, only KR0072 entries added", not r["removed"] and not r["changed"] and not r["non_kdb_touched"],
          "added %d (all KR0072: %s)" % (len(r["added"]), all(k[0] == CODE for k in r["added"])))
    check("F10 set_dangi.cells: non-KDB entries identical and in the same order", r["non_kdb_order_same"])
    check("F11 CLAIM loader: set_dangi 37 -> 45 (+8)", len(sb["cells"]) + 8 == len(sc["cells"]) and len(r["added"]) == 8,
          "%d -> %d" % (len(sb["cells"]), len(sc["cells"])))
    say("")

    # ------------------------------------------------------------------ G. user_csm_cells
    say("== G. data/_gold/user_csm_cells.json")
    bm = rd_json(P(BK, "data/_gold/user_csm_cells.json"))
    cm = rd_json(P(CUR, "data/_gold/user_csm_cells.json"))
    t = top_level(bm, cm)
    say("   top-level: added %s  removed %s  changed %s" % (t["added"], t["removed"], t["changed"]))
    check("G1 top level: only the KDB doc key added, only `set` changed",
          t["added"] == ["_doc_e23_kr0072_20261023"] and not t["removed"] and t["changed"] == ["set"] and t["order_same"])
    r = analyze(bm["set"], cm["set"], gkf)
    check("G2 set: no duplicate cell keys", r["dups_old"] == 0 and r["dups_new"] == 0)
    check("G3 set: every added/changed/removed entry is KR0072", not r["non_kdb_touched"], "non-KDB touched %d" % len(r["non_kdb_touched"]))
    check("G4 set: non-KDB entries identical and in the same order", r["non_kdb_order_same"], "non-KDB entries %d" % r["non_kdb_count"])
    check("G5 CLAIM loader: set 417 -> 428 (13 new, 5 replaced, 2 removed)",
          r["n_old"] == 417 and r["n_new"] == 428 and len(r["added"]) == 13 and len(r["changed"]) == 5 and len(r["removed"]) == 2,
          "%d -> %d, added %d, changed %d, removed %d" % (r["n_old"], r["n_new"], len(r["added"]), len(r["changed"]), len(r["removed"])))
    gcsm_res = r
    say("")

    # ------------------------------------------------------------------ H. ledger
    say("== H. data/_gold/gold_overlay_ledger.json")
    bl = rd_json(P(BK, "data/_gold/gold_overlay_ledger.json"))
    cl = rd_json(P(CUR, "data/_gold/gold_overlay_ledger.json"))
    t = top_level(bl, cl)
    say("   top-level: added %s  removed %s  changed %s" % (t["added"], t["removed"], t["changed"]))
    check("H1 top level: only `entries` changed", not t["added"] and not t["removed"] and t["changed"] == ["entries"])
    be, ce = bl["entries"], cl["entries"]
    rem = sorted(set(be) - set(ce))
    add = sorted(set(ce) - set(be))
    chg = sorted(k for k in set(be) & set(ce) if canon(be[k]) != canon(ce[k]))
    say("   entries %d -> %d ; removed %s ; added %s ; changed %s" % (len(be), len(ce), rem, add, chg))
    check("H2 entries: exactly 3 removed, all KR0072 CSM pins; none added; none changed",
          rem == ["CSM|KR0072|2023.1Q|6", "CSM|KR0072|2023.2Q|4", "CSM|KR0072|2023.2Q|5"] and not add and not chg)
    check("H3 entries: remaining order identical", [k for k in be if k in ce] == list(ce))
    ledger_res = dict(removed=rem)
    say("")

    # ------------------------------------------------------------------ I. test file
    say("== I. tests/test_rule_coverage_manifest.py")
    bt = rd_text(P(BK, "tests/test_rule_coverage_manifest.py")).splitlines(keepends=True)
    ct = rd_text(P(CUR, "tests/test_rule_coverage_manifest.py")).splitlines(keepends=True)
    sm = difflib.SequenceMatcher(None, bt, ct, autojunk=False)
    rem_l, add_l = [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        rem_l += [x.rstrip("\r\n") for x in bt[i1:i2]]
        add_l += [x.rstrip("\r\n") for x in ct[j1:j2]]
    say("   removed lines: %d ; added lines: %d" % (len(rem_l), len(add_l)))
    for x in rem_l:
        say("   - " + x[:200])
    for x in add_l:
        say("   + " + x[:300])
    check("I1 removed lines are exactly the old GOLD_OVERLAY_CENSUS line",
          rem_l == ['GOLD_OVERLAY_CENSUS = {"CSM": (417, 77), "PL": (1379, 22)}'])
    check("I2 added lines are exactly the KDB comment line + the new GOLD_OVERLAY_CENSUS line",
          len(add_l) == 2 and add_l[0].startswith("# 2026-10-23 ticket 20261023T0900Z (parser/ifrs17, D3: 케이디비생명보험 KR0072")
          and add_l[1] == 'GOLD_OVERLAY_CENSUS = {"CSM": (428, 74), "PL": (1440, 22)}')
    say("")

    # ------------------------------------------------------------------ J. master_tables_golden
    say("== J. tests/fixtures/master_tables_golden.json")
    bj = rd_json(P(BK, "tests/fixtures/master_tables_golden.json"))
    cj = rd_json(P(CUR, "tests/fixtures/master_tables_golden.json"))
    t = top_level(bj, cj)
    check("J1 only `summary` changed", t["changed"] == ["summary"] and not t["added"] and not t["removed"])
    tok_b = [x.strip() for x in bj["summary"].split("|")]
    tok_c = [x.strip() for x in cj["summary"].split("|")]
    diff_tok = [(a, b) for a, b in zip(tok_b, tok_c) if a != b]
    say("   summary tokens changed:")
    for a, b in diff_tok:
        say("     %s  ->  %s" % (a, b))
    check("J2 same token count; changed tokens are exactly pl_bridge, qoq_warn, oci_vs_bs_aoci",
          len(tok_b) == len(tok_c) and [a.split(":")[0] for a, _ in diff_tok] == ["pl_bridge", "qoq_warn", "oci_vs_bs_aoci"])
    say("")

    # ------------------------------------------------------------------ K. builder fingerprints
    say("== K. tests/fixtures/builder_input_fingerprints.json")
    bf = rd_json(P(BK, "tests/fixtures/builder_input_fingerprints.json"))
    cf = rd_json(P(CUR, "tests/fixtures/builder_input_fingerprints.json"))
    t = top_level(bf, cf)
    check("K1 only `specs` changed", t["changed"] == ["specs"] and not t["added"] and not t["removed"])
    ts = top_level(bf["specs"], cf["specs"])
    check("K2 only specs.viz_ifrs17_panels changed", ts["changed"] == ["viz_ifrs17_panels"] and not ts["added"] and not ts["removed"], str(ts["changed"]))
    tv = top_level(bf["specs"]["viz_ifrs17_panels"], cf["specs"]["viz_ifrs17_panels"])
    check("K3 within it only inputs_sha256 and input_bytes changed", tv["changed"] == ["input_bytes", "inputs_sha256"] and not tv["added"] and not tv["removed"], str(tv["changed"]))
    d_bytes = cf["specs"]["viz_ifrs17_panels"]["input_bytes"] - bf["specs"]["viz_ifrs17_panels"]["input_bytes"]
    d_file = os.path.getsize(P(CUR, "CSM_waterfall.json")) - os.path.getsize(P(BK, "CSM_waterfall.json"))
    check("K4 input_bytes delta equals the CSM_waterfall.json size delta (it is an input of that builder)", d_bytes == d_file, "delta %d vs %d" % (d_bytes, d_file))
    say("")

    # ------------------------------------------------------------------ L. warn files
    say("== L. regenerated side effects (rows of the gate warn lists)")
    for rel, label in (("data/_derived/qoq_warn.json", "L1 qoq_warn"), ("data/_derived/pl_oci_vs_bs_aoci_warn.json", "L2 oci_vs_bs_aoci_warn")):
        bw, cw = rd_json(P(BK, rel)), rd_json(P(CUR, rel))
        cb = collections.Counter(canon(x) for x in bw)
        cc = collections.Counter(canon(x) for x in cw)
        gone = list((cb - cc).elements())
        new = list((cc - cb).elements())
        comp = lambda s: json.loads(s)["company"]
        non_kdb = [s for s in gone + new if comp(s) != kdb_name]
        seq_b = [canon(x) for x in bw if x["company"] != kdb_name]
        seq_c = [canon(x) for x in cw if x["company"] != kdb_name]
        say("   %s: rows %d -> %d ; rows gone %d ; rows new %d ; non-KDB rows touched %d" % (rel, len(bw), len(cw), len(gone), len(new), len(non_kdb)))
        check(label + " only %s rows differ" % kdb_name, not non_kdb)
        check(label + " non-KDB rows identical and in the same order", seq_b == seq_c, "%d rows" % len(seq_b))
    say("")

    # ------------------------------------------------------------------ M. summary
    n_fail = sum(1 for _, ok, _ in RESULTS if not ok)
    say("== SUMMARY  checks %d  PASS %d  FAIL %d" % (len(RESULTS), len(RESULTS) - n_fail, n_fail))
    say("ALL PASS" if n_fail == 0 else "FAILED: " + ", ".join(n for n, ok, _ in RESULTS if not ok))

    text = "\n".join(LOG) + "\n"
    with open("%s/k01_prove_kdb_only%s.txt" % (EVD, TAG), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    with open("%s/k01_prove_kdb_only%s.json" % (EVD, TAG), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(dict(cur_root=CUR, n_checks=len(RESULTS), n_fail=n_fail,
                       checks=[dict(name=n, ok=ok, detail=d) for n, ok, d in RESULTS]),
                  fh, ensure_ascii=False, indent=1)
    sys.stdout.reconfigure(encoding="utf-8")
    print(text)
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
