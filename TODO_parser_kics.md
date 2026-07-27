# Insurequant Parser TODO — K-ICS lane (Stage 2)

> Last updated: 2026-07-27 (owner 지시 — `## Status` 섹션 압축, 649→273줄. 최근 4라운드[2026-07-15~16] 원문 보존, 그 이전 18개 완결 라운드는 changelog 참조로 압축) · Stage 2/5 — parser (kics lane)
> Prompt: docs/agents/claude-agent-parser.md · Changelog: docs/changelog_parser_kics.md (pre-split: docs/changelog_parser.md)

Stage 2 — **parser, K-ICS lane**: solvency disclosure extraction. Source = Docling MD; output = `kics_disclosure.json`; validators = `validate_kics_disclosure.py` / RS1–4 / market census. The IFRS17 lane (CSM/PL extraction off DART XML) lives in `TODO_parser_ifrs17.md` and runs as a separate session.

Session start: read this file + `docs/agents/claude-agent-parser.md` + `docs/domains/claude-agent-kics.md`. English where Korean encoding is fragile (see `CLAUDE.md`).

## Status

**2026-07-16 — owner 지시("경과조치 미적용 확실 + 비율 동일하면 하위항목 미러링") 대응, 전사 스윕
241셀 + 기존 스크립트의 데이터오염 버그 발견·정정.**
- **비적용사 정의**: `validate_kics_disclosure.py`의 `_TRANSITION_APPLIERS`(owner FSS 정본 18사) 밖
  전 회사. **미러링 안전기준을 owner 제안(item27·28 둘 다 동일)에서 item14(지급여력기준금액) 단독
  동일로 정교화** — item27/28 둘 다 확인하면 실제로는 놓치는 셀이 많았음: TFI(공통조치, 비적용사도
  다 적용)가 자본 티어(기본자본↔보완자본)만 재배분해도 item28(기본자본비율)이 5~15%p씩 움직이는
  사례가 수두룩(item27은 그대로인데) — 이건 요구자본(15-46) 안전성과 무관한 자본측 재분류일 뿐이라
  item14만 보는 게 더 정확(raw로 다수 확인된 K-ICS 구조: TFI는 요구자본측을 아예 안 건드림).
  `scripts/_probes/survey_item14_gap.py`로 tolerance 보정(247/252 exact-0, 노이즈 상한 0.45, 진짜
  이상치 1건(하나손해 2023.2Q, diff=45)만 정확히 걸러짐 확인).
- **⚠️ 부수 발견 — 기존 스크립트 데이터오염 버그**: 1차 라운드 초반 실행했던
  `backfill_post_transition_when_not_applied.py`(item1/14/27만 보고 판정)가 KB라이프생명 2024.2Q·
  동양생명 2024.1Q에서 item12/13(불인정항목/보완자본재분류)을 잘못 미러링했던 것 발견 — 이미 정확히
  채워져 있던 item2(기본자본)값과 항등식(item2=item4-item12-item13)이 안 맞음. 되돌림
  (`fix_20260716_revert_wrong_item1213_mirror.py`). 해당 스크립트에 경고 docstring 추가, items 1-13은
  더 이상 이 방식으로 안 건드림.
- **신규 영구 스크립트** `fix_20260716_nonapplier_requirement_mirror.py`(idempotent, 매 분기 재실행
  안전) — items 15-26(item14 게이트)·29-35(item17 게이트, 2Q/4Q만)·36-40(item19 게이트, 2Q/4Q만)
  3단 게이팅, items 1-13은 아예 스코프 밖(위 버그 재발 방지).

**결과**: 241셀/20(회사,분기) 신규 채움 — 코리안리(6분기, 3차에서 미룬 "non-display" 건도 이걸로
해소)·동양생명(7분기, 3차 잔여분 포함)·DB손해보험(2분기, 신규)·한화생명/삼성생명(item24-26, 15-23은
1-2차에서 이미 완료였는데 24-26은 놓쳤던 잔여). continuity break 62→**34셀/10→5쌍**(잔여 5쌍은 전부
18사 적용사 관련 raw확인필요·documented exception, 이 스윕 스코프 밖). core RED 12(무관 기존건, 회귀
0). `pytest` 110 passed. xlsx 재생성 완료.

