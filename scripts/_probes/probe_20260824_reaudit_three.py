"""Read-only re-audit probe for the three assigned exemption buckets.

  KR0097 2024.4Q  _AFTER_SUBRISK_NOT_DISCLOSED
  KR0049 2024.3Q  _POST_PARENT_NOT_DISCLOSED
  KR0079 2023.2Q  _LIFE8_ISSUER_INCONSISTENT

Prints the master cells and re-computes the axes that the exemption silences.
Nothing is written.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import validate_kics_disclosure as V  # noqa: E402
from solvency.validation.kics_json_rules import R4, R7, MARKET_M  # noqa: E402

TARGETS = [("KR0097", "2024.4Q"), ("KR0049", "2024.3Q"), ("KR0079", "2023.2Q")]


def _num(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def load_master():
    p = ROOT / "kics_disclosure.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) else d
    return recs


def build(recs):
    byq = {}
    name = {}
    for r in recs:
        c, q, it = r.get(V.KEY_CODE), r.get(V.KEY_QUARTER), r.get(V.KEY_ITEM)
        name[c] = r.get(V.KEY_NAME, c)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if c and q:
            byq.setdefault((c, q), {})[it] = (_num(r.get(V.KEY_VALUE)),
                                              _num(r.get(V.KEY_VALUE_POST)))
    return byq, name


def dsqrt(vals, mat):
    return V._diversified_sqrt(np.array(vals, dtype=float), mat)


def main():
    recs = load_master()
    byq, name = build(recs)
    for key in TARGETS:
        m = byq.get(key)
        print("=" * 96)
        print(f"{key[0]} {name.get(key[0])} {key[1]}   items in bucket = {len(m or {})}")
        if not m:
            print("  (no bucket)")
            continue
        for it in sorted(m):
            pre, post = m[it]
            print(f"  item{it:>3}  전={pre!s:>16}  후={post!s:>16}"
                  + ("   [후=전]" if pre is not None and post is not None
                     and abs(pre - post) < 1e-9 else ""))
        # axis recomputation
        print("  --- axis recomputation (both columns) ---")
        for label, idx in (("전", 0), ("후", 1)):
            for parent, (subs, mat, add_item, tol_kind) in sorted(V._TRANS_PARENT_SUBS.items()):
                p = m.get(parent, (None, None))[idx]
                sv = [m.get(i, (None, None))[idx] for i in subs]
                add = m.get(add_item, (None, None))[idx] if add_item else 0.0
                if p is None or any(v is None for v in sv) or add is None:
                    miss = [i for i in subs if m.get(i, (None, None))[idx] is None]
                    print(f"    [{label}] axis item{parent}: SKIP "
                          f"(parent={p} missing_subs={miss} add={add})")
                    continue
                exp = dsqrt(sv, mat) + add
                tol = V._eff_tol(key[0]) if tol_kind == "flat" else max(V._eff_tol(key[0]),
                                                                       0.05 * abs(exp))
                st = "FAIL" if abs(p - exp) > tol else "ok"
                print(f"    [{label}] axis item{parent}: parent={p:.4f} expected={exp:.4f} "
                      f"diff={p - exp:+.4f} tol={tol:.4f}  {st}")
        # diversification sanity
        for label, idx in (("전", 0), ("후", 1)):
            v16 = m.get(16, (None, None))[idx]
            i15 = m.get(15, (None, None))[idx]
            subs = [m.get(i, (None, None))[idx] for i in (17, 18, 19, 20, 21)]
            der = (sum(subs) - i15) if (i15 is not None and all(s is not None for s in subs)) else None
            print(f"    [{label}] div: item16={v16} derived(sum17-21 - item15)="
                  f"{None if der is None else round(der, 4)}")
        # parent-child after census
        for p, kids in sorted(V._PARENT_CHILD_AFTER.items()):
            post_p = m.get(p, (None, None))[1]
            expected = [k for k in kids
                        if (m.get(k, (None, None))[0] is not None
                            and abs(m.get(k, (None, None))[0]) >= V._CHILD_MATERIAL_FLOOR)]
            missing = [k for k in expected if m.get(k, (None, None))[1] is None]
            print(f"    census-after parent{p}: post={post_p} expected_children={expected} "
                  f"missing={missing}")
    print("=" * 96)
    print("_TRANS_PARENT_SUBS =", {k: (v[0], v[3]) for k, v in V._TRANS_PARENT_SUBS.items()})
    print("_CHILD_MATERIAL_FLOOR =", V._CHILD_MATERIAL_FLOOR)
    print("_POST_PARENT_CORE =", V._POST_PARENT_CORE, " _POST_CAPITAL_CORE =", V._POST_CAPITAL_CORE)


if __name__ == "__main__":
    main()
