"""s3_inventory.py -- step 3 (READ-ONLY).  Complete inventory of every registered K-ICS gate exception and a first (registry-declared)
type classification.

Sources (all read-only):
  * code registries, imported from scripts/validate_kics_disclosure.py, src/solvency/validation/kics_json_rules.py and
    scripts/validate_kics_rate_sensitivity.py (the code is the final word; docs/kics_gate_exceptions.md lags behind it)
  * data/_gold/kics_exemption_provenance.json   (evidence ledger: claim_kind / status / citation / registered_by)
  * data/_gold/kics_subrisk_source_absent.json, data/_gold/kics_item23_children_post_absent.json, data/_gold/kics_restatement_ledger.json
  * the baseline gate report of the live master (to count the raw RED findings each registration neutralises)

Declared type (what the REGISTRY says it is):
  A = cross-filing conflict (this principle's target)      B = issuer self-inconsistency (one filing, table vs table)
  C = source absent                                        D = parser / tooling error or false positive
  E = other (policy, meta-rule, legit identity, unexplained)
The measured cross-filing test (step 6) later promotes some B / C / E rows to A.
"""
import csv
import json
import sys
from collections import Counter, defaultdict

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_precedence_dryrun_20261012")
from lib_dry import *  # noqa: F401,F403,E402

utf8_stdout()
import validate_kics_disclosure as vkd  # noqa: E402
import solvency.validation.kics_json_rules as kjr  # noqa: E402
import validate_kics_rate_sensitivity as rs  # noqa: E402

BASELINE_REPORT = REPO / "artifacts" / "kics_validation" / "report_20261012T094845Z.json"
LEDGER = read_json(REPO / "data" / "_gold" / "kics_exemption_provenance.json")["entries"]
SUBRISK_ABS = read_json(REPO / "data" / "_gold" / "kics_subrisk_source_absent.json")
ITEM23_ABS = read_json(REPO / "data" / "_gold" / "kics_item23_children_post_absent.json")
RESTATE = read_json(REPO / "data" / "_gold" / "kics_restatement_ledger.json")

rows_master = read_rows()
_, NAMES = master_index(rows_master)
NAMES.update({"KR1107": "퍼시픽라이프리", "KR1108": "마이브라운반려동물전문보험"})
NAME_TO_CODE = {v: k for k, v in NAMES.items()}

report = read_json(BASELINE_REPORT)
RED = [f for f in report["findings"] if f["status"] == "RED"]
RED_BY_BUCKET = defaultdict(list)
for f in RED:
    RED_BY_BUCKET[(f["원보험사코드"], f["공시분기"])].append(str(f["rule"]))

LEDGER_BY = {}
for e in LEDGER:
    LEDGER_BY.setdefault((e["registry"], e["company"], e["quarter"]), e)

TYPE_OF_CLAIM = {
    "ISSUER_INTERNAL_INCONSISTENCY": "B", "ISSUER_ROW_PRINTS_POST_LIMIT_VALUE": "B", "ISSUER_ROW_SHIFTED_BY_ONE_DEDUCTION": "B",
    "ISSUER_INCONSISTENT": "B", "DERIVATION_NOT_REPRODUCIBLE": "B",
    "TABLE_ABSENT": "C", "SECTION_ABSENT": "C", "DOCUMENT_PENDING_NOTICE": "C", "NOT_POSTED": "C", "SITE_ROLLED_OFF": "C",
    "STATED_NOT_APPLICABLE": "C", "COLLECTION_POLICY": "E", "PRINTED_DASH_MICRO_SCALE_FALSE_POSITIVE": "D",
}

inv = []


