"""cand_selftest: fidelity of cand.vector(which='same') against the live master for life buckets (t2 = master note items).
A bucket passes when every item 1..32 equals the master (or the master cell is an owner gold cell)."""
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import cand as K  # noqa: E402
import mlib as M  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
tests = [("KR0099", q) for q in ("2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q")] + \
        [("KR0079", q) for q in ("2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q")] + \
        [("KR0070", q) for q in ("2023.3Q", "2023.4Q", "2024.4Q")] + [("KR0072", "2023.3Q"), ("KR0083", "2024.4Q"), ("KR0083", "2024.3Q")]
gold = M.jload(M.SNAP / "user_pl_cells.json")
gset = {(c["원보험사코드"], c["공시분기"], c["항목번호"]) for c in gold["set"]}
for code, q in tests:
    v, t1 = K.vector(code, q, "same")
    if v is None:
        print(code, q, "no FS-API same")
        continue
    d = K.diff_vs_master(code, q, v)
    non_gold = [x for x in d if (code, q, x[0]) not in gset]
    print(code, q, "items differing vs master:", len(d), " non-gold:", [(i, o, round(n, 3) if n is not None else None) for i, o, n in non_gold][:8])
