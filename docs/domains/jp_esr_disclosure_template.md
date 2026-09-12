# 일본 ESR 규제 공시 양식 지도 (jp 레인 정본, 2026-09-12 신설)

> 근거 티켓: `inbox/jp/20260912T0905Z__owner__JP_MULTI__esr_disclosure_template_map.md`. 기계 스키마: `J-ESR/esr_disclosure_schema.json`.
> 표본값+검산: `J-ESR/raw/fy2025_samples/extracted_sample_values.json`. 생성기(10월 62사 추출의 프로토타입):
> `J-ESR/extract_esr_template_samples.py` (`C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe J-ESR/extract_esr_template_samples.py`, exit 0 = 검산 전부 통과 + census 헤드라인 일치).
> 합산 규정(상관행렬) 기계본: `J-ESR/esr_aggregation_rules.json` — §8 (2026-09-12 추가, 티켓 `inbox/jp/20260912T1005Z__owner__JP_MULTI__esr_aggregation_rule.md`).
> **10월 말 재census 의 확장 열 이름은 이 문서의 항목 id 를 그대로 쓴다.**

## 0. 한 줄 요약

- 규제 양식(保険業法施行規則 59条の2, 令和7年金融庁告示第74号·第75号)은 **회사가 달라도 표 골격이 같다.** 정량 7절(요약 → 적격자본 구성 → 소요자본 구성 → 경제가치 BS → 외국증권 → 보험부채 상품별 → 민감도) + 정성 2절(전제·수법 / 검증체제). 손보 표본 2사에서 라벨은 전각/반각·기호 `(A)` vs `（A）`·`Tier1` vs `Tier１` 차이뿐, NFKC 정규화 후 **동일**.
- 헤드라인 `esr_pct` 는 `適格資本の額(A) / 所要資本の額(B)`. 두 표본 모두 census 값과 일치(au 791.7 / Meiji Yasuda Non-Life 743.2). 금액은 百万円 절사라 비율 검산은 **구간 검산**이어야 한다(§4 C01).
- 스키마는 두 층: `layer:"esr"` 115항목(표 T1~T8, 생보 리스크 하위 6행 포함) / `layer:"article_axes"` 22항목(금융청 모니터링 보고서 3축 + ESR 빈 자리 골격). 검산 C01~C34 + A01~A05 + **G01~G10(상관행렬 재계산, §8)**: au 43/43, Meiji Yasuda Non-Life 49/51(미재현 2건은 등재된 informational), NN Life 4/4.
- **소요자본 합산은 √(xᵀRx) 로 재현된다.** 告示74 第百五十五条 행렬(생보·손보 0.00, 나머지 0.25)로 분산효과 au 273.6 vs 274 · MY 2,529.5 vs 2,530, 세효과 = 0.8 × 28.0% × 세효과전 으로 두 회사 모두 ±1. 하위(시장 第百二十七条)도 재현. 안 되는 곳은 손보 하위(다지역 회사)와 巨大災害(MY) — §8.
- **세 번째 층 `layer:"profit"` 36항목(2026-09-12 추가, §9)** — J-GAAP 법정 손익계산서 층. 생보 基礎利益·キャピタル/臨時·三利源, 손보 保険引受利益·資産運用損益·損害率/事業費率/合算率, 공통 経常利益·当期純利益 + 전기 비교값(`{prev, cur}`) + 회계기준 메타(`accounting_basis`/`ifrs17_applied`). 검산 P01~P13: au 19/19, NN Life 12/12, MY 는 별책에 손익 표가 없어 본편 미확보(NOT_ACQUIRED).

## 1. 표본

| key | 회사 | 문서 | 페이지 | 층 | 비고 |
|---|---|---|---|---|---|
| `au_nonlife` | au損害保険 (au Non-Life) | `J-ESR/raw/fy2025_samples/au_nonlife_disclo_260730_4of5.pdf` (ディスクロージャー誌 業績データ편, 2026-07-30) | 31p | esr + article_axes | ESR 절 p21~30. 5개년 표 p2 헤드라인 791.7%. 민감도 값 **생략**(전 시나리오 차이 1%p 미만 주기). 본편에 責任準備金の内訳(p8)·出再 표(p6) 포함 |
| `meijiyasuda_nonlife` | 明治安田損害保険 (Meiji Yasuda Non-Life) | `J-ESR/raw/fy2025_samples/meijiyasuda_nonlife_20260904_performance_data.pdf` (【別冊】業績データ, 2026-09-04) | 14p | esr + article_axes | 별책 전체가 ESR 규제 양식(p1 목차 = 告示 절 번호 그대로). 이상위험준비금·재보험 표는 **본편에 있어 별책엔 없음** |
| `nnlife` | エヌエヌ生命保険 (NN Life) | `J-ESR/raw/fy2025_samples/nnlife_2025disclosure_202607.pdf` (ディスクロージャー誌 2026-07-29) | 95p | article_axes 만 | ESR `後日公表予定`(3곳). 基礎利益 p60, 逆ざや p15, 出再 표 p64. ESR 표 골격은 **없고 문장만** (§7-3) |

세 PDF 모두 텍스트 PDF(fitz 추출 정상, 스캔 없음). 페이지 번호는 PDF 인덱스(1부터)이며 인쇄 페이지 번호와 다르다(au 인쇄 69~79 = PDF 21~31).

## 2. 규제 양식 구조 (告示 절 번호 = Meiji Yasuda 별책 목차)

| 절 | 일본어 제목 | 표 id | 내용 | au 위치 | MY 위치 |
|---|---|---|---|---|---|
| 정량 1 | ソルベンシー・マージン比率並びに適格資本の額及び所要資本の額 | T1 (要約) | (A) 적격자본·(B) 소요자본·(A)/(B) 비율, 열 = 前年度(－)/当年度/増減 | p22 (2) | p2 |
| (au 만) | 保険会社に係る保険金等の支払能力の充実の状況（単体SMR） | T1_combined | Tier1/2 요약 + 리스크 (a)~(k) 한 표. `非保険事業に係る所要資本の額 (i)` 행이 여기만 있음 | p22 (1) | 없음 |
| 정량 2 | 適格資本の額の構成に関する事項 | T2 | Tier1 (A)=(B)−(C), Tier2 (D)=(E)−(F)−(G), 합계 (A)+(D). 33행 | p23 (3) | p3 |
| 정량 3 | 所要資本の額の構成に関する事項 | T3 | 리스크 (A)~(G), 분산효과 (H), 세효과전 (I/J), 세효과 (J/K), 세효과후. 31행 | p24 (4) | p4 |
| 정량 4 | 経済価値ベースのバランスシートに関する事項 | T4 | 4열(財務会計/組替え/評価替え/経済価値) BS + 주기(작성방침·할인율·MOCE) | p25~27 (5) | p5~9 |
| 정량 5 | 外国証券の種類別差異調整に関する事項 | T5 | 외국증권 look-through (미추출) | p27 (6) | p10 |
| 정량 6 | 保険負債の商品別差異調整に関する事項 | T6 | 6열(財務会計/再保険グロスアップ/非経済前提/経済前提/その他/経済価値 MOCE除く) × 상품 | p28 (7) | p11 |
| 정량 7 | 感応度分析に関する事項 | T7 | 8열(基準 + 7 시나리오) × 10행. MY 는 差額表 추가 | p29 (8) 값 생략 | p12 |
| (au 만) | 適格資本の額及び所要資本の額の変動要因分析 | — | 초년도라 該当なし | p29 (9) | 없음 |
| 정성 1 | 計算に用いられた前提及び手法 | T8 | 할인율 버킷·비경제전제·경영조치·리스크경감·USP·내부모형·내부할인율·중요변경 | p29 (10) 문장 | p13 항목식 |
| 정성 2 | 算出及び検証に係る手続並びに体制 | — | 검증책임자 체제(미추출) | p30 (11) | p14 |

**민감도 시나리오 8열(고정 순서):** 当期末 / 円金利 50bp 上昇 / 円金利 50bp 下降 / 米ドル金利 50bp 上昇 / 米ドル金利 50bp 下降 / 円金利 UFR 50bp 下降 / 株式・不動産 10% 下落 / 為替 10% 円高.
**민감도 행 10개:** SMR / 適格資本 / 総資産 / 保険負債(MOCE除く) / MOCE / 非保険負債 / 純資産 / 所要資本 / 生命保険リスク(au 는 행 없음) / 市場リスク.

## 3. 항목 표 (스키마 = 이 표, 두 층 131항목)

열 설명: `kics` = K-ICS 마스터 항목번호(§6, 근사 포함, 빈칸 = 대응 없음). 회사 열 = 실측값(百万円; pct 는 %; `－` = 원문 대시 = null). `page` = au/MY PDF 페이지. `formula` = 검산·정의.

