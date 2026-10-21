"""Read-only, independent of the apply script: JSON-level diff of the files changed by the 2023.3Q single-quarter blanking, working tree vs git HEAD."""
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
say(f"  changed cells: {len(changed)}; companies {sorted({k[0] for k in changed})}; quarters {sorted({k[2] for k in changed})}; fields {sorted({f for v in changed.values() for f in v})}")
say(f"  new 값_당분기 values of the changed cells: {sorted({repr(kb[k].get('값_당분기')) for k in changed})}; cumulative 값 changed: {sum(1 for k in changed if ka[k]['값'] != kb[k]['값'])}")
say("  blanked items (KR0073 2023.3Q): " + str(sorted(k[1] for k in changed)))
for k in sorted(changed, key=lambda x: x[1]):
    say(f"    item {k[1]:>2} {ka[k]['항목명'][:16]:16s} 값 {kb[k]['값']:>16,.2f} | 값_당분기 {ka[k]['값_당분기']!s:>18} -> {kb[k]['값_당분기']}")
keep = [(k[1], ka[k]["값_당분기"]) for k in ka if k[0] == "KR0073" and k[2] == "2023.3Q" and k not in changed]
say(f"  KR0073 2023.3Q cells NOT changed (kept): {keep}")
other_q = {k for k in ka if k[0] == "KR0073" and k[2] in ("2023.2Q", "2023.4Q", "2024.3Q")}
say(f"  KR0073 2023.2Q / 2023.4Q / 2024.3Q cells changed: {len([k for k in other_q if k in changed])} of {len(other_q)}")

ga, gb = head("data/_gold/user_pl_cells.json"), cur("data/_gold/user_pl_cells.json")
say(f"user_pl_cells.json: `set` identical: {ga['set'] == gb['set']} ({len(ga['set'])} entries); top-level keys HEAD {list(ga)} -> now {list(gb)}")
say(f"  `_doc` changed: {ga.get('_doc') != gb.get('_doc')}; null_dangi cells: {len(gb['null_dangi']['cells'])} -> {sorted(set((c[0], c[1]) for c in gb['null_dangi']['cells']))}")
(HERE / "diff_vs_head_seam.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
