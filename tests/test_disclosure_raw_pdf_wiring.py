# -*- coding: utf-8 -*-
"""Regression guard for inbox ticket 20260901T0430Z (parser/kics, raw-vs-pdf-dir assumption).

**Why this exists.** `data/disclosure/<period>/raw/` was the only populated PDF directory for
13 straight quarters (FY2023_Q1..FY2026_Q1), so scripts hard-coded `.../raw/*.pdf` glob calls.
FY2026_Q2 flipped it (raw/ has 1 file, pdf/ has 39) and every script that hard-coded raw/ went
from "found the file" to "silently found nothing" -- no exception, no log, just an empty PDF
list that reads as "nothing to do" (validate_kics_disclosure `[UNMEASURED]`,
`rebuild_combined_transition_after.py`'s `rejects` bucket, etc). The same bug landed at least
THREE separate times in this repo (`rebuild_combined_transition_after.py::_pdf()`,
`fill_market_subitems_to_disclosure.py`, then a batch of 11 more scripts caught by validation's
2026-09-01 sweep) before `scripts/_disclosure_pdf_paths.py::disclosure_pdfs()` was written as
the single interpreter (raw/ first, pdf/ only as fallback -- preserves all 13 legacy quarters'
resolution unchanged; scripts/_probes/verify_20260901_disclosure_pdfs_no_regression.py measured
0 flips across 509 (period, code) pairs).

"Wrote the interpreter" is not "nobody can bypass it" -- this repo has been burned by exactly
that gap before (CLAUDE.md: "'배선했다' != '강제된다'"). This test makes bypassing it a failing
build instead of a fourth silent recurrence: it statically scans every top-level `scripts/*.py`
file for the shape `<path-expr referencing "disclosure"> / "raw"` used as the object of a
`.glob(...)` call (or fed to `glob.glob(str(...))`), which is exactly the pattern every one of
the 13 prior offenders used.

**Scope.** Only direct children of `scripts/` (not `scripts/_probes/`, which is disposable
point-in-time diagnostics, not pipeline code an owner reads or a gate calls; not
`scripts/pl_breakdown/`, an ifrs17-lane package with no `data/disclosure` reason to exist).
`data/dart/<period>/raw`, `data/kidi/<period>/raw`, `data/ir/<period>/raw`, `data/bonds/.../raw`
are different sources with no raw/pdf split and are deliberately NOT flagged -- the detector
requires "disclosure" to be reachable from the same path expression, not just present anywhere
in the file (see the negative-control cases below).
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO / "scripts"
INTERPRETER = "_disclosure_pdf_paths.py"

# Ticket-approved: 1회성, 특정 분기에 고정된 스크립트 (inbox 20260901T0430Z 본문 "제외해도 되는 것").
ALLOWLIST = {
    "fix_20260821_tier2_limit_lines.py",
    "fix_20260824_register_source_vision.py",
}


def _is_raw_join(expr: ast.AST) -> bool:
    """True for the AST of `<anything> / "raw"` (or `'raw'`) -- a pathlib join whose LAST
    segment is literally the raw/ directory name."""
    return (
        isinstance(expr, ast.BinOp)
        and isinstance(expr.op, ast.Div)
        and isinstance(expr.right, ast.Constant)
        and expr.right.value == "raw"
    )


def _contains_raw_join(expr: ast.AST) -> bool:
    return any(_is_raw_join(n) for n in ast.walk(expr))


def _refs_disclosure(expr: ast.AST, assigns: dict[str, ast.AST], seen: frozenset[str] = frozenset()) -> bool:
    """True if `expr`'s subtree contains the string literal "disclosure", directly or via a
    Name that (transitively) resolves to an assignment containing it."""
    for n in ast.walk(expr):
        if isinstance(n, ast.Constant) and n.value == "disclosure":
            return True
        if isinstance(n, ast.Name) and n.id in assigns and n.id not in seen:
            if _refs_disclosure(assigns[n.id], assigns, seen | {n.id}):
                return True
    return False


def _unwrap_str_call(expr: ast.AST) -> ast.AST:
    """`str(X)` -> `X`; anything else unchanged (glob.glob(str(path)) is the common form)."""
    if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name) and expr.func.id == "str" and expr.args:
        return expr.args[0]
    return expr


def find_violations(source: str, filename: str = "<test>") -> list[str]:
    """-> list of 'lineno: <code>' strings for every disclosure-raw-only glob found."""
    tree = ast.parse(source, filename=filename)
    assigns: dict[str, ast.AST] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            assigns[node.targets[0].id] = node.value

    hits: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        # Both shapes end in a `.glob` attribute access: `X.glob(...)` (X = a path expression,
        # possibly via an intermediate Name) and the module-level `glob.glob(str(X))` (where
        # `glob` itself is the module Name, not a path -- must read args[0], not func.value).
        # `.iterdir()` is included too: audit_all_periods.py's original offender enumerated
        # raw/ by hand (`for f in raw.iterdir(): if f.name.startswith(...)`) instead of
        # globbing -- same bug class, no `.glob(` call to catch it by.
        if not (isinstance(node.func, ast.Attribute) and node.func.attr in ("glob", "iterdir")):
            continue
        obj = node.func.value
        if node.func.attr == "glob" and isinstance(obj, ast.Name) and obj.id == "glob":
            if not node.args:
                continue
            target = _unwrap_str_call(node.args[0])
        elif isinstance(obj, ast.Name) and obj.id in assigns:
            target = assigns[obj.id]
        else:
            target = obj
        if _contains_raw_join(target) and _refs_disclosure(target, assigns):
            hits.append(f"line {node.lineno}: {ast.unparse(node)[:120]}")
    return hits


def _candidate_scripts() -> list[Path]:
    return sorted(
        p for p in SCRIPTS_DIR.glob("*.py")
        if p.name != INTERPRETER and p.name not in ALLOWLIST
    )


@pytest.mark.parametrize("path", _candidate_scripts(), ids=lambda p: p.name)
def test_script_does_not_glob_disclosure_raw_directly(path: Path):
    # This tree is shared with concurrent sibling sessions (CLAUDE.md multi-agent parallel
    # workflow) that create/delete their own scratch scripts directly under scripts/ while
    # this file runs -- a file present at collection time can be gone by the time this test
    # body executes. That's not a violation of anything; skip rather than error (observed
    # 2026-09-01: scripts/_tmp_orig_tier2_20260901.py raced exactly this way).
    try:
        src = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        pytest.skip(f"{path.name} no longer exists (removed by a concurrent session)")
    hits = find_violations(src, filename=str(path))
    assert not hits, (
        f"{path.relative_to(REPO)} globs data/disclosure/<period>/raw/ directly, bypassing "
        f"scripts/_disclosure_pdf_paths.py::disclosure_pdfs() -- this silently drops every "
        f"quarter whose PDFs live under pdf/ instead of raw/ (FY2026_Q2: raw=1, pdf=39; the "
        f"same bug hit 13 scripts before, see inbox/parser/_resolved or the 20260901T0430Z "
        f"ticket). Import disclosure_pdfs(period, code) instead:\n  " + "\n  ".join(hits)
    )


# --- self-test: prove the detector actually fires (and doesn't over-fire) ------------------

_BUGGY_SNIPPETS = [
    # scripts/append_kics_detail_from_pdf.py's original shape
    'REPO = X\n'
    'def f(period, code):\n'
    '    raw = REPO / "data" / "disclosure" / period / "raw"\n'
    '    pdfs = sorted(raw.glob(f"{code}_*.pdf"))\n',
    # scripts/extract_market_section_pages.py's original shape (glob.glob(str(...)))
    'import glob\n'
    'DISCLOSURE = X / "data" / "disclosure"\n'
    'def f(quarter, code):\n'
    '    pdfs = sorted(glob.glob(str(DISCLOSURE / quarter_to_period(quarter) / "raw" / f"{code}_*.pdf")))\n',
    # inline, no intermediate variable
    'def f(period, code):\n'
    '    return sorted((ROOT / "data" / "disclosure" / period / "raw").glob(f"{code}_*.pdf"))\n',
    # scripts/audit_all_periods.py's original shape: iterdir(), not glob()
    'def has_disclosure_file(period, kr):\n'
    '    raw = ROOT / "data" / "disclosure" / period / "raw"\n'
    '    for f in raw.iterdir():\n'
    '        if f.is_file() and f.name.startswith(kr + "_"):\n'
    '            return True\n'
    '    return False\n',
]

_SAFE_SNIPPETS = [
    # the actual fix
    'from _disclosure_pdf_paths import disclosure_pdfs\n'
    'def f(period, code):\n'
    '    pdfs = disclosure_pdfs(period, code)\n',
    # a DIFFERENT source's raw/ dir (dart) -- must NOT be flagged (no "disclosure" anywhere)
    'def f(period, code):\n'
    '    raw_dir = ROOT / "data" / "dart" / period / "raw"\n'
    '    return list(raw_dir.glob(f"{code}_*"))\n',
    # disclosure appears in the file, but this glob is for an unrelated raw/ dir (kidi) --
    # the detector must scope "refs_disclosure" to the glob's own expression, not the file
    'DISCLOSURE = ROOT / "data" / "disclosure"\n'
    'def f(period, code):\n'
    '    raw_dir = ROOT / "data" / "kidi" / period / "raw"\n'
    '    return list(raw_dir.glob(f"{code}_*.json"))\n',
    # globbing the disclosure pdf/ dir directly is fine -- only raw/ is the banned literal
    'DISCLOSURE = ROOT / "data" / "disclosure"\n'
    'def f(period, code):\n'
    '    return sorted((DISCLOSURE / period / "pdf").glob(f"{code}_*.pdf"))\n',
]


@pytest.mark.parametrize("snippet", _BUGGY_SNIPPETS)
def test_detector_catches_the_known_buggy_shapes(snippet):
    assert find_violations(snippet), f"detector missed a known-buggy pattern:\n{snippet}"


@pytest.mark.parametrize("snippet", _SAFE_SNIPPETS)
def test_detector_does_not_flag_safe_patterns(snippet):
    hits = find_violations(snippet)
    assert not hits, f"detector false-positived on a safe pattern:\n{snippet}\n-> {hits}"


def test_allowlist_entries_actually_exist_and_are_still_offenders():
    """If an allowlisted file gets fixed (or deleted) later, its entry should come out --
    otherwise the allowlist silently grows stale and nobody notices new files re-adding the
    same name by coincidence would be masked too. Not fatal (deletion is fine), just visible."""
    for name in ALLOWLIST:
        p = SCRIPTS_DIR / name
        if not p.exists():
            continue  # deleted since -- fine, nothing to mask
        hits = find_violations(p.read_text(encoding="utf-8"), filename=str(p))
        if not hits:
            pytest.fail(
                f"{name} is allowlisted as a raw-only offender but no longer contains the "
                f"pattern -- remove it from ALLOWLIST in tests/test_disclosure_raw_pdf_wiring.py "
                f"so it goes back under active enforcement."
            )
