"""Read-only: build exceptions_inventory.csv - every exception / registration / hold that the IFRS17 lane still carries, one row per entry.

Machine-read sources (all read-only):
  scripts/validate_master_tables.py : WFY_EXCEPTIONS, LOB_LEG_NA          scripts/validate_data_contract.py : _CSM_CONTINUITY_EXCEPTIONS, _CSM_SIGN_EXCEPTIONS (ast literal)
  data/_gold/*.json                  : csm_amort_identity_ledger, pl_csm_amort_missing_ledger, pl_amort_coverage_baseline(_released), pl_bridge_baseline,
                                       user_pl_confirmed_cells, bs_restated_cells, statutory_reserve_baseline/legit, user_csm_cells(exclude), gold overlays (blocks)
  data/_derived/ilp_restated_comparative.json, ilp_includes_lic.json, insurance_liability_portfolio_provenance.json (not_loaded, lrc_model_not_loaded)
  baseline gate outputs (baseline/*.txt): ABSENT-PL, ZLEG, SPIKE, CONT, WFYEX, LIC yellow lines
Curated rows (TODO_parser_ifrs17.md / TODO.md / changelog / inbox) carry their citation in `registry`.
type: A 공시 간·재작성 충돌(이 원칙의 대상)  B 발행사 자체 불일치  C 원문 부재  D 파서 오류/오탐  E 기타(정의 차이·계약이전·owner 확정·정보성)
status: active | baseline_known_failure | hold | dead_exemption | released | gold_overlay | resolved_prior_round | open_ticket | informational
"""
from __future__ import annotations

import ast
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lib_dryrun as D  # noqa: E402

ROOT = D.ROOT
NAMES = D.names()
for r in D.load_json("PL_breakdown.json"):
    NAMES.setdefault(r["원보험사코드"], r["원수사명"])
for r in D.load_json("IFRS17_BS.json"):
    NAMES.setdefault(r["원보험사코드"], r["원수사명"])
NAME2CODE = {v: k for k, v in NAMES.items()}
NAME2CODE.update({"IBK연금보험": "KR1011", "KB라이프생명": "KR0099"})
TYPE_LABEL = {"A": "공시 간·재작성 충돌", "B": "발행사 자체 불일치", "C": "원문 부재", "D": "파서 오류/오탐", "E": "기타"}

rows = []


def add(**kw):
    kw.setdefault("code", "")
    kw.setdefault("company", NAMES.get(kw["code"], kw.get("company", "")))
    kw.setdefault("quarters", "")
    kw.setdefault("n_cells", "")
    kw.setdefault("rule", "")
    kw.setdefault("reason", "")
    kw.setdefault("status", "active")
    kw.setdefault("registry", "")
    kw.setdefault("type", "E")
    kw.setdefault("prior_round", "")
    kw["type_label"] = TYPE_LABEL[kw["type"]]
    kw["cross_filing_candidate"] = "Y" if kw["type"] == "A" else kw.get("cross_filing_candidate", "N")
    kw["id"] = f"INV-{len(rows)+1:04d}"
    rows.append(kw)


def short(s, n=300):
    s = re.sub(r"\s+", " ", str(s or "")).strip()
    return s if len(s) <= n else s[:n] + "…"


chain0 = D.csm_chain()
gblocks0, _excl0 = D.gold_csm_blocks()
viol0 = {co: D.strict_violations(q) for co, q in chain0.items()}


def strict_wfy(co, fy):
    return [x for x in viol0.get(co, []) if x["rule"] == "WFY" and any(q.startswith(fy) for q in x["quarters"])]


# ----------------------------------------------------------------------------------------------------------------- CSM
sys.path.insert(0, str(ROOT / "scripts"))
import validate_master_tables as VM  # noqa: E402  (module import only; main() is not called)

for (nm, fy) in sorted(VM.WFY_EXCEPTIONS):
    code = NAME2CODE.get(nm, "")
    active = bool(strict_wfy(code, fy))
    add(domain="CSM_waterfall", code=code, company=nm, quarters=f"FY{fy}", n_cells="", rule="WITHIN_FY_OPENING_DRIFT(_EXCEPTED)",
        reason=("FY 내 기초 CSM 불일치 — 원천 공시가 FY 중 정정·소급재작성(교보는 3Q24 공식 소급재작성 주석). "
                + ("현재 엄격 기준(면제 없이)에서도 벌어져 있음." if active else
                   ("현재 마스터에는 드리프트가 없다 — 해당 FY 에 gold 오버레이 블록이 있어 앵커가 정렬돼 있음(죽은 면제)." if any(q.startswith(fy) for (c_, q) in gblocks0 if c_ == code)
                    else "현재 마스터에는 드리프트가 없다(죽은 면제)."))),
        status="active" if active else "dead_exemption", registry="scripts/validate_master_tables.py WFY_EXCEPTIONS", type="A")

