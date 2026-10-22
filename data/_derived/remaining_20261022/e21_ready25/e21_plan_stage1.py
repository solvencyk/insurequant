# -*- coding: utf-8 -*-
"""e21 plan stage 1: read every READY bucket independently (e21_plan_lib), classify each item against the HEAD master, compare with the measure-phase candidates.
Writes e21_stage1.json (all reads) + e21_stage1_report.txt.  READ-ONLY on every repo file."""
import json
import sys
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_plan_lib as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
SPECS = [
    ("KR0104", "2023.1Q", "life", "prior"), ("KR0104", "2023.2Q", "life", "prior"),
    ("KR0083", "2024.4Q", "life", "prior"),
    ("KR0070", "2024.4Q", "life", "prior"),
    ("KR0079", "2023.4Q", "life", "prior"), ("KR0079", "2024.1Q", "life", "prior"), ("KR0079", "2024.2Q", "life", "prior"), ("KR0079", "2024.3Q", "life", "prior"),
    ("KR0010", "2023.1Q", "kb", "prior"), ("KR0010", "2023.2Q", "kb", "prior"), ("KR0010", "2023.4Q", "kb", "prior"),
    ("KR0010", "2024.1Q", "kb", "prior"), ("KR0010", "2024.2Q", "kb", "prior"), ("KR0010", "2024.3Q", "kb", "prior"),
    ("KR0099", "2024.1Q", "kblife_fix", "cur"),
    ("KR0003", "2023.1Q", "lotte", "prior"), ("KR0003", "2023.2Q", "lotte", "prior"), ("KR0003", "2024.1Q", "lotte", "prior"), ("KR0003", "2024.2Q", "lotte", "prior"), ("KR0003", "2024.3Q", "lotte", "prior"),
    ("KR0001", "2023.1Q", "meritz", "prior"), ("KR0001", "2023.2Q", "meritz", "prior"),
    ("KR0068", "2023.1Q", "life", "prior"), ("KR0068", "2023.2Q", "life", "prior"), ("KR0068", "2023.3Q", "life", "prior"),
]


def classify(old, c):
    new = c["val"]
    if old is None:
        return "fill"
    d = new - old
    units = {p["unit"] for p in c["parts"]} or {"백만원"}
    exact_src = units == {"원"}
    if abs(d) <= 2e-5:
        return "equal"
    band = 2e-5 if exact_src else (1.0 + 0.5 * (max(1, len(c["parts"])) - 1) + 1e-3)
    if abs(d) <= band:
        return "rounding"
    return "changed"


def main():
    plh = P.head_json("PL_breakdown.json")
    master = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in plh}
    cj = json.loads((P.MEAS / "cands_READY_all.json").read_text(encoding="utf-8"))
    cand = {(c["code"], c["q"], c["item"]): c for c in cj["pl_cells"]}
    out, L = [], []
    n_pl = 0
    for code, q, kind, role in SPECS:
        try:
            rb = P.read_bucket(code, q, kind, master, role)
        except Exception as e:  # noqa: BLE001
            L.append(f"== {code} {q} {kind}: READ ERROR {type(e).__name__}: {e}")
            out.append(dict(code=code, quarter=q, error=f"{type(e).__name__}: {e}"))
            continue
        meta, items = rb["meta"], rb["items"]
        cset = {i for (c_, q_, i) in cand if c_ == code and q_ == q}
        L.append(f"== {code} {q} {kind} later {meta['file']} unit {meta['unit']} fmt {meta['fmt']}")
        rows = []
        for i in sorted(items):
            c = items[i]
            assert abs(P.value_of(c) - c["val"]) < 1e-5, (code, q, i, P.value_of(c), c["val"])
            old = master.get((code, i, q))
            cls = classify(old, c)
            cd = cand.get((code, q, i))
            flag = ""
            if cd is not None:
                flag = "CAND_EQ" if abs(cd["new"] - c["val"]) <= 1e-3 else f"CAND_DIFF(cand={cd['new']})"
            elif cls in ("fill", "changed"):
                flag = "NOT_IN_CAND"
            rows.append(dict(item=i, old=old, new=c["val"], cls=cls, cand=None if cd is None else cd["new"], flag=flag))
            if cls in ("fill", "changed", "rounding") or cd is not None:
                L.append(f"   i{i:>2} old={old} new={c['val']} cls={cls} {flag}")
        missing = sorted(cset - set(items))
        if missing:
            L.append(f"   CANDIDATE ITEMS NOT READ BY ME: {missing}")
        out.append(dict(code=code, quarter=q, kind=kind, meta=meta, rows=rows, cset=sorted(cset), missing=missing))
        n_pl += len([r for r in rows if r["cls"] in ("fill", "changed")])
    (P.EV / "e21_stage1_report.txt").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    (P.EV / "e21_stage1.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("\n".join(L[:400]))
    print("cells fill/changed by my read:", n_pl)


if __name__ == "__main__":
    main()
