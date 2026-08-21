# Insurequant Parser TODO — K-ICS lane (Stage 2)

> Last updated: 2026-08-21(7회차) — 흥국생명(KR0071) 2024.4Q "wrong document" 3연속 오판정 정정,
> POST_TRANSITION_PARENT_MISSING 4건 종결, 상세는 최상단 항목 참조 · Stage 2/5 — parser (kics lane)
> Prompt: docs/agents/claude-agent-parser.md · Changelog: docs/changelog_parser_kics.md (pre-split: docs/changelog_parser.md)

Stage 2 — **parser, K-ICS lane**: solvency disclosure extraction. Source = Docling MD; output = `kics_disclosure.json`; validators = `validate_kics_disclosure.py` / RS1–4 / market census. The IFRS17 lane (CSM/PL extraction off DART XML) lives in `TODO_parser_ifrs17.md` and runs as a separate session.

Session start: read this file + `docs/agents/claude-agent-parser.md` + `docs/domains/claude-agent-kics.md`. English where Korean encoding is fragile (see `CLAUDE.md`).

## Status

**2026-08-21(7회차) — inbox `20260821T1720Z`(orchestrator) 드레인: 흥국생명(KR0071) 2024.4Q
`POST_TRANSITION_PARENT_MISSING` 4건(item15/16/22/23후) 종결.**

- **근본원인**: raw(`data/disclosure/FY2024_Q4/raw/KR0071_흥국생명보험.pdf`, md5 `25ee539046c51cf5`,
  538p)가 downloader→orchestrator 순으로 "DART 사업보고서(오문서)"로 3연속 오판정됐다 — 근거는
  fitz `"경과조치"` 전페이지 0회. 실제로는 **p1-112가 전부 스캔 이미지**(K-ICS 본문)이고 텍스트가
  잡히는 p113-450은 재무제표·감사보고서라 그 키워드가 원래 없다. 페이지당 533자(text-layer 존재)인데도
  본문이 이미지인 사례라 "텍스트레이어 有=키워드로 판정 가능"이 깨진다. 같은 함정을 흥국화재(KR0005)에서
  이미 겪고 240dpi 렌더링으로 풀었던 교훈이 이 회사엔 적용 안 됐던 것 — 세 명이 순서대로 반복.
- **해결**: `get_pixmap(dpi=260)`으로 p44/47/49/50/51 직접 렌더링·육안판독(fitz 텍스트 0자 재확인).
  이 회사는 TIR(신규보험위험=장수·사업비·해지·대재해, p50)·TER(주식위험, p51) 둘 다 신청한
  다중경과조치사라 결합값이 필요했다 — 기존 검증된 알고리즘(`scripts/rebuild_combined_transition_after.py`,
  leaf는 "누가 줄였는지"로 합치고 부모는 R4/R7/MARKET_M 재계산, 기준금액은 헤드라인(p44: 16,987억)에
  앵커, 법인세는 잔차, `AFFILIATE={"KR0071":"KR0005"}`로 item23=관계회사 흥국화재 item14 환산치)를
  import로 재사용하고, 이 스크립트의 `main()`이 놓치던 타겟(값_적용후가 "틀림"이 아니라 "아예 없음")만
  새로 짠 상주 스크립트 `scripts/fix_20260821_kr0071_2024q4_post_combine.py`로 채웠다. `scan_occurrences()`
  (fitz 텍스트 스캔)는 스캔본이라 0건 반환 확인 후, p50/p51에서 직접 읽은 값을 `occ` 딕셔너리에 수기
  입력 — 그 뒤 R4/R7/MARKET_M 재계산·단조성·affiliate 비율(13분기 중앙값 0.40061 vs 이 분기 0.40062,
  diff 0.00001)·법인세잔차 검증은 전부 기존 코드 로직 그대로 통과. 교차검증으로 item14/17/19/27/28/
  36-40후를 독립 재계산했더니 기존 저장값과 전부 정확히 일치 확인(그래서 그 항목들은 안 씀, 4셀만 UPSERT).
  identity 검산: item15후(14747.27)−item22후(3360.12)+item23후(5599.84)=16987.00=item14후(diff 0).
- **`_POST_PARENT_NOT_DISCLOSED` 등재 해제**: validation이 같은 날 이미 해제해 둔 상태였음(2026-08-21,
  "image-only PDF" 사유가 거짓으로 확인) — 이번 라운드는 그 자리를 실값으로 채운 것.
- **게이트**: `validate_data_contract.py` RED **12 → 8**(흥국생명 4건 전부 소멸, 잔존 8건은
  신한라이프/교보생명 `KICS_36_irr`+`TRANSITION_AFTER_IRR_MISMATCH` — owner 결정 대기, 이 라운드 밖).
  `validate_kics_disclosure.py` RED=6 불변(다른 룰셋, 무관). golden 배터리 123 passed, drift 0.
  `sh .githooks/pre-push` 4분2초 — `RED=8 · inbox 위반=0 · offline tests=pass → BLOCKED`
  (잔존 8건이 스코프 밖이라 여전히 BLOCKED, 이 티켓 인수조건은 달성).
- **부수 발견(안 건드림)**: KR0005(흥국화재) 2024.4Q item23 값_적용후=null(다른 전 분기는 0으로 미러) —
  RED는 아님(review 등급), spawn_task로 후속 플래그만 남김.
- inbox: `20260821T1720Z` → answered(원문 캡처 답변 첨부). `python scripts/check_inbox_hygiene.py` 위반 0.

---

**2026-08-21(6회차) — inbox `20260821T1600Z`(orchestrator)·`20260821T1620Z`(validation) 드레인:
`INTERNAL_MODEL_36IRR_EXEMPT` 반증(owner 승인분 5건 전건 해제, `20260614T0930Z` 등재 사유가 raw
대조로 거짓 확인)으로 드러난 RED 처리.**

- **A. 36_irr 5건**(교보생명 2025.2Q · 신한라이프 2024.2Q/2024.4Q/2025.2Q/2025.4Q) — items 41-46(금리위험
  순자산가치 6-시나리오)을 raw에서 "당기" 컬럼으로 직접 로드(30셀 신규, `scripts/fix_20260821_
  36irr_and_hana_post.py`). 컬럼오독 함정 실측: 오케스트레이터 원 티켓의 교보 수치(456,919)는 실제로
  전기(비교)열이었음(정정, p21 당기=459,988이 맞음) — 세션 자체는 라벨을 직접 대조해 이 함정을
  피했다. **여전히 GREEN 아님**: 게이트 36_irr derive식(sqrt(max(상승,하락)²+max(평탄,경사)²)+평균회귀)
  으로 재현하면 공시 금리위험액과 5.25~25.62% 벗어남(`run_validation()` 직접 호출로 확인, 값 안
  맞춤). 유력 가설(KR0094 raw p144 주2: 2024년부터 표 모수가 "금리노출 자산부채 한정"으로 변경)은
  미확정 — owner 결정 대기(새 면제 또는 허용오차 조정), **새 면제 등록 안 함**. 완전성 확보 부수효과로
  `TRANSITION_AFTER_IRR_MISMATCH` 4건(신한24.2Q 제외, display-scope)도 동일 근본원인으로 새로 노출(회귀
  아님 — 이전엔 41-46후 결측이라 미판정/SKIP이었을 뿐 통과였던 적 없음).
