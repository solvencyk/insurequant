# -*- coding: utf-8 -*-
"""Patch this folder's planner copy (asserted substitutions, each must hit exactly once).
KDB 2023.2Q prints the CSM amortisation 23,415 in BOTH the consolidated-looking notes (L21229) and the separate notes (L40301) of the original filing (same text), so the shared locator
(which expects exactly one hit with sep_only=False) raises.  Same fallback as the ABL load: use the separate-only hit (one hit) for BOTH the gold-source print and the separate original print."""
from pathlib import Path

p = Path(__file__).resolve().parent / "e23_plan.py"
s = p.read_text(encoding="utf-8")


def sub(a, b, count=1):
    global s
    assert s.count(a) == count, (s.count(a), a[:100])
    s = s.replace(a, b)


sub('def jl(rel):\n    return json.loads((ROOT / rel).read_text(encoding="utf-8"))\n',
    'def jl(rel):\n    return json.loads((ROOT / rel).read_text(encoding="utf-8"))\n\n\n'
    'def orig_print_records23(code, q, item):\n'
    '    """shared locator, with a fallback for a print that appears in both the consolidated-looking and the separate notes (same text): use the separate-only hit for both records"""\n'
    '    try:\n'
    '        return PF.orig_print_records(code, q, item)\n'
    '    except RuntimeError as e:\n'
    '        if "located 2 times" not in str(e):\n'
    '            raise\n'
    '        spec = PF.ORIG_PRINT[(code, q, item)]\n'
    '        gs = PF.print_record(code, q, spec["gold_src"], sep_only=True)\n'
    '        return gs, gs\n')
sub('gs, op = PF.orig_print_records(c["code"], c["quarter"], c["item"])', 'gs, op = orig_print_records23(c["code"], c["quarter"], c["item"])')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok", len(s))