def add(registry, domain, code, quarter, rules, items, residual, declared, claim_kind, reason, approved, status, cite, extra=None):
    ledger = LEDGER_BY.get((registry, code, quarter)) or {}
    rec = {
        "registry": registry, "domain": domain, "code": code, "company": NAMES.get(code, code), "quarter": quarter,
        "rules": ";".join(rules) if isinstance(rules, (list, tuple)) else (rules or ""),
        "items_involved": ";".join(str(i) for i in items) if isinstance(items, (list, tuple, set)) else (items or ""),
        "pinned_residual": residual if isinstance(residual, str) else (json.dumps(residual, ensure_ascii=False) if residual else ""),
        "n_raw_red_in_bucket": len(RED_BY_BUCKET.get((code, quarter), [])),
        "raw_red_rules_in_bucket": ";".join(sorted(set(RED_BY_BUCKET.get((code, quarter), [])))),
        "claim_kind": claim_kind or ledger.get("claim_kind") or "",
        "reason": reason or "",
        "ledger_claim": (ledger.get("claim") or ""),
        "approved_or_registered_by": approved or ledger.get("registered_by") or "",
        "ledger_status": status or ledger.get("status") or "",
        "citation": cite or json.dumps(ledger.get("citation"), ensure_ascii=False) if (cite or ledger.get("citation")) else "",
        "declared_type": declared,
    }
    if extra:
        rec.update(extra)
    inv.append(rec)


# ---------------------------------------------------------------- _TIER2_ISSUER_INCONSISTENT
for (c, q), v in sorted(vkd._TIER2_ISSUER_INCONSISTENT.items()):
    led = LEDGER_BY.get(("_TIER2_ISSUER_INCONSISTENT", c, q)) or {}
    ck = led.get("claim_kind", "")
    cells = v.get("cells", {})
    add("_TIER2_ISSUER_INCONSISTENT", "K-ICS", c, q, list(v.get("findings", {}).keys()), sorted(int(k) for k in cells),
        {k: f.get("residual") for k, f in v.get("findings", {}).items()}, TYPE_OF_CLAIM.get(ck, "B"), ck,
        "tier2/기본자본 다리 축: " + (led.get("claim") or "")[:120], "owner 위임 2026-08-24/10-10", led.get("status"), None)

# ---------------------------------------------------------------- _IDENT_ISSUER_INCONSISTENT
for (c, q), v in sorted(vkd._IDENT_ISSUER_INCONSISTENT.items()):
    led = LEDGER_BY.get(("_IDENT_ISSUER_INCONSISTENT", c, q)) or {}
    rules = sorted({k.split("|")[0] for k in v["findings"]})
    add("_IDENT_ISSUER_INCONSISTENT", "K-ICS", c, q, ["룰" + r for r in rules], sorted(int(k) for k in v["cells"]),
        v["findings"], "B", led.get("claim_kind"), "평문 항등식 룰 2·4·5·6: " + (led.get("claim") or "")[:120], v.get("approved"), led.get("status"), None)

# ---------------------------------------------------------------- _LIFE8_ISSUER_INCONSISTENT
for (c, q), v in sorted(vkd._LIFE8_ISSUER_INCONSISTENT.items()):
    led = LEDGER_BY.get(("_LIFE8_ISSUER_INCONSISTENT", c, q)) or {}
    add("_LIFE8_ISSUER_INCONSISTENT", "K-ICS", c, q, ["8_life", "mmult17후"], [17, 29, 30, 31, 32, 33, 34, 35], v, "B",
        led.get("claim_kind"), "생명장기 총괄 대 세부표: " + (led.get("claim") or "")[:120], "owner 2026-08-21/10-10", led.get("status"), None)

# ---------------------------------------------------------------- IRR_DERIVE_ISSUER_INCONSISTENT
for (c, q), v in sorted(kjr.IRR_DERIVE_ISSUER_INCONSISTENT.items()):
    led = LEDGER_BY.get(("IRR_DERIVE_ISSUER_INCONSISTENT", c, q)) or {}
    add("IRR_DERIVE_ISSUER_INCONSISTENT", "K-ICS", c, q, ["36_irr", "TRANSITION_AFTER_IRR_MISMATCH"], [36, 41, 42, 43, 44, 45, 46], v, "B",
        led.get("claim_kind"), "금리위험액 도출식 불일치(원인 UNEXPLAINED): " + (led.get("claim") or "")[:100], "owner 2026-08-21/09-01", led.get("status"), None,
        {"type_note": "원인 미규명 - B 와 E 의 경계"})