for key, spec in [("하나생명보험", "2024.4Q")]:
    add(domain="CSM_waterfall", code="KR0097", company="하나생명보험", quarters="2024.4Q", rule="CSM_CONTINUITY_FY_BOUNDARY_EXCEPTED",
        reason="FY2025 사업보고서 note 38: 보험금융 회계정책 소급 적용으로 2024.1.1/2024.12.31 BS 만 재작성(기초 Δ+73.0억) — 2023.4Q(FY2023 원본)와 못 닫음. 2024.4Q 6항목은 이미 FY2025 <전기> 표(최신 비교 컬럼). 2023 이전 소급 없음.",
        status="active", registry="scripts/validate_data_contract.py _CSM_CONTINUITY_EXCEPTIONS", type="A",
        prior_round="2024.4Q 는 이미 최신 비교 컬럼으로 적재됨(재판정 안 함)")
add(domain="CSM_waterfall", code="KR0004", company="예별손해보험", quarters="2025.4Q", rule="CSM_SIGN_CONVENTION_EXCEPTED",
    reason="신계약CSM 부호: 발행사가 손실부담계약 전입/환입을 CSM 열 안에 표시((1,166,995)천원) — 공시 표기 그대로.", status="active",
    registry="scripts/validate_data_contract.py _CSM_SIGN_EXCEPTIONS", type="B")

led = D.load_json("data/_gold/csm_amort_identity_ledger.json")["entries"]
for k, e in led.items():
    nm, q = k.split("|")
    t = "A" if e["cause"] == "RESTATEMENT_BASIS" else "E"
    add(domain="PL_breakdown↔CSM_waterfall", code=NAME2CODE.get(nm, ""), company=nm, quarters=q, rule="CSM_AMORT_IDENTITY_PINNED", n_cells=2,
        reason=f"PL(원수+수재)CSM상각 {e['pl_eok']}억 대 워터폴 {e['waterfall_eok']}억, 잔차 {e['residual_eok']:+}억({e['rel']*100:.2f}%) [{e['cause']}] " + short(e["note"], 200),
        status="baseline_known_failure", registry="data/_gold/csm_amort_identity_ledger.json", type=t,
        prior_round="CSM 은 2024년 필링 비교(전기)컬럼=재작성값, PL 은 2023 원 필링값(등재부 사유)" if t == "A" else "원인 미규명(UNRESOLVED)")

led2 = D.load_json("data/_gold/pl_csm_amort_missing_ledger.json")["entries"]
for k, e in led2.items():
    nm, q = k.split("|")
    add(domain="PL_breakdown↔CSM_waterfall", code=NAME2CODE.get(nm, ""), company=nm, quarters=q, rule="PL_CSM_AMORT_MISSING_DOCUMENTED", n_cells=1,
        reason=f"PL 원수CSM상각=None, 워터폴 상각 {e['wf_amort_eok']}억 — " + short(e["note"], 220), status="active",
        registry="data/_gold/pl_csm_amort_missing_ledger.json", type="C" if e["cause"] == "NOT_DISCLOSED_SOURCE" else "D")

rel = D.load_json("data/_gold/pl_amort_coverage_baseline.json").get("_released_entries", {})
for k, e in rel.items():
    nm, q = k.split("|")
    add(domain="PL_breakdown↔CSM_waterfall", code=NAME2CODE.get(nm, ""), company=nm, quarters=q, rule="PL_BUCKET_ABSENT_VS_WATERFALL(released)",
        reason=f"[해소됨·카운트 제외] {e.get('status')}: " + short(e.get("note"), 160), status="released",
        registry="data/_gold/pl_amort_coverage_baseline.json _released_entries", type="D")

gblocks, excl = D.gold_csm_blocks()
d_csm = D.load_json("data/_gold/user_csm_cells.json")
for co, why in d_csm.get("exclude_companies", {}).items():
    add(domain="CSM_waterfall", code=co, quarters="전 분기", rule="exclude_companies", reason=short(why, 260), status="active",
        registry="data/_gold/user_csm_cells.json exclude_companies", type="C")

# gold overlays (owner cells) - one row per block
def gold_type(note):
    n = note or ""
    if re.search(r"재작성|소급|restat|전기 비교|비교컬럼|re-anchor|re-anch|WFY|전분기 re", n, re.I):
        return "A"
    if re.search(r"lag|오독|mis|오선택|잘못|1000|단위", n, re.I):
        return "D"
    if re.search(r"ROW_ABSENT|없음|부재|미공시|NOT", n, re.I):
        return "C"
    return "E"


gb = list(csv.DictReader(open(HERE / "gold_overlay_blocks.csv", encoding="utf-8-sig")))
for r in gb:
    t = gold_type(r["notes"])
    add(domain=r["master"], code=r["code"], quarters=r["quarter"], n_cells=r["n_items"], rule="GOLD_OVERLAY(owner xlsx fill)",
        reason=f"items {r['items']}: " + short(r["notes"], 220), status="gold_overlay",
        registry=("data/_gold/user_csm_cells.json" if r["master"] == "CSM_waterfall" else "data/_gold/user_pl_cells.json"), type=t)