| id | layer | table | label (ja) | meaning (ko) | unit | parent | kics | au_nonlife | meijiyasuda_nonlife | nnlife | page | formula |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `eligible_capital` | esr | T1 | 適格資本の額(A) | 적격자본 총액(A) | JPY_million |  | 1 | 9,278 | 40,290 | n/a(not_yet) | 22/2 | = tier1_eligible + tier2_eligible |
| `required_capital` | esr | T1 | 所要資本の額(B) | 소요자본 총액(B, 세효과 고려후) | JPY_million |  | 14 | 1,171 | 5,420 | n/a(not_yet) | 22/2 | = rc_post_tax |
| `esr_pct` | esr | T1 | ソルベンシー・マージン比率((A)/(B)) | ESR(경제가치기준 지급여력비율, 신기준 SMR) | pct |  | 27 | 791.7 | 743.2 | n/a(not_yet) | 22/2 | = eligible_capital / required_capital * 100 (truncation interval) |
| `tier1_eligible` | esr | T2 | Tier1適格資本の額 | Tier1 적격자본(A) | JPY_million | eligible_capital | 2 | 9,102 | 40,140 | n/a(not_yet) | 23/3 | = tier1_basic - tier1_adjustments |
| `tier1_basic` | esr | T2 | Tier1適格資本に係る基礎項目の額 | Tier1 기초항목(B) = EBS 순자산 | JPY_million | tier1_eligible | 4 | 13,880 | 42,118 | n/a(not_yet) | 23/3 | = tier1_instr_unrestricted + tier1_instr_restricted + tier1_non_instrument; == ebs_net_assets |
| `tier1_instr_unrestricted` | esr | T2 | 算入制限のないTier1資本調達手段の額 | 산입제한 없는 Tier1 자본조달수단(자본금·기금) | JPY_million | tier1_basic | 5 | 3,150 | 10,000 | n/a(not_yet) | 23/3 |  |
| `tier1_instr_restricted` | esr | T2 | 算入制限のあるTier1資本調達手段の額 | 산입제한 있는 Tier1 자본조달수단(신종자본증권 등) | JPY_million | tier1_basic | 6 | － | － | n/a(not_yet) | 23/3 |  |
| `tier1_non_instrument` | esr | T2 | 資本調達手段以外のTier1適格資本の額 | 자본조달수단 이외 Tier1 적격자본 | JPY_million | tier1_basic |  | 10,730 | 32,118 | n/a(not_yet) | 23/3 | = tier1_ni_retained_earnings + tier1_ni_capital_surplus + tier1_ni_aoci + tier1_ni_other_contrib + tier1_ni_ev_adjustment |
| `tier1_ni_retained_earnings` | esr | T2 | 剰余金等の額又は利益剰余金等の額 | 잉여금등(이익잉여금+규제상 준비금) | JPY_million | tier1_non_instrument | 7 | 5,998 | 18,237 | n/a(not_yet) | 23/3 | = ebs_retained_earnings + ebs_regulatory_reserve_equity |
| `tier1_ni_capital_surplus` | esr | T2 | 資本剰余金(Tier2適格資本に算入されるものを除く)の額 | 자본잉여금(Tier2 산입분 제외) | JPY_million | tier1_non_instrument |  | 2,850 | 8,455 | n/a(not_yet) | 23/3 | == ebs_capital_surplus |
| `tier1_ni_aoci` | esr | T2 | その他の包括利益累計額又は評価・換算差額等の額 | 기타포괄손익누계액(평가·환산차액) | JPY_million | tier1_non_instrument | 9 | － | 2,064 | n/a(not_yet) | 23/3 | == ebs_aoci |
| `tier1_ni_other_contrib` | esr | T2 | その他の拠出金等の額 | 기타 출자금등 | JPY_million | tier1_non_instrument |  | － | － | n/a(not_yet) | 23/3 |  |
| `tier1_ni_ev_adjustment` | esr | T2 | 経済価値ベースの調整額 | 경제가치기준 조정액(EBS 순자산 − 회계 순자산 − 규제상 준비금) | JPY_million | tier1_non_instrument | 11 | 1,882 | 3,362 | n/a(not_yet) | 23/3 | == ebs_ev_adjustment |
| `tier1_adjustments` | esr | T2 | Tier1適格資本に係る調整項目の額 | Tier1 조정항목(C, 공제) | JPY_million | tier1_eligible | 12 | 4,778 | 1,978 | n/a(not_yet) | 23/3 | = Σ tier1_adj_* (7 subs) |
| `tier1_adj_intangibles` | esr | T2 | 無形固定資産(繰延税金負債相殺後)の額 | 무형고정자산(DTL 상계후) | JPY_million | tier1_adjustments |  | 4,778 | 1,978 | n/a(not_yet) | 23/3 | == ebs_intangibles |
| `tier1_adj_dta` | esr | T2 | 繰延税金資産の額 | 이연법인세자산 | JPY_million | tier1_adjustments |  | － | － | n/a(not_yet) | 23/3 |  |
| `tier1_adj_pension_asset` | esr | T2 | 前払年金費用又は退職給付に係る資産 | 선급연금비용/퇴직급여 관련 자산 | JPY_million | tier1_adjustments |  | － | － | n/a(not_yet) | 23/3 |  |
| `tier1_adj_holdings_other_fi` | esr | T2 | 他の金融機関等が意図的に保有しているTier1資本調達手段の額 | 타 금융기관 의도적 보유 Tier1 조달수단 | JPY_million | tier1_adjustments |  | － | － | n/a(not_yet) | 23/3 |  |
| `tier1_adj_own_instruments` | esr | T2 | 自己のTier1資本調達手段への投資の額 | 자기 Tier1 조달수단 투자 | JPY_million | tier1_adjustments |  | － | － | n/a(not_yet) | 23/3 |  |
| `tier1_adj_ineligible_reinsurance` | esr | T2 | 不適格再保険資産の額 | 부적격 재보험자산 | JPY_million | tier1_adjustments |  | － | － | n/a(not_yet) | 23/3 |  |
| `tier1_adj_encumbered_excess` | esr | T2 | 処分制約のある資産のうち関連する負債と所要資本を上回る額 | 처분제약 자산 중 관련부채+소요자본 초과분 | JPY_million | tier1_adjustments |  | － | － | n/a(not_yet) | 23/3 |  |
| `tier2_eligible` | esr | T2 | Tier2適格資本の額 | Tier2 적격자본(D) | JPY_million | eligible_capital | 3 | 175 | 149 | n/a(not_yet) | 23/3 | = tier2_basic - tier2_adjustments - tier2_cap_deduction |
| `tier2_basic` | esr | T2 | Tier2適格資本に係る基礎項目の額 | Tier2 기초항목(E) | JPY_million | tier2_eligible |  | 175 | 149 | n/a(not_yet) | 23/3 | = tier2_instruments + tier2_non_instrument |
| `tier2_instruments` | esr | T2 | Tier2資本調達手段の額 | Tier2 자본조달수단(후순위채 등) | JPY_million | tier2_basic |  | － | － | n/a(not_yet) | 23/3 | = tier2_instr_t1_excess + tier2_instr_paid + tier2_instr_unpaid |
| `tier2_instr_t1_excess` | esr | T2 | 算入制限のあるTier1資本調達手段の制限を超過した額 | 제한초과 Tier1 조달수단(Tier2 재분류) | JPY_million | tier2_instruments | 13 | － | － | n/a(not_yet) | 23/3 |  |
| `tier2_instr_paid` | esr | T2 | 払込済みTier2資本調達手段の額 | 납입완료 Tier2 조달수단 | JPY_million | tier2_instruments |  | － | － | n/a(not_yet) | 23/3 |  |
| `tier2_instr_unpaid` | esr | T2 | 払込未済のTier2資本調達手段の額 | 미납입 Tier2 조달수단(약정자본) | JPY_million | tier2_instruments |  | － | － | n/a(not_yet) | 23/3 |  |
| `tier2_non_instrument` | esr | T2 | 資本調達手段以外のTier2適格資本の額 | 자본조달수단 이외 Tier2 적격자본 | JPY_million | tier2_basic |  | 175 | 149 | n/a(not_yet) | 23/3 | = tier2_ni_surplus_from_instr + tier2_ni_encumbered_t1_deducted + tier2_ni_basket |
| `tier2_ni_surplus_from_instr` | esr | T2 | Tier2資本調達手段の額に含まれる資本調達手段を | Tier2 조달수단 발행 자본잉여금 | JPY_million | tier2_non_instrument |  | － | － | n/a(not_yet) | 23/3 |  |
| `tier2_ni_encumbered_t1_deducted` | esr | T2 | 処分制約のある資産のうちTier1適格資本から控除される額 | 처분제약 자산 중 Tier1 공제분 | JPY_million | tier2_non_instrument |  | － | － | n/a(not_yet) | 23/3 |  |
| `tier2_ni_basket` | esr | T2 | Tier2バスケット(上限適用後)の額 | Tier2 바스켓(상한 적용후) | JPY_million | tier2_non_instrument |  | 175 | 149 | n/a(not_yet) | 23/3 |  |
| `tier2_adjustments` | esr | T2 | Tier2適格資本に係る調整項目の額 | Tier2 조정항목(F) | JPY_million | tier2_eligible |  | － | － | n/a(not_yet) | 23/3 | = tier2_adj_holdings_other_fi + tier2_adj_own_instruments |
| `tier2_adj_holdings_other_fi` | esr | T2 | 他の金融機関等が意図的に保有しているTier2資本調達手段の額 | 타 금융기관 의도적 보유 Tier2 조달수단 | JPY_million | tier2_adjustments |  | － | － | n/a(not_yet) | 23/3 |  |
| `tier2_adj_own_instruments` | esr | T2 | 自己のTier2資本調達手段への投資の額 | 자기 Tier2 조달수단 투자 | JPY_million | tier2_adjustments |  | － | － | n/a(not_yet) | 23/3 |  |
| `tier2_cap_deduction` | esr | T2 | Tier2適格資本への上限適用による控除の額 | Tier2 상한 적용 공제(G) | JPY_million | tier2_eligible |  | － | － | n/a(not_yet) | 23/3 |  |
| `eligible_capital_total` | esr | T2 | 適格資本の額((A)+(D)) / 適格資本の額(A)+(D) | 적격자본 합계(A+D) — T2 표 합계행 | JPY_million |  | 1 | 9,278 | 40,290 | n/a(not_yet) | 23/3 | == eligible_capital |
| `rc_life` | esr | T3 | 生命保険リスクの額 | 생명보험리스크(A) | JPY_million | rc_pre_tax | 17 | － | － | n/a(not_yet) | 24/4 | = sqrt(x^T R x) of rc_life_* subs (告示74 第八十一条 matrix, esr_aggregation_rules.json levels.life) |
| `rc_life_mortality` | esr | T3 | 死亡リスクの額 | 사망리스크 | JPY_million | rc_life | 29 | － | － | n/a(not_yet) |  |  |
| `rc_life_longevity` | esr | T3 | 長寿リスクの額 | 장수리스크 | JPY_million | rc_life | 30 | － | － | n/a(not_yet) |  |  |
| `rc_life_morbidity` | esr | T3 | 罹患及び障害リスクの額 | 이환·장해리스크(질병·상해) | JPY_million | rc_life | 31 | － | － | n/a(not_yet) |  |  |
| `rc_life_lapse` | esr | T3 | 解約及び失効リスクの額 | 해지·실효리스크 | JPY_million | rc_life | 33 | － | － | n/a(not_yet) |  |  |
| `rc_life_expense` | esr | T3 | 経費リスクの額 | 사업비리스크 | JPY_million | rc_life | 34 | － | － | n/a(not_yet) |  |  |
| `rc_life_mgmt_action` | esr | T3 | マネジメント・アクションの効果の額 | 경영조치 효과(생보, 정보행 — 하위액에 이미 반영) | JPY_million | rc_life |  | － | － | n/a(not_yet) |  |  |
| `rc_nonlife` | esr | T3 | 損害保険リスクの額 | 손해보험리스크(B) | JPY_million | rc_pre_tax | 18 | 1,119 | 2,096 | n/a(not_yet) | 24/4 | <= rc_nl_liability + rc_nl_motor + rc_nl_property + rc_nl_other (correlation aggregation) |
| `rc_nl_liability` | esr | T3 | 賠償責任保険類似の商品に係るリスクの額 | 배상책임보험 유사 상품 리스크 | JPY_million | rc_nonlife |  | － | 283 | n/a(not_yet) | 24/4 |  |
| `rc_nl_motor` | esr | T3 | 自動車保険類似の商品に係るリスクの額 | 자동차보험 유사 상품 리스크 | JPY_million | rc_nonlife |  | － | 0 | n/a(not_yet) | 24/4 |  |
| `rc_nl_property` | esr | T3 | 財物保険類似の商品に係るリスクの額 | 재물보험 유사 상품 리스크 | JPY_million | rc_nonlife |  | 159 | 518 | n/a(not_yet) | 24/4 |  |
| `rc_nl_other` | esr | T3 | その他保険に係るリスクの額 | 기타보험 리스크 | JPY_million | rc_nonlife |  | 1,031 | 1,657 | n/a(not_yet) | 24/4 |  |
| `rc_catastrophe` | esr | T3 | 巨大災害リスクの額 | 거대재해리스크(C) | JPY_million | rc_pre_tax |  | 87 | 1,865 | n/a(not_yet) | 24/4 | <= rc_cat_natural + rc_cat_other - rc_cat_mgmt_action |
| `rc_cat_natural` | esr | T3 | 巨大自然災害リスクの額 | 거대자연재해리스크 | JPY_million | rc_catastrophe |  | － | 1,748 | n/a(not_yet) | 24/4 | <= rc_cat_nat_jp_earthquake + rc_cat_nat_jp_windflood + rc_cat_nat_jp_snow + rc_cat_nat_foreign + rc_cat_nat_other |
| `rc_cat_nat_jp_earthquake` | esr | T3 | 日本における地震に係るリスクの額 | 일본 지진 | JPY_million | rc_cat_natural |  | － | 546 | n/a(not_yet) | 24/4 |  |
| `rc_cat_nat_jp_windflood` | esr | T3 | 日本における風水災に係るリスクの額 | 일본 풍수해 | JPY_million | rc_cat_natural |  | － | 1,447 | n/a(not_yet) | 24/4 |  |
| `rc_cat_nat_jp_snow` | esr | T3 | 日本における雪災に係るリスクの額 | 일본 설해 | JPY_million | rc_cat_natural |  | － | 374 | n/a(not_yet) | 24/4 |  |
| `rc_cat_nat_foreign` | esr | T3 | 外国における巨大自然災害リスクの額 | 해외 거대자연재해 | JPY_million | rc_cat_natural |  | － | 156 | n/a(not_yet) | 24/4 |  |
| `rc_cat_nat_other` | esr | T3 | その他の額 | 기타(거대자연재해 내) | JPY_million | rc_cat_natural |  | － | － | n/a(not_yet) | 24/4 |  |
| `rc_cat_other` | esr | T3 | その他の巨大災害に係るリスクの額 | 기타 거대재해(팬데믹·테러 등) | JPY_million | rc_catastrophe |  | 87 | 918 | n/a(not_yet) | 24/4 |  |
| `rc_cat_mgmt_action` | esr | T3 | マネジメント・アクションの効果の額 | 경영조치 효과(거대재해) | JPY_million | rc_catastrophe |  | － | － | n/a(not_yet) | 24/4 |  |
| `rc_market` | esr | T3 | 市場リスクの額 | 시장리스크(D) | JPY_million | rc_pre_tax | 19 | 247 | 4,613 | n/a(not_yet) | 24/4 | <= rc_mkt_interest + rc_mkt_spread + rc_mkt_equity + rc_mkt_property + rc_mkt_fx + rc_mkt_concentration - rc_mkt_mgmt_action |
| `rc_mkt_interest` | esr | T3 | 金利リスクの額 | 금리리스크 | JPY_million | rc_market | 36 | － | 665 | n/a(not_yet) | 24/4 |  |
| `rc_mkt_spread` | esr | T3 | スプレッドリスクの額 | 스프레드리스크 | JPY_million | rc_market |  | 0 | － | n/a(not_yet) | 24/4 |  |
| `rc_mkt_equity` | esr | T3 | 株式リスクの額 | 주식리스크 | JPY_million | rc_market | 37 | － | 2,218 | n/a(not_yet) | 24/4 |  |
| `rc_mkt_property` | esr | T3 | 不動産リスクの額 | 부동산리스크 | JPY_million | rc_market | 38 | － | 1,591 | n/a(not_yet) | 24/4 |  |
| `rc_mkt_fx` | esr | T3 | 為替リスクの額 | 환리스크 | JPY_million | rc_market | 39 | － | 1,681 | n/a(not_yet) | 24/4 |  |
| `rc_mkt_concentration` | esr | T3 | 資産集中リスクの額 | 자산집중리스크 | JPY_million | rc_market | 40 | 247 | 1,412 | n/a(not_yet) | 24/4 |  |
| `rc_mkt_mgmt_action` | esr | T3 | マネジメント・アクションの効果の額 | 경영조치 효과(시장) | JPY_million | rc_market |  | － | － | n/a(not_yet) | 24/4 |  |
| `rc_credit` | esr | T3 | 信用リスクの額 | 신용리스크(E) | JPY_million | rc_pre_tax | 20 | 78 | 475 | n/a(not_yet) | 24/4 |  |
| `rc_operational` | esr | T3 | オペレーショナル・リスクの額 | 운영리스크(F) | JPY_million | rc_pre_tax | 21 | 251 | 463 | n/a(not_yet) | 24/4 |  |
| `rc_mgmt_action_excess` | esr | T3 | マネジメント・アクションの効果の上限超過額 | 경영조치 효과 상한초과액(G, 가산) | JPY_million | rc_pre_tax |  | － | － | n/a(not_yet) | 24/4 |  |
| `rc_diversification` | esr | T3 | 分散効果の額 | 분산효과(H, 차감) | JPY_million | rc_pre_tax | 16 | 274 | 2,530 | n/a(not_yet) | 24/4 |  |
| `rc_pre_tax` | esr | T3 | 所要資本の額(税効果考慮前) | 소요자본(세효과 고려전, I/J) | JPY_million | required_capital | 15 | 1,510 | 6,985 | n/a(not_yet) | 24/4 | = rc_life + rc_nonlife + rc_catastrophe + rc_market + rc_credit + rc_operational + rc_mgmt_action_excess - rc_diversification + rc_non_insurance_business |
| `rc_tax_effect` | esr | T3 | 所要資本の税効果の額 | 소요자본 세효과(J/K, 차감) | JPY_million | required_capital | 22 | 338 | 1,564 | n/a(not_yet) | 24/4 |  |
| `rc_post_tax` | esr | T3 | 所要資本の額(税効果考慮後) | 소요자본(세효과 고려후) — T3 합계행 | JPY_million |  | 14 | 1,171 | 5,420 | n/a(not_yet) | 24/4 | = rc_pre_tax - rc_tax_effect; == required_capital |
| `ebs_total_assets` | esr | T4 | 総資産 | EBS 총자산 | JPY_million |  |  | 22,664 | 64,031 | n/a(not_yet) | 25/5 | = statutory + reclass + revaluation (row-wise) |
| `ebs_intangibles` | esr | T4 | 無形固定資産 | EBS 무형고정자산 | JPY_million | ebs_total_assets |  | 4,778 | 1,978 | n/a(not_yet) | 25/5 | == tier1_adj_intangibles |
| `ebs_reinsurance_recoverables` | esr | T4 | 再保険回収額 | EBS 재보험회수액 | JPY_million | ebs_total_assets |  | 1,575 | 142 | n/a(not_yet) | 25/5 |  |
| `ebs_total_liabilities` | esr | T4 | 総負債 | EBS 총부채 | JPY_million |  |  | 8,783 | 21,912 | n/a(not_yet) | 25/6 | = ebs_insurance_liabilities + ebs_non_insurance_liabilities |
| `ebs_insurance_liabilities` | esr | T4 | 保険負債(保険契約準備金)合計 | EBS 보험부채 합계 | JPY_million | ebs_total_liabilities |  | 4,969 | 7,306 | n/a(not_yet) | 25/6 | = ebs_current_estimate + ebs_moce |
| `ebs_current_estimate` | esr | T4 | 現在推計の額 | 현재추계(최선추정부채, BEL) | JPY_million | ebs_insurance_liabilities |  | 4,917 | 7,099 | n/a(not_yet) | 25/6 |  |
| `ebs_moce` | esr | T4 | 現在推計を超えるマージン | MOCE(현재추계 초과 마진, 위험마진) | JPY_million | ebs_insurance_liabilities |  | 51 | 207 | n/a(not_yet) | 25/6 |  |
| `ebs_reg_reserve_in_liabilities` | esr | T4 | 規制上の準備金に属するもの | 규제상 준비금(위험준비금·이상위험준비금 등, 회계기준 보험부채 내) — イ열 | JPY_million | ebs_insurance_liabilities |  | 2,222 | 14,879 | n/a(not_yet) | 25/6 | reclassified to equity (ロ열 △) |
| `ebs_non_insurance_liabilities` | esr | T4 | 非保険負債合計 | EBS 비보험부채 합계 | JPY_million | ebs_total_liabilities |  | 3,814 | 14,605 | n/a(not_yet) | 25/6 |  |
| `ebs_other_reserves_reclass` | esr | T4 | その他の準備金 | 기타 준비금(부채로 재분류된 규제상 준비금 일부) — ニ열 | JPY_million | ebs_non_insurance_liabilities |  | － | 322 | n/a(not_yet) | 6 |  |
| `ebs_price_fluctuation_reserve` | esr | T4 | 価格変動準備金 | 가격변동준비금(회계기준, 자본으로 재분류) — イ열 | JPY_million | ebs_non_insurance_liabilities |  | － | 831 | n/a(not_yet) | 6 |  |
| `ebs_net_assets` | esr | T4 | 純資産 | EBS 순자산 | JPY_million |  | 4 | 13,880 | 42,118 | n/a(not_yet) | 25/7 | = ebs_total_assets - ebs_total_liabilities; == tier1_basic; = ebs_net_assets_statutory + ebs_regulatory_reserve_equity + ebs_ev_adjustment |
| `ebs_net_assets_statutory` | esr | T4 | 純資産 | 회계기준 순자산(EBS 표 イ열) | JPY_million | ebs_net_assets |  | 9,776 | 23,367 | n/a(not_yet) | 25/7 |  |
| `ebs_capital_stock` | esr | T4 | 基金又は資本金 / 資本金 | 자본금/기금 | JPY_million | ebs_net_assets |  | 3,150 | 10,000 | n/a(not_yet) | 25/7 |  |
| `ebs_capital_surplus` | esr | T4 | 資本剰余金 | 자본잉여금 | JPY_million | ebs_net_assets |  | 2,850 | 8,455 | n/a(not_yet) | 25/7 |  |
| `ebs_retained_earnings` | esr | T4 | 剰余金又は利益剰余金 / 利益剰余金 | 이익잉여금 | JPY_million | ebs_net_assets |  | 3,776 | 2,847 | n/a(not_yet) | 25/7 |  |
| `ebs_regulatory_reserve_equity` | esr | T4 | 規制上の準備金 | 규제상 준비금(자본으로 재분류된 합계) — ニ열 | JPY_million | ebs_net_assets |  | 2,222 | 15,389 | n/a(not_yet) | 25/7 | ≈ ebs_reg_reserve_in_liabilities + ebs_price_fluctuation_reserve - ebs_other_reserves_reclass (observed bridge) |
| `ebs_aoci` | esr | T4 | その他の包括利益累計額合計 / その他の包括利益累計額 | 기타포괄손익누계액 | JPY_million | ebs_net_assets |  | － | 2,064 | n/a(not_yet) | 7 |  |
| `ebs_ev_adjustment` | esr | T4 | 経済価値ベースの調整額 | 경제가치기준 조정액 | JPY_million | ebs_net_assets | 11 | 1,882 | 3,362 | n/a(not_yet) | 25/7 |  |
| `il_total_ex_moce` | esr | T6 | 保険負債 | 보험부채(MOCE 제외) 경제가치 | JPY_million |  |  | 4,917 | 7,099 | n/a(not_yet) | 28/11 | == ebs_current_estimate |
| `il_unexpired` | esr | T6 | 未経過責任に係る保険負債 | 미경과책임 보험부채(LRC 상당) | JPY_million | il_total_ex_moce |  | 2,020 | 823 | n/a(not_yet) | 28/11 |  |
| `il_incurred` | esr | T6 | 既経過責任に係る保険負債 | 기경과책임 보험부채(LIC 상당) | JPY_million | il_total_ex_moce |  | 2,897 | 6,275 | n/a(not_yet) | 28/11 |  |
| `rc_non_insurance_business` | esr | T1_combined | 非保険事業に係る所要資本の額 | 비보험사업 소요자본(i) — au 결합표에만 있는 행 | JPY_million | rc_pre_tax | 23 | － | － | n/a(not_yet) | 22 |  |
| `tier1_ratio_pct` | esr | derived |  | 기본자본비율 상당 = tier1_eligible / required_capital × 100 (일본 미공시, 파생) | pct | esr_pct | 28 | 777.3 | 740.6 | n/a(not_yet) |  | = tier1_eligible / required_capital * 100 |
| `esr_pct_5yr_summary` | esr | summary_5yr | 単体ベースのソルベンシー・マージン比率 / ソルベンシー・マージン比率 新基準 | 5개년 주요지표 표의 헤드라인(교차확인용) | pct | esr_pct |  | 791.7 | － | n/a(not_yet) | 2 | == esr_pct |
| `sens_jpy_rate_up50_esr_pct` | esr | T7 | 円金利50ベーシス・ポイント上昇 | 민감도 ESR: 엔 금리 +50bp | pct | esr_pct |  |  | 736.7 | n/a(not_yet) | 29/12 | levels row ソルベンシー・マージン比率 × column; ESR-under-shock — K-ICS 는 kics_rate_sensitivity.json(별도 마스터, 항목번호 없음) |
| `sens_jpy_rate_down50_esr_pct` | esr | T7 | 円金利50ベーシス・ポイント下降 | 민감도 ESR: 엔 금리 -50bp | pct | esr_pct |  |  | 750.1 | n/a(not_yet) | 29/12 | levels row ソルベンシー・マージン比率 × column; ESR-under-shock — K-ICS 는 kics_rate_sensitivity.json(별도 마스터, 항목번호 없음) |
| `sens_usd_rate_up50_esr_pct` | esr | T7 | 米ドル金利50ベーシス・ポイント上昇 | 민감도 ESR: 달러 금리 +50bp | pct | esr_pct |  |  | 743.3 | n/a(not_yet) | 29/12 | levels row ソルベンシー・マージン比率 × column; ESR-under-shock — K-ICS 는 kics_rate_sensitivity.json(별도 마스터, 항목번호 없음) |
| `sens_usd_rate_down50_esr_pct` | esr | T7 | 米ドル金利50ベーシス・ポイント下降 | 민감도 ESR: 달러 금리 -50bp | pct | esr_pct |  |  | 743.2 | n/a(not_yet) | 29/12 | levels row ソルベンシー・マージン比率 × column; ESR-under-shock — K-ICS 는 kics_rate_sensitivity.json(별도 마스터, 항목번호 없음) |
| `sens_jpy_ufr_down50_esr_pct` | esr | T7 | 円金利UFR50ベーシス・ポイント下降 | 민감도 ESR: 엔 UFR -50bp | pct | esr_pct |  |  | 743.2 | n/a(not_yet) | 29/12 | levels row ソルベンシー・マージン比率 × column; ESR-under-shock — K-ICS 는 kics_rate_sensitivity.json(별도 마스터, 항목번호 없음) |
| `sens_equity_property_down10_esr_pct` | esr | T7 | 株式・不動産10%下落 | 민감도 ESR: 주식·부동산 -10% | pct | esr_pct |  |  | 764.4 | n/a(not_yet) | 29/12 | levels row ソルベンシー・マージン比率 × column; ESR-under-shock — K-ICS 는 kics_rate_sensitivity.json(별도 마스터, 항목번호 없음) |
| `sens_fx_yen_up10_esr_pct` | esr | T7 | 為替10%円高 | 민감도 ESR: 환율 10% 엔고 | pct | esr_pct |  |  | 755.9 | n/a(not_yet) | 29/12 | levels row ソルベンシー・マージン比率 × column; ESR-under-shock — K-ICS 는 kics_rate_sensitivity.json(별도 마스터, 항목번호 없음) |
| `internal_model_applied` | esr | T8 | 内部モデル手法の適用 | 내부모형 적용 여부 | flag |  |  | unstated | False | n/a(not_yet) |  |  |
| `usp_applied` | esr | T8 | 会社固有のストレス係数手法の適用 | 회사고유 스트레스계수(USP) 적용 여부 | flag |  |  | unstated | False | n/a(not_yet) |  |  |
| `internal_discount_rate_applied` | esr | T8 | 内部割引率手法の適用 | 내부할인율 적용 여부 | flag |  |  | unstated | False | n/a(not_yet) |  |  |
| `mgmt_action_applied` | esr | T8 | マネジメント・アクション | 경영조치(management action) 반영 여부 | flag |  |  | unstated | False | n/a(not_yet) |  |  |
| `risk_mitigation_reinsurance` | esr | T8 | リスク削減手法 / リスク削減効果 | 재보험 리스크경감 반영 여부 | flag |  |  | True | True | n/a(not_yet) |  |  |
| `transitional_measures` | esr | T8 | 経過措置 / 激変緩和 | 경과조치(激変緩和措置) 적용 여부 | flag |  |  | False | False | n/a(not_yet) |  |  |
| `sensitivity_omitted` | esr | T8 | 記載を省略 | 민감도 표 생략 여부(차이 1%p 미만 사유) | flag |  |  | True | False | n/a(not_yet) |  |  |
| `first_year_no_movement_analysis` | esr | T8 | 変動要因分析 | 변동요인분석 미기재(초년도) | flag |  |  | True | False | n/a(not_yet) |  |  |
| `calc_method` | esr | T8 | 内部モデル手法の適用 / 標準的手法 | 산정방식 standard / standard_implied / internal_model | enum |  |  | standard_implied | standard | n/a(not_yet) |  | derived from internal_model_applied |
| `discount_bucket_jpy` | esr | T8 | 適用バケット / 一般バケット / ミドルバケット / トップバケット | 엔화 할인율 버킷 | enum |  |  | 一般バケット | 一般バケット | n/a(not_yet) |  |  |
| `discount_rates_jpy` | esr | T8 | 主な通貨 / 主要な年限ごとの割引率 | 엔화 할인율(연한별 %) | pct_by_tenor |  |  | {'1y': 1.21, '2y': 1.447, '3y': 1.576} | {'5y': 1.889, '10y': 2.49, '15y': 3.013, '20y': 3.579} | n/a(not_yet) |  |  |
| `esr_status` | article_axes | axes:esr_placeholder | 後日公表予定 / 別途公表予定 / 2026年10月末に公表予定 | posted / not_yet / not_found | enum |  |  | posted | posted | not_yet |  |  |
| `esr_placeholder_locations` | article_axes | axes:esr_placeholder | ソルベンシー・マージン比率 新基準 / 保険金等の支払能力の充実の状況（ソルベンシー・マージン比率） | '後日公表予定' 문구가 놓인 표/절 위치 목록(10월에 채워질 자리) | list |  |  | － | － | 3 loc |  |  |
| `smr_old_basis_fy2024_pct` | article_axes | axes:esr_placeholder | ソルベンシー・マージン比率 旧基準 | 구기준 SMR FY2024 (비교 참고, ESR 아님) | pct |  |  | － | － | 863.9 |  |  |
| `cat_reserve_total` | article_axes | axes:catastrophe_reserve_adequacy | 異常危険準備金 / 責任準備金の内訳 | 이상위험준비금 잔액 합계(전 종목) | JPY_million |  |  | 2,222 | － | － |  |  |
| `cat_reserve_fire` | article_axes | axes:catastrophe_reserve_adequacy | 火災 行 × 異常危険準備金 列 | 화재 종목 이상위험준비금 잔액(금융청 부족 지적 대상) | JPY_million |  |  | － | － | － |  |  |
| `cat_reserve_by_line` | article_axes | axes:catastrophe_reserve_adequacy | 火災/海上/傷害/自動車/自動車損害賠償責任/その他 | 종목별 이상위험준비금 잔액 | dict |  |  | {"火災": null, "海上": null, "傷害": 1421, "自動車": null, "自動車損害賠償責任": null, "その他": 800} | － | － |  |  |
| `ordinary_reserve_total` | article_axes | axes:catastrophe_reserve_adequacy | 普通責任準備金 | 보통책임준비금 합계(같은 표) | JPY_million |  |  | 3,259 | － | － |  |  |
| `cat_reserve_adequacy_note` | article_axes | axes:catastrophe_reserve_adequacy | 積立不足 / 積立率 / 異常危険準備金の取崩 | 적립 부족/적립률 서술 유무 (없으면 null) | text |  |  | － | NOT_IN_SAMPLE_DOC (別冊 業績データ has no 責任準備金の内訳 table — main disclosure volume needed) | － |  |  |
| `air_used` | article_axes | axes:air_used | アセット・インテンシブ / 資産集約型再保険 / 再保険 | not_mentioned / mentioned / mentioned_esr_purpose | enum |  |  | not_mentioned | not_mentioned | not_mentioned |  |  |
| `air_evidence` | article_axes | axes:air_used | 既契約の出再に伴う損益 / 共同保険式再保険 / 最低保証再保険 | AIR 정황 근거(기계약 출재 손익·관계사 재보험 각주 등) | text |  |  | － | － | 基礎利益 note: 既契約の出再に伴う損益を除外 (in-force block cession P&L excluded from core profit); 関連当事者取引 note: 共同保険式再保険・最低保証再保険 (coinsurance-type / guarantee reinsurance with group company) |  |  |
| `inforce_cession_pl` | article_axes | axes:air_used | 既契約の出再に伴う損益に相当する額 | 기계약 출재 관련 손익(기초이익에서 제외된 액) | JPY_million |  |  | － | － | -3,733 |  |  |
| `reins_counterparties_n` | article_axes | axes:air_used | 出再先保険会社の数 / 再保険を引き受けた主要な保険会社等の数 | 출재 상대 재보험사 수 | count |  |  | 5 | － | 5 |  |  |
| `reins_top5_share_pct` | article_axes | axes:air_used | 出再保険料のうち上位5社の出再先に集中している割合 / 支払再保険料の金額が大きい上位5社に対する支払再保険料の割合 | 상위 5사 출재보험료 집중도 | pct |  |  | 100.0 | － | 100.0 |  |  |
| `reins_rating_a_or_above_pct` | article_axes | axes:air_used | 出再保険料の格付ごとの割合 / 格付機関による格付に基づく区分ごとの支払再保険料の割合 | A등급 이상 재보험사 출재보험료 비중 | pct |  |  | 80.0 | － | 100.0 |  |  |
| `reins_unreceived_claims` | article_axes | axes:air_used | 未だ収受していない再保険金の金額 | 미수 재보험금 | JPY_million |  |  | － | － | 17,042 |  |  |
| `core_profit` | article_axes | axes:interest_margin_sign | 基礎利益 | 기초이익(당기) | JPY_million |  |  | － | － | 18,523 |  |  |
| `core_profit_prev` | article_axes | axes:interest_margin_sign | 基礎利益 | 기초이익(전기) | JPY_million |  |  | － | － | 14,828 |  |  |
| `negative_spread_100m` | article_axes | axes:interest_margin_sign | 逆ざや / 逆鞘 | 역마진(逆ざや) 금액 — 단위 億円(표본 원문 단위) — 양수=역마진 존재 | JPY_100million |  |  | － | － | 37 |  |  |
| `negative_spread_prev_100m` | article_axes | axes:interest_margin_sign | 逆ざや | 역마진 전기(億円) | JPY_100million |  |  | － | － | 67 |  |  |
| `interest_margin` | article_axes | axes:interest_margin_sign | 利差損益 / 利差益 / 利差損 / 順ざや | 이차손익(三利源 공시사에서만) | JPY_million |  |  | － | － | － |  |  |
| `interest_margin_sign` | article_axes | axes:interest_margin_sign | 利差損益 / 逆ざや / 順ざや | positive / negative / unstated (역마진이면 negative) | enum |  |  | － | － | negative |  |  |
| `three_source_disclosed` | article_axes | axes:interest_margin_sign | 利差損益 / 危険差損益 / 費差損益 | 三利源(利差·危険差·費差) 분해 공시 여부 | bool |  |  | － | － | False |  |  |

