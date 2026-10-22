# -*- coding: utf-8 -*-
"""plan_md: assemble PLAN.md (the ranked plan in Markdown) from plan_table.csv + the static findings below.  READ-ONLY (writes PLAN.md in this folder only).
Run after plan_build.py."""
import csv
import sys
from collections import OrderedDict

sys.stdout.reconfigure(encoding="utf-8")
H = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure/"
rows = list(csv.DictReader(open(H + "plan_table.csv", encoding="utf-8-sig")))


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


groups = OrderedDict()
for r in rows:
    groups.setdefault((r["rank"], r["code"], r["scenario"]), []).append(r)

tot = {}
for k in ("READY", "NEEDS_OWNER", "BLOCKED"):
    rs = [r for r in rows if r["readiness"] == k]
    tot[k] = (len(rs), sum(int(r["pl_value_cells"] or 0) for r in rs), sum(int(r["csm_cells"] or 0) for r in rs))
all_rows = sum(v[0] for v in tot.values())
all_pl = sum(v[1] for v in tot.values())
all_csm = sum(v[2] for v in tot.values())

out = []
W = out.append

W("# e20 STEP 2 측정: 최신 비교열이 못 닫은 버킷과 잔여 버킷의 처리 계획")
W("")
W("범위: 티켓 `inbox/parser/20261022T1800Z__orchestrator__MULTI_2023.1Q-2025.2Q__latest_comparative_held_and_remaining.md` 의 STEP 2 (읽기 전용 측정).")
W("마스터·gold·provenance·테스트·TODO·changelog 는 건드리지 않았고 커밋·푸시도 하지 않았다. 모든 산출은 이 폴더(`data/_derived/remaining_20261022/e20_held_and_remaining/measure/`) 안에만 있다.")
W("후보 마스터와 후보 provenance 는 세션 scratchpad 에만 있고, 게이트는 `gate_overlay.py`(저장소 쓰기를 모두 버리는 in-process 실행기)로 돌렸다. 측정 기준 마스터 = 세션 시작 스냅샷(`snap_hashes_start.txt`).")
W("STEP 1 은 그 뒤 커밋 `5419a817` 로 적재됐다(8절에 상호작용 점검).")
W("")
W("## 0. 한눈에")
W("")
W("| 구분 | 계획표 행 | PL 칸 | CSM 칸 | 뜻 |")
W("|---|---:|---:|---:|---|")
W(f"| READY | {tot['READY'][0]} | {tot['READY'][1]} | {tot['READY'][2]} | 리더 변경이 작고 실제 필링에서 독립 재독으로 검증했으며 게이트 모의가 통과한다. 지금 적재할 수 있다 |")
W(f"| NEEDS_OWNER | {tot['NEEDS_OWNER'][0]} | {tot['NEEDS_OWNER'][1]} | {tot['NEEDS_OWNER'][2]} | 기술적으로는 닫히지만 owner 결정(면제 등재, 연쇄용 gold 교체, 현대해상 레그 원천)이 먼저다 |")
W(f"| BLOCKED | {tot['BLOCKED'][0]} | {tot['BLOCKED'][1]} | {tot['BLOCKED'][2]} | 원천이 raw 에 없는 버킷. 0행 (현대해상 FY2023 은 DART 에 없지만 IR 팩트시트가 raw 에 있어 NEEDS_OWNER) |")
W(f"| 합계 | {all_rows} | {all_pl} | {all_csm} | |")
W("")
W("티켓이 지목한 「닫히지 않은 STAY 22버킷」은 READY 12 / NEEDS_OWNER 10 / BLOCKED 0 으로 갈린다(현대해상 2023.4Q 가 NEEDS_OWNER). 나머지 계획표 행은 같은 회사×FY 블록의 형제 분기와 범위 (1)(2)(5) 항목이다. 대응표는 `stay_mapping.csv` 와 2절 (4).")
W("")
W("### 가장 중요한 발견 5개")
W("")
W("1. **농협생명 2023.1Q/2Q 「bridge FAIL −98,612/−191,660 mn」은 census 산식의 인공물이다.** 라이브 게이트는 이 두 칸을 FAIL 이 아니라 NOLHS(보험손익 없음)로 센다(`g_base/master_tables.txt` L189-190). 진짜 결함은 FY2023 Q1/Q2 DART 구양식(`영업수익/영업비용`, `<TD>`) 손익계산서를 못 읽어 32칸 중 20칸이 공란이고 4칸(16·22·23·24)이 경영공시 PDF 억원 반올림값인 것이다. 후속 FY2024 Q1/Q2 필링의 전기 누계 열(`20240514001371.xml` L5592-6957, `20240814002115.xml` L5706-7074)로 48칸이 항등식 잔차 0.000000 으로 닫힌다.")
W("2. **생보는 LOB 노트 전기열 리더가 필요 없다.** 마스터 item 2/3/8 이 손익계산서 4줄(보험수익·재보험수익·발행보험서비스비용·재보험비용)을 따르므로 후속 필링의 전기열 4줄만으로 가교가 닫힌다(KB라이프·미래에셋·한화·ABL·KDB·푸본). census 의 「LOB note prior-column reader missing」은 생보에는 틀린 진단이다. 손보만 노트 리더가 필요한데 셋 다 작다: KB손보(생산 `extract_tier2_kb(item1=…)` 그대로, 잔차 0/0/−1/0 mn), 롯데(둘째 표·전반기 마커 표 선택, 잔차 −0.75/−0.53/0/0 및 2023.1Q/2Q +0.40/−0.43), 메리츠(Format-B 둘째 표, +0.5/−1.2). 현대해상은 DART 에 전분기 LOB 분해가 없어 IR 팩트시트가 필요하다(5번).")
W("3. **「CSM 전기열 못 읽음·재작성」 라벨의 상당수가 리더 오독이었다.** ABL·롯데 2024.4Q 의 DIFF 는 dry-run `별도세그합산` 오독(체인 불일치)이고 진짜 전기열 = 마스터(SAME)다. 푸본 2024.4Q·미래에셋 2023.4Q 도 SAME(라벨링 실패일 뿐)이다. 그래서 「이중 재작성 3사 연속성 RED 3건」은 실제로 2건(KB라이프 FY2023 의 3개 판 6.75% · 롯데 FY2023 0.63%)이고 ABL 은 0건이다. READY 의 CSM 55칸은 전부 독립 리더로 후속 필링 표에서 다시 읽어 줄 번호까지 대조했다(`ready_csm_cells.csv`).")
W("4. **막고 있는 것은 리더가 아니라 owner 판단이다.** ① KB라이프 FY2023 의 3개 판(V0 31,201.3 / V1 31,327.6 / V2 33,595.7) — 분기별 최신(A)은 연속성 RED 1(WFY 면제를 등재하면 YELLOW), FY 일관판(B)은 RED 0. ② ABL·KDB·현대 FY2023 의 owner CSM gold 는 Q1~Q3 원 기초를 Q4 에 강제한 연쇄용이라 Q1~Q3 가 최신으로 움직이면 이유가 사라진다(교체 승인 필요). ③ 롯데 FY2023.4Q 채택은 WFY 0.63% 를 만든다(면제 등재 vs 보류). 모의 결과는 4절.")
W("5. **현대해상 FY2023 은 DART 만으로는 못 닫지만 원천이 raw 에 있다.** 2023.1Q/2Q 보험손익이 −124.5/−838.5억 재작성되는데 LOB 다리의 재작성값은 FY2024 Q1/Q2 DART 필링에 없다. 그러나 `data/ir/FY2024_Q1`·`FY2024_Q2` 의 IR 팩트시트 `(3) UW Income` 전년동기 누계 열의 LOB 보험손익(일반·장기·자동차)이 재작성 item 1(246,045.3 / 415,652.3 mn)과 소수점 아래까지 같고, 이 레그를 쓰면 가교가 0.0 으로 닫히며 게이트 모의가 통과한다(N6c). downloader 가 할 일은 없고 owner 가 IR 팩트시트를 레그 원천으로 허용하는지(2023.4Q 레그는 이미 IR 유래 gold)와 연쇄용 gold 교체를 정해야 한다.")
W("")
W("### READY 25행 일괄 모의 (시나리오 `READY_all`: 471 PL + 55 CSM 칸)")
W("")
W("| 게이트 | 기준선 | READY_all 적용 후 |")
W("|---|---|---|")
W("| master_tables pl_bridge | 3697P / FAIL 23 / NEW 0 | **3755P / FAIL 18 / NEW 0** (해소 5건: KB라이프 2024.1Q, 롯데 2023.2Q, 메리츠 2023.2Q, 한화생명 2023.1Q·2Q) |")
W("| csm_amort_identity | 387P / 5S | 388P / 4S (롯데 2023.1Q PL4 공란 해소) |")
W("| 연속성(csm_continuity) | flagged 2 / RED 0 | flagged 1 / RED 0 (메리츠 FY2023 WFY 면제가 불용이 됨) |")
W("| csm_waterfall · nb_csm | pass 41 · 5/5 | 불변 |")
W("| data_contract | RED 0 / YELLOW 173 | **RED 2 = xlsx 동기화(CSM워터폴·손익분해PL) 뿐**, YELLOW 173 불변(롯데 2023.1Q 줄이 DOCUMENTED → LEDGER_INERT 로 바뀜) |")
W("| live_artifacts | RED 0 | RED 5 = NB_VS_WATERFALL ×4 (메리츠 2023.1Q·2Q, 한화생명 2023.1Q·2Q: NB 마스터 재빌드) + PUBLIC_EXPORT_DRIFT 손익분해PL(publishing 동기화) |")
W("| oci_vs_bs_aoci(YELLOW) | 23 | 29 (정보성) |")
W("")
W("`gates_compare_READY_all.txt`, `gate_digest_all.txt` 에 원 출력이 있다. 단 롯데 2023.1Q 의 contract_notes provenance 블록은 마스터에 없던 블록이라 적재 때 새로 만들어야 한다(안 만들면 MISSING_PROVENANCE · SOURCE_ID_LINEAGE_MISMATCH RED 2건; 후보 provenance 에는 만들어 모의했다).")
W("")