# Lina held CSM rows
add(domain="CSM_waterfall", code="KR0074", quarters="2023.1Q", n_cells=6, rule="WITHIN_FY_OPENING_DRIFT(would fire)",
    reason="경영공시 2023.1Q/2024.1Q <전분기> 모두 재작성 전(옛) 기준 — 기초 22,082.5억 ≠ 마스터 2023.3Q/4Q 기초 35,264.0억(재작성). 보류.", status="hold",
    registry="data/_derived/csm_backfill_lina_20261011/held_rows_waterfall.json", type="A", prior_round="owner 2026-10-12 「보류 유지」 승인(TODO.md owner 결정 해소 목록)")
add(domain="CSM_waterfall", code="KR0074", quarters="2023.2Q", n_cells=6, rule="WITHIN_FY_OPENING_DRIFT(would fire)",
    reason="경영공시 2023.2Q/2024.2Q <전반기> 모두 재작성 전(옛) 기준(기초 22,082.5억). 보류.", status="hold",
    registry="data/_derived/csm_backfill_lina_20261011/held_rows_waterfall.json", type="A", prior_round="owner 2026-10-12 「보류 유지」 승인")

# CSM vs ILP basis-diff cells (validation 2026-10-12)
for code, qs, why, t in (
    ("KR0073", "2024.1Q·2024.2Q", "워터폴=owner override(원공시 쪽), ILP=2025.1Q·2Q 경영공시 전년동기 열(재작성) — 워터폴 62,139.4/61,330.8 대 ILP 58,860/57,689(+5.6~6.3%)", "A"),
    ("KR0099", "2023.4Q", "워터폴 30,176.4(원기준) 대 ILP 31,798(FY2024 주석 45 소급재작성) −5.1%", "A"),
    ("KR0097", "2024.4Q", "워터폴=FY2025 note 38 재작성(4,446.8), ILP=원공시(4,389.6) +1.3%", "A"),
    ("KR0003", "2023.4Q~2024.3Q", "재작성 군집: 워터폴 FY2024 기초 23,860.8 대 2023.4Q 기말 23,966.2(−105.4 연속성 단절, 0.5% 밴드가 가림); 2024.3Q 잔차 −23 은 설명 안 됨", "A"),
    ("KR0004", "2025.4Q", "계약이전(보고주체 변경): 워터폴 0.0 대 ILP 6,227", "E")):
    add(domain="CSM_waterfall↔ILP", code=code, quarters=qs, rule="CSM_WATERFALL_VS_ILP_CSM_STOCK (룰 미배선, 제안만)", reason=why, status="open_ticket",
        registry="data/_derived/validation_registrations_20261012/csm_wf_vs_ilp_basis_diff_cells.md", type=t, prior_round="등재하지 않음(룰 설계 필요, Opus 몫)")

for nm in ("DB손해보험", "NH농협손해보험", "동양생명", "메리츠화재해상보험", "삼성생명보험", "삼성화재해상보험", "아이엠라이프생명보험", "에이비엘생명보험", "케이디비생명보험", "코리안리", "푸본현대생명보험", "한화손해보험", "흥국생명보험", "흥국화재", "라이나생명보험"):
    add(domain="CSM_amortization", company=nm, code=NAME2CODE.get(nm, ""), quarters="2025.4Q", n_cells=10, rule="_pick_amort_block 동점 시 전기말 표 선택",
        reason="연간 CSM 상각 스케줄이 직전 연도 표(합계가 직전 연도 기말 CSM 과 0.05% 이내로 같음) — 뷰 빌더 선택 버그", status="open_ticket", registry="TODO_parser_ifrs17.md 열린 일(15사)", type="D")
add(domain="CSM_amortization", company="AIA·처브·메트라이프·BNP카디프·한화생명", quarters="2025.4Q", n_cells=18, rule="분할표 읽기(패널·extract_amort_schedule)",
    reason="마스터 18칸은 정정됐으나 패널·추출기는 분할표 앞 반쪽만 읽음(한화생명은 연결 표 선택)", status="open_ticket", registry="TODO_parser_ifrs17.md 열린 일(분할표)", type="D")
add(domain="CSM_waterfall", code="KR0072", quarters="2024.1Q→2024.2Q", rule="CSM_PLAUSIBILITY SPIKE", reason="기말 CSM 5,854→9,238억(+58%) — 게이트 출력 spike 1건(미등재).", status="active",
    registry="baseline/master_tables.txt 1b", type="E")
