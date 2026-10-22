# -*- coding: utf-8 -*-
"""plan_build: assemble plan_table.csv (one row per bucket) from the scenario candidate files (cands_*.json), the gate digests and the static findings below.  READ-ONLY.
Run after build_cands.py / gates_scn.sh for every scenario."""
import csv
import json
import sys
from collections import defaultdict

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
pl, names, inames = M.load_pl()


def C(scn):
    return json.loads((M.MEASURE / f"cands_{scn}.json").read_text(encoding="utf-8"))


SC = {s: C(s) for s in ("R0_KBlife_2024Q1_fix", "R1", "R1b_KB_siblings", "R2", "R2b_Lotte_2023_1Q2Q", "N1_KBlife_A", "N2_KBlife_B", "N4_ABL_FY2023", "N5_KDB_FY2023", "N6_HD_FY2023", "N6b_HD_CSM_PL4only", "N6c_HD_FY2023_IRlegs", "N7_Lotte_FY2023Q4")}
csm6 = {}
for s, d in SC.items():
    for c in d["csm_cells"]:
        if c["item"] == 6:
            csm6[(s, c["code"], c["q"])] = (c["old"], c["new"])

# ------------------------------------------------------------------------------------------------------------------------------------------------------------
# bucket -> (scenario, readiness, rank, scope refs, census disposition, e20 cause, source, reader change, verified on, decision / blocker, gate result)
# ------------------------------------------------------------------------------------------------------------------------------------------------------------
GATE = {
    "R1": "R1 9버킷 136칸: RED 0->1(xlsx 손익분해PL 동기화 뿐) · pl_bridge +18P/0 NEW/FAIL 23 불변 · 연속성·워터폴·NB·live_artifacts 불변",
    "R1b_KB_siblings": "R1b 2버킷 50칸: RED 0->1(xlsx) · pl_bridge +4P · 나머지 불변",
    "R0_KBlife_2024Q1_fix": "R0 3칸: RED 0->1(xlsx) · pl_bridge FAIL 23->22 (KB라이프 2024.1Q 보험손익(dual) +1,136 해소)",
    "R2": "R2 11버킷 222+53칸: RED 0->2(xlsx 2시트) · pl_bridge +21P·FAIL 23->20(메리츠 2023.2Q·한화 2023.1Q/2Q 해소)·NEW 0 · 메리츠 FY2023 WFY 면제 소멸 · NB_VS_WATERFALL RED 4(메리츠2·한화2 = NB 마스터 재빌드 필요) · OCI_VS_BS_AOCI YELLOW +4",
    "R2b_Lotte_2023_1Q2Q": "R2b 2버킷 60+2칸: pl_bridge 3697P/23F -> 3711P/22F(롯데 2023.2Q leg-coverage -102,898 해소, NEW 0) · csm_amort_identity 387P/5S -> 388P/4S(2023.1Q PL4 공란 해소, PL_CSM_AMORT_MISSING 등재 1줄 불용) · 연속성·워터폴·NB 불변 · RED 0->2(xlsx 2시트 뿐; 2023.1Q contract_notes provenance 블록은 적재 때 새로 만들어야 하며 만들면 0) · OCI_VS_BS_AOCI YELLOW +2",
    "N1_KBlife_A": "A(8버킷 134+37칸): 연속성 RED 1(FY2023 기초 31,328~33,596, 6.75%) · pl_bridge FAIL 23->22 · xlsx RED 2",
    "N2_KBlife_B": "B(FY2023 Q1~Q3, 61+15칸): RED 0(xlsx 2 제외) · 연속성 불변 · pl_bridge +10P",
    "N4_ABL_FY2023": "ABL FY2023 4버킷 75+20칸: 연속성·워터폴 RED 0 · xlsx RED 2 · NB_VS_WATERFALL RED 3(ABL 2023.1Q~3Q, NB 재빌드 필요)",
    "N5_KDB_FY2023": "KDB FY2023 4버킷 70+20칸: 새 RED/FAIL 0 (xlsx RED 2 뿐) · OCI_VS_BS_AOCI YELLOW +1",
    "N6_HD_FY2023": "현대 FY2023 4버킷 52+18칸: 신규 FAIL 2(보험손익(dual) 2023.1Q +8,429.8 · 2023.2Q +75,080.6 = LOB 다리 미갱신) · NB RED 2",
    "N6c_HD_FY2023_IRlegs": "현대 FY2023 4버킷 58+18칸(레그 2/13/14 = IR 팩트시트): pl_bridge 3697P/23F -> 3707P/23F(+10P, NEW 0; 레그를 DART 원 판대로 둔 N6 은 NEW FAIL 2) · RED 0->2(xlsx 2시트 뿐) · 연속성·워터폴 불변 · NB_VS_WATERFALL RED 2(현대 2023.1Q/2Q: NB 마스터 재빌드) · OCI_VS_BS_AOCI YELLOW +2",
    "N6b_HD_CSM_PL4only": "대안 N6b(CSM 18칸 + PL4 3칸, PL Tier-1 은 원 판): RED 0->2(xlsx 뿐) · pl_bridge 불변 3697P/23F · NB_VS_WATERFALL RED 2",
    "N7_Lotte_FY2023Q4": "롯데 2023.4Q 단독 19+5칸: WFY 0->1(FY2023 기초 16,774.4 x3 / 16,669.0, 0.63% > 0.5%) · 연속성 스크립트는 1% 미만이라 RED 0",
}

KEYB = {}


def add(code, qs, **kw):
    for q in qs:
        KEYB[(code, q)] = dict(kw)