# ---------------------------------------------------------------- 1. ranked plan table
W("## 1. 계획표 (준비 순)")
W("")
W("전체 문장·원천 줄번호·검증·모의 결과는 `plan_table.csv`(46행), 칸 단위 후보와 줄번호 인용은 `ready_cells_ALL.csv`(526칸: PL 471 + CSM 55)에 있다.")
W("")
W("| 순위 | 구분 | 회사 (코드) | 분기 | PL 칸 | CSM 칸 | 가교 잔차(mn) | 시나리오 | 한 줄 요약 |")
W("|---:|---|---|---|---:|---:|---:|---|---|")
BRIEF = {
    ("1", "KR0104"): "구양식 손익계산서 미독해. FY2024 Q1/Q2 전기 누계 열로 48칸 닫힘, CSM 불변",
    ("2", "KR0083"): "CSM 전기 = 마스터(SAME, 라벨링 실패). PL Tier-1 10칸만",
    ("3", "KR0070"): "CSM 전기 = 마스터(SAME, dry-run 오독). OCI 3칸만",
    ("4", "KR0079"): "CSM SAME. 투자손익·OCI Tier-1 11칸, 2023.4Q 단일분기 이음매 11칸",
    ("5", "KR0010"): "손보 LOB 노트 전기 표를 생산 핸들러 그대로 읽음(item1 유도)",
    ("6", "KR0099"): "마스터 오류 3칸(abs() 부호)만, KB라이프 블록 결정과 무관",
    ("7", "KR0003"): "롯데 LOB 전기 표 + CSM 전기 + PL4 를 짝으로",
    ("7.5", "KR0003"): "FY2023 Q1/Q2 형제: LOB·CSM(2023.1Q)·PL4 채택, 2023.4Q 결정(D2)과 독립",
    ("8", "KR0079"): "손익계산서 4줄 + CSM 소폭 재작성(기말 +8.5~8.9억)",
    ("9", "KR0001"): "FY2023 한 판 맞추기(기초 96,376.4). Format-B 둘째 표",
    ("10", "KR0068"): "FY2023 한 판 맞추기(기초 97,629.5). 순이익 +1,139.9/+1,053.7억",
    ("11", "KR0099"): "FY2023 3개 판. 결정 D1",
    ("12", "KR0003"): "FY2023.4Q 채택 시 WFY 0.63%. 결정 D2",
    ("13", "KR0070"): "FY2023 한 판(7,585.3). 연쇄용 gold 교체 승인 D3",
    ("14", "KR0072"): "FY2023 한 판(5,695.9). 연쇄용 gold 교체 승인 D3",
    ("15", "KR0009"): "레그 원천 IR 팩트시트 + 연쇄용 gold. 결정 D3",
}
for (rank, code, scn), rs in groups.items():
    qs = ", ".join(r["quarter"].replace(" (마스터 오류 정정 3칸)", "") for r in rs)
    pl = sum(int(r["pl_value_cells"] or 0) for r in rs)
    cs = sum(int(r["csm_cells"] or 0) for r in rs)
    resid = [num(r["bridge_residual_mn"]) for r in rs if num(r["bridge_residual_mn"]) is not None]
    rmax = max(resid, key=abs) if resid else None
    W(f"| {rank} | {rs[0]['readiness']} | {rs[0]['company']} ({code}) | {qs} | {pl} | {cs} | {'' if rmax is None else f'{rmax:+,.2f}'} | `{scn}` | {BRIEF.get((rank, code), '')} |")
W("")