---

**2026-07-15(3차) — validation이 신설 게이트(`_post_transition_parent_census`, inbox `20260715T0835Z`)로
적발한 continuity-break(적용후 공시하다 특정 분기만 결측) 14쌍/96셀 처리, 62셀/10쌍 잔존.**
- **완전 해소(raw 재대조, 전부 선택경과조치 완전 미적용)**: 삼성생명(KR0069) 2025.1Q, 동양생명(KR0087)
  2024.2Q·2024.4Q·2025.1Q·2025.2Q(연쇄 노출분 포함) — 16-23후=전 미러링.
- **부분 해소**: 하나생명(KR0097) 2024.4Q — raw가 표준양식 아닌 "지급여력 및 건전성감독기준
  재무상태표"(감사보고서 첨부, 단위 천원) 스타일임을 확인, 18-23 채움. **item17후=1757.32(기존값)가
  이 페이지 값(2001.90)과 불일치·출처 불명** — item16과 함께 보류(validation에 원 출처 문의).
  흥국생명(KR0071) 2024.4Q — **image-only PDF, 비전으로 스캔페이지 직접 판독**(8차 changelog 선례
  재현). item17/18/19/20/21 disjoint-derive로 채움, **item22/23가 두 경과조치 표에서 서로 달라
  R4 역산도 헤드라인과 ~2,240 차이로 재현 안 됨** — 진짜 다중결합 불명, item15/16/22/23 보류.
- **손 안 댐**: ticket이 명시한 "non-display/비차단"(코리안리 3분기·처브 2024.3Q) + 기존
  documented exception(IBK연금 2023.2Q, 5차 라운드 `_AFTER_SUBRISK_NOT_DISCLOSED`).
- **미확인 잔여**: 하나손해 2023.2Q·하나생명 2023.2Q(별개 분기)·악사손해 2024.3Q — 다음 라운드.

재검증: RED 12(무관 기존건, 회귀 0), `pytest` 110 passed. inbox `20260715T0835Z`에 상세 회신
(`status: answered`). 스크립트: `scripts/fix_20260715_round3_continuity_gaps.py` +
`fix_20260715_round3b_dongyang_2025q2.py`.

---

**2026-07-15(2차) — owner 지시로 "2차(과거분기 유사갭)" 이어서 처리, 완료 + 2026-07-12(2차) 오판정
정정.** 한화생명(KR0068) 2024.3Q·2025.2Q·2025.3Q, 농협생명(KR0104) 2023.1Q·2023.2Q raw 재대조:
- 한화생명 3개 분기: 전부 선택경과조치 완전 미적용(raw 명시, 1차와 동일 패턴) → 15-23후=전 미러링.
- 농협생명 2개 분기: ②+③ 동시적용, 1차와 동일 비중첩 구조로 item17/19 개별신뢰 + R4 역산 검증. 부수로
  농협 2023.2Q 시장하위(36-40후)도 해소(1차 패턴과 동일).
- **⚠️ 오판정 정정**: 농협생명 2023.1Q item17후가 `10,899.56`("다중 경과조치 결합공식 불명", 2026-07-12
  2차)으로 저장돼 있었는데, raw `[지급여력비율총괄]`(지급여력기준금액후=22,802 직접공시) 앵커 + R4
  역산이 `8,979.7`로 수렴(원 ②표 값과 일치) — 10,899.56은 어떤 raw 표·항등식도 만족 못 함을 확인,
  **오류로 정정**. 함께 None 처리됐던 33/34/35(해지·사업비·대재해)도 raw dash(=0)로 복원.
  (`scripts/_probes/verify_r4_kr0104_2023q1.py`)

50셀 추가+정정. 재검증 RED 12(무관 기존건, 회귀 0), census 결측 4(회귀 0, 신규노출분도 해소).
`pytest` 110 passed. inbox `20260715T0801Z`에 2차 회신 추가. **owner가 언급한 과거분기 갭은 이 5건이
전부, 2차도 종결.**

