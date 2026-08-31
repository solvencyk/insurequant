"""Diagnose why 28/39 companies are missing 금리민감도 2026.2Q rows.

Read-only: imports extract_kics_rate_sensitivity functions, runs the same
find_section_table/measure_rows/split_blocks pipeline for FY2026_Q2 only,
for ALL 39 companies (so we see the 11 that already work too, as a sanity
baseline), and reports which diag bucket each falls into + a snippet of the
raw MD around the '금리' + '민감도' heading search to see what's actually there.

Usage: PYTHONIOENCODING=utf-8 C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
       scripts/_probes/probe_20260901_ratesens_2026q2_diag.py
"""
from __future__ import annotations
import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import extract_kics_rate_sensitivity as ex  # noqa: E402

PERIOD = "FY2026_Q2"
QUARTER = "2026.2Q"

MISSING = """KR0001 KR0003 KR0004 KR0009 KR0011 KR0029 KR0032 KR0051 KR0068 KR0069
KR0070 KR0071 KR0072 KR0073 KR0079 KR0080 KR0082 KR0083 KR0087 KR0094
KR0097 KR0099 KR0100 KR0104 KR0150 KR1010 KR1011 KR1098""".split()

disc = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
names = {}
for r in disc:
    names.setdefault(r["원보험사코드"], r["원수사명"])

md_files = sorted((REPO / "md_inbox" / PERIOD).glob("*.md"))
all_codes = sorted({p.name.split("_", 1)[0] for p in md_files})
print(f"md_inbox/{PERIOD}: {len(all_codes)} companies")
print(f"missing list (owner-supplied): {len(MISSING)}")
print()

HEADING_ANY_MARKER = re.compile(r"금리|민감도")


def heading_lines(md_text):
    """All markdown heading lines that mention 금리 or 민감도 or 위험 (broad net)."""
    out = []
    for i, ln in enumerate(md_text.splitlines()):
        s = ln.lstrip()
        if s.startswith("#"):
            n = ex.norm(s)
            if "민감도" in n or ("금리" in n and "위험" in n) or "6-8" in n or "6.8" in n:
                out.append((i, ln.strip()))
    return out


buckets = {}
detail = {}
for code in all_codes:
    md_path = ex.pick_md(code, PERIOD)
    name = names.get(code, code)
    if md_path is None:
        buckets.setdefault("NO_MD", []).append(code)
        continue
    text = Path(md_path).read_text(encoding="utf-8")
    tbl = ex.find_section_table(text)
    heads = heading_lines(text)
    if tbl is None:
        # classify further: is there ANY heading that looks like the sensitivity section?
        if heads:
            bucket = "heading_present_no_table"
        else:
            bucket = "no_heading_at_all"
        buckets.setdefault(bucket, []).append(code)
        detail[code] = {"name": name, "md": md_path, "headings": heads[:5]}
        continue
    rows = ex.measure_rows(tbl)
    if not rows:
        buckets.setdefault("table_found_no_measure_rows", []).append(code)
        detail[code] = {"name": name, "md": md_path, "table_lines": len(tbl), "sample": tbl[:3]}
        continue
    blocks = ex.split_blocks(rows)
    emitted = sum(1 for blk in blocks if ex.block_dict(blk) is not None)
    if emitted == 0:
        buckets.setdefault("all_blocks_empty", []).append(code)
    else:
        buckets.setdefault("EXTRACTABLE", []).append(code)
    detail[code] = {"name": name, "md": md_path, "n_blocks": len(blocks), "emitted": emitted}

print("=== bucket summary ===")
for k, v in sorted(buckets.items(), key=lambda kv: -len(kv[1])):
    tag = "  (in MISSING list)" if any(c in MISSING for c in v) else ""
    print(f"  {k:32s} n={len(v):3d}  {sorted(v)}")

print()
print("=== cross-check vs owner MISSING list ===")
extractable_but_missing = [c for c in buckets.get("EXTRACTABLE", []) if c in MISSING]
print(f"EXTRACTABLE (should have worked) but in owner MISSING list: {extractable_but_missing}")
not_in_any_28 = [c for c in all_codes if c not in MISSING and c not in
                  ['KR0002','KR0005','KR0008','KR0010','KR0049','KR0050','KR0074','KR0075','KR0076','KR0095','KR1000']]
print(f"companies not accounted for (neither 11-present nor 28-missing): {not_in_any_28}")

print()
print("=== per-code detail for non-EXTRACTABLE among MISSING ===")
for code in MISSING:
    if code in buckets.get("EXTRACTABLE", []):
        continue
    d = detail.get(code, {})
    print(f"-- {code} {d.get('name','?')}")
    print(f"   md: {d.get('md')}")
    if "headings" in d:
        print(f"   headings found (n={len(d.get('headings', []))}): {d.get('headings')}")
    if "table_lines" in d:
        print(f"   table_lines={d.get('table_lines')}  sample={d.get('sample')}")
    if "n_blocks" in d:
        print(f"   n_blocks={d.get('n_blocks')} emitted={d.get('emitted')}")

out = REPO / "data" / "_derived" / "_probe_ratesens_2026q2_diag.json"
out.write_text(json.dumps({k: sorted(v) for k, v in buckets.items()}, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nwrote {out}")