add("KR0104", ["2023.1Q", "2023.2Q"], scn="R1", ready="READY", rank=1, scope="1", census="STAY: 'bridge already FAIL (-98,612.4 / -191,659.9 mn) and stays FAIL'",
    cause="census 산식 인공물: 마스터에 보험손익·LOB 다리가 비어 있어 -(후속 item1)로 계산됨. 실제 결함 = FY2023 Q1/Q2 DART 구양식('영업수익/영업비용', <TD>) 포괄손익계산서를 Tier-1 이 못 읽음(FS-API status 013 + HTML 추출기 None) -> 32칸 중 20칸 공란, 16/22/23/24 는 경영공시 PDF 억원 반올림(원 판)",
    src="후속 공시 FY2024_Q1 20240514001371.xml 4-2 포괄손익계산서 L5592-6957 (전기 누계 4번째 열) / FY2024_Q2 20240814002115.xml L5706-7074",
    reader="없음(적재는 gold set + provenance 블록 교체, e19 방식). 근본 수정은 tier1 가 '영업수익/영업비용' 양식에서 보험수익·재보험수익·보험서비스비용·재보험비용·사업비를 읽어 item1=그 합으로 파생(소) — 불요",
    ver="k6_kr0104_cells.txt: 독립 XML 재독 vs FS-API 전기값 2023.2Q 18/18 일치 · 2023.1Q 17/18(항목 16 만 FS-API 값이 인쇄값의 3배라 XML 인쇄값 9,197.9 채택 — 원 경영공시 9,200 과 일치), 항등식 7종 잔차 0.000000, 생보 LOB 가교 item1=2+15-16 정확히 0",
    dec="owner 승인 불요(18차 농협생명 2023.3Q 선례와 같은 방식). 2023.1Q/2Q CSM 은 이미 최신(불변). 적재 시 provenance income_statement 블록을 DISCLOSURE->OWNER_GOLD 로 같이 교체(안 하면 CONCEPT_MIXED_DISCLOSURE_INTO_DART RED 2건)")
add("KR0083", ["2024.4Q"], scn="R1", ready="READY", rank=2, scope="3,4", census="STAY: 'CSM prior column could not be extracted' (UNVERIFIED)",
    cause="CSM 전기열이 없는 것이 아니라 라벨링 실패: FY2025 사업보고서 별도 주석에 제품별 3표(유배당/무배당/변액)가 당기말 3개 + 전기말 3개로 이어지는데 '2) 전기말' 문단이 하위 캡션 규칙에 먹혀 표 캡션이 '① 유배당보험' 뿐이라 prior 로 안 잡힘. 전기 벡터를 합산하면 [1658.3,528.8,82.9,-675.8,-170.6,1423.5] = 마스터 2024.4Q (SAME) -> CSM 변경 없음, PL 만 적재",
    src="FY2025_Q4 20260331002089.xml 별도 주석: 당기 L48473/L48861/L49250, '2) 전기말' 문단 L49637, 전기 표 L49640(유배당)/L50029(무배당)/L50418(변액) (기초 CSM L49719-20 등, 합 c2_KR0083_FY2025_Q4.txt); 손익계산서 L35083-35454",
    reader="CSM 적재 불필요. (선택) dry-run prior_csm.label_blocks 에 '문단 마커(N) 당기말/전기말' 상속 규칙 추가 — 소",
    ver="c2_csm_product_tables.py: 6표 합산 prior == master 6항목; life_cands 10칸 항등식 0",
    dec="2024.3Q(STEP 1, gold 27 교체)와 같이 적재해야 단일분기 이음매가 없다")
add("KR0070", ["2024.4Q"], scn="R1", ready="READY", rank=3, scope="2", census="ADDL_CSM_ONLY: 'CSM restated items 1-6, PL4 not read, residual -14.34 eok' (STAY)",
    cause="dry-run 리더 오독(자체 chain_ok=False): '별도세그합산' 이 연결/별도·당기/전기를 섞어 [9287.7..10070.9] 를 만듦. 별도 감사 첨부 _00760 의 제품별 4표 합산 = 전기 [8695.4,2458.4,341.4,-1231.4,-889.3,9374.6] == 마스터(SAME), 당기 [9374.6,...,9702.5] == 마스터 2025.4Q. -14.34억 = 오독 상각 -903.6 대 -889.3 의 차. 남는 것은 OCI 3칸(25,26,31)뿐",
    src="FY2025_Q4 20260331003080_00760.xml 당기 L16202/L16459/L16716/L16973, 전기 L17230/L17487/L17744/L18001 (c4_KR0070_FY2025_Q4.txt)",
    reader="없음(CSM 불변). dry-run 의 '별도세그합산' 모드는 annual 에서 chain_ok False 면 폐기",
    ver="c4_abl_product_csm.py: 당기 == 2025.4Q 마스터 · 전기 == 2024.4Q 마스터 (6항목 모두 일치)",
    dec="없음. OCI-only 3칸")
add("KR0079", ["2023.4Q"], scn="R1", ready="READY", rank=4, scope="4", census="STAY: UNVERIFIED (CSM prior column unreadable)",
    cause="당기/전기가 한 표 안의 '행 블록'(마커 행 '당기' / '전기')이라 prior 표로 안 잡힘. 제품 5표(사망/건강/연금/저축/기타)의 CSM 소계 열을 전기 블록에서 합산하면 [19795.0,2920.5,454.5,-977.9,-1977.6,20214.5] == 마스터(SAME; 상각 0.1억 반올림). 보험손익 불변 -> Tier-1 PL 만 적재(투자손익 -204억, OCI +362억)",
    src="FY2024_Q4 20250318001228.xml 별도 주석 제품표 L63671/L64337/L65003/L65666/L66329 전기 행블록 (기초 L64085.. 등, c3_KR0079_FY2024_Q4.txt); 손익계산서",
    reader="CSM 적재 불필요. (선택) 같은 표 안에서 '전기' 마커 행 이후를 prior 블록으로 쪼개는 규칙 — 소(아래 R2 의 2024.1Q 에서 필요)",
    ver="c3_mirae_product_csm.py FY2024_Q1..Q4 + FY2025_Q1 (현재열 == 마스터 재현)",
    dec="연도말만 재작성(FY2023 Q1~Q3 비교열은 불변)이라 2023.4Q 단일분기가 구조적으로 이음매 — 18차 선례대로 단일분기 null_dangi(11칸)")