# ---------------------------------------------------------------- 2. scope answers
W("## 2. 티켓 STEP 2 범위 (1)~(5)에 대한 답")
W("")
W("### (1) 농협생명 KR0104 2023.1Q/2Q")
W("")
W("- **원인**: 위 발견 1. 마스터는 item 1,2,3,7,8,12,15,17–21,25–32 가 null(32칸 중 20칸)이고 16/22/23/24 는 경영공시 PDF 억원 반올림(원 판)이다. FS-API 는 status 013(데이터 없음), HTML Tier-1 추출기는 None(`t1_probe.py`).")
W("- **정확한 칸 목록**: 버킷당 24칸(20칸 null→값 + 16/22/23/24 교체) × 2 = 48칸, 줄번호·항등식 잔차가 `k6_kr0104_cells.txt`/`k6_kr0104_cells.json`, 인용은 `ready_cells_ALL.csv`(code=KR0104). 당기순이익 2023.1Q 1,146.0 → 1,076.7억(−69.3), 2023.2Q 1,415.0 → 1,457.7억(+42.7). 발행사 재작성 효과가 반올림 차이에 섞여 있다.")
W("- **검증**: 독립 XML 재독 vs d5 의 FS-API 전기값 2023.2Q 18/18 일치, 2023.1Q 17/18(항목 16 만 FS-API 값이 인쇄값의 3배라 XML 인쇄값 9,197.9 채택. 원 경영공시 9,200 과 일치). 항등식 7종 잔차 0.000000, 생보 LOB 가교 item1 = 2+15−16 정확히 0.")
W("- **적재 시**: provenance income_statement 블록을 DISCLOSURE → OWNER_GOLD 로 같이 교체한다(안 하면 CONCEPT_MIXED_DISCLOSURE_INTO_DART RED 2건). CSM 은 이미 최신이다. owner 승인 불요(18차 농협생명 2023.3Q 선례).")
W("")
W("### (2) ABL KR0070 2024.4Q 와 2023.4Q")
W("")
W("- **2024.4Q (READY, PL 3칸)**: census 의 「CSM restated items 1–6, residual −14.34억」은 dry-run `별도세그합산` 오독이다(chain_ok False). 별도 감사 첨부 `20260331003080_00760.xml` 제품별 4표의 합산 전기 [8695.4, 2458.4, 341.4, −1231.4, −889.3, 9374.6] = 마스터 2024.4Q(SAME), 당기 [9374.6, …, 9702.5] = 마스터 2025.4Q(`c4_KR0070_FY2025_Q4.txt`: 당기 L16202/L16459/L16716/L16973, 전기 L17230/L17487/L17744/L18001). −14.34억 = 오독 상각 −903.6 대 −889.3 의 차였다. 남는 것은 OCI 3칸(25·26·31)뿐이다. CSM 변경 없음.")
W("- **2023.4Q (NEEDS_OWNER D3)**: PL4 + CSM 채택에 필요한 것은 ① CSM 전기열: FY2024 연간 `20250331001358.xml` 제품 합계 표 L26772(기초 L26808 → 기말 L26872)에 합계가 인쇄돼 있다(분기 비교열도 FY2024 Q1 L20300 / Q2 L20912 / Q3 L20361 에서 줄번호로 재독). FY2023 4분기 모두 최신 기초 7,585.3 이라 한 판(WFY 0)이다. ② PL4 전기열: 연간은 `[구분|당기|전기]` 노트의 전기 열 92,971 = CSM5′ −929.7억, 분기는 `(1) 당반기와 전반기 중 보험영업수익` 의 보험계약마진상각 행 마지막 숫자 셀(Q2 L22569 46,789, Q3 L22013 69,639; `pl4_equality.csv` 3/3). 생산 `extract_tier2_abl`(tier2.py:527)의 캡션 게이트가 분기 양식과 안 맞아 위치만 고치면 된다. ③ owner CSM gold 교체: 2023.4Q 항목 1(7,017.8 → 7,585.3), 4(−1,148.8 → −1,716.3)는 원 필링 값도 최신 값도 아닌 Q1~Q3 원 기초를 Q4 에 강제한 연쇄용(ⓑ)이다. PL gold 2023.1Q 항목 4(22,664 → 22,410)는 원 인쇄값이라 ⓐ 규칙으로 교체한다. 모의(N4): 연속성·워터폴 RED 0, NB_VS_WATERFALL RED 3(ABL 2023.1Q~3Q: NB 재빌드).")
W("")
W("### (3) 푸본현대 KR0083 2024.4Q: CSM 전기열 위치")
W("")
W("- FY2025 사업보고서 `data/dart/FY2025_Q4/raw/KR0083_푸본현대생명보험_20260331002089/20260331002089.xml` 별도 주석에 제품별 3표(유배당·무배당·변액)가 당기말 3개(L48473 / L48861 / L49250) 뒤에 `2) 전기말` 문단(L49637)과 전기 표 3개(L49640 / L50029 / L50418, 기초 CSM L49719-20 등)로 이어진다. 전기 표의 캡션이 `① 유배당보험` 뿐이라 prior 라벨러가 못 잡았다.")
W("- 읽는 법: 문단 마커 `(N) 당기말/전기말` 을 뒤따르는 제품표에 상속(라벨러 소 변경). 6표(당기 3 + 전기 3)를 합산하면 전기 [1658.3, 528.8, 82.9, −675.8, −170.6, 1423.5] = 마스터 2024.4Q(SAME)이다(`c2_KR0083_FY2025_Q4.txt`). 그래서 CSM 은 적재할 것이 없고 PL Tier-1 10칸만 적재한다. 2024.3Q 는 STEP 1 이 이미 적재했으므로 4Q 단일분기 칸이 이음매 없이 이어진다(8절).")
W("")
W("### (4) 닫히지 않은 STAY 22버킷: LOB 다리 전기열 리더가 빠진 것인가")
W("")
W("답: **생보는 아니다(손익계산서 4줄로 닫힘). 손보 3사는 맞고 리더가 작다. 현대해상은 DART 에 원천이 없다.**")
W("")
W("| 버킷(STAY) | LOB 다리가 후속 필링으로 닫히나 | 읽는 표 · 리더 | 잔차 | CSM | 계획표 |")
W("|---|---|---|---:|---|---|")
STAY = [
    ("KR0099", "2023.3Q", "생보: 손익계산서 4줄", "KB라이프", "V1 (D1)"),
    ("KR0099", "2023.4Q", "생보: 손익계산서 4줄", "KB라이프", "V2 (D1)"),
    ("KR0099", "2024.1Q", "생보: 손익계산서 4줄 + 마스터 오류 3칸(abs())", "KB라이프", "최신 (D1)"),
    ("KR0099", "2024.2Q", "생보: 손익계산서 4줄", "KB라이프", "최신 (D1)"),
    ("KR0099", "2024.3Q", "생보: 손익계산서 4줄", "KB라이프", "최신 (D1)"),
    ("KR0010", "2023.4Q", "손보: `(N) 당기와 전기 중 보험손익의 상세내역` 전기 표 L65978 · `extract_tier2_kb` item1 유도", "KB손보", "불변"),
    ("KR0010", "2024.1Q", "손보: FY2025_Q1 L36148", "KB손보", "불변"),
    ("KR0010", "2024.2Q", "손보: FY2025_Q2 L39399", "KB손보", "불변"),
    ("KR0010", "2024.3Q", "손보: FY2025_Q3 L33735", "KB손보", "불변"),
    ("KR0003", "2023.4Q", "손보: FY2024_Q4 L25326 · 롯데 bycontent 둘째 표", "롯데", "FY2024 연간 기초 16,669.0 (D2)"),
    ("KR0003", "2024.1Q", "손보: FY2025_Q1 L20090 · bycontent 둘째 표", "롯데", "최신 (23,860.8 기초)"),
    ("KR0003", "2024.2Q", "손보: FY2025_Q2 split 8표 L58037~L61879 · 마커 이후 연속 LOB 표만", "롯데", "최신"),
    ("KR0003", "2024.3Q", "손보: FY2025_Q3 split 8표 L32050~L34035", "롯데", "최신"),
    ("KR0079", "2023.4Q", "생보: 손익계산서 4줄", "미래에셋", "SAME"),
    ("KR0079", "2024.1Q", "생보: 손익계산서 4줄", "미래에셋", "행블록 분할 합산 (+8.9억)"),
    ("KR0079", "2024.2Q", "생보: 손익계산서 4줄", "미래에셋", "넓은 롤포워드 합산 (+8.7억)"),
    ("KR0079", "2024.3Q", "생보: 손익계산서 4줄", "미래에셋", "넓은 롤포워드 합산 (+8.5억)"),
    ("KR0070", "2023.3Q", "생보: 손익계산서 4줄", "ABL", "최신 7,585.3 (D3)"),
    ("KR0070", "2023.4Q", "생보: 손익계산서 4줄", "ABL", "최신 7,585.3 (D3)"),
    ("KR0072", "2023.3Q", "생보: 손익계산서 4줄", "KDB생명", "최신 5,695.9 (D3)"),
    ("KR0083", "2024.4Q", "생보: 손익계산서 4줄", "푸본현대", "SAME"),
    ("KR0009", "2023.4Q", "손보: 레그는 owner IR gold. 재작성 item1 차 +1.0억이라 가교 −98 mn 이 허용오차(0.1%) 안", "현대해상", "최신 83,515.4 (D3)"),
]
byk = {(r["code"], r["quarter"].replace(" (마스터 오류 정정 3칸)", "")): r for r in rows if "마스터 오류" not in r["quarter"]}
for code, q, how, co, csm in STAY:
    r = byk.get((code, q))
    resid = num(r["bridge_residual_mn"]) if r else None
    W(f"| {co} {q} | 예 | {how} | {'' if resid is None else f'{resid:+,.2f}'} | {csm} | {r['readiness'] if r else ''} (`{r['scenario'] if r else ''}`) |")
