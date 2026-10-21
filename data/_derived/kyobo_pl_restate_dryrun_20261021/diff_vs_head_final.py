"""Read-only, independent of the apply scripts: JSON-level diff of every file this ticket changed, working tree vs git HEAD (cumulative = E5 + R + PL refresh).

Output: per file the number of changed cells/entries, the companies touched, and the exact changed-key lists (written to diff_vs_head_final.txt).
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")


def head(rel):
    p = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{rel}"], capture_output=True)
    if p.returncode != 0:
        raise SystemExit(f"git show failed for {rel}: {p.stderr.decode('utf-8', 'replace')[:200]}")
    return json.loads(p.stdout.decode("utf-8"))


def cur(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


out = []


def say(s=""):
    print(s)
    out.append(s)


def rows_diff(rel, fields):
    a, b = head(rel), cur(rel)
    key = lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"])
    ka, kb = {key(r): r for r in a}, {key(r): r for r in b}
    say(f"== {rel}: rows HEAD {len(a)} / now {len(b)}; only-in-HEAD {len(set(ka) - set(kb))}; only-now {len(set(kb) - set(ka))}; order same: {[key(r) for r in a] == [key(r) for r in b]}")
    changed = {}
    other_field = []
    for k in ka:
        if k not in kb:
            continue
        ra, rb = ka[k], kb[k]
        diff_f = [f for f in set(ra) | set(rb) if ra.get(f) != rb.get(f)]
        if diff_f:
            changed[k] = diff_f
            other_field += [f for f in diff_f if f not in fields]
    cos = sorted({k[0] for k in changed})
    say(f"   changed cells (rows): {len(changed)} in companies {cos}; fields touched: {sorted({f for v in changed.values() for f in v})}; unexpected fields: {sorted(set(other_field))}")
    by_field = {f: sum(1 for v in changed.values() if f in v) for f in fields}
    say(f"   per field: {by_field}")
    by_q = {}
    for (c, i, q) in changed:
        by_q.setdefault(q, []).append(i)
    say("   by quarter: " + "; ".join(f"{q}: {len(v)}" for q, v in sorted(by_q.items(), key=lambda x: (int(x[0][:4]), int(x[0][5])))))
    return changed


def gold_diff(rel):
    a, b = head(rel), cur(rel)
    key = lambda e: (e["원보험사코드"], e["항목번호"], e["공시분기"])
    ka, kb = {key(e): e for e in a["set"]}, {key(e): e for e in b["set"]}
    add = sorted(set(kb) - set(ka), key=lambda x: (x[2], x[1]))
    rem = sorted(set(ka) - set(kb))
    upd = sorted((k for k in set(ka) & set(kb) if ka[k] != kb[k]), key=lambda x: (x[2], x[1]))
    other_keys = {k: (a[k] == b[k]) for k in set(a) | set(b) if k != "set"}
    say(f"== {rel}: entries HEAD {len(ka)} / now {len(kb)}; added {len(add)}, updated {len(upd)}, removed {len(rem)}; companies touched {sorted({k[0] for k in add + upd + rem})}; other top-level keys unchanged: {all(other_keys.values())}")
    return add, upd, rem


def dict_diff(rel, sub=None):
    a, b = head(rel), cur(rel)
    if sub:
        a, b = a[sub], b[sub]
    add, rem = sorted(set(b) - set(a)), sorted(set(a) - set(b))
    upd = sorted(k for k in set(a) & set(b) if a[k] != b[k])
    say(f"== {rel}{'['+sub+']' if sub else ''}: entries HEAD {len(a)} / now {len(b)}; added {len(add)} {add[:6]}; removed {len(rem)} {rem[:15]}; updated {len(upd)} {upd[:6]}")


def prov_diff(rel):
    a, b = head(rel), cur(rel)
    ka = {(c["company_code"], c["quarter"], c["item_block"]): c for c in a["cells"]}
    kb = {(c["company_code"], c["quarter"], c["item_block"]): c for c in b["cells"]}
    upd = sorted((k for k in ka if k in kb and ka[k] != kb[k]), key=lambda x: (x[0], x[1], x[2]))
    top = sorted(k for k in set(a) | set(b) if k != "cells" and a.get(k) != b.get(k))
    say(f"== {rel}: cells HEAD {len(ka)} / now {len(kb)}; added {len(set(kb) - set(ka))}, removed {len(set(ka) - set(kb))}, changed {len(upd)}; companies {sorted({k[0] for k in upd})}; top-level keys changed/added: {top}")
    say("   changed blocks: " + "; ".join(f"{k[0]} {k[1]} {k[2]}" for k in upd))


rows_diff("CSM_waterfall.json", ["값", "값_당분기"])
rows_diff("PL_breakdown.json", ["값", "값_당분기"])
gold_diff("data/_gold/user_csm_cells.json")
gold_diff("data/_gold/user_pl_cells.json")
dict_diff("data/_gold/gold_overlay_ledger.json", "entries")
dict_diff("data/_gold/csm_amort_identity_ledger.json", "entries")
prov_diff("CSM_waterfall_provenance.json")
prov_diff("PL_breakdown_provenance.json")
(HERE / "diff_vs_head_final.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