# reinsurer CSM items (TODO_parser_ifrs17.md)
for code, qs, rule, why, t, pr in (
    ("KR1107", "2024 민감도", "CSM_sensitivity", "퍼시픽 2024 민감도: FY2025 전기 열이 한 행 밀려 인쇄 — 규칙대로 FY2025 채택 중", "B", "R1 규칙 적용됨"),
    ("KR1106", "당기손익", "CSM_sensitivity", "스코리 당기손익: 원문이 손실=(+) 표기라 부호 반전 적재(항등식 근거) — 적재 확인 요청", "B", "이전 라운드"),
    ("KR1102", "신계약 CSM", "CSM_waterfall", "스위스리 신계약 CSM(감사보고서 1,098/1,743억 대 4-6-3 ① 622/1,328억) 불일치", "B", ""),
    ("KR1104", "2025.4Q", "CSM_waterfall", "하노버 FY2025 IFRS17 감사보고서 별첨 없음 → 2025.4Q 워터폴 행 부재(downloader)", "C", ""),
    ("KR1105", "2025.4Q", "CSM_waterfall", "RGA FY2025 IFRS17 감사보고서 별첨 없음 → 2025.4Q 워터폴 행 부재(downloader)", "C", ""),
    ("KR1108", "전 분기", "CSM_*", "마이브라운 CSM 계열 전부 PAA 전용 — 해당 없음", "C", "")):
    add(domain="CSM_reinsurers", code=code, quarters=qs, rule=rule, reason=why, status="open_ticket", registry="TODO_parser_ifrs17.md '재보사 CSM 계열'", type=t, prior_round=pr)
add(domain="CSM_waterfall", code="KR1107", quarters="2023.4Q", rule="항목 4 인쇄값(영업양수 포함)", reason="퍼시픽 항목 4 = 950.77억(영업양수 1,069억 포함, 인쇄값) — 인쇄값 유지 + 사이드카 비고(9차 ⑳)",
    status="resolved_prior_round", registry="docs/changelog_parser_ifrs17.md 9차 ⑳", type="E", prior_round="3bf1690 — 변경 0, 재판정 안 함")

# ----------------------------------------------------------------------------------------------------------------- PL
bridge = D.load_json("data/_gold/pl_bridge_baseline.json")["entries"]
cls_type = {"pre_existing": "D", "lob_sum_gap": "D", "lob_split_not_extracted": "D", "single_leg_gap_생명장기": "D", "single_leg_gap_자동차_일반": "D",
            "tier1_tier2_basis_split": "D", "dart_dual_tag": "B"}
for k, e in bridge.items():
    nm, q, rule = k.split("|")
    add(domain="PL_breakdown", code=NAME2CODE.get(nm, ""), company=nm, quarters=q, n_cells=1, rule=f"PL_BRIDGE:{rule}",
        reason=f"[{e['class']}] 잔차 {e.get('diff')} (lhs {e.get('lhs')}) " + short(e["reason"], 200), status="baseline_known_failure",
        registry="data/_gold/pl_bridge_baseline.json", type=cls_type.get(e["class"], "D"),
        cross_filing_candidate="Y" if q.startswith("2023") else "N")

conf = D.load_json("data/_gold/user_pl_confirmed_cells.json")["cells"]
for c in conf:
    is_collapse = c.get("rule") == "PL_YTD_COLLAPSE_TO_ZERO"
    add(domain=c["master"], company=c["company"], code=NAME2CODE.get(c["company"], ""), quarters=c["quarter"], n_cells=1,
        rule=c.get("rule") or ("owner-confirmed outlier" if c["master"] == "PL_breakdown" else "R-RSV-6 legit zero"),
        reason=f"{c['item']}={c['value']} — " + short(c.get("note"), 200), status="active", registry="data/_gold/user_pl_confirmed_cells.json",
        type="E")

for nm, q, kind in (("서울보증보험", "2024.2Q", "SITE_ROLLED_OFF"), ("서울보증보험", "2024.3Q", "SITE_ROLLED_OFF"), ("하노버재보험", "2025.3Q", "NOT_POSTED")):
    add(domain="PL_breakdown", company=nm, code=NAME2CODE.get(nm, ""), quarters=q, rule="MASTER_HOLE_SOURCE_ABSENT", n_cells="통째", reason=f"원천부재 면제 [{kind}] — PL 버킷 없음(사이트 미게시)",
        status="active", registry="data/_gold/kics_exemption_provenance.json (PL source-absent ledger)", type="C")

for nm, legs, why in (("코리안리재보험", "자동차손익", "전업 재보험사 — 자동차 컬럼 부재"), ("서울보증보험", "생명장기손익", "보증보험사 — 장기 보장 상품 미판매")):
    add(domain="PL_breakdown", company=nm, code=NAME2CODE.get(nm, ""), quarters="전 분기", rule="LOB_LEG_NA", reason=f"{legs}: {why}", status="active",
        registry="scripts/validate_master_tables.py LOB_LEG_NA", type="C")