## 4. 검산식과 결과 (`run_checks` / `run_axes_checks`)

허용오차 원칙: 금액은 百万円 미만 **절사**(au 주기 5 "記載単位未満を切り捨て")라, 합계행 = Σ내역 검산은 항 수만큼 ±1 씩 벌어질 수 있다. 비율은 분자·분모 각각 [x, x+1) 구간이라 **구간 검산**.

| id | 식 | 오차 | au | MY | 비고 |
|---|---|---|---|---|---|
| C01 | `esr_pct ∈ [E/(R+1), (E+1)/R]×100` | ±0.05 | 791.7 ∈ [791.64, 792.40] | 743.2 ∈ [743.22, 743.38] | 점추정 792.31 / 743.36 — **소수 첫째자리 반올림으로는 안 맞는다**, 구간으로만 맞는다 |
| C02 | `eligible_capital == eligible_capital_total` (T1 == T2 합계행) | 0 | 9,278 | 40,290 | |
| C03 | `required_capital == rc_post_tax` (T1 == T3 합계행) | 0 | 1,171 | 5,420 | |
| C04 | `eligible = tier1 + tier2` | ±1 | 9,102+175=9,277 vs 9,278 | 40,140+149=40,289 vs 40,290 | 둘 다 절사 1 차이 |
| C05 | `tier1 = tier1_basic − tier1_adjustments` | ±1 | 13,880−4,778 | 42,118−1,978 | |
| C06 | `tier1_basic = 無制限調達手段 + 制限付 + 調達手段以外` | ±1 | 3,150+10,730 | 10,000+32,118 | |
| C07 | `調達手段以外 = 剰余金等 + 資本剰余金 + AOCI + 拠出金 + 経済価値調整額` | ±2 | 5,998+2,850+0+0+1,882 | 18,237+8,455+2,064+0+3,362 | |
| C08 | `tier1_adjustments = Σ 7개 공제` | ±2 | 4,778 (무형만) | 1,978 (무형만) | |
| C09~C11 | Tier2 (D)=(E)−(F)−(G), (E)=조달수단+그 외, 그 외 = 3 내역 | ±1 | 175 | 149 | 두 회사 모두 Tier2 = バスケット 뿐 |
| C12 | `rc_pre_tax = A+B+C+D+E+F+G − H (+ 非保険事業)` | ±9 | 1,508 vs 1,510 | 6,982 vs 6,985 | 항별 절사 누적 |
| C13 | `rc_post_tax = rc_pre_tax − rc_tax_effect` | ±1 | 1,510−338=1,172 vs 1,171 | 6,985−1,564=5,421 vs 5,420 | |
| C14~C17 | 부모 리스크 ≤ Σ 하위 (상관 통합이라 단순합 아님, 표 주기) | ≤ | 損保 1,119 ≤ 1,190 · 市場 247 = 247 | 損保 2,096 ≤ 2,458 · 巨大災害 1,865 ≤ 2,666 · 自然災害 1,748 ≤ 2,523 · 市場 4,613 ≤ 7,567 | 부등식은 1차 방어선일 뿐 — **등식은 §8 의 √(xᵀRx) 재계산(G05~G08, G10)** 이 정본 |
| C18 | `tier1_basic == ebs_net_assets` | 0 | 13,880 | 42,118 | T2 ↔ T4 교차 |
| C19 | `ebs_net_assets = 総資産 − 総負債` | ±1 | 22,664−8,783=13,881 | 64,031−21,912=42,119 | |
| C20 | `総負債 = 保険負債 + 非保険負債` | ±1 | 4,969+3,814 | 7,306+14,605 | |
| C21 | `保険負債 = 現在推計 + MOCE` | ±1 | 4,917+51=4,968 | 7,099+207 | |
| C22 | `EBS 純資産 = 회계 純資産 + 規制上の準備金 + 経済価値調整額` | ±1 | 9,776+2,222+1,882 | 23,367+15,389+3,362 | 회계→경제가치 순자산 브리지 |
| C23~C27 | T2 내역 ↔ T4 자본항목 교차(調整額·無形·資本剰余金·剰余金等=利益剰余金+規制上準備金·AOCI) | 0~±1 | 전부 일치 | 18,237 = 2,847+15,389 (Δ1) | |
| C28~C29 | T6 `保険負債(MOCE除く) == 現在推計`, `= 未経過 + 既経過` | ±1 | 4,917 = 2,020+2,897 | 7,099 = 823+6,275 (Δ1) | |
| C30 | 5개년 표 헤드라인 == esr_pct | 0 | 791.7 | (별책엔 5개년 표 없음) | |
| C31 | 민감도 基準열 == 헤드라인(9행) 또는 생략 주기 존재 | 0 | 생략 주기 확인 | 9/9 일치 | au 는 "差の絶対値がいずれも1%未満" 주기로 값 생략 |
| C32 | 差額表 = 水準表 − 基準 (pct ±0.15, 금액 ±1) | count | — | 57/57 | 절사로 447 vs 448 같은 1 차이 발생 |
| C33 | 시나리오별 esr == eligible/required 구간 | count | — | 7/7 | |
| C34 | `規制上の準備金(자본) = 危険準備金等(부채 イ열) + 価格変動準備金 − その他の準備金(ニ열)` | ±2 | 2,222 = 2,222 | 15,389 ≈ 14,879+831−322 = 15,388 | 표본 2건 관측식(告示 정의 확인 전) |
| A01 | `規制上の準備金 == 異常危険準備金 합계 (+価格変動準備金)` | ±1 | 2,222 == 2,222 | (별책에 표 없음) | au 는 이상위험준비금이 유일한 규제상 준비금 |
| A02 | 출재 격付 비중 합 = 100 | ±0.2 | 80+0+20 | — | NN Life 10.8+88.8+0.4 |
| A03~A04 | 基礎利益 정수 파싱 / `interest_margin_sign == negative ⇔ 逆ざや > 0` | — | — | — | NN Life 37億円 → negative |
| A05 | `esr_status == not_yet` 이면 placeholder 위치 ≥ 1 | — | — | — | NN Life 3곳 |

