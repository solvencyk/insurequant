# Insurequant Parser TODO — IFRS17 lane (Stage 2)

> **Status (top, 2026-09-12 90th pass 직후): AIA-456 종결(KR0080 2025.4Q item4/5/6 을
> 산문에서 주석18(4) 측정요소 표 기준으로 전환 + item9-12 재보험 신규 등재) + KR1010
> 2023.4Q item2 불일치(4,698백만) 원인 규명·정정(연결 손익계산서 "7.기타영업비용" 누락
> 발견, item16 보정으로 잔차 0 확정).** 게이트 RED=0(PL 축, K-ICS공시 xlsx RED 1건은
> kics 레인 동시작업 소관·무관), PL/master_tables 골든 `--update`. push 안 함.

> **2026-09-12 (90th pass) — AIA-456(item4/5/6 주석 전환 + item9-12 신규) + KR1010
> 2023.4Q item2/item16 근본원인 규명·정정, 10칸 변경.**
>
> 발주: 오케스트레이터 후속 2건, 둘 다 어제 하위 에이전트 조사(`docs/parser/
> pl_gap14_subagent_findings_20260912.md`)를 근거로. 하위 에이전트 없이 직접 처리.
>
> ### ① AIA-456 — KR0080(에이아이에이생명보험) 2025.4Q item4/5/6 정밀 소스 전환
>
> `companies.py`에 `_aia_note_pair`/`_aia_note_csm_ra_exp`/`_aia_note18_4_items`/
> `_aia_note19_3_items` 4개 함수 신설, `extract_tier2_aia`의 `if stmt:` 분기에 배선.
> 주석18(4) "...보험계약부채의 측정요소별 변동내역" 원수 표에서 item4/5/6 을 합계열
> 부호반전으로 직접 읽는다(153,100/30,500/−25,000[산문] → 153,059/30,499/−25,069[주석
> 천원정밀]) — item7 은 assemble() 잔차(item3−(4+5+6))가 자동 재계산(18,354.203→
> 18,465.203). **부수로 item9-12(재보험 CSM/RA/경험조정)도 신규 등재** — 주석19(3)
> "...재보험계약자산의..." 표에서 item9/10/11 을 뽑되, 이 표는 원수표와 **부호를 반전하지
> 않는다**(raw 그대로): 우선 uniform 반전을 시도하면 item12(=item8−(9+10+11))가
> −222,488.79(|item8|의 2.8배, 잔차가 총계를 압도)로 나와 즉시 기각, 반전 없이 쓰면
> item12=+65,275.21 로 이 표 자신의 "미래서비스+과거서비스" 두 블록 합(64,936, 부호선택과
> 무관하게 독립 계산됨)과 근접(같은 ~339백만 statement-vs-note 오차대) — 경제적으로도
> 타당하다(재보험 HELD CSM 상각은 원수와 달리 원수사 입장에서 비용이라 원수의 이익방향과
> 반대). item8(계산서 기준, 불변)과의 부호일치 게이트로 코드에도 고정.
>
> `_aia_note18_4_pair`는 캡션이 아니라 기초/기말 합계 연속성(전기 기말==당기 기초)으로
> 당기/전기 표를 가른다 — AIA는 "1) 당기"/"2) 전기" 두 표에 캡션 캡처 아티팩트(처브 사례와
> 동일)로 **똑같은 캡션 문자열**이 찍혀 텍스트로는 구별 불가.
>
> **2023.4Q·2024.4Q 는 손대지 않았다** — dry-run 만(직접 raw 로드해 새 함수 단독 호출,
> `extract_tier2_aia`의 실제 라우팅은 그 두 분기 모두 `_aia_from_statement` 경로라 내 변경이
> 애초에 안 닿는다는 것도 코드로 확인):
>   - 2023.4Q: `_aia_note18_4_items`가 `None` 반환(그 해 raw 에 대응 표 자체가 이 continuity
>     조건으로 안 잡힘) — 결과적으로 원래도 비어 있던 item4/5/6이 그대로 비어 있다.
>   - 2024.4Q: 같은 매핑을 적용하면 4=156,162.0 · 5=23,485.0 · 6=7,708.0(item9/10/11 도
>     −11,990/−6,542/−222,255) — 기존 마스터(156,200/23,500/7,500, 산문 기준)와 억원
>     반올림 수준에서 일치해 **방법론이 한 번 더 검증**됐을 뿐, 적재하지 않았다.
>
> ### ② KR1010(교보라이프플래닛) 2023.4Q item2(−19,236.64) ≠ item3+item8(−14,538.66) 원인
>
> raw 연결포괄손익계산서(`20240328001012_00761.xml`, 제11(당)기)를 직접 재파싱해
> 근본원인을 특정했다. **이 필링의 Ⅱ.영업비용 은 하위행이 7개인데("1.보험서비스비용"~
> "7.기타영업비용") 그중 "7.기타영업비용"(4,691,303,769원=4,691.303769백만원)이
> "3.기타사업비용"(1,933,610,508원)과 별개 행으로 존재 — 기존 item16 추출이 후자만 잡고
> 전자를 통째로 놓치고 있었다.** 2024/2025.4Q 는 "1.보험영업수익/2.보험서비스비용" 2행
> 구조라 기타비용이 한 줄에 다 들어있어 이 해만의 함정이었다(`pl_bridge_baseline.json`
> `_round_20260826b` 가 2024.4Q 를 이미 그렇게 raw 확인해 뒀다).
>
> item16 을 3.기타사업비용+7.기타영업비용=6,624.914277 로 고치면 item1(=item20−item17,
> top-down, **불변**) = item2(=item3+item8, canonical 공식) + item15 − item16 이
> **잔차 0.000000 으로 정확히 닫힌다**(재현: `scripts/_probes/
> probe_20260912_kr1010_2023q4_bridge_verify.py`). item2 도 임시값(=item1 을 그대로
> 복사, "원인 미규명"으로 89th pass 가 병기했던 값)에서 canonical 공식(=item3+item8=
> −14,538.659979)으로 정정 — `pl_bridge_baseline.json`의 known-gap 등재(class
> lob_sum_gap)는 삭제(자연히 닫히므로 예외 불요).
>
> **2024.4Q 의 item2=item1(−26,015.543184) 패턴은 손대지 않았다** — 겉보기엔 같은
> "item2=item1" 모양이지만 원인이 다르다: 이건 owner xlsx fill(review-loop 2026-06-19/
> 20)이고, `pl_bridge_baseline.json` `_round_20260826b`(2026-08-26, validation)가 그 해
> 필링의 "Ⅰ.보험손익" 원문 헤드라인 자체가 item3+item8−item16(하위행 누락 없음) 과 원
> 단위까지 일치함을 독립적으로 raw 확인해 뒀다 — 그 해는 기타사업비용이 보험손익 라인
> **안에서** 원수·재보험과 나란한 세 번째 다리라 item1=item2 가 그 해의 진짜 구조다. 서로
> 다른 필링 연도의 서로 다른 레이아웃이라 같은 수정을 적용하면 안 된다.
>
> ### 검증
>
> 회사 스코프 재실행(`scripts/_probes/probe_20260912_pl_scoped_build_aia_kr1010.py`,
> TARGET_CODES={KR0080,KR1010}) + combo-diff(LOST=0/GAINED=0/CHANGED=10, 두 회사 외
> 0건) → `build_root_masters.build_pl()`(개별 호출, `main()` 아님) → 재-combo-diff
> 동일 10칸 확인, 필드단위 null-flip 감사(2층) 0건. **안전성 재확인**: 골든 갱신을 위해
> `scripts/build_pl_breakdown.py` bare 를 1회 실행(SKILL 문서가 명시한 골든 갱신 절차,
> `build_root_masters.py::main()` 과는 다른 스크립트라 금지 대상 아님) → 결과가 스코프
> 빌드와 **cell-level 완전 동일**(LOST=0/GAINED=0/CHANGED=0, 12,122행·374개
> 회사분기 불변) — 이 가지가 git-purge 로 인한 붕괴 없이 안전함을 실측으로 재확인.
>
> `validate_data_contract.py`: 손익분해PL MASTER_XLSX_DRIFT RED → `sync_master_xlsx_
> sheet.py "손익분해PL"` 로 해소, 최종 **RED=0**(PL/CSM 축). 남은 RED 1건(K-ICS공시 시트
> 행누락, KR0079 등)은 kics 레인이 동시에 고치고 있는 `kics_disclosure.json` 소관이라
> 손대지 않음(재확인: 내 세션은 그 파일·시트를 한 번도 쓰지 않았다). `RUN_PL_GOLDEN=1
> pytest tests/test_pl_breakdown_golden.py` 는 의도된 드리프트(non_null_values
> 10253→10257, +4=신규 item9/10/11/12) 확인 후 `--update`. `test_master_tables_golden.py`
> 도 pl_bridge 3144P/35F/561S→3146P/34F/560S(+2P/−1F/−1S, KR1010 두 등식 동시 해소)·
> zero_legs 10→9 로 이동해 `--update`, 재확인 PASS. `test_rule_coverage_manifest.py`
> 93개 중 92 PASS·1 FAIL(`test_master_xlsx_clean_state_has_no_red`, 사유는 위와 같은
> K-ICS공시 RED, 무관). `validate_golden_input_fingerprints.py` 는 **pl_breakdown 항목만
> 수술적으로 갱신**(스크립트 자체는 all-or-nothing 이라 전용 스크립트로 그 키만 다시
> 계산해 UPSERT) — ifrs17_bs/dividend/post_transition 3그룹은 여전히 FAIL 인 채로 안 건드림
> (89th pass 부터 이어지는 kics 레인 concurrent 사유, 이 세션이 검증하지 않은 걸 blanket
> --update 로 얼렁뚱땅 통과시키지 않기 위해). `sync_master_xlsx_sheet.py "손익분해PL"`
> 검증 OK(12,122행×9열 완전일치).
>
> **최종 수치**: `PL_breakdown.json` 12,122행 불변(LOST=0), 값 변경 10칸(KR0080 4,5,6,7,
> 9,10,11,12 / KR1010 2,16). `pl_bridge_baseline.json` entries 35→34(KR1010 lob_sum_gap
> 삭제, `_round_20260912` 사유 기록).
>
> **파일**: `scripts/pl_breakdown/companies.py`(AIA 주석18(4)/19(3) 리더 4함수 신규 +
> `extract_tier2_aia` 배선) · `scripts/build_pl_breakdown.py`(`_GOLD_CELL_OVERRIDE`
> `("KR1010","2023.4Q")` item2/16 정정 + 주석) · `data/_gold/pl_bridge_baseline.json`
> (KR1010 항목 삭제 + `_round_20260912`) · `data/dart/viz/pl_breakdown_master.json` ·
> `data/_derived/pl_breakdown_coverage.json` · `PL_breakdown.json` · `insurequant_
> master_tables.xlsx`(손익분해PL) · `tests/fixtures/{pl_breakdown,master_tables}_
> golden.json`(`--update`) · `tests/fixtures/builder_input_fingerprints.json`
> (pl_breakdown 만) · `scripts/_probes/probe_20260912_kr1010_2023q4_bridge_verify.py`
> (신규, 커밋용 재현 프로브) · `scripts/_probes/probe_20260912_pl_scoped_build_aia_
> kr1010.py`(신규, 회사스코프 재빌드 스크립트).
>
> **잔여**: 없음 — 두 티켓 모두 자기완결(raw 근거·검산 잔차 0·게이트 확인 전부 이 세션
> 안에서 재현 가능). K-ICS공시 xlsx RED 1건은 kics 레인 몫(관찰만, 라우팅 불필요 —
> 그쪽 세션이 진행 중인 작업의 자연스러운 중간상태로 판단).