- **B. 하나생명(KR0097) 2024.4Q item16/17후 — 종결.** raw p281 `[지급여력기준금액]` 표(천원, 적용전/후
  두 컬럼 명문)로 item16후 신설(1613.67) + item17후 정정(1757.32→2001.90, 기존값은 phase-in 10% 역산
  파생값으로 추정). 검산 2001.90+0+2003.45+1548.78+364.85−1613.67=4305.31=item15후 정확히 닫힘.
  `POST_TRANSITION_PARENT_MISSING`(하나생명분) RED 종결.
- **C. 흥국화재(KR0005) 2024.4Q — 종결(코디네이터 중간 재수집 지시).** 세션 도중 downloader가 올바른
  정기경영공시(96p, **데이터 표 전부 래스터 이미지** — fitz "경과조치" 0회는 정상, 원 wrong-document는
  `data/_archive/20260821T044328Z/`로 격리)를 새로 받아옴. items 36-40후(개별 leaf)는 이미 정확했고,
  문제는 item19후(결합) — 저장값(3860.81)이 회사가 공시하는 4개 단일축 표 중 ③(주식위험 경과조치)
  자체의 서브토탈이었을 뿐, EQ+INT 두 축(`_TRANSITION_KIND`)을 동시에 반영한 결합값이 아니었다.
  게이트 R4/MARKET_M을 직접 import해 재계산(`scripts/fix_20260821_kr0005_2024q4_market_combined.py`):
  item19후 3860.81→2801.44(=게이트 자체가 이미 "계산"이라 표시하던 값과 정확히 일치) + 연쇄
  item15/16/22후 재계산. item14후(13978, 공시 총괄표 앵커)는 불변, item27=27894/13978×100=199.56%로
  공시와 정확히 재현. `TRANSITION_AFTER_MMULT_MISMATCH`(흥국화재분) RED 종결.
- **D. 흥국생명(KR0071) 2024.4Q — 손 안 댐.** downloader가 두 채널(생명보험협회·자사)로 재수집
  시도했으나 둘 다 기존 wrong document(DART 사업보고서)와 SHA256 동일 — issuer 자신이 잘못된 문서를
  공시채널에 올려놓은 상태. 면제 등록 안 함, 값 조작 안 함. 코디네이터가 owner 에스컬레이션 중.
- **게이트**: `validate_data_contract.py` RED 10(세션 시작, display-scope) → 13(A~B 반영,
  TRANSITION_AFTER_IRR_MISMATCH 신규 노출 포함) → **12(최종, C 반영)** — 8건(36_irr류, owner 결정
  대기) + 4건(흥국생명, downloader 대기) = parser 권한 밖. `validate_kics_disclosure.py` Status
  RED=6(불변, 기존 documented). `pytest`(4개 골든+deploy_assets) 13 passed, `--update` 불요(이번
  변경이 그 골든들의 스냅샷 범위 밖). `sh .githooks/pre-push < /dev/null` exit=2(BLOCKED, RED=12,
  inbox 위반 0, offline tests 131 passed) — 예상된 결과, 남은 12건 전부 parser 밖 결정 대기.
- **TODO.md**: `INTERNAL_MODEL_36IRR_EXEMPT` 항목 갱신(허위 사유 제거 + raw 재검증 근거 + 잔존 잔차 +
  owner 결정 필요사항), cross-stage 요약줄에 2026-08-21 갱신 추가.
- **후속(parser 밖)**: 흥국생명 raw 정상화는 owner/issuer 소관. 36_irr 8건 스코프 가설(금리노출
  자산부채 한정)은 owner 재조사 필요 시 KR0094 전체 분기 census로 검증 가능(미착수).

---

**2026-08-21(5회차) — inbox `20260821T1505Z`(오케스트레이터, item4 되맞춤+census 2건) 드레인 +
중간에 코디네이터 긴급정정(KR0097 2024.2Q item41-46후 조작 컬럼) 처리. item4·item3 두 스크립트의
동어반복(reconcile) 버그 근본수정 + 129셀 원문복원, 카카오페이 census 2셀(65행) 로드,
KR0087 시장하위 후미러 4셀. 게이트 `validate_kics_disclosure.py` MISSING_CELLS 2→0(원 티켓 인수조건
달성) — 단 그 사이 validation이 새 메타룰 `IDENTITY_TAUTOLOGY`를 배선해 넣어 exit는 여전히 2, 원인은
전부 이 티켓 밖(아래 참조). row_count 18987→19052(+65, 전부 INSERT).**

- **① item4(Ⅰ 순자산) 되맞춤 버그 — 최우선 항목, 완료.** `fill_period_to_disclosure.py::_reconcile_
  item4_from_components`(잔차≤10이면 자식합으로 교체)와 `recalc_kics_derived.py`(상대오차>5%면 교체)
  둘 다 제거 — item4는 이제 추출값만, 절대 재계산 안 함. **부수 발견**: `recalc_kics_derived.py`
  L188-210이 item3(보완자본)도 **허용오차 없이 무조건** `item1-item2`로 덮어쓰고 있었다(R1 적용전
  축이 잔차 97.7% 정확0이던 원인) — 같이 제거(존재하는 값은 이제 절대 안 건드림, 결측일 때만 역산
  생성은 유지).
  - **복원(자식합 역산 아님, md_inbox 원문 재추출)**: item4 435건 비교 → 122건 불일치(전부
    "master==Σ자식≠raw" 지문) → 121건 복원(diff 대부분 ±1, 억원 반올림 정상 신호). **KR0003
    2023.4Q 1건은 보류**(raw p41 총계행 자체가 자기모순 — 같은 행 성분합 24,808 vs 인쇄된 총계
    2,481, 인접분기·item1과도 10배 이탈 — 필러 오타로 판단, 현재값 유지, 등재는 안 함). 라운드2에서
    미변환 6분기 docling 재실행(KR0051×4·KR0071·KR0074·KR0080, `run_harness --stage parse`) +
    수기 3건(KR0032×2·KR0049, md_inbox 직접 대조) 추가 복원. 그 과정에서 **KR0080 2023.2Q
    item7/9/11**(이익잉여금·기타포괄손익·조정준비금)도 같이 깨져 있던 것 발견·raw로 동시정정(같은
    표 같은 컬럼). item3 쪽도 80건 복원 중 **KR0004 2024.2Q 1건**을 되짚어 정정(내 첫 복원값 3085가
    부정확한 표에서 왔다 — 백만원 단위 정밀표(48,998/308,195)가 더 정확, 3081.95로 재정정. 이 표는
    **이미 있던 값_적용후(3081.95)의 출처**이기도 해서 전/후 정합이 됨).
  - **손 안 댐(정책)**: KR0010·KR0079·KR0080(2024.4Q~)·KR0071(2024.4Q) 24셀 — `IMAGE_OCR_COMPANIES`/
    GOLD-SCAN 코호트, 텍스트레이어 실질 부재 확인(fitz `total_chars` 실측), 즉흥 OCR 금지 정책 준수.
  - **잔차 분포 before/after**: 적용전 452/486(93.0%)→327/488(67.0%), 적용후 212/230(92.2%)→
    172/232(74.1%). 귀무기대(반올림 Irwin-Hall) ~54%대에 근접, 남은 초과분은 위 24셀(스캔본, resid=0
    로 고정) 때문으로 추정.
