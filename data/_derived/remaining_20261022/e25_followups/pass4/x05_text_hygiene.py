# -*- coding: utf-8 -*-
"""READ-ONLY: encoding hygiene of every file this ticket wrote or changed (BOM-free UTF-8, no kana, no U+FFFD, new gold notes readable)."""
import glob, json, re, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
EV = f"{ROOT}/data/_derived/remaining_20261022/e25_followups/pass4"
files = [f"{ROOT}/{p}" for p in ("PL_breakdown.json", "PL_breakdown_provenance.json", "data/_gold/user_pl_cells.json", "tests/test_rule_coverage_manifest.py", "TODO_parser_ifrs17.md", "docs/changelog_parser_ifrs17.md",
                                 "inbox/parser/20261024T1000Z__orchestrator__KR0087-KR0032__2023.1Q-2024.4Q__complete_blocks_dongyang_nhfire.md", "tests/fixtures/master_tables_golden.json")]
files += sorted(glob.glob(f"{EV}/*.py")) + sorted(glob.glob(f"{EV}/*/*.py")) + sorted(glob.glob(f"{EV}/*.txt")) + sorted(glob.glob(f"{EV}/*/*.txt")) + [f"{EV}/answer_ticket.md", f"{EV}/INDEX.txt", f"{EV}/p4_plan.json"]
KANA = re.compile("[\u3040-\u30ff]")
bad = 0
for f in files:
    try:
        b = open(f, "rb").read()
    except FileNotFoundError:
        continue
    issues = []
    if b.startswith(b"\xef\xbb\xbf"):
        issues.append("BOM")
    try:
        t = b.decode("utf-8")
    except UnicodeDecodeError as e:
        issues.append("not utf-8: %s" % e)
        t = b.decode("utf-8", errors="replace")
    if KANA.search(t):
        issues.append("kana")
    if "\ufffd" in t:
        issues.append("U+FFFD")
    if issues:
        bad += 1
        print("ISSUE", f.replace(ROOT + "/", ""), issues)
print("files scanned", len(files), "with issues", bad)
g = json.load(open(f"{ROOT}/data/_gold/user_pl_cells.json", encoding="utf-8"))
for e in g["set"][-15:]:
    print(e["원보험사코드"], e["공시분기"], e["항목번호"], e["값"], "|", e["note"][:150].replace("\n", " "))
