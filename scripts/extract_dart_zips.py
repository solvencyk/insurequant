# -*- coding: utf-8 -*-
"""Extract DART document.zip into body XML where extraction never ran.

Background
----------
Most DART fetch/batch scripts extractall() the downloaded ``document.zip`` next
to it (or into an ``xml/`` subdir). A subset of filings were left at the
fetch-only stage: the dir holds only ``document.zip`` and no body XML, so the
parser reports ``status=raw_not_extracted`` and can pull no CSM/PL.

Two reasons combine for the affected (mostly non-listed / foreign) insurers:
  1. The dir was created fetch-only (e.g. --skip-extract, or a never-extracted
     dir relocated by Reorg #2), so extractall() never ran.
  2. Their filing is a standalone 감사보고서 whose zip contains ONLY the
     sub-documents ``<rcept>_00760.xml`` (연결) / ``<rcept>_00761.xml`` (별도) and
     NO main ``<rcept>.xml`` body. Any check globbing for the main xml therefore
     also treated the dir as empty.

The IFRS17 disclosures (보험계약마진 / 포괄손익 / 부문) live INSIDE document.zip in
those _0076x members, so this is a pure local-extraction fix -- no re-download,
no separate 별첨/감사보고서 zip fetch.

Behaviour
---------
Idempotent. For every ``data/dart/FY*_Q*/raw/*/document.zip``:
  - if the dir already has any ``*.xml`` / ``xml/*.xml`` / ``extracted*/*.xml``
    -> skip (already extracted).
  - else extractall() all members in-place next to document.zip (matches the
    dominant good-dir layout, e.g. KR0001 메리츠), so the parser's *.xml glob
    catches them.

Scope
-----
By default only insurer dirs are touched -- dir name starts with an insurer
prefix (``KR`` universe code or the ``AIA`` alias). Financial-holding-company
filings (지주, corp_code-prefixed e.g. ``00382199_신한지주``) are NOT insurers and
are skipped; pass --include-all to extract those too.

Usage
-----
  python scripts/extract_dart_zips.py            # extract missing insurer dirs
  python scripts/extract_dart_zips.py --dry-run  # report only, change nothing
  python scripts/extract_dart_zips.py --include-all  # also non-insurer (지주) dirs
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

DART_ROOT = ROOT / "data" / "dart"

# Insurer dir prefixes: KR#### universe codes + the AIA alias (AIA생명 was saved
# under "AIA_" rather than its KR0080 code). Anything else (e.g. corp_code-
# prefixed 지주 holding companies) is not an insurer the parser tracks.
INSURER_PREFIXES = ("KR", "AIA")


def is_insurer_dir(d: Path) -> bool:
    return d.name.startswith(INSURER_PREFIXES)


def has_xml(d: Path) -> bool:
    """True if the dir already exposes body XML the parser would find."""
    return bool(
        list(d.glob("*.xml"))
        or list(d.glob("xml/*.xml"))
        or list(d.glob("extracted*/*.xml"))
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would be extracted, change nothing")
    ap.add_argument("--include-all", action="store_true",
                    help="also extract non-insurer (지주 corp_code) dirs")
    args = ap.parse_args()

    zips = sorted(DART_ROOT.glob("FY*_Q*/raw/*/document.zip"))
    extracted, skipped, skipped_noninsurer, bad, members_total = [], 0, 0, [], 0

    for zp in zips:
        d = zp.parent
        if not args.include_all and not is_insurer_dir(d):
            skipped_noninsurer += 1
            continue
        if has_xml(d):
            skipped += 1
            continue
        try:
            with zipfile.ZipFile(zp) as zf:
                names = zf.namelist()
                if not args.dry_run:
                    zf.extractall(d)
        except zipfile.BadZipFile as exc:
            bad.append((str(d.relative_to(ROOT)), str(exc)))
            continue
        members_total += len(names)
        extracted.append((str(d.relative_to(ROOT)), names))

    print("=" * 72)
    print(f"DART zip extraction  ({'DRY-RUN' if args.dry_run else 'APPLIED'})")
    print("=" * 72)
    print(f"  scanned document.zip : {len(zips)}")
    print(f"  skipped non-insurer  : {skipped_noninsurer}  (지주 etc.; use --include-all)")
    print(f"  already had xml      : {skipped}")
    print(f"  extracted now        : {len(extracted)}  ({members_total} xml members)")
    print(f"  bad/corrupt zip      : {len(bad)}")
    if extracted:
        print("\n  --- extracted dirs ---")
        for rel, names in extracted:
            print(f"   {rel}")
            for n in names:
                print(f"        + {n}")
    if bad:
        print("\n  --- BAD ZIPS (need re-download) ---")
        for rel, err in bad:
            print(f"   {rel}: {err}")


if __name__ == "__main__":
    main()