---

**2026-07-15 — owner ticket `20260715T0801Z`: 2026.1Q 요구자본(15-23) 적용후 5개사 결측 → raw 재대조로
46셀 채움, 하나생명 기존 오류 4셀 정정.** 신규 로드된 FY2026_Q1에 대해 `fill_post_transition_to_
disclosure.py`/`backfill_post_transition_when_not_applied.py`가 아직 재실행 안 된 것이 근본원인
(과거 분기는 이미 처리됨, 2026.1Q는 처음). 5개사(한화생명·교보생명·하나생명·롯데손해·농협생명)
raw PDF 직접 재대조:
- 한화생명: 선택경과조치 완전 미적용(raw 명시 확인) → 15-23후=전 미러링.
- 교보·농협: ②(장수)+③(주식/금리) 동시적용이지만 두 표가 서로 다른 항목만 건드리는 비중첩 구조 확인
  (상대방 항목 불변을 각 표가 자체 교차확인) → item17=②표/item19=③표 개별신뢰, item16=derive.
  R4 공식으로 역산해 각사 헤드라인 item14와 ±0.5억 이내 재현 확인(우연 아님).
- **하나생명: 기존 item14/15/27/28후가 ②표 단독(isolated) 값으로 잘못 저장돼 있던 것 발견·정정**
  (진짜 헤드라인=`[지급여력비율총괄]` 5,558억인데 저장값은 5,769.44억=②만 적용했을 때 값이었음).
- 롯데손해: ②만 단독 적용(raw 명시) → ②표가 곧 결합 정답, 경합 없음.
- 부수: 농협생명 item19 채우자 census가 시장하위(36-40후) 결측도 지적 → 같은 raw(③표)로 마저 해소,
  MARKET_M 공식 역산이 item19=10865.69 소수점까지 정확 재현.

재검증: RED 12(전부 무관 기존 건, 회귀 0), 적용후 census 결측 5→4(농협 해소, 잔여 4=예별손해
2023.1-3Q·IBK 2023.2Q 기존 documented). `pytest tests/unit/` 110 passed. xlsx 재생성 완료. inbox
`20260715T0801Z`에 상세 회신(`status: answered`). **2차(과거분기 유사갭)는 위 2026-07-15(2차) 항목에서
완료.**

---

**완결 이력 (2026-07-12, 6개 라운드) — 상세는 `docs/changelog_parser_kics.md` 해당 날짜:**
- (6차) IBK 재정정(공통TFI 합산 누락)+예별손해 3분기 동형 정정. 전수재조정 119건 시도는 포맷 불균질로 폐기(커밋 안 함).
- (5차) KR1011 2023.2Q 다중경과조치(②+③) 값 혼합→분산효과 음수 정정. item16/17/19후 결합불명 판정, None+`_AFTER_SUBRISK_NOT_DISCLOSED`.
- (4차) 요구자본 census 322셀 결측 처리(CARRY206+DERIVE96+EXTRACT20), 322→2(raw부재 영구잔존).
- (3차) items4/12/13 적용후 결측=구조적 미공시(raw 자체 없음) 확인, designer에 표시방식 재고 권장 회신.
- (2차) KR0104 fill오류 발견·원복, "다중경과조치 결합공식 불명" 최초 판정(⚠️ **2026-07-15(2차)에서 오판정으로 재정정됨** — 10,899.56은 오류, 8,979.7이 정답).
- (무번호) validation 재검 잔여10셀 중 9셀 raw 재대조 해소, 추출갭 10→3.

**완결 이력 (2026-07-11, 4개 라운드) — 상세는 `docs/changelog_parser_kics.md` 해당 날짜:**
- (4차) owner 재지시로 세부위험 갭 계속 착수, post_transition/market 스크립트 실버그 6개 발견·수정. 추출갭 52→10.
- (3차) owner "진짜 다 끝났냐" 재확인 요청, fill_subitems 실버그 4개 발견·수정(SKIP 3건 GREEN 전환). 추출갭 52→40.
- (2차) owner ticket `20260703T1138Z` Tier C(금리민감도) 재검증, 실데이터 오염 2건(푸본현대·예별손해) 수정. RS1/RS2/RS4 RED=0.
- (무번호) Tier B 세부위험 후컬럼: 근본버그 4개+회귀 3개 수정. 추출갭 206→52.