W("")
W("프로토타입(전부 읽기 전용, 같은 필링 재현으로 충실도 확인 후 전기열 적용): `p_kb.py`/`kb_cands.py`(KB손보 4/4 재현 OK), `lotte_lib.py`+`p_lotte_run.py`(롯데 6분기), `p_meritz_lib.py`+`p_meritz.py`, `p_lifeold.py`(KDB), `p_kblife.py`, `p_hanwha.py`, `p_abl.py`, `p_hyundai.py`(현대해상: 전분기 LOB 분해 표 없음 확인), `l1_bridge_scan.py`(census 104버킷 전수의 마스터 레그 vs 후속 손익계산서 레그).")
W("")
W("### (5) 같은 뿌리의 단일분기 어긋남 4사와 이중 재작성 3사")
W("")
W("각 필링이 인쇄한 판의 전수는 `vintage_table.md`/`vintage_table.csv`(9사 × FY2023·2024 × 4분기, rcept 번호, 원 판 vs 후속 비교열, 연내 편차 WFY, FY 경계 연속성). 요약:")
W("")
W("| 회사 | FY2023 판 | FY2024 판 | 기대된 RED | 실측 | 계획표 순위 |")
W("|---|---|---|---|---|---|")
W("| 메리츠화재 | Q1·Q2 원 판(기초 100,383.8), Q3·Q4 최신(96,376.4, 2026-10-12 채택). FY2024 Q1/Q2 비교열은 96,376.4 | 한 판(104,687.3) | 단일분기 어긋남 | 채택 후 FY2023 한 판, WFY 면제 불용 | 순위 9 (READY) |")
W("| 한화생명 | Q1·Q2 원 판(96,679.3), Q3·Q4 97,629.5. FY2024 Q1~Q3 비교열 97,629.5 | 한 판(92,384.9) | 단일분기 어긋남 | 채택 후 한 판 | 순위 10 (READY) |")
W("| KB라이프 | V0 31,201.3 ×3 / V1 31,327.6(Q4 원본). 비교열: FY2024 Q1~Q3 = V1, FY2024 연간 = V2 33,595.7 → 31,798.2 | 원 30,176.4 ×4 / 최신 31,798.3 ×4 | 연속성 RED | 방식에 따라 RED 1(A) · 0(B) · 4(A′) | 순위 11 (NEEDS_OWNER, D1) |")
W("| 롯데손보 | Q1~Q3 16,774.4, 연간 비교열(FY2024 Q4) 16,669.0 | 원: Q1~Q3 23,966.2 / Q4 23,860.8. FY2025 비교열 23,860.8 ×4 = 마스터 Q4(SAME) | 연속성 RED | FY2024 Q1~Q3 채택(순위 7)은 RED 0. FY2023.4Q 채택(D2)이 WFY 0.63% | 순위 7 · 7.5 (READY), 12 (NEEDS_OWNER, D2) |")
W("| ABL | 원 7,017.8 ×4 (Q4 는 gold 로 강제). 모든 FY2024 비교열 7,585.3 | 한 판(8,695.4, SAME) | 연속성 RED | **0건** (한 번만 재작성, FY2023 4분기 비교열 일치) | 순위 13 (NEEDS_OWNER, D3) |")
W("")
W("이중 재작성으로 지목된 3사 중 ABL 은 한 번만 재작성됐고 롯데는 연간 비교열만 한 번 더 어긋난다(진짜 이중은 KB라이프 하나). 그래서 연속성 RED 기대치는 3이 아니라 2다(KB라이프 6.75% · 롯데 0.63%이며 롯데는 연속성 스크립트 1% 기준으로는 RED 가 아니고 master_tables WFY 0.5% 기준에서만 걸린다).")
W("")

