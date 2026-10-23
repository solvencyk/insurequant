# -*- coding: utf-8 -*-
"""Peek at the nested gold / ledger / provenance structures (read-only)."""
import json
import sys

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
OUT = ROOT + "/data/_derived/remaining_20261022/e23_d1_d3/kdb_restore/k00b_peek_gold_ledger.txt"


def short(v, n=500):
    s = json.dumps(v, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + "...(%d chars)" % len(s)


def load(p):
    with open(ROOT + "/" + p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def main():
    out = []
    pl = load("data/_gold/user_pl_cells.json")
    for k in ("null_dangi", "set_dangi"):
        d = pl[k]
        out.append("== user_pl_cells.%s: %d keys" % (k, len(d)))
        for kk, vv in d.items():
            if isinstance(vv, list):
                out.append("   [%s] list len=%d first=%s" % (kk, len(vv), short(vv[0] if vv else None, 400)))
            elif isinstance(vv, dict):
                out.append("   [%s] dict len=%d keys(first 6)=%s" % (kk, len(vv), short(list(vv.keys())[:6], 300)))
            else:
                out.append("   [%s] %s: %s" % (kk, type(vv).__name__, short(vv, 200)))
    out.append("== user_pl_cells.set entry fields (first KR0072 entry)")
    for e in pl["set"]:
        if e.get("원보험사코드") == "KR0072":
            out.append("   " + short(e, 900))
            break
    csm = load("data/_gold/user_csm_cells.json")
    out.append("== user_csm_cells.set entry fields (first KR0072 entry)")
    for e in csm["set"]:
        if e.get("원보험사코드") == "KR0072":
            out.append("   " + short(e, 900))
            break
    led = load("data/_gold/gold_overlay_ledger.json")
    for k in ("_measured_at", "_population", "_tolerance"):
        out.append("== ledger.%s = %s" % (k, short(led.get(k), 900)))
    ents = led["entries"]
    out.append("== ledger.entries type=%s len=%d" % (type(ents).__name__, len(ents)))
    if isinstance(ents, list):
        out.append("   first=" + short(ents[0], 700))
        k72 = [e for e in ents if "KR0072" in json.dumps(e, ensure_ascii=False)]
        out.append("   KR0072 entries (current): %d" % len(k72))
        for e in k72:
            out.append("     " + short(e, 600))
    elif isinstance(ents, dict):
        ks = list(ents.keys())
        out.append("   first keys=" + short(ks[:5], 400))
        k72 = [k for k in ks if "KR0072" in k]
        out.append("   KR0072 keys (current): %d -> %s" % (len(k72), short(k72, 800)))
    pp = load("PL_breakdown_provenance.json")
    cells = pp["cells"]
    out.append("== PL_breakdown_provenance.cells len=%d first=%s" % (len(cells), short(cells[0], 700)))
    k72 = [c for c in cells if c.get("company_code") == "KR0072"]
    out.append("   KR0072 cells: %d" % len(k72))
    for c in k72[:8]:
        out.append("     " + short(c, 500))
    for k in pp:
        if k.startswith("merge_note_20261023"):
            out.append("   key %s: %s" % (k, short(pp[k], 400)))
    cp = load("CSM_waterfall_provenance.json")
    k72 = [c for c in cp["cells"] if c.get("company_code") == "KR0072"]
    out.append("== CSM_waterfall_provenance KR0072 cells: %d" % len(k72))
    for c in k72:
        out.append("     " + short(c, 500))
    for k in cp:
        if k.startswith("merge_note_20261023"):
            out.append("   key %s: %s" % (k, short(cp[k], 300)))
    text = "\n".join(out) + "\n"
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    sys.stdout.reconfigure(encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