> **2026-09-12 (89th pass) — 티켓 2건 병행 처리: 3사 원문 대조(ticket 20260902T1200Z) +
> PL gap14 잔여 6칸 신규 등재 + AIA 재원 전환(ticket 20260901T1630Z).**
>
> ### ① `inbox/parser/20260902T1200Z` — KR1098/KR0075/KR0150 2023.4Q raw 대조
>
> downloader가 회수한 감사보고서 3건을 IFRS17_BS/CSM_waterfall/PL_breakdown 21항목/6항목/
> 24항목 스키마로 전수 대조. **IFRS17_BS**: 21항목×3사=63칸 대조 가능 셀 중 KR1098
> 12/13(1개 라벨변형 있었으나 값 확인), KR0075 9/9(480원 이내 반올림 1건), KR0150
> 17/17 **EXACT MATCH** — 특히 KR0150은 항목 전부 원 단위까지 일치해 기존 경영공시 백필
> (86th~88th pass) 품질을 raw 로 독립 재확인한 셈. 신규 채움 6칸(KR1098 item21=0,
> KR0075 item10/11/13/20/24) + 정밀도 교체 1칸(KR0150 item6, 경영공시 억원반올림→감사
> 보고서 천원단위, 억원 반올림 시 두 값 동일 수렴). **KR0075 item1/2(자산·부채총계)만
> raw(비정정 rcept)와 마스터(3필링 교차확인 vision-read) 사이 0.08%(2,412백만원) 불일치
> — item3/4는 정확히 일치해 정정공시 존재를 의심, 마스터 유지 + downloader 후속 확인
> 필요.** **CSM_waterfall**: KR1098/KR0150은 `보험계약마진` raw 키워드 0회/2회(전부
> 회계정책 서술문)로 기존 구조적 무 판정 재확인. **KR0075는 신규 6칸**(§14(4) 측정요소별
> 변동내역 원수 표에서 기초 257.511·신계약 18.131·이자부리 4.939·조정 148.174·상각
> -86.846·기말 341.909억원, 폐쇄검증 잔차 0, 2024.4Q 기초와 EXACT 연속성). **PL_breakdown**
> 은 이미 fe3a20f(09-02)가 KR1098/KR0075 2023.4Q 스켈레톤을 채워 뒀으나 item3-7(생명장기
> 원수손익 분해)이 비어 있었음 — CSM 갱신으로 새로 뜬 RED `PL_CSM_AMORT_VS_WATERFALL`을
> 계기로 같은 §14(4) 표에서 5칸 채움(item3=-10596.067·item4=-8684.565[CSM_waterfall과
> 원단위 일치]·item5=-2624.504·item6=-41152.756·item7=41865.758).
>
> ### ② `inbox/parser/20260901T1630Z` — PL gap14 잔여 6칸 + AIA Q2
>
> owner 결정(코디네이터 전달): Q1(6칸 신규 등재) + Q2(AIA 계산서 전환) 둘 다 승인. KR0050·
> KR0076·KR1098 8칸은 이미 이전 세션(09b4b26)이 처리해 검증만. 남은 6칸을 하위 에이전트
> 6개+AIA 조사 1개(총 7개, 병렬, 파일쓰기 없이 값·근거만 조사)로 원문 확보 후 이 세션이
> 직접 적재:
>   - **KR1010(교보라이프플래닛) 2023.4Q**: 24항목(연결 기준 — 기존 2024.4Q 마스터가 연결
>     값과 일치해 시계열 일관성 채택). item2(-19236.64) 대 item3+item8(-14538.66) 사이
>     4,698백만원 불일치 발견 — 둘 다 원문 근거 있으나 통합 안 됨, `pl_bridge_baseline.json`
>     에 `lob_sum_gap`으로 등재(원인 미규명, 후속 필요).
>   - **KR0150(서울보증) 2024.4Q**: `extract_tier2_sgi`/`_sgi_re_legs`가 이 필링 특유
>     라벨변형("재보험영업수익:" — 기존 코드는 "재보험수익:"만 인식)을 놓쳐 item13/14가
>     구조적으로 안 나오던 핸들러 버그를 **코드 수정**(companies.py)으로 해결 + item1/15-24는
>     `_GOLD_CELL_OVERRIDE`로 11칸 채움(13항목). 항등식 item1≈13+14+15-16 잔차 0.000346.
>     item2(생명장기손익) 구조적 N/A를 `LOB_LEG_NA` 등재부에 신규 등록(코리안리 옆에 서울
>     보증 추가) — 이 회사가 item1/24를 채워 `coverage_holes()`의 active_min=7 문턱을 처음
>     넘기면서 원래부터 구조적이던 item2 결측이 전 분기(2024.4Q~2026.2Q, 7분기) 일제히
>     "MASTER_HOLE 부분" RED로 터진 것을 `coverage_holes()`에 `na_registry` 파라미터
>     신설(양쪽 게이트 파일 공유)로 근본 해결.
>   - **KR0003(롯데손해) 2023.1Q**: IFRS17 최초도입분기, "4.재무제표"~"5.주석" 섹션이 원문
>     자체 공백(raw 직접 확인) — item20-24(요약손익표) 5칸만, 1-19는 억지로 채우지 않음.
>     CSM_waterfall엔 이 분기 데이터가 있어(item5 -392.84억) `PL_CSM_AMORT_VS_WATERFALL`
>     신규 RED 1건 발생 → `pl_csm_amort_missing_ledger.json`에 `NOT_DISCLOSED_SOURCE`로
>     등재(AIA 2023.4Q와 동일 카테고리).
>   - **KR0008(삼성화재) 2023.1Q**: `pl_breakdown_coverage.json`에 이미 no_income_statement
>     기록됐던 최초도입분기 전용 표 구조를 주석20 직접판독으로 24항목 채움(item1=2+13+14-16
>     원 단위 1 이내 정합). item15(기타영업수익)를 처음엔 N/A로 뒀다가 `보험손익(dual)`
>     leg-coverage 검사가 item15/16 둘 다 필요함을 실측하고 0.0으로 정정(assemble()의
>     기존 관례 "t1 있으면 item15 기본 0"과 정합).
>   - **KR0032(NH농협손보) 2023.1Q**: `extract_tier2_nh`의 캡션 매칭이 이 분기 전용 라벨
>     변형("보험손익" vs "보험영업이익", "적용하지않는" vs "을적용하지않는")을 못 잡던 것을
>     주석14+MD&A 직접판독으로 22항목 채움(item2=3+8·item20=1+17·item22=20+21·
>     item24=22-23 전부 EXACT). CSM_waterfall item5(-604.6억)와 item4(60459백만원)
>     억원단위 교차확인 일치.
>   - **KR0072(KDB생명) 2023.1Q**: 2023.2Q와 동일 원인(FS-API 013 + 구양식) — 기존
>     `_GOLD_CELL_OVERRIDE[("KR0072","2023.2Q")]`와 같은 메커니즘으로 18항목(13직접+5파생)
>     신규 등재. **부수 발견**: `build_pl_breakdown.py::main()`이 t1=t2=None이면 override
>     존재 여부와 무관하게 무조건 skip하는 버그가 있어 이 셀의 override가 애초에 적용
>     불가능했다 — override 존재 시 skip을 우회하도록 수정(다른 회사 영향 0, 전 회사 재빌드
>     row/company_quarter 카운트 불변으로 확인).
>   - **AIA(KR0080) 2025.4Q**: item18/19는 이미 정확(2023/2024.4Q도 재확인, 무변경).
>     item1/3/7/8/16/17/18/20/21/22/23/24 13칸을 산문(억원 반올림) 기준에서 감사받은
>     포괄손익계산서(`_aia_statement`, 천원 정밀) 기준으로 전환(`extract_tier2_aia` 수정 —
>     item4/5/6는 계산서에 측정요소 분해가 없어 계속 산문 소스, item7은 잔차로 전환).
>     `pl_bridge_baseline.json`의 `보험손익(dual) diff=+1000.0` 항목이 실제로 0.000으로
>     닫혀 등재 제거.
>
> ### 공통 검증·게이트
>
> 전부 `scripts/build_pl_breakdown.py::_GOLD_CELL_OVERRIDE`(신규 5개사) + companies.py
> 코드수정(KR0150) + `data/dart/viz/{bs_manual_overrides,pl_bridge_baseline,
> pl_csm_amort_missing_ledger}.json`/`data/_gold/{user_csm_cells,user_pl_cells}.json`
> gold-overlay로 반영, **회사 스코프 재실행**(`build_pl_breakdown.py::discover_filings`
> 결과를 TARGET_CODES로 필터링하는 전용 스크립트, `build_root_masters.py main()` 미실행)
> + **combo-diff 2층**(cell-key 전수 LOST/GAINED/CHANGED + 예상 밖 회사 터치 여부)로 매
> 단계 확인. 최종: `IFRS17_BS.json` 8,840→8,846행 · `CSM_waterfall.json` 2,172→2,178행 ·
> `PL_breakdown.json` 11,930→12,122행(LOST=0 전 구간). `RUN_PL_GOLDEN=1 pytest
> tests/test_pl_breakdown_golden.py`가 전체 39사 재빌드로 회사스코프 결과와 **바이트
> 동일**함을 재확인(로우/회사분기/논널 카운트 일치) — 별건 회귀 없음 증명. `validate_data_
> contract.py` **RED=0**(작업 중 신규 RED 3종 전부 fix 또는 등재로 해소: PL_CSM_AMORT_VS_
> WATERFALL 2건[KR0075→fix, KR0003→등재], MASTER_HOLE 7건[KR0150 item2→LOB_LEG_NA
> 등재로 구조적 해소]). `test_master_tables_golden.py`/`test_rule_coverage_manifest.py`
> (83개 전부 통과 — item23 법인세를 PL_CONSTRUCTIVE_BLIND→GUARDED로 이동, PL_YTD_
> COLLAPSE_TO_ZERO가 KR0072 2023.1Q 신규로 인접분기 비교가 가능해지며 새로 포착됨을
> 실측 확인) 전부 `--update` 재생성+PASS. `sync_master_xlsx_sheet.py`로 "17BS"·"CSM워터폴"·
> "손익분해PL" 3시트 cherry-pick(전부 "검증 OK"). 골든 입력지문(ifrs17_bs·pl_breakdown·
> viz_ifrs17_panels 3그룹) surgical 갱신 — **dividend·post_transition 2그룹은 여전히
> FAIL, kics 레인이 병행 수정 중인 `kics_disclosure.json`이 원인이라 손대지 않음**
> (spawn_task로 후속 티켓 등록, kics 레인 작업 완료 후 그쪽에서 재검증 필요).
>
> **파일**: `scripts/build_pl_breakdown.py`(`_GOLD_CELL_OVERRIDE` 6개사 신규/보강 +
> None/None skip 버그 fix) · `scripts/pl_breakdown/companies.py`(`_sgi_re_legs`/
> `extract_tier2_sgi` 라벨변형 + `extract_tier2_aia` 계산서기준 전환) ·
> `scripts/validate_master_tables.py`(`coverage_holes(na_registry=)` 신설, `LOB_LEG_NA`
> 에 서울보증 추가, `PL_ITEMS_UNCHECKABLE_BY_EQUATION`에서 item23 제거) ·
> `scripts/validate_data_contract.py`(MASTER_HOLE 호출부 na_registry 배선) ·
> `tests/test_rule_coverage_manifest.py`(item23 BLIND→GUARDED, GOLD_OVERLAY_CENSUS 갱신) ·
> `data/dart/viz/bs_manual_overrides.json`(2081→2087) · `data/_gold/user_csm_cells.json`
> (270→276) · `data/_gold/user_pl_cells.json`(198→203) · `data/_gold/pl_bridge_baseline.json`
> (+1 KR1010, -1 AIA) · `data/_gold/pl_csm_amort_missing_ledger.json`(+1 KR0003) ·
> 골든 4종(ifrs17_bs·master_tables·pl_breakdown 전부 `--update`) · 지문·xlsx 동기화.
> `scripts/_probes/probe_20260911_*.py`·`probe_20260912_*.py`(신규 조사/적용 스크립트 다수).
>
> **잔여**: KR1010 item2 vs item3+item8 불일치 원인 미규명(등재만 완료) · KR0075 item1/2
> 0.08% 불일치(정정공시 여부 downloader 확인 필요) · KR0080 item4/5/6은 여전히 산문 소스
> (계산서에 측정요소 분해 없음, 더 정밀한 별도 주석표가 있다면 후속) · dividend/post_
> transition 지문 FAIL은 kics 레인 몫.

