"""Read-only: KR0073 PL 값 / 값_당분기 before (3e53aef8~1), after (3e53aef8) and now (HEAD + working tree) for 2023.3Q / 2023.4Q / 2024.3Q (+ 2023.2Q / 2024.2Q for context).

Classifies every 2023.3Q cell: BLANK_BEFORE_FILLED_AFTER (the set to blank), NONNULL_BEFORE_CHANGED, NONNULL_BEFORE_SAME, STILL_BLANK, and writes seam_cells.txt / seam_cells.json.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
CODE = "KR0073"


def git_json(rev, rel):
    p = subprocess.run(["git", "-C", str(ROOT), "show", f"{rev}:{rel}"], capture_output=True)
    if p.returncode != 0:
        raise SystemExit(f"git show {rev}:{rel} failed: {p.stderr.decode('utf-8', 'replace')[:200]}")
    return json.loads(p.stdout.decode("utf-8"))


def kr(rows):
    out = {}
    for r in rows:
        if r["원보험사코드"] == CODE:
            out[(r["공시분기"], r["항목번호"])] = r
    return out


before = kr(git_json("3e53aef8~1", "PL_breakdown.json"))
after = kr(git_json("3e53aef8", "PL_breakdown.json"))
head = kr(git_json("HEAD", "PL_breakdown.json"))
now = kr(json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8")))
print("HEAD == 3e53aef8 for KR0073 PL (값, 값_당분기):", all((head[k].get("값"), head[k].get("값_당분기")) == (after[k].get("값"), after[k].get("값_당분기")) for k in after))
print("working tree == HEAD for KR0073 PL (값, 값_당분기):", all((now[k].get("값"), now[k].get("값_당분기")) == (head[k].get("값"), head[k].get("값_당분기")) for k in head))
names = {k[1]: v["항목명"] for k, v in after.items()}
f = lambda v: "None" if v is None else f"{v:,.2f}"
lines = []
res = {}
for q in ("2023.2Q", "2023.3Q", "2023.4Q", "2024.2Q", "2024.3Q"):
    lines.append(f"=== {q}   (값 before -> after | 값_당분기 before -> after)")
    for i in range(1, 33):
        b, a = before.get((q, i)), after.get((q, i))
        bv, av = b.get("값"), a.get("값")
        bd, ad = b.get("값_당분기"), a.get("값_당분기")
        if q == "2023.3Q":
            if bd is None and ad is not None:
                cls = "BLANK_BEFORE_FILLED_AFTER"
            elif bd is not None and ad is not None and abs(bd - ad) > 5e-4:
                cls = "NONNULL_BEFORE_CHANGED"
            elif bd is not None and ad is not None:
                cls = "NONNULL_BEFORE_SAME"
            elif bd is not None and ad is None:
                cls = "NONNULL_BEFORE_NOW_NULL"
            else:
                cls = "STILL_BLANK"
            res.setdefault(cls, []).append(i)
        else:
            cls = ""
            if bd is None and ad is not None:
                cls = "blank->filled"
            elif bd is not None and ad is not None and abs(bd - ad) > 5e-4:
                cls = "changed"
        lines.append(f"  item{i:2d} {names[i][:14]:14s} 값 {f(bv):>16s} -> {f(av):>16s} | 당분기 {f(bd):>16s} -> {f(ad):>16s}  {cls}")
text = "\n".join(lines)
(HERE / "seam_cells.txt").write_text(text + "\n", encoding="utf-8", newline="\n")
(HERE / "seam_cells.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print(text)
print()
for k, v in res.items():
    print(f"2023.3Q {k}: {len(v)} items {v}")