# ---------------------------------------------------------------- 3. cards
W("## 3. 계획표 상세 (그룹별 카드)")
W("")
for (rank, code, scn), rs in groups.items():
    r0 = rs[0]
    qs = ", ".join(r["quarter"].replace(" (마스터 오류 정정 3칸)", "") for r in rs)
    W(f"### 순위 {rank}. {r0['company']} ({code}) {qs} · {r0['readiness']} · `{scn}`")
    W("")
    W(f"- **센서스(d_census)**: {r0['census(d_census)']}")
    W(f"- **원인**: {r0['e20_cause']}")
    W(f"- **원천 필링·표(줄번호)**: {r0['source_filing_and_tables']}")
    W(f"- **리더 변경**: {r0['reader_change']}")
    W(f"- **검증**: {r0['verified_on']}")
    W(f"- **게이트 모의**: {r0['gate_simulation']}")
    W(f"- **결정·비고**: {r0['decision_or_blocker']}")
    for r in rs:
        extra = []
        if r["headline_delta_eok"]:
            extra.append("화면(억원) " + r["headline_delta_eok"])
        if r["csm_closing_delta_eok"]:
            extra.append("CSM 기말 " + r["csm_closing_delta_eok"])
        W(f"  - {r['quarter']}: PL {r['pl_value_cells']}칸 · CSM {r['csm_cells']}칸 · 가교 잔차 {num(r['bridge_residual_mn']) if num(r['bridge_residual_mn']) is not None else '-'} mn" + ("  /  " + " ; ".join(extra) if extra else ""))
    W("")

# ---------------------------------------------------------------- 4. decision tables
W("## 4. owner 결정표 (고르지 않았다. 모의 결과만 적는다)")
W("")
W("owner 규칙(2026-10-12): 「최신 공시의 전기·전년동기 비교열 우선, 단 검증 단위(회사×FY 블록, 짝 항목 포함)까지 산술이 닫힐 때만」. 아래 표의 RED/FAIL 수치는 모두 게이트 실행 결과(`gates_compare_*.txt`, `gate_digest_all.txt`)이고, 「WFY 면제」 모의는 `validate_master_tables.py`·`validate_csm_continuity.py` 의 샌드박스 사본에 WFY_EXCEPTIONS 두 줄을 더한 것이다(`exc_make.py`, `g_exc_ALL_latest/`; 저장소 불변).")
W("")
W("### D1. KB라이프 FY2023 (8버킷): 분기별 최신 vs FY 일관판")
W("")
W("판의 정의: V0 = FY2023 Q1~Q3 원 필링 기초 31,201.3. V1 = FY2023 연간 원본 = FY2024 Q1~Q3 비교열 기초 31,327.6(기말 30,176.4). V2 = FY2024 연간 비교열 기초 33,595.7 → 기말 31,798.2 (Q1~Q3 의 V2 는 어느 필링에도 인쇄되지 않았다). FY2024 는 원 30,176.4, 최신 31,798.3 (FY2025 Q1~Q4 비교열 4개 일치). 줄번호: `csm_vector_sources.csv`.")
W("")
W("| 옵션 | 적재 범위 | 칸(PL/CSM) | FY2023 분기별 기초 | 연내 편차 | FY 경계 | 게이트 모의 |")
W("|---|---|---:|---|---:|---|---|")
W("| C 현 상태 | 없음 | 0/0 | 31,201.3 ×3 / 31,327.6 | 0.40% | 2023.4Q 기말 30,176.4 = 2024.1Q 기초 | 기준선 (KB라이프 2024.1Q +1,136 FAIL 은 R0 로 따로 해소 가능) |")
W("| B FY2023 Q1~Q3 만 (V1) | KB라이프 2023.1Q~3Q | 61/15 | 31,327.6 ×4 | 0% | 연속 | **RED 0**(xlsx 제외) · pl_bridge +10P · FAIL 23 불변 · 연속성 불변 (`N2_KBlife_B`) |")
W("| A 분기별 최신 전부 | 8버킷 | 134/37 | 31,327.6 ×3 / 33,595.7 | 6.75% | 연속(31,798.2 → 31,798.3) | **연속성 RED 1**(WITHIN_FY_OPENING_DRIFT 6.75% > 1%) + master_tables WFY 1 · pl_bridge FAIL 23→22. (\"KB라이프생명\",\"2023\") 를 WFY_EXCEPTIONS 에 등재하면 RED → YELLOW(EXCEPTED), WFY 0 (샌드박스 모의) (`N1_KBlife_A`) |")
W("| A′ A 에서 2023.4Q 만 제외 | 7버킷 | 117/32 | 31,327.6 ×4 | 0% | 2023.4Q 기말 30,176.4 ≠ 2024.1Q 기초 31,798.3 (Δ+1,622) | **CSM_CONTINUITY_FY_BOUNDARY RED ×4** + data_contract RED 6. 연속성 단절은 면제 불가(owner 2026-06-16) → 선택 불가 (`N3_KBlife_Aprime`) |")
W("")
W("참고(결정이 아님): 닫힘의 단위를 「회사×FY 블록의 일관성까지」로 읽으면 B(+FY2024 보류)가 규칙에 그대로 맞고, A 는 문서화된 소급재작성 면제 등재가 있어야 통과한다. 어느 쪽이든 FY2023 Q1~Q3 의 V2 는 존재하지 않아 「FY 단위 단일 판」은 B 의 V1 뿐이다. KB라이프 2024.1Q 마스터 오류 3칸(R0)은 D1 과 무관하게 먼저 적재할 수 있다.")
W("")
W("### D2. 롯데 FY2023.4Q (19 PL + 5 CSM): 채택 vs 보류")
W("")
W("| 옵션 | 내용 | 게이트 모의 |")
W("|---|---|---|")
W("| 보류 | FY2023 Q4 를 원 판으로 둔다 (기초 16,774.4 / 기말 23,966.2). FY2024 Q1~Q3 는 READY(R2)로 채택 → 기초 23,860.8 | FY2023→FY2024 경계 Δ105.4(0.44% < 0.5%)라 CONT 통과, 단 105.4억 이음매가 화면에 남는다. WFY 0 |")
W("| 채택 | 2023.4Q 채택(기초 16,669.0, 기말 23,860.8) | FY2023 기초 16,774.4 ×3 / 16,669.0 → **master_tables WFY 1(0.63% > 0.5%)**. 연속성 스크립트(1% 기준)는 RED 0. (\"롯데손해보험\",\"2023\") WFY 면제 등재 시 WFYEX 로 바뀜(샌드박스). 경계 연속은 정확히 0 (`N7_Lotte_FY2023Q4`) |")
W("")
W("롯데 FY2023.1Q/2Q 형제(READY 7.5)는 이 결정과 독립이다(Q1~Q3 비교열 기초는 16,774.4 그대로).")
W("")
W("### D3. 연쇄용 owner CSM gold 를 가진 ABL · KDB생명 · 현대해상 FY2023")
W("")
W("세 회사 모두 FY2023 4분기의 최신 비교열 기초가 한 판이라(ABL 7,585.3 · KDB 5,695.9 · 현대 83,515.4) 채택하면 WFY 0 이다. 남은 장애는 owner CSM gold 가 Q1~Q3 원 기초를 Q4 에 강제한 연쇄용(ⓑ)이라는 점이다. Q1~Q3 가 최신으로 움직이면 gold 의 존재 이유가 사라진다. gold 목록은 `gold_cells_replaced.csv`.")
W("")
W("| 회사 | 교체되는 gold | 분류 | 화면 변화(CSM 기말, 억원) | 게이트 모의 |")
W("|---|---|---|---|---|")
W("| ABL (`N4_ABL_FY2023`, 75/20칸) | CSM 2023.4Q 항목 1(7,017.8 → 7,585.3)·4(−1,148.8 → −1,716.3); PL 2023.1Q 항목 4(22,664 → 22,410) | ⓑ 연쇄 2 · ⓐ 1 | 2023.1Q +348.2 / 2Q −173.9 / **3Q −1,292.4(−13.3%)** / 4Q 0 | 연속성·워터폴 RED 0 · NB_VS_WATERFALL RED 3(ABL 2023.1Q~3Q) · pl_bridge +6P |")
W("| KDB생명 (`N5_KDB_FY2023`, 70/20칸) | CSM 2023.1Q 4·5·6, 2023.2Q 4·5, 2023.4Q 1·4; PL 2023.2Q·3Q 항목 4·7 | ⓑ 연쇄 2 · ⓐ 9 | 2023.1Q +410.9 / 2Q +459.7 / 3Q +506.0 / 4Q 0 | 새 RED/FAIL 0 (xlsx 제외) · OCI_VS_BS_AOCI YELLOW +1 |")
W("| 현대해상 (`N6c_HD_FY2023_IRlegs`, 58/18칸) | CSM 2023.3Q 1·4, 2023.4Q 1·4; PL 2023.4Q 항목 16(반올림 0.03) | ⓑ 연쇄 4 · ⓐ 1 | 2023.1Q **−4,675.4(−5.2%)** / 2Q **−5,376.5(−5.9%)** / 3Q 0 / 4Q −1.0 | pl_bridge 3707P/23F(NEW 0) · RED 0→2(xlsx 뿐) · NB_VS_WATERFALL RED 2(현대 2023.1Q/2Q) · 연속성·워터폴 불변 |")
W("")
W("현대해상만 추가 결정이 하나 더 있다. LOB 다리(2/13/14)의 재작성값이 DART FY2024 Q1/Q2 필링에 없어 레그를 DART 원 판대로 둔 채 보험손익만 채택하면(N6) 가교가 깨진다(신규 FAIL 2건: 2023.1Q +8,429.8 mn, 2023.2Q +75,080.6 mn). IR 팩트시트(raw 에 있음)의 전년동기 누계 LOB 보험손익을 레그로 쓰면 0.0 으로 닫힌다(N6c).")
W("")
W("| 현대해상 옵션 | 내용 | 게이트 모의 |")
W("|---|---|---|")
W("| X 보류 | 현 상태 유지 | 기준선 |")
W("| Y IR 레그 허용 후 전체 채택 (`N6c`) | PL 58 + CSM 18칸, 레그 = IR 팩트시트 `(3) UW Income` L11/L26/L30 | 위 표. 2023.4Q 레그가 이미 IR 유래 owner gold 라 선례가 있다 |")
W("| Z CSM + PL4 만 (`N6b`) | CSM 18 + PL4 3칸, PL Tier-1 원 판 유지 | xlsx 제외 RED 0 · pl_bridge 불변 · NB_VS_WATERFALL RED 2. 보험손익이 원 판으로 남아 CSM 최신 판과 한 FY 안에서 판이 섞인다 |")
W("| (비선택) DART 레그 그대로 전체 채택 (`N6`) | | **신규 FAIL 2** → 불가 |")
W("")

