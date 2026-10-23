# -*- coding: utf-8 -*-
"""Proves the new live-data test (tests/test_rule_coverage_manifest.py::test_csm_null_dangi_is_declared_read_and_enforced) is sensitive: it must FAIL when the builder ignores / mis-reads the entry.
Mutation M1: build_root_masters._csm_null_dangi_keys returns the empty set (builder ignores the section).  M2: it returns a different cell (reads the wrong item).  M3: it silently ignores set_dangi.
Baseline: the unmutated test passes."""
import importlib.util
import sys
import tempfile
from pathlib import Path

import pytest

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "src"))
spec = importlib.util.spec_from_file_location("trcm", str(ROOT / "tests/test_rule_coverage_manifest.py"))
T = importlib.util.module_from_spec(spec)
spec.loader.exec_module(T)
import build_root_masters as brm  # noqa: E402

orig = brm._csm_null_dangi_keys


def run(label, patch):
    mp = pytest.MonkeyPatch()
    brm._csm_null_dangi_keys = orig
    if patch is not None:
        brm._csm_null_dangi_keys = patch
    try:
        with tempfile.TemporaryDirectory() as td:
            try:
                T.test_csm_null_dangi_is_declared_read_and_enforced(Path(td), mp)
                res = "PASS (test did not fail)"
            except BaseException as e:  # noqa: BLE001
                res = f"FAIL as expected: {type(e).__name__}: {str(e)[:120]}"
    finally:
        mp.undo()
        brm._csm_null_dangi_keys = orig
    print(f"{label:55s} -> {res}")
    return res.startswith("PASS")


ok0 = run("baseline (unmutated builder)", None)
m1 = run("M1 builder ignores null_dangi (empty set)", lambda p: set())
m2 = run("M2 builder reads the wrong item (item 2 instead)", lambda p: {("KR0003", "2023.4Q", 2)})


def m3(p):
    import json
    doc = json.loads(Path(p).read_text(encoding="utf-8"))
    return {(c[0], c[1], int(c[2])) for c in (doc.get("null_dangi") or {}).get("cells", [])}      # same keys, but never refuses set_dangi
m3r = run("M3 builder silently ignores set_dangi", m3)
print("RESULT:", "OK (baseline passes, all mutations detected)" if ok0 and not (m1 or m2 or m3r) else "NOT SENSITIVE")
sys.exit(0 if ok0 and not (m1 or m2 or m3r) else 1)