결과: **au 34/34, Meiji Yasuda Non-Life 41/41, NN Life 4/4 통과, census 헤드라인 2/2 일치, NN Life census `not_yet` 일치.**

## 5. 추출 규칙 (10월 62사 적용)

1. **라벨 정규화**: 줄 단위 NFKC → `（A）`→`(A)`, `Tier１`→`Tier1`, `－`→`-`. 대시 집합 `- ー − ― ‐` 는 null. `△`/`▲` 접두 = 음수. `%` 접미 허용.
2. **열 순서**: FY2025 는 모든 표가 `イ=前年度(－) / ロ=当年度 (/ ハ=増減)` — 값 토큰 **2번째**가 당기. FY2026 부터는 前年度 열이 채워지므로 같은 규칙으로 2번째 = 당기(증감 열 유무 무관). EBS 는 4열이라 마지막 토큰 = 経済価値, 첫 토큰 = 財務会計(4토큰 행에서만).
3. **중복 라벨은 순차 커서**: `マネジメント・アクションの効果の額` 은 巨大災害 안·市場 안 두 번, `財物保険類似` 등은 T6 에 여러 번. 표 안에서 앞 항목 매치 위치 다음부터 찾는다(ITEMS 순서 = 양식 행 순서).
4. **라벨 뒤 코드/계속줄 건너뛰기**: `(A)`, `①`, `(a)+(b)+…`, `（（J）－（K））`, 줄바꿈된 라벨 후반부(`余金の額`, `金に属するもの以外）`)가 값 앞에 최대 6줄 끼어든다.
5. **행 생략 회사**: au 는 EBS 에서 값이 전부 대시인 행을 통째로 뺀다(`価格変動準備金`·`その他の包括利益累計額`·`コールローン` 등). MY 는 양식 전 행을 찍는다. → 못 찾은 행은 `ROW_OMITTED`(=0) 로 두고 실패로 치지 않는다. T2·T3 는 두 회사 다 전 행 인쇄.
6. **정성 플래그는 정성 페이지(T8)+민감도 페이지(T7)에서만 검색**한다. 전체 문서에서 `マネジメント・アクション` 을 찾으면 T3 행 라벨에 걸려 "적용" 으로 오판한다(실측 사고, 수정됨). MY 처럼 항목식(`該当ありません`)이면 False, au 처럼 언급이 없으면 `unstated`.
7. **`calc_method`**: `内部モデル手法の適用 該当ありません` → `standard`; 언급 없음 → `standard_implied`(규제상 내부모형은 승인·공시 의무라 무언급 = 표준식으로 본다, 단 census 에는 구분 유지). `confidence_level` 은 양식에 없다 — 告示 표준식 = 1년 VaR 99.5% 고정이라 `standard` 면 99.5 로 채운다.
8. **경과조치(激変緩和措置)**: 두 표본 모두 `経過措置` 문자열 0건 → 양식에 경과조치 표가 없다. 회사가 적용하면 정성 절 "その他の重要な前提及び手法" 에 문장으로 나올 것이므로 그 절에서 검색(`transitional_measures` 플래그). 한국 K-ICS 처럼 적용전/적용후 2열 표는 **없다**.
9. 헤드라인 5개년 표(au p2·NN p11): 열이 **오래된→최신** 순, 신기준은 마지막 열만 값. `esr_pct_5yr_summary` = 페이지의 마지막 `%` 토큰.

