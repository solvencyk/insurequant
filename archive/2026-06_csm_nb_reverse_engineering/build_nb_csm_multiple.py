#!/usr/bin/env python3
"""Compute NB CSM multiple from real KIDI 월납초회+기타초회 premium (손보 + 생보).

multiple = 신계약 CSM (YTD) ÷ (월납초회 + 기타초회) (YTD, same quarter)

Numerator  : csm_waterfall_history.json new_business (YTD), csm_waterfall.json (FY).
Denominator: 손보 = kidi_longterm_premium.json first_premium_eok (월납+기타, N07);
             생보 = kidi_life_premium.json wolnap_etc_sum_eok (월납+기타, ML01).
일시납 초회 is EXCLUDED (생보 저축성 lump-sum would collapse the multiple; confirmed
by 삼성생명 FY2024 = 9.80 EXACT-matching IR Total 9.8).

Replaces the circular IR-back-solved premium (F2). Output: data/_derived/nb_csm_multiple.json
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIZ = ROOT / "data" / "dart" / "viz"
ASSOC = ROOT / "data" / "_derived"
IR = ROOT / "data" / "ir"
OUT_PATH = ASSOC / "nb_csm_multiple.json"

YM_TO_Q = {"03": "1Q", "06": "2Q", "09": "3Q", "12": "4Q"}

# KIDI short name -> (universe company name)
SONBO_MAP = {
    "삼성": "삼성화재해상보험", "현대": "현대해상", "메리츠": "메리츠화재해상보험",
    "DB": "DB손해보험", "KB": "KB손해보험", "농협": "NH농협손해보험",
    "한화": "한화손해보험", "롯데": "롯데손해보험", "흥국": "흥국화재", "하나": "하나손해보험",
}
LIFE_MAP = {
    "삼성": "삼성생명", "한화": "한화생명", "교보": "교보생명보험", "농협": "농협생명보험",
    "동양": "동양생명", "미래에셋": "미래에셋생명", "신한라이프": "신한라이프생명보험",
    "흥국": "흥국생명보험", "라이나": "라이나생명보험", "메트라이프": "메트라이프생명보험",
    "AIA": "에이아이에이생명보험", "ABL": "에이비엘생명보험", "KDB": "케이디비생명보험",
    "KB라이프": "케이비라이프생명보험", "푸본현대": "푸본현대생명보험", "하나": "하나생명보험",
    "DB": "DB생명보험", "ACE": "처브라이프생명보험",
}
# IR samsung_life key in nb_csm_ratio.json -> universe (for Total-series cross-check)
IR_KEY_MAP = {"samsung_life": "삼성생명", "hanwha_life": "한화생명",
              "samsung_fire": "삼성화재해상보험", "hyundai_marine": "현대해상",
              "db_insurance": "DB손해보험", "kb_insurance": "KB손해보험"}


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def ym_to_period(ym: str) -> str:
    return f"{ym[:4]}.{YM_TO_Q[ym[4:]]}"


def ir_total_series() -> dict[str, dict[str, float]]:
    """company -> {period 'YYYY.NQ' -> IR-disclosed Total multiple}."""
    path = IR / "nb_csm_ratio.json"
    if not path.exists():
        return {}
    data = load(path)
    out: dict[str, dict[str, float]] = {}
    for section in ("life", "non_life"):
        for key, entry in (data.get(section) or {}).items():
            uni = IR_KEY_MAP.get(key)
            if not uni:
                continue
            total = (entry.get("series") or {}).get("total")
            if not total:
                continue
            pts = {}
            for p in total.get("points") or []:
                per = p.get("period", "")  # e.g. 'FY24.4Q'
                val = p.get("value")
                if per.startswith("FY") and val is not None:
                    yr = "20" + per[2:4]
                    q = per.split(".")[-1]
                    pts[f"{yr}.{q}"] = float(val)
            if pts:
                out[uni] = pts
    return out


def build_sector(prem_records: dict, name_map: dict, den_of, hist: dict,
                 fy: dict, sector: str, ir_totals: dict) -> list[dict]:
    """den_of(rec) -> 월납초회 ONLY denominator in 억원 (월납월초; 기타·일시납 제외).

    The denominator is 월납 초회보험료 only — confirmed by 삼성생명's directly
    disclosed FY2025 신계약 배수 = 11.0 (= 30,595억 ÷ 2,789억 월납초회). Adding
    기타초회 understated the multiple (9.8) by matching a derived/circular IR total.
    """
    out = []
    for kidi, uni in name_map.items():
        periods_map = (hist.get(uni) or {}).get("periods", {})
        ir_pts = ir_totals.get(uni, {})
        series: dict[str, dict] = {}
        for k, rec in sorted(
            ((kk.split("|")[1], vv) for kk, vv in prem_records.items()
             if vv["company_kidi"] == kidi)
        ):
            per = ym_to_period(k)
            snap = periods_map.get(per) or {}
            nb_mn = ((snap.get("stages") or {}).get("new_business") or {}).get("value_mn_krw")
            den = den_of(rec)
            if nb_mn is None or not den:
                continue
            nb_eok = abs(nb_mn) / 100.0
            row = {
                "nb_csm_eok": round(nb_eok, 1),
                "wolnap_chowoe_eok": round(den, 1),
                "multiple": round(nb_eok / den, 2),
            }
            if per in ir_pts:
                row["ir_total_multiple"] = ir_pts[per]
            series[per] = row
        # FY2024 snapshot
        fy_snapshot = None
        fy_rec = prem_records.get(f"{kidi}|202412")
        fy_nb = ((fy.get(uni, {}).get("stages") or {}).get("new_business") or {}).get("value_mn_krw")
        if fy_rec and fy_nb is not None and den_of(fy_rec):
            nb_eok = abs(fy_nb) / 100.0
            fy_snapshot = {
                "period": "FY2024",
                "nb_csm_eok": round(nb_eok, 1),
                "wolnap_chowoe_eok": round(den_of(fy_rec), 1),
                "multiple": round(nb_eok / den_of(fy_rec), 2),
                "ir_total_multiple": ir_pts.get("2024.4Q"),
            }
        if series or fy_snapshot:
            out.append({
                "company": uni, "kidi_name": kidi, "sector": sector,
                "fy2024": fy_snapshot, "series": series,
            })
    return out


def main() -> int:
    hist = {c["company"]: c for c in load(VIZ / "csm_waterfall_history.json")["companies"]}
    fy = {c["company"]: c for c in load(VIZ / "csm_waterfall.json")["companies"]}
    ir_totals = ir_total_series()

    # Sector-specific denominators, each matching that sector's IR footnote:
    #  손보 = 월납환산 = 월납초회 + 기타초회 (일시납≈0). 삼성화재 footnote "월납환산";
    #         disclosed 환산배수 3Q25=14.9 vs computed 14.8.
    #  생보 = 월납월초 = 월납초회 only (일시납 저축성·기타 제외). 삼성생명 footnote
    #         "월납월초"; disclosed FY2025 배수 11 vs computed 10.9.
    def son_den(rec):
        return rec.get("first_premium_eok")        # 월납 + 기타 (월납환산)

    def life_den(rec):
        return rec.get("wolnap_chowoe_eok")         # 월납 only (월납월초)

    companies: list[dict] = []
    son_path = ASSOC / "kidi_longterm_premium.json"
    if son_path.exists():
        companies += build_sector(load(son_path)["records"], SONBO_MAP,
                                  son_den, hist, fy, "Non-Life", ir_totals)
    life_path = ASSOC / "kidi_life_premium.json"
    if life_path.exists():
        companies += build_sector(load(life_path)["records"], LIFE_MAP,
                                  life_den, hist, fy, "Life", ir_totals)
    companies.sort(key=lambda c: (c["sector"], c["company"]))

    payload = {
        "_meta": {
            "definition": "NB CSM multiple = 신계약 CSM ÷ (월납초회 + 기타초회), YTD-matched, 일시납 제외",
            "numerator": "csm_waterfall(_history) new_business CSM (억원)",
            "denominator_sonbo": "KIDI 장기보험 원수보험료 N07 월납+기타초회",
            "denominator_life": "KIDI 수입보험료 명세표 ML01 월납+기타초회 (일시납 제외)",
            "validation": "삼성생명 FY2024=9.80 vs IR Total 9.8 (exact); 손보 삼성화재/메리츠/DB ±5%",
            "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "build_script": "scripts/build_nb_csm_multiple.py",
            "company_count": len(companies),
        },
        "companies": companies,
    }
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT_PATH}  ({len(companies)} companies)")
    for sec in ("Life", "Non-Life"):
        print(f"\n=== {sec} FY2024 ===")
        for c in companies:
            if c["sector"] != sec or not c.get("fy2024"):
                continue
            s = c["fy2024"]
            ir = s.get("ir_total_multiple")
            tag = f"  vs IR Total {ir} ({(s['multiple']-ir)/ir*100:+.0f}%)" if ir else ""
            print(f"  {c['company']:18} {s['multiple']:6.1f}x{tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