- **② KR0087 2023.2Q item36-39후 — 완료.** raw p11 신청현황표(TAC/TIR/TER/TIRR 전부 X)·p12-13
  서술("지급여력비율 경과조치 미적용으로 경과조치 전·후 금액 및 비율이 동일")·공통TFI표(지급여력
  기준금액 전후 동일) 3중 확인 후 item36-39후=item36-39전 미러 4셀. item19(부모)는 이미 미러
  상태였음(추측 아니라 확인 후 채움).
- **③ 카카오페이손해(KR1098) 2024.2Q/2024.3Q — 완료(census 2셀→행 65개).** raw 존재 확인
  (`data/disclosure/FY2024_Q{2,3}/raw/`) → **파싱갭**(다운로더 발주 안 함). 두 PDF 모두 텍스트레이어
  실질 0(fitz: 622자/45p, 28자/19p) — 스캔본. `get_pixmap(dpi=100)` 렌더링+vision으로 Q3 PDF p11의
  3분기 비교표(24.3Q/24.2Q/24.1Q 동시 수록, 24.1Q 컬럼이 기존 마스터와 완전일치해 판독법 자체를
  교차검증) 판독 → items1-28 양분기 로드(27항목×2, 비적용사 확인되어 값_적용후=값 미러) + item36-40
  시장하위(p26-29, item36=derive식 검산 diff 0.24 exact) + item41-46 IRR(p26-27, item36 재도출과
  cross-check). 29-35는 item17=0(2Q)/2(3Q, 미미)이라 미적재.
- **코디네이터 긴급정정 (작업 도중 수신, 즉시 처리)**: KR0097 2024.2Q item41-46 값_적용후가 이전
  라운드에서 값과 동일하게 미러돼 있었는데, 이 항목군(3-1-0~3-1-5 금리위험 순자산가치)은 원문에
  경과조치 적용전/후 축 자체가 없다(충격전/충격후 축만 존재, p27 확인) — 조작된 컬럼. 6셀 값_적용후
  삭제(키 자체 제거, null 아님 — 이 파일의 "결측=키부재" 관례와 일치). 18사 적용사 전수 스윕으로
  KR0097만 유일한 오염 확인(다른 17사는 전부 정상 결측), KR0087 2023.2Q도 같이 확인했으나 이미
  정상(결측)이었음.
- **게이트 재검증**: `validate_kics_disclosure.py` — census(MISSING_CELLS) **2→0**(원 티켓 인수조건
  충족). regular rule 개별 findings 신규 RED **0건**(내가 만든 파생 불일치는 발견 즉시 같은 라운드에서
  정정 완료). 단 **exit는 여전히 2** — 이 티켓이 진행되는 동안 validation이 새 메타룰
  `IDENTITY_TAUTOLOGY`(오케스트레이터 별도 티켓 `20260821T1500Z`로 발주)를 게이트에 배선해 넣었다.
  R1(item3 관련)은 내 수정으로 자동 해소(97.7%→81.3%, 귀무 이내). **R2(item4)는 아직 RED**(67.9%/
  78.0%, 귀무 대비 여전히 높음) — 남은 초과분이 위 정책보호 24셀(KR0010/KR0079/KR0080/KR0071 스캔본)
  때문임을 확인했으나 그 이상은 손 안 댐(SKILL 정책). **rule 36_irr 5건**(KR0094 4분기+KR0073
  2025.2Q, item36 있는데 41-46 결측)도 exit=2에 기여하는데 — **내가 안 건드린 회사, 체크포인트
  비교로 확인**(item3 라운드 직후엔 없었다가 이후 라운드에 나타남 → 동시편집 세션 추정, 이 티켓
  스코프 아님). `pre-push` 훅(`validate_data_contract.py` 포함, ~6.5분)도 exit=2 — RED 10건 전부
  대조 결과 **미접촉 회사/이미 문서화된 과거 이슈**(흥국생명·흥국화재 2024.4Q raw 오염=2026-07-07
  경 downloader 기발주, 하나생명 2024.4Q=2026-07-15(3차) 보류 결정, 신한라이프/교보생명 36_irr=위
  R2와 동일건). 상세 근거는 inbox 답변 참조.
- **골든 재생성**: `test_kics_rules_golden.py`·`test_post_transition_golden.py` `--update`(의도된
  이동, 사유 위와 동일). `pytest tests/test_kics_rules_golden.py tests/test_post_transition_golden.py
  tests/test_master_tables_golden.py tests/test_deploy_assets.py tests/unit/` = **123 passed**.
- **xlsx 미동기화** — 이번 세션 변경분 `insurequant_master_tables.xlsx`에 반영 안 함(티켓이 명시적으로
  금지, "손대지 마라"). 다음 라운드에 `sync_master_xlsx_sheet.py`로 K-ICS공시 시트 cherry-pick 필요.
- **owner/validation 판단 대기**: (a) rule 36_irr KR0094/KR0073 원인 규명 — 내가 안 건드렸는데 언제
  나타났는지 불명, 다음 세션이 raw로 재확인 필요. (b) IDENTITY_TAUTOLOGY R2 잔존분(24셀)을 축
  정의에서 image-only 코호트로 제외할지는 validation 판단(내가 임의로 축 정의 못 바꿈). (c) KR0003
  2023.4Q item4 총계행 자기모순 — 필러 오류로 추정만, 확정 불가.
- 신규 상주 스크립트: `fix_20260821_item4_writepath_restore.py`·`fix_20260821_item3_writepath_
  restore.py`·`fix_20260821_item4_manual_stragglers.py`·`fix_20260821_kr0080_2023q2_children.py`·
  `fix_20260821_kr0004_item3_revert.py`·`fix_20260821_kr0087_2023q2_market_post_mirror.py`·
  `fix_20260821_kr1098_2024q2q3_load.py`·`fix_20260821_kr1098_2024q2_market_subs.py`·
  `fix_20260821_kr1098_2024q2_irr.py`·`fix_20260821_kr0097_2024q2_irr_post_denull.py`. 진단 probe
  다수는 `scripts/_probes/`(`probe_item4_raw_vs_master.py`·`probe_item3_raw_vs_master.py`·
  `probe_item4_residual.py`·`probe_item4_unmatched_residual.py` 등). 전부 cell-by-cell UPSERT/INSERT,
  실행마다 전/후 census 출력.

---

**2026-08-21(4회차) — 크래시 복구 세션: inbox 4건(F1/F2/F3 leaf잔차·KR0071 item24·KR0087 2023.2Q 26항목·
KR0097 2024.2Q 스캔본) 순차 처리. 게이트 RED 12→1(KR0087 7건·KR0097 4건 완전 해소, 잔여 1건은
KR0079 8_life — 오케스트레이터 소관, 안 건드림). row_count 18918→18987(+69, 전부 INSERT, DELETE 0).**