## 6. K-ICS 대응 (`kics_item_ref`) — 억지 대응 금지 원칙

| J-ESR id | K-ICS | 대응 성격 |
|---|---|---|
| `eligible_capital` / `eligible_capital_total` | 1 지급여력금액 | 정확 |
| `required_capital` / `rc_post_tax` | 14 지급여력기준금액 | 정확(둘 다 세효과 후) |
| `esr_pct` | 27 지급여력비율 | 정확 |
| `tier1_eligible` / `tier2_eligible` | 2 기본자본 / 3 보완자본 | 정확 |
| `tier1_basic` / `ebs_net_assets` | 4 건전성감독기준 재무상태표 순자산 | 근사(일본 Tier1 기초항목 = EBS 순자산 그대로; 한국 4 도 감독기준 BS 순자산) |
| `tier1_instr_unrestricted` / `tier1_instr_restricted` | 5 보통주 / 6 보통주 이외 자본증권 | 근사(일본은 資本金·基金 = 무제한 조달수단; 한국 5 는 보통주 자본금+주식발행초과금 범위가 다를 수 있음) |
| `tier1_ni_retained_earnings` | 7 이익잉여금 | 근사(일본은 規制上の準備金 포함) |
| `tier1_ni_aoci` | 9 기타포괄손익누계액 | 정확 |
| `tier1_ni_ev_adjustment` / `ebs_ev_adjustment` | 11 조정준비금 | 근사(둘 다 회계 순자산→감독 순자산 차이 계정) |
| `tier1_adjustments` | 12 불인정 항목 | 부분(한국 12 는 예정배당 등, 일본 (C) 는 무형·DTA·자기보유 등 — 공제라는 위치만 같다) |
| `tier2_instr_t1_excess` | 13 보완자본 재분류 항목 | 정확 |
| `rc_pre_tax` | 15 기본요구자본 | 근사(일본은 非保険事業 (i) 포함, 한국 15 는 미포함·23 별도) |
| `rc_diversification` | 16 분산효과 | 정확(부호: 둘 다 차감) |
| `rc_life` | 17 생명장기손해보험위험액 | 부분(한국 17 은 장기손보 포함) |
| `rc_life_mortality/longevity/morbidity/lapse/expense` | 29/30/31/33/34 | 정확(사망·장수·장해질병·해지·사업비; 한국 32 장기재물·기타, 35 대재해는 일본 생보 하위에 없음 — 대재해는 巨大災害 (C) 로 별도) |
| `rc_nonlife` | 18 일반손해보험위험액 | 부분(한국 18 은 대재해 포함, 일본은 巨大災害 (C) 별도) |
| `rc_catastrophe`, `rc_cat_*` | — | **null**: 한국 대재해는 18 내부(별도 번호 없음). 35 대재해위험액은 생명장기 하위라 다른 개념 |
| `rc_market` | 19 시장위험액 | 정확 |
| `rc_mkt_interest/equity/property/fx/concentration` | 36/37/38/39/40 | 정확 |
| `rc_mkt_spread` | — | **null**: K-ICS 시장위험에 스프레드 없음(신용스프레드는 신용위험) |
| `rc_credit` / `rc_operational` | 20 / 21 | 정확 |
| `rc_tax_effect` | 22 법인세조정액 | 정확 |
| `rc_non_insurance_business` | 23 기타 요구자본 | 근사 |
| `tier1_ratio_pct` (파생) | 28 기본자본비율 | 정확(일본 미공시라 tier1/required 로 파생) |
| 민감도 `純資産の額` × 円金利 ±50bp | 41(충격전)/43(상승)/44(하락) | 근사(K-ICS 는 규정 충격 시나리오, 일본은 50bp 평행) — 스키마 `sensitivity.rows[].kics_item_ref` |
| `sens_*_esr_pct` | — | null: 한국은 ESR-under-shock 항목이 없고 `kics_rate_sensitivity.json` 별도 마스터 |
| EBS·T6·MOCE·할인율·article_axes 전부 | — | null(한국 마스터에 개념 없음) |

## 7. 회사별 편차 (10월엔 이 편차가 62사로 늘어난다)

### 7-1. 손보 2사(같은 규제 양식) 사이의 편차

| 축 | au Non-Life | Meiji Yasuda Non-Life | 추출기 대응 |
|---|---|---|---|
| 문서 | ディスクロージャー誌 본편의 業績データ 장 안(인쇄 p69~79) — 5개년 표·재보험·준비금 표와 같은 파일 | 【別冊】業績データ 가 ESR 양식 전용, 본편 별도 | 3축은 별책 회사면 **본편을 하나 더 열어야** 한다 |
| 헤드라인 표 | (1) 결합표(Tier1/2 + 리스크 (a)~(k)) **와** (2) 要約 두 번 | 要約 한 번 | T1 은 要約 에서, (i) 非保険事業 은 결합표에서 |
| 열 | 前年度/当年度/増減 3열 | 前年度/当年度 2열(요약만 増減 있음) | 2번째 토큰 = 당기, 공통 |
| 리스크 코드 | T3 세효과전 (I), 세효과 (J) | (J), (K) | 코드 무시, 라벨로 매칭 |
| EBS 행 | 값 없는 행 생략(価格変動準備金·AOCI·コールローン 등) | 전 행 인쇄 | `ROW_OMITTED` 허용 |
| 민감도 | 값 전부 대시 + "差の絶対値がいずれも1%未満" 주기 | 水準表 + 差額表 2개 | `sensitivity_omitted` 플래그, 生命保険リスク 행 au 없음 |
| 정성 절 | 문장식(내부모형·USP 언급 없음 → `unstated`) + 変動要因分析 절(초년도 該当なし) | 항목식(a~e 전부 該当ありません → False) | tri-state |
| 할인율 표 | 1/2/3년 (단기 상품) | 5/10/15/20년 | 연한 키는 회사별 |
| 규제상 준비금 | 異常危険準備金 2,222 뿐(価格変動準備金 0) | 危険準備金等 14,879 + 価格変動準備金 831 − その他 322 | C34 관측식 |
| 단위 | 百万円 | 百万円 | 둘 다 百万円. **생보 대형사·지주 결산설명자료는 億円** 이 관행이라 10월엔 `unit_disclosed` 열 필수(§5) |
| 세효과 | 세효과전→세효과의 額→세효과후 3행 동일 | 동일 | 헤드라인 (B) = 세효과 **후** 로 통일(둘 다) |

### 7-2. 생보 양식 vs 손보 양식 (article_axes 층)

| 축 | 손보 (au / MY) | 생보 (NN Life) |
|---|---|---|
| `catastrophe_reserve_adequacy` | 본편 `責任準備金の内訳` 표: 종목(火災/海上/傷害/自動車/自賠責/その他) × 열(普通責任準備金/異常危険準備金/危険準備金/払戻積立金/契約者配当準備金等/合計). au 는 火災 없음(상해·기타 보험사)이라 `cat_reserve_fire` null — 금융청 부족 지적 대상(화재)은 대형 손보에서만 의미. 적립 부족 서술은 두 표본 모두 없음 | **해당 없음**(생보엔 이상위험준비금 없음. 대신 危険準備金 + 責任準備金積立率 100% 표) |
| `air_used` | 出再 표 `(10) 出再先保険会社の数·上位5社割合`, `(11) 格付ごとの割合`(A以上/BBB以上/その他 3버킷). AIR 언급 0 | 재보험 표 `(4) 主要な保険会社等の数`, `(5) 上位5社`, `(6) 格付区分`(AA−/A+/A 등 세부 등급, 괄호 = 제3분야 무적립 계약분), `(7) 未収再保険金`. AIR(`アセット・インテンシブ`) 언급 0 이지만 **정황 2건**: 基礎利益 주기 "既契約の出再に伴う損益を除外"(FY2025 △3,733百万円) + 관련당사자 각주 "共同保険式再保険・最低保証再保険"(그룹사 출재) → `air_evidence` 에 기록, `air_used=not_mentioned` 유지 |
| `interest_margin_sign` | **해당 없음**(손보엔 이차손익·逆ざや 개념 없음) | 健全性 box `逆ざや 67→37 億円`(단위 **億円**, 다른 표는 百万円) → negative. `基礎利益` 표(p60)는 キャピタル損益·臨時損益 분해뿐 **三利源(利差·危険差·費差) 분해 없음** → `three_source_disclosed=false`. 대형 생보는 三利源 을 내므로 `interest_margin` 은 그쪽에서 채운다 |
| ESR 헤드라인 | 규제 양식 표 | `後日公表予定` 3곳(§7-3) |

### 7-3. NN Life 의 ESR 빈 자리 골격 (10월에 채워질 위치)

1. p11 主要な経営指標 5개년 표: 행 `ソルベンシー・マージン比率` 가 `新基準`(전 열 `-`, 2025 열에 `(注2)`) / `旧基準`(783.4→863.9%, 2025 `-`) 2단. 주기 (注2) "…2025年度より異なる基準によって算出されます。なお、当該数値に関しては、後日公表予定です。" — **구기준도 FY2025 부터 중단**(au 도 "旧制度による前年度以前の数字の記載を省略").
2. p15 健全性 box: `新基準 -（別途公表予定）`, `旧基準 863.9 / -`, 같은 페이지 `逆ざや` 표.
3. p54 業績・データ編 "7. 保険金等の支払能力の充実の状況（ソルベンシー・マージン比率）": **표 없이 문장 1단락**. 10월엔 여기(또는 별책)에 au (1)~(11) 과 같은 규제 양식 표가 들어올 것으로 본다 — census 는 `esr_placeholder_locations` 의 페이지를 먼저 다시 연다.
4. p42 회사데이터편 5개년 표 재게재(1과 동일 주기).

### 7-4. 10월 62사에서 예상되는 추가 편차(표본에 없어 미검증, notes 에 적을 것)

- 지주 6사·상호회사 5사: 결산설명자료 헤드라인이 **그룹 연결**(`scope=group`)이고 단위 億円·소수 0~1자리. 규제 양식 단체값은 디스클로저지 별책. 둘 다 적되 `scope` 구분.
- 생보: T3 에 `生命保険リスク (A)` 가 채워지고 하위(死亡/長寿/罹患及び障害/解約及び失効/経費 + マネジメント・アクション) 행이 생긴다 — 告示75 別紙様式第三号 확인 후 `rc_life_*` 6개를 ITEMS 에 **등록함(2026-09-12, optional, 損保 표본은 ROW_OMITTED)**. 생보 표본이 오면 G10(第八十一条 행렬) 재현을 처음 검증한다.
- 내부모형 승인사·USP 적용사: 정성 절이 `適用しています` 로 바뀌며 `calc_method=internal_model`. 경과조치 적용사는 문장으로만.
- 억円 표기 회사: 절사 구간 검산의 폭이 100배 커진다(C01 의 ±1 → ±100百万円). `unit_disclosed` 로 분기.