# ---------------------------------------------------------------- 5. gate table
W("## 5. 게이트 시뮬레이션 전체표")
W("")
W("기준선 `g_base`: pl_bridge 3697P/FAIL 23/NEW 0 · csm_amort_identity 387P/5S · plausibility 0dup/1spike/1cont/0wfy · data_contract RED 0/YELLOW 173 · 연속성 flagged 2/RED 0 · csm_waterfall pass 41 · nb_csm 5/5 · live_artifacts RED 0/YELLOW(기지) 25. 모든 시나리오에서 data_contract 의 RED 2 중 `MASTER_XLSX_DRIFT`(CSM워터폴·손익분해PL)는 publishing 의 xlsx 동기화 몫이고, `PUBLIC_EXPORT_DRIFT`도 마찬가지다.")
W("")
W("| 시나리오 | 구성 | PL/CSM 칸 | pl_bridge | 연속성·WFY | data_contract RED | live_artifacts RED |")
W("|---|---|---:|---|---|---:|---|")
W("| R0 | KB라이프 2024.1Q 마스터 오류 | 3/0 | 3698P / FAIL 22 | 불변 | 1 (xlsx) | 0 |")
W("| R1 | 농협 ×2 · 푸본 · ABL 2024.4Q · 미래에셋 2023.4Q · KB손보 4 | 136/0 | 3715P / FAIL 23 | 불변 | 1 (xlsx) | 0 |")
W("| R1b | KB손보 2023.1Q/2Q | 50/0 | 3701P / FAIL 23 | 불변 | 1 | 0 |")
W("| R2 | 롯데 2024.1Q~3Q · 미래에셋 2024.1Q~3Q · 메리츠 ×2 · 한화 ×3 | 222/53 | 3718P / FAIL 20 | flagged 1 (메리츠 면제 불용) | 2 | 4 (NB ×4) |")
W("| R2b | 롯데 2023.1Q/2Q | 60/2 | 3711P / FAIL 22 | 불변 | 2 | 1 (export) |")
W("| **READY_all** | R0+R1+R1b+R2+R2b | **471/55** | **3755P / FAIL 18 / NEW 0** | flagged 1 · RED 0 | 2 (xlsx) | 5 (NB ×4 + export) |")
W("| N1 (D1-A) | KB라이프 8버킷 | 134/37 | 3711P / FAIL 22 | **continuity RED 1**, WFY 1 | 2 | 0 |")
W("| N2 (D1-B) | KB라이프 2023.1Q~3Q | 61/15 | 3707P / FAIL 23 | 불변 | 2 | 0 |")
W("| N3 (D1-A′) | KB라이프 A 에서 2023.4Q 제외 | 117/32 | 3711P / FAIL 22 | **CONT 1→5**, data_contract CSM_CONTINUITY_FY_BOUNDARY ×4 | 6 | 0 |")
W("| N4 (D3) | ABL FY2023 | 75/20 | 3703P / FAIL 23 | 불변 | 2 | 3 (NB ×3) |")
W("| N5 (D3) | KDB FY2023 | 70/20 | 3703P / FAIL 23 | 불변 | 2 | 0 |")
W("| N6 (비선택) | 현대 FY2023, DART 레그 | 52/18 | 3705P / FAIL 25 / **NEW 2** | 불변 | 2 | 2 (NB ×2) |")
W("| N6b (D3-Z) | 현대 CSM + PL4 만 | 3/18 | 3697P / FAIL 23 | 불변 | 2 | 2 (NB ×2) |")
W("| N6c (D3-Y) | 현대 FY2023, IR 레그 | 58/18 | 3707P / FAIL 23 / NEW 0 | 불변 | 2 | 2 (NB ×2) |")
W("| N7 (D2) | 롯데 2023.4Q | 19/5 | 불변 | **WFY 1** (0.63%) | 2 | 0 |")
W("| ALL_latest | 현대 제외 전부(READY 전체 + D1-A + D2 + ABL + KDB) | 706/135 | 3766P / FAIL 19 | WFY 2, **continuity RED 1** | 2 | 7 (NB ×7) |")
W("| ALL_latest + WFY 면제 2줄 (샌드박스) | 위 + KB라이프 2023, 롯데 2023 | 706/135 | 3766P / FAIL 19 | WFYEX 2, continuity RED 0 (KB라이프 YELLOW EXCEPTED) | - | - |")
W("")