- **`20260821T1030Z`(F1/F2/F3 leaf 스케일 잔여) — 크래시 전 에이전트가 이미 완료.** 코드 확인 결과
  F2(문턱 0.005억 고정)·F3(연속페이지 포함+시장leaf 대시=전후동일)가 이미
  `scripts/rebuild_combined_transition_after.py`에 반영돼 있었고, `--leaves --dry-run`(전 APPLIERS
  스코프, `--only` 없이)이 **"갱신 0셀"**을 반환 — 111셀 전부 이미 정확. 감사기 재실행(F2/F3 반영된
  스캐너로) → 182건(오늘 아침 stale) → **7건**으로 급감, 그중 4건은 감사기 자체의 새 버그(동률 tie-break
  `max(set(cand), key=cand.count)`가 엉뚱한 값을 고름, 교보생명 item35전 3건+처브라이프 1건 — **값
  컬럼**이라 이 티켓 스코프 밖이기도 함), 3건(예별손해보험 KR0004 2023.4Q/2024.1Q/2024.2Q item36후
  =0 vs raw 652.39~716.06)은 `_leaves_mode`의 부모후 재현 가드가 정당하게 막은 **미해결 실사례**
  (item19 계열에 별도 오류가 있을 가능성, 추측 기입 안 함 — 다음 라운드 후보, 아래 잔여 항목 참조).
- **`20260821T1105Z`(KR0071 item24) — 1셀.** 원문 "-"(해당없음)이 8313(item23/26 복붙 오염)으로
  저장돼 있던 것을 0으로 정정(item25 처리와 일관). 전사 스윕(item23=24+25+26, tol 1.5억)으로 이 1건
  외 위반 없음 확인.
- **`20260821T1140Z`(KR0087 2023.2Q 메인표) — 29셀.** raw p11/p12 직접 재추출로 26항목(item10 제외,
  raw에 행 자체 없음 확인) INSERT + item2/3후 원문 TFI표에서 채움 + item15-26후는 item14후=item14전
  정밀일치를 근거로 기존 미러링 룰 적용 + item28후 산출. **부수: item19 적재가 19_market을 새
  RED로 노출**시켜 raw p20-22에서 item37-40(주식/부동산/외환/자산집중위험액) 4셀 추가 발견·적재,
  MARKET_M 검산(diff 0.07억) 후 반영. **KR0087 2023.2Q RED 7→0(19_market 포함).**
- **`20260821T1230Z`(KR0097 2024.2Q, 세션 중 신규 발주) — 40셀.** 순수 스캔본(fitz 0자) —
  `get_pixmap(dpi=300)`로 p15·p17·p18 직접 렌더링해 오케스트레이터 판독과 별개로 재판독, 100% 일치
  확인 후 34셀 INSERT(item4-13후는 원문 부재로 null 유지). **부수: item36 적재가 36_irr을 새 RED로
  노출**시켜 p27(당기 금리위험 IRR 시나리오표, 렌더링 재확인)에서 item41-46 6셀 추가 발견·적재,
  derive식 검산(diff 0.002) 후 반영, 41-46후는 TIRR 미신청 확인되어 전=후 미러. **KR0097 2024.2Q
  RED 4→0(36_irr 포함).**
- **게이트**: RED 12(세션 시작, baseline과 일치) → 5(티켓3 후) → 1(티켓4 후, 잔여=KR0079 2023.2Q
  8_life만, documented·오케스트레이터 소관). `pytest tests/test_kics_rules_golden.py
  tests/test_post_transition_golden.py tests/test_master_tables_golden.py tests/test_deploy_assets.py
  tests/unit/` = **123 passed**(`test_kics_rules_golden`만 `--update` 재생성 필요, 나머지는 무변경
  PASS). `validate_master_tables.py --no-build` 별도 확인(ifrs17 레인 마스터라 내 변경과 무관, 정상).
- **신규 상주 스크립트**: `fix_20260821_kr0071_item24_fabricated_dash.py` ·
  `fix_20260821_kr0087_2023q2_main_table.py` · `fix_20260821_kr0087_2023q2_market_leaves.py` ·
  `fix_20260821_kr0097_2024q2_vision_ocr.py` · `fix_20260821_kr0097_2024q2_irr.py`. 전부 cell-by-cell
  UPSERT(통짜 rewrite 아님), 실행마다 자체 전/후 census(row_count·combo delta) 출력.
- **xlsx 미동기화** — 이번 69셀(4개 티켓 합산)을 `insurequant_master_tables.xlsx`에 아직 반영 안 함
  (지시대로 이번 턴엔 손 안 댐). 다음 라운드에 `sync_master_xlsx_sheet.py`로 K-ICS공시 시트
  cherry-pick 필요.
- **다음 라운드 후보(미해결, 강제 기입 안 함)**: (a) 예별손해보험(KR0004) 2023.4Q·2024.1Q·2024.2Q
  item36(금리위험액)_적용후 — raw는 전후 동일(652.39/716.06/567.90)로 명확한데 `_leaves_mode`의
  부모(item19)후 재현 가드가 막는다(계산 1,446~1,601 vs 저장 1,106~1,341) → item19나 다른 leaf에
  별도 문제 있을 가능성, raw 재조사 필요. (b) 아이엠라이프(KR0076) 2023.1Q parent17 hold(diff 9.91) —
  미조사. (c) `leaf_scale_residue_audit.py`의 동률 tie-break 버그(`max(set(cand), key=cand.count)`가
  카운트 동률일 때 임의값 선택) — read-only 진단 스크립트라 게이트는 안 막지만 다음 감사 때 오탐
  유발. 재현: `scripts/_probes/leaf_scale_residue_audit.py` 실행 후 교보생명 2023.2Q/2024.2Q/2026.1Q
  item35 값(전) 3건 확인.

---

**2026-08-21(3회차) — inbox `20260821T0400Z` 드레인(validation 적대적 재검증, raw-only). ①REVERT+REDO 1건·②③④ raw 오류/결측 셀 로드·⑤ 36_irr 미러 확인. RED 12(회귀 0, 도중 15까지 갔다가 원인 규명 후 복귀).**

- **① 한화손해(KR0002) 2024.2Q — REVERT 확인.** 어젯밤 `item1후 53541→53537.72`는 틀렸다(validation
  지적대로). raw p14 "공통적용 경과조치"표(기본자본 2,638,159→2,872,265·보완자본 2,715,975→2,481,870,
  합 5,354,135=item1전 불변)를 직접 재확인 → `item1후=53541`(원복)·`item2후=28722.65`·
  `item3후=24818.7`. 2024.1Q/2024.3Q도 같은 관례(총괄표=item1후, 공통표=item2/3후) 확인.
  **부수: item28후가 옛 item2후에서 도출된 값(103.12)으로 정체돼 새 RED 유발 → item28후=112.28로
  캐스케이드 수정**(item2/14후 재계산, `fix_20260821_hanwha_kr0002_item28_cascade.py`).
- **② 롯데손해(KR0003) 2026.1Q item29~35후 7셀 — raw p24 직접 재확인 후 5셀 교체**(29·31·32·33·34,
  30·35는 이미 일치). ticket 인용과 완전 일치.
- **③ 면제 사유 오류 2건 — raw에 표가 있다.** `_AFTER_SUBRISK_NOT_DISCLOSED`의 `("KR0003","2026.1Q")`
  "②③표 부재" 및 `("KR0073","2026.1Q")` "섹션 자체 없음" 둘 다 **거짓**(docling MD 유실, raw PDF엔
  표가 있음) — 등재 해제는 validation/owner 소관이라 안 건드림. **KR0073 2026.1Q item29~35는 행
  자체가 없었다** → raw p15 ②표(전/후 둘 다)로 7행 신설, R7-sqrt로 item17전/후 둘 다 소수점 단위로
  재현(diff -0.09/-0.01) 확인 후 반영.