**완결 이력 (2026-07-08, 3개 라운드) — 상세는 `docs/changelog_parser_kics.md` 해당 날짜:**
- (3차) 세션 재개, 라이브 게이트 전수 트리아지: KR0051 `19_market` 단위힌트 버그 수정. RED 14→13.
  ⚠️ 별건(당시 미해결, 이후 해소): `scripts/` 다수 파일+xlsx가 git 미추적이었던 문제 — 현재는 추적됨(git 확인).
- (2차) 적용후 R1 가용자본(item1=item2+item3) 항등식 3건 해소(농협생명·롯데손해·하나생명), raw 원인 3건 전부 다름.
- (ROUND2 반려 대응) ③표(주식·금리위험) 미반영 근본수정 — 이전 라운드가 ②표만 고치고 "완료" 보고했다 반려됨. R5/R6 45+6→0, mmult 4→1, COPY 7→2.

**완결 이력 (2026-07-07, 5개 라운드) — 상세는 `docs/changelog_parser_kics.md` 해당 날짜(9차 관련은 후속 3항목 포함):**
- (9차) 적용후 전체룰 재검증 대응, 근본버그 4개 수정. `transition_ratio_after_capture` RED 39→8, R8 147→0 완전해소.
- (9차 후속) item12=item1 셀밀림 154셀 근본원인 확정(라벨 fuzzy-매칭 충돌), 95셀 수정(154→63).
- (9차 후속2/3) item12 잔여 63→0 완료(owner "0 될 때까지 멈추지 마라").
- (8차, downloader) "원본 결측" 판정이 fitz 텍스트추출 실패를 오해석한 것이었음 정정 — 흥국화재·흥국생명 비전으로 직접 판독, item2/3/14/27/28후 복원. 상세는 `docs/changelog_downloader.md` 2026-07-07.
- (7차) ⚠️ 8차 정정으로 무효화된 결론(원본 정상 파일이었음) — 기록만 유지.
- (6차) 악사손해 2024.3Q item27/28 복구, 4→2셀.
- (무번호) FSS 정본으로 선택경과조치 적용사=18개사 확정(`_TRANSITION_APPLIERS`), item28 검사+AMT_MISMATCH 룰 추가.

**2026-06-14 — REFACTOR closure + market 36-46 fitz root-cause + inbox 드레인(4개 항목)**: pdfplumber
localizer 무음실패 root-cause 확인, fitz 재추출로 RED 52→42→23→21. 상세는 `docs/changelog_parser_kics.md`
2026-06-14(4항목).

**K-ICS lane 성숙도**: disclosure+rate-sensitivity+market-subitem 마스터 전부 구축(`kics_disclosure.json`
조립, xlsx 재생성 완료). 게이트는 2026-06-11 RED=0 도달 이력 — 현재 상태는 이 파일 최상단 최신 라운드 참고
(2026-07-16 기준 core RED 12, 전부 documented).

---

## 🔴 Open — P1

### TRANS-18 — 경과조치 적용후 정본 18사, `transition_ratio_after_capture` 12셀 최종 (2026-07-07 마감)

정본 = FSS 2023-03-20 보도자료 붙임-1 → elective 경과조치 실제 적용 **18사**:
- 생보12: 에이비엘(KR0070)·흥국생명(0071)·케이디비생명(0072)·교보생명(0073)·아이엠라이프(0076)·DB생명(0082)·푸본현대(0083)·하나생명(0097)·처브라이프(0100)·교보라이프플래닛(1010)·IBK연금(1011)·농협생명(0104)
- 손보6: 악사손해(0049)·한화손해(0002)·롯데손해(0003)·예별손해(0004)·흥국화재(0005)·NH농협손해(0032)
- **나머지 전사(코리안리·메리츠·삼성생명·한화생명·신한라이프·KB라이프·동양생명 등) = 공통(TFI)만 → 적용후=적용전이 정상, 건드리지 말 것.**

