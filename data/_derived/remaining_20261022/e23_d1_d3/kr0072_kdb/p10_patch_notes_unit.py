# -*- coding: utf-8 -*-
"""patch kdb_notes.py: use the in-table unit (table_unit) at both call sites (asserted single-hit substitutions)."""
from pathlib import Path

p = Path(__file__).resolve().parent / "kdb_notes.py"
s = p.read_text(encoding="utf-8")


def sub(a, b, count=1):
    global s
    assert s.count(a) == count, (s.count(a), a[:80])
    s = s.replace(a, b)


sub("    un, unl = unit_above(L, ta + 1, span=120)\n    hdr = next(r for r in rows if r[\"cells\"] and nspace(r[\"cells\"][0][\"text\"]) == \"구분\")",
    "    un, unl, uwhere = table_unit(L, ta, tb)\n    hdr = next(r for r in rows if r[\"cells\"] and nspace(r[\"cells\"][0][\"text\"]) == \"구분\")")
sub("out = dict(printed=t, line=ln, unit=un, unit_line=unl, mn=mn(t, un),", "out = dict(printed=t, line=ln, unit=un, unit_line=unl, unit_where=uwhere, mn=mn(t, un),")
sub("        un, _ = unit_above(L, ta + 1, span=120)\n        res, extra = {}, {}", "        un, unl, uwhere = table_unit(L, ta, tb)\n        res, extra = {}, {}")
sub("out[role] = dict(rows=res, extra=extra, table=(ta + 1, tb + 1), caption=(cap_line, cap_txt), unit=un, col=jcsm, heads=heads)",
    "out[role] = dict(rows=res, extra=extra, table=(ta + 1, tb + 1), caption=(cap_line, cap_txt), unit=un, unit_line=unl, unit_where=uwhere, col=jcsm, heads=heads)")
p.write_text(s, encoding="utf-8", newline="\n")
print("patched")