- **④ 미공시 3건 로드 + 스윕 중 신규 결함 2건 추가 발견.**
  - 신한이지(KR0051) 2024.4Q item30 신설(raw p33 "-"=0) + **item31~35가 이미 /100 스케일 오류로
    적재돼 있었음**(0.04 등, 있어야 할 값의 1/100) 발견 → ×100 정정(4/1/2/2/2). 전분기 census로
    2024.4Q만의 단발 오류 확인(다른 전 분기는 item17=sum(29-35) 비율 정상).
  - 신한이지 2023.1Q item29~35 신설 — get_text() 컬럼 순서가 뒤섞여 pdfplumber 단어좌표로 재구성,
    R7-sqrt로 item17=2.93 정확히 재현(diff 0.00).
  - AIA(KR0080) 2023.3Q item40 신설(0) + **item19가 오류(3643, 참값 3779)였고 이게 item14·15·16·
    20·22·27·28 전체 클러스터와 자기정합적으로 얽혀 있었음**(전부 서로 다른 잘못된 값끼리만
    맞아떨어짐) → raw p9(헤드라인)·p10(공통경과조치표)·p11(②표) 3중 인용 일치 확인 후 10개 항목
    (1·2·3·14·15·16·20·22·27·28) 전/후 동시 교체. R1/R5 정확히 닫히고 R4/R6 잔차 1~2(정상 반올림)로
    수렴.
  - **홀수분기 미러링 스윕(요청4) — B3b 5셀 개별 확인, 패치 불요 3건 + OCR 재분류 2군.** 롯데
    2023.1Q item19: raw p10 재확인 결과 item29~40 **이미 마스터가 raw와 정확히 일치**(해지·사업비·
    대재해만 진짜 "-"=0, 나머지 불변 — 이전 세션이 이미 정확히 반영). item36~40은 그 분기 raw
    자체에 시장위험 세부표가 없어(1개 결합표만 존재) 소스 결측, 패치 대상 아님. 현대해상(KR0009)
    2023.1Q: raw p8/p10에 **"경과조치 후: 해당사항 없음"이 명시 문구로 박혀있음** — 결측이 아니라
    구조적 정당(2023.1Q 최초분기라 선택경과조치 자체 미신청 추정), 새 면제 카테고리 후보로 보고만.
    AIA(KR0080) 2025.1Q·2025.3Q·2026.1Q: 페이지 텍스트가 "페이지 N/32" + 산발적 "0"뿐 →
    **스캔본(텍스트레이어 실질 부재)**, ticket의 B3a(OCR 큐) 버킷으로 재분류 요청(B3b 아님).
- **⑤ 36_irr(item41~46) 적용후 — ticket 결론 전수 확인, 미수정.** 코드로 618셀(103 (사,분기)×6항목)
  전수를 직접 스캔 → **618/618 전부 정확히 값_적용전과 동일**(오차 0). raw 2건(흥국화재 기존 인용+
  한화손해 KR0002 p32 신규 확인)에서 시나리오표 헤더가 `충격 전|충격 후(평균회귀·금리상승·…)`뿐이고
  경과조치 축 자체가 없음을 직접 확인 — "경과조치 적용후" 개념이 원천에 없다는 ticket 결론 재확인.
  **null 처리 + `POST_SCENARIO_NOT_IN_SOURCE` 면제 신설은 owner 결정 대기, 셀 미변경.**
- **재검증**: `validate_kics_disclosure.py` RED **12**(불변 — KR0087 7룰·KR0097 4룰·KR0079 8_life
  1건, 전부 기존 documented). 적용후 mmult 불일치 2→1(잔여 KR0079 2023.2Q, 기존 documented) ·
  적용후 항등식 위반 2→0 · 선택경과조치 적용후 AMT_MISMATCH 1→0. (수정 도중 RED가 일시 15까지
  올라갔다 — item19 교정이 KR0080의 자기정합적 오류 클러스터를 노출시켰기 때문. 원인 추적 후 클러스터
  전체 교정으로 12 복귀. 상세는 스크립트 주석·inbox 답변 참조.) `pytest tests/unit/` 110 +
  `test_deploy_assets` 10 + `test_kics_rules_golden`(`--update`, 6804 findings/486 buckets, RED 12
  불변) + `test_master_tables_golden`(`--no-build`) 1 + `test_post_transition_golden`(`--update`,
  6114 cells/428 company-quarters) = **123 passed**.
- **xlsx 미동기화** — `insurequant_master_tables.xlsx`에 이번 셀 반영 안 함(`sync_master_xlsx_sheet.py`
  로 K-ICS공시 시트 cherry-pick 필요, 다음 라운드로 이연).
- **owner 판단 대기 (parser는 등재하지 않음)**: (a) `_AFTER_SUBRISK_NOT_DISCLOSED`에서
  `("KR0003","2026.1Q")`·`("KR0073","2026.1Q")` 해제(사유가 raw와 불일치, 값은 이미 로드됨).
  (b) item41~46 적용후 103셀(618개 값_적용후 cell) null 처리 + `POST_SCENARIO_NOT_IN_SOURCE` 면제
  신설. (c) 현대해상류 "해당사항 없음" 명시-부재를 새 면제 카테고리로 등재할지. (d)
  `fix_20260716_nonapplier_requirement_mirror.py` L115 짝수분기 게이팅을 부모후결측 조합까지 포함해
  완화할지(코리안리·AIA·신한이지 3반례 확인됨, 다른 홀수분기는 이번 스윕에서 추가 반례 없음).
  (e) KB손해 5분기·미래에셋 6분기·동양 2026.1Q(+AIA 2025.1Q/2025.3Q/2026.1Q 신규)를 OCR 큐에 등록할지.
- 신규/변경 스크립트: `scripts/fix_20260821_adversarial_reverification.py`(①②③④ 핵심 36셀) ·
  `scripts/fix_20260821_hanwha_kr0002_item28_cascade.py`(① 캐스케이드 1셀) ·
  `scripts/fix_20260821_aia_kr0080_2023q3_headline.py`(④ 헤드라인 클러스터 20셀).

---

**2026-08-21(2회차) — inbox `20260821T0155Z` 드레인: validation이 게이트를 적용사 18사→전사 39사로
확대 배선한 뒤 새로 드러난 RED 3종(적용후 항등식·mmult·하위census) 중 2종 해소.**

- **한화손해보험(KR0002) 2024.2Q item1후**(53541→53537.72): 적용전 복사 버그, raw로 확정 수정.
  **전사 스윕**(item1후==item1전인데 item2후+item3후와 불일치)을 돌리니 486버킷 중 138개가 걸렸지만
  거의 전부 정수/소수 반올림 경계 노이즈였다 — `round()` 기준으로 좁히니 7건, 그중 raw 대조로
  **4건은 진짜 오탐**(케이디비생명 3분기·하나생명 1분기 — 전부 TAC 적용사라 item1이 `①자본감소분`
  표에서 item2/3와 별개로 산출됨, item1=item2+item3 가정 자체가 안 맞음), 2건은 반올림 경계일 뿐
  버그 아님(DB생명·하나손해), 1건은 검증불가(카카오페이, image-only PDF, RED 임계 밖이라 비차단).
  **진짜 버그는 최초 지적받은 한화 1건이 전부** — naive 규칙으로 138건을 일괄 처리했으면 정상인
  TAC 반영값을 깨뜨릴 뻔했다.