**최종 12셀 = 전부 "더 파싱해도 안 바뀜"**(라이브 게이트 `transition_ratio_after_capture` 기준):
- **원천 미공시 7셀**(raw에 표 자체 없음): 흥국화재 2024.4Q(2)·악사손해 2024.3Q(2)·에이비엘 2025.3Q(1)·흥국생명 2024.4Q(1)·푸본현대 2023.1Q(1).
- **게이트 마진 오탐 5셀**(COPY, 소액/음수인접사의 진짜 개선폭을 반올림복사로 오판): 예별손해 3·롯데손해 1·IBK연금 1 → **validation 마진로직 재검토**(파서가 데이터 더 고쳐도 안 바뀜).
- 흥국화재·흥국생명 2024.4Q = raw 오염(정기경영공시서 아닌 사업/감사보고서 오수집) → downloader 발주됨.
- rule_8_post 3건(흥국생명·푸본현대·에이비엘) = item2후를 None으로 정직 유지한 셀에서 검증기 폴백버그 노출 → validation 로직 이슈(파서 소관 아님).

날짜별 라운드 상세(139→90→42→13→12) + 18사 확정 왕복 이력 → `docs/changelog_parser_kics.md` 2026-07-07.


### LOCALIZER-FITZ — 시장위험 localizer pdfplumber EOF 무음실패 → fitz fallback (2026-06-14)

**DONE**: `extract_market_section_pages.py`에 pdfplumber→fitz fallback 추가(EOF-PDF DB손해 24.4Q·NH 25.4Q ERR→OK). 상세 → changelog.
- [ ] (validation 측) ERR/NO_SIGNAL을 'TOOLING_FAIL' census 버킷으로 분리 — localizer 안착 후 wire-up(inbox/validation 합의). parser는 선결조건 해소.


### GOLD-CHAIN — review-loop 영속화 정합 + backfill 스크립트 체인 편입 (2026-06-20, inbox 0811Z)

owner xlsx fill·내 backfill이 rebuild에서 살아남는지 점검 → 2대 사각 (메모리 [[reference_kics_gold_reviewloop]]).
- [x] **DONE 2026-06-20**: owner image-OCR fill(카카오 KR1098 2023.4Q/2024.4Q·AIA KR0080·한화 KR0068 it37)을
  durable gold(`data/_gold/user_kics_cells.json`)에 영속화(+90셀, `append_owner_image_fills_to_gold.py`) +
  stale-gold 1건(한화 it37 45096.51→58590.96, owner 수정 클로버 차단) `reconcile_gold_to_xlsx.py`로 정합.
- [ ] **backfill 스크립트 rebuild 체인 편입**: `backfill_life_subrisk_positional.py`·`_from_pdf.py`·시장하위
  backfill이 `fill_*→apply_user_kics_gold→recalc` 체인 밖 → from-scratch 재빌드 시 미재현(+155 life-subrisk 등 소실).
  체인 러너(or 문서)에 `fill_market_*` 다음·`apply_user_kics_gold` 앞 단계로 편입. 현재는 커밋에만 존재.
- [ ] **gold git 추적 결정**: `user_kics_cells.json`은 현재 untracked(머신-로컬) — 다른 세션/머신 rebuild 시
  owner fill 소실. 추적 여부 owner 확인(민감정보 아님, 추적 권장).

### DEDUP — kics_disclosure 중복 행 slice (발견 2026-06-12, changelog (s))

