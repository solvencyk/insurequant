# -*- coding: utf-8 -*-
"""Fallback raw-fetch when DART's document.xml API returns status:014 but the filing is
already visible on the DART web viewer (dsaf001/main.do) -- confirmed 2026-08-15 for the
2026.2Q batch that filed on the legal deadline (21 companies at once, API export pipeline
stuck 24h+ while the web-facing viewer already renders full content).

Mechanism (reverse-engineered from network inspection, no auth/session needed for either
call):
  1. GET dsaf001/main.do?rcpNo=<rcept> -- the shell page embeds the FULL document tree
     as inline JS (`node3['eleId']/['offset']/['length']/['dcmNo']` object literals), one
     per section.
  2. GET report/viewer.do?rcpNo=&dcmNo=&eleId=&offset=&length=&dtd= for each node --
     returns that section's HTML fragment (same report_xml.css styling DART's real
     document.xml content uses).
  3. Concatenate all fragments, zip as `<rcept>.xml` inside `document.zip` -- matches the
     exact member-naming convention of a normal DART document.xml fetch, so the existing
     `extract_dart_zips.py` / parser's `*.xml` glob picks it up with zero changes on
     parser's side.

Writes a `meta.json` sidecar with `"source": "viewer_fallback"` so this is traceable and
distinguishable from a normal API fetch (owner instruction: never silently blur provenance).
Does NOT touch the real document.xml retry path (scout_2026q2_halfyear.py) -- this is an
independent, additive route for the same canonical raw location.
"""
from __future__ import annotations

import json
import re
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://dart.fss.or.kr"
# The tree JS uses a DIFFERENT variable name per nesting depth (node1/node2/node3/...) --
# a company whose notes fit in one big node2 chunk (no node3 children) was silently
# undershot when this only matched `node3` (found empirically: NH농협손해보험's "5. 재무제표
# 주석" is a single 760KB node2 leaf, while 삼성생명's notes are ~30 small node3 leaves under
# a near-empty node2 stub). Match any nodeN and dedupe by id so every leaf-sized chunk is
# caught regardless of which depth it lives at.
NODE_RE = re.compile(
    r"node\d+\['text'\]\s*=\s*\"(?P<text>[^\"]*)\";\s*"
    r"node\d+\['id'\]\s*=\s*\"(?P<id>[^\"]*)\";\s*"
    r"node\d+\['rcpNo'\]\s*=\s*\"(?P<rcpNo>[^\"]*)\";\s*"
    r"node\d+\['dcmNo'\]\s*=\s*\"(?P<dcmNo>[^\"]*)\";\s*"
    r"node\d+\['eleId'\]\s*=\s*\"(?P<eleId>[^\"]*)\";\s*"
    r"node\d+\['offset'\]\s*=\s*\"(?P<offset>[^\"]*)\";\s*"
    r"node\d+\['length'\]\s*=\s*\"(?P<length>[^\"]*)\";\s*"
    r"node\d+\['dtd'\]\s*=\s*\"(?P<dtd>[^\"]*)\";",
)
KEYWORDS = ["보험계약마진", "보험료배분접근법", "신계약", "보험손익"]
BODY_RE = re.compile(r"<BODY[^>]*>(.*?)</BODY>", re.I | re.S)


def _get_with_retry(url: str, params: dict, timeout: int, attempts: int = 3) -> requests.Response:
    last_exc = None
    for i in range(attempts):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            r.encoding = "utf-8"
            return r
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_exc = exc
            time.sleep(2.0 * (i + 1))
    raise last_exc  # noqa: B904


def _select_leaf_nodes(candidates: list[dict]) -> list[dict]:
    """Drop any node whose (offset, offset+length) range fully contains another node's
    range. A parent-level tree entry (e.g. "3. 연결재무제표 주석") sometimes carries the
    SAME underlying byte range as the sum of its ~30 numbered children -- fetching both
    means the whole notes section twice. Containment on the numeric range is a tree-
    structure-agnostic way to detect this (confirmed empirically: 삼성생명's parent note
    node contains all its node3 children's ranges; a company with no sub-items, e.g.
    NH농협손해보험's undivided notes blob, contains nothing and survives as a leaf)."""
    spans = [(n, int(n["offset"]), int(n["offset"]) + int(n["length"])) for n in candidates]
    leaves = []
    for n, start, end in spans:
        contains_another = any(
            (n2["id"] != n["id"]) and start <= start2 and end2 <= end and (start2, end2) != (start, end)
            for n2, start2, end2 in spans
        )
        if not contains_another:
            leaves.append(n)
    return leaves