- **코리안리재보험(KR1000) 2023.3Q 세부위험 12셀**(item29-35·36-40 적용후 결측): ticket의 "백필
  경로 버그" 가설은 틀렸음을 raw로 확인 — 2023.3Q 자체 raw에 ②③표가 존재하고, 전 행이 "-"로
  채워진 채 "당사는 ~ 적용하지 않아 경과조치 전·후의 금액 및 비율이 동일함" 각주가 명시돼 있다
  (필러의 "전후 동일" 표기 관례이지 결측이 아님). `fix_20260716_nonapplier_requirement_mirror.py`
  L115가 세부위험 미러링을 짝수분기로만 게이팅해놨는데(대부분 회사는 홀수분기에 세부표 자체가
  없다는 전제가 맞지만) 코리안리는 예외 — 그 예외만 게이트를 피해갔다. 같은 신호(부모 전후 동일 +
  세부전 존재 + 세부후 결측, 홀수분기 전수)로 스윕해 **롯데손해보험(KR0003) 2026.1Q 시장위험
  5셀**도 동일 패턴으로 발견, raw(직전 짝수분기 2025.4Q의 확립된 미러 패턴)로 근거 확인 후 같이
  수정. 총 17셀, 전부 자기 값_적용전 그대로 미러링(값 자체는 raw에 이미 있던 것).
- **재검증**: 적용후 항등식 위반(RED) 1→**0**, 적용후 하위 census 결측(RED) 2→**0**, 적용후
  mmult 불일치(RED)는 KR0079(documented, owner 승인 대기) 1건 불변(지시대로 미터치). RED 전체
  12→**12**(회귀 0). `pytest` unit 110 + deploy_assets 10 + master_tables_golden(--no-build) 1 +
  post_transition_golden 1 = 122 passed. `test_kics_rules_golden`은 이번 셀들이 그 골든 스냅샷
  범위(8-rule 엔진, 확대 전 코어) 밖이라 재생성 불요, 그대로 통과.
- **게이트 코드(2Q/4Q 게이팅) 자체는 안 고침** — 이번엔 셀 데이터만 직접 수정(parser 스크립트
  코드 변경은 별도 판단 필요, 지금 스윕으로 이 2건 외 추가 후보 없음 확인됨).
- 상세 raw 인용·전수스윕 커맨드는 `inbox/parser/20260821T0155Z__validation__MULTI__after_column_widening_findings.md`
  (`status: answered`) 참조.

---

**2026-08-21 — inbox `20260821T0010Z` 드레인: 적용후 mmult 3축 감사(축C 기본요구자본 9~36건 미closure,
axis A 비적용사 3건, R1 1건) 전부 해소. RED 12(불변, 회귀 0).**

- **⚠️ 이 작업 도중 같은 브랜치·같은 파일(`kics_disclosure.json`)을 편집하는 다른 세션이 동시에
  돌고 있었다**(커밋 없이 워킹트리만 — `git show --stat`로 그 세션의 커밋 3개(`404581a`/`88f059c`/
  `f90d38c`)는 TODO/changelog/inbox/probe만 건드리고 데이터는 안 건드린 것 확인. 값이 세션 중간에
  두 번 다르게 읽혀서 발견). 그 세션의 축-C 수정 방법론(총괄표 헤드라인 우선+R4/MARKET_M 역도출)을
  내가 독립적으로 재도출한 것과 교차검증해 대부분 일치 확인 → 이미 고쳐진 셀(에이비엘 3분기·농협생명
  2분기·흥국생명 2분기·흥국화재 2023.2Q)은 안 건드리고, **그 세션이 아직 안 건드린 잔여만** 직접
  수정. 상세 방법론·재현 커맨드·셀별 raw 근거는 티켓 `## 답변` 섹션(2026-08-21T0230Z) 참조.
- **내가 직접 수정한 셀 (raw 근거 포함, 전부 티켓에 인용)**:
  - 흥국화재(KR0005) 2023.1Q item15/16/19/22/36후 — 이 회사만 유일하게 시장위험 경과조치가 ③(주식)
    ④(금리) **별도 표 2개**로 분리공시되는데 기존 item19후가 ③표만 반영하고 ④표(금리위험
    454,370→272,622백만)를 누락한 부분치였음 + item14후 자체가 이 회사 PDF의 비-브래킷 헤드라인
    레이아웃을 못 찾아 ②표(TIR 단독)의 자체 기준금액으로 오인돼 있었음(둘 다 raw fitz로 재확인).
  - 신한이지(KR0051) 2025.1Q item35후(43→2)·하나손해(KR0050) 2025.2Q item34후(44.43→381.53)·
    KB라이프(KR0099) 2024.2Q item33후(12364→10787.13) — 전부 **비적용사**(선택경과조치 미신청,
    `_TRANSITION_APPLIERS` 밖)인데 `_transition_mmult_after`가 적용사 18사만 순회해 게이트를 한번도
    안 거친 오염 셀. 전=후 미러가 정상인 회사라 전값으로 복원.
  - KB라이프(KR0099) 2026.1Q item3후(23071→22573) — 공통TFI표 보완자본 재분류(2,307,119→2,257,319
    백만) 반영 누락. item1=item2+item3 R1 항등식 복원.
- **재검증**: `validate_kics_disclosure.py` RED=12(전부 기존 documented: KR0087 동양생명 image-only·
  KR0097 하나생명·KR0079 미래에셋 8_life scan-only), 적용후 mmult 불일치=0, 적용후 항등식 위반=0.
  축C 기본요구자본 mmult 적용후 **480/480 PASS(FAIL 9→0)**. 축A/B 적용후 고유 FAIL 4/1→0(잔여 각 1건은
  기존 documented, 신규 아님). `pytest tests/unit/` 110 passed·`test_deploy_assets`·
  `test_master_tables_golden`(--no-build)·`test_post_transition_golden` 통과. `test_kics_rules_golden`
  은 의도된 데이터 이동이라 `--update` 재생성(6,804 findings/486 buckets, RED=12 불변, 룰엔진 코드는
  무변경).
- **owner 승인 대기 (self-close 안 함)**: item5-11(순자산 구성요소)·41-46(IRR 시나리오) 적용후 커버리지
  47%/21% — item5 계열은 raw 전수 확인 결과 **적용사 0%/비적용사 91%**로 극명히 갈려, "적용후 순자산
  구성요소"라는 공시 개념 자체가 없고 비적용사만 baseline 미러로 채워져 있음이 원인(파싱갭 아님).
  41-46은 미검증(시간배분상 5-11 우선). `MARKET_BREAKDOWN_EXEMPT`류 census 면제 등재 여부는 owner
  판단 필요 — 임의 등재 안 함.
- **게이트 배선(범위구멍 2개) 변경 없음**: `_transition_mmult_after`의 18사 스코프 제한·
  `_TRANS_PARENT_SUBS`의 item15 부재는 코드상 그대로. 데이터만 고쳤고 룰엔진(validation 소관)은
  손 안 댐. 데이터가 깨끗해졌으니 축C를 전사·item15 포함으로 확장 배선해도 즉시 RED는 안 뜬다(0/0).
