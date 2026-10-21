"""Read-only, independent of the apply scripts: JSON-level diff vs git HEAD after the printed-3-month step -> diff_vs_head_seam2.txt (and the per-item set/null table for the report)."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
out = []


def say(s=""):
    print(s)
    out.append(s)


def head(rel):
    p = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{rel}"], capture_output=True)
    if p.returncode != 0:
        raise SystemExit(f"git show failed for {rel}")
    return json.loads(p.stdout.decode("utf-8"))


cur = lambda rel: json.loads((ROOT / rel).read_text(encoding="utf-8"))
key = lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"])
a, b = head("PL_breakdown.json"), cur("PL_breakdown.json")
ka, kb = {key(r): r for r in a}, {key(r): r for r in b}
say(f"PL_breakdown.json: rows HEAD {len(a)} / now {len(b)}; only-in-HEAD {len(set(ka) - set(kb))}; only-now {len(set(kb) - set(ka))}; order same: {[key(r) for r in a] == [key(r) for r in b]}")
changed = {k: sorted(f for f in set(ka[k]) | set(kb[k]) if ka[k].get(f) != kb[k].get(f)) for k in ka if ka[k] != kb[k]}
say(f"  changed cells vs HEAD: {len(changed)}; companies {sorted({k[0] for k in changed})}; quarters {sorted({k[2] for k in changed})}; fields {sorted({f for v in changed.values() for f in v})}; cumulative 값 changed: {sum(1 for k in changed if ka[k]['값'] != kb[k]['값'])}")
say("  KR0073 2023.2Q / 2023.4Q / 2024.3Q cells changed: " + str(len([k for k in changed if k[0] == "KR0073" and k[2] in ("2023.2Q", "2023.4Q", "2024.3Q")])))
plan = json.loads((HERE / "seam_3m_plan.json").read_text(encoding="utf-8"))
setv = {c[2]: c[3] for c in plan["set"]}
nullv = {c[2] for c in plan["null"]}
say("")
say("KR0073 2023.3Q 값_당분기 per item (백만원): decision | HEAD (3e53aef8 derived) | now | changed vs HEAD")
for i in range(1, 33):
    k = ("KR0073", i, "2023.3Q")
    h, n = ka[k].get("값_당분기"), kb[k].get("값_당분기")
    dec = "SET" if i in setv else ("NULL" if i in nullv else "KEEP")
    ch = "CHANGED" if k in changed else "same"
    f = lambda v: "None" if v is None else f"{v:,.4f}"
    say(f"  item {i:>2d} {ka[k]['항목명'][:14]:14s} {dec:4s} | HEAD {f(h):>18s} | now {f(n):>18s} | {ch}")
ga, gb = head("data/_gold/user_pl_cells.json"), cur("data/_gold/user_pl_cells.json")
say("")
say(f"user_pl_cells.json: `set` identical to HEAD: {ga['set'] == gb['set']} ({len(ga['set'])} entries); top-level keys HEAD {list(ga)} -> now {list(gb)}")
say(f"  null_dangi cells: {gb['null_dangi']['cells']}; set_dangi cells: {len(gb['set_dangi']['cells'])} (items {[c[2] for c in gb['set_dangi']['cells']]})")
(HERE / "diff_vs_head_seam2.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
