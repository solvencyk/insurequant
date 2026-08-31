# -*- coding: utf-8 -*-
"""Isolation take 2 -- import tests/test_kics_rules_golden.py's OWN _run()/_manifest() (exact
methodology, not a reimplementation) and monkeypatch its MASTER global to point at the
session-start backup vs the live (post-fix) file. Never writes to kics_disclosure.json.
"""
from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

BACKUP = REPO / "kics_disclosure.json.bak_20260901_035527_kr0005_combined_after"
LIVE = REPO / "kics_disclosure.json"

spec = importlib.util.spec_from_file_location(
    "test_kics_rules_golden", REPO / "tests" / "test_kics_rules_golden.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

golden = json.loads(mod.GOLDEN.read_text(encoding="utf-8"))


def run_against(path: Path) -> dict:
    mod.MASTER = path
    return mod._manifest(mod._run())


m_pre = run_against(BACKUP)
mod.MASTER = LIVE  # restore default before the second call (defensive, _run reads mod.MASTER)
m_post = run_against(LIVE)

print("golden sha256       :", golden.get("sha256"))
print("pre-fix (backup) sha :", m_pre["sha256"])
print("post-fix (live)  sha :", m_post["sha256"])
print()
print("pre-fix  == golden ?", m_pre["sha256"] == golden.get("sha256"))
print("post-fix == golden ?", m_post["sha256"] == golden.get("sha256"))
print("pre-fix  == post-fix (did MY edit change the run_validation() hash) ?",
      m_pre["sha256"] == m_post["sha256"])

print("\nby_status pre :", m_pre["by_status"])
print("by_status post:", m_post["by_status"])
print("by_status golden:", golden.get("by_status"))

if m_pre["by_rule"] != m_post["by_rule"]:
    print("\n--- by_rule diff (pre -> post, MY edit's effect) ---")
    rules = set(m_pre["by_rule"]) | set(m_post["by_rule"])
    for r in sorted(rules):
        a, b = m_pre["by_rule"].get(r), m_post["by_rule"].get(r)
        if a != b:
            print(f"  {r}: {a} -> {b}")
else:
    print("\nby_rule IDENTICAL pre vs post -- my edit did not move run_validation()'s output at all")

if golden.get("by_rule") != m_post["by_rule"]:
    print("\n--- by_rule diff (golden -> post-fix live, PRE-EXISTING drift unrelated to me) ---")
    rules = set(golden.get("by_rule", {})) | set(m_post["by_rule"])
    for r in sorted(rules):
        a, b = golden.get("by_rule", {}).get(r), m_post["by_rule"].get(r)
        if a != b:
            print(f"  {r}: golden={a} -> live={b}")
