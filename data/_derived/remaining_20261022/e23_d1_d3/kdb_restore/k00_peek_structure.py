# -*- coding: utf-8 -*-
"""Peek at the structure of the master / provenance / gold JSON files (read-only)."""
import json
import sys

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
OUT = ROOT + "/data/_derived/remaining_20261022/e23_d1_d3/kdb_restore/k00_peek_structure.txt"

FILES = [
    "PL_breakdown.json",
    "CSM_waterfall.json",
    "PL_breakdown_provenance.json",
    "CSM_waterfall_provenance.json",
    "data/_gold/user_pl_cells.json",
    "data/_gold/user_csm_cells.json",
    "data/_gold/gold_overlay_ledger.json",
    "data/_derived/qoq_warn.json",
    "data/_derived/pl_oci_vs_bs_aoci_warn.json",
    "tests/fixtures/master_tables_golden.json",
    "tests/fixtures/builder_input_fingerprints.json",
]


def short(v, n=300):
    s = json.dumps(v, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + "...(%d chars)" % len(s)


def describe(path, lines):
    with open(ROOT + "/" + path, "r", encoding="utf-8") as fh:
        raw = fh.read()
    lines.append("=" * 100)
    lines.append("%s  (%d chars, starts with BOM: %s)" % (path, len(raw), raw.startswith("\ufeff")))
    data = json.loads(raw)
    lines.append("top-level type: %s" % type(data).__name__)
    if isinstance(data, dict):
        keys = list(data.keys())
        lines.append("top-level keys (%d): %s" % (len(keys), short(keys, 600)))
        for k in keys[:6]:
            v = data[k]
            lines.append("  [%s] type=%s len=%s sample=%s" % (
                k, type(v).__name__, len(v) if hasattr(v, "__len__") else "-", short(v, 400)))
    elif isinstance(data, list):
        lines.append("list length: %d" % len(data))
        for i in (0, 1, len(data) - 1):
            if 0 <= i < len(data):
                lines.append("  item[%d]=%s" % (i, short(data[i], 600)))


def main():
    lines = []
    for p in FILES:
        try:
            describe(p, lines)
        except Exception as exc:  # report, do not hide
            lines.append("ERROR %s: %r" % (p, exc))
    text = "\n".join(lines) + "\n"
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    sys.stdout.reconfigure(encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