# ---------------------------------------------------------------- source-absent families
for (c, q), v in sorted(vkd._CENSUS_SOURCE_ABSENT.items()):
    led = LEDGER_BY.get(("_CENSUS_SOURCE_ABSENT", c, q)) or {}
    kind = v.get("kind")
    add("_CENSUS_SOURCE_ABSENT", "K-ICS", c, q, ["coverage_census"], "1-54(버킷 전체)", "", TYPE_OF_CLAIM.get(kind, "C"), kind,
        "census 원천부재: " + (led.get("claim") or "")[:120], v.get("approved"), led.get("status"), None)
for (c, q), v in sorted(vkd._PL_SOURCE_ABSENT.items()):
    led = LEDGER_BY.get(("_PL_SOURCE_ABSENT", c, q)) or {}
    add("_PL_SOURCE_ABSENT", "PL_breakdown(ifrs17 레인 소관 데이터)", c, q, ["PL MASTER_HOLE"], "PL 버킷", "", "C", v.get("kind"),
        "PL 원천부재: " + (led.get("claim") or "")[:120], v.get("approved"), led.get("status"), None)
for (c, q) in sorted(kjr.IRR_SCENARIO_EXEMPT):
    led = LEDGER_BY.get(("IRR_SCENARIO_EXEMPT", c, q)) or {}
    add("IRR_SCENARIO_EXEMPT", "K-ICS", c, q, ["36_irr census"], [41, 42, 43, 44, 45, 46], "", "C", led.get("claim_kind"),
        "금리 충격시나리오 표 부재: " + (led.get("claim") or "")[:100], led.get("registered_by"), led.get("status"), None)
for (c, q) in sorted(kjr.MARKET_BREAKDOWN_EXEMPT):
    led = LEDGER_BY.get(("MARKET_BREAKDOWN_EXEMPT", c, q)) or {}
    add("MARKET_BREAKDOWN_EXEMPT", "K-ICS", c, q, ["19_market"], [36, 37, 38, 39, 40], "", "C", led.get("claim_kind"),
        "시장위험 분해표 부재(간이공시): " + (led.get("claim") or "")[:100], led.get("registered_by"), led.get("status"), None)
for (c, q) in sorted(vkd._AFTER_SUBRISK_NOT_DISCLOSED):
    led = LEDGER_BY.get(("_AFTER_SUBRISK_NOT_DISCLOSED", c, q)) or {}
    cells = sorted(vkd._AFTER_SOURCE_ABSENT_CELLS.get((c, q), []))
    add("_AFTER_SUBRISK_NOT_DISCLOSED", "K-ICS", c, q, ["8_post/mmult후 세부"], cells, "", "C", led.get("claim_kind"),
        "적용후 세부 미공시: " + (led.get("claim") or "")[:100], led.get("registered_by"), led.get("status"), None)
for (c, q, it) in sorted(kjr._TFI_MEMO_ISSUER_BLANK):
    add("_TFI_MEMO_ISSUER_BLANK", "K-ICS", c, q, ["53_tfi_memo_rows"], [it], "", "C", "ISSUER_BLANK_MEMO_ROW",
        "발행사가 TFI 메모행 라벨만 찍고 값을 안 넣음(대시와 다름)", "코드 주석(parser raw 판독)", "코드 등재(원장 항목 없음)", "")
for (c, q) in sorted(kjr._TFI_MEMO_TABLE_NOT_SCANNED):
    add("_TFI_MEMO_TABLE_NOT_SCANNED", "K-ICS", c, q, ["53_tfi_memo_rows"], [53, 54], "", "D", "OUR_BACKLOG_TABLE_NOT_SCANNED",
        "로더 텍스트 스캐너가 TFI 표를 못 읽음 = 우리 쪽 backlog(발행사 공란 아님)", "코드 주석(parser iter-10)", "코드 등재(원장 항목 없음)", "")
for code in sorted(kjr.IMAGE_OCR_COMPANIES):
    add("IMAGE_OCR_COMPANIES", "K-ICS", code, "(전 분기)", ["허용오차 10.0"], "1-26", "", "D", "IMAGE_OCR_TOLERANCE",
        "이미지/OCR 판독 회사의 룰 허용오차 완화(2.0 -> 10.0)", "코드 주석", "코드 등재", "")