## 8. 합산 규정과 재현 결과 (2026-09-12 추가 — 소요자본을 상관행렬로 다시 계산해 공시값과 대조)

> 티켓 `inbox/jp/20260912T1005Z__owner__JP_MULTI__esr_aggregation_rule.md`. 기계본 `J-ESR/esr_aggregation_rules.json`(행렬은 id 순서 명시), 검산 `extract_esr_template_samples.py::run_aggregation_checks`(G01~G10). K-ICS 레인의 mmult 검산에 해당한다.

### 8-1. 규정 문서 (확보본 `J-ESR/raw/regulation/`, sha256 은 rules JSON `sources[]`)

| key | 문서 | 판·날짜 | 로컬 | 쓴 조문 |
|---|---|---|---|---|
| kokuji74 | 令和七年金融庁告示第七十四号(1柱告示, ソルベンシー・マージン比率告示) — 所要資本 계산 방법 | 2025-07-23 제정, 2026-03-31 적용. fsa.go.jp 게시 통합본(PDF 생성 2026-03-19, **2026-03-23 개정 반영 확인** — 第二十六条第四項 ローリングヘッジ·附則第十三条 포함) | `fsa_pillar1_kokuji_14.pdf`(167p) + `.txt` | 第四十五条·第四十六条·第五十四条·第八十一条·第八十二条·第八十九条·第九十条·第九十二条·第九十三条·第百条·第百一条·第百十二条·第百二十七条·第百二十八条·第百五十四条~第百五十七条·別表七 |
| kokuji75 | 令和七年金融庁告示第七十五号(3柱告示) — 공시 양식 別紙様式第三号 所要資本の額の構成 + 記載上の注意 | 2025-07-23 | `fsa_pillar3_kokuji_13.pdf`(67p) + `.txt` (curl 은 35KB 에서 끊겨 WebFetch 바이너리 저장본 324KB 사용) | 様式第三号 행 정의, 注 1(3)·2(7)·3(2)·4(2)~(5)·5(3)·6(3)~(7) |
| kokuji_r8_6 | 令和八年金融庁告示第六号 — 74호 일부개정 | 2026-03-23 | `fsa_20260323_03_pillar1_amend.pdf`(8p) | 개정 조문 第二十六·二十七·六十四·百二十八·百四十·百七十条·附則十三 → **합산 조문 변경 없음** |

미확보(curl 000, 시간대 차단): 3柱告示 개정(20260323/04.pdf)·概要(10.pdf)·Q&A(11.pdf)·2024 필드테스트 仕様書(08_1.pdf). 합산 규정에는 불필요. Q&A 는 第九十二条 "適切な方法"(지역 간 巨大自然災害 통합) 해석에 쓸 수 있어 443 열리면 재시도.

### 8-2. 규정 (표준적 수법)

**최상위 (第百五十五条).** 5개 리스크를 아래 행렬로 √(xᵀRx) 통합한 뒤 **オペレーショナル・リスク를 선형 가산**한다. 순서 = `rc_life, rc_nonlife, rc_catastrophe, rc_market, rc_credit`.

| | 生保 | 損保 | 巨大災害 | 市場 | 信用 |
|---|---|---|---|---|---|
| 生保 | 1.00 | 0.00 | 0.25 | 0.25 | 0.25 |
| 損保 | 0.00 | 1.00 | 0.25 | 0.25 | 0.25 |
| 巨大災害 | 0.25 | 0.25 | 1.00 | 0.25 | 0.25 |
| 市場 | 0.25 | 0.25 | 0.25 | 1.00 | 0.25 |
| 信用 | 0.25 | 0.25 | 0.25 | 0.25 | 1.00 |

- **분산효과 (H)** — 告示75 注 6(5): (A)~(F) 단순합 − 第八節 통합액(= √ + F). 즉 `H = (A+B+C+D+E) − √(xᵀRx)`.
- **세효과전 (J)** = √ + F(オペ) + G(MA 上限超過, 第四十六条第三項) + I(非保険事業, 単体은 0).
- **オペ (F)** — 第百五十四条: min(상한적용전 오퍼리스크, **0.20 × (√ + G)**). 상한적용전 = 손보 max(2.75%×수입보험료, 2.75%×현재추계)+성장가산 / 생보(유리스크) max(4%×보험료, 0.45%×현재추계)+성장가산 / 특별계정 0.40%×현재추계 — 입력이 양식에 없어 **상한만 검산**.
- **세효과 (K)** — 第百五十六条第一号(単体): min(**0.80 × 法定実効税率 × (√+F+G)**, [0.5×税率×직근5기 세전이익]⁺ + [DTL−DTA]⁺ − min([DTA−DTL]⁺, 0.15×(√+F+G))). 세율은 회사별 法定実効税率(고시에 숫자 없음). 연결(第二号)은 3년 가중 실효세율 + 해외 결손금 환급 항 추가.
- **생보 하위 (第八十一条)** 순서 死亡·長寿·罹患及び障害·解約及び失効·経費: 死亡–長寿 **−0.25**, 死亡–罹患 0.25, 死亡–経費 0.25, 長寿–解約 0.25, 長寿–経費 0.25, 罹患–経費 0.50, 解約–経費 0.50, 그 외 0.00. MA 행은 정보행(注 6(3), 하위액에 이미 반영) — √ 뒤에 빼지 않는다.
- **손보 하위 (第八十九条 + 別表七)** 4단계: ① (地域×商品区分)별 保険料リスク–支払備金リスク ρ0.25 → ② 商品大区分 안의 商品区分 끼리 別表七 ρ(財物 0.50 / 賠償 0.50 / 自動車 0.75 / その他 0.25; 不動産ローン保証·信用保険 제외 — 각각 不動産リスク 第百十九条·信用リスク 第百二十八条第三号 로 감) → ③ 地理的区分 안의 大区分 4개 ρ**0.50** → ④ 지역(日本/EEA/米加/中国·その他) ρ0.25. **공시 하위 4행은 注 3(2)에 따라 大区分별로 지역을 먼저 ρ0.25 로 묶은 값**이라 ③④ 순서가 규정과 반대 → 단일 √(ρ0.50) 재계산은 **일본 단일지역 회사에서만 정확**.
- **巨大災害 (第百条)** 巨大自然災害·テロ·感染症·信用保証 4액 ρ**0.00**. 공시 `その他の巨大災害` = 뒤 3액의 ρ0.00 통합(注 4(4)) → `C = √(nat² + other²)` 이어야 함. 巨大自然災害: 일본 3 peril(地震·風水災·雪災) ρ0.00(第九十三条), 해외는 正味既経過保険料×係数(EEA 40/米加 50/其他 30%, 第九十二条第二号), **지역 간은 "適切な方法"(ρ 미지정)**.
- **시장 하위 (第百二十七条)** 순서 金利·スプレッド·株式·不動産·為替·資産集中. 스프레드 上昇 ≥ 下降이면 case_up, 아니면 case_down(注 5(3): 행 라벨이 `スプレッドリスク（上昇）/（下降）の額` 로 바뀌므로 라벨로 선택). 資産集中은 전부 0.00(사실상 √ 밖 제곱합).

| case_up | 金利 | スプ | 株式 | 不動産 | 為替 | 集中 |
|---|---|---|---|---|---|---|
| 金利 | 1.00 | 0.25 | 0.25 | 0.25 | 0.25 | 0.00 |
| スプレッド | 0.25 | 1.00 | 0.75 | 0.50 | 0.25 | 0.00 |
| 株式 | 0.25 | 0.75 | 1.00 | 0.50 | 0.25 | 0.00 |
| 不動産 | 0.25 | 0.50 | 0.50 | 1.00 | 0.25 | 0.00 |
| 為替 | 0.25 | 0.25 | 0.25 | 0.25 | 1.00 | 0.00 |
| 資産集中 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 |

case_down 은 スプレッド–株式 0.00, スプレッド–不動産 0.00 (나머지 동일).

- **信用 (第百二十八条)** 단순합(EAD×係数 + 特別勘定分 + 信用保険分) — 행렬·하위행 없음.

### 8-3. 재현 결과 (百万円, 공시 / 재계산 / 차)

| 검산 | 식 | au Non-Life | Meiji Yasuda Non-Life | 판정 |
|---|---|---|---|---|
| G01 분산효과 | H = ΣA..E − √ | 274 / 273.6 / +0.4 | 2,530 / 2,529.5 / +0.5 | **재현** (절사 이내) |
| G02 세효과전 | J = √+F+G+I | 1,510 / 1,508.4 / +1.6 | 6,985 / 6,982.5 / +2.5 | 재현 (7항 절사 허용 ±7) |
| G03 オペ 상한 | F ≤ 0.2×(√+G) | 251 / 상한 251.5 → **상한에 걸림** | 463 / 상한 1,303.9 → 여유 | 통과. au 는 오퍼리스크가 20% 캡으로 결정됨 |
| G04 세효과 | K = 0.8×t×(√+F+G) | 338 / 337.9 (t=28.0%) | 1,564 / 1,564.1 | **재현**, 두 회사 모두 1호 전단(80%) 분기, 역산 税率 27.98% / 27.99% → 法定実効税率 28.0% |
| G05 시장 | D = √(xᵀR_mkt x) | 247 / 247.0 (集中만) | 4,613 / 4,611.8 / −1.2 | **재현** (case_up, スプレッド 0 이라 case 무관) |
| G06 손보 | B = √(x ρ0.50 x) | 1,119 / 1,119.0 / 0 | 2,096 / 2,137.3 / **+41 (+2.0%)** | au 정확(단일지역). MY 는 `外国における巨大自然災害 156 > 0` = 다지역 → 구조적 불일치(informational, 등재) |
| G07 巨大災害 | C = √(nat²+other²) | 87 / 87.0 (other 만) | 1,865 / 1,974.4 / **+109 (+5.9%)** | MY **미재현** — known_deviations 등재(아래) |
| G08 巨大自然災害 | nat = √(Σ日本 peril²) + 해외 | (전부 대시) | 1,748 / 1,591.2+156 = 1,747.2 / −0.8 | MY 는 지역 간 **단순합**(hypot 이면 1,598.8 로 불일치) — informational |
| G09 세효과후 | J_calc − K_calc | 1,171 / 1,170.5 / −0.5 | 5,420 / 5,418.4 / −1.6 | 재현 |
| G09b ESR | E / post_calc | 791.7 / 792.6 (허용 ±5.4pp = 분모 ±8) | 743.2 / 743.6 (±1.1pp) | 재현 — 비율은 분모 절사 1당 au 0.68pp 흔들림 |
| G10 생보 | A = √(xᵀR_life x) | — | — | 표본 없음(손보 2사 하위 생략, NN Life not_yet) |

**결론.** 표준식 손보 2사에서 **최상위 통합(분산효과)·세효과·시장 하위·헤드라인 체인은 규정 행렬로 재현된다.** 안 되는 두 곳은 모두 Meiji Yasuda Non-Life 의 손보·巨大災害 하위다:
1. 손보 B (+41): 규정은 지역 안에서 大区分을 먼저 묶고(ρ0.50) 지역을 나중에 묶는데(ρ0.25), 공시 하위행은 지역을 먼저 묶은 값이라 두 단계가 교환되지 않는다. 단일지역 au 는 정확히 맞으므로 행렬 자체는 맞다. → 규칙: `rc_cat_nat_foreign > 0`(또는 해외 사업 有)이면 G06 은 informational.
2. 巨大災害 C (+109): 注 4(4) 대로면 정확히 맞아야 하는데 안 맞는다. 가설 (a) 공시 `その他の巨大災害 918` 이 テロ/感染症/信用保証의 **단순합**이고 ρ0.00 통합액은 ≈650(예: 500+418 → 651.6) — C=1,865 와 정합; (b) 1,748 안의 지역 통합 방식이 단순합이 아님; (c) 感染症 MA(第四十六条) 미공시 — MA 행이 대시라 낮음. **10월 손보 다수에서 G07 이 같은 방향으로 깨지면 (a)가 업계 관행**이라는 뜻이므로 그때 규칙을 바꾼다. 등재: rules JSON `known_deviations`.

### 8-4. 내부모형·USP 회사의 판정 규칙 (census `calc_method` 열과 연결)

- `standard` / `standard_implied`: G01·G02·G04·G05·G09 는 **게이트**(안 맞으면 파싱 오류 우선 의심). G06 은 단일지역만 게이트, G07 은 등재 예외 외 게이트, G08 은 항상 informational.
- `internal_model`(T8 に 内部モデル手法 適用): 第六章 승인 모형이 巨大自然災害(注 4(2)) 등 하위액을 대체하므로 **G06/G07/G08(모형 범위에 따라 G05/G10 도) 재현 안 되는 것이 정상**. 단 第百五十五条 최상위 행렬은 내부모형사에도 적용되므로 G01·G02·G04 는 그대로 게이트.
- USP(会社固有のストレス係数/リスク係数): 하위 입력값만 바뀌고 행렬은 그대로 → 전 검산 적용.
- 판정 흐름: G06/G07 실패 + T8 `内部モデル 適用` → expected(`calc_method=internal_model` 기록) / + `該当ありません` → known_deviations 후보로 티켓.
- 세율: `implied_statutory_tax_rate = K/(J−I)/0.8` 가 0.27~0.31 밖이면 2호 분기(DTA 과다·적자사) — 데이터 오류 아님, notes 에 적는다.

