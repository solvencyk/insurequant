# -*- coding: utf-8 -*-
"""After reconverting KR0079/80/82/94/99/104 (FY2026_Q2), compare freshly
extracted items 36-40 against the current kics_disclosure.json master.

Reports, per (company, item): MATCH (extracted == master, within rounding),
MISMATCH (both present but differ -- patch candidate), NEW (master had no
value, extractor now supplies one -- patch candidate), STILL_MISSING
(extractor still can't find it after reconversion -- needs another pass).
Read-only; writes no master file."""
from __future__ import annotations
import glob
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(REPO / "scripts"))
import fill_market_subitems_to_disclosure as F  # noqa: E402

MD_DIR = REPO / "md_inbox" / "FY2026_Q2"
JSON_PATH = REPO / "kics_disclosure.json"
QUARTER = "2026.2Q"
TARGETS = ["KR0079", "KR0080", "KR0082", "KR0094", "KR0099", "KR0104"]


def main():
    rows = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    master = {}  # (code, item_no) -> raw string value
    for r in rows:
        if r.get("공시분기") != QUARTER:
            continue
        code = r["원보험사코드"]
        if code not in TARGETS:
            continue
        it = int(r["항목번호"])
        if 36 <= it <= 40:
            master[(code, it)] = str(r.get("값", ""))

    for code in TARGETS:
        g = sorted(glob.glob(str(MD_DIR / f"{code}_*.md")))
        if not g:
            print(f"{code}: NO_MD")
            continue
        text = Path(g[0]).read_text(encoding="utf-8")
        subs = F.extract_mkt_subs(text)
        print(f"\n{code}:")
        for item_no in (36, 37, 38, 39, 40):
            master_val = master.get((code, item_no))
            if item_no in subs:
                raw, unit = subs[item_no]
                extracted_eok = F._to_eok(raw, unit)
                if master_val is None:
                    status = "NEW (master had none)"
                else:
                    try:
                        diff = abs(float(extracted_eok) - float(master_val.replace(",", "")))
                        rel = diff / abs(float(master_val.replace(",", ""))) * 100 if float(master_val.replace(",", "")) != 0 else (0 if diff == 0 else 999)
                        status = "MATCH" if rel < 0.5 else f"MISMATCH (diff={diff:.2f}, rel={rel:.2f}%)"
                    except (ValueError, ZeroDivisionError):
                        status = f"MATCH" if extracted_eok == master_val else "MISMATCH (non-numeric compare)"
                print(f"  item{item_no}: extracted={extracted_eok} master={master_val!r} unit_raw={unit} -> {status}")
            else:
                print(f"  item{item_no}: extractor found nothing. master={master_val!r} -> {'STILL_MISSING' if master_val is None else 'MASTER_HAS_IT_EXTRACTOR_DOES_NOT'}")


if __name__ == "__main__":
    main()