add("KR0010", ["2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q"], scn="R1", ready="READY", rank=5, scope="4", census="STAY: 'Tier-2 legs do not sum to later item 1 (residual 943/-1766/-7866/-9795 mn): LOB note prior-column reader missing'",
    cause="손보 LOB 주석 '(N) 당기와 전기 중 보험손익의 상세내역'(별도, 장기/일반/자동차/해외 열) 의 전기 쌍둥이 표를 안 읽음. 재작성은 장기 다리(item 2 = 총 보험서비스결과 장기)와 재보험 다리(8,9,11,12)에만 있고 원수 4,5,6·자동차·일반은 불변, CSM 불변",
    src="FY2024_Q4 20250314001697.xml 전기 표 L65978 (총 보험서비스결과 R66268: 805,032|(2,892)|48,834|(18,995)|831,979, 셀 L66270-74) / FY2025_Q1 20250515001437.xml L36148 (R36438) / FY2025_Q2 20250814003072.xml L39399 (R39850, 누적 반 L39857-61) / FY2025_Q3 20251114001554.xml L33735 (R34186, 누적 반 L34193-97)",
    reader="생산 핸들러 extract_tier2_kb 를 후속 필링 표에 item1=후속 전기 item1 로 호출하면 그 표를 스스로 고름 -> 코드 변경 사실상 0 (prior 모드 인자 1개)",
    ver="p_kb.py: 같은 필링 재현 4/4 OK, 전기열 합 - item1 = 0 / 0 / -1 / 0",
    dec="2024.2Q item16 gold 192,135 -> 192,136 은 1 mn 재인쇄 차이: 제외 권고(반올림 규칙). 단일분기 이음매: FY2024 Q4 가 불변이라 4Q 단일분기 auto-follow")
add("KR0010", ["2023.1Q", "2023.2Q"], scn="R1b_KB_siblings", ready="READY", rank=5, scope="4(블록)", census="ADDL_SIBLING STAY (gold 16other)",
    cause="FY2023 블록의 형제: 2023.1Q/2Q 마스터는 OCI(25~32) 공란 + 항목 16 gold(=원 공시 인쇄값 92,565 @FY2023_Q1 L6171 / 190,719 @FY2023_Q2 L7649). 후속 전기열 91,710 / 189,068 로 교체(규칙 ⓐ)",
    src="FY2024_Q1 20240516001008.xml L35403 (총 보험서비스결과 L35684: 231,611|(8,090)|30,684|(5,298)|248,907) / FY2024_Q2 20240814002750.xml L38795",
    reader="위와 동일", ver="kb_cands_sib2.txt + gate R1b", dec="FY2023 블록을 한 판으로 만들려면 2023.4Q 와 같이")
add("KR0099", ["2024.1Q#fix"], scn="R0_KBlife_2024Q1_fix", ready="READY", rank=6, scope="4", census="STAY: 'bridge already FAIL on the current master (-1256.0 mn) and stays FAIL'",
    cause="마스터 자체 결함(벤더 판 무관): extract_tier2_kblife 가 '총 재보험수익' 을 abs() 로 읽어 음수(-568)를 +568 로 뒤집음 -> item8 -832 (정답 -568-1,400 = -1,968), 가교 +1,136 mn. 2/8/12 세 칸. 같은 판(원 공시)에서 IS 4줄(보험수익 202,164·재보험수익 (568)·보험서비스비용 115,699·재보험비용 1,400)로 정정",
    src="FY2024_Q1 20240516001445.xml 손익계산서 L25433-26241: 재보험영업수익 (568) @L25538, 재보험영업비용 1,400 @L25589, 보험수익 202,164 @L25521",
    reader="extract_tier2_kblife 의 _jang_rerev/_jang_recost 에서 abs() 제거(1줄)(assemble 주석: 재보험수익은 음수 가능)",
    ver="cand_selftest: 같은 판 candidate 가 마스터와 3칸(2,8,12)만 다름; gate R0 FAIL 23->22",
    dec="없음(최신 비교열 문제와 독립). KB라이프 블록 결정(D1)과 무관하게 먼저 적재 가능")