## 9. 손익 층 `layer:"profit"` (2026-09-12 추가 — 티켓 `inbox/jp/20260912T1150Z__owner__JP_MULTI__profit_layer_schema.md`)

> 한국 PL 패널(손익분해)의 일본판 입력층. 일본 법정 결산은 **J-GAAP 원가법**(책임준비금 標準責任準備金 lock-in, IFRS17 미적용)이라 CSM·RA·예실차가 없고,
> 대신 생보는 `基礎利益`(기초이익)+`三利源`, 손보는 `保険引受利益`+`資産運用損益`+비율 3종이 공시서류 표로 있다. 기사 3축 ③(이차손익 전환, 도메인 문서 §4b-3)은
> 이 층의 `pl_interest_margin` 으로 흡수한다(`article_axes.interest_margin_sign` 은 유지, 三利源 공시사는 `pl_interest_margin` 부호가 정본).
> 기계 스키마 = `J-ESR/esr_disclosure_schema.json` `layer:"profit"` 36항목(값 32 + 메타 4). 값은 `{"prev": 前年度, "cur": 当年度}` 쌍, 百万円(비율 %).
> 추출·검산 = `extract_esr_template_samples.py::extract_profit / run_profit_checks / run_profit_axes_xref`.

### 9-1. 항목 (id → 위치·검산·한국 PL 대응)

`pl` 열 = 루트 `PL_breakdown.json` 항목번호(1~32). **억지 대응 금지** — 정확(당기순이익 24·세전 22·법인세 23)과 근사(経常利益→20 영업이익, 保険引受利益→1 보험손익, 資産運用損益→17 투자손익)만 적고 나머지는 null.
근사 사유: 일본 特別損益 ≈ 한국 영업외손익(20↔経常利益), 保険引受利益 은 J-GAAP 원가법(責任準備金繰入 포함)이라 IFRS17 보험서비스결과와 범위가 다름, 資産運用損益 은 보험금융손익(19)을 포함하지 않음.

| id | scope | 표 | label (ja) | 뜻 | pl | au Non-Life (prev) | NN Life (prev) | page |
|---|---|---|---|---|---|---|---|---|
| `pl_ordinary_revenue` | both | 損益計算書 | 経常収益 | 경상수익 |  | 8,320 (8,129) | 596,118 (576,434) | 17/44 |
| `pl_ordinary_expenses` | both | 損益計算書 | 経常費用 | 경상비용 |  | 6,665 (6,678) | 574,744 (562,097) | 17/44 |
| `pl_ordinary_profit` | both | 損益計算書 | 経常利益 | 경상이익 | 20(근사) | 1,654 (1,451) | 21,373 (14,336) | 17/44 |
| `pl_extraordinary_gains` / `pl_extraordinary_losses` | both | 損益計算書 | 特別利益 / 特別損失 | 특별이익/손실 |  | －/1 (－/82) | 0/446 (13/529) | 17/44 |
| `pl_pretax_profit` | both | 損益計算書 | 税引前当期純利益(純剰余) | 세전이익 | 22 | 1,652 (1,368) | 20,928 (13,819) | 17/44 |
| `pl_income_taxes` | both | 損益計算書 | 法人税等合計 | 법인세 | 23 | 481 (407) | 5,837 (3,414) | 17/44 |
| `pl_net_income` | both | 損益計算書 | 当期純利益 / 当期純剰余(상호회사) | 당기순이익 | 24 | 1,171 (961) | 15,090 (10,405) | 17/44 |
| `pl_interest_dividend_income` | both | 損益計算書 | 利息及び配当金(等)収入 | 이자·배당수입 |  | 48 (7) | 20,895 (22,133) | 17/44 |
| `pl_net_premiums_written` | nonlife | 損益計算書 | 正味収入保険料 | 정미수입보험료 |  | 8,137 (7,976) | n/a | 17 |
| `pl_net_claims_paid` / `pl_loss_adjustment_expenses` | nonlife | 損益計算書 | 正味支払保険金 / 損害調査費 | 손해율 분자 |  | 1,940/649 | n/a | 17 |
| `pl_commissions_collection` / `pl_operating_general_admin` | nonlife | 損益計算書 | 諸手数料及び集金費 / 営業費及び一般管理費 | 사업비율 분자·전체 판관비 |  | 79/3,121 | n/a | 17 |
| `pl_other_ordinary_revenue` / `pl_other_ordinary_expenses` | nonlife | 損益計算書 | その他経常収益 / 費用 | P07 브리지 항 |  | 65/0 | n/a | 17 |
| `pl_underwriting_revenue` / `pl_underwriting_expenses` / `pl_uw_operating_general_admin` / `pl_underwriting_other` | nonlife | 保険引受利益明細表 | 保険引受収益 / 費用 / 保険引受に係る営業費及び一般管理費 / その他収支 | 인수이익 내역 |  | 8,206/3,543/3,113/－ | n/a | 5 |
| `pl_underwriting_profit` | nonlife | 保険引受利益明細表 | 保険引受利益 | 보험인수이익 | 1(근사) | 1,550 (1,363) | n/a | 5 |
| `pl_investment_pl` | nonlife | 資産運用利回り(実現利回り) 합계행 | 資産運用損益(実現ベース) | 자산운용손익 | 17(근사) | 48 (7) | n/a | 11 |
| `pl_loss_ratio_pct` / `pl_expense_ratio_pct` / `pl_combined_ratio_pct` | nonlife | 正味損害率、正味事業費率及びその合算率 合計행 | 正味損害率 / 正味事業費率 / 合算率 | 손해율/사업비율/합산율 |  | 31.8/39.2/71.1 (29.4/42.7/72.1) | n/a | 5 |
| `pl_premium_income` | life | 損益計算書 | 保険料等収入 | 보험료등수입 |  | n/a | 371,006 (395,528) | 44 |
| `pl_core_profit` | life | 経常利益等の明細(基礎利益) | 基礎利益 (A) | 기초이익 |  | n/a | 18,523 (14,828) | 60 |
| `pl_capital_gains` / `pl_extraordinary_pl` | life | 같은 표 | キャピタル損益 (B) / 臨時損益 (C) | 캐피털/임시손익 |  | n/a | △1,232/4,082 (△1,007/515) | 60 |
| `pl_interest_margin` / `pl_mortality_margin` / `pl_expense_margin` | life | 三利源 표 | 利差損益 / 危険差損益 / 費差損益 | 三利源 |  | n/a | TABLE_ABSENT | — |
| `accounting_basis` | meta | 会計方針 절·감사 문구·P&L 양식 | — | jgaap / ifrs / unstated |  | jgaap (B) | jgaap (A) | 15·17·31 / 47~49 |
| `ifrs17_applied` | meta | 〃 | IFRS第17号 | true / false / unstated |  | false | false | |
| `accounting_basis_evidence` / `profit_source_doc` | meta | | | 근거 문장 / 출처 문서 |  | | | |

Meiji Yasuda Non-Life: **2026-09-12 2회차에 본편을 owner 가 직접 확보**(`J-ESR/raw/fy2025_samples/meijiyasuda_nonlife_20260729_main.pdf`, 60p)해 25/25
applicable 전항목 추출·`accounting_basis=jgaap`/`ifrs17_applied=false` 로 채워졌다 — 상세·검산·라벨/레이아웃 특이점은 §9-6.

### 9-2. 위치 (회사 유형별)

| 유형 | 손익계산서 | 손보 인수이익·비율 | 손보 운용손익 | 생보 기초이익 | 회계방침 |
|---|---|---|---|---|---|
| au Non-Life (본편 業績データ 장) | p17 `(2)損益計算書` 3열(前年度/当年度/比較増減) + 관계주기(正味収入保険料 내역 등) | p5 `(6)正味損害率、正味事業費率及びその合算率`(종목×3개년, 合計행)·`(8)保険引受利益明細表`(3개년) | p11 `(3)資産運用利回り(実現利回り)` 合計행(損益·平均運用額·利回り × 3개년 = 9토큰, 当期 = 7번째) | — | 貸借対照表関係注記(p15) 는 감가상각·인당 방침만, `企業会計基準` 문구 없음 → **B 티어**: P&L 법정양식(責任準備金繰入額·支払備金繰入額) + p31 会社法第436条/保険業法第111条 감사 문구 |
| NN Life (ディスクロージャー誌 본편) | p44 `2.損益計算書` 4열(前年度 金額/百分比/当年度 金額/百分比 — 소계행만 4토큰, 내역행 2토큰) | — | — | p60 `9.経常利益等の明細(基礎利益)`: 基礎利益 A / キャピタル収益·費用 → B / 臨時収益·費用 → C / 経常利益 A+B+C, 라벨 뒤 기호 A·B·C 가 별도 줄 | p47~49 `1.会計方針に関する事項`(有価証券 評価·標準責任準備金 大蔵省告示第48号·ヘッジ会計 企業会計基準第10号) → **A 티어** |
| Meiji Yasuda Non-Life (별책) | 없음 → 본편 필요 | 없음 | 없음 | — | 없음 → unstated |
| 5개년 主要な経営指標 (au p2, NN p11) | 열 = 오래된→최신 5개년, 마지막 = 当年度·직전 = 前年度. au 는 행 라벨이 **세로쓰기(한 글자 한 줄)** 로 추출돼 `merge_vertical` 로 합친 뒤 매칭 | | | | P10 교차검산 소스 |

### 9-3. 검산 P01~P13 (cur·prev 각각, `run_profit_checks`)

| id | 식 | 오차 | au (cur/prev) | NN (cur/prev) | 비고 |
|---|---|---|---|---|---|
| P01 | 生保 `経常利益 = 基礎利益 + キャピタル損益 + 臨時損益` | ±2 | — | 18,523−1,232+4,082 = 21,373 ✓ / 14,336 ✓ | 基礎利益 정의(2022년도 개정식)의 항등식 |
| P02 | 生保 `基礎利益 ≈ 利差 + 危険差 + 費差` | ±5, informational | — | TABLE_ABSENT | NN 은 三利源 미공시. 대형 생보는 회사별 정의(その他 포함 여부) 차이 있어 informational |
| P03 | `経常利益 = 経常収益 − 経常費用` | ±1 | 8,320−6,665=1,655 vs 1,654 / 1,451 ✓ | 21,374 vs 21,373 / 14,337 vs 14,336 | 百万円 절사 |
| P04 | `税引前 = 経常利益 + 特別利益 − 特別損失` | ±1 | 1,653 vs 1,652 / 1,369 vs 1,368 | 20,927 vs 20,928 / 13,820 vs 13,819 | |
| P05 | `当期純利益 = 税引前 − 法人税等合計` | ±1 | 1,171 ✓ / 961 ✓ | 15,091 vs 15,090 / 10,405 ✓ | |
| P06 | 損保 `合算率 = 損害率 + 事業費率` | ±0.15 | 71.0 vs 71.1 / 72.1 ✓ | — | 각 비율이 소수1자리 반올림이라 ±0.1 초과 가능 |
| P07 | 損保 `経常利益 = 保険引受利益 + 資産運用損益 + (その他経常収益 − その他経常費用 − (営業費及び一般管理費 − 保険引受に係る営業費及び一般管理費))` | ±3 | 1,550+48+(65−0−8)=1,655 vs 1,654 / 1,451 ✓ | — | 티켓의 "± その他" 를 P&L 행으로 명시한 식. 판관비 중 보험인수 귀속분 외(8)는 경상비용에만 있음 |
| P08 | 損保 `損害率 = (正味支払保険金 + 損害調査費) / 正味収入保険料` | ±0.1 | 31.82→31.8 / 29.34→29.4 | — | 회사 주기 정의 그대로 |
| P09 | 損保 `事業費率 = (諸手数料及び集金費 + 保険引受に係る営業費及び一般管理費) / 正味収入保険料` | ±0.1 | 39.23→39.2 / 42.72→42.7 | — | |
| P10 | 5개년 主要な経営指標 표 == P&L/明細表 (8행 × cur·prev) | 0 | 16/16 | (NN 5개년 표는 億円 — 미비교) | |
| P11 | 損保 `保険引受利益 = 保険引受収益 − 保険引受費用 − 保険引受に係る営業費及び一般管理費 + その他収支` | ±1 | 1,550 ✓ / 1,364 vs 1,363 | — | |
| P12 | `profit.pl_core_profit == article_axes.core_profit` (cur·prev) | 0 | — | 18,523 / 14,828 ✓ | 두 층이 같은 표를 읽는지 교차 |
| P13 | `利息及び配当金収入 ≈ 資産運用損益` | ±1, informational | 48 ✓ / 7 ✓ | — | au 는 운용비용·매각손익 0 이라 등식. 유가증권 보유사는 당연히 깨진다 |

결과: **au 19/19, NN Life 12/12 (게이트 0 실패), Meiji Yasuda Non-Life P00 NOT_ACQUIRED 1건(informational).**

### 9-4. 생보/손보 차이와 10월 62사 주의점

