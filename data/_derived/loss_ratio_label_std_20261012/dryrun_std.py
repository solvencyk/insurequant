"""Dry run (no writes to data/loss_ratio): rebuild the master in memory with the reinsurer segment standard and diff it against the committed master.
Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/loss_ratio_label_std_20261012/dryrun_std.py
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import build_loss_ratio_master as M  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
OUT = Path(__file__).resolve().parent
LR = ROOT / "data" / "loss_ratio"
NEW = [f"KR110{i}" for i in range(1, 8)]
SEGFIELDS = ("세그먼트", "상품구분")


def load_src():
    p = LR / "risk_premium_vs_expected_claims.json"
    gz = LR / "risk_premium_vs_expected_claims.json.gz"
    return M.read_json(gz if gz.exists() else p)


def main():
    log = []

    def P(s=""):
        log.append(s)
        print(s)

    src = load_src()
    census = M.read_csv(LR / "census.csv")
    reg = M.load_registry()
    old = json.loads((LR / "master_loss_ratio.json").read_text(encoding="utf-8"))
    res = M.build_from(src, census, reg)
    pub = [M.public_row(r) for r in res["master"]]
    P(f"old master {len(old)} rows; new master {len(pub)} rows")
    old_non = [r for r in old if r["원보험사코드"] not in NEW]
    new_non = [r for r in pub if r["원보험사코드"] not in NEW]
    P(f"non-reinsurer rows: old {len(old_non)} new {len(new_non)} identical(list equality, order+values): {old_non == new_non}")
    old_re = [r for r in old if r["원보험사코드"] in NEW]
    new_re = [r for r in pub if r["원보험사코드"] in NEW]
    P(f"reinsurer rows: old {len(old_re)} new {len(new_re)}")

    def other_key(r):
        return tuple((k, json.dumps(r[k], ensure_ascii=False)) for k in M.ALL_COLS if k not in SEGFIELDS)
    co, cn = Counter(other_key(r) for r in old_re), Counter(other_key(r) for r in new_re)
    P(f"reinsurer rows identical on the other {len(M.ALL_COLS) - 2} fields (multiset): {co == cn}  (only-old {sum((co - cn).values())}, only-new {sum((cn - co).values())})")
    # per-row old->new mapping via the other-fields key (unique? check)
    by_old = defaultdict(list)
    for r in old_re:
        by_old[other_key(r)].append(r)
    by_new = defaultdict(list)
    for r in new_re:
        by_new[other_key(r)].append(r)
    dup = [k for k, v in by_old.items() if len(v) > 1]
    P(f"rows whose other-field key is not unique (old): {len(dup)}")
    trans = Counter()
    changed_rows = Counter()
    for k, olist in by_old.items():
        nlist = by_new.get(k, [])
        if len(olist) != 1 or len(nlist) != 1:
            continue
        o, n = olist[0], nlist[0]
        d = tuple(f for f in SEGFIELDS if o[f] != n[f])
        changed_rows[d] += 1
        trans[(o["원보험사코드"], o["세그먼트"], o["상품구분"], "->", n["세그먼트"], n["상품구분"])] += 1
    P(f"changed field sets (row counts): {dict(changed_rows)}")
    for k, v in sorted(trans.items()):
        P(f"   {' | '.join(map(str, k))} : {v}")
    errs, warns, stats = M.verify(src, pub)
    P(f"verify: errs {len(errs)}, warns {len(warns)}, stats { {k: v for k, v in stats.items() if k != 'src_dups'} }")
    for e in errs[:20]:
        P("   ERR " + e[:240])
    # master key uniqueness
    keys = Counter((r["원보험사코드"], r["공시분기"], r["세그먼트"], r["경과차년"], r["구분"], r["상품구분"], r["포트폴리오"]) for r in pub)
    P(f"master key duplicates: {sum(1 for v in keys.values() if v > 1)}")
    (OUT / "dryrun_std.txt").write_text("\n".join(log), encoding="utf-8")
    (OUT / "dryrun_new_reinsurer_rows.json").write_text(json.dumps(new_re, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
