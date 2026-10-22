# -*- coding: utf-8 -*-
"""e21 seam exploration (READ-ONLY): for every single quarter (값_당분기) whose derivation changes when the stage-1 cells are adopted, compare the derived value with the 3-month column printed in the
later filing of that quarter (Tier-1 items 1, 16..32).  Prints mismatches; Q4 cells (no printed 3-month column) are listed separately."""
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_plan_lib as P  # noqa: E402
import e21_read as R  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
TIER1 = [1, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]


def main():
    plh = P.head_json("PL_breakdown.json")
    master = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in plh}
    masterd = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r.get("값_당분기") for r in plh}
    s1 = json.loads((P.EV / "e21_stage1.json").read_text(encoding="utf-8"))
    adopted = {}
    for b in s1:
        if "error" in b:
            continue
        for r in b["rows"]:
            if r["cls"] in ("fill", "changed") and r["item"] in TIER1 and not (r["item"] == 29 and r["old"] is None):
                adopted[(b["code"], r["item"], b["quarter"])] = r["new"]
    by_code = {}
    for (c, i, q), v in adopted.items():
        by_code.setdefault(c, []).append((i, q))
    stmts = {}

    def stmt(c, fy):
        if (c, fy) not in stmts:
            stmts[(c, fy)] = R.Stmt(c, fy)
        return stmts[(c, fy)]

    def cum(c, i, q):
        return adopted.get((c, i, q), master.get((c, i, q)))

    def prevq(q):
        return None if q[5] == "1" else f"{q[:4]}.{int(q[5]) - 1}Q"

    L = []
    for c, lst in sorted(by_code.items()):
        touched = set()
        for (i, q) in lst:
            touched.add((i, q))
            n = int(q[5])
            if n < 4:
                touched.add((i, f"{q[:4]}.{n + 1}Q"))
        for (i, qq) in sorted(touched, key=lambda x: (x[1], x[0])):
            n = int(qq[5])
            pq = prevq(qq)
            cur = cum(c, i, qq)
            prev = cum(c, i, pq) if pq else None
            if n == 1:
                continue
            D = None if (cur is None or prev is None) else cur - prev
            live = masterd.get((c, i, qq))
            if n == 4:
                L.append(f"Q4 {c} {qq} i{i}: cum_after={cur} prev_cum={prev} D={D} live_dangi={live} adopted_cur={(c, i, qq) in adopted} adopted_prev={(c, i, pq) in adopted}")
                continue
            fy = P.later_fy(qq)
            try:
                st = stmt(c, fy)
                v3 = R.read_vector(st, "prior", "3m")
                p3 = v3[i]["val"]
                unit = st.unit
            except Exception as e:  # noqa: BLE001
                L.append(f"?? {c} {qq} i{i}: 3m read error {type(e).__name__}: {str(e)[:80]}")
                continue
            tol = 3 * (2e-5 if unit == "원" else 1.0)
            flag = "" if D is None else ("OK" if abs(D - p3) <= tol else "SEAM")
            L.append(f"{flag or 'D=None'} {c} {qq} i{i}: D={D} printed3m={round(p3, 6)} diff={None if D is None else round(D - p3, 6)} live_dangi={live} adopted_cur={(c, i, qq) in adopted} adopted_prev={(c, i, pq) in adopted}")
    out = "\n".join(L)
    (P.EV / "e21_seam_explore.txt").write_text(out + "\n", encoding="utf-8", newline="\n")
    print(out[:60000])


if __name__ == "__main__":
    main()
