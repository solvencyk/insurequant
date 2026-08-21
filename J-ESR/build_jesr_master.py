# -*- coding: utf-8 -*-
"""Build J-ESR data layer J-ESR/jesr_master.json from downloader's collected
headline ESR (jesr_sources_2026Q1.csv). Strict as-of flags, unit normalization,
provenance, and a universal-math structure validator (no hand-gold).

NEW jesr lane — independent of kics/ifrs17. Output: J-ESR/ only.
Owner spec: inbox/parser/20260624T0337Z. Usage: python J-ESR/build_jesr_master.py
"""
from __future__ import annotations
import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
SRC = HERE / "jesr_sources_2026Q1.csv"
OUT = HERE / "jesr_master.json"
AS_OF_TARGET = "2026-03-31"
# 相互会社 (mutual companies) — non-listed, no EDINET, IR PDF only
MUTUAL = {"日本生命保険", "住友生命保険", "明治安田生命保険", "富国生命保険"}


def _f(s):
    if s is None:
        return None
    s = str(s).strip().replace(",", "")
    if s in ("", "-", "—", "?"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _canon(n):
    if n is None:
        return None
    return int(round(n)) if abs(n - round(n)) < 1e-9 else round(n, 4)


def main() -> int:
    with SRC.open(encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))

    records, undisclosed = [], []
    for r in rows:
        esr = _f(r.get("esr_pct"))
        as_of = (r.get("as_of") or "").strip()
        # unit normalize: 総資産 兆円 -> 億円 (x1e4); 所要/適格 十億円(bn) -> 億円 (x10)
        tot_tn = _f(r.get("総資産_tn_jpy"))
        req_bn = _f(r.get("所要資本_bn_jpy"))
        elig_bn = _f(r.get("適格資本_bn_jpy"))
        rec = {
            "company_jp": r.get("company_jp", "").strip(),
            "company_en": r.get("company_en", "").strip(),
            "ticker": (r.get("ticker") or "").strip() or None,
            "entity_type": "mutual" if r.get("company_jp", "").strip() in MUTUAL else "group",
            "esr_pct": _canon(esr),
            "esr_basis": "新J-ICS",   # all values are economic-value ESR (not 旧SMR)
            "esr_basis_raw": (r.get("esr_basis") or "").strip(),
            "as_of": as_of or None,
            "as_of_consistent": (as_of == AS_OF_TARGET),
            "所要資本_억엔": _canon(req_bn * 10) if req_bn is not None else None,
            "적격자본_억엔": _canon(elig_bn * 10) if elig_bn is not None else None,
            "총자산_억엔": _canon(tot_tn * 1e4) if tot_tn is not None else None,
            "단위": "억엔",
            "target_pct": (r.get("target_pct") or "").strip() or None,
            "yoy_change_pp": _canon(_f(r.get("yoy_change_pp"))),  # signed; △ at display
            "provenance": {
                "source_url": (r.get("source_url") or "").strip() or None,
                "doc": (r.get("doc_type") or "").strip() or None,
                "doc_date": (r.get("doc_date") or "").strip() or None,
                "page": None,
            },
            "notes": (r.get("notes") or "").strip() or None,
        }
        if esr is None:
            rec["status"] = "not_yet_disclosed"
            undisclosed.append(rec["company_jp"])
        records.append(rec)

    # ---- structure validator (universal math, no hand-gold) ----
    checks = {"plausible_range": [], "component_identity": [], "census": {}}
    for rec in records:
        e = rec["esr_pct"]
        if e is None:
            continue
        if not (100 <= e <= 400):
            checks["plausible_range"].append(
                {"company": rec["company_jp"], "esr_pct": e, "flag": "OUT_OF_RANGE"})
        req, elig = rec["所要資本_억엔"], rec["적격자본_억엔"]
        if req and elig:
            implied = elig / req * 100
            ok = abs(implied - e) <= max(2.0, e * 0.02)
            checks["component_identity"].append(
                {"company": rec["company_jp"], "implied": round(implied, 2),
                 "reported": e, "ok": ok})
    valued = [r for r in records if r["esr_pct"] is not None]
    checks["census"] = {
        "downloader_collected": len(rows),
        "master_records": len(records),
        "with_esr_value": len(valued),
        "as_of_consistent(2026-03-31)": sum(1 for r in valued if r["as_of_consistent"]),
        "prior_period(flagged false)": sum(1 for r in valued if not r["as_of_consistent"]),
        "not_yet_disclosed": undisclosed,
        "component_identity_runnable": bool(checks["component_identity"]),
    }

    out = {
        "_meta": {
            "lane": "jesr", "track": "J-ESR", "period": "2026.1Q",
            "as_of_target": AS_OF_TARGET, "unit": "억엔 (1兆=10000억, 1bn=10억)",
            "source": "downloader inbox/parser/20260624T0200Z (jesr_sources_2026Q1.csv)",
            "validator": checks,
            "supplemental_not_checked": ["大同生命", "太陽生命", "ライフネット生命"],
            "note": "데이터레이어 전용 — as-of 혼재(2025.3~2026.3). 비교 viz 금지, "
                    "designer가 as_of_consistent로 분리. △는 표시레이어(designer).",
        },
        "records": records,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}  ({len(records)} records, {len(valued)} with ESR, "
          f"{len(undisclosed)} not_yet_disclosed)")
    print(f"  as_of_consistent={checks['census']['as_of_consistent(2026-03-31)']}, "
          f"prior_period={checks['census']['prior_period(flagged false)']}")
    print(f"  plausible_range flags: {len(checks['plausible_range'])}  "
          f"component_identity runnable: {checks['census']['component_identity_runnable']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
