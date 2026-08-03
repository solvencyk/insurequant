#!/usr/bin/env python3
"""Every file a deployed page fetches must exist in the repo.

The live site is a static GitHub Pages deploy of a hand-derived keep-list
(see docs/agents/claude-agent-publishing.md §0: "derive the keep-list,
never guess it"). If a page starts fetching a new JSON and that file is
not shipped, the panel silently falls back to its placeholder — no error,
no console message, just a blank panel nobody notices.

That is exactly the failure mode this repo has been bitten by, so assert
it mechanically instead of relying on the deploy checklist. Fast and
deterministic: no browser, no server.
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
PAGES = ["index.html", "K-ICS.html", "IFRS17.html", "공시보고서.html"]

# fetch('x.json'), fetch("x.json"), fetch(`x.json`)
_FETCH = re.compile(r"""fetch\(\s*['"`]([^'"`)]+)['"`]""")
# <link href="...">, <script src="...">, <img src="...">
_ASSET = re.compile(r"""<(?:link[^>]*href|script[^>]*src|img[^>]*src)\s*=\s*["']([^"']+)["']""")


def _local(url: str) -> bool:
    return not url.startswith(("http://", "https://", "//", "data:"))


def _referenced(page: Path) -> set[str]:
    html = page.read_text(encoding="utf-8")
    return {u for u in (_FETCH.findall(html) + _ASSET.findall(html)) if _local(u)}


def test_every_python_file_parses():
    """No BOM / UTF-16 sources.

    CLAUDE.md mandates UTF-8 without BOM, and the failure is nasty: a UTF-16
    file cannot be executed at all ("source code string cannot contain null
    bytes" — scripts/export_red_all_cases.py sat broken while the publishing
    prompt listed it as a tool), and a UTF-8 BOM runs fine but breaks every
    AST-based check, so such files are invisible to exactly the tooling that
    would find problems in them. Both classes were found by hand twice
    (2026-07-21 in scripts/, 2026-07-22 in src/bonds/); assert it instead.
    """
    skip = {".git", "__pycache__", "node_modules", "archive", "data", "output",
            "md_inbox", "research", ".venv"}
    bad = []
    for dirpath, dirnames, filenames in os.walk(REPO):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            p = Path(dirpath) / fn
            raw = p.read_bytes()
            if raw.startswith((b"\xef\xbb\xbf", b"\xff\xfe", b"\xfe\xff")):
                bad.append(f"{p.relative_to(REPO)}: BOM")
                continue
            try:
                ast.parse(raw.decode("utf-8"))
            except Exception as e:
                bad.append(f"{p.relative_to(REPO)}: {type(e).__name__} {e}")
    assert not bad, "files that are not clean UTF-8 Python:\n  " + "\n  ".join(bad)


@pytest.mark.parametrize("page_name", PAGES)
def test_referenced_files_exist(page_name):
    page = REPO / page_name
    if not page.exists():
        pytest.skip(f"{page_name} not in this working tree")
    missing = sorted(u for u in _referenced(page) if not (REPO / u).exists())
    assert not missing, (
        f"{page_name} references files that are not in the repo: {missing}. "
        "A deployed page fetching a missing file fails silently."
    )


def test_no_reference_to_deleted_source_paths():
    """Nothing may point at a repo path that no longer exists.

    The 2026-07-21 refactor deleted src/solvency/{legacy,transform} and
    validation/{rules,schema}.py. The markdown-link audit could not see the
    four downloader profiles that told a future session to "port the
    click-driven flow from src/solvency/legacy/downloaders/..." — that
    instruction lived inside a YAML `notes:` block, not a link. Those now say
    where to retrieve the file from git, which is why a `git show <sha>:path`
    line is allowed.
    """
    gone = [
        "src/solvency/legacy/",
        "src/solvency/transform/",
        "src/solvency/validation/rules.py",
        "src/solvency/validation/schema.py",
        "schemas/kics_data.schema.json",
    ]
    skip_dirs = {".git", "__pycache__", "node_modules", "archive", "data",
                 "output", "md_inbox", "research", ".venv", ".pytest_cache", "_resolved"}
    exts = {".py", ".yaml", ".yml", ".json", ".js", ".cfg", ".toml", ".txt"}
    hits = []
    for dirpath, dirnames, filenames in os.walk(REPO):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for fn in filenames:
            p = Path(dirpath) / fn
            if p.suffix.lower() not in exts or p.name == Path(__file__).name:
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for g in gone:
                if g not in text:
                    continue
                # a file that also shows how to retrieve it from git is documenting
                # the deletion, not still depending on the path
                if re.search(rf"git show [0-9a-f]{{7,40}}:{re.escape(g)}", text):
                    continue
                line_no = text[:text.index(g)].count("\n") + 1
                hits.append(f"{p.relative_to(REPO)}:{line_no} -> {g}")
    assert not hits, "references to deleted paths:\n  " + "\n  ".join(hits)


def _fetched_json(page: Path) -> set[str]:
    """Every .json URL the page actually requests, including fetch(<var>)."""
    t = page.read_text(encoding="utf-8")
    u = set(_FETCH.findall(t))
    u |= set(re.findall(r"""resolveUrl\(\s*['"]([^'"]+)['"]""", t))
    for a, b in re.findall(r"""dataPaths\(\s*['"]([^'"]+)['"]\s*,\s*['"]([^'"]+)['"]""", t):
        u |= {a, b}
    for var in re.findall(r"fetch\(\s*([A-Za-z_$][\w$]*)\s*\)", t):
        m = re.search(rf"""{re.escape(var)}\s*=\s*['"]([^'"]+\.json)['"]""", t)
        if m:
            u.add(m.group(1))
    return {x.lstrip("./") for x in u if x.endswith(".json")}


def test_docs_agree_with_what_pages_fetch():
    """The two docs that drive the deploy keep-list must match reality.

    claude-agent-publishing.md §1 and claude-agent-designer.md §1 both tabulate
    "which page reads which JSON". On 2026-07-22 both were wrong in BOTH
    directions — they listed five files no page fetches (csm_bubble.json,
    ifrs17_panels.json, net_income_breakdown.json, disclosed_csm_multiple.json,
    nb_premium_wolnap.json) and omitted eight that are fetched. The keep-list is
    derived from those tables, so a wrong table means a silently broken deploy.

    Assert the weaker, stable direction: every JSON a page fetches must be named
    in both docs. (The reverse — a doc naming an unfetched file — is intentional
    in the "이전 표에 있었으나 읽지 않는 것" note, so it is not asserted.)
    """
    docs = {
        "claude-agent-publishing.md": (REPO / "docs/agents/claude-agent-publishing.md"),
        "claude-agent-designer.md": (REPO / "docs/agents/claude-agent-designer.md"),
    }
    missing = []
    for page_name in PAGES:
        page = REPO / page_name
        if not page.exists():
            continue
        for url in sorted(_fetched_json(page)):
            base = Path(url).name
            for doc_name, doc in docs.items():
                if doc.exists() and base not in doc.read_text(encoding="utf-8"):
                    missing.append(f"{doc_name} never mentions {base} (fetched by {page_name})")
    assert not missing, (
        "deploy keep-list docs are out of date with the pages:\n  " + "\n  ".join(missing)
    )


def test_kics_panel_data_is_external():
    """K-ICS.html must not carry its panel data inline again.

    Until 2026-07-21 the tier1/tier2/forward panel JSON was pasted into the
    page as window.TIER1_DATA / TIER2_DATA / FORWARD_DATA — 147KB, 70% of
    the file, with no generator for two of the three, so the HTML copy could
    drift from the JSON the builders produced.
    """
    html = (REPO / "K-ICS.html").read_text(encoding="utf-8")
    inline = [n for n in ("TIER1_DATA", "TIER2_DATA", "FORWARD_DATA")
              if f"window.{n} =" in html]
    assert not inline, f"panel data inlined back into K-ICS.html: {inline}"

    for name in ("kics_tier1_utilization.json", "kics_tier2_utilization.json",
                 "kics_forward_capital.json"):
        assert f"fetch('{name}')" in html, f"K-ICS.html no longer fetches {name}"
        assert (REPO / name).exists(), f"missing deploy asset {name}"


def test_capsec_provenance_source_id_matches_lineage():
    """The three capital-securities sidecars must declare the source_id their source_file's
    lineage actually implies — and be reproducible by a generator, not typed by hand.

    Until 2026-08-03 all three said `source_id: "FSC_BONDS"` because the gate hardcoded that
    enum, while tier1/tier2 had been fed by DART since 2026-06-20
    (`data/bonds/capital_securities_fy2025.json`). The gate "verified" a label that was false —
    a false-green (owner inbox/validation/20260803T0056Z, PM-2026-08-03). The gate now REDs on
    the mismatch (SOURCE_ID_LINEAGE_MISMATCH); this test is the fast local signal so a rebuild
    that washes the correction out is caught before push.
    """
    import subprocess

    sys.path.insert(0, str(REPO / "scripts"))
    from validate_data_contract import source_id_for_lineage

    for name in ("kics_forward_capital_provenance.json",
                 "kics_tier1_utilization_provenance.json",
                 "kics_tier2_utilization_provenance.json"):
        p = REPO / name
        assert p.exists(), f"missing provenance sidecar {name}"
        for cell in json.loads(p.read_text(encoding="utf-8")).get("cells", []):
            sf = cell.get("source_file")
            expected = source_id_for_lineage(sf)
            assert expected is not None, (
                f"{name}: source_file={sf} lineage unregistered in _SOURCE_LINEAGE")
            assert cell.get("source_id") == expected, (
                f"{name}: source_id={cell.get('source_id')} but {sf} lineage is {expected}")
            assert cell.get("effective_filtered") is True, (
                f"{name}: effective_filtered must stay true (donut bug guard)")

    # the sidecars must be regenerable — a hand-typed sidecar has no defence against a rebuild
    r = subprocess.run([sys.executable, str(REPO / "scripts" / "emit_capsec_provenance.py"),
                        "--check"], capture_output=True, text=True, encoding="utf-8", cwd=REPO)
    assert r.returncode == 0, (
        f"emit_capsec_provenance.py --check reports drift:\n{r.stdout}\n{r.stderr}")
