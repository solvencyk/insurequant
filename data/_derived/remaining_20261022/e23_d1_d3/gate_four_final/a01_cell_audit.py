# -*- coding: utf-8 -*-
"""a01: per-company cell-change census of PL_breakdown.json / CSM_waterfall.json, working tree vs git HEAD.

Read-only. Independent of the parser's k01/k03 scripts. A cell = (code, item, quarter) row's field.
Counts per company: value cells (값) changed + rows added + rows removed, and 값_당분기 changes separately,
plus any change in non-value fields (name, ticker, item name) so a silent relabel cannot hide.
Usage: python a01_cell_audit.py   (writes a01_cell_audit.txt next to this file)
"""
import collections
import json
import subprocess
from pathlib import Path

REPO = Path("C:/Users/sangwook.cho/Desktop/insurequant")
OUT = Path(__file__).resolve().parent / "a01_cell_audit.txt"
EXPECT = {"PL_breakdown.json": {"KR0099": 60, "KR0003": 18, "KR0070": 74, "KR0009": 57},
          "CSM_waterfall.json": {"KR0099": 15, "KR0003": 5, "KR0070": 20, "KR0009": 18}}
lines = []


def say(s=""):
    lines.append(s)


def head_json(name):
    raw = subprocess.run(["git", "-C", str(REPO), "show", "HEAD:" + name], capture_output=True, check=True).stdout
    return json.loads(raw.decode("utf-8"))


def cur_json(name):
    with open(REPO / name, "r", encoding="utf-8") as fh:
        return json.load(fh)


def keyed(rows):
    out, seen = {}, collections.Counter()
    for r in rows:
        k = (r["원보험사코드"], r["항목번호"], r["공시분기"])
        seen[k] += 1
        out[k + (seen[k],)] = r
    return out, sum(1 for v in seen.values() if v > 1)


def same(a, b):
    if a is None or b is None:
        return a is None and b is None
    return a == b


ok_all = True
for name, exp in EXPECT.items():
    h, dh = keyed(head_json(name))
    c, dc = keyed(cur_json(name))
    val = collections.Counter()
    dangi = collections.Counter()
    other = collections.Counter()
    added = collections.Counter()
    removed = collections.Counter()
    for k in set(h) | set(c):
        co = k[0]
        if k not in h:
            added[co] += 1
            if c[k].get("값") is not None:
                val[co] += 1
            continue
        if k not in c:
            removed[co] += 1
            if h[k].get("값") is not None:
                val[co] += 1
            continue
        a, b = h[k], c[k]
        if not same(a.get("값"), b.get("값")):
            val[co] += 1
        if not same(a.get("값_당분기"), b.get("값_당분기")):
            dangi[co] += 1
        for f in set(a) | set(b):
            if f not in ("값", "값_당분기") and a.get(f) != b.get(f):
                other[(co, f)] += 1
    say("=" * 80)
    say(f"{name}: HEAD rows {len(h)} (dup keys {dh}) -> working rows {len(c)} (dup keys {dc})")
    cos = sorted(set(val) | set(dangi) | set(added) | set(removed) | {x[0] for x in other} | set(exp) | {"KR0072"})
    for co in cos:
        say(f"  {co}: 값 changed {val[co]:4d} (added rows {added[co]}, removed rows {removed[co]})  "
            f"값_당분기 changed {dangi[co]:4d}  expected 값 {exp.get(co, 0)}")
    for co in cos:
        if val[co] != exp.get(co, 0):
            ok_all = False
            say(f"  MISMATCH {co}: {val[co]} != {exp.get(co, 0)}")
    unexpected_dangi = sorted(co for co in dangi if co not in exp)
    if unexpected_dangi:
        ok_all = False
        say(f"  MISMATCH 값_당분기 changed outside the four: {unexpected_dangi}")
    if other:
        ok_all = False
        say(f"  MISMATCH non-value fields changed: {dict(other)}")
    say(f"  total 값 changed {sum(val.values())} (expected {sum(exp.values())}); 값_당분기 changed {sum(dangi.values())}")
say("=" * 80)
say("RESULT " + ("PASS" if ok_all else "FAIL"))
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