> **2026-09-11 (88th pass) — round2 백필: 엔진 버그 6종 수정 + 서브에이전트 4개(≤4 한도)
> 병렬 비전 백필, 코어 결측 117→29(88건 닫음, 75%).**
>
> 발주: `inbox/parser/20260911T0920Z`(오케스트레이터). 87th pass(1라운드)가 닫은 925칸
> 이후 남은 코어(항목1·2·3) 결측 (회사,분기) 117개를 마저 닫는 것이 목표. 근본원인을
> sender 가 "①표 고정 과엄격 ②QoQ 단방향 앵커 ③4Q앵커 없음" 3가지로 짚었으나, **실측
> 재현해보니 실제 원인은 다른 6가지 엔진 버그였다**(sender 가설이 완전히 틀린 건 아니고
> 방향은 맞았으나 구체 메커니즘이 달랐음 — 아래 "실제 근본원인" 참조). 사람이 추측으로
> 우회하지 않고 코드를 고쳐 기계가 다시 찾게 만드는 쪽을 택했다.
>
> **실제 근본원인 6가지 (전부 `scripts/bs_disclosure/common.py` 실측 재현 후 수정)**:
>   1. **헤더 마커 사각**: `당분기`/`당기말`/`당분기말`/`해당분기`(현재기간)와 `전기기말`
>      (전기)가 `_CUR_WORD_RE`/`_PREV_WORD_RE`에 없어 헤더 인식 자체가 실패(악사손해 다수
>      분기). `당기` 리터럴만 보고 `당기`+접미사 변형을 놓치는 비대칭이 원인.
>   2. **헤더-데이터 열 오프셋**: 일부 표는 헤더 텍스트가 데이터보다 그리드 1칸 뒤에 찍힌다
>      (헤더 `과목`은 col1, 데이터 라벨은 col0 — 병합폭 안에서 헤더가 오른쪽으로 밀림). 방치하면
>      라벨 칸에 다음 칸 값이 섞이고 당기/전기/증감이 하나씩 밀려 서로 바뀐 값을 읽는다
>      (AIG손해·악사손해 다수 분기). `_pad_shift()` 신설로 해결 — 패딩 없는(대다수) 표는 항등.
>   3. **표제 순서 반전**: "(별도)"/"(연결)" 괄호수식어가 별개 텍스트런이라 fitz 추출이
>      "재무상태표별도"/"재무상태표연결"(순서 반전)로 뽑는 문서가 있다(AIG손해 2026.1Q) —
>      `page_is_consolidated()`가 "별도재무상태표" 순서만 봐서 신호없음(None)으로 떨어져
>      최악의 경우 연결표를 고를 위험이 있었다. 양쪽 순서 다 인식하도록 수정.
>   4. **"6-4" 마커 오탐**: 숫자 조판 우연으로 "...206" 바로 뒤에 음수 "-4,558,932"가
>      이어 붙으면 "206-4,558,932" 안에 "6-4" 부분문자열이 생겨 진짜 별도표 페이지가
>      `EXCLUDE_PAGE_MARKERS`에 걸려 통째로 후보에서 빠졌다(AIG손해 2026.1Q). "6-4."(마침표
>      포함)로 좁혀 해결 — 원래 의도(6-4.시장위험 절번호)는 `시장위험`/`익스포져` 마커가
>      이미 중복 커버해 안전.
>   5. **△(세모) 미인식** — **가장 파급력 큰 버그**: `parse_number()`가 괄호(1라운드 기지)만
>      음수로 인식하고 **한국 회계 관행의 세모(△) 음수 표기를 몰랐다**. 값이 "△244,064,
>      855,740" 이면 `float()` 가 ValueError 로 죽고 그 행 전체가 **스킵 사유도 없이 조용히**
>      유실됐다(KR0004 2025.1Q '자본 총계' 실측). 음수 항목이 있는 분기마다 재발 가능한
>      구조적 함정이었다 — 수정 후 KR0004 여러 분기가 추가로 열렸다.
>   6. **표 하나가 페이지/표객체 여러 개로 쪼개짐**: (a) 페이지 경계(기존 1페이지 이어짐
>      로직을 최대 8페이지로 확장 — 처브라이프 KR0100 은 자산총계~부채와자본총계가 6페이지에
>      걸침) (b) **같은 페이지 안에서** fitz 가 표 객체 2개로 쪼개는 경우(KR0100 2023.3Q,
>      자산+부채 앞부분/자본총계 뒷부분이 별개 객체) — 두 경우 다 원표 열 개수와 다르면
>      `groups`의 논리 열 순서로 재배치해 병합하도록 일반화. (c) **한 논리열 안에서 총계류
>      4개 행만 별도 칸에 분산**(IBK연금 KR1011, `Ⅱ.기타포괄손익누계\n액` 줄바꿈 아티팩트도
>      같이 발견) — `_reconcile_two_blob_span()` 신설, 라벨 순서를 따라가며 총계 라벨은
>      별도 뭉치에서 뽑아 재구성.
>
> **추가로 항목3(자본총계) QoQ hold 4칸을 DART/뉴스 공시이력으로 사람이 확인 후 수동
> 승격**(엔진이 안 낸 값이 아니라 엔진이 **정확히 추출은 했는데** 양방향 QoQ 게이트가
> hold 한 값을 산업 맥락 검증 후 채택 — `data/_derived/bs_from_disclosure_parts/
> {KR1010,KR0004}_agent_note.json`): KR1010(교보라이프플래닛) 2023.1Q/2Q/3Q 자본총계
> 103,768/125,904/131,097백만원 — 웹검색(인사이트코리아·ZDNet 기사)으로 2023년 7차
> 유상증자(누적 3,690억) + IFRS17 도입 연간손실 214억원 확인, "증자 후 상승→연말 대손실로
> 재하락"(2023.4Q 기존 마스터 61,432백만원과 정합) 패턴 확정. KR0004(예별손해) 2025.3Q
> 자본총계 29,899.975245백만원 — 티켓이 owner 확정치로 지목한 "+29,899"와 추출값이 정확히
> 일치, MG→예별 자본확충 이력(project memory)과 정합. **KR0004 2024.1Q/2Q/3Q 항목3도
> 같은 유형(190,149→15,696→-55,146→-18,433→-125,357 감소추세, 항등식은 닫힘)이지만
> 티켓이 명시 지목하지 않았고 외부 근거가 KR1010/2025.3Q 만큼 강하지 않아 owner 재확인
> 대상으로 남기고 스킵 유지**(skip_reason 에 추출값 그대로 보존).
>
> **서브에이전트 4개 병렬**(세션 한도 준수) — 이미지 기반(텍스트 레이어 없음) 5개사를
> 렌더링(dpi220)+시각판독으로 백필, 전부 4Q 정답지 교차확인 후 적재:
>   - KR0074(라이나생명) 9분기(2023.1Q~2025.3Q) — 129칸, 2024.4Q 15/15 EXACT. 부수발견:
>     2023.4Q↔2024.1Q 사이에 소급재작성 basis 경계(주석34, IFRS1117/갱신형보험) — 이 티켓
>     범위 밖이라 안 건드리고 owner 재확인용으로 파일 readme 에 기록만.
>   - KR0075(BNP카디프생명) 11분기 — 106칸, 4개 앵커(2023.4Q/2024.1Q/2024.3Q/2025.1Q/
>     2026.1Q) 교차확인. 구조적 발견: 항목10·11·13·20·24 는 이 회사 분기공시가 특별계정
>     제외 일반계정만 집계하는데 마스터는 감사보고서 기준 전사합계라 **개념 자체가 다름**을
>     4분기 교차대조로 확정(최대 85배 이탈 실측) — 11개 분기 전부 그 5항목만 의도적 결측.
>   - KR0097(하나생명) 10분기 — 143칸, 2023.4Q 16/16 EXACT. 2024.1Q 항목1 은 원문 헤드라인
>     자체가 1,000만원 오류(세부합계·부채+자본 둘 다와 어긋남, 500dpi 재확인)라 결측 유지.
>     2026.1Q 는 8-1.별도재무상태표 물리 페이지 자체가 PDF 에서 누락(전수 페이지시퀀스
>     확인) — 대체 가능한 표는 전부 억원 단위 요약/감독기준표라 채택 불가.
>   - KR0076(아이엠라이프)+KR1098(카카오페이손해) 10분기 — 138칸. KR0076 는 사명변경 이력
>     (DGB생명→iM라이프) 확인, 2개 앵커×2개 filing 재현(30항목-분기 중 29 EXACT, 유일
>     불일치 항목24 는 확정급여부채 분리 이전/이후 컨벤션 차이로 원인 규명 후 스킵).
>     KR1098 는 연차(Q4) 공시 자체가 없는 회사라 **분기 filing 의 전년도말 비교열을 4Q
>     대용 앵커로 사용**(48/48 EXACT) — `calibrate_detail_items` 개선 아이디어로 TODO 하단
>     기록. item31 라벨 미등록 변형("이익잉여금(결손금)") 도 항등식 역산으로 확인.
>
> **머지+빌드+검증(1라운드와 동일 경로)**: `merge_bs_disclosure_parts.py`(엔진 24 +
> note 2 + vision 8 파트파일) → **머지 전 전수 충돌검사 스크립트로 기존 overrides
> 1,208칸 중 이번 라운드 파트파일과 겹치는 136개 전부 값 동일(충돌 0건) 확인 후 실행** —
> 873신규+136교체(교체=동일값 재적용, 실질 변경 없음), overrides 1,208→2,081칸.
> `build_ifrs17_bs.py` → 마스터 7,967→8,840행(순증 873행). **`verify_no_change.py`(baseline
> 스냅샷 대조)로 기존 7,967행 전부 값 불변(0건 변경/삭제) 확인** — 1라운드 925칸 포함 전체
> 보호됨. `validate_data_contract.py` **RED=0** YELLOW=88(1라운드 83 대비 +5, kics_disclosure/
> PL_breakdown 카테고리라 IFRS17_BS 무관 — 동시 세션 작업으로 추정, 미조사). `validate_
> master_tables.py --no-build` 는 exit code 2(FAIL 다수)지만 **`test_master_tables_golden.py`
> PASS로 확인 — 전부 사전 등재된 PL/CSM 기지 baseline, 회귀 0**(BS 데이터를 건드리지 않는
> 축이라 원천적으로 무관). `tests/test_ifrs17_bs_golden.py --update`(8,840행·39사, 재현
> 363초) + `validate_golden_input_fingerprints.py --update` + `sync_master_xlsx_sheet.py
> "17BS"`(7,967→8,840행 동기화 확인) 전부 완료. `tests/test_deploy_assets.py` 11/11 PASS
> (신규 .py 5개 BOM 없음·구문 정상 확인).
>
> **최종 수치**: 코어(1·2·3) 결측 (회사,분기) **117 → 29**(88건 닫음, 75%). `bs_manual_
> overrides.json` 1,208→2,081칸(순증 873). `IFRS17_BS.json` 7,967→8,840행. 사이드카
> `data/_derived/bs_from_disclosure.json` 1,009칸/366스킵(스킵 전부 skip_reason 有 — 잔여
> 29건도 전수 확인: `scratchpad/final_gap_check.py`+수기 grep 으로 0 건 누락). 게이트
> `validate_data_contract.py` RED=0. push 안 함(금지).
>
> **잔여 29건 사유 분류** (전부 skip_reason 기록, 추측 적재 0건): 이미지(텍스트 레이어
> 없음, 렌더링 미착수) 12건 — KR0049 3(2024.3Q~2026.1Q)·KR0080 3(2025.1Q~2026.1Q)·KR1011
> 4(2025.1Q~2026.1Q, 총계열 분산 패턴이 다름 6번 항목과 별개)·KR0100 1(2024.2Q)·KR0097
> 1(2026.1Q, 물리페이지 누락). 원문 자체 데이터 결함 1건 — KR0097 2024.1Q(헤드라인
> 1,000만원 오차). 경영공시 첨부파일 미수집(원본이 disclosure PDF 밖) 9건 — KR0050 전부
> (15페이지 축약본, "재무제표 사항은 첨부 파일 참조"). QoQ 게이트 hold(원문 재확인
> 필요, owner 재검토 권장) 7건 — KR0004 5(2024.1Q~3Q 항목3 + 2026.1Q/2Q 항목1, 2026년
> 값은 48배 점프로 스케일 오판 의심이라 특히 재확인 필요)·KR0051 1(2025.3Q)·KR1098
> 1(2025.2Q).
>
> **owner 재확인 필요 2건**: (1) KR0004 2026.1Q/2Q 항목1이 직전 대비 48배 — 정상 성장
> 범위를 크게 벗어나 스케일 오판 의심, 사람 재확인 후 채택 여부 결정. (2) KR0004
> 2024.1Q~3Q 항목3 — 항등식은 닫히고 트렌드도 그럴듯하나(자본잠식 진행형) KR1010 만큼
> 강한 외부 근거는 없음, DART 공시이력 추가 확인 후 채택 여부 결정.
>
> **재현 명령**:
> ```
> C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/extract_bs_from_disclosure.py --company all,KR0002,KR0005,KR0068,KR0069,KR0083
> C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/merge_bs_disclosure_parts.py
> C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/build_ifrs17_bs.py
> C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_data_contract.py
> C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/sync_master_xlsx_sheet.py "17BS"
> ```

