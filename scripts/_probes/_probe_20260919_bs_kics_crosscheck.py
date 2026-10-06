"""READ-ONLY feasibility probe (ticket part C): can IFRS17_BS.json (DART lineage) and
kics_disclosure.json (정기경영공시 lineage) check each other?

Enumerates candidate item pairs, converts units (K-ICS 억원 x100 -> 백만원), and measures
the residual distribution per pair over the (company, quarter) intersection. Design input
only — nothing is wired, no master is touched.

Writes data/_derived/_probe_20260919_bs_kics_crosscheck.json
"""
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "data" / "_derived" / "_probe_20260919_bs_kics_crosscheck.json"

K_CODE, K_Q, K_ITEM, K_V, K_VA, K_NAME = (
    "원보험사코드", "공시분기", "항목번호", "값", "값_적용후", "원수사명")

# (pair_id, description, bs_items(list, summed), kics_items(list, summed))
PAIRS = [
    ("P1_이익잉여금", "17BS 31 이익잉여금 ↔ K-ICS 7 이익잉여금", [31], [7]),
    ("P2_기타포괄손익누계액", "17BS 4 ↔ K-ICS 9", [4], [9]),
    ("P3_자본금_보통주", "17BS 30 자본금 ↔ K-ICS 5 보통주", [30], [5]),
    ("P4_자본총계_vs_순자산", "17BS 3 자본총계(K-IFRS) ↔ K-ICS 4 건전성감독기준 순자산", [3], [4]),
    ("P5_자본총계_vs_Σ5_11", "17BS 3 ↔ K-ICS Σ(5..11)", [3], [5, 6, 7, 8, 9, 10, 11]),
    ("P6_해약환급금준비금_vs_조정준비금", "17BS 5 ↔ K-ICS 11 조정준비금", [5], [11]),
    ("P7_법정준비금합_vs_조정준비금", "17BS 5+6+7+8 ↔ K-ICS 11 조정준비금", [5, 6, 7, 8], [11]),
    ("P8_자본금+잉여금+AOCI_vs_순자산", "17BS 30+31+4 ↔ K-ICS 4", [30, 31, 4], [4]),
]
SCALE = 100.0  # K-ICS 억원 -> 백만원


def num(v):
    if v is None:
        return None
    s = str(v).replace(",", "").replace("△", "-").strip()
    if s in ("", "-"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def main():
    bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
    ki = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))

    bidx = defaultdict(dict)
    for r in bs:
        bidx[(r.get(K_CODE), r.get(K_Q))][r.get(K_ITEM)] = num(r.get(K_V))
    kidx = defaultdict(dict)
    names = {}
    for r in ki:
        kidx[(r.get(K_CODE), r.get(K_Q))][r.get(K_ITEM)] = num(r.get(K_V))
        names[r.get(K_CODE)] = r.get(K_NAME)

    bkeys, kkeys = set(bidx), set(kidx)
    inter = sorted(bkeys & kkeys)
    cov = {
        "bs_buckets": len(bkeys), "kics_buckets": len(kkeys),
        "intersection_buckets": len(inter),
        "bs_companies": len({c for c, _ in bkeys}),
        "kics_companies": len({c for c, _ in kkeys}),
        "intersection_companies": len({c for c, _ in inter}),
        "bs_only_quarters": sorted({q for _, q in bkeys} - {q for _, q in kkeys}),
        "kics_only_quarters": sorted({q for _, q in kkeys} - {q for _, q in bkeys}),
    }

    results = {}
    for pid, desc, bitems, kitems in PAIRS:
        rows, skipped = [], Counter()
        for key in inter:
            b, k = bidx[key], kidx[key]
            bv = [b.get(i) for i in bitems]
            kv = [k.get(i) for i in kitems]
            if any(x is None for x in bv):
                skipped["BS_INPUT_MISSING"] += 1
                continue
            if any(x is None for x in kv):
                skipped["KICS_INPUT_MISSING"] += 1
                continue
            bsum = sum(bv)
            ksum = sum(kv) * SCALE
            base = max(abs(bsum), abs(ksum))
            resid = bsum - ksum
            rows.append({"code": key[0], "name": names.get(key[0]), "q": key[1],
                         "bs": round(bsum, 2), "kics_mn": round(ksum, 2),
                         "resid_mn": round(resid, 2),
                         "rel": (None if base == 0 else round(resid / base, 6))})
        rels = [abs(r["rel"]) for r in rows if r["rel"] is not None]
        rels.sort()

        def pct(p):
            if not rels:
                return None
            i = min(len(rels) - 1, int(round(p * (len(rels) - 1))))
            return round(rels[i], 6)
        results[pid] = {
            "desc": desc, "n": len(rows), "skipped": dict(skipped),
            "rel_median": round(statistics.median(rels), 6) if rels else None,
            "rel_p10": pct(0.10), "rel_p25": pct(0.25), "rel_p75": pct(0.75),
            "rel_p90": pct(0.90), "rel_p95": pct(0.95), "rel_max": pct(1.0),
            "share_rel_le_0.001": (round(sum(1 for x in rels if x <= 0.001) / len(rels), 4)
                                   if rels else None),
            "share_rel_le_0.01": (round(sum(1 for x in rels if x <= 0.01) / len(rels), 4)
                                  if rels else None),
            "share_rel_le_0.05": (round(sum(1 for x in rels if x <= 0.05) / len(rels), 4)
                                  if rels else None),
            "worst": sorted(rows, key=lambda r: -abs(r["rel"] or 0))[:8],
            "rows": rows,
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"coverage": cov, "pairs": results},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("coverage:", json.dumps(cov, ensure_ascii=False))
    for pid, r in results.items():
        print(f"{pid:36s} n={r['n']:4d} skip={r['skipped']} med={r['rel_median']} "
              f"p75={r['rel_p75']} p90={r['rel_p90']} max={r['rel_max']} "
              f"<=0.1%={r['share_rel_le_0.001']} <=1%={r['share_rel_le_0.01']} "
              f"<=5%={r['share_rel_le_0.05']}")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