add("KR0003", ["2024.1Q", "2024.2Q", "2024.3Q"], scn="R2", ready="READY", rank=7, scope="4,5", census="STAY: LOB bridge break + CSM restated + PL4 not read + 'chain not adoptable'",
    cause="(1) LOB: 2번째(전기) 쌍둥이 표 — 2024.1Q 표 L20090 'bycontent', 2024.2Q/3Q 는 split 양식(전반기 마커) — 의 다리 합이 후속 item1 에 닫힘(잔차 -0.53/0/0). (2) CSM: FY2025 Q1~Q3 비교열 기초 23,860.8(=2024.4Q 마스터 기초) 이라 FY2024 는 Q4 마스터와 한 판으로 닫힘. (3) PL4 전기열 = |CSM5'| ±0.05억(4/4)",
    src="FY2025_Q1 20250515002628.xml 전기 표 L20090(LOB)/L15356(CSM, 기초 L15400 기말 L15609 상각 L15444) / FY2025_Q2 20250814003966.xml split 전반기 표 L58037..61879 / FY2025_Q3 20251114002985.xml L32050..34035",
    reader="extract_tier2_lotte 3개 레이아웃에 prior 스위치(둘째 표 / 전반기 마커 표; split 은 마커 뒤 연속 LOB 표로 한정) — lotte_lib.py 100줄 미만",
    ver="p_lotte_run.py: 같은 필링 재현 4/4, 전기열 합-목표 -0.75/-0.53/0/0 (2023.4Q 포함); CSM 2024.1Q 독립 재독 == dry-run",
    dec="PL+CSM+PL4 를 같이 적재(짝). CSM 3칸군 + FY2024 Q4 는 SAME(오독 정정)")
add("KR0003", ["2023.4Q"], scn="N7_Lotte_FY2023Q4", ready="NEEDS_OWNER", rank=12, scope="4,5", census="STAY: LOB bridge + CSM restated",
    cause="LOB·PL4 는 닫힘(잔차 -0.75, PL4 185,905 == 1859.0억). 그러나 FY2024 연간 보고서가 2023 기초를 16,669.0 으로 재작성(FY2024 Q1~Q3 의 2023 비교열은 16,774.4 그대로) -> 분기별 최신으로 쓰면 FY2023 기초가 16,774.4 x3 / 16,669.0 (0.63%) 로 WFY 깨짐 (원=한 판, 최신=두 판)",
    src="FY2024_Q4 20250320001732_00760.xml 전기 표 L10874 (기초 16,669.0 L10918, 기말 23,860.8 L11127)",
    reader="LOB·PL4 는 lotte_lib 로 읽힘", ver="own-read FY2024_Q4 _00760; gate N7",
    dec="D2: 보류(현 상태 유지) vs 채택(+WFY_EXCEPTIONS 등재). 보류해도 FY2024 Q1~Q3 채택(R2)은 CONT 0.44% < 0.5% 로 통과")
add("KR0003", ["2023.1Q", "2023.2Q"], scn="R2b_Lotte_2023_1Q2Q", ready="READY", rank=7.5, scope="4(블록)", census="ADDL_SIBLING STAY (2023.1Q CSM gold items 1-6; 2023.2Q gold item 19)",
    cause="FY2023 블록 형제: 2023.1Q 는 CSM 4·6(기말 17,427.5 -> 17,934.9)만 재작성, 2023.2Q CSM 은 불변(SAME). Q1~Q3 비교열 기초는 16,774.4 그대로라 Q4 결정(D2)과 독립. PL 은 LOB 다리를 FY2024 Q1/Q2 전기 표에서 읽으면 가교 +0.4/-0.4. 마스터 2023.1Q 는 item1·LOB 가 비어 있고 PL4 도 공란(PL_CSM_AMORT_MISSING_DOCUMENTED) -> PL4 도 채워짐",
    src="FY2024_Q1 20240516001888.xml 전기 LOB 표(p_lotte_run: combined), FY2024_Q2 20240814002875.xml; CSM 비교열 dry-run(2023.1Q open_ok)",
    reader="lotte_lib 와 동일 + 마스터에 없던 provenance 블록 생성", ver="gate R2b (가교·PL4 항등 통과)",
    dec="gold(CSM 6칸 ⓐ 원 인쇄값, 2023.2Q 항목 19 ⓐ) 교체. 2023.1Q provenance 블록 신규. 단일분기: 2023.2Q 값_당분기 auto-follow")

add("KR0079", ["2024.1Q", "2024.2Q", "2024.3Q"], scn="R2", ready="READY", rank=8, scope="4", census="STAY: 2024.1Q LOB bridge + CSM unreadable; 2024.2Q/3Q LOB bridge + CSM restated (3..6)",
    cause="LOB 다리는 손익계산서 4줄 전기열로 닫힘(생보 — 새 리더 불요). CSM 은 소폭 재작성(기말 +8.9/+8.7/+8.5억, 기초 20,214.5 불변 -> FY2024 한 판 유지). 2024.1Q 전기열은 행 블록 레이아웃이라 못 읽었음 -> 행 블록 합산으로 [20214.5,962.0,118.2,138.1,-507.6,20925.2]",
    src="FY2025_Q1 20250515001717.xml 제품 5표 L42459/L43126/L43793/L44457/L45121 전기 행블록; 2024.2Q/3Q 는 FY2025_Q2/Q3 prior 블록(csm_sources.txt)",
    reader="CSM prior 라벨러에 '표 안 마커 행(전기/전분기/전반기) 이후 = prior' 규칙(소) + PL4 는 같은 표 합(= -CSM5')",
    ver="c3_mirae_product_csm.py (FY2024_Q1~Q4, FY2025_Q1)", dec="없음")
add("KR0001", ["2023.1Q", "2023.2Q"], scn="R2", ready="READY", rank=9, scope="5", census="ADDL_SIBLING STAY (single-quarter vintage seam; gold 16other)",
    cause="같은 뿌리의 단일분기 어긋남: FY2023 마스터가 Q1/Q2=원 판(기초 100,383.8), Q3/Q4=최신(96,376.4, 2026-10-12 채택). FY2024 Q1/Q2 비교열(기초 96,376.4)로 갱신하면 FY2023 이 한 판. LOB: Format-B 상세내역 전기 쌍둥이 표 장기 357,082 / 790,286, 가교 +0.5 / -1.2 (item16 부호 보존 필수: 1Q 음수)",
    src="FY2024_Q1 20240516001162.xml 전기 표 L48018 (총 보험서비스결과 R48309: 357,082|18,331|14,528|389,941; 보험계약마진 L48079) / FY2024_Q2 20240814003013.xml L51801",
    reader="extract_tier2_sonbo_structured 에 둘째 표 선택(prior) — p_meritz_lib.py", ver="p_meritz.py 같은 필링 재현 OK, 가교 +0.5/-1.2, PL4 256,695/515,014 == CSM5' (±0.05억)",
    dec="gold 16 (원 인쇄값 L5994/L9430) 교체 ⓐ. NB_CSM 마스터 2행 재빌드, pl_bridge_baseline 1줄·WFY_EXCEPTIONS 삭제")