`(원보험사코드, 공시분기, 항목번호, 항목명)` 중복 **94키 (값 상이 65키)** — 예: KR0001 2023.1Q item26 ×13, item12 값 {257, 32, 68431}. 과거 fill 누적 잔재. fill의 (code,item,name) index와 validator 입력이 어느 행을 읽느냐에 따라 흔들리는 잠복 리스크.
- [ ] dedup 스크립트: 같은 키 그룹 → 정답 판별(MD 재추출 대조 우선, 불능 시 최빈/최신) → 1행만 유지.
- [ ] fill_period에 신규-행 삽입 전 동일키 존재 가드 추가(이름 변형이 아닌 진짜 중복 차단).
- [ ] validation에 룰 입력의 중복 반응(first/last/any) 질의함 — inbox 20260612T1100Z 4).
- NOTE: FY2023_Q1 `--refresh` dry-run에서 메리츠 item12 257→68431 오매칭 신호도 관찰 — dedup 후 해당 라벨 매칭 재점검 (refresh는 그 전까지 금지).

### NEW-1 — 시장위험 하위(item36-40) 추가 backfill (inbox 20260612T0900Z 신규-1 + 20260611T2200Z systemic)

소스 MD에 5종 세부표(자산집중위험 행) 있는데 JSON 미적재인 (사,분기). validator는 "전사적 미파싱"으로 승격(19_market SKIP→RED). 분절표(`<!-- image -->`) 봉합 + 라벨변형(`(\d\.)?\s*(금리|주식|부동산|외환|자산집중)\s*위험(액)?`) + 값셀 탐색(방법 텍스트 다음 숫자).
- [ ] **224건, 36개사, 전 13분기** 36-40 재추출. gold anchor: 하나손해 2025.4Q(시장 76,839 / 금리 30,358 / 주식 62,491 / 부동산 2,643 / 외환 12,483 / 자산집중 5,251 백만원) + 삼성생명 2025.4Q. 도구 `fill_market_subs_from_pdf.py`(words-coordinate 전략) 또는 MD 분단표 합치기. **게이트: 19_market 행렬합 rel<2%** 통과분만 적재. 생보도 동일 스캔 후 일괄.
- [ ] 진짜 미공시 (사,분기)는 raw 표 부재 명시 회신 → validation `MARKET_BREAKDOWN_EXEMPT` 등록.
- [ ] **2026.1Q 항목 절단 backfill**: 30개사가 1-28만, 29-46 전무(8_life 29-35 + 시장위험 36-46) → 29-46 backfill.
- [ ] **census 미싱셀 28건**(MD parsed인데 JSON 추출 누락): 미래에셋 7분기·코리안리 6분기·동양·하나생명 등 + 2026.1Q 6사(한화손해·롯데손해·삼성화재·하나손해·미래에셋·동양). 명단 inbox 20260611T2200Z.

### NEW-2 — 생보 경과조치 적용후 요구자본 20건 → 2026-07-07(9차)로 18사 일괄 적재, 상위호환 완결. 잔여 3사(예별·흥국화재·흥국생명)는 TRANS-AFTER-9 참조.


### TRANS-AFTER-9 — 적용후 잔여 3사 + item12 셀밀림 (2026-07-07, 9차 후속)

9차(`fill_post_transition_to_disclosure.py` 4버그) + 후속 라운드로 R1 53→0(TAC 도출 `_extract_tac_amount` 신설)·mmult 5→4·**item12 셀밀림 154→0**(labels_compatible 대칭가드 + 퍼센트파싱 + 8개 근본버그 + raw 수기 2건). 완결 상세 전부 → changelog 9차. 잔여 open 2:
- [ ] **R5/R6/mmult 51+4건, 예별손해(KR0004)·흥국화재(KR0005)·흥국생명(KR0071)**: 3사가 ③(주식·금리) 또는 시장위험 36-40 세부도 동시 적용인데 이 스크립트 스코프 밖 → 총괄표 파싱 실패 시 부분치 폴백으로 항등식 안 닫힘. ③표 파싱 또는 36-40후 추출(F12/NEW-1 계열) 필요, validation에 스코프 확장 발주(`inbox/parser/20260707T0600Z`).
- [ ] **DEDUP 선행**: 라이브 `--refresh --all-periods`는 고정밀 파생값 손실 부작용 → DEDUP(94중복키) 해소 전까지 전면 실행 금지. scratch-리다이렉트+방어적 병합이 표준 우회로.