# ---------------------------------------------------------------- 6. reader inventory
W("## 6. 리더 변경 목록 (코드 위치 · 크기 · 검증)")
W("")
W("| # | 대상 | 코드 위치 | 변경 | 크기 | 검증 |")
W("|---:|---|---|---|---|---|")
W("| 1 | KB손보 LOB 노트 전기 표 | `scripts/pl_breakdown/companies.py:118 extract_tier2_kb(tables, item1=None)` | 후속 필링 표에 item1 = 후속 전기 item1 로 호출하면 그 표를 스스로 고른다 → 드라이버의 prior 인자 전달 | ~5줄 | `p_kb.py`: 같은 필링 재현 4/4, 전기열 합 − item1 = 0/0/−1/0 |")
W("| 2 | 롯데 LOB 전기 표 | `companies.py:2686 extract_tier2_lotte` (+ `_extract_tier2_lotte_combined`·`_combined_bycontent`·`_split`) | 세 레이아웃에 prior 스위치(둘째 표 / 전반기 마커 뒤 연속 LOB 표만) | <100줄(프로토타입 `lotte_lib.py`) | `p_lotte_run.py` 6분기 잔차 −0.75/−0.53/0/0 및 0.40/−0.43. 2023.1Q/2Q 는 원 필링 쪽 레이아웃이 안 읽히는(`layout orig=None`) 분기라 전기열이 유일한 경로 |")
W("| 3 | 메리츠 LOB 전기 표 | `scripts/pl_breakdown/tier2.py:176 extract_tier2_sonbo_structured` | Format-B 상세내역 둘째(전기) 표 선택. item 16 부호 보존 필수(2023.1Q 음수) | 소(`p_meritz_lib.py`) | 잔차 +0.5/−1.2 mn, PL4 256,695/515,014 = CSM5′ |")
W("| 4 | OLD 생보(KDB 등) PL4 전기 | `companies.py:3389 _oll_num` | prior 인자(pair: ns[3], single: ns[1]) | 4줄 | `p_lifeold.py` PL4 4/4 |")
W("| 5 | KB라이프 | `companies.py:3288 extract_tier2_kblife` | **3347행 `out[\"_jang_rerev\"] = abs(jrr)` → `jrr`** (재보험수익은 음수 가능, 2024.1Q −568 이 +568 로 뒤집혀 item 8 −832 · 가교 +1,136). `_jang_recost` 의 abs 는 비용이라 유지 | 1줄 | R0 후보와 같은 필링 재현. 코드를 고치면 PL 골든(`RUN_PL_GOLDEN=1`)이 바뀌는 셀을 확인해야 하므로 마스터 3칸 직접 적재가 더 안전 |")
W("| 6 | KB라이프 PL4/CSM 전기 표 | `extract_tier2_kblife` 의 전기/twin 블록 | `p_kblife.py` | 소 | PL4 5/5 |")
W("| 7 | ABL PL4 분기 prior | `tier2.py:527 extract_tier2_abl(tables, quarter=None)` | 분기 양식의 캡션 게이트 위치 수정 | 소 | `pl4_equality.csv` 3/3 |")
W("| 8 | CSM prior 라벨러(dry-run `prior_csm.label_blocks`, e19 가 쓰는 것) | `data/_derived/ifrs17_latest_comparative_precedence_dryrun_20261012/prior_csm.py` | (a) 문단 마커 `(N) 당기말/전기말` 상속(푸본) (b) 짧은 캡션 `(2) 전기` 를 직전 `(1) 당기` 헤더와 같으면 prior 로 상속(현대) (c) 표 안 마커 행 이후를 prior 로 쪼개기(미래에셋 FY2025 Q1) (d) annual 에서 chain_ok False 인 `별도세그합산` 모드 폐기(ABL·롯데 2024.4Q 오독 방지) | 소 | `c2`·`c3`·`c4`·`c5` 출력, `v1_csm_verify.py`·`v3_mirae_wide.py`·`v4_meritz_csm.py` 독립 재독 |")
W("| 9 | OCI item 30 이름 폴백 | `build_cands.py` 의 OCI 보정 | 전기열에서 리프(26~30)가 untagged 면 FS-API 가 item 32 로 흡수 → XML 라벨 폴백(KB라이프 2023.3Q 재보험계약자산부채순금융손익 427, FY2024_Q3 L25661) | 소 | 후보에서 OCI 항등식 0 |")
W("| 10 | 현대해상 IR 팩트시트 레그(신규, NEEDS_OWNER) | 신규 | 시트 `(3) UW Income` 블록 아래 첫 `보 험 손 익` 행의 마지막 숫자 셀 = 전년동기 누계 | 25줄(`w4_hd_ir_legs.py`) | 레그 합 = 재작성 item1 차 0 |")
W("")