# ZLEG flags from the baseline gate output
mt = (HERE / "baseline" / "master_tables.txt").read_text(encoding="utf-8").splitlines()
for ln in mt:
    m = re.match(r"\s+ZLEG\s+(\S+)\s+(\d{4}\.\dQ)\s+zero=(\d+) none=(\d+)\s+(.*)", ln)
    if m:
        add(domain="PL_breakdown", company=m.group(1), code=NAME2CODE.get(m.group(1), ""), quarters=m.group(2), n_cells=m.group(4), rule="PL_ZERO_LEGS",
            reason=f"생명장기 sub-leg {m.group(4)}개 None/0 ({m.group(5)}) — 추출 갭 가능성", status="active", registry="baseline/master_tables.txt 2b (validation 09-20 12차 ZERO_LEGS DART 4Q 9건)", type="D")
add(domain="PL_breakdown", company="(DISCLOSURE 계보 비상장·재보사)", quarters="2024.1Q~2026.2Q", n_cells=269, rule="PL_BRIDGE leg-coverage SKIP(원천 미수록)",
    reason="경영공시 §2-1 요약 PL 은 LOB 분해를 싣지 않는다 — 검산 불가로 SKIP(통과 아님). 건별 인쇄는 게이트 출력 2e.", status="informational", registry="baseline/master_tables.txt 2e", type="C")
add(domain="PL_breakdown", company="(DISCLOSURE 계보 비상장·재보사)", quarters="2024.1Q~2026.2Q", n_cells=195, rule="PL_ZERO_LEGS SKIP(원천 미수록)",
    reason="생명장기 sub-leg 원천 미수록 195셀(ZLEGNA)", status="informational", registry="baseline/master_tables.txt 2b-na", type="C")
for typ, n, why in (("A", 9, "생명 항목 2 레그 — Tier-2 생명 핸들러 확장 또는 게이트 면제 조건 변경"), ("D", 5, "항목 15 기타영업수익=0.0 승인 시 잔차 −79~+77로 닫힘"), ("D", 3, "삼성화재 2023.2Q(DART 기준 제안)·롯데 레그 없음·예별 장기 레그 없음")):
    add(domain="PL_breakdown", company="(복수)", quarters="2023~2026", n_cells=n, rule="PL 항목 1 보류", reason=f"보류 17칸 중 {n}칸: {why}", status="hold",
        registry="TODO_parser_ifrs17.md ⑥ (PL 항목 1 보류 17칸)", type=typ, cross_filing_candidate="Y" if n == 9 else "N")
add(domain="PL_breakdown", company="삼성화재해상보험", code="KR0008", quarters="2023.2Q", n_cells=3, rule="일반손익(14) 마스터 오류(DART 보험종목별 표 재계산 161,674 대 354,530)",
    reason="항목 1·15·16 을 DART 별도 기준으로 맞추는 제안(proposed_pl_kr0008_2023.2Q_dart_basis.json) — owner 대기", status="open_ticket", registry="TODO_parser_ifrs17.md ③", type="D")
add(domain="PL_breakdown", company="케이디비생명보험", code="KR0072", quarters="2023.4Q~2026.2Q", n_cells=37, rule="3개월/누적 쌍 표 열 혼입 정정 37칸 gold 미등재",
    reason="build_pl 재실행 시 되돌아감(등재 후보 proposed_gold_overlay_pl_20261011.json)", status="open_ticket", registry="TODO_parser_ifrs17.md ③", type="D")
add(domain="PL_breakdown", company="(복수)", quarters="2023.4Q~2025.4Q", n_cells=26, rule="PL 부모 #2 결측 26버킷", reason="inbox/parser/20260918T0710Z — 칸마다 FILLED/ABSENT_IN_SOURCE/UNREADABLE 회신 대기",
    status="open_ticket", registry="inbox/parser/20260918T0710Z", type="C")
add(domain="PL_breakdown", company="라이나생명보험", code="KR0074", quarters="2023.4Q", n_cells=1, rule="PL 골든 sha256_coverage", reason="디스크 coverage 와 빌더 산출 불일치 1행(no_income_statement vs ok)",
    status="open_ticket", registry="TODO_parser_ifrs17.md 열린 일(PL 골든 실패)", type="D")
add(domain="PL_breakdown", company="(복수)", quarters="", n_cells=369, rule="값_당분기 None 잔존", reason="항목 1·16·22·23·24 의 값_당분기 None 369행(빌더 결함)", status="open_ticket",
    registry="TODO_parser_ifrs17.md ⑦", type="D")
add(domain="PL_breakdown", company="예별손해보험", code="KR0004", quarters="2023.4Q·2025.4Q", n_cells=14, rule="extract_tier2_yebyeol 핸들러(13·14 손익 부호, 장기 열 합계)",
    reason="루트 마스터 10칸만 정정돼 build_pl() 이 되돌림; ZERO_LEGS 5·6·7·9~12 잔여", status="open_ticket", registry="TODO_parser_ifrs17.md 열린 일(예별 핸들러)", type="D")
