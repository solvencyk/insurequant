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
import os
import re
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
