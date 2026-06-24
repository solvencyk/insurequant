#!/usr/bin/env python3
"""Compute Subresource Integrity (SRI) sha384 hashes for the CDN assets used by
the deployed insurequant.com HTML pages.

WHY: the 4 deployed pages (index.html, K-ICS.html, IFRS17.html, 공시보고서.html)
load chart.js / echarts / chartjs-plugin-annotation / pretendard from
cdn.jsdelivr.net with NO integrity= attribute. If jsdelivr (or the package)
were tampered, the pages would execute attacker JS. SRI pins the exact bytes.

This script must run somewhere with outbound internet (the build/dev machine).
The Claude Code sandbox has no network, so the hashes cannot be computed there.

USAGE:
    python scripts/compute_sri.py

It prints, for each pinned URL, the ready-to-paste integrity attribute, e.g.:
    chart.js@4.4.0 -> integrity="sha384-XXXX..." crossorigin="anonymous"

Then the 'designer' stage pastes each value onto the matching <script>/<link>
tag (same pinned version) across the HTML files.

NOTE on fonts: SRI on the pretendard .css protects the CSS file only. The woff2
font files it pulls via @font-face are NOT SRI-protected (no SRI mechanism for
CSS-referenced subresources). Self-hosting pretendard would close that gap.
"""

import base64
import hashlib
import sys
import urllib.request

# Exact pinned URLs as referenced in the HTML <head> (keep versions in lockstep
# with the tags; if a version bumps, update both here and the HTML).
ASSETS = [
    ("chart.js@4.4.0",
     "https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"),
    ("echarts@5.5.0",
     "https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"),
    ("chartjs-plugin-annotation@3.0.1",
     "https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"),
    ("pretendard@v1.3.9 (css)",
     "https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css"),
]


def sri_for(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "sri-compute/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read()
    digest = hashlib.sha384(body).digest()
    return "sha384-" + base64.b64encode(digest).decode("ascii")


def main() -> int:
    failed = False
    print("# SRI integrity values (sha384). Paste onto the matching pinned tag.\n")
    for name, url in ASSETS:
        try:
            integrity = sri_for(url)
        except Exception as exc:  # noqa: BLE001 - report and continue
            failed = True
            print(f"{name}\n  ERROR fetching {url}: {exc}\n")
            continue
        print(f"{name}")
        print(f'  integrity="{integrity}" crossorigin="anonymous"')
        print(f"  ({url})\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