> **2026-09-11 (87th pass) — 코디네이터 course-correction 5건 전부 처리, 게이트 RED
> 12→0.** 86th pass 직후 코디네이터가 지시한 5건: (1) 분기공시사 5개사(한화손해·흥국화재·
> 삼성생명·푸본현대·한화생명) 9분기 백필 — 이미 86th pass 세션 도중 처리돼 있었음(재확인만).
> (2) merge→build→validate 재실행. (3) **RED=12(예별손해·카카오페이손해 2023 QoQ hold) —
> "게이트 판정이 아니라 원문으로 직접 판정하라"** 지시대로 DART 자본변동표 조회: 예별손해는
> FY2023 사업보고서(rcept 20240408000665)에 유상증자(자본금+13.9억/자본잉여금+26.0억)+
> 결손보전(자본잉여금→이월결손금 308.5억 재분류) 실측, 카카오페이손해는 FY2023 사업보고서
> (rcept 20240329002933)에 유상증자 1,000억(자본금 1,000→2,000억, 2023.12.31) 실측 — 둘 다
> 2023년 중 진짜 자본재구성이 있었다(추출오류 아님). `scratchpad/unhold_kr0004_kr1098.py`로
> QoQ 게이트 우회 후 항등식(1=2+3)은 그대로 검산, 41칸 적재(기존 엔진출력 9칸과 값 100%
> 일치 — 교차검증). (4) KR1011(IBK연금)·KR0080(AIA) 렌더링+비전 — 이미 86th pass 세션
> 도중 완료돼 있었음(KR1011 15칸·KR0080 17칸, 전부 4Q/축척 항등식 교차확인, 재확인만).
> (5) 사이드카 skip_reason "None 잔존" 재확인 — `grep -rzoP '"skip_reason":\s*null'` 전체
> parts(29개)+사이드카 전수 스캔 **0건**, 코디네이터가 본 None은 이 세션 초반의 stale
> 스냅샷으로 판단(이미 그때 수정 완료돼 있었음). 사이드카(`bs_from_disclosure.json`)가
> 유일 정본이고 parts 개별파일은 재실행마다 대상축소로 내용이 줄어들 수 있다는 점을
> 명시(완전 빈 파일 KR0002.json 1개만 정리 삭제, 스킵사유 있는 0-cell 파일은 보존).
>
> **게이트 RED=12→3→0 경로**: merge(606칸)+rebuild(7959→7966행, combo-diff LOST=0)+
> validate → RED=3(COMPLETENESS CENSUS 1 + MASTER_XLSX 2). 잔여 COMPLETENESS RED
> 1건(**푸본현대생명 2023.1Q 항목3(자본총계) 결측**) 조사: 원문 raw PDF p22 에 '자본총계'
> 578,326,429,715원 값이 실재하고 항등식(1=2+3) EXACT, 축척 앵커 완전일치, 현재 시점 QoQ
> 재계산도 -9.7%로 정상 통과 — 과거(이 세션 초반, 앵커 후보가 지금보다 훨씬 적던 시점)
> QoQ hold 로 단독 스킵된 뒤 항목1 이 이미 채워져 재타겟되지 않고 방치된 것으로 판단, 직접
> 복원(`_fill_kr0083_2023q1_item3.json`). 추가로 KR0002(한화손해) 항목4 2023.1Q/2Q 도 같은
> 부류(라벨 '기타자본구성요소' 정확매칭·항등식 EXACT·축척 완전일치인데 앵커가 부호반전
> 구간이라 QoQ 상대비율이 폭발해 hold)로 원문 재확인 후 해제, KR0068(한화생명) 항목4
> 2023.2Q 는 fitz 표가 라벨 21개를 한 칸에 뭉친 특수구조라 위치기반 복원(같은 표 9개
> 타항목 전부 마스터와 EXACT 일치로 열정렬 검증 + 자본 5구성요소 합산=자본총계 EXACT로
> 행정렬 이중검증). re-merge(607칸)+rebuild(7966→7967행, combo-diff LOST=0, GAINED=
> KR0083|3|2023.1Q 1건만)+validate → **RED=3→2**(MASTER_XLSX 2건만) → `sync_master_xlsx_
> sheet.py "17BS"`(7772→7967행 동기화) → **RED=0**. `tests/test_ifrs17_bs_golden.py
> --update`(7967행·39사) + `validate_golden_input_fingerprints.py --update` 둘 다 재생성,
> `validate_master_tables.py --no-build` 골든(`test_master_tables_golden.py`) 통과 재확인
> (CSM/PL 축 무변경이라 회귀 없음).
>
> **최종 수치**: `bs_manual_overrides.json` 363→1,208칸(순증 845칸), `IFRS17_BS.json`
> 7,042→7,967행(순증 925행, 39사). `data/_derived/bs_from_disclosure.json` 사이드카
> 607칸/240스킵(스킵 전부 skip_reason 有, 재현: 위 grep). 게이트 최종
> `validate_data_contract.py` **RED=0 YELLOW=83**(기존 수준). push 안 함(여전히 금지).
> 티켓 `## 답변` 갱신 완료.