- **xlsx 미동기화**: 위 셀 수정을 `insurequant_master_tables.xlsx`에 아직 반영 안 함 — 동시편집
  세션이 아직 활성이라(§ 위) 부분 동기화가 곧바로 stale해질 위험 판단, 다음 라운드(그 세션 마무리 후)
  로 이연. `sync_master_xlsx_sheet.py`로 K-ICS공시 시트 cherry-pick 필요.

**2026-08-21 (이어서, 병렬 세션) — 같은 티켓을 동시에 잡은 두 번째 세션의 기록.** 위 항목을 쓴
세션과 내가 같은 브랜치에서 `kics_disclosure.json`을 각자 통째로 read-modify-write 했다.

- **⚠️ lost update 실발생 1건**: KB라이프 2026.1Q `item3후`(공통TFI 보완자본 재분류 22,573.19)가
  내 전체쓰기에 덮여 사라져 있었다. R1 전수감사로 재적발 → raw p21 대조 후 복구
  (`scripts/fix_20260821_missing_life_subs.py`). **감사 스크립트가 유일한 안전망이었다** — 이 마스터를
  통째로 쓰는 스크립트는 동시 세션에서 조용히 서로를 지운다. 다음 라운드에 셀 단위 write 로 바꿀 것.
- **축 C 를 36건 전건으로 확대 종결** (`scripts/rebuild_combined_transition_after.py`, 신규·상주).
  결합 모델 = leaf 는 그 leaf 를 줄인 표에서, 부모는 R7/MARKET_M/R4 로 재계산, **기준금액후는 회사
  공시 헤드라인 비율에 앵커**하고 법인세조정액후는 잔차. 쓰기 전 가드 3개(적용전 재현 / 표 공시
  부모후 재현 / 단일표 대비 단조성) 통과분만 반영. 36/36 이 원문 헤드라인을 소수 둘째자리까지 재현.
  **흥국생명 11분기**의 기타요구자본(관계회사 환산치)은 **흥국화재 item14 로 환산**해 풀었다 —
  환산계수 0.40060±0.00003 (13분기 실측). `20260706T0502Z`에서 "추정 금지"로 비워 둔 셀이 근거를
  갖고 채워졌다.
- **비적용사 오염 전수 스윕 21셀 복원** (`scripts/fix_nonapplier_after_drift.py`, 상주). 게이트가
  `_TRANSITION_APPLIERS` 18사만 보느라 한 번도 안 거친 구간이다. + `item29(사망위험)=0`인데 원문엔
  값이 있는 케이스 전수 확인 → 1건(KB손해 2023.2Q 258,369백만) 반영.
- **0값 leaf 행 누락 41건 중 71셀 복원** (`scripts/fill_zero_subrisk_rows.py`, 상주). 판정은 추정이
  아니라 검산 — 결측 leaf 를 0 으로 놓았을 때 mmult 가 저장된 부모를 재현할 때만 쓴다. 계산불가
  A 141→131 · B 190→138. **이 항목이 아래 "남긴 잔여 1"의 해소분이다.** 보류 17건(0 으로 놓으면
  부모 재현 실패 = 진짜 결측)은 다음 라운드.
- **요청4 판정 — item41~46 적용후는 원천 부재**(census 면제 대상). 전수 결과 **전≠후 셀이 0건**이고,
  원문 금리위험 순자산가치 표는 경과조치 전/후 컬럼이 아예 없는 단일 표다(농협생명 FY2024_Q2
  p23·p24 등 확인). 경과조치는 산출된 금리위험액에 적용될 뿐 순자산가치를 바꾸지 않는다.
  item5~11 도 동일(①②③④ 어느 표에도 순자산 구성요소 행이 없음).
- **xlsx 동기화 완료** — `sync_master_xlsx_sheet.py`로 `K-ICS공시` 시트 cherry-pick(변경 셀 455 ·
  신설 행 21), 나머지 7개 시트 값 동일 검증. 위 항목의 "다음 라운드로 이연"을 이 세션에서 처리.
  (도구 버그도 하나 잡음: 다중 삽입 시 인덱스 보정 누락 — 검증 가드가 저장 전에 막았다.)
- **재검증**: `validate_kics_disclosure.py` RED=12(회귀 0) · 적용후 mmult 0 · 적용후 항등식 0 ·
  적용후 하위 census 0 · continuity break 0 · 조정항목 review 5→3. R1 적용후 FAIL 1→0.
  `pytest` 122 passed. `test_kics_rules_golden` 은 의도된 이동(rule 8_life SKIP 136→128 ·
  GREEN 337→344, RED 불변)이라 `--update` 재생성.

---

**2026-08-20 — inbox 드레인 2건 종결(`20260706T0502Z` iter-2 · `20260803T0520Z` UH-8).
경과조치 적용후 continuity break 34셀/5쌍 → 0, 적용후 하위 census 결측 4 → 0.**

- **다섯 (회사,분기)의 원인이 전부 달랐다.** 전부 raw PDF를 fitz로 직접 읽어 처리(Docling MD는
  다섯 중 넷에서 경과조치 섹션을 통째로 흘렸거나 열을 밀어 넣었다).
  - **KR0050 하나손해 2023.2Q = 결측이 아니라 오염.** 저장된 값_적용후가 [경과조치 적용 전 …세부]
    3분기 비교표의 **전분기(2023.1Q) 컬럼**이었다(컬럼 한 칸 밀림). raw는 "경과조치를 적용하고 있는
    사항이 없습니다" + 네 표 전부 "전·후 동일" 주석 → 전값 미러로 교체. 같은 시그니처
    (후(q)==전(q−1)≠전(q))로 전 그리드 스윕 → **이 한 건이 유일**.
  - **KR0097 하나생명 2023.2Q · KR1011 IBK연금 2023.2Q · KR0004 예별손해 2023.1~3Q = ②+③ 비중첩
    결합.** 결합 벡터 R4 재계산이 공시 헤드라인 지급여력기준금액후를 백만원 단위로 재현
    (360,712.71/3,607억 · 517,910.57/5,179억 · 820,515.73/820,516 · 785,931.40/785,937 ·
    767,461.88/767,462). ② 단독·③ 단독도 각각 재현되므로 우연이 아니다. **IBK 2023.2Q에 대한
    2026-07-12(5차) "다중경과조치 결합공식 불명" 판정은 오판으로 정정.**
  - **KR0100 처브라이프 2024.3Q** — "②표 값이 행별로 다른 컬럼 착지"는 Docling 아티팩트였고 raw는
    fitz로 깨끗하다. `_AFTER_SUBRISK_NOT_DISCLOSED`에서 **해제**(면제로 두면 새로 채운 값이 mmult
    검사에서 영구 skip).
  - **KR0049 악사손해 2024.3Q = 유일한 진짜 미공시.** 그 분기 공시서에 지급여력비율 섹션이 통째로
    없고(부칙 제3조 유예), 값의 출처인 FY2024_Q4 공시서는 과거분기 경과조치후를 [지급여력비율 총괄]
    3줄로만 싣는다 → 15-23후 원천 부재. `TODO.md` documented exception + `_POST_PARENT_NOT_DISCLOSED`
    등재. 가용자본측 item3후만 TIR 단독 적용 근거로 확정해 채움(2,326).
  - **KR0071 흥국생명 2023.1Q** — 공통TFI 재분류(신종자본증권 50,000백만 보완→기본)로 item1후
    26,499 · item3후 17,737.26 확정. R1 닫힘.