add(domain="PL_breakdown/IFRS17_BS/ILP", company="예별손해보험", code="KR0004", quarters="2025.2Q·3Q·4Q", rule="보고주체 단절", reason="2025.2Q(구 MG)·2025.3Q(신설 제1기)·2025.4Q(DART 엠지, 2025-09-03 계약이전) 세 칸 보고주체가 다름; DART 728억 대 경영공시 38,191억(52배)",
    status="active", registry="TODO_parser_ifrs17.md KR0004 / docs/domains/claude-agent-ifrs17.md §0.2", type="E")
add(domain="PL_breakdown", company="신한이지·카카오페이·하나손보·예별·AIA·아이엠라이프", quarters="4Q", rule="PL 부호 규약(FS-API 한화손해 16·23 등)", reason="XBRL 부호 규약 차이: 원 공시 대 후속 비교열 동일 크기 반대 부호 10칸은 재작성이 아니다(census)",
    status="informational", registry="pl_tier1_scan_refined.csv kind=SIGN_FLIP", type="D")

# ----------------------------------------------------------------------------------------------------------------- BS
for k, c in D.load_json("data/_gold/bs_restated_cells.json")["cells"].items():
    nm, it, q = k.split("|")
    add(domain="IFRS17_BS", company=nm, code=NAME2CODE.get(nm, ""), quarters=q, n_cells=1, rule="bs_restated_cells (owner adopt_restated 2026-09-02)",
        reason=f"항목 {it}: 마스터 {c['마스터']:.0f} (후속 필링 재작성본) 대 원 필링 {c['원_필링_당시본']:.0f} — 소급재작성본을 최종 채택", status="resolved_prior_round",
        registry="data/_gold/bs_restated_cells.json", type="A", prior_round="owner 결정 2026-09-02 최신 재작성본 채택 — 재판정 안 함")
res = D.load_json("data/_gold/statutory_reserve_baseline.json")["entries"]
add(domain="IFRS17_BS", company="(복수)", quarters="2023.1Q~2026.2Q", n_cells=len(res), rule="R-RSV-1 BASELINE (연속 동일값)", reason="법정준비금 연속 동일값 13건(결산 적립이 안 움직임; owner 이월 결정 이후 잔여)",
    status="baseline_known_failure", registry="data/_gold/statutory_reserve_baseline.json", type="C")
leg = D.load_json("data/_gold/statutory_reserve_legit.json")
add(domain="IFRS17_BS", company="(복수)", quarters="", n_cells=len(leg["disclosed_none"]) + len(leg["legit_flat"]), rule="R-RSV legit (disclosed_none 11 + legit_flat 4)",
    reason="원문이 그렇게 공시했으므로 옳은 것(원문 인용 evidence 보유)", status="active", registry="data/_gold/statutory_reserve_legit.json", type="E")
hb = D.load_json("data/_derived/bspl_apply_20261011/hold_list_B_20261011.json")["holds"]
for h in hb:
    add(domain="IFRS17_BS", code=h["company"] if h["company"].startswith("KR") else "", quarters=",".join(h["quarters"][:4]) + ("…" if len(h["quarters"]) > 4 else ""),
        n_cells=h["cells_still_blank"], rule="BS 보류 (B) 목록", reason=f"항목 {h['items']}: " + short(h["reason"], 220), status="hold",
        registry="data/_derived/bspl_apply_20261011/hold_list_B_20261011.json", type="A" if re.search(r"재작성|R1", h["reason"]) else "D")
h5 = D.load_json("data/_derived/bspl_followup_20261011/hold_reasons_5c.json")
catn = Counter()
for x in h5:
    catn[x["category"]] += x["n_cells"]
for cat, n in sorted(catn.items()):
    add(domain="IFRS17_BS", company="(복수)", quarters="", n_cells=n, rule=f"BS 보류 5c: {cat}", reason="정의/앵커 불일치로 적재하지 않은 칸(사유 hold_reasons_5c.json)", status="hold",
        registry="data/_derived/bspl_followup_20261011/hold_reasons_5c.json", type="E" if "DEFINITION" in cat or "DIFFERS" in cat or "FORM" in cat else ("C" if "NO_OWN" in cat else "D"))
add(domain="IFRS17_BS", company="(복수)", quarters="2023.1Q~2026.2Q", n_cells=17, rule="BS_KICS_BASELINE_BREAK (17BS↔K-ICS 자본계정)", reason="17BS 별도 ↔ K-ICS 연결 혼재로 평소와 다른 이탈; K-ICS 레인 확인 필요",
    status="informational", registry="baseline/data_contract.txt", type="E")