add("TIER2_STALE_FALSE_POSITIVE", "K-ICS", "KR1108", "2025.3Q", ["47_tier2_census(_post) TIER2_LIMIT_STALE"], [47, 48, 49, 53, 54],
    json.dumps(kjr.TIER2_STALE_FALSE_POSITIVE[("KR1108", "2025.3Q")]["cells"], ensure_ascii=False), "D",
    "PRINTED_DASH_MICRO_SCALE_FALSE_POSITIVE", "원문 대시(0)가 전기 한도 잔존 지문에 걸린 거짓 양성", "owner 2026-10-12",
    (LEDGER_BY.get(("TIER2_STALE_FALSE_POSITIVE", "KR1108", "2025.3Q")) or {}).get("status"), None)
for k, v in sorted(vkd._TAUT_EXEMPT.items()):
    add("_TAUT_EXEMPT", "K-ICS(메타룰)", "(전사)", "(전 분기)", ["IDENTITY_TAUTOLOGY " + k[0] + " " + k[1]], "4 = sum(5..11)", v, "E",
        "ISSUER_FORMAT_DEFINES_IDENTITY", "발행사 서식이 총계를 성분의 합으로 정의 - 잔차 0 이 정상(상한 박제)", "owner 2026-08-21", "코드 등재", "")

# ---------------------------------------------------------------- JSON-gold absent registries
for e in SUBRISK_ABS.get("table_absent", []):
    add("kics_subrisk_source_absent.json:table_absent", "K-ICS", e["code"], e["quarter"], ["8_life_census"], e.get("items"), "", "C", e.get("verdict"),
        "29~35 원천 표 생략(보일러플레이트 한 줄): " + (e.get("reason") or "")[:100], "owner/parser 2026-09-03", e.get("confidence"), e.get("citation"))
for e in SUBRISK_ABS.get("legit_zero", []):
    add("kics_subrisk_source_absent.json:legit_zero", "K-ICS", e["code"], e["quarter"], ["8_life_census"], e.get("items"), "", "E", e.get("verdict"),
        "표는 있고 7항목 전부 '-' (정당한 0)", "owner/parser 2026-09-03", e.get("confidence"), "")
for key, e in sorted(ITEM23_ABS.get("entries", {}).items()):
    code, q = key.split("|")
    v = e.get("verdict")
    add("kics_item23_children_post_absent.json", "K-ICS", code, q, ["other_capital_children_sum"], [24, 25, 26], "",
        "C" if v == "SOURCE_ABSENT" else "E", v, "item23 후 자식 24/25/26 결측: " + (e.get("note") or "")[:100], "validation 2026-09-01", "원장 등재", e.get("evidence_file"))

# ---------------------------------------------------------------- rate-sensitivity gate (kics_rate_sensitivity.json - a different sheet; listed for completeness)
for (c, q), v in sorted(rs._RS1_ISSUER_INCONSISTENT.items()):
    led = LEDGER_BY.get(("_RS1_ISSUER_INCONSISTENT", c, q)) or {}
    add("_RS1_ISSUER_INCONSISTENT", "금리민감도", c, q, ["RS1"], "+100bp 3칸", v.get("findings"), "B", v.get("kind"),
        "금리민감도 표 안 비율 대 금액/기준금액 자기모순: " + (led.get("claim") or "")[:100], v.get("approved"), led.get("status"), None)
for (c, q), v in sorted(rs._RS5_SOURCE_ABSENT.items()):
    led = LEDGER_BY.get(("_RS5_SOURCE_ABSENT", c, q)) or {}
    add("_RS5_SOURCE_ABSENT", "금리민감도", c, q, ["RS5"], "버킷", "", "C", v.get("kind"),
        "금리민감도 표 부재(해당사항 없음): " + (led.get("claim") or "")[:100], v.get("approved"), led.get("status"), None)
for (name, q) in sorted(rs.RS2_EXCEPTIONS):
    add("RS2_EXCEPTIONS", "금리민감도", NAME_TO_CODE.get(name, name), q, ["RS2"], "base 지급여력기준금액", "", "B", "ISSUER_TABLE_TO_TABLE_OR_BASIS",
        "금리민감도 표 대 환율민감도 표(또는 별도/연결 basis) 지급여력기준금액 불일치(반올림 Δ3)", "코드 주석 2026-09-01", "코드 등재", "")