add("KR0068", ["2023.1Q", "2023.2Q", "2023.3Q"], scn="R2", ready="READY", rank=10, scope="5", census="ADDL_SIBLING STAY (gold 20other / 21other)",
    cause="같은 뿌리: FY2023 Q1/Q2 원 판(기초 96,679.3) vs Q3/Q4(97,629.5). FY2024 Q1~Q3 비교열(기초 97,629.5)로 갱신하면 한 판. 마스터 2023.1Q/2Q 는 item2(생명장기손익)가 공란이라 가교가 0 으로 채워져 FAIL(-152,373/-396,756) -> 손익계산서 4줄 전기열로 채워 해소. 순이익 2023.1Q +1,139.9억, 2Q +1,053.7억(발행사 재작성)",
    src="FY2024_Q1 20240514000837.xml 손익계산서 L66068-67252 (분기순이익 전기누계 470,912,058,790 @L66938); FY2024_Q2 20240813000860.xml; FY2024_Q3 20241113000407.xml",
    reader="없음(손익계산서 4줄 + PL4 L1 둘째 표 p_hanwha.py)", ver="p_hanwha.py 2Q/3Q PL4 451,415/668,342 == CSM5'; gate R2",
    dec="gold 20(2023.1Q 원 인쇄 L52688)/21(2023.2Q 원 누적에서 파생) 교체 ⓐ. NB 2행 재빌드, pl_bridge_baseline 2줄")
add("KR0099", ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q"], scn="N1_KBlife_A", ready="NEEDS_OWNER", rank=11, scope="4,5", census="STAY (5): LOB bridge + CSM restated + PL4 not read + 'chain not adoptable'",
    cause="LOB 다리는 IS 4줄로 닫힘(새 리더 불요), PL4 전기열 5/5 일치(KB라이프 2023.3Q..2024.3Q 5표). 막는 것은 CSM 3가지 판: V0(Q1~Q3 원 기초 31,201.3) / V1(FY2023 연간 원본 = FY2024 Q1~Q3 비교열, 31,327.6) / V2(FY2024 연간 비교열 33,595.7 -> 기말 31,798.2) — V2 는 Q4 만 인쇄(Q1~Q3 의 V2 는 어느 필링에도 없음). FY2024 는 Q1~Q4 모두 최신 31,798.3, 원은 30,176.4(+Q4 gold 30,176.4 = 연쇄 맞추기용 ⓑ)",
    src="FY2024_Q4 20250314000905.xml 전기 표 L50518 (기초 L50565 기말 L50765); 분기 비교열 FY2024 Q1~Q3 / FY2025 Q1~Q3 (csm_sources)",
    reader="없음(CSM prior 는 dry-run 5/5 + 독립 재독 1건)", ver="p_kblife.py PL4 5/5; gate N1/N2/N3",
    dec="D1: A(분기별 최신 전체, 연속성 RED 1) / B(FY2023 Q1~Q3 만, RED 0) / C(현 상태). A'(2023.4Q 만 빼기)는 CONT RED 4 로 최악")
add("KR0070", ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"], scn="N4_ABL_FY2023", ready="NEEDS_OWNER", rank=13, scope="2,4", census="STAY: 2023.3Q LOB bridge + CSM restated; 2023.4Q CSM restated + owner CSM gold (items 1,4); siblings 2023.1Q/2Q",
    cause="FY2023 은 분기 4개 모두 최신 비교열 기초 7,585.3 으로 한 판(WFY 0, 4Q 기말 8,695.4 = 마스터) — 닫힘. LOB 다리는 IS 4줄(2023.3Q 잔차 -6,748 은 이것으로 해소). 막는 것 = owner CSM gold 2023.4Q 항목 1(7,017.8)·4(-1,148.8): 원 인쇄값(7,585.3/-1,716.3)도 최신값도 아님 = Q1~Q3 원 기초를 Q4 에 강제한 연쇄용 gold(ⓑ). Q1~Q3 가 7,585.3 이 되면 이유 소멸",
    src="FY2024_Q4 20250331001358_00760.xml 전기 표 L14100 (기초 L14127, 신계약 L14175, 상각 L14191, 기말 L14290대); FY2024 Q1~Q3 CSM 비교열; PL4 후속 '(1) 당분기와 전분기 중 보험영업수익' 보험계약마진상각 prior-YTD: Q2 L22569 46,789 · Q3 L22013 69,639",
    reader="PL4 분기 prior = 보험영업수익 주석 '보험계약마진상각' 행의 마지막 숫자 셀(생산 extract_tier2_abl 캡션 게이트는 분기 양식 미일치 — 위치만 고치면 됨)",
    ver="c4_abl_product_csm.py(연간 전기), pl4_equality.csv ABL 3/3, gate N4", dec="D3: gold 2개 교체(ⓑ-연쇄) 승인 + PL gold 2023.1Q 항목4(22,664)·7 ⓐ 교체. NB 재빌드 3행")