def fetch_full_document(rcept: str) -> tuple[str, int]:
    r = _get_with_retry(f"{BASE}/dsaf001/main.do", {"rcpNo": rcept}, timeout=20)
    all_nodes = [m.groupdict() for m in NODE_RE.finditer(r.text)]
    if not all_nodes:
        raise RuntimeError(f"no tree nodes found in viewer shell for rcept {rcept}")
    # dedupe by id, skip zero/near-zero-length header stubs (real content lives elsewhere
    # in the tree for those -- e.g. a 206-byte "3. 연결재무제표 주석" placeholder whose actual
    # 760KB of content sits under a sibling/child id)
    by_id: dict[str, dict] = {}
    for n in all_nodes:
        if int(n["length"]) < 50:
            continue
        by_id[n["id"]] = n
    nodes = sorted(_select_leaf_nodes(list(by_id.values())), key=lambda n: int(n["id"]))
    fragments = []
    for n in nodes:
        params = {
            "rcpNo": n["rcpNo"], "dcmNo": n["dcmNo"], "eleId": n["eleId"],
            "offset": n["offset"], "length": n["length"], "dtd": n["dtd"],
        }
        resp = _get_with_retry(f"{BASE}/report/viewer.do", params, timeout=25)
        # Each viewer.do response is a COMPLETE standalone <!DOCTYPE><HTML>...</HTML>
        # document (meant for iframe embedding in the live viewer), not a bare fragment.
        # Concatenating those as-is produces N sibling documents in one file, which a
        # real HTML parser only reads the first of (confirmed the hard way: parser bounce
        # inbox/downloader/20260815T0230Z, lxml "Misplaced DOCTYPE" on document #2 onward,
        # only the cover page's 4 tables survived). Keep just the <BODY> inner content so
        # the final concatenation is genuinely one well-formed document.
        body_match = BODY_RE.search(resp.text)
        inner = body_match.group(1) if body_match else resp.text
        fragments.append(f"<!-- ===== {n['id']}: {n['text']} ===== -->\n" + inner)
        time.sleep(0.15)
    full_body = "\n".join(fragments)
    single_doc = (
        "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.01 Transitional//EN\" "
        "\"http://www.w3.org/TR/html4/loose.dtd\">\n"
        "<HTML><HEAD><META http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">"
        "</HEAD><BODY>\n" + full_body + "\n</BODY></HTML>"
    )
    return single_doc, len(nodes)


def write_canonical(kr: str, canonical: str, rcept: str, full_text: str, period_dir: Path) -> Path:
    out_dir = period_dir / f"{kr}_{canonical}"
    out_dir.mkdir(parents=True, exist_ok=True)
    zpath = out_dir / "document.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{rcept}.xml", full_text.encode("utf-8"))
    meta = {
        "rcept_no": rcept,
        "source": "viewer_fallback",
        "fetched_at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "note": "document.xml API returned status:014 for 24h+; fetched via dsaf001/main.do "
                "+ report/viewer.do reconstruction instead (inbox/downloader/20260814T0149Z).",
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return zpath


TARGETS = [
    ("KR0005", "00103176", "흥국화재", "20260814003618"),
    ("KR0008", "00139214", "삼성화재해상보험", "20260814003992"),
    ("KR0009", "00164973", "현대해상", "20260814003474"),
    ("KR0011", "00159102", "DB손해보험", "20260814003682"),
    ("KR0032", "00908155", "NH농협손해보험", "20260814003298"),
    ("KR0069", "00126256", "삼성생명", "20260814003263"),
    ("KR0070", "00148391", "에이비엘생명보험", "20260814003770"),
    ("KR0071", "00167068", "흥국생명보험", "20260814003688"),
    ("KR0073", "00112882", "교보생명보험", "20260814004024"),
    ("KR0079", "00112332", "미래에셋생명", "20260814004054"),
    ("KR0083", "00459844", "푸본현대생명보험", "20260814004204"),
    ("KR0087", "00117267", "동양생명", "20260814003397"),
    ("KR0099", "00160393", "케이비라이프생명보험", "20260814003260"),
    ("KR1000", "00113191", "코리안리", "20260814003862"),
]


def main() -> int:
    period_dir = REPO / "data" / "dart" / "FY2026_Q2" / "raw"
    results = []
    for kr, cc, canonical, rcept in TARGETS:
        try:
            full_text, n_sections = fetch_full_document(rcept)
            zpath = write_canonical(kr, canonical, rcept, full_text, period_dir)
            counts = {kw: full_text.count(kw) for kw in KEYWORDS}
            ok = any(v > 0 for v in counts.values())
            results.append({"kr": kr, "canonical": canonical, "rcept": rcept,
                             "sections": n_sections, "chars": len(full_text),
                             "keyword_counts": counts, "ok": ok})
            print(f"{kr} {canonical}: {n_sections} sections, {len(full_text)} chars, "
                  f"keywords={counts} -> {zpath}")
        except Exception as exc:  # noqa: BLE001
            results.append({"kr": kr, "canonical": canonical, "rcept": rcept, "error": str(exc)})
            print(f"{kr} {canonical}: FAILED - {exc}")

    out = REPO / "data" / "_derived" / "viewer_fallback_2026q2_census.json"
    out.write_text(json.dumps({
        "fetched_at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "results": results,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    ok_count = sum(1 for r in results if r.get("ok"))
    print(f"\n=== {ok_count}/{len(results)} succeeded with keyword hits. census: {out} ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
