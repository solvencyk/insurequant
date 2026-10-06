"""READ-ONLY simulation of a candidate gate rule, run over EVERY bucket before any edit.

Candidate: `2_tier1_bridge_post` promoted from YELLOW to RED using a **delta-of-residual**
test instead of a raw equality test:

    resid(col) = item4(col) - item12(col) - item13(col) - item2(col)
    fire  <=>  both columns computable  AND  |resid_post - resid_pre| > tol

Rationale: a raw `resid_post == 0` test would red-out every issuer whose 적용전 bridge
already carries a documented residual (the gate already exempts 19 such buckets).
The delta form asks only "did the 적용후 column move together with the tier split",
which is exactly the mirror defect, and is blind to a constant issuer offset.

Also simulates the naive variant so both directions (closes / breaks) are counted.

Writes data/_derived/_probe_20260919_bridge_delta_sim.json
No mutation. No build. No network.
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "data" / "_derived" / "_probe_20260919_bridge_delta_sim.json"
AUDIT = ROOT / "data" / "_derived" / "_probe_20260919_mirror_audit_v4.json"

K_CODE, K_NAME, K_ITEM, K_Q, K_V, K_VA = (
    "원보험사코드", "원수사명", "항목번호", "공시분기", "값", "값_적용후")
TOL = 2.0


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
    data = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    midx = {}
    for r in data:
        midx.setdefault((r.get(K_CODE), r.get(K_Q)), {})[r.get(K_ITEM)] = r

    audit = {(r["code"], r["q"]): r
             for r in json.loads(AUDIT.read_text(encoding="utf-8"))["rows"]}

    rows = []
    for (code, q), items in sorted(midx.items()):
        def g(n, col):
            r0 = items.get(n)
            if not r0:
                return None
            return num(r0.get(K_V if col == 0 else K_VA))
        name = next((r0.get(K_NAME) for r0 in items.values() if r0.get(K_NAME)), code)
        rec = {"code": code, "name": name, "q": q}
        for col, tag in ((0, "pre"), (1, "post")):
            i4, i12, i13, i2 = g(4, col), g(12, col), g(13, col), g(2, col)
            rec[f"resid_{tag}"] = (None if None in (i4, i12, i13, i2)
                                   else round(i4 - i12 - i13 - i2, 4))
            rec[f"inputs_{tag}"] = [i4, i12, i13, i2]
        rp, rq = rec["resid_pre"], rec["resid_post"]
        if rp is None or rq is None:
            rec["sim_delta"] = "SKIP_INPUT_MISSING"
        else:
            rec["delta"] = round(rq - rp, 4)
            rec["sim_delta"] = "FIRE" if abs(rq - rp) > TOL else "PASS"
        rec["sim_naive"] = ("SKIP_INPUT_MISSING" if rq is None
                            else ("FIRE" if abs(rq) > TOL else "PASS"))
        a = audit.get((code, q))
        rec["audit_verdict"] = a["verdict"] if a else "NO_MIRROR_CELLS"
        rec["audit_delta"] = a.get("tier_delta") if a else None
        rows.append(rec)

    cd = Counter(r["sim_delta"] for r in rows)
    cn = Counter(r["sim_naive"] for r in rows)
    fire_delta = [r for r in rows if r["sim_delta"] == "FIRE"]
    # cross-tab against the raw-anchored audit verdict
    xtab = Counter((r["audit_verdict"], r["sim_delta"]) for r in rows)
    # of the 60 CONTAMINATED buckets, how many does the candidate catch?
    cont = [r for r in rows if r["audit_verdict"] == "CONTAMINATED"]
    caught = [r for r in cont if r["sim_delta"] == "FIRE"]
    missed = [r for r in cont if r["sim_delta"] != "FIRE"]
    benign = [r for r in rows if r["audit_verdict"].startswith("BENIGN")]
    false_fire = [r for r in benign if r["sim_delta"] == "FIRE"]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "buckets": len(rows),
        "sim_delta_counts": dict(cd),
        "sim_naive_counts": dict(cn),
        "xtab_audit_x_simdelta": {f"{k[0]}|{k[1]}": v for k, v in sorted(xtab.items())},
        "contaminated_total": len(cont),
        "contaminated_caught": len(caught),
        "contaminated_missed": [
            {"code": r["code"], "q": r["q"], "resid_pre": r["resid_pre"],
             "resid_post": r["resid_post"], "audit_delta": r["audit_delta"]}
            for r in missed],
        "benign_false_fire": [
            {"code": r["code"], "name": r["name"], "q": r["q"],
             "resid_pre": r["resid_pre"], "resid_post": r["resid_post"],
             "delta": r.get("delta")} for r in false_fire],
        "fire_rows": fire_delta,
        "rows": rows,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("buckets:", len(rows))
    print("candidate (delta-of-residual):", dict(cd))
    print("naive (resid_post==0):        ", dict(cn))
    print(f"contaminated caught {len(caught)}/{len(cont)}  missed {len(missed)}")
    print(f"benign buckets that would fire (false positives): {len(false_fire)}")
    for r in false_fire:
        print("   FP:", r["code"], r["name"], r["q"], r["resid_pre"], r["resid_post"])
    for r in missed:
        print("   MISS:", r["code"], r["q"], r["resid_pre"], r["resid_post"], r["audit_delta"])
    print("wrote", OUT)


if __name__ == "__main__":
    main()