add("KR0072", ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"], scn="N5_KDB_FY2023", ready="NEEDS_OWNER", rank=14, scope="4", census="STAY: 2023.3Q LOB bridge + CSM restated + PL4 not read + chain not adoptable (owner gold)",
    cause="FY2023 4분기 모두 최신 기초 5,695.9 로 한 판(Q4 기말 5,830.5 = 마스터). 생보라 LOB 는 IS 4줄. 막는 것 = owner CSM gold 2023.4Q 1·4 (5,239.4/-2,103.5: Q1~Q3 원 기초 강제, ⓑ-연쇄) + 2023.1Q 4·5·6 / 2023.2Q 4·5 (원 인쇄값 정밀판, ⓐ) + PL gold 2023.2Q/3Q 항목 4·7(축척 오류 정정치, ⓐ)",
    src="FY2024 Q1~Q4 KDB 별도 CSM 비교열(dry-run open/chain OK); PL4 prior: p_lifeold (OLD life L2, 한 기간 블록 우측) 11,641/24,509/37,266/51,198",
    reader="_oll_num 에 prior 인자(pair: ns[3], single: ns[1]) — 4줄", ver="p_lifeold.py(KDB) + pl4_equality 4/4; gate N5 clean",
    dec="D3: gold 7+4칸 교체(ⓑ-연쇄 2 · ⓐ 9) 승인")
add("KR0009", ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"], scn="N6c_HD_FY2023_IRlegs", ready="NEEDS_OWNER", rank=15, scope="4,5", census="STAY: 2023.4Q CSM prior column unreadable (UNVERIFIED); siblings CSM restated",
    cause="CSM 전기열은 읽힘: FY2024 연간 별도 '(2) 전기' 표(짧은 캡션이라 prior 로 안 잡힘) -> [83515.4,16792.4,2636.3,-2716.0,-8805.4,91422.7]; FY2023 4분기 모두 기초 83,515.4 로 일관. PL: 2023.1Q/2Q 보험손익이 -124.5/-838.5억 재작성되는데 LOB 다리(2/13/14)의 재작성값은 DART FY2024 Q1/Q2 필링에 없다(사업의 내용 「보험종목별 수지」는 당기 한 기간, 전분기 LOB 분해 표 없음 — p_hyundai.py). 그래서 레그를 둔 채 채택하면(N6) 가교 FAIL 2건(+8,429.8 / +75,080.6 mn). 원천은 raw 에 있다: IR 팩트시트 '(3) UW Income' 전년동기 누계 열의 LOB 보험손익(일반·장기·자동차)이 재작성 item1(246,045.3 / 415,652.3 mn)과 소수점 아래까지 같다(w4_hd_ir_legs.py) -> 이 레그를 쓰면 가교 0.0 으로 닫힘(N6c)",
    src="CSM: FY2024_Q4 20250313001346.xml '(2) 전기' 표 L36017(전전기말 CSM L36061 -> 전기말 L36117); 분기 비교열 FY2024_Q1 20240516002153.xml L23214 / Q2 20240814004187.xml L25432 / Q3 20241114003026.xml L23616. 레그: data/ir/FY2024_Q1/raw/KR0009_현대해상/dd7e547e6e1f9cc171b77dcb4bf67d58.xlsx 및 FY2024_Q2/.../d33c3d385303361798f75607750ca360.xlsx 의 시트 '(3) UW Income' 셀 L11(일반)·L26(장기)·L30(자동차)·L31(합계)",
    reader="신규(소): IR 팩트시트 레그 리더 — 시트 '(3) UW Income' 의 블록(일반/장기/자동차) 아래 첫 '보 험 손 익' 행의 마지막 숫자 셀 = 전년동기 누계(w4_hd_ir_legs.py 25줄). CSM: '(2) 전기' 짧은 캡션 표를 직전 '(1) 당기' 표의 헤더와 같으면 prior 로 상속(dry-run short_prior_blocks 존재). 2023.4Q 레그(13/14)는 이미 owner gold(IR 유래)라 손대지 않음(가교 -98 mn, 허용오차 안)",
    ver="v1_csm_verify: 4분기 CSM 벡터 전부 별도 단일 표에서 줄번호로 재독(Q1 L44042 / Q2 L47726 / Q3 L45851 / Q4 L75486; 연결 쌍둥이 L22208 / L24426 / L22607 / L34789); w4: 레그 합 == 재작성 item1 (차 0); gate N6c; 대안 N6b(CSM+PL4 만)도 모의",
    dec="D3: ① 레그 원천에 IR 팩트시트를 허용할지(2023.4Q 레그가 이미 IR 유래 owner gold 이므로 선례 있음; DART 1차 원칙의 예외라 owner 승인 필요), ② 연쇄용 CSM gold 4칸(2023.3Q 1·4, 2023.4Q 1·4) + PL gold 2023.4Q 항목16(반올림 0.03) 교체 승인. 원천 허용이 안 되면 N6b(CSM+PL4 만 적재, PL Tier-1 은 원 판 유지)가 xlsx 제외 RED 0 으로 가능(NB_VS_WATERFALL RED 2 는 둘 다 NB 재빌드 필요)")


# ---- e20 independent re-read evidence (v1_csm_verify / v3_mirae_wide / v4_meritz_csm): exact table / row lines per bucket -------------------------------------------------------
def _ov(code, qs, **kw):
    for q in qs:
        KEYB[(code, q)].update(kw)