add(domain="IFRS17_BS", company="(복수)", quarters="", n_cells=3, rule="빌더 결함 3건", reason="build_ifrs17_bs 항목 10 행 선택(알파벳 순) · FS-API 013 분기 XML 폴백 표 선택 · KR0072 핸들러", status="open_ticket",
    registry="TODO_parser_ifrs17.md ⑦", type="D")
add(domain="IFRS17_BS", company="비엔피파리바카디프생명보험", code="KR0075", quarters="2023.4Q", n_cells=2, rule="자산·부채총계 0.08% 차이", reason="마스터 자산 2,933,816/부채 2,687,608 대 감사보고서 2,931,404/2,685,196(FY2024 비교열도 동일) — 자본은 동일",
    status="open_ticket", registry="TODO_parser_ifrs17.md 열린 일(KR0075)", type="D", cross_filing_candidate="Y")

# ----------------------------------------------------------------------------------------------------------------- ILP
for (c, q), p in {("KR0029", "2024.4Q"): None}.items():
    add(domain="ILP", code=c, quarters=q, n_cells=1, rule="R3_PINNED_EXEMPTION", reason="순 LRC 가 0 근처(+31.0억, DART 30.23) vs BS 20 2,917.7억 — 10배 규칙, 값은 맞고 구조적", status="active",
        registry="scripts/validate_insurance_liability_portfolio.py R3_PINNED_EXEMPTIONS", type="E")
rc = D.load_json("data/_derived/ilp_restated_comparative.json")["cells"]
for c in rc:
    add(domain="ILP", code=c["company_code"], quarters=c["quarter"], n_cells="1셀(항목 8·10~15)", rule="ilp_restated_comparative (최신 비교열 채택)",
        reason="최신 공시 비교열(재작성 기준)로 적재 — " + short(c["restatement_reason"], 150), status="resolved_prior_round", registry="data/_derived/ilp_restated_comparative.json", type="A",
        prior_round="owner 「최신 공시 쓰기」 적용 — 재판정 안 함")
ic = D.load_json("data/_derived/ilp_includes_lic.json")["companies"]
for co, v in ic.items():
    add(domain="ILP", code=co, quarters=f"{v['quarters'][0]}~{v['quarters'][-1]}", n_cells=len(v["quarters"]), rule="ilp_includes_lic 사이드카",
        reason="2-4 합계가 LIC 를 이미 포함(항목 8≈15) — 정의 차이", status="active", registry="data/_derived/ilp_includes_lic.json", type="E")
prov = D.load_json("insurance_liability_portfolio_provenance.json")
for x in prov["not_loaded"]:
    add(domain="ILP", code=x["company_code"], quarters=x["quarter"], rule="not_loaded", reason=short(x["reason"], 240), status="hold",
        registry="insurance_liability_portfolio_provenance.json not_loaded", type="E" if x["company_code"] == "KR0004" else "C")


def lrc_type(reason):
    r = reason or ""
    if re.search(r"disagrees with the FY2023 original basis|재작성", r):
        return "A"
    if re.search(r"disagrees with|오기|Indirect-Par|omit", r):
        return "B"
    return "C"


for x in prov["lrc_model_not_loaded"]:
    add(domain="ILP", code=x["company_code"], quarters=x["quarter"], rule="lrc_model_not_loaded", reason=f"items {x.get('items')}: " + short(x["reason"], 230),
        status="resolved_prior_round" if x.get("resolved") else "hold", registry="insurance_liability_portfolio_provenance.json lrc_model_not_loaded", type=lrc_type(x["reason"]),
        prior_round="resolved 표지" if x.get("resolved") else "")
add(domain="ILP", company="(복수)", quarters="2025.1Q~2026.2Q", n_cells=55, rule="R4_NA_VS_MISSING 항목 9 빈칸", reason="항목 9 가 빈 국내 55칸(PDF 대조: 해당사항 없음 39 → 0 후보, 텍스트층에서 못 찾음 16)", status="hold",
    registry="TODO_parser_ifrs17.md '항목 9'", type="C")
add(domain="ILP", company="(복수)", quarters="2023.1Q~2026.2Q", n_cells=283, rule="LIC 검산기 SOURCE-ABSENT", reason="DART 필링 자체가 no_filing 인 (회사,분기) — 정상 공백", status="informational",
    registry="baseline/ilp_lic.txt", type="C")
for ln in (HERE / "baseline" / "ilp_lic.txt").read_text(encoding="utf-8").splitlines():
    m = re.match(r"\s+(R-LIC\d)\s+(KR\d+)\s+(\d{4}\.\dQ):\s+(.*)", ln)
    if m:
        add(domain="ILP", code=m.group(2), quarters=m.group(3), rule=m.group(1) + " YELLOW", reason=short(m.group(4), 240), status="informational", registry="baseline/ilp_lic.txt",
            type="E" if "BS-lane" in m.group(4) or "offset" in m.group(4) else "D")
