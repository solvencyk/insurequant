# -*- coding: utf-8 -*-
"""자본증권 인정한도 소진율(기본자본·보완자본)을 경영공시 항목에서 **규정 근거 산식**으로 산출해
배포본 `kics_tier{1,2}_utilization.json` 과 빌더 산출물 `output/tier{1,2}_utilization/*` 에 쓴다.

## 2026-10-12 재정의 (owner 채택 — 결정 ①~⑦)

정본 근거 `data/_derived/capital_utilization_definition_20261012/definition_memo.md`(보험업감독업무시행세칙
[별표22] Ⅲ.2.다·마, Ⅵ.1.가·라). 산식 자체는 `scripts/capital_utilization_rules.py` 에 있고 이 스크립트는
그 결과를 행 필드로 옮기기만 한다.

    보완자본 소진율 = 보완자본 한도 적용 전 / (총요구자본(항목 14, 경과조치 적용 전) x 50%)
        보완자본 한도 적용 전 = 보완자본 - 해약환급금 부족분 상당액 중 해약환급금준비금 상당액 초과분
                                 - 기발행 자본증권(공통적용 경과조치)
        = 경과조치 표 「보완자본 한도 적용 전」 적용 후 열 + 발행사 인쇄 관행 정규화 R0~R5 (행의 `rule`)
        항목 47~54 원문 부재 -> 값 null + reason "경과조치 표 미공시"
    기본자본 소진율 = max( 기발행 신종(항목 53) / (항목 14 x 15%) ,
                           기본자본형 신규(항목 6 - 기발행 - 보완자본형) / (항목 14 x 10%) )
        보완자본형 판정은 증권별 계층 등재부 `data/bonds/capital_tier_registry.json`

종전(2026-09-01) 산식과 달라진 점: 보완자본은 적용 **전** 열(값)을 그대로 나눠 기발행분이 한도 대상에
섞였고(14사), 발행사가 「한도 적용 전」 행에 보완자본 총액을 찍은 5사는 해약환급금 초과분까지 나눴다.
기본자본은 항목 6 전체(보완자본형 신종 포함)를 SCR x 15% 로 나눴다.

## 2026-09-01 결정 중 유지되는 것

분자·분모 모두 같은 분기말 경영공시 항목이라 기준일이 어긋나지 않는다. 분모는 공시 항목 48 이 아니라
조문식(항목 14 x 50%)으로 세운다(항목 48 파싱 결함이 소진율로 새지 않게). 채권 단위 데이터
(`kics_capital_securities.json`)는 화면 참고 줄(발행잔액)과 forward outlook 에만 쓴다.

## 배포본·빌더 산출물 둘 다 쓴다

배포본만 고치면 `validate_live_artifacts` 가 "배포본 != 빌더 산출물"(TIER_DEPLOYED_VALUE_DIFFERS)로
RED 를 낸다. 같은 값을 두 곳에 쓴다(불변식 1번).

## securities_summary (2026-10-12, 소진율 도넛 밑 신종·후순위 큰 셀)

두 파일의 회사 행 모두에 같은 값으로 `securities_summary` 를 더한다(최근 발행금리·2023년 이후 총발행액·가장 가까운
콜). 값 정의는 `scripts/capital_securities_summary.py` 머리말이 정본이고, 입력은 소진율 분자(경영공시 항목)가 아니라
`data/bonds/capital_securities_fy2026h1.json` 의 증권 단위 자료다(발행금리·콜일은 경영공시에 없다).

기존 필드 이름·구조는 그대로 두고 새 필드만 더한다(구판 HTML 이 깨지지 않게). 화면·게이트가 읽는
`utilization_pct`·`tier1_hybrid_recognized_eok`·`tier1_hybrid_limit_eok`(결속 한도 쪽)·`numerator_eok`·
`tier2_limit_eok` 는 새 산식 값이다.

실행:
  python scripts/apply_disclosure_utilization.py --quarter 2026.2Q [--dry-run]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import capital_utilization_rules as R  # noqa: E402
import capital_securities_summary as SUM  # noqa: E402
from add_reinsurers_to_capsec_panels import REINSURER_NOTES  # noqa: E402

KICS = ROOT / "kics_disclosure.json"
T1F = ROOT / "kics_tier1_utilization.json"
T2F = ROOT / "kics_tier2_utilization.json"
OUT_T1 = ROOT / "output" / "tier1_utilization"
OUT_T2 = ROOT / "output" / "tier2_utilization"
_QEND = {"1Q": (3, 31), "2Q": (6, 30), "3Q": (9, 30), "4Q": (12, 31)}

T1_DATA_SOURCE = ("kics_disclosure max(item53 / (item14 x 15%), 기본자본형 신규 / (item14 x 10%)) "
                  "· data/bonds/capital_tier_registry.json")


def _r2(v):
    return None if v is None else round(v, 2)


def _type_note(entry: dict, t1: dict) -> str | None:
    """화면 ? 팝오버·xlsx 비고용 한 줄 근거 - 미확정이면 사유를 붙인다."""
    note = entry.get("note")
    if not t1.get("type_unconfirmed"):
        return note
    reasons = [s.get("unconfirmed_reason") for s in entry.get("securities") or [] if s.get("type_unconfirmed")]
    head = "기본자본형/보완자본형 미확정 - 기본자본형으로 보고 상한(분모 10%) 계산."
    return " ".join(x for x in [head, note, reasons[0] if reasons else None] if x)


def apply_tier1(row: dict, res: dict, registry: dict, ledger_entry: dict, as_of: str) -> None:
    t1 = res["t1"]
    code = row["code"]
    row["tier1_hybrid_issued_eok"] = t1["securities_eok"]
    # 화면 숫자 줄 "기본자본 자본증권 X / 인정한도 Y" 와 게이트 항등식(recognized / limit x 100 ==
    # utilization_pct)은 **결속하는 한도 쪽**의 분자·분모다(두 한도 중 먼저 차는 쪽).
    row["tier1_hybrid_recognized_eok"] = t1["binding_numerator_eok"]
    row["tier1_hybrid_limit_eok"] = t1["binding_limit_eok"]
    row["tier1_hybrid_limit_strict_eok"] = t1["basic_new_limit_eok"]
    row["tier1_hybrid_overflow_eok"] = t1["overflow_eok"]
    row["utilization_pct"] = t1["pct"]
    row["utilization_pct_strict"] = t1["basic_new_pct"]
    if res.get("item53") is not None:
        row["tier1_grandfathered_hybrid_eok"] = res["item53"]
    row["numerator_as_of"] = as_of
    row["data_source"] = T1_DATA_SOURCE
    row["issued_source"] = "disclosure_item6"
    row["hybrid_outstanding_eok"] = round(ledger_entry.get("hybrid", 0.0), 1)
    row["subordinated_outstanding_eok"] = round(ledger_entry.get("sub", 0.0), 1)
    row["bond_balance_as_of"] = ledger_entry.get("as_of")
    # --- 2026-10-12 새 필드(결속 시험의 두 다리 + 판정 근거) ---
    entry = R.registry_entry(registry, code)
    row["tier1_legacy_eok"] = t1["legacy_eok"]
    row["tier1_legacy_limit_eok"] = t1["legacy_limit_eok"]
    row["tier1_legacy_pct"] = t1["legacy_pct"]
    row["tier1_basic_new_eok"] = t1["basic_new_eok"]
    row["tier1_basic_new_limit_eok"] = t1["basic_new_limit_eok"]
    row["tier1_basic_new_pct"] = t1["basic_new_pct"]
    row["tier1_excluded_tier2_type_eok"] = t1["excluded_tier2_type_eok"]
    row["binding_leg"] = t1["binding_leg"]
    row["type_unconfirmed"] = t1["type_unconfirmed"]
    row["tier1_pct_if_unconfirmed_tier2"] = t1["pct_if_unconfirmed_tier2"]
    row["type_note"] = _type_note(entry, t1)
    row["no_capital_securities"] = res["no_capital_securities"]


def apply_tier2(row: dict, res: dict, ledger_entry: dict, as_of: str) -> None:
    t2 = res["t2"]
    na = t2["rule"] == "NA"
    row["tier2_limit_eok"] = t2["limit"]
    row["numerator_eok"] = t2["numerator"]
    row["utilization_pct"] = t2["pct"]
    if na:
        row["data_source"] = f"kics_disclosure item47 부재 - {R.REASON_NO_TFI_TABLE}"
        row["quality_flag"] = "tfi_table_absent"
    else:
        row["data_source"] = f"kics_disclosure item47 규정 정규화 {t2['rule']} / (item14 x 50%)"
        if row.get("quality_flag") in (None, "numerator_undisclosed", "tfi_table_absent"):
            row["quality_flag"] = "ok"
    if res.get("item54") is not None:
        row["grandfathered_subordinated_eok"] = res["item54"]
    if res.get("item53") is not None:
        row["grandfathered_hybrid_eok"] = res["item53"]
    row["numerator_as_of"] = None if na else as_of
    row["hybrid_outstanding_eok"] = round(ledger_entry.get("hybrid", 0.0), 1)
    row["subordinated_outstanding_eok"] = round(ledger_entry.get("sub", 0.0), 1)
    row["bond_balance_as_of"] = ledger_entry.get("as_of")
    # --- 2026-10-12 새 필드(적용 규칙과 근거) ---
    row["rule"] = t2["rule"]
    row["rule_basis"] = R.rule_basis(t2)
    row["numerator_source"] = t2["numerator_source"]
    row["reason"] = R.REASON_NO_TFI_TABLE if na else None
    row["numerator_tfi_off_eok"] = t2["numerator_tfi_off"]
    row["utilization_pct_tfi_off"] = t2["pct_tfi_off"]
    row["item47_scope"] = t2["scope"]
    row["rule_flags"] = t2["flags"]
    row["supplementary_capital_eok"] = res.get("item3")
    row["lapse_excess_item49_eok"] = res.get("item49")
    # 2026-10-12: 「기본자본 한도초과분의 보완자본 재분류」 는 예전에 채권원장 발행액 - SCR x 15% (wire_capital_securities_to_utilization.py)
    # 로 한 번 쓰이고 갱신이 끊겨 있었다(하나생명 665.7 = 1,798.8 - 1,133.1). 이제 기본자본 소진율과 같은 출처
    # (공시 항목 6 + 등재부 분류, 기발행은 SCR x 15% · 기본자본형 신규는 SCR x 10% 초과분)의 tier1 결과를 그대로 쓴다.
    t1 = res.get("t1")
    row["tier1_overflow_into_tier2_eok"] = None if t1 is None else t1["overflow_eok"]
    row["no_capital_securities"] = res["no_capital_securities"]


def main() -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quarter", default="2026.2Q")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    y, q = a.quarter.split(".")
    as_of = date(int(y), *_QEND[q]).isoformat()

    records = json.loads(KICS.read_text(encoding="utf-8"))
    ledger = R.load_ledger()
    registry = R.load_registry()
    res_by_code = R.compute_quarter(records, a.quarter, ledger, registry)
    summaries = SUM.summaries_by_code(a.quarter)
    t1doc = json.loads(T1F.read_text(encoding="utf-8"))
    t2doc = json.loads(T2F.read_text(encoding="utf-8"))
    for doc, name in ((t1doc, T1F.name), (t2doc, T2F.name)):
        if doc.get("quarter") != a.quarter:
            raise SystemExit(f"[FATAL] {name} quarter={doc.get('quarter')} != --quarter {a.quarter}")

    changed, skipped = [], []
    for row in t1doc["results"]:
        row["securities_summary"] = summaries.get(row["code"]) or SUM.empty_summary(a.quarter)
        res = res_by_code.get(row["code"])
        if not res or res["t1"] is None:
            skipped.append(("t1", row["code"]))
            continue
        before = (row.get("utilization_pct"), row.get("tier1_hybrid_recognized_eok"))
        apply_tier1(row, res, registry, ledger.get(row["code"]) or {}, as_of)
        if row["code"] in REINSURER_NOTES and isinstance(row.get("reinsurer_basis"), dict):
            row["reinsurer_basis"]["note"] = REINSURER_NOTES[row["code"]]["why"]
        if before != (row["utilization_pct"], row["tier1_hybrid_recognized_eok"]):
            changed.append(("t1", row["code"], row["company"], before[0], row["utilization_pct"],
                            row["binding_leg"] or "-"))
    for row in t2doc["results"]:
        row["securities_summary"] = summaries.get(row["code"]) or SUM.empty_summary(a.quarter)
        res = res_by_code.get(row["code"])
        if not res:
            skipped.append(("t2", row["code"]))
            continue
        before = (row.get("utilization_pct"), row.get("numerator_eok"))
        apply_tier2(row, res, ledger.get(row["code"]) or {}, as_of)
        if row["code"] in REINSURER_NOTES and isinstance(row.get("reinsurer_basis"), dict):
            row["reinsurer_basis"]["note"] = REINSURER_NOTES[row["code"]]["why"]
        if before != (row["utilization_pct"], row["numerator_eok"]):
            changed.append(("t2", row["code"], row["company"], before[0], row["utilization_pct"], row["rule"]))

    src = f"kics_disclosure.json ({a.quarter} 경영공시)"   # emit_capsec_provenance 가 이 문자열에서 원천을 찾는다
    t1def = t1doc.setdefault("definition", {})
    t1def.update({
        "limit_primary": "SCR×15% (기발행 신종 - [별표22] Ⅵ.1.가.(1) 공통적용 경과조치, 2032-12-31 까지)",
        "limit_strict": "SCR×10% (기본자본형 신규 자본증권 - [별표22] Ⅲ.2.다.(1)②)",
        "numerator": ("기본자본 자본증권 = max(기발행 신종(item53) / (item14 x 15%), 기본자본형 신규(item6 - 기발행 - "
                      "보완자본형) / (item14 x 10%)) 의 결속 쪽. 보완자본형(Ⅲ.2.다.(2)) 신종은 제외"),
        "limit": "item14 x 15% (기발행) · item14 x 10% (기본자본형 신규) 중 결속 쪽",
        "source": src,
        "registry": "data/bonds/capital_tier_registry.json",
        "as_of": as_of,
        "rule_version": "2026-10-12 규정 근거 재정의 (data/_derived/capital_utilization_definition_20261012/definition_memo.md)",
    })
    t2def = t2doc.setdefault("definition", {})
    t2def.update({
        "numerator": ("보완자본 한도 적용 전 = 보완자본 - 해약환급금 부족분 상당액 중 해약환급금준비금 상당액 초과분 - "
                      "기발행 자본증권 (item47 경과조치 적용 후 열, 발행사 인쇄 관행 정규화 R0~R5 = 행의 rule)"),
        "limit": "item14 x 50% ([별표22] Ⅲ.2.마, 경과조치 적용 전 총요구자본 - Ⅵ.1.라)",
        "source": src,
        "as_of": as_of,
        "null_rule": f"rule=NA(항목 47~54 원문 부재)이면 numerator_eok·utilization_pct 는 null, reason='{R.REASON_NO_TFI_TABLE}'",
        "rule_version": "2026-10-12 규정 근거 재정의 (data/_derived/capital_utilization_definition_20261012/definition_memo.md)",
    })
    for d in (t1def, t2def):
        d["as_of_note"] = ("분자·분모 모두 같은 분기말 경영공시 항목이라 기준일이 어긋나지 않는다. "
                           "채권 발행현황(data/bonds/**)은 참고 줄과 forward outlook 전용으로 남는다.")

    print(f"[{a.quarter}] 규정 근거 산식 적용 - 소진율/분자 변경 {len(changed)}건 (tier1 "
          f"{sum(1 for c in changed if c[0] == 't1')} · tier2 {sum(1 for c in changed if c[0] == 't2')})")
    for tier, code, name, b, aft, tag in changed:
        print(f"  {tier} {code} {str(name)[:12]:14s} {b} -> {aft}  [{tag}]")
    if skipped:
        print(f"  계산 불가(항목 6·14 결측 등) {len(skipped)}건: {skipped}")
    if a.dry_run:
        print("(dry-run; 파일 안 씀)")
        return 0
    tag = a.quarter.replace(".", "")
    written = []
    for doc, deploy, outdir, tier in ((t1doc, T1F, OUT_T1, "tier1"), (t2doc, T2F, OUT_T2, "tier2")):
        txt = json.dumps(doc, ensure_ascii=False, indent=2) + "\n"
        deploy.write_text(txt, encoding="utf-8")
        written.append(deploy.name)
        f = outdir / f"{tier}_utilization_{tag}.json"
        if f.exists():
            f.write_text(txt, encoding="utf-8")
            written.append(f.relative_to(ROOT).as_posix())
    print("[wrote] " + " · ".join(written))
    return 0


if __name__ == "__main__":
    sys.exit(main())