### GOLD-SCAN — owner gold 필요 (이미지 스캔 PDF, 2026-06-12 확정)

자사+협회 모두 이미지 스캔 — 텍스트 추출 불가, KB(KR0010) xlsx-gold 전례 경로 권고:
- [ ] KR0079 미래에셋생명 — 전 구간 (기존 KICS-IMG 항목과 동일 코호트).
- [ ] KR0080 에이아이에이생명 — 2024.4Q~2026.1Q (2023.1Q~2024.3Q는 텍스트 있어 적재 완료, 신규 편입).
- [ ] KR0087 동양생명 — 2026.1Q만.
- [ ] KR0049 악사손해 — 2026.1Q 세부표 페이지(p16)만 이미지 → 코어 5행 외 잔여 항목 (게이트 잔여 RED 4건).

---

## 🟠 Open — P2

### MARKET-P2 — 시장위험 Phase-2 잔여 (after 2026-06-09 (e), 정당/후속)

- [ ] **19_market 구조적 SKIP ~100** (삼성화재 전분기·삼성생명·현대해상·한화생명): PDF에도 하위5종 비공시 = 정당 SKIP, RED 아님 (NEW-1과 분류 확정 필요).
- [ ] **36_irr Q1/Q3 ~85**: 분기보고서에 시나리오표 원천부재 = 구조적 SKIP.
- [ ] **IRR 직접형/granular 15** (KR0097 하나생명·KR1010 교보라이프·KR0051 신한이지): derived≠item36 → 직접공시 시나리오위험액 별도 schema 필요(저장 보류, SKIP 유지).
- [ ] **PDF 레이아웃 미스** (하나손해 2024.x 등): interleaved/grouped/concat fallback에 words-coordinate 전략 추가.
- [ ] **KB손해 image-only 4분기**: 스캔본 → OCR 경로.

### FY2026Q1 — K-ICS PDF→MD docling 잔여 (inbox 20260612T0900Z)

- [ ] **FY2026_Q1 K-ICS PDF→MD docling** (`data/disclosure/FY2026_Q1/raw/` → md_inbox; 일부 대형 PDF std::bad_alloc) → 금리민감도·시장하위 추출기 재실행으로 흡수.

### F12 — K-ICS 시장위험 하위위험액 전체 파싱 (parser side)

Cross-stage feature (root `TODO.md` keeps a 1-line ref; full detail here). Parser + validation cross-stage. 화면 노출 X, 데이터 신뢰용. Validation half = V3 in `TODO_validation.md`.
- [ ] 시장위험 하위 5개 + 분산효과 row 추출 추가
- [ ] 금리위험액 (+5쇼크 순자산 민감도 = 듀레이션갭) display-ready 필드 분리
- [ ] 출력 schema에 `market_risk_breakdown` 신설 → validation R11 sqrt 정합성 룰의 입력

---

## 🟡 Open / waiting

- [ ] **validation: RS1–4 룰 발주 대기** (스펙 §5). 마스터 ready 회신 = `inbox/validation/20260610T0830Z__parser__ALL__rate_sensitivity_master.md`. (RS1-4는 통과했으나 정식 룰 구현 확인 잔여.)
- [ ] **MLG-2 시장위험 분해** (owner 결정): PL-Tier2급 사별 핸들러 + 금리 유도규칙 owner 결정 필요. R11은 금리 확정 후. [xref: parser-ifrs17] (PL-Tier2급 핸들러 패턴은 IFRS17 lane이 owner; 본 항목은 시장위험액이 1차 데이터라 K-ICS lane 소관.)
- [ ] **IFRS-NORMALIZE** — 23-co full normalization: `row_aliases.yaml` 확장(현 PoC 930/2956 tagged) + K-ICS sensitivity 잔여 empty FY2025_Q4 생보사 normalize. (K-ICS sensitivity normalization이 1차; IFRS17 lane도 row_aliases.yaml 공유하므로 [xref: parser-ifrs17].)
- [ ] **KICS-IMG** — image-only PDF manual OCR: KR0010 KB손해(rule 2 ×2)·KR0079 미래에셋생명·KR0080. 정책: parser는 image-only 만나면 escalate, OCR 즉흥 금지 (`claude-agent-parser.md` §2.1). (KR0010은 2026-06-11 (r)에 owner gold로 RED=0 달성.)
- [ ] **REFACTOR-3 slice2 — PARKED (owner-gated, 2026-06-14)**: `make_quarter_column_picker` / `_canonicalize_table_label` 등 파라미터화 로직을 `company_handlers.REGISTRY[code]` dict-dispatch로 흡수. **착수 조건 = 진짜 KR-keyed 노브(column-picker quirk·값 reconcile 등)가 실제 발생할 때.** 현재 `src/`에 `if code==KR` 분기 0개(확인) → 지금 추출은 over-engineering(정적 config 아닌 predicate 로직). slice1(레지스트리)+DEDUP-1/2+GOLDEN-E2E(csm)는 완료 → changelog_parser_kics 2026-06-14. 원 스레드 inbox `_resolved/20260613T0200Z__owner__ALL__parser_refactor.md` (resolved).