_ov("KR0003", ["2023.1Q", "2023.2Q"],
    src="LOB: FY2024_Q1 20240516001888.xml 전기 표 L20526 · FY2024_Q2 20240814002875.xml L22710 (bycontent 둘째 표; 원 필링 FY2023 Q1/Q2 쪽은 레이아웃이 안 읽혀(layout orig=None) 전기열이 유일한 경로). CSM 2023.1Q: FY2024_Q1 L15703 (기초순보험계약부채 L15747 -> 기말 L15956; 최초인식 L15834 · 이자 L15890 · 조정 L15846 · 현행서비스(상각) L15780). 2023.2Q CSM 불변",
    ver="p_lotte_run.py 잔차 +0.395/-0.433 mn; v1_csm_verify.py 로 CSM 6항목을 후속 필링 단일 표에서 줄번호 재독; PL4 노트 39,284 = |CSM5'| 392.84억; gate R2b",
    reader="lotte_lib 와 동일(bycontent 둘째 표) + 마스터에 없던 contract_notes provenance 블록 생성(적재 시)")
_ov("KR0003", ["2024.1Q", "2024.2Q", "2024.3Q"],
    ver="p_lotte_run.py 같은 필링 재현, 전기열 합-목표 -0.53/0/0; CSM 6항목을 v1_csm_verify.py 로 후속 필링 단일 표에서 줄번호 재독 (2024.1Q FY2025_Q1 L15356 / 2Q FY2025_Q2 L39908 / 3Q FY2025_Q3 L22476); PL4 노트 = |CSM5'| ±0.05억 (3/3)")
_ov("KR0079", ["2024.1Q", "2024.2Q", "2024.3Q"],
    src="2024.1Q: FY2025_Q1 20250515001717.xml 제품 5표 L42459/L43126/L43793/L44457/L45121 전기 행블록 (c3_KR0079_FY2025_Q1.txt); 2024.2Q: FY2025_Q2 xml/20250814003532.xml T92008-94067 (기초 R92286 · 상각 R92782 · 기말 R93960); 2024.3Q: FY2025_Q3 xml/20251114002791.xml T49706-50442 (기초 R49858 · 기말 R50413) (v3_mirae_wide.txt)",
    ver="Q1: c3_mirae_product_csm.py 행블록 합 / Q2·Q3: v3_mirae_wide.py 넓은 롤포워드(5제품 x CSM 3열) 합이 dry-run 벡터와 6항목 모두 일치 ([20214.5,1723.9,243.3,-271.6,-1007.0,20903.2] / [20214.5,2742.6,374.7,-1190.5,-1487.1,20654.1])")
_ov("KR0001", ["2023.1Q", "2023.2Q"],
    src="LOB: FY2024_Q1 20240516001162.xml 전기 표 L48018 (총 보험서비스결과 R48309) / FY2024_Q2 20240814003013.xml L51801. CSM: FY2024_Q1 T46620-46957 (기초 R46667 CSM 3열 L46671-73 · 신계약 R46697 · 이자 R46837 · 조정 R46707 · 상각 R46747 · 기말 R46927) / FY2024_Q2 T50248-50585 (기초 R50295 · 기말 R50555)",
    ver="p_meritz.py 같은 필링 재현 OK, 가교 +0.5/-1.2, PL4 256,695/515,014 == CSM5'(±0.05억); v4_meritz_csm.py: 3개 CSM 열 합이 dry-run 벡터와 6항목 모두 일치(잔차 0.00)")
_ov("KR0068", ["2023.1Q", "2023.2Q", "2023.3Q"],
    src="FY2024_Q1 20240514000837.xml 손익계산서 L66068-67252 (분기순이익 전기누계 470,912,058,790 @L66938); FY2024_Q2 20240813000860.xml; FY2024_Q3 20241113000407.xml. CSM 별도 표: FY2024_Q1 L77426 (기초 L77453 9,762,946 -> 기말 L77613 9,879,107) / Q2 L78102 (L78129 -> L78328 10,122,695) / Q3 L68140 (L68167 -> L68327 9,799,116)",
    ver="p_hanwha.py 2Q/3Q PL4 451,415/668,342 == CSM5'; v1_csm_verify.py: 별도 표에 6항목 합계가 인쇄돼 줄번호 재독; gate R2")
_ov("KR0099", ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q"],
    src="CSM 벡터 줄번호: V1 = FY2024_Q1 20240516001445.xml L17051 / Q2 20240814002882.xml L18524 / Q3 20241114001333.xml L15216 (기초 3,132,761 mn); V2 = FY2024_Q4 20250314000905.xml L50518 (기초 L50565 3,359,570 -> 기말 L50765 3,179,825); FY2024 최신 = FY2025_Q1 L16573 / Q2 L18615 / Q3 L15426 / Q4 20260313001119.xml L30423 (기초 3,179,826). 전수: csm_vector_sources.csv",
    ver="p_kblife.py PL4 5/5; v1_csm_verify.py 로 8개 CSM 벡터 전부 단일 표에서 줄번호 재독; gate N1/N2/N3")
_ov("KR0070", ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"],
    src="CSM: FY2024_Q1 20240516002045.xml L20300 (기초 L20336 758,530 -> 기말 L20400 789,846) / Q2 20240814004092.xml L20912 / Q3 20241114002738.xml L20361 / Q4 20250331001358.xml L26772 (기초 L26808 -> 기말 L26872 869,543); PL4 후속 '(1) 당분기와 전분기 중 보험영업수익' 보험계약마진상각 prior-YTD: Q2 L22569 46,789 · Q3 L22013 69,639; Q4 [구분|당기|전기] 전기 92,971. 전수: csm_vector_sources.csv")
