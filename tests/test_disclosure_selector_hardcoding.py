# -*- coding: utf-8 -*-
"""Regression guard for inbox ticket 20260901T0140Z (downloader, disclosure
selector hardening).

**Why this exists.** In the 2026.2Q round, 3 non-life insurers silently
re-fetched their FY2026_Q1 정기경영공시 PDF instead of the requested 2026.2Q
one -- KR0011(DB손해)/KR0029(AIG손해)/KR0150(서울보증). Nothing raised: each
selector resolved to *some* element and the download "succeeded", it just
picked the wrong quarter --

  - KR0011: xpath ended in a fixed `li[1]` -- "first item in the list",
    not "this quarter's item".
  - KR0029: the second-step URL hardcoded `pancId=15467`, a per-posting id
    the site's own notes said "varies per quarter" -- the value never
    advanced past 2026.1Q.
  - KR0150: 5 quarterly download links on the same page all share
    `id="test1"`; Playwright's `.first` always grabbed whichever one the
    site happened to list first.

The downstream data-contract gate stayed RED=0 (false-green) because the
arithmetic on the stale numbers was internally consistent -- position/id
bugs like this are invisible to a rules engine that only checks the shape
of the data, not its provenance. Fixed 2026-09-01 by switching all 3 to
xpaths anchored on the quarter's own visible label text
(`contains(., "...")`) in both docs/agents/source-catalog.yaml (documentation)
and scripts/download_disclosure_2026q2_nonlife.py (the actual engine) --
verified live against both companies' sites (see the ticket's answer
section for the exact bytes/sha256 comparison against the manually
recovered files).

**Scope.** This freezes the fix for these 3 specific companies (not a
blanket ban on positional xpaths repo-wide -- several *other* entries in
the same catalog/engine carry their own, separately tracked positional
risk that is out of this ticket's scope, e.g. KR0010/KB's fixed `tr[3]`
row index, already flagged in its own comment as a caution, not a fix).
It also bans the `pancId=<digits>` literal company-agnostically, since
AIG's own site documents that parameter as varying every quarter -- any
hardcoded value is definitionally stale the moment a new quarter posts.
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
CATALOG = REPO / "docs" / "agents" / "source-catalog.yaml"
ENGINE = REPO / "scripts" / "download_disclosure_2026q2_nonlife.py"

# The 3 companies from the 2026-08-31 incident (inbox 20260901T0140Z).
GUARDED_KRS = ["KR0011", "KR0029", "KR0150"]

_SELECTOR_KEYS = (
    "url", "url1", "url2",
    "xpath", "xpath_step1", "xpath_step2",
    "step1_xpath", "step2_xpath", "period_verify_xpath",
)
_HAS_TEXT_ANCHOR = re.compile(r"contains\(")
_PANCID_LITERAL = re.compile(r"pancId=\d+")


def _load_engine_insurers() -> dict:
    spec = importlib.util.spec_from_file_location("_dl_engine_under_test", ENGINE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.INSURERS


def _load_catalog_entries() -> dict:
    data = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
    for src in data["sources"]:
        if src["id"] == "disclosure_nonlife":
            return {e["kr"]: e for e in src["entries"]}
    raise AssertionError("disclosure_nonlife source not found in " + str(CATALOG))


def _all_entries() -> dict:
    """kr -> merged {catalog entry, engine cfg} for every company appearing in
    either file, so the pancId check below covers both without re-reading."""
    merged: dict[str, dict] = {}
    for kr, e in _load_catalog_entries().items():
        merged.setdefault(kr, {}).update(e)
    for kr, e in _load_engine_insurers().items():
        merged.setdefault(kr, {}).update(e)
    return merged


def _selector_strings(entry: dict) -> list[str]:
    """All URL/xpath-ish string values on one entry (catalog dict and engine
    cfg dict share the same key vocabulary)."""
    return [v for k, v in entry.items() if k in _SELECTOR_KEYS and isinstance(v, str)]


@pytest.mark.parametrize("kr", GUARDED_KRS)
def test_catalog_entry_is_text_anchored(kr):
    entries = _load_catalog_entries()
    assert kr in entries, f"{kr} missing from {CATALOG.name} disclosure_nonlife entries"
    strings = _selector_strings(entries[kr])
    assert any(_HAS_TEXT_ANCHOR.search(s) for s in strings), (
        f"{kr}: no contains(...) text anchor in any of {strings!r} -- this reverted to "
        f"position/id-based selection (the 2026-08-31 incident this test guards against)"
    )


@pytest.mark.parametrize("kr", GUARDED_KRS)
def test_engine_entry_is_text_anchored(kr):
    insurers = _load_engine_insurers()
    assert kr in insurers, f"{kr} missing from {ENGINE.name} INSURERS"
    strings = _selector_strings(insurers[kr])
    assert any(_HAS_TEXT_ANCHOR.search(s) for s in strings), (
        f"{kr}: no contains(...) text anchor in any of {strings!r} -- this reverted to "
        f"position/id-based selection (the 2026-08-31 incident this test guards against)"
    )


@pytest.mark.parametrize("kr", ["KR0011", "KR0029"])
def test_engine_entry_not_hardcoded_detail_url(kr):
    """two_step_direct_url was the mode name for "skip the list page, jump
    straight to a hardcoded per-quarter detail URL" -- exactly the KR0011/
    KR0029 bug shape. The mode's handling branch was removed from _run_one
    when this was fixed, so reintroducing this string alone would already
    fail loudly at runtime (unknown mode); this test catches it at review
    time instead of at the next live run."""
    insurers = _load_engine_insurers()
    assert insurers[kr]["mode"] != "two_step_direct_url", (
        f"{kr}: mode='two_step_direct_url' hardcodes a per-quarter detail-page id/param "
        f"-- resolve it from the list page's own link text every run instead"
    )


def test_no_hardcoded_pancid_literal_anywhere():
    """Checks structured selector fields only (url/url1/url2/xpath/...), not
    free-text notes/comments -- this fix's own changelog-style comments
    necessarily quote the retired 'pancId=15467' value as history, which is
    not the bug this test guards against (a *live* config field using it)."""
    for kr, entry in _all_entries().items():
        for s in _selector_strings(entry):
            hits = _PANCID_LITERAL.findall(s)
            assert not hits, (
                f"{kr}: hardcoded pancId literal(s) {hits} in {s!r} -- AIG's own site notes "
                f"say this param varies every quarter, so any fixed value is stale by "
                f"definition; resolve it from the list page instead"
            )


@pytest.mark.parametrize("kr", GUARDED_KRS)
def test_engine_entry_declares_period_verify(kr):
    """Selector text-anchoring alone is a single point of failure if a future
    edit narrows the xpath without preserving the guard. period_include_regex
    makes the downloader itself assert (at run time, via _verify_period in
    the engine) that whatever it picked actually names the requested
    quarter, and fail loudly rather than silently save the wrong one."""
    insurers = _load_engine_insurers()
    assert "period_include_regex" in insurers[kr], (
        f"{kr}: no period_include_regex -- the engine can no longer verify it "
        f"picked the requested quarter before downloading"
    )