---

## ✅ Done (archive)

One line per finished item. Full story in `docs/changelog_parser.md` + git. (Pre-split combined archive; K-ICS-lane items only — IFRS17-lane done items moved to `TODO_parser_ifrs17.md`.)

- K-ICS 금리민감도 추출 — `extract_kics_rate_sensitivity.py` → `kics_rate_sensitivity.json` 423행, RS1/RS2 pass — 2026-06-10 (changelog 2026-06-10)
- BNP(KR0075)/코리안리(KR1000) FY2025 재파싱 — docling v4 페이지선택 수정, +12행, RS4 hole=0 — 2026-06-10 (changelog (b))
- KB손해(KR0010) owner gold cell 적재 — `apply_kr0010_gold.py`, RED=0 최초 달성 — 2026-06-11 (changelog (r))
- 값_적용후 정합 2건 + recalc 분모버그 — 농협생명·삼성화재 + den14=post14 — 2026-06-11 (changelog (p))
- 2026.1Q 36/39사 적재 + MG/AIA 신규 편입 + 파서 버그 2건 — `append_kics_detail_from_pdf.py`·`seed_new_companies.py` — 2026-06-12 (changelog (s))
- 시장위험 하위분해 적재 (items 36–46) — `fill_market_subitems_to_disclosure.py`, +1,449행 — 2026-06-09 (changelog (c))
- 시장위험 커버리지 census + Phase-2 PDF 추출 — 36-46 복구 +150행, RED 0 — 2026-06-09 (changelog (d)·(e))
- K-ICS parser: split-table + row scope + Q4 reparse + KR0069/KR0097 fixes — 2026-05-24 (changelog archive)
- K-ICS RED reduction passes (419→311→217) + sub-items 29-35 + 값_적용후 historical — 2026-05-24/25 (changelog archive)
- Unit-hint mismatch auto-detect — 23 insurer-quarter latent bugs, 56 post 보정 — done (UNIT-HINT)
- B5-APPENDIX K-ICS sensitivity appendix headings + multi-period batch — 2026-05-25 (B5-APPENDIX)
- Pipeline foundation (Docling PDF→MD, 협회 파서 1차, kics_disclosure.json) — 2026-04-25~28 (changelog archive)

---

## Reading order for parser subagent (K-ICS lane)

1. This file (`TODO_parser_kics.md`) — open work + done archive
2. `docs/changelog_parser.md` — history (pre-split combined)
3. `docs/agents/claude-agent-parser.md` — master prompt + per-domain contract
4. Domain ref: `docs/domains/claude-agent-kics.md` for label variants and company quirks
5. Root `TODO.md` only for cross-stage items (F12) — full detail lives here
6. Sibling lane: `TODO_parser_ifrs17.md` (CSM/PL extraction) — for [xref] items

## Hand-off to validation

After parser produces normalized `kics_disclosure.json`, validation is invoked per `docs/agents/claude-agent-validation.md` §3 (retry loop, max 5). On RED, validation calls back the parser with the failing rule + suspected source.