# ---------------------------------------------------------------- 7. apply notes
W("## 7. 적재 때 지켜야 할 것")
W("")
W("1. **영속 경로**: PL 은 `data/_gold/user_pl_cells.json`, CSM 은 `user_csm_cells.json` 에 셀 단위 set(e19 의 `apply/e19_apply.py` 방식). 단일분기(`값_당분기`)는 YTD 에서 파생되지만 연도말만 재작성되는 곳은 이음매다(미래에셋 2023.4Q 11칸 등): null_dangi/set_dangi 로 처리(`scenario_stats.txt` 의 auto-follow 수치, `e19_verify_seams.py` 참고).")
W("2. **gold 겹침**: `gold_cells_replaced.csv` (31칸: 시나리오·칸·gold 값·builder 값·후보). READY 에서 교체되는 gold 는 KB손보 항목 16 ×3(2024.2Q 의 192,135 → 192,136 은 1 mn 재인쇄 차이라 제외 권고), 메리츠 항목 16 ×2, 한화 2023.1Q 항목 20·2023.2Q 항목 21, 롯데 2023.2Q 항목 19, 롯데 2023.1Q CSM 항목 4·6 이고 전부 원 인쇄값 = gold 인 ⓐ 규칙이다. gold 칸 수가 바뀌면 `tests/test_rule_coverage_manifest.py::GOLD_OVERLAY_CENSUS` 도 같이 고쳐야 푸시 훅이 통과한다.")
W("3. **provenance**: income_statement 블록 DISCLOSURE → OWNER_GOLD 교체(농협 2023.1Q/2Q 등), 롯데 2023.1Q contract_notes 블록 신규. e19 의 샌드박스 emitter 복사본(`emit_pl_provenance_sandbox_copy.py`)으로 생성한다(손으로 쓰지 않는다).")
W("4. **NB_CSM_multiple 마스터** 4행 재빌드(메리츠 2023.1Q·2Q, 한화 2023.1Q·2Q; D3 를 채택하면 ABL 3행·현대 2행 추가): `scripts/build_nb_csm_multiple.py` 통짜 실행은 위험하니 개별 행만 비교 후 적재.")
W("5. **기준선·면제 정리**: `data/_gold/pl_bridge_baseline.json` 해소 FAIL 5줄(KB라이프 2024.1Q, 롯데 2023.2Q, 메리츠 2023.2Q, 한화 2023.1Q·2Q), `validate_master_tables.WFY_EXCEPTIONS` 의 메리츠·한화 FY2023 항목 불용, `data/_gold/pl_csm_amort_missing_ledger.json` 롯데 2023.1Q 줄 불용(게이트가 LEDGER_INERT YELLOW 로 알려 줌).")
W("6. **xlsx·public_exports**: 바뀐 시트(CSM워터폴·손익분해PL)만 `sync_master_xlsx_sheet.py` (publishing 몫). 통짜 재생성 금지.")
W("7. **골든·테스트**: 마스터만 적재하는 경로(e19 방식)면 PL 골든 영향이 없다. 핸들러 코드를 고치면 `RUN_PL_GOLDEN=1 tests/test_pl_breakdown_golden.py`(약 95초)로 바뀌는 셀을 확인하고 이유를 커밋에 남긴다. `tests/fixtures/master_tables_golden.json` 의 SUMMARY 지문이 pl_bridge 합계를 포함하므로 적재 뒤 `--update` 재생성이 필요하다.")
W("")

# ---------------------------------------------------------------- 8. STEP 1 interaction
W("## 8. STEP 1 과의 상호작용 (커밋 5419a817 · 2d14e4e5 반영 후 재측정)")
W("")
W("STEP 1 이 시작 스냅샷 이후 바꾼 것: PL 118칸 / 29버킷(YTD 값 84칸 / 21버킷, 나머지는 단일분기 파생), CSM 0칸. **내 후보와 YTD 값 칸 충돌 0** (`step1_value_collision.py`). 겹치는 버킷은 푸본현대 2024.4Q 하나이고 그 단일분기 칸 8개(항목 17·19·20·22·23·24·25·27)는 STEP 1 이 2024.3Q 를 적재하면서 비어 있다(null_dangi). 내 푸본 2024.4Q 적재가 이 칸들을 복구하므로 같은 순서(2024.3Q 가 먼저, 2024.4Q 가 나중)면 이음매가 없다. 내 후보의 `old` 값은 스냅샷 기준이지만, 후보 982칸(READY 526 + NEEDS_OWNER 456) 전부를 현재 라이브 마스터(HEAD)와 대조하니 `old` 가 전부 일치한다(`final_old_vs_live.txt`, 차이 0). 단 단일분기(`값_당분기`) 칸은 YTD 에서 다시 파생되므로 적용 직전에 `e19_diff_vs_head.py` 방식으로 다시 비교한다. 참고: 스냅샷은 세션 시작 시점의 작업 트리(STEP 1 적재가 진행 중이던 중간 상태)라 어느 커밋과도 해시가 같지 않다.")
W("")

# ---------------------------------------------------------------- 9. limits
W("## 9. 한계와 미검증")
W("")
W("- **독립 재독 수준**: READY CSM 55칸 전부 독립 리더로 후속 필링에서 다시 읽었다(롯데·한화·KB라이프·ABL·KDB·현대: 단일 표에 합계가 인쇄돼 줄번호 인용 / 메리츠: 3개 CSM 열 합 / 미래에셋: Q1 행블록 합·Q2/Q3 넓은 롤포워드 합 / 푸본·ABL 2024.4Q·미래에셋 2023.4Q: SAME). 줄번호는 `ready_csm_cells.csv`, `csm_vector_sources.csv`, `v1_csm_verify_*.txt`, `v3_mirae_wide.txt`, `v4_meritz_csm.txt`.")
W("- **PL4 독립 대조**: `pl4_equality.csv` 21/21(노트의 보험계약마진상각 = CSM5′ ±0.05억) + 롯데 2023.1Q 39,284 = CSM5′ −392.8. 미래에셋은 CSM 표와 보험수익 주석이 같은 셀이라 독립성이 없다. 게이트 모의의 PL4 는 CSM5 에서 파생했으므로(그래서 csm_amort_identity 가 항상 닫힌다) 증거는 이 독립 대조다.")
W("- **후보 provenance 단순화**: 모의용 provenance 는 OWNER_GOLD 일괄 표기라 실제 emitter 출력과 블록 구성이 다를 수 있다. data_contract 가 보는 것은 파일 존재·계보 등록이라 결과는 같지만 적재 때 실제 emitter 로 다시 확인한다.")
W("- **범위 밖(측정 안 함)**: `d_census_addl.csv` 의 STAY 중 코리안리 5(2023.4Q·2024.2Q·2024.3Q·2024.4Q·2025.1Q), 흥국생명 2023.1Q·2024.4Q, 삼성생명 2024.4Q, KDB 2025.2Q 는 이 티켓 STEP 2 의 (1)~(5)에 없어 건드리지 않았다(`stay_mapping.csv` 에 「not in plan」으로 표시). 코리안리는 CSM gold 가 6항목 전부 겹쳐 별도 판단이 필요해 보인다.")
W("- **KB손보 2024.2Q 항목 16**: gold 192,135 → 후보 192,136(1 mn 재인쇄 차이)은 반올림 규칙상 제외를 권한다. 계획표 칸 수에는 포함돼 있다.")
W("- **화면 숫자 변화가 큰 READY**: 메리츠 2023.1Q/2Q CSM 기말 −3,579.1/−3,668.8억(−3.6%), 한화생명 2023.1Q/2Q 당기순이익 +1,139.9/+1,053.7억(+32%/+21%), 롯데 2023.1Q CSM 기말 +507.4억. 모두 owner 규칙(2026-10-12)이 허용하는 최신 비교열 채택이지만 화면 숫자 변경이므로 owner 에게 알려야 한다.")
W("")

# ---------------------------------------------------------------- 10. reproduction
W("## 10. 산출물과 재현")
W("")
W("`INDEX.txt` 에 파일 지도와 재현 순서가 있다. 핵심: `plan_table.csv`(46행) · `PLAN.md`(이 문서) · `ready_cells_ALL.csv`(526칸) · `ready_csm_cells.csv` · `csm_vector_sources.csv` · `vintage_table.md` · `gold_cells_replaced.csv` · `stay_mapping.csv` · `gate_digest_all.txt` · `gates_compare_*.txt`.")
W("")

open(H + "PLAN.md", "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
print("PLAN.md lines", len(out))
