# -*- coding: utf-8 -*-
"""k03: per-company cell counts vs git HEAD, KR0072 vs HEAD, other four vs post-load snapshot.

Read-only.  Usage:
    python k03_vs_head.py MODE [ROOT]
MODE = pre   (before the restore: KR0072 is expected to differ from HEAD)
     = post  (after the restore:  KR0072 must be identical to HEAD)
ROOT defaults to the live working tree.
"""
import collections
import json
import sys

REPO = "C:/Users/sangwook.cho/Desktop/insurequant"
E23 = REPO + "/data/_derived/remaining_20261022/e23_d1_d3"
EVD = E23 + "/kdb_restore"
HEAD = EVD + "/head_copies"
SNAP = E23 + "/kr0072_kdb_load2/post_load_copies"
CODE = "KR0072"

MODE = sys.argv[1] if len(sys.argv) > 1 else "post"
ROOT = sys.argv[2] if len(sys.argv) > 2 else REPO

# owner-stated expectations for the four companies that stay loaded
FOUR = collections.OrderedDict([
    ("KR0099", ("KB라이프생명", 60, 15)),
    ("KR0003", ("롯데손해보험", 18, 5)),
    ("KR0070", ("에이비엘생명보험", 74, 20)),
    ("KR0009", ("현대해상", 57, 18)),
])

LOG = []
RESULTS = []


def say(s=""):
    LOG.append(s)


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    say("%s  %s%s" % ("PASS" if ok else "FAIL", name, (" :: " + detail) if detail else ""))


def canon(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True)


