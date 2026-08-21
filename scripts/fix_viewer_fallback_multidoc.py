# -*- coding: utf-8 -*-
"""One-off repair for the viewer-fallback multi-document-concatenation bug
(inbox/downloader/20260815T0230Z, parser bounce). fetch_dart_viewer_fallback.py joined
each section's FULL <!DOCTYPE><HTML>...</HTML> response as-is instead of stripping the
wrapper, so the 14 saved zips each contain N complete sibling HTML documents -- any real
parser (lxml included) only reads the first one.

Repacks IN PLACE from the already-saved raw (no re-fetch from DART): split on the
`<!-- ===== id: text ===== -->` section markers already embedded by the original script,
extract each fragment's <BODY> inner content, and re-wrap the concatenation in a single
clean document. Then re-zips as the same `<rcept>.xml` member name (no path/naming
change, so parser's existing raw-ready pointers stay valid).
"""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

REPO = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
sys.stdout.reconfigure(encoding="utf-8")

MARKER_RE = re.compile(r"<!-- ===== (\d+): ([^=]*?) ===== -->\n")
BODY_RE = re.compile(r"<BODY[^>]*>(.*?)</BODY>", re.I | re.S)

TARGETS = [
    ("KR0005", "흥국화재"), ("KR0008", "삼성화재해상보험"), ("KR0009", "현대해상"),
    ("KR0011", "DB손해보험"), ("KR0032", "NH농협손해보험"), ("KR0069", "삼성생명"),
    ("KR0070", "에이비엘생명보험"), ("KR0071", "흥국생명보험"), ("KR0073", "교보생명보험"),
    ("KR0079", "미래에셋생명"), ("KR0083", "푸본현대생명보험"), ("KR0087", "동양생명"),
    ("KR0099", "케이비라이프생명보험"), ("KR1000", "코리안리"),
]


def repack_one(kr: str, canonical: str) -> dict:
    out_dir = REPO / "data" / "dart" / "FY2026_Q2" / "raw" / f"{kr}_{canonical}"
    zpath = out_dir / "document.zip"
    with zipfile.ZipFile(zpath) as z:
        member = z.namelist()[0]
        raw = z.read(member).decode("utf-8")

    parts = MARKER_RE.split(raw)
    # split() on a 2-group pattern yields [pre, id, title, chunk, id, title, chunk, ...]
    bodies = []
    n_sections = 0
    n_body_found = 0
    for i in range(1, len(parts), 3):
        sid, title, chunk = parts[i], parts[i + 1], parts[i + 2]
        n_sections += 1
        m = BODY_RE.search(chunk)
        if m:
            n_body_found += 1
            bodies.append(f"<!-- ===== {sid}: {title} ===== -->\n{m.group(1)}")
        else:
            # no BODY tag found (shouldn't happen given the source pattern, but don't
            # silently drop content if it does -- keep the raw chunk minus any DOCTYPE/
            # HTML/HEAD open tags as a fallback)
            bodies.append(f"<!-- ===== {sid}: {title} (no BODY match, raw kept) ===== -->\n{chunk}")

    full_body = "\n".join(bodies)
    single_doc = (
        "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.01 Transitional//EN\" "
        "\"http://www.w3.org/TR/html4/loose.dtd\">\n"
        "<HTML><HEAD><META http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">"
        "</HEAD><BODY>\n" + full_body + "\n</BODY></HTML>"
    )

    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(member, single_doc.encode("utf-8"))

    return {"kr": kr, "canonical": canonical, "sections": n_sections,
            "body_matched": n_body_found, "final_chars": len(single_doc)}


def verify_one(kr: str, canonical: str) -> dict:
    import lxml.etree as ET
    zpath = REPO / "data" / "dart" / "FY2026_Q2" / "raw" / f"{kr}_{canonical}" / "document.zip"
    with zipfile.ZipFile(zpath) as z:
        content = z.read(z.namelist()[0])
    errors = []
    parser = ET.HTMLParser(recover=True)
    tree = ET.fromstring(content, parser=parser)
    for e in parser.error_log:
        if "Misplaced DOCTYPE" in str(e) or "expected '>'" in str(e):
            errors.append(str(e))
    n_tables = len(tree.findall(".//table")) if tree is not None else 0
    n_csm = content.decode("utf-8", "ignore").count("보험계약마진")
    return {"misplaced_doctype_errors": len(errors), "tables_found": n_tables, "csm_keyword_count": n_csm}


def main() -> int:
    for kr, canonical in TARGETS:
        r = repack_one(kr, canonical)
        v = verify_one(kr, canonical)
        print(f"{kr} {canonical}: sections={r['sections']} body_matched={r['body_matched']} "
              f"chars={r['final_chars']} | verify: doctype_errors={v['misplaced_doctype_errors']} "
              f"tables={v['tables_found']} csm_kw={v['csm_keyword_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