- 손익계산서 골격(経常収益→経常利益→特別損益→税引前→法人税等→当期純利益)은 생·손보 공통. 상호회사는 `当期純剰余`·`税引前当期純剰余`(라벨 변형 등록됨).
- **생보**: `基礎利益` 표(経常利益等の明細)는 전사 공통이지만 **三利源 표는 대형사·일부 상장사만**(NN 없음). 三利源 라벨 변형 `利差損益/利差益/利差損`(부호는 益/損 으로 표기, 損 이면 음수로 저장할 것 — 표본 없어 미검증). 逆ざや 는 §7-2 대로 `article_axes` 에 남긴다.
- **손보**: 비율 3종은 `合計` 행이 여러 표에 반복(正味 표·出再控除前 표)되므로 `(6)正味損害率` 제목 뒤 첫 `合計` 만 잡는다. 資産運用損益 도 `(2)インカム利回り`·`(3)実現利回り`·`(参考)時価総合利回り` 세 표에 `合計` 가 있어 `(3)` 뒤 첫 `合計`. 대형 손보(지주 자회사)는 본편 業績データ에 같은 순번 표가 있으나 **단위 億円·소수 1자리** 가 흔하다(§7-4) — `unit_disclosed` 필수.
- 열 레이아웃은 회사별 `pl_layout` 로 선언한다(`prev_cur_diff` au / `prev_pct_cur_pct` NN). 10월엔 `prev_cur`(2열)·`cur_only` 가 더 나올 수 있다 — 첫 매칭 행의 토큰 수로 판별하되 자동 추정하지 말고 회사별로 적는다.
- **회계기준 판정 규칙**(`accounting_basis`): (A) 会計方針 절이 `標準責任準備金`/`大蔵省告示第48号`/`企業会計基準` 을 인용 → jgaap. (B) 회계방침 절이 없어도 법정 損益計算書 양식(`責任準備金繰入額`·`支払備金繰入額`) + `会社法第436条`/`保険業法第111条` 감사 문구가 같이 있고 IFRS 언급 0 → jgaap. `連結財務諸表の作成基準` 에 `国際財務報告基準`/`IFRS` → ifrs(지주 연결 결산설명자료에서 나올 수 있음, 표본 0). 둘 다 아니면 unstated.
  `ifrs17_applied`: `IFRS第17号` 명시 → true; accounting_basis=jgaap 인 **単体 법정재무제표** → false(保険業法·会社計算規則상 単体은 J-GAAP 강제, IFRS 는 上場社 連結 임의적용뿐 — 문서 밖 추정이 아니라 법령 사실); 그 외 unstated. 3사 판정: au jgaap/false(B), NN jgaap/false(A), MY unstated/unstated(별책만).
- 그룹 지주 6사의 결산설명자료는 **연결 J-GAAP**(修正利益·グループ調整利益 등 자체 지표)이라 이 층의 単体 항목과 섞지 않는다 — `scope=group` 행은 `pl_net_income`(親会社株主に帰属する当期純利益)만 채우고 나머지는 null 로 두는 편이 안전하다(10월 결정).

### 9-5. publishing 용 블록 제안 (`jp/jesr_detail.json` companies[].profit)

```json
"profit": {
  "fiscal_year": "FY2025", "period": "2025-04-01..2026-03-31", "unit": "JPY_million",
  "accounting_basis": "jgaap", "ifrs17_applied": false,
  "accounting_basis_evidence": "A(会計方針 p47): 標準責任準備金 … 大蔵省告示第48号",
  "source": {"doc": "au_nonlife_disclo_260730_4of5.pdf", "pages": {"pl": [17], "uw": [5], "ratio": [5], "inv": [11]}},
  "items": {
    "pl_ordinary_profit":      {"cur": 1654, "prev": 1451, "pl_item_ref": 20},
    "pl_net_income":           {"cur": 1171, "prev": 961,  "pl_item_ref": 24},
    "pl_underwriting_profit":  {"cur": 1550, "prev": 1363, "pl_item_ref": 1},
    "pl_investment_pl":        {"cur": 48,   "prev": 7,    "pl_item_ref": 17},
    "pl_loss_ratio_pct":       {"cur": 31.8, "prev": 29.4},
    "pl_expense_ratio_pct":    {"cur": 39.2, "prev": 42.7},
    "pl_combined_ratio_pct":   {"cur": 71.1, "prev": 72.1}
  },
  "checks": {"pass": 19, "total": 19, "failed": []},
  "not_acquired": null
}
```

- `items` 는 `extracted_sample_values.json` `companies[].profit.values` 에서 null 이 아닌 것만, 값·단위 무변환(百万円 그대로; 화면 億円 변환은 designer). `_meta.labels` 에는 이미 36개 profit id 의 ja/ko/unit 이 들어간다(schema `items` 전체를 복사하므로).
- 생보는 `pl_core_profit`·`pl_capital_gains`·`pl_extraordinary_pl`(+ 三利源 있으면 3개) 가 핵심, 손보는 위 7개. `pl_item_ref` 는 스키마에서 조인(null 이면 키 생략).
- 미확보 회사(MY)는 `"items": {}`, `"not_acquired": "<profit_source_doc 문자열>"`, `"main_volume_url"` 을 넣어 화면이 "본편 미확보" 를 구분 표시할 수 있게 한다.
- 검산 게이트: `failed` 가 비어야 블록을 붙인다(informational P02/P13/P00 은 제외). 전기값은 회사가 같은 표에 찍은 값이라 별도 검증 없이 그대로.

### 9-6. Meiji Yasuda Non-Life 본편 확보 (2026-09-12 2회차, 티켓 `inbox/_resolved/20260912T1150Z__owner__JP_MULTI__profit_layer_schema.md` 말미에 append)

owner 가 본편 `明治安田損害保険の現状2026`(60p)를 직접 받아 `J-ESR/raw/fy2025_samples/meijiyasuda_nonlife_20260729_main.pdf` 에 넣었다.
**결과: 25/25 applicable 전항목 추출, 검산 17/19(2건은 P13 informational — au 도 동일 성격), `accounting_basis=jgaap`/`ifrs17_applied=false`.**

**페이지 매핑.** 이 PDF 는 두 인쇄쪽을 한 PDF 페이지에 담는다 — 인쇄쪽번호 P(TOC 기준) ↔ pdf 페이지 index N: `N = (P+3)/2`(P 홀수, 좌쪽) 또는
`N = (P+2)/2`(P 짝수, 우쪽). 검증: TOC "2.損益計算書 81" → N=(81+3)/2=42 (실제 그 자리에 있음). 이번 라운드 실사용 페이지: `pl`(損益計算書)=42,
`uw`(保険引受利益明細表)=36, `ratio`(正味損害率·正味事業費率·合算率)=35, `summary5`(主要な業務の状況を示す指標 5개년표)=9, `basis`(회계기준 근거: 損益計算書 법정양식 +
10.会計監査 감사문구)=42,45.

**라벨 렌더링 특이점 (이 회사만, au/NN 무변경 확인).** 이 PDF 는 표 라벨을 글자 하나씩 세로줄로 찍는다(`経`→`常`→`収`→`益` 각각 한 줄). 게다가
損益計算書(p42)는 **한 구획(경상수익 12항목/경상비용 15항목/특별손익/세전~당기순이익)의 라벨을 전부 나열한 뒤 그 구획 전체의 3개년 값을 한꺼번에** 찍는다
(항목별로 라벨+값이 번갈아 나오는 明細表·比率표 방식과 다르다) — 그래서 라벨 정규식으로 앵커를 잡는 기존 `grab()` 방식이 아예 안 먹는다.
처리: 라벨을 무시하고 **"損益計算書" 제목 ~ "損益計算書の注記" 사이의 숫자 토큰만 순서대로 뽑아(`pl_flat_tokens`, 120개 확인) 검증된 고정 위치**로
읽는다(`MEIJI_PL_FLAT_MAP`, `extract_esr_template_samples.py`). 明細表(uw)·比率표(ratio)는 항목별 번갈아 방식이라 `merge_vertical()`(기존에
summary5 전용이던 함수)을 uw/ratio 에도 적용해 라벨을 한 줄로 합치는 것만으로 기존 코드가 그대로 동작한다(`vertical_labels=True`). 比率표 헤딩도
"(6)正味損害率"(au) 대신 "6. 正味損害率"(Meiji) 라서 헤딩 매칭을 "正味損害率"+"正味事業費率" 동시 포함으로 느슨화했다(au 도 안 깨짐, 확인함).
明細表의 보험인수 관련 영업비 행은 라벨이 그냥 "営業費及び一般管理費"(注記로만 보험인수 귀속분임을 밝힘) — 스키마의 정본 라벨
"保険引受に係る営業費及び一般管理費" 는 안 바꾸고 **회사별 `label_overrides` 로만 대체**(스키마 항목 정의 무변경 원칙 유지).
회계기준 근거문(会計方針/責任準備金繰入額/会社法第436条 등) 판정도 이 세로줄 렌더링 때문에 "\n"→" " 치환 후 공백이 글자 사이마다 끼어 substring
매칭이 깨졌다 — 공백을 전부 제거한 사본(`basis_ns`/`doc_ns`)으로 판정하도록 고쳤다(CJK 는 원래 공백이 없으므로 매치를 늘리기만 하고 au/NN 의
기존 매치는 그대로 유지, 회귀 없음 확인).

**`pl_investment_pl` 이중계상 발견.** 資産運用利回り(実現利回り) 합계행(자산운용손익·실현기준, 스키마 정본 소스)의 분자는
`資産運用収益+積立保険料等運用益-資産運用費用` 인데, `積立保険料等運用益` 은 이미 `保険引受収益`(→保険引受利益) 안에 들어 있다. au 는 이 값이 0 이라
안 드러났지만 Meiji 는 17(백만엔)이라 그대로 쓰면 P07(경상이익 검산)이 ±15 로 어긋난다. **손익계산서의 `資産運用収益-資産運用費用`(=773, prev 592)
로 대체**(`pl_investment_override="pl_stmt"`) 하면 P07 이 ±1 로 닫힌다. 10월 62사에서 積立保険料等運用益 이 0 이 아닌 손보사는 같은 대체가 필요할 수
있다 — `pl_investment_override` 를 회사별로 켤 것.

**추출값 (百万円, cur=2025년도, prev=2024년도).** 経常収益 16,757(15,956) · 経常費用 15,163(14,739) · 経常利益 1,594(1,216) · 特別利益 0(26,
2024년만 26 발생) · 特別損失 19(0) · 税引前 1,574(1,242) · 法人税等合計 571(465) · 当期純利益 1,003(777) · 利息及び配当金収入 657(546) ·
正味収入保険料 15,692(15,327) · 正味支払保険金 5,108(5,098) · 損害調査費 814(778) · 諸手数料及び集金費 3,492(3,336) ·
営業費及び一般管理費(전체) 4,709(4,648) · 保険引受収益 15,856(15,350) · 保険引受費用 10,267(10,063) · 保険引受に係る営業費及び一般管理費
4,624(4,555) · その他収支 -1(-2) · 保険引受利益 963(729) · 資産運用損益(P&L 기준) 773(592) · 損害率/事業費率/合算率 37.7/51.7/89.5
(38.3/51.5/89.8).

**검산.** P03·P04·P05·P06·P08·P09·P11 cur+prev 전부 통과(±1~±0.15 허용오차 내), P10(5개년표 대조) 6/6, **P07 은 위 이중계상 대체 후 통과**.
P13(이자배당수입≈투자손익, informational)만 au 와 같은 사유(운용비용·유가증권매각손익이 0 이 아니라서)로 실패 — 게이트 무관.

**회계기준.** au 와 같은 **B 티어**: 회계방침 절은 없지만 법정 損益計算書 양식(責任準備金繰入額·支払備金繰入額, p42) + p45 10.会計監査
"保険業法第111条第1項…「会社法第436条第2項第1号」…有限責任あずさ監査法人の会計監査を受けており、適正である旨の証明を受けています" 로 jgaap 판정,
IFRS/国際財務報告基準 문자열 0건 확인 → `ifrs17_applied=false`.

**파일 소실 사고 (owner 확인 필요).** 이 라운드 도중 owner 가 넣어 준 `meijiyasuda_nonlife_20260729_main.pdf` 가 세션 중간에 로컬 디스크에서
사라졌다(전체 홈 디렉터리 검색 + git 이력 대조로 확인 — 애초에 git 추적 대상도 아니었음, 원인 불명). 파일이 사라지기 **전에** 읽은 원문 텍스트를
`J-ESR/raw/fy2025_samples/meijiyasuda_nonlife_main_pages_fixture.json`(p9·35·36·42·45 의 `get_text('text')` 스냅샷)로 남겨 뒀고,
`extract_esr_template_samples.py::main()` 은 **① 실물 PDF 우선 → ② 없으면 이 fixture 로 재현 → ③ 그것도 없으면 NOT_ACQUIRED** 순으로
동작한다(`profit_pdf_fixture`, `FixtureDoc`). 위 25/25·17/19 는 이 fixture 재현 경로로 나온 결과다 — **실물 PDF 가 돌아오면 다음 실행이
자동으로 그쪽을 쓰고, 같은 숫자가 나오는지 대조해 볼 것**(라벨/좌표가 100% 같은 파일이면 바이트 단위로 같아야 한다).
