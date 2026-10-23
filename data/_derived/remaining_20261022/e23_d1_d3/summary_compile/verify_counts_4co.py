# -*- coding: utf-8 -*-
"""Read-only recount of the FOUR-company tree (KDB KR0072 held at HEAD) against git HEAD.

Supersedes verify_counts.py (that one counted the five-company state with KDB loaded).
Writes only verify_counts_4co.txt next to this file. Run: python verify_counts_4co.py < /dev/null
Checks:
  A  the live tree is the one validation measured (sha256 of masters, gold, provenance)
  B  master cell diff vs HEAD per company (PL, CSM): values, single-quarter values, other fields, rows
  C  gold overlay diff vs HEAD (entries added / replaced / removed, pins, ledger, GOLD_OVERLAY_CENSUS)
  D  provenance diff vs HEAD (KR0072 blocks identical; merge-note keys added)
  E  numbers quoted by the open items (롯데 CSM 4Q single-quarter residual, KB라이프 4Q single quarter,
     현대해상 CSM boundary seam and LOB leg bridge, ABL 2023.1Q item 5)
"""
import hashlib
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
E = ROOT / "data/_derived/remaining_20261022/e23_d1_d3"
OUT = E / "summary_compile/verify_counts_4co.txt"
FOUR = ["KR0099", "KR0003", "KR0070", "KR0009"]
HELD = "KR0072"
NAME = {"KR0099": "KB라이프", "KR0003": "롯데손보", "KR0070": "ABL생명", "KR0009": "현대해상", "KR0072": "KDB생명(보류)"}

lines = []


def P(*a):
    s = " ".join(str(x) for x in a)
    lines.append(s)
    print(s)


def head_json(rel):
    out = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{rel}"], capture_output=True, check=True,
                         stdin=subprocess.DEVNULL).stdout
    return json.loads(out.decode("utf-8"))