add(domain="ILP", code="KR0074", quarters="2023.1Q·2023.2Q", n_cells=8, rule="옛 기준 (항목 10·13·14·15)", reason="FY2024_Q1/Q2 공시 비교열도 재작성 전 기준 — 2023.2Q→3Q 에서 LRC·합계 계열이 끊김(LIC 는 매끈). 두 칸 유지 여부 owner 결정",
    status="open_ticket", registry="TODO_parser_ifrs17.md 열린 일(ILP 라이나)", type="A")
add(domain="ILP", code="KR1104", quarters="2026.2Q", n_cells=8, rule="2-4 합계 BEL −292 대 BS 순 LRC BEL −440.95", reason="같은 공시 내 불일치(RA·CSM 은 같음) — 항목 1~8 미적재", status="hold",
    registry="TODO_parser_ifrs17.md 재보사 ILP 잔여 ①", type="B")
add(domain="ILP", code="KR1104", quarters="2025.3Q", rule="PDF 부재", reason="하노버 2025.3Q 경영공시 PDF 수집 필요(2024.3Q 비교 칸도 그 안에 있음)", status="hold", registry="TODO_parser_ifrs17.md ②", type="C")
add(domain="ILP", company="스위스리·제네럴·RGA·스코리·마이브라운·하노버·퍼시픽", quarters="연말", rule="LIC(10~15) 비어 있음", reason="경영공시에 재무상태표 상세 없음(RGA·스코리·마이브라운은 감사보고서 주석에 다른 표기로 있음)",
    status="hold", registry="TODO_parser_ifrs17.md ③", type="C")
for code, qs, why, pr in (("KR1104", "2023.4Q", "하노버 2023.4Q ILP 공란 — FY2024 4-6-2 <2023> 표(합계 (572.65) 77.05 254.77)가 재작성 전 기준과 충돌", "9차 ㉒ 변경 없음"),
                          ("KR1101", "2023.4Q", "뮌헨 2023.4Q ILP 부호 — 인쇄 부호 반전 확인", "9차 ㉑ 변경 없음"),
                          ("KR1103", "민감도", "제네럴 민감도 — 방향 미확정이라 빈칸(전 칸)", "9차 ㉑ 변경 없음")):
    add(domain="ILP/CSM_sensitivity", code=code, quarters=qs, rule="재보사 재작성·부호 충돌", reason=why, status="resolved_prior_round", registry="docs/changelog_parser_ifrs17.md 9차", type="A" if code == "KR1104" else "B", prior_round=pr)
add(domain="ILP", code="KR1102", quarters="2026.1Q", n_cells=8, rule="인쇄 합계가 Indirect-Par 행 제외", reason="owner 지시로 전체 행 합 적재(10차, 4147fc1)", status="resolved_prior_round",
    registry="docs/changelog_parser_ifrs17.md 10차", type="B", prior_round="owner 결정 적용 — 재판정 안 함")
# reinsurer R1 (owner 2026-10-09)
add(domain="PL_breakdown/IFRS17_BS", company="재보사 8곳", quarters="2023.2Q~2025.2Q", n_cells=15, rule="R1(충돌 시 최신 공시의 전기 칸)",
    reason="PL 11칸(+연동 4행) + BS 하노버 2023.4Q 5칸·스코리 2024.4Q 1칸을 최신 공시 전기 칸으로 교체", status="resolved_prior_round", registry="docs/changelog_parser_ifrs17.md / bspl_granularity_runlog 8차",
    type="A", prior_round="owner 2026-10-09 R1(재보사 한정) 적용 — 재판정 안 함")

# ----------------------------------------------------------------------------------------------------------------- write
json.dump(rows, open(HERE / "_inventory_base.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
cols = ["id", "domain", "code", "company", "quarters", "n_cells", "rule", "reason", "status", "registry", "type", "type_label", "cross_filing_candidate", "prior_round"]
with open(HERE / "exceptions_inventory.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
cnt_status = Counter(r["status"] for r in rows)
cnt_type = Counter(r["type"] for r in rows if r["status"] not in ("released",))
print("rows", len(rows))
print("by status:", dict(cnt_status))
print("by type (excluding released):", dict(cnt_type))
core = [r for r in rows if r["status"] not in ("gold_overlay", "released", "informational", "resolved_prior_round")]
print("core exceptions/holds (excl. gold overlay, released, informational, resolved):", len(core), dict(Counter(r["type"] for r in core)))
print("cross-filing candidates (type A or flagged):", sum(1 for r in rows if r["cross_filing_candidate"] == "Y" and r["status"] not in ("released",)))
json.dump({"rows": len(rows), "by_status": dict(cnt_status), "by_type": dict(cnt_type), "core": len(core), "core_by_type": dict(Counter(r["type"] for r in core))},
          open(HERE / "exceptions_inventory_summary.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
