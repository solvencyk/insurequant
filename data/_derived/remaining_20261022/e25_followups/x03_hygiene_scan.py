# -*- coding: utf-8 -*-
"""READ-ONLY hygiene scan of every file this batch created or changed: valid UTF-8, no BOM, no U+FFFD replacement character, no Japanese kana (U+3040-U+30FF), .py files parse (ast).
usage: x03_hygiene_scan.py  -> x03_hygiene_scan.txt"""
import ast
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
EV = ROOT / "data/_derived/remaining_20261022/e25_followups"
files = []
for p in EV.rglob("*"):
    if p.is_file() and "backup_before_apply" not in p.parts and "__pycache__" not in p.parts and p.suffix.lower() in (".py", ".md", ".txt", ".json", ".sh", ".diff", ".log"):
        files.append(p)
for rel in ("scripts/build_root_masters.py", "tests/test_rule_coverage_manifest.py", "tests/test_gold_overlay_survives_rebuild.py", "tests/fixtures/master_tables_golden.json", "tests/fixtures/builder_input_fingerprints.json",
            "TODO_parser_ifrs17.md", "docs/changelog_parser_ifrs17.md", "docs/todo_archive_parser_ifrs17.md", "data/_gold/user_pl_cells.json", "data/_gold/user_csm_cells.json", "PL_breakdown.json", "CSM_waterfall.json",
            "PL_breakdown_provenance.json"):
    files.append(ROOT / rel)
for p in (ROOT / "inbox/parser").glob("20261023T1130Z*"):
    files.append(p)
for pat in ("20261023T1210Z*", "20261023T0600Z*", "20261024T0100Z*", "20261023T1215Z*"):
    files += list((ROOT / "inbox/parser").glob(pat))
KANA = re.compile("[\u3040-\u30ff]")
bad, n = [], 0
for p in sorted(set(files)):
    b = p.read_bytes()
    n += 1
    why = []
    if b.startswith(b"\xef\xbb\xbf"):
        why.append("BOM")
    try:
        t = b.decode("utf-8")
    except UnicodeDecodeError as e:
        why.append(f"not UTF-8 ({e.reason} at {e.start})")
        t = None
    if t is not None:
        if "\ufffd" in t:
            why.append("U+FFFD")
        if KANA.search(t):
            why.append("kana " + "".join(sorted(set(KANA.findall(t))))[:20])
        if p.suffix == ".py":
            try:
                ast.parse(t.lstrip("\ufeff"))
            except SyntaxError as e:
                why.append(f"SyntaxError {e}")
    if why:
        bad.append((str(p.relative_to(ROOT)), why))
out = [f"scanned {n} files; problems {len(bad)}"] + [f"  {a}: {', '.join(w)}" for a, w in bad]
print("\n".join(out))
(EV / "x03_hygiene_scan.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
