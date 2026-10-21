"""Read-only: JSON-level cell diff of the working-tree files vs git HEAD (independent of the apply script).

Prints, for CSM_waterfall.json: every row whose any field differs (key, field, old, new), rows added/removed;
for user_csm_cells.json: every `set` entry that differs (value/why/was), added, removed; for the ledgers/provenance: key-level differences.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")


def head(rel):
    out = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT, capture_output=True)
    if out.returncode != 0:
        raise SystemExit(f"git show failed for {rel}: {out.stderr.decode('utf-8', 'replace')[:200]}")
    return json.loads(out.stdout.decode("utf-8"))


def work(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def diff_rows(rel):
    a, b = head(rel), work(rel)
    ka = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in a}
    kb = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in b}
    print(f"[{rel}] rows HEAD={len(a)} work={len(b)} added={len(set(kb) - set(ka))} removed={len(set(ka) - set(kb))}")
    n = 0
    companies = set()
    for k in sorted(ka, key=lambda x: (x[0], x[2], x[1])):
        if k in kb and ka[k] != kb[k]:
            for f in sorted(set(ka[k]) | set(kb[k])):
                if ka[k].get(f) != kb[k].get(f):
                    print(f"   {k[0]} {k[2]} item{k[1]} {f}: {ka[k].get(f)!r} -> {kb[k].get(f)!r}")
                    n += 1
                    companies.add(k[0])
    print(f"   field changes: {n}; companies touched: {sorted(companies)}")


def diff_gold(rel):
    a, b = head(rel), work(rel)
    print(f"[{rel}] top-level keys equal except set: {all(a[k] == b[k] for k in a if k != 'set')}; set len HEAD={len(a['set'])} work={len(b['set'])}")
    ka = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in a["set"]}
    kb = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): e for e in b["set"]}
    print(f"   added={sorted(set(kb) - set(ka))} removed={sorted(set(ka) - set(kb))}")
    for k in sorted(ka, key=lambda x: (x[0], x[2], x[1])):
        if k in kb and ka[k] != kb[k]:
            changed = [f for f in set(ka[k]) | set(kb[k]) if ka[k].get(f) != kb[k].get(f)]
            print(f"   {k[0]} {k[2]} item{k[1]}: changed fields {sorted(changed)}; 값 {ka[k].get('값')} -> {kb[k].get('값')}")
    order_same = [(e["원보험사코드"], e["항목번호"], e["공시분기"]) for e in a["set"]] == [(e["원보험사코드"], e["항목번호"], e["공시분기"]) for e in b["set"]]
    print(f"   entry order unchanged: {order_same}")


def diff_dict(rel, path):
    a, b = head(rel), work(rel)
    for p in path:
        a, b = a[p], b[p]
    removed = sorted(set(a) - set(b))
    added = sorted(set(b) - set(a))
    changed = sorted(k for k in a if k in b and a[k] != b[k])
    print(f"[{rel}:{'/'.join(path)}] removed={removed} added={added} changed={changed}")


def diff_prov(rel):
    a, b = head(rel), work(rel)
    print(f"[{rel}] top keys HEAD={list(a)} work={list(b)}")
    ca = {(c["company_code"], c["quarter"], c["item_block"]): c for c in a["cells"]}
    cb = {(c["company_code"], c["quarter"], c["item_block"]): c for c in b["cells"]}
    print(f"   cells HEAD={len(ca)} work={len(cb)} added={sorted(set(cb) - set(ca))} removed={sorted(set(ca) - set(cb))}")
    for k in sorted(ca):
        if k in cb and ca[k] != cb[k]:
            print(f"   {k}: {ca[k]} -> {cb[k]}")


def main():
    diff_rows("CSM_waterfall.json")
    diff_gold("data/_gold/user_csm_cells.json")
    diff_dict("data/_gold/csm_amort_identity_ledger.json", ["entries"])
    diff_dict("data/_gold/gold_overlay_ledger.json", ["entries"])
    diff_prov("CSM_waterfall_provenance.json")


if __name__ == "__main__":
    main()