def rd(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def cells(rows):
    out = {}
    for r in rows:
        k = (r["원보험사코드"], r["항목번호"], r["공시분기"])
        assert k not in out, k
        out[k] = r
    return out


def diff_counts(head_rows, cur_rows):
    """per company: {value_diff, dangi_diff, any_diff, only_cur, only_head}."""
    h, c = cells(head_rows), cells(cur_rows)
    res = collections.defaultdict(lambda: collections.Counter())
    for k in set(h) | set(c):
        co = k[0]
        if k not in h:
            res[co]["only_cur"] += 1
            continue
        if k not in c:
            res[co]["only_head"] += 1
            continue
        a, b = h[k], c[k]
        if canon(a) == canon(b):
            continue
        res[co]["any_diff"] += 1
        if canon(a.get("값")) != canon(b.get("값")):
            res[co]["value_diff"] += 1
        if canon(a.get("값_당분기")) != canon(b.get("값_당분기")):
            res[co]["dangi_diff"] += 1
        others = [f for f in set(a) | set(b) if f not in ("값", "값_당분기") and canon(a.get(f)) != canon(b.get(f))]
        if others:
            res[co]["other_field_diff"] += 1
    return res


def kdb_rows(rows):
    return [r for r in rows if r["원보험사코드"] == CODE]


def main():
    say("k03 vs HEAD  MODE=%s  ROOT=%s" % (MODE, ROOT))
    say("")
    pl_head, pl_cur = rd(HEAD + "/PL_breakdown.json"), rd(ROOT + "/PL_breakdown.json")
    cs_head, cs_cur = rd(HEAD + "/CSM_waterfall.json"), rd(ROOT + "/CSM_waterfall.json")
    plc, csc = diff_counts(pl_head, pl_cur), diff_counts(cs_head, cs_cur)

    say("== 1. every company that differs from HEAD (cells with a different row)")
    allco = sorted(set(plc) | set(csc))
    say("   %-8s %-18s | PL 값 | PL 당분기 | PL any | PL only_cur/head | CSM 값 | CSM 당분기 | CSM any | CSM only_cur/head" % ("code", "name"))
    names = {r["원보험사코드"]: r["원수사명"] for r in pl_cur}
    for co in allco:
        p, c = plc.get(co, collections.Counter()), csc.get(co, collections.Counter())
        say("   %-8s %-18s | %5d | %9d | %6d | %d/%d | %6d | %10d | %7d | %d/%d" % (
            co, names.get(co, "?"), p["value_diff"], p["dangi_diff"], p["any_diff"], p["only_cur"], p["only_head"],
            c["value_diff"], c["dangi_diff"], c["any_diff"], c["only_cur"], c["only_head"]))
    say("")

    say("== 2. the four companies that stay loaded: 값 cells different from HEAD (owner-stated expectation)")
    for co, (nm, pl_exp, cs_exp) in FOUR.items():
        p, c = plc.get(co, collections.Counter()), csc.get(co, collections.Counter())
        check("2 %s %s PL 값 cells vs HEAD == %d" % (co, nm, pl_exp), p["value_diff"] == pl_exp, "measured %d" % p["value_diff"])
        check("2 %s %s CSM 값 cells vs HEAD == %d" % (co, nm, cs_exp), c["value_diff"] == cs_exp, "measured %d" % c["value_diff"])
        check("2 %s %s no cell added/removed vs HEAD, no field other than 값/값_당분기" % (co, nm),
              not (p["only_cur"] or p["only_head"] or c["only_cur"] or c["only_head"] or p["other_field_diff"] or c["other_field_diff"]))
    say("")

    say("== 3. KR0072 vs HEAD (masters)")
    p, c = plc.get(CODE, collections.Counter()), csc.get(CODE, collections.Counter())
    say("   KR0072 PL: 값 diff %d, 값_당분기 diff %d, any %d ; CSM: 값 diff %d, 값_당분기 diff %d, any %d" % (
        p["value_diff"], p["dangi_diff"], p["any_diff"], c["value_diff"], c["dangi_diff"], c["any_diff"]))
    hk, ck = kdb_rows(pl_head), kdb_rows(pl_cur)
    say("   KR0072 PL rows HEAD %d, current %d ; CSM rows HEAD %d, current %d" % (len(hk), len(ck), len(kdb_rows(cs_head)), len(kdb_rows(cs_cur))))
    if MODE == "post":
        check("3 KR0072 PL_breakdown.json: zero changed cells vs HEAD (all fields)", p["any_diff"] == 0 and not p["only_cur"] and not p["only_head"],
              "any %d only_cur %d only_head %d" % (p["any_diff"], p["only_cur"], p["only_head"]))
        check("3 KR0072 CSM_waterfall.json: zero changed cells vs HEAD (all fields)", c["any_diff"] == 0 and not c["only_cur"] and not c["only_head"],
              "any %d only_cur %d only_head %d" % (c["any_diff"], c["only_cur"], c["only_head"]))
        check("3 KR0072 PL rows identical to HEAD as a list (order too)", canon(hk) == canon(ck))
        check("3 KR0072 CSM rows identical to HEAD as a list (order too)", canon(kdb_rows(cs_head)) == canon(kdb_rows(cs_cur)))
    else:
        check("3(pre) KR0072 PL 값 cells differ from HEAD by the loaded 65", p["value_diff"] == 65, "measured %d" % p["value_diff"])
        check("3(pre) KR0072 CSM 값 cells differ from HEAD by the loaded 20", c["value_diff"] == 20, "measured %d" % c["value_diff"])
    say("")

    say("== 4. KR0072 gold / ledger / provenance vs HEAD")
    hg, cg = rd(HEAD + "/data/_gold/user_pl_cells.json"), rd(ROOT + "/data/_gold/user_pl_cells.json")
    hm, cm = rd(HEAD + "/data/_gold/user_csm_cells.json"), rd(ROOT + "/data/_gold/user_csm_cells.json")
    hl, cl = rd(HEAD + "/data/_gold/gold_overlay_ledger.json"), rd(ROOT + "/data/_gold/gold_overlay_ledger.json")
    hpp, cpp = rd(HEAD + "/PL_breakdown_provenance.json"), rd(ROOT + "/PL_breakdown_provenance.json")
    hcp, ccp = rd(HEAD + "/CSM_waterfall_provenance.json"), rd(ROOT + "/CSM_waterfall_provenance.json")

    def k72(lst, pos=None):
        if pos is None:
            return [e for e in lst if e.get("원보험사코드") == CODE]
        return [e for e in lst if e[pos] == CODE]

    pairs = [
        ("user_pl_cells.set", k72(hg["set"]), k72(cg["set"])),
        ("user_pl_cells.null_dangi.cells", k72(hg["null_dangi"]["cells"], 0), k72(cg["null_dangi"]["cells"], 0)),
        ("user_pl_cells.set_dangi.cells", k72(hg["set_dangi"]["cells"], 0), k72(cg["set_dangi"]["cells"], 0)),
        ("user_csm_cells.set", k72(hm["set"]), k72(cm["set"])),
        ("ledger.entries (keys with KR0072)", {k: v for k, v in hl["entries"].items() if "|KR0072|" in k},
         {k: v for k, v in cl["entries"].items() if "|KR0072|" in k}),
        ("PL provenance blocks", [c for c in hpp["cells"] if c.get("company_code") == CODE], [c for c in cpp["cells"] if c.get("company_code") == CODE]),
        ("CSM provenance blocks", [c for c in hcp["cells"] if c.get("company_code") == CODE], [c for c in ccp["cells"] if c.get("company_code") == CODE]),
    ]
    for name, a, b in pairs:
        same = canon(a) == canon(b)
        say("   %-38s HEAD %3d  current %3d  identical %s" % (name, len(a), len(b), same))
        if MODE == "post":
            check("4 KR0072 %s identical to HEAD" % name, same, "HEAD %d current %d" % (len(a), len(b)))
    kdb_keys_cur = [k for k in list(cg["set_dangi"]) + list(cm) + list(cpp) + list(ccp) if "kr0072" in k.lower()]
    kdb_keys_head = [k for k in list(hg["set_dangi"]) + list(hm) + list(hpp) + list(hcp) if "kr0072" in k.lower()]
    say("   keys naming kr0072 in gold / provenance files: HEAD %s ; current %s" % (kdb_keys_head, kdb_keys_cur))
    if MODE == "post":
        check("4 the set of kr0072-named doc / merge-note keys equals HEAD (the KDB-load keys are gone)",
              kdb_keys_cur == kdb_keys_head, "HEAD %s ; current %s" % (kdb_keys_head, kdb_keys_cur))
        loaded = [k for k in kdb_keys_cur if k in ("_doc_e23_kr0072_20261023", "merge_note_20261023_e23_kr0072_kdb", "merge_note_20261023_e23_kr0072_kdb_csm")]
        check("4 none of the three KDB-load keys is present", not loaded, str(loaded))
    say("")

    if MODE == "post":
        say("== 5. other companies: restored files vs the post-load snapshot (everything except KR0072 identical)")
        s_pl, s_cs = rd(SNAP + "/PL_breakdown.json"), rd(SNAP + "/CSM_waterfall.json")
        nk_pl_s = [r for r in s_pl if r["원보험사코드"] != CODE]
        nk_pl_c = [r for r in pl_cur if r["원보험사코드"] != CODE]
        nk_cs_s = [r for r in s_cs if r["원보험사코드"] != CODE]
        nk_cs_c = [r for r in cs_cur if r["원보험사코드"] != CODE]
        check("5 PL_breakdown.json non-KR0072 rows identical to snapshot (order too)", canon(nk_pl_s) == canon(nk_pl_c), "%d rows" % len(nk_pl_c))
        check("5 CSM_waterfall.json non-KR0072 rows identical to snapshot (order too)", canon(nk_cs_s) == canon(nk_cs_c), "%d rows" % len(nk_cs_c))
        sg, sm = rd(SNAP + "/data/_gold/user_pl_cells.json"), rd(SNAP + "/data/_gold/user_csm_cells.json")
        check("5 user_pl_cells.set non-KR0072 identical to snapshot", canon([e for e in sg["set"] if e["원보험사코드"] != CODE]) == canon([e for e in cg["set"] if e["원보험사코드"] != CODE]))
        check("5 user_csm_cells.set non-KR0072 identical to snapshot", canon([e for e in sm["set"] if e["원보험사코드"] != CODE]) == canon([e for e in cm["set"] if e["원보험사코드"] != CODE]))
        say("")

    n_fail = sum(1 for _, ok, _ in RESULTS if not ok)
    say("== SUMMARY  MODE=%s  checks %d  PASS %d  FAIL %d" % (MODE, len(RESULTS), len(RESULTS) - n_fail, n_fail))
    say("ALL PASS" if n_fail == 0 else "FAILED: " + ", ".join(n for n, ok, _ in RESULTS if not ok))
    text = "\n".join(LOG) + "\n"
    with open("%s/k03_vs_head_%s.txt" % (EVD, MODE), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    sys.stdout.reconfigure(encoding="utf-8")
    print(text)
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