def live_json(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def K(r):
    return (r["원보험사코드"], r["항목번호"], r["공시분기"])


def SK(k):
    # gold files may carry item numbers as int or str: sort on text only
    return tuple(str(x) for x in k)


# ------------------------------------------------------------------ A
P("=== A. live tree vs the tree validation measured last (sha256)")
for line in (E / "gate_four_final/tests/sha_after.txt").read_text(encoding="utf-8").splitlines():
    m = re.match(r"^([0-9a-f]{64}) \*(.+)$", line.strip())
    if not m:
        continue
    want, rel = m.group(1), m.group(2)
    got = sha(ROOT / rel)
    P(f"   {'SAME' if got == want else 'DIFF'}  {rel}")
P("   -- files restored by the KDB hold (kdb_restore/k04_sha_after_restore.txt, working-tree column at 22:20)")
for line in (E / "kdb_restore/k04_sha_after_restore.txt").read_text(encoding="utf-8").splitlines():
    parts = line.split()
    if len(parts) < 3 or parts[0] == "file" or not re.fullmatch(r"[0-9a-f]{64}", parts[1]):
        continue
    rel, want = parts[0], parts[1]
    p = ROOT / rel
    if not p.exists():
        P(f"   MISSING {rel}")
        continue
    note = ""
    if rel.startswith(("tests/test_rule", "scripts/validate_master")):
        note = "  (validation edited this file later, item 23 revert: a difference is expected)"
    P(f"   {'SAME' if sha(p) == want else 'DIFF'}  {rel}{note}")

# ------------------------------------------------------------------ B
P("")
P("=== B. master cells vs git HEAD")
masters = {}
for rel in ("PL_breakdown.json", "CSM_waterfall.json"):
    h, l = head_json(rel), live_json(rel)
    hi = {K(r): r for r in h}
    li = {K(r): r for r in l}
    P(f"-- {rel}: rows head {len(h)} live {len(l)} | dup keys head {len(h) - len(hi)} live {len(l) - len(li)} "
      f"| rows added {len(set(li) - set(hi))} removed {len(set(hi) - set(li))}")
    val, dan, other = Counter(), Counter(), Counter()
    per_q = defaultdict(Counter)
    for k, r in li.items():
        o = hi.get(k)
        if o is None:
            continue
        for f in set(r) | set(o):
            if r.get(f) == o.get(f):
                continue
            if f == "값":
                val[k[0]] += 1
                per_q[k[0]][k[2]] += 1
            elif f == "값_당분기":
                dan[k[0]] += 1
            else:
                other[(k[0], f)] += 1
    for c in FOUR + [HELD]:
        P(f"   {c} {NAME[c]:<8} 값 {val[c]:>3} | 값_당분기 {dan[c]:>3} | by quarter {dict(sorted(per_q[c].items()))}")
    outside = sorted({c for c in set(val) | set(dan)} - set(FOUR))
    P(f"   total 값 {sum(val.values())} | total 값_당분기 {sum(dan.values())} | companies outside the four: {outside or 'none'}"
      f" | other fields changed: {dict(other) or 'none'}")
    masters[rel] = (hi, li)

# ------------------------------------------------------------------ C
P("")
P("=== C. gold overlay vs git HEAD")


def gold_diff(label, rel):
    h, l = head_json(rel), live_json(rel)
    he = {K(e): e for e in h["set"]}
    le = {K(e): e for e in l["set"]}
    P(f"-- {label} set: head {len(h['set'])} (unique {len(he)}) live {len(l['set'])} (unique {len(le)})")
    added = defaultdict(int)
    for k in le:
        if k not in he:
            added[k[0]] += 1
    removed = [k for k in he if k not in le]
    replaced = [k for k in he if k in le and he[k].get("값") != le[k].get("값")]
    meta = [k for k in he if k in le and he[k].get("값") == le[k].get("값") and he[k] != le[k]]
    P(f"   added by company {dict(sorted(added.items()))} (total {sum(added.values())})")
    P(f"   removed {len(removed)} | value replaced {len(replaced)} | note/why-only changed {len(meta)}")
    for k in sorted(removed, key=SK):
        P(f"     REMOVED  {k[0]} {k[2]} item {k[1]}: head 값 {he[k].get('값')}  (live value flows from the builder)")
    for k in sorted(replaced, key=SK):
        P(f"     REPLACED {k[0]} {k[2]} item {k[1]}: head 값 {he[k].get('값')} -> live 값 {le[k].get('값')}")
    for k in sorted(meta, key=SK):
        P(f"     META     {k[0]} {k[2]} item {k[1]}: value unchanged {le[k].get('값')}, text changed")
    P(f"   {HELD} entries: head {sum(1 for k in he if k[0] == HELD)} live {sum(1 for k in le if k[0] == HELD)} "
      f"identical={[he[k] for k in sorted(he, key=SK) if k[0] == HELD] == [le[k] for k in sorted(le, key=SK) if k[0] == HELD]}")
    return h, l


gpl_h, gpl_l = gold_diff("PL gold", "data/_gold/user_pl_cells.json")
gcsm_h, gcsm_l = gold_diff("CSM gold", "data/_gold/user_csm_cells.json")
P(f"   CSM gold doc keys added vs head: {sorted(set(gcsm_l) - set(gcsm_h))} | removed: {sorted(set(gcsm_h) - set(gcsm_l))}")
P(f"   CSM gold exclude_companies unchanged: {gcsm_h['exclude_companies'] == gcsm_l['exclude_companies']}")

for pin in ("null_dangi", "set_dangi"):
    hc = [tuple(c[:3]) for c in gpl_h[pin]["cells"]]
    lc = [tuple(c[:3]) for c in gpl_l[pin]["cells"]]
    ca, cb = Counter(c[0] for c in hc), Counter(c[0] for c in lc)
    P(f"-- PL {pin}: head {len(hc)} live {len(lc)} | added {len(set(lc) - set(hc))} removed {len(set(hc) - set(lc))} | "
      f"by company added {dict(sorted(Counter(c[0] for c in set(lc) - set(hc)).items()))} | {HELD} head {ca[HELD]} live {cb[HELD]}")
    if pin == "set_dangi":
        hv = {tuple(c[:3]): c[3] for c in gpl_h[pin]["cells"]}
        lv = {tuple(c[:3]): c[3] for c in gpl_l[pin]["cells"]}
        P(f"   set_dangi values changed on common cells: {sum(1 for k in hv if k in lv and hv[k] != lv[k])}")

led_h, led_l = head_json("data/_gold/gold_overlay_ledger.json"), live_json("data/_gold/gold_overlay_ledger.json")
P(f"-- ledger entries: head {len(led_h['entries'])} live {len(led_l['entries'])} | identical={led_h['entries'] == led_l['entries']}"
  f" | {HELD} lines head {sum(1 for k in led_h['entries'] if HELD in k)} live {sum(1 for k in led_l['entries'] if HELD in k)}")

test_text = (ROOT / "tests/test_rule_coverage_manifest.py").read_text(encoding="utf-8")
m = re.search(r"^GOLD_OVERLAY_CENSUS = (\{.*\})$", test_text, re.M)
P(f"-- tests/test_rule_coverage_manifest.py: GOLD_OVERLAY_CENSUS = {m.group(1) if m else 'NOT FOUND'} | live gold set sizes: "
  f"CSM {len(gcsm_l['set'])} PL {len(gpl_l['set'])} | head sizes CSM {len(gcsm_h['set'])} PL {len(gpl_h['set'])}")

# ------------------------------------------------------------------ D
P("")
P("=== D. provenance vs git HEAD")
for rel in ("PL_breakdown_provenance.json", "CSM_waterfall_provenance.json"):
    h, l = head_json(rel), live_json(rel)

    def blocks(d):
        out = {}
        for c in d["cells"]:
            code = c.get("company_code") or c.get("원보험사코드")
            out[(code, c.get("quarter") or c.get("공시분기"), c.get("item_block") or c.get("항목번호"))] = c
        return out

    hb, lb = blocks(h), blocks(l)
    changed = Counter(k[0] for k in set(hb) | set(lb) if hb.get(k) != lb.get(k))
    notes_new = sorted(k for k in l if k.startswith("merge_note") and k not in h)
    P(f"-- {rel}: cells head {len(h['cells'])} live {len(l['cells'])} | blocks changed by company {dict(sorted(changed.items()))}"
      f" | {HELD} blocks changed: {changed.get(HELD, 0)}")
    P(f"   merge_note keys added: {notes_new}")

# ------------------------------------------------------------------ E
P("")
P("=== E. numbers quoted by the open items (live masters, 억원 for CSM, 백만원 for PL)")
pl_h, pl_l = masters["PL_breakdown.json"]
csm_h, csm_l = masters["CSM_waterfall.json"]


def v(d, c, it, q, f="값"):
    r = d.get((c, it, q))
    return None if r is None else r.get(f)


def resid(d, c, q, f):
    xs = [v(d, c, i, q, f) for i in (1, 2, 3, 4, 5, 6)]
    if None in xs:
        return None, xs
    return round(sum(xs[:5]) - xs[5], 2), xs


P("-- 롯데손보 KR0003 CSM roll-forward residual (1+2+3+4+5-6)")
for q in ("2023.3Q", "2023.4Q"):
    for f in ("값", "값_당분기"):
        r, xs = resid(csm_l, "KR0003", q, f)
        P(f"   {q} {f}: items1-6 {xs} residual {r}")
P(f"   head 2023.4Q 값_당분기 residual: {resid(csm_h, 'KR0003', '2023.4Q', '값_당분기')[0]}")
P("-- KB라이프 KR0099 2023.4Q PL single quarter (head -> live, 백만원); 2023.4Q cumulative unchanged")
for it in (1, 17, 19, 20, 22, 23, 24, 25, 27, 31):
    P(f"   item {it:>2}: cum head {v(pl_h, 'KR0099', it, '2023.4Q')} live {v(pl_l, 'KR0099', it, '2023.4Q')} | "
      f"single head {v(pl_h, 'KR0099', it, '2023.4Q', '값_당분기')} live {v(pl_l, 'KR0099', it, '2023.4Q', '값_당분기')}")
P(f"   KB라이프 PL cells with 4Q single changed: "
  f"{sum(1 for k in pl_l if k[0] == 'KR0099' and k[2] == '2023.4Q' and pl_h[k].get('값_당분기') != pl_l[k].get('값_당분기'))}"
  f" | CSM 4Q single changed: "
  f"{sum(1 for k in csm_l if k[0] == 'KR0099' and k[2] == '2023.4Q' and csm_h[k].get('값_당분기') != csm_l[k].get('값_당분기'))}")
P("-- 현대해상 KR0009 CSM FY boundary")
P(f"   2023.4Q 기말 {v(csm_l, 'KR0009', 6, '2023.4Q')} | 2024.1Q 기초 {v(csm_l, 'KR0009', 1, '2024.1Q')} | "
  f"FY2024 기초 1Q..4Q {[v(csm_l, 'KR0009', 1, q) for q in ('2024.1Q', '2024.2Q', '2024.3Q', '2024.4Q')]}")
P("-- 현대해상 KR0009 2023.4Q LOB leg bridge (백만원)")
i1 = v(pl_l, "KR0009", 1, "2023.4Q")
legs = [v(pl_l, "KR0009", i, "2023.4Q") for i in (2, 13, 14)]
P(f"   item 1 {i1} | legs 2/13/14 {legs} | sum {None if None in legs else round(sum(legs), 3)} | "
  f"residual {None if None in legs or i1 is None else round(i1 - sum(legs), 3)}")
p3 = [v(pl_l, "KR0009", i, "2023.4Q") for i in (3, 4, 5, 6, 7)]
P(f"   item 3 {p3[0]} | 4,5,6,7 {p3[1:]} | 3-(4+5+6+7) = {None if None in p3 else round(p3[0] - sum(p3[1:]), 3)}")
P("-- ABL KR0070 wrong-leg and old-vintage cells (백만원)")
P(f"   item 5: 2023.1Q 값 {v(pl_l, 'KR0070', 5, '2023.1Q')} | 2023.2Q 값 {v(pl_l, 'KR0070', 5, '2023.2Q')} 단일 {v(pl_l, 'KR0070', 5, '2023.2Q', '값_당분기')}")
P(f"   item 9: 2023.3Q 값 {v(pl_l, 'KR0070', 9, '2023.3Q')} | 2023.4Q 값 {v(pl_l, 'KR0070', 9, '2023.4Q')} 단일 {v(pl_l, 'KR0070', 9, '2023.4Q', '값_당분기')}")
P(f"   item 10: 2023.3Q 값 {v(pl_l, 'KR0070', 10, '2023.3Q')} | 2023.4Q 값 {v(pl_l, 'KR0070', 10, '2023.4Q')} 단일 {v(pl_l, 'KR0070', 10, '2023.4Q', '값_당분기')}")
P("-- KB라이프 KR0099 2023.1Q items 9/11/12 (old vintage) and 2023.2Q single")
for it in (9, 11, 12):
    P(f"   item {it}: 2023.1Q 값 {v(pl_l, 'KR0099', it, '2023.1Q')} | 2023.2Q 단일 {v(pl_l, 'KR0099', it, '2023.2Q', '값_당분기')}")
P("-- KDB KR0072 held: 2023.3Q / 2023.4Q items 17/18/20/22/24/31 equal HEAD (separate-basis original prints)")
for it in (17, 18, 20, 22, 24, 31):
    P(f"   item {it}: 3Q 값 head {v(pl_h, 'KR0072', it, '2023.3Q')} live {v(pl_l, 'KR0072', it, '2023.3Q')} | "
      f"4Q 값 head {v(pl_h, 'KR0072', it, '2023.4Q')} live {v(pl_l, 'KR0072', it, '2023.4Q')}")

OUT.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))  # LF only (write_text would add CR on Windows)