> **2026-09-11 (86th pass) — 17BS 경영공시(정기경영공시 raw PDF) 백필 신규 엔진 구축,
> TIER2 15개사 21항목 대상 overrides 669칸 순증(363→1,032칸), 마스터 7,042→7,772행.**
>
> 발주: `inbox/parser/20260911T0109Z`(오케스트레이터, 15-agent 조사 `artifacts/validation/
> ifrs17bs_disclosure_backfill_survey_20260911.md` 기반). 대상 = TIER2(연1회 공시사)
> 15개사 × 2023.1Q~2026.2Q × 마스터 스키마 21항목(1·2·3·4·5·6·7·8·10·11·12·13·14·15·20·
> 21·22·23·24·30·31) 전부. **5개 분기공시사(KR0002 한화손해·KR0005 흥국화재·KR0068
> 한화생명·KR0069 삼성생명·KR0083 푸본현대)는 owner 가 명시적으로 범위 밖으로 지정** —
> 원인이 DART FS-API 전사 무응답(013)이라 disclosure-PDF 백필 축이 아니다, 손대지 않음.
> 세션 도중 12:20경 API 세션한도(429)로 오케스트레이터 + 서브에이전트 3개가 전부 죽었다가
> 12:50 리셋 후 재개(코디네이터 course-correction 메시지로 디스크 실측 상태 재확인 후 계속).
>
> **1) 신규 패키지 `scripts/bs_disclosure/`**(common.py 659L + reserve.py 39L) +
> `scripts/extract_bs_from_disclosure.py`(371L, 오케스트레이터) + `scripts/
> merge_bs_disclosure_parts.py`(123L, 병합+오버라이드 UPSERT). 방법:
>   - **표 고정**: `재무상태표` 신호 있는 후보 페이지 중 `비지배지분` 행 부재 AND
>     `운용자산` 행 부재(감독규정 별표 배제) AND 자산총계/부채총계/자본총계 3개 라벨
>     실존. `업무보고서 기준으로 작성`/`감독회계기준`/`건전성감독기준`/`요약재무상태표`/
>     `시장위험`/`익스포져`/`6-4`/**`첨부파일 참조`**(신규, 아래) 페이지는 후보에서 제외.
>   - **열 고정**: 헤더 마커 3가지 컨벤션 지원 — ①`제N(당)기...`(최다수) ②맨 `당기`/`전기`
>     (괄호 없음) ③**역년**(`2023년도`/`2023년`, AIG 실측 — 더 큰 연도가 당기). 증감(QoQ)
>     열은 `당기-전기==증감` 자기검산으로 열 매핑을 재검증.
>   - **축척 판정**: 후보 4종(원/천원/백만원/억원)을 전부 계산해 **같은 회사·항목의 가장
>     가까운 "다른 분기" 관측치와 배수가 0.2~5배 안에 드는 후보가 정확히 하나**일 때만
>     채택(표 하나=단위 하나, 항목1로 대표 판정 후 전 항목에 동일 적용). **티켓 원문의
>     "±50백만원 절대오차"를 그대로 안 썼다** — 실측(KR1010 2022.4Q→2023.1Q 자산 +6.4%,
>     41,168백만 증가)으로 절대오차가 인접분기 정상 성장조차 못 버텨 전면 스킵을 냈다.
>     후보 4종이 100~1000배씩 차이나므로 배수 방식으로도 자릿수 오류와 정상 변동이 안
>     섞인다(그 이유를 common.py `SCALE_BAND` 주석에 실측과 함께 남겼다).
>   - **calibration gate**: 항목1(자산총계)만 무조건 신뢰(축척 기준점). 항목2/3/4/10~31은
>     그 회사의 **실제 Q4**(마스터에 DART 원천값 있음)에서 같은 방법으로 재현되는지 먼저
>     검사하고 통과분만 중간분기에 적용. **항목2/3도 코어인데 이 게이트를 받는다** —
>     비순환 검증 중 TIER-1 KR0070(에이비엘생명)·KR0071(흥국생명) 두 회사에서 경영공시
>     표의 부채/자본 분류가 마스터(DART)와 15~23% 어긋남을 실측(원인: 신종자본증권류
>     하이브리드 자본상품의 부채/자본 분류 차이로 추정, 자산총계는 무관). **항등식(1=2+3)
>     은 이 오류를 못 잡는다**(같은 합계 안에서 2↔3 로 값이 옮겨가므로). Q4 앵커가 아예
>     없는 회사(예: KR1010 항목31)는 라벨이 단일개념이라 애매하지 않은 항목(4·10·11·12·
>     14·15·30·31)만 미검증 통과("unverified" 표시), 위험항목(13·20·21·22·23·24)은
>     계속 막는다. 항목13(상각후원가측정금융자산)은 부모/자식/개별자식(대출채권 등) 3종
>     후보를 다 만들어 Q4 재현되는 쪽을 채택 — 같은 회사도 시점에 따라 컨벤션이 바뀐다
>     (2025년 계정명 변경, KR1010 실측: 2024.4Q 는 자식(대출채권)=합계로 우연히 같았다).
>   - **산술검산**: 항목2/3 후보가 둘 다 있으면 항등식(1=2+3) 검사, 실패 시 항목1 만 남기고
>     그 분기 나머지 전부 스킵(표 오선택 의심). **QoQ ±30% 초과는 hold**(스킵+사유, 절대
>     추측하지 않음).
>   - 법정준비금 5~8은 새로 안 만들고 기존 `scripts/_probes/probe_20260902_surrender_
>     reserve_vs_disclosure.py`(84th/85th pass, 39사 전수검증 완료)를 그대로 재사용,
>     **마스터에 이미 값 있는 셀은 건드리지 않음**(결측 채우기 전용).
>
> **2) 실측 버그 4종 발견·수정**(전부 common.py/orchestrator 에 실측 사례와 함께 주석):
>   - `qualify_table`이 라벨칸이 아니라 행 전체를 이어붙여 총계행 숫자가 라벨에 달라붙어
>     정확일치가 깨짐(KR1010 2023.1Q "자산총계683,734,..." 로 오판) → 라벨 span만 사용.
>   - 헤더 탐색이 0행 고정이라 "회사명+단위캡션" 이 0행에 끼는 필링(KR1010 2026.1Q)에서
>     실패 → 처음 3행 중 마커 있는 행을 헤더로.
>   - **Q4 경영공시 본문에 BS 가 아예 없고 "감사보고서·재무상태표·...등은 첨부파일
>     참조"만 있는 회사**(KR0051 실측)에서, 그 안내문에 "재무상태표" 단어가 들어 있어
>     엉뚱한 노트표(금융상품 현황)가 후보로 오탐될 뻔함 → `첨부파일 참조` 페이지 배제.
>     **이게 애초 "KR0051 항목2/3/4 가 안 나온다"는 회귀처럼 보였던 근본원인**이었다(Q4
>     재현검사가 매번 실패해 calibration 이 통째로 blocked 로 떨어졌었다) — 고친 뒤
>     "Q4 표 자체가 없는 회사"를 **구조적 미검증**(대조 실패가 아님)으로 별도 분류해
>     항목2/3 도 안전-미검증 허용 대상에 넣도록 재설계.
>   - **항목8(보증준비금)을 손보사에도 씀** — reserve.py 래퍼가 build_ifrs17_bs.py 의
>     생손보 가드를 안 물려받아 손보 TIER2 6개사(예별·AIG·악사·하나손해·신한이지·
>     카카오페이손해)에 오기재 57칸, 검증룰 R_RSV_8 RED 다발. `NONLIFE_TIER2` 가드 추가
>     + 오기재 57칸 제거(직접 삭제, 재빌드로 자동 정리되는 게 아니라 overrides.json 에서
>     명시적으로 지워야 했다 — 그 값이 이미 한 번 병합됐었으므로).
>   - fitz `find_tables()`가 섹션 전체(9~37줄)를 라벨/값 한 셀에 `\n` 으로 뭉치는 페이지
>     (AIA 2023.1Q 부채 9줄, IBK연금 2026.2Q 전체 37줄) → `_split_multiline_rows`로
>     라벨·값 분할 개수가 일치할 때만 복원(IBK연금은 라벨 안에 워드랩 `\n`과 항목구분
>     `\n`이 섞여 있어 이 방법으로도 못 품 — 아래 잔여 참조).
>   - 표가 페이지 경계에서 잘림(AIA 2023.4Q 36행에서 끊기고 다음 페이지가 "5.이익잉여금"
>     부터 이어받음, 헤더 반복 없이) → `_continuation_rows`로 다음 페이지 표를 병합
>     시도 후 전체 재검증(qualify_table 전부 통과해야 채택 — 오탐 방지).
>   - `find_tables_on_page`가 문서 마지막 페이지에서 `page_idx+1` 조회 시 IndexError로
>     죽음(비순환검증 재실행 중 실측) → 범위 밖이면 빈 리스트.
>
> **3) 비순환 확대 재현**(수용기준 6번, `--validate`, `data/_derived/
> bs_backfill_validation.json`): TIER-1(TIER2 아닌 전부) 24사 × 중간분기 × 항목1/2/3,
> 축척 앵커로 쓴 항목은 순환이라 집계 제외. **최종 match=143 mismatch=59 skip=147**
> (엔진 개선 전 1차 실측 50/32/207 대비 향상). mismatch 분류:
>   - KR0070·KR0071·KR0003(합 34건): 위 하이브리드자본 부채/자본 분류차이 패턴 — 추출
>     자체는 정확(원문과 소수점까지 일치 확인), calibration gate 로 프로덕션 경로는 방어됨.
>   - KR1000(18건): 1~14% 양방향 노이즈, 방향성 없어 원인 미상 — 후속조사 필요.
>   - KR0094(7건): 0.3~0.6% 소액 반올림, 사실상 일치로 봐도 무방.
>
> **4) 이미지 BS(수용기준 7번)** — fitz 텍스트/표 추출이 전혀 안 통하는 4개사 중
> **3개사를 직접 렌더링(dpi=220)+시각판독**으로 처리, 전부 **4Q 정답지 교차확인 후에만
> 적재**(비교열 vs 마스터 실측 Q4 값 EXACT 일치 확인):
>   - KR0074(라이나생명) 2026.1Q/2Q: 15/15 항목 EXACT, 전부 적재(항목21 한 칸은 원문
>     "-"라 스킵).
>   - KR0097(하나생명) 2026.2Q: 15/15 항목 EXACT, 전부 적재(항목22 투자계약부채 최초
>     실사례 확보). 2026.1Q는 disclosure PDF 자체가 18p 축약본이라 8-1 절이 없어 스킵.
>   - KR0075(BNP카디프) 2026.2Q: 9개 항목 EXACT, **5개 항목(10·11·13·20·24)은 4Q
>     정답지와 불일치**(특별계정/변액 자산 재구성 의심, 원인 미확정) → 그 5개 항목은
>     스킵(틀린 값을 싣느니 빈 칸).
>   - `data/_derived/bs_from_disclosure_parts/{KR0074,KR0097,KR0075}_agent_vision.json`.
>
> **5) `check_ifrs17_bs`의 `_in_scope`(수용기준 8번, L2448 근방) 확장** —
> `scripts/validate_data_contract.py`에 `_bs_in_scope(code, q)` 신설, `BS_BACKFILL_
> TIER2`(15개사) 소속일 때만 전체 분기지평(quarter_horizon)을 스코프로 쓰고 그 외
> 회사는 기존 `_DISPLAY_QUARTERS` 그대로. **처음엔 회사축 없이 전사로 넓혔다가 무관
> TIER-1 9개사(한화손해·흥국화재·DB손해·한화생명·삼성생명·에이비엘생명·흥국생명·
> 푸본현대·서울보증) 2023.1~2Q(+서울보증 2024.1~3Q) 기존 결측이 RED 51건으로 쏟아진
> 것을 실측하고 회사축을 추가했다** — 그 결측은 이 백필과 무관(별도 티켓 몫)이고 게이트가
> 떠안으면 안 된다. 배당·CSM연속성 등 다른 검사의 공유 `_in_scope`/`_DISPLAY_QUARTERS`는
> 안 건드림.
>
> **6) 게이트 최종 상태**(`validate_data_contract.py`, push 안 함): **RED=12**
> (COMPLETENESS CENSUS, 그 외 전부 0) + YELLOW=83(기존 수준). 12건 전부 설명됨 —
> 예별손해보험(KR0004) 2023.1~3Q 항목3/4 + 카카오페이손해보험(KR1098) 2023.1~3Q
> 항목1/3/4/30 등, 개별 항목의 QoQ ±30% hold 가 남긴 잔여(둘 다 초기 급성장 디지털
> 보험사 — KR1098 자본금은 2023.2Q→4Q 사이 정확히 2배로 튀는데 이는 실제 증자로
> 보이나 이번 세션에서 DART 공시이력으로 독립 확인은 못 했다). **강제로 채우지 않고
> hold 로 남겼다** — 후속 세션에서 개별 확인 후 QoQ 임계값 예외 등재 또는 원문 재확인
> 필요. `scripts/sync_master_xlsx_sheet.py "17BS"` 검증 OK(7,772행×10열 완전일치).
>
> **7) 잔여(후속 세션 몫)**:
>   - **KR1011(IBK연금)**: fitz `find_tables()`가 BS 전체(37줄)를 라벨·값 각 셀 하나에
>     뭉치는데, 라벨 안에 항목구분 개행과 워드랩 개행이 구분 불가하게 섞여 있어
>     `_split_multiline_rows`로도 못 푼다. 텍스트 경로로는 천장 낮음(3칸) — 좌표기반
>     파서 또는 렌더링+비전이 필요.
>   - **KR0080(AIA생명)**: 다수 항목이 감독규정 별표(운용자산/비운용자산 서식)로만
>     존재하고 순수 IFRS 표가 없어 천장 낮음(13칸). 별표 서식에서 "명확한 항목만" 넣는
>     로직(티켓이 KR0100 에 요구한 것과 동일)은 이번 세션에서 미착수.
>   - **`data/_derived/bs_from_disclosure.json` 사이드카 완전성 제한**: KR0004/KR0029/
>     KR0049/KR0050/KR0051/KR1098 6개사는 항목8 정정 재실행 중 `target_quarters_for()`가
>     "이미 마스터에 있는 분기"를 targets 에서 뺐고, 그래서 이 6사의 **PDF 페이지/sha256
>     상세 계보가 sidecar 에서는 축약**돼 있다(값 자체는 `bs_manual_overrides.json`에
>     온전히 남아 있다 — 근거 텍스트 수준 계보는 보존, 페이지번호는 유실). 필요하면
>     `data/disclosure/`를 다시 열어 재확인 가능(공시분기·항목만 알면 페이지 재탐색은
>     빠르다), 정밀 계보가 필요하면 그 6사만 재추출 권장.
>   - KR0075 의 5개 미확정 항목(10·11·13·20·24) 특별계정 재구성 원인 규명.
>   - 비순환검증 KR1000 18건 방향성 없는 불일치 원인.
>   - 서울보증(KR0150) 6칸은 경영공시 PDF 자체 미수집 → `inbox/downloader/
>     20260911T0115Z` 로 이미 별도 발주됨(이 티켓 범위 아님, 확인만).

> 📦 **Status 이력은 `docs/todo_archive_parser_ifrs17.md` 로 이동했다** (2026-09-11, 내용 무수정 — 2026-09-03 (84th pass) 및 그 이전 항목). 세션 시작 시 읽지 않는다; changelog 처럼 특정 과거 결정의 배경이 필요할 때만 연다. **이 Status 는 최신 5개 항목만 유지**하고, 밀려난 항목은 그 파일 헤더 바로 아래에 그대로 잘라 붙인다.

## 🔴 Open — P1

### XLSX-FOLLOWUP — owner xlsx 수동검토 후속 (2026-06-10, CSM 정정은 changelog (c) 반영 완료)

- [ ] **NB배수 분모 '기타' 초회보험료 혼입** — 농협생명/NH손보 568억(26.1Q) 등. 기타 제외 재계산(KB라이프/교보/한화/삼성생명 포함), 삼성 IR 대조, 10~17 range 확인 → 분모 정의 수정 여부 결정. (분모=월납초회 VAL4만 적용은 06-11에 했으나 IR 대조·range 확인 잔여.)
- [ ] **PL 0값 sanity 감사** — 현대해상(생명장기 원수/재보험 6항목 전부 0)·롯데 25.2Q·NH손보·악사·ABL·KDB·라이나·미래에셋·동양·메트라이프. 분류: extraction_miss/legit_absent(→null)/true_zero. (10/10 감사는 06-11 (o) 완료; 잔여는 designer null 렌더링.)
- [ ] **0의 의미론**: 미공시 항목이 0으로 적재되는 설계 교정 검토 — 미공시=null, 공시된 0만 0.
- [ ] (validation 발주됨) **AMORT_ZERO** 룰 — 상각=0 불가. inbox `20260610T1700Z__parser__MULTI__csm_owner_review_fixes.md`.
- [ ] (validation 발주됨) **NB배수 <1.0 하한** (분자붕괴 표면화).
- 미래에셋 '기타' 테이블 CSM: owner — 식별비용 크면 패스 가능 (보류).

---

## 🟠 Open — P2

### KR0075-BS-008 — 카디프생명 2023.4Q 자산·부채총계 0.08%(2,411.95백만원) 차이 원인 (2026-09-12 오케스트레이터)
downloader 실측: DART 제출 이력에 정정공시 없음(2024~2026 감사보고서 3건 전부 정규) → '정정본 반영' 가설 기각. 남은 후보: FS-API 기준(마스터)과 감사보고서 본문 표의 소급재작성/재분류. 로컬에 있는 FY2024 감사보고서 `data/dart/FY2024_Q4/raw/KR0075_비엔피파리바카디프생명보험_20250404003021/20250404003021_00760.xml` 의 **2023.12.31 비교열**이 마스터(자산 2,933,816.215 / 부채 2,687,607.771 백만원)와 FY2023 본문 중 어느 쪽과 같은지 대조하면 판정된다(네트워크 불요). 마스터 값은 FS-API(정본)라 바꾸지 말고, 원인만 `docs/domains/claude-agent-ifrs17.md` 회사 quirk 에 한 줄 기록.

### AIA-456 — KR0080 2025.4Q item4/5/6 을 주석18(4) 측정요소 표 기준으로 교체 ✅ DONE 2026-09-12 (90th pass)
`extract_tier2_aia`에 주석18(4)(원수)·19(3)(재보험) 리더 배선 완료 — item4/5/6 153,100/
30,500/−25,000(산문) → 153,059/30,499/−25,069(주석), item7 잔차 자동 재계산(18,465.203).
부수로 item9-12(재보험)도 신규 등재. 2023.4Q/2024.4Q 는 dry-run 만(미적용, 라우팅 자체가
그 두 분기엔 안 닿음). 상세: TODO 상단 90th pass Status 항목 ①.

### PL-T2 — PL Tier-2 residual gaps (after 2026-06-08 census, changelog (m))

Track with `python scripts/check_pl_reconcile.py`. 큰 systematic 갭은 닫힘(예실차-미공시 generic closure + 에이비엘 leg + 하나 장기). Remaining actionable (non-legit, 2024.2Q+):
- [ ] **KR0004(예별손해=구MG) PL breakdown 전무** (2026-07-30) — CSM waterfall은 3개년 적재+continuity 검증 완료(`inbox/_resolved/20260616T0210Z`)했으나 `PL_breakdown.json`엔 행 0개. `scripts/pl_breakdown/`이 회사별 커스텀 핸들러 구조(`companies.py`)라 신규 소형사 온보딩엔 전용 핸들러 작성 필요 — raw는 이미 3개 dir 확보돼 있음(`data/dart/FY{2023,2024,2025}_Q4/raw/KR0004_엠지손해보험_*`).
- [ ] **동양(2024.x) / 케이디비(2025.x) 재보 CSM상각(item9) / RA(item10)** — 출재 섹션 깊이 박힘, 분기별 노트 구조 상이. Small (재보 sub-slice), per-company/quarter handler. fragile fix 강제 안 함.
- [ ] **하나생명 투자손익(item17)** 2024.4Q/2025.4Q — Tier-1/FS-API lane (parser scope 밖일 수 있음).
- [ ] **교보라이프플래닛 Tier-2 absent** — 디지털 생보, 공시 최소 (likely legit-absent; confirm).
- [ ] **KDB 2023.2Q items 15/17/18** (OLD 양식 매핑 모호 — owner gold 대기) + **KDB 2025.2Q item6 오염 의심** (보정값 미확보, 미래에셋 2025.2Q diff).
- legit (not bugs): 코리안리 자동차(item13) — 재보험사 무자동차(11 c-q). FY2023 holes/WRONG = 사이트 비노출.

### CSM-FOLLOWUP — CSM closing / 마스터 통합 잔여 (2026-06-07 야간, changelog 2026-06-07)

- [ ] **closing 5 SKIP**: 라벨변형(KDB 2023.1Q·미래에셋 2025.2Q/3Q·하나손해 2024.4Q — 상각/이자 변동요인별 라벨) + AIG 2025.4Q(단위오류 null). `viz_build_csm_waterfall.py` STAGE_PATTERNS amortization에 라벨 append.
- [ ] **메트라이프 2025.4Q ~2.2× 점프**(세그 중복 의심) + **KDB 2025.4Q 기초 불연속**(closing 통과, 시퀀스만) — 발행 전 review.
- [ ] **pl_bridge 36F 잔존** = bare-closes 오탐(룰 dual-form 권고) + DB생명/동양 2023(FY2023 상반기 Tier-1 부재) + DB OLD 재보.
- [ ] **crosscheck 9F 잔존** = 코리안리 재보험 item4 scope(상각 1y lag 의심) + 소수.
- [ ] CSM diag → canonical 통합 확인 / 분기 시계열 연속성 재검증(별도 min-opening 적용 후) / KDB·ABL 생명 CSM 미커버 구조 확인.

### TIER2-NEXT — Tier-2 대확장 후속 (2026-06-06 (b), changelog 2026-06-06 (b))

- [ ] **미래에셋 분기 4/12** — rollforward 원-unit → 백만원 emit 핸들러(현재 sanity cap으로 garbage만 차단).
- [ ] **한화손해 13/14 퇴직연금** — owner 배분판단 필요(현재 순수 PAA값). + pre-2025.2Q OLD 핸들러(8분기 blank). + 2025.1Q NB stale carryover.
- [ ] **흥국화재 NEW 2025.4Q/2026.1Q** — 연차 단일표 오작동(4/5=0). 별도 수정.
- [ ] **흥국생명 2026.1Q 더블링** — `_life_comprehensive` dedup이 caption 공백차 중복노트 누적.
- [ ] **롯데 6/12** — 2024.2Q/3Q·2025.3Q/2026.1Q 컴포넌트노트 미발견(deeper probe).
- [ ] 교보 반기/분기 3개월 basis(누적 아님) / 한화생명 2023.2Q(x=1, FY2023 outlier).
- [ ] 아이엠라이프 빌더 핸들러 정식화 (현 override 정상 — KR0076 구성요소별 변동표 CSM열 전용).

검증: `PYTHONIOENCODING=utf-8 PYTHONPATH=. python scripts/build_pl_breakdown.py` → `scripts/_verify_pl_golds.py` → `scripts/_pl_selfcheck.py`.

### Cross-stage parser features (full detail here; root TODO.md keeps 1-line refs)

#### F15 — CSM 시계열 분기 결측 (after 2026-05-29 fixes). 잔여 honest gaps:
- [ ] **삼성생명 2023.1Q** — early-2023 layout, parser miss
- [ ] **미래에셋 2023.1Q / 2023.3Q / 2026.1Q** — early-2023 layouts + 2026.1Q anomaly
- [ ] **동양생명 2025.2Q ~ 2026.1Q** — 잔액(기초/기말) row 0 추출; 재다운로드 검토 `TODO_downloader.md` F15-DL
- [ ] **손보 일부 전사-vs-세그먼트 pick** — reject guard 후 gap 처리; 회사별 disambiguation matrix 필요

#### F16 — Panel 5 흥국생명 민감도 (product-as-rows layout) ✅ DONE 2026-06-14 (changelog 2026-06-14 sensitivity follow-up)
흥국생명 sensitivity 표 별도 양식: 상품(사망/건강/연금)=행, 당기말/전기말 × CSM/손익효과/자본효과=컬럼. 영문 'CSM'+'손익 효과' 라벨. 기존 3-path band parser 미적용 → 행 어긋남.
- [x] product-row × period-band-column 4번째 path 신설 — `_extract_heungkuk_product_rows` + `_is_heungkuk_csm_pl_capital_layout` guard (`viz_build_ifrs17_panels.py`). 흥국 6 시나리오(위험×상승/하락) 정상.
- [x] 다른 회사 회귀 zero check — status {ok:25,unavailable:1,partial:2} 불변, 타 패널 byte-identical, pytest 110
- [ ] Panel 5 caption 갱신 (가능한 회사 명시) — designer 소관

#### F17 — Tier1 + Tier2 LOB 당기순이익 분해 (parser body). 남은 parser gap:
- [ ] **KB / 메리츠 / NH농협** — FY2025 사업보고서가 FS를 별첨 감사보고서로 분리, body XML에 LOB 없음. (별첨 fetch 안 함; 회사별 label 매트릭스 + 본문 내 다른 표 찾기)
- [ ] **DB / 한화 / 흥국** — 회사별 disambiguation (다중후보표 중 picker 오선택)
- [ ] **삼성화재 Tier2** — taxonomy 보장성/물보험/저축성 → 현 파서가 장기/자동차/일반만 기대해 미스 (Taxonomy 참조)
- [ ] **코리안리** — 재보험사 LOB N/A, 영구 SKIP
- [ ] FY2024 LOB — 사업보고서에 존재(감사보고서 X). 필요 시 fetch 대상 분리
- [ ] **In-flight decision (2026-05-31):** Tier2 LOB 9/11 손보 OK. (1) 9/11 commit + 2 gap을 documented exception, (2) 삼성·DB debug, (3) IR-clean 회사만 — 중 하나 결정 대기.

#### F18 — IR factsheet 정형화 (DART↔IR cross-validation 활성화)
Validation 룰 3개 추가됨 (V1 in `TODO_validation.md`); 활성화 대기.
- [ ] **Delivery 계약**: `data/ir/<period>/parsed/<KR>.json` 정형 JSON. Schema: `docs/agents/claude-agent-validation.md` §1.4. 모든 값 억원
- [ ] **출발 cohort 9사**: 메리츠·삼성화재·현대·KB·DB·한화생명·삼성생명·미래에셋·동양
- [ ] IR 미공시 회사 (교보·KDB·외국계·카카오페이손해 등) auto-SKIP 명시
- [ ] 생보 `segment_insurance_income` 키 셋 (보장성/저축성/연금/변액 후보) 확정 — validation V1 참조

---

## 🟡 Open / waiting

- [ ] **코리안리(KR1000) FY2025 CSM basis 결정 (escalated 2026-06-09 (b), inbox `20260609T0200Z`)** — CSM이 두 노트에서 상이(일반모형 FY2024말 8031.5 vs CER/배당칼럼 9046.7). FY2024→2025 경계 +1015억 점프 + 2025.2Q 이자부리 FX 혼입(−147.2억). 단순 re-anchor 불가. **owner/2nd소스 결정:** Option A — 전년 일반모형노트로 통일(2025+ 재추출, 기초 8031.5, 내부일관) / Option B — 2025+ CER basis 수용, 경계를 documented basis-switch exception(파서 무변경). ⚠️ pattern2/배당칼럼 = 삼성화재/현대/한화손보/삼성생명 공유 → 재추출 시 per-company 가드 + full diff. 함께: 2025.2Q FX를 item3 대신 item4 residual로(삼성생명 회귀확인).
- [ ] **validation 회신 대기**: WFY documented exception 9건 등록 + KR0011 해소 확인 + NB<1.0·AMORT_ZERO 룰 구현 확인.
- [ ] **designer 핸드오프**: PL legit-absent null '—' 렌더. 메트라이프 2025.4Q CSM 점프(~2.2x) 재확인. 3사 중 신한이지 '분리공시 미제공' HTML 처리(root TODO).
- [ ] **MLG-1 듀레이션갭** (owner 결정): 100bp 민감도 추출이 첫 단계, 유도식 owner 결정. DART 본문에 갭 서술+만기사다리+100bp 민감도 있으나 듀레이션 숫자·갭 자체 없음. [xref: parser-kics] (듀레이션갭은 K-ICS 금리위험과도 연결되나 CSM/민감도 컨텍스트가 1차라 IFRS17 lane 소관 — default rule per split.)
- [xref: parser-kics] **IFRS-NORMALIZE** — `row_aliases.yaml` 확장이 IFRS17 lane과 공유됨(현 PoC 930/2956 tagged). Full substance + owner = K-ICS lane (`TODO_parser_kics.md`). IFRS17 lane은 row_aliases.yaml 변경 시 동기화만 확인.

---

## Taxonomy note (do not conflate in parser)

LOB axis differs between 손보 CSM decomposition and 손보 P&L decomposition:
- **손보 CSM decomposition** = 보장성 / 물보험 / 저축성 (all within 장기보험; 삼성화재 uses this)
- **손보 P&L decomposition (보험손익)** = 장기 / 자동차 / 일반 (Tier2 in F17)
- 자동차 / 일반 = PAA contracts → no CSM rollforward; P&L only
- 보종별 신계약 CSM multiple은 일부 보험사만 IR 공시 — DART에서 합성 금지

Remove once F17 lands and prompt §2.2 captures it.

---

## ✅ Done (archive)

완결 항목 40+개(IFRS17 lane, 2026-05-24~06-11) — CSM waterfall 블록선택·basis disambiguation, PL breakdown 24항목 전사 sweep, sensitivity heatmap, NB CSM 배수, root 마스터 빌드, `<TE>` parser fix, 외국계 5사 등. 한 줄 상세는 `docs/changelog_parser.md`(당시 `(changelog XX)`로 인덱싱) + git log. (K-ICS-lane done items → `TODO_parser_kics.md`.)


---

## Reading order for parser subagent (IFRS17 lane)

1. This file (`TODO_parser_ifrs17.md`) — open work + done archive + taxonomy note
2. `docs/agents/claude-agent-parser.md` — master prompt + per-domain contract
3. Domain ref: `docs/domains/claude-agent-ifrs17.md` for label variants and company quirks
4. Root `TODO.md` only for cross-stage items (F15/F16/F17/F18) — full detail lives here
5. Sibling lane: `TODO_parser_kics.md` (solvency disclosure) — for [xref] items

Deferred (2026-07-27): `docs/changelog_parser_ifrs17.md` (+ pre-split `changelog_parser.md`) is history — open only when you need a past decision's background; most sessions don't.

## Hand-off to validation

After parser produces normalized CSM/PL masters, validation is invoked per `docs/agents/claude-agent-validation.md` §3 (retry loop, max 5). On RED, validation calls back the parser with the failing rule + suspected source.