for (name, q, ph, col) in sorted(rs.RS1_EXCEPTIONS):
    add("RS1_EXCEPTIONS", "금리민감도", NAME_TO_CODE.get(name, name), q, ["RS1 " + ph + " " + col], "지급여력기준금액 " + col, "", "B", "ISSUER_PRINT_TYPO",
        "원문이 -100bp/-50bp 두 칸에 같은 9,170 을 인쇄(복붙 오류)", "코드 주석 2026-08-31", "코드 등재", "")
for (c, q) in sorted(rs.RS5_EXCEPTIONS):
    add("RS5_EXCEPTIONS", "금리민감도", c, q, ["RS5"], "버킷", "", "D", "PRE_EXISTING_BUCKET_HOLE_CAUSE_UNKNOWN",
        "kics_disclosure 에는 있는데 금리민감도 마스터에 통째 없음(원인 미규명, 백필 후보)", "코드 주석 2026-09-01", "코드 등재", "")
for (c, q, ph) in sorted(rs.RS6_KNOWN_HOLES):
    add("RS6_KNOWN_HOLES", "금리민감도", c, q, ["RS6 " + ph], "phase 행", "", "D", "ROUTED_BACKFILL_WORKLIST",
        "phase(적용전/후) 행 결손 - 정당한 부재 아님, parser 백필 대기(inbox 20260921T1400Z)", "코드 주석 2026-09-21", "코드 등재", "")

# ---------------------------------------------------------------- write
inv_sorted = sorted(inv, key=lambda r: (r["registry"], r["code"], r["quarter"]))
for i, r in enumerate(inv_sorted, 1):
    r["seq"] = i
cols = ["seq", "registry", "domain", "code", "company", "quarter", "rules", "items_involved", "pinned_residual", "n_raw_red_in_bucket",
        "raw_red_rules_in_bucket", "claim_kind", "declared_type", "type_note", "reason", "approved_or_registered_by", "ledger_status", "citation", "ledger_claim"]
for r in inv_sorted:
    r.setdefault("type_note", "")
with open(OUT / "exceptions_inventory_base.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for r in inv_sorted:
        rr = dict(r)
        rr["ledger_claim"] = (rr["ledger_claim"] or "")[:400]
        w.writerow(rr)
write_json_lf(OUT / "exceptions_inventory_base.json", inv_sorted)

# ---------------------------------------------------------------- which registration neutralises each of the 56 RED findings
tier2 = vkd._TIER2_ISSUER_INCONSISTENT
ident = vkd._IDENT_ISSUER_INCONSISTENT
life8 = vkd._LIFE8_ISSUER_INCONSISTENT
red_map = []
unmapped = []
for f in sorted(RED, key=lambda f: (f["원보험사코드"], f["공시분기"], str(f["rule"]))):
    c, q, rule = f["원보험사코드"], f["공시분기"], str(f["rule"])
    reg = None
    if (c, q) in tier2 and rule in tier2[(c, q)]["findings"]:
        reg = "_TIER2_ISSUER_INCONSISTENT"
    elif (c, q) in ident and f"{rule}|적용전" in ident[(c, q)]["findings"]:
        reg = "_IDENT_ISSUER_INCONSISTENT"
    elif (c, q) in life8 and rule == "8_life":
        reg = "_LIFE8_ISSUER_INCONSISTENT"
    if reg is None:
        unmapped.append((c, q, rule))
    red_map.append({"code": c, "company": NAMES.get(c, c), "quarter": q, "rule": rule, "registry": reg, "expected": f.get("expected"),
                    "actual": f.get("actual"), "diff": f.get("diff"), "detail": str(f.get("detail") or "")[:160]})
write_json_lf(OUT / "red56_registry_map.json", red_map)
print("raw RED findings:", len(RED), "| mapped to a registry:", len(red_map) - len(unmapped), "| unmapped:", unmapped)
print("by registry:", dict(Counter(r["registry"] for r in red_map)))
print("inventory rows:", len(inv_sorted))
print("rows by registry:")
for k, n in sorted(Counter(r["registry"] for r in inv_sorted).items()):
    print(f"   {k:55s} {n}")
print("rows by declared type:", dict(Counter(r["declared_type"] for r in inv_sorted)))