_ov("KR0072", ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"],
    src="CSM: FY2024_Q1 20240516000597.xml L17151 (기초 L17179 569,595 -> 전분기말 L17355 513,820) / Q2 20240814000801.xml L19544 / Q3 20241114000809.xml L18341 / Q4 20250331002302.xml L30718 (기초 L30758 -> 기말 L30822 583,047); PL4 prior: p_lifeold (OLD life L2, 한 기간 블록 우측) 11,641/24,509/37,266/51,198. 전수: csm_vector_sources.csv")


# ---- separate-basis table lines (master basis = OFS): supersede the first-found (consolidated twin) lines above ----
_ov("KR0099", ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q"],
    src="CSM 벡터(별도 표) 줄번호: V1 = FY2024_Q1 20240516001445.xml L34183 (기초 L34230 3,132,761 -> 분기말 L34430 3,161,352) / Q2 20240814002882.xml L37997 / Q3 20241114001333.xml L34025; V2 = FY2024_Q4 20250314000905.xml L50518 (기초 L50565 3,359,570 -> 기말 L50765 3,179,825); FY2024 최신 = FY2025_Q1 20250515001983.xml L37587 / Q2 20250814004162.xml L41496 / Q3 20251114001600.xml L36869 / Q4 20260313001119.xml L65705 (기초 L65745 3,179,826 -> 기말 L65801 3,010,508). 연결 표는 같은 숫자의 쌍둥이. 전수: csm_vector_sources.csv")
_ov("KR0070", ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"],
    src="CSM(별도 표): FY2024_Q1 20240516002045.xml L37328 (기초 L37355 758,530 -> 분기말 L37546 789,846) / Q2 20240814004092.xml L38981 (L39008 -> L39199) / Q3 20241114002738.xml L38106 (L38133 -> L38317) / Q4 20250331001358.xml L50524 (L50551 -> L50735 869,543); PL4 후속 '(1) 당분기와 전분기 중 보험영업수익' 보험계약마진상각 prior-YTD: Q2 L22569 46,789 · Q3 L22013 69,639; Q4 [구분|당기|전기] 전기 92,971. 전수: csm_vector_sources.csv")
_ov("KR0072", ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"],
    src="CSM(별도 표): FY2024_Q1 20240516000597.xml L36277 (기초 L36305 569,595 -> 전분기말 L36481 513,820) / Q2 20240814000801.xml L40636 (L40664 -> L40840 604,335) / Q3 20241114000809.xml L18341 (L18372 -> L18554 583,684) / Q4 20250331002302.xml L26189 (L26220 -> L26396 583,047); PL4 prior: p_lifeold (OLD life L2, 한 기간 블록 우측) 11,641/24,509/37,266/51,198. 전수: csm_vector_sources.csv")
_ov("KR0009", ["2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q"],
    src="CSM(별도 표): 분기 비교열 FY2024_Q1 20240516002153.xml L44042 (기초 L44069 -> 기말 L44261) / Q2 20240814004187.xml L47726 (L47753 -> L47945) / Q3 20241114003026.xml L45851 (L45878 -> L46070); 연간 20250313001346.xml '(2) 전기' L76716 (기초 L76757 -> 기말 L76815) 및 '나. 전기' L75486 (L75513 -> L75705). 레그: data/ir/FY2024_Q1/raw/KR0009_현대해상/dd7e547e6e1f9cc171b77dcb4bf67d58.xlsx 및 FY2024_Q2/.../d33c3d385303361798f75607750ca360.xlsx 의 시트 '(3) UW Income' 셀 L11(일반)·L26(장기)·L30(자동차)·L31(합계)")


def q_bucket_numbers(scn, code, q):
    d = SC[scn]
    b = d["buckets"].get(f"{code}|{q}")
    return b


rows = []
for (code, q), meta in sorted(KEYB.items(), key=lambda kv: (kv[1]["rank"], kv[0])):
    scn = meta["scn"]
    qreal = q.split("#")[0]
    b = q_bucket_numbers(scn, code, qreal)
    sc = b["screen_eok"] if b else {}
    c6 = csm6.get((scn, code, qreal))
    rows.append({
        "rank": meta["rank"], "readiness": meta["ready"], "scope_ref": meta["scope"], "company": names.get(code), "code": code, "quarter": (q.replace("#fix", " (마스터 오류 정정 3칸)")), "scenario": scn,
        "census(d_census)": meta["census"], "e20_cause": meta["cause"], "source_filing_and_tables": meta["src"], "reader_change": meta["reader"], "verified_on": meta["ver"],
        "pl_value_cells": (b or {}).get("n_pl"), "csm_cells": (b or {}).get("n_csm"),
        "bridge_residual_mn": (b or {}).get("closure", {}).get("I7 LOB bridge (min of bare/adj)"),
        "headline_delta_eok": "; ".join(f"{k} {v[0]:,.1f}->{v[1]:,.1f}({v[2]:+,.1f})" for k, v in sc.items()),
        "csm_closing_delta_eok": (None if not c6 or c6[0] is None else f"{c6[0]:,.1f}->{c6[1]:,.1f}({c6[1] - c6[0]:+,.1f})"),
        "gate_simulation": GATE.get(scn, ""), "decision_or_blocker": meta["dec"],
    })
with open(M.MEASURE / "plan_table.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
from collections import Counter
print(len(rows), "rows", Counter(r["readiness"] for r in rows))
print("PL cells by readiness:", {k: sum((r["pl_value_cells"] or 0) for r in rows if r["readiness"] == k) for k in ("READY", "NEEDS_OWNER", "BLOCKED")})
print("CSM cells by readiness:", {k: sum((r["csm_cells"] or 0) for r in rows if r["readiness"] == k) for k in ("READY", "NEEDS_OWNER", "BLOCKED")})
