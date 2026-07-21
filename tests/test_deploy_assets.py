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