- **부수 적발 — ③표 미반영 실데이터 오류 2분기.** 예별손해 2023.1Q·2023.3Q의 item36(금리)·
  item37(주식) **적용후가 ②표(시장 불변) 값**이었다(③표 주식·금리 경과조치 미반영). **item19후가
  결측이라 mmult가 영구 skip 되면서 숨어 있던 값**이다. 정정 후 MARKET_M 정확히 닫힘. 같은 조합
  ("부모후 결측 + 세부후 present")을 전 그리드 스윕 → 이 3분기가 전부, 지금은 0.
- **조정항목(22 법인세·23 기타요구자본) 적용후 전수 종결.** 적용사 121(회사,분기)이 비어 있었고
  게이트 review는 그중 17만 보여 주고 있었다(직전 분기에 후가 있을 때만 발화 → 채울 때마다 앞
  분기가 새로 드러나는 구조). 3중 가드(행 라벨 정확일치+②/③ 페이지 / raw 적용전이 저장값과 단위까지
  일치 / R5 적용후 항등식 성립)로 **148셀 채움, 7건 보류** → review 17 → **5**.
- **재검증**: 핵심룰 RED=12(전부 기존 documented 이미지·스캔 3건, 회귀 0) · 적용후 mmult 0 ·
  적용후 항등식 0 · `pytest tests/unit/` 110 passed · `test_deploy_assets`·`test_post_transition_golden`·
  `test_master_tables_golden` 통과. `test_kics_rules_golden`은 **의도된 이동** 3건(rule10 KR0050
  GREEN→SKIP·rule8_life KR0097 SKIP→GREEN·rule8_post SKIP→GREEN)이라 `--update` 재생성.
- **UH-8(금리민감도 provenance) 종결**: `kics_rate_sensitivity_provenance.json` 87셀 발행 +
  발행기 `scripts/emit_rate_sensitivity_provenance.py` 상주. `validate_data_contract.py` RED=0 유지,
  validation이 CHECK 2 2a(iv) 배선하면 됨.
- **신규 상주 스크립트**: `scripts/fix_20260820_post_transition_sandwiched.py`(티켓 6쌍+예별 3분기,
  값별 raw 인용은 docstring) · `scripts/fill_post_transition_adjust_items.py`(22/23후 전수, 매 분기
  재실행 안전) · `scripts/emit_rate_sensitivity_provenance.py`. 진단 probe 6종은 `scripts/_probes/`.

**남긴 잔여 (다음 라운드 인계):**
1. **0값 세부위험 행이 통째로 빠지는 별건 — 31(회사,분기).** 29-35 중 일부 행 결측 17건 · 36-40 중
   일부 결측 14건, 거의 전부 **원천 값이 0인 행**(item32·item40이 압도적). 행이 없으면 mmult·census가
   그 부모를 통째로 건너뛴다(= 이번 KR0097 2023.2Q가 딱 그 케이스라 raw 근거로 행 신설했다).
   재현: `scripts/_probes/probe_subrisk_rowcensus.py`.
2. **조정항목 보류 7건** — KR0071 2023.1Q·2024.3Q·2025.3Q(기타요구자본=관계회사 환산치가 ②표/③표로
   갈려 결합 불명, 추정 금지) · KR0071 2024.4Q + KR0005 2024.4Q(image-only, 기존 documented) ·
   KR0002 2024.3Q·KR0082 2023.3Q(raw 행에 값 칸 자체가 빔) · KR0032 2023.1Q(item15후 결측).
**✅ `insurequant_master_tables.xlsx` 동기화 완료 (cherry-pick).** owner 상시 지시(`inbox/_resolved/
20260819T0500Z` L119: *"전체 재생성 금지 — 해당 시트만 cherry-pick 동기화할 것"*)에 따라
`build_master_xlsx.py`는 **쓰지 않았다.** 신규 상주 도구 `scripts/sync_master_xlsx_sheet.py`로
`K-ICS공시` 시트만 셀 단위 반영 — **변경 셀 260 · 추가 행 1 · 삭제 0**(전부 `값_적용후` 컬럼,
`값` 컬럼은 한 칸도 안 건드림). 사후 독립검증: K-ICS공시 18,879행 × 9열이 마스터와 **셀 불일치 0**,
나머지 7개 데이터 시트 **값 기준 완전 동일**, 수식 0개·파트 17개 유지(피벗/차트 유실 없음).
덤으로 `요약` 시트 행수가 실측과 어긋나 있던 것 보정(17BS 6,953→6,855 · 배당 1,924→2,043 —
다른 레인이 시트를 cherry-pick 한 뒤 `요약`을 안 고쳐서 생긴 stale, 설명 칸은 손대지 않음).

---

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
- [x] **(종결 2026-08-20) 36-40 재추출** — 주장 224건은 stale. 실측: item19 보유 484 (사,분기) 중 36-40 결측 144건인데 **133건이 홀수분기**(세부표는 짝수분기 공시가 표준 = 구조적 정상). 진짜 후보는 **짝수분기 11건뿐**이고 KR0051(1)·KR0079 미래에셋(6)·KR0080 AIA(4) — 전부 이미지/스캔 원천으로 아래 KICS-IMG 코호트와 동일. 원래 남은 항목: gold anchor: 하나손해 2025.4Q(시장 76,839 / 금리 30,358 / 주식 62,491 / 부동산 2,643 / 외환 12,483 / 자산집중 5,251 백만원) + 삼성생명 2025.4Q. 도구 `fill_market_subs_from_pdf.py`(words-coordinate 전략) 또는 MD 분단표 합치기. **게이트: 19_market 행렬합 rel<2%** 통과분만 적재. 생보도 동일 스캔 후 일괄.
- [ ] 진짜 미공시 (사,분기)는 raw 표 부재 명시 회신 → validation `MARKET_BREAKDOWN_EXEMPT` 등록.
- [x] **(종결 2026-08-20) 2026.1Q 29-46 backfill** — 실측 **20사가 29-46 보유**('전무' 주장은 stale). 원문:(8_life 29-35 + 시장위험 36-46) → 29-46 backfill.
- [x] **(종결 2026-08-20) census 미싱셀** — 게이트 실측 `MISSING_CELLS(RED)=2`(28건 주장은 stale). 원문:(MD parsed인데 JSON 추출 누락): 미래에셋 7분기·코리안리 6분기·동양·하나생명 등 + 2026.1Q 6사(한화손해·롯데손해·삼성화재·하나손해·미래에셋·동양). 명단 inbox 20260611T2200Z.

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
- [x] **(종결 2026-08-20) KR0049 악사손해 2026.1Q** — '게이트 잔여 RED 4건' 주장 stale. 현재 RED=12는 KR0087·KR0097·KR0079 셋뿐이고 **악사는 없다**(`TODO.md` L10).

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

- [x] **(종결 2026-08-20) RS1–4 룰** — `TODO.md`에 *"validation: RS1–RS4 룰 구현, 게이트 RED=0"*로 이미 완료 기록됨(2026-06-10). 원문: 마스터 ready 회신 = `inbox/validation/20260610T0830Z__parser__ALL__rate_sensitivity_master.md`. (RS1-4는 통과했으나 정식 룰 구현 확인 잔여.)
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
