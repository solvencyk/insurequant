"""READ-ONLY: is the P1/P2 (이익잉여금 · AOCI) residual bimodality explained by
별도/연결 basis, 특별계정, or something else? Split by company and by whether the
K-ICS filing carries 비지배지분(item10) != 0 (a connected-basis marker).
"""
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "data" / "_derived" / "_probe_20260919_bs_kics_crosscheck.json"
OUT = ROOT / "data" / "_derived" / "_probe_20260919_bs_kics_split.json"
K_CODE, K_Q, K_ITEM, K_V = ("원보험사코드", "공시분기", "항목번호", "값")


def num(v):
    if v is None:
        return None
    s = str(v).replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def main():
    d = json.loads(SRC.read_text(encoding="utf-8"))
    ki = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    nci = defaultdict(lambda: None)
    for r in ki:
        if r.get(K_ITEM) == 10:
            nci[(r.get(K_CODE), r.get(K_Q))] = num(r.get(K_V))

    out = {}
    for pid in ("P1_이익잉여금", "P2_기타포괄손익누계액"):
        rows = d["pairs"][pid]["rows"]
        percomp = defaultdict(list)
        for r in rows:
            if r["rel"] is None:
                continue
            percomp[(r["code"], r["name"])].append(abs(r["rel"]))
        comp = []
        for (c, n), vals in sorted(percomp.items()):
            comp.append({"code": c, "name": n, "n": len(vals),
                         "median_rel": round(statistics.median(vals), 5),
                         "max_rel": round(max(vals), 5),
                         "share_le_0.001": round(sum(1 for v in vals if v <= 0.001) / len(vals), 3)})
        # NCI split
        grp = {"nci_zero_or_none": [], "nci_nonzero": []}
        for r in rows:
            if r["rel"] is None:
                continue
            v = nci.get((r["code"], r["q"]))
            key = "nci_nonzero" if (v is not None and abs(v) > 0) else "nci_zero_or_none"
            grp[key].append(abs(r["rel"]))
        out[pid] = {
            "per_company": sorted(comp, key=lambda x: -x["median_rel"]),
            "nci_split": {k: {"n": len(v),
                              "median": round(statistics.median(v), 5) if v else None,
                              "share_le_0.001": (round(sum(1 for x in v if x <= 0.001) / len(v), 3)
                                                 if v else None)}
                          for k, v in grp.items()},
        }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for pid, r in out.items():
        print("=" * 80)
        print(pid, "NCI split:", json.dumps(r["nci_split"], ensure_ascii=False))
        print("  companies sorted by median |rel| (worst first):")
        for c in r["per_company"]:
            print(f"    {c['code']} {c['name']:22s} n={c['n']:3d} med={c['median_rel']:<10} "
                  f"max={c['max_rel']:<10} share<=0.1%={c['share_le_0.001']}")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
