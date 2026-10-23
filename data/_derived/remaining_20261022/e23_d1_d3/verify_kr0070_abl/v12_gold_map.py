import json, subprocess, collections, re
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
OUT = ROOT + "/data/_derived/remaining_20261022/e23_d1_d3/verify_kr0070_abl/"
def head(path):
    return json.loads(subprocess.run(["git", "-C", ROOT, "show", "HEAD:" + path], capture_output=True).stdout.decode("utf-8"))
L = []
def P(s): L.append(s)
for tag, gpath, mpath in (("PL", "data/_gold/user_pl_cells.json", "PL_breakdown.json"), ("CSM", "data/_gold/user_csm_cells.json", "CSM_waterfall.json")):
    gh = head(gpath); gw = json.load(open(ROOT + "/" + gpath, encoding="utf-8"))
    mh = {(r["공시분기"], r["항목번호"]): r for r in head(mpath) if r["원보험사코드"] == "KR0070"}
    mw = {(r["공시분기"], r["항목번호"]): r for r in json.load(open(ROOT + "/" + mpath, encoding="utf-8")) if r["원보험사코드"] == "KR0070"}
    sh = {(e["공시분기"], e["항목번호"]): e for e in gh["set"] if e["원보험사코드"] == "KR0070"}
    sw = {(e["공시분기"], e["항목번호"]): e for e in gw["set"] if e["원보험사코드"] == "KR0070"}
    dup = collections.Counter((e["공시분기"], e["항목번호"]) for e in gw["set"] if e["원보험사코드"] == "KR0070")
    P("== %s: KR0070 set entries HEAD %d WORK %d; duplicate keys in WORK %s" % (tag, len(sh), len(sw), [k for k, c in dup.items() if c > 1]))
    removed = [k for k in sh if k not in sw]; added = [k for k in sw if k not in sh]
    changed = [k for k in sh if k in sw and sh[k] != sw[k]]
    P("   removed %s ; added %d ; changed-in-place %s" % (sorted(removed), len(added), sorted(changed)))
    # master cells whose 값 changed
    mchg = {k for k in mw if k in mh and mh[k]["값"] != mw[k]["값"]} | {k for k in mw if k not in mh}
    P("   master 값 changed cells: %d" % len(mchg))
    new_keys = set(added) | set(changed)
    P("   gold new/changed keys == master changed keys? only-gold %s ; only-master %s" % (sorted(new_keys - mchg), sorted(mchg - new_keys)))
    # per-entry checks
    bad = 0
    for k in sorted(new_keys):
        e = sw[k]; m = mw[k]["값"]; hv = mh.get(k, {}).get("값")
        okv = abs(e["값"] - m) < 1e-9
        okw = (e.get("was") == hv) or (e.get("was") is not None and hv is not None and abs(e["was"] - hv) < 1e-9)
        note = e.get("note") or e.get("why") or ""
        okn = "2026-10-23" in note and ("owner" in note)
        if not (okv and okw and okn):
            bad += 1; P("   ENTRY ISSUE %s val_ok=%s was_ok=%s (was=%s headmaster=%s) note_ok=%s" % (k, okv, okw, e.get("was"), hv, okn))
    P("   entry checks: %d entries, issues %d" % (len(new_keys), bad))
    # key set of removed entries: check master equals approved
    for k in sorted(removed):
        P("   removed entry %s HEAD gold 값=%s was=%s ; master now %s ; HEAD master %s" % (k, sh[k]["값"], sh[k].get("was"), mw[k]["값"], mh[k]["값"]))
    # other KR0070 entries unchanged?
    keep = [k for k in sh if k in sw and sh[k] == sw[k]]
    P("   untouched KR0070 entries: %d" % len(keep))
    # other companies' entries touched? (not our scope but ensure KR0070 only inside our change set) -> count foreign changes just for reference
    hs = collections.Counter(e.get("원보험사코드") for e in gh["set"]); ws = collections.Counter(e.get("원보험사코드") for e in gw["set"])
    P("   set-entry count by company changes (HEAD->WORK): %s" % {c: (hs.get(c, 0), ws.get(c, 0)) for c in set(hs) | set(ws) if hs.get(c, 0) != ws.get(c, 0)})
# provenance OWNER_GOLD in HEAD for other companies?
ph = head("PL_breakdown_provenance.json")["cells"]
P("HEAD PL provenance cells with source_id OWNER_GOLD: %d (companies %s)" % (len([c for c in ph if c["source_id"] == "OWNER_GOLD"]), sorted({c["company_code"] for c in ph if c["source_id"] == "OWNER_GOLD"})))
open(OUT + "v12_gold_map.txt", "w", encoding="utf-8").write("\n".join(L))
print("\n".join(L))
