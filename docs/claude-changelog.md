# Cross-stage Changelog

> Last updated: 2026-10-24 · Stage: cross-stage
> Index: CLAUDE.md (5-stage) · Stage histories: docs/changelog_<stage>.md

Cross-stage entries only (gathering / pushing / refactor / cross-stage viz / 폴더 정리). Stage-specific history lives in `docs/changelog_<stage>.md`. See `CLAUDE.md` for the 5-stage index.

Convention: latest few entries detailed; older compressed to 1-liners (git log has commit-level detail after first push 2026-05-25).

---

- **2026-10-24 2026.3Q 푸시 분할 결정 반영(owner 「dart 관련 항목들부터 먼저 push 하고 그다음 경영공시 push, kidi 는 늦게 올라올 것」)**: 계획 `docs/flows/round_2026_3Q_plan.md` 에 §1-1 을 추가했다. 1차 = DART 묶음(PL 24사·CSM 23사·BS 24사·배당 + 기존 분기 칸, 11/24 전후), 2차 = 경영공시 묶음(K-ICS·PL/BS 15사 + 재보사·라이나·ILP·자본증권, 12/2), 3차 = KIDI 도착 뒤 NB 배수 소배포. 이전 권고 「한 번에 푸시」는 폐기. 부작용: 분기 지평이 5개 마스터 최댓값에서 파생돼 1차에서 경영공시 소스 칸이 hole RED 로 읽힌다 → validation 에 「대기 선언」(칸 단위·매 실행 재검산·2차에서 만료) 설계 티켓 `inbox/validation/20261024T0658Z…` 발주. main 배포는 단계마다 owner GO.

- **2026-10-24 2026.3Q 수집 계획 작성(owner 「3분기 공시 뜰 때인데 뭐뭐 가져올지 계획 짜놔」; 읽기 전용 조사 7개 영역 + 비평 1회, 수집은 시작하지 않음)**: 지난 3번의 3분기(2023·2024·2025)와 2026.1Q 를 데이터셋별로 실측해 `docs/flows/round_2026_3Q_plan.md` 에 정리했다. 결론: 3Q 경영공시는 간이 양식(쪽수 중앙값 31 대 2Q 65)이라 금리민감도·금리위험 시나리오(41-46)·유지율·손해율 가정·CSM 민감도·경영효율은 수집 제외, 헤드라인 1-28·47-54·PL·BS·CSM·ILP·배당·자본증권은 수집, 하위위험(29-35)은 경과조치 적용 20사 의무 + 자율 약 3사(기대 23±2), 시장위험 분해(36-40)는 12사 의무 + 자율 4사(기대 16~19), 당기순이익은 `PL_breakdown` 항목 24 로 47사 전부(DART 24사 + 경영공시 15사·재보사 8곳). 비평이 바로잡은 사실: DART 3Q 제출사는 24사. 새로 확인한 함정: 분기 지평이 5개 마스터 최댓값에서 파생돼 일부만 3Q 를 담으면 HOLE·MISSING_FILER_CELL RED(한 번에 푸시), 서울보증이 7번째 분기를 적재하면 K-ICS census 정규 공시사로 뒤집힘, `verify_q2_disclosure_content.py` 가 없는 `pdf/` 를 읽어 빈 폴더에서도 exit 0, 재보사 수집 스크립트가 저장소에 없음, 메리츠화재 2026.2Q 적용후 항목 2·3·28 이 적용전 복사로 라이브에 올라 있음(티켓 `20260919T1400Z`). owner 결정 대기 항목은 문서 §9 에 모았다(3Q 푸시를 막는 5건 · 수집 범위 7건 · 준비 승인 9건 · 이월 7건).

- **2026-10-24 임시 파일·스크립트·낡은 문서 정리(owner 「문서 충돌·outdated 싸그리 정리, 임시파일·임시스크립트 전부 삭제」; 오케스트레이터 + 읽기·정정 에이전트 3개)**: ① 삭제: `scripts/_probes` 1,580개(분기 라운드가 부르는 5개와 README 만 남김), 날짜가 붙은 일회성 스크립트 277개(`fix_2026MMDD_*`·`bspl_apply_*`·`bspl_followup_*`·`bspl_granularity*`·`reinsurer_resweep_*`·`*_2026MMDD` 적재기), `data/_derived` 끝난 증거 폴더·`_probe_*` 4,890개(추적), 추적되지 않던 백업(루트 xlsx `.bak_*` 7개, `artifacts/pytest_tmp` 1.76GB, `_derived` 백업 폴더) 약 3GB. 코드·테스트·골든·HTML 이 읽는 파일, `*_parts` 입력, `_patch*_2026q2_KR*` 입력, 코드가 근거로 인용한 증거, 결정 대기 중인 KDB 재적재 증거는 남겼다. 지운 파일은 `git log --diff-filter=D -- <경로>` 로 삭제 커밋을 찾고 `git show <커밋>^:<경로>` 로 되살린다(추적되지 않던 백업은 복구 불가). ② 문서: 규칙 문서(`CLAUDE.md` §4·§5, 에이전트 프롬프트, 룰 카탈로그의 허용오차·룰 ID, 배포 절차, jp 레인 안내, 페이지별 fetch 표)와 `TODO*.md`(낡은 「미커밋」·「GO 대기」, 끝난 항목은 아카이브로 무수정 이동)를 실제 코드·게이트·측정에 맞췄다. 방치 티켓 12건을 하나씩 재측정해 5건(`20261008T1427Z` · `20261009T0330Z` · `20261009T0700Z` · `20261012T1820Z` · `20261019T1400Z`)을 종결하고 남은 일은 `TODO_parser_ifrs17.md` · `TODO_designer.md` 로 옮겼다(나머지 7건은 부분 처리 또는 미처리라 열어 둠). 개인 문서(pptx·docx·xlsx·연락망·`scratch_ppt`)는 건드리지 않았다.

- **2026-10-22~24 orchestrator 최신 비교열 적재·배포 4회전(owner 구두 GO 뒤 이 PC 격리 sparse 클론에서 main 배포, 작업 브랜치 push 마다 풀 훅 gate-clear)**: ① 10-22 교보생명 KR0073 CSM·PL 한 기준 적재(`3e53aef8`) + 2023.3Q 단일분기(`5f818b59`) → main `1a73d4c2`, OCI 13칸·BS/ILP 9칸(`e01f1395`·`59e6e459`) → main `66af419c`, 7사 19버킷 최신 비교열(`acdb2fe9`) → main `80ba3c1d`. ② 10-23 11사 21버킷(`5419a817`) + READY-25 9사(`afea4342`) → main `72999c88`; owner 결정 D1~D3 4사(KB라이프·롯데·ABL·현대해상 FY2023, `b1187788`·`90be97e7`) → main `7e00a62a`, KDB생명은 연결 기준 혼합이라 보류. ③ 10-24 이웃 옛 판 칸 점검 1~4차(`fc41f505`·`a20976cf`·`fb3960f9`·`f25ed8b8`) → main `8eb01df`(라이브 6파일 바이트 일치, build_id `74a9353f`). ④ 10-22 jp 레인을 이 브랜치에서 분리(`da2c8572`, 브랜치 `lane/jp`·워크트리 `../iq_jp`)하고 배포 스크립트에 `--only <prefix>` 를 추가(`2fa7a046`).
  단계별 수치·게이트는 `docs/changelog_parser_ifrs17.md` 14~25차 · `docs/changelog_publishing.md` 2026-10-22~24 · `docs/changelog_validation.md` 31~33차. owner 결정 대기 5건은 `TODO.md`. 같은 날 TODO·archive 문서 정리(낡은 Status · 끝난 항목 이동, 각 `docs/todo_archive_*.md` 맨 위 「문서 정리로 이동」 절).

- **2026-10-19 밤 접근성 2차(owner 「일본은 보류하고 접근성 C8~C17 진행」; 에이전트 2개 · 약 1시간, 구현 35분 + 검증 25분 상자; push `7fc4971f`, main 배포 `3a91a4ea` 완료·라이브 4파일 바이트 일치)**: C8 · C9 · C10 · C11 · C12 · C13 · C14 · C15 · C17 구현. C16 은 WCAG 목표 결정 대기, 일본 오류 제보 위젯 제외는 보류. 구현은 `docs/changelog_designer.md` 2026-10-19 (밤 2) 항목. 전날의 8시간 교훈대로 워크플로우 없이 구현 1 + 좁은 검증 1로 끝냄.

- **2026-10-19 낮~밤 owner 후속(「선택기는 조사 추천대로」 「접근성 추천대로」 「오류 제보 내부접속 제외」; 워크플로우 2회 · 에이전트 약 22개; push `a8d9f193`, main 배포 `5221a1b4` 완료·라이브 7파일 바이트 일치)**: ① 손해율 비교 단위 선택기 + 위험보험료 단위환산 100배 오류 정정 + 반올림 half-up 통일(compare 93칸 +0.1) + 마스터 대조 테스트. ② 오류 제보 위젯 내부 접속 제외. ③ 접근성 C1 · C2 · C3 · C4 · C6. 구현은 `docs/changelog_designer.md` · `docs/changelog_publishing.md` 2026-10-19 (밤) 항목.
  운영 교훈: 후속 워크플로우가 약 8시간 걸렸다(a11y 구현 106분 → UX 검증자 라운드당 약 108분 x 2 → 문서 한 줄 정정 에이전트 63분, 모두 직렬). owner 가 「디자인 변경에 왜 이렇게 오래」 라고 질책했다. 검증은 범위를 좁히고 시간 상한을 두며, 마지막 C1 수정은 오케스트레이터가 직접 단순화(옆 삼각형 → 400ms 유예)했다.

- **2026-10-19 owner 결정 반영 + 후속 처리(구두 승인 · 동시 에이전트 최대 3 · 독립 검증 포함; push 8851145b, main 배포 f96f06b0)**: ① 규칙: 동시 에이전트 수는 고정 상한이 아니라 메모리·CPU 여유로 정함(`CLAUDE.md` §10), main 배포는 기본이 오케스트레이터 직접(owner 구두 GO 뒤)이고 push 가 막히면 2회 시도 후 Termux 명령·배치파일 제시(§11), Status 항목 5줄(§2), §8 에 sync 스크립트의 수식 REFUSE 단서 추가(워크북 수식 0개 실측). ② 문서: 별첨 수집 범위(경영공시 별첨 수집 · DART 금지)와 손보 수집 경로(2026.2Q 사별 사이트 스크립트 · 생보 협회 일괄 zip) 정정, 끝난 handoff 2개와 mockups/compare 를 `docs/archive/` 로(force-add), `.githooks/pre-push` 소요 문구 약 11분. ③ 정리: `.claude.json.tmp.*` 81개(4.3MB) 삭제. ④ 조사 `docs/loss_ratio_comparable_unit_20261019.md`: 최소 비교 단위 = 구분×포트폴리오 한 줄(생보 4 · 손보 4), Non-Par 한 줄은 생보에서 아직 왜곡. ⑤ 티켓: validation `20261019T0200Z`(카카오페이손보 잎 합 대 합계 행 · 이상치 4건), designer `20261019T1400Z`(a11y 18건). ⑥ 첫 인용 기사 확인(조선비즈 2026-10-18), 기사 수치 17개 마스터와 일치.
  구현은 `docs/changelog_designer.md` · `docs/changelog_publishing.md` 2026-10-19 항목. 모델 · 비용: 에이전트 약 16개(Sonnet 계열), 토큰 약 280만, 세 번의 워크플로우.

- **2026-10-18 TODO 일괄 처리(owner 「샥 돌려봐, 난 자고온다」; 20개 에이전트 · 동시 3개 · 독립 검증 포함, 푸시·배포는 하지 않음)**: ① 정리 fan-out 1차: 캐시 · 빈 폴더 43개 삭제, 추적되지 않는 임시 · 증거 외 파일 1259개(10.5GB)를 `C:/Users/sangwook.cho/insurequant_quarantine_20261018` 로 이동(삭제 아님, MOVED.json · README.txt), 추적 백업 2개(`CSM_waterfall.backup.json` · `insurance_pl_breakdown.json.bak_pre39`) 제거, git status 체감 5초 → 1초 미만. 이동 후 추적 파일의 참조 0건 · 개인 파일 무손상 확인. ② 문서: `CLAUDE.md` · TODO_* · inbox/README · `.claude/` · docs 의 낡은 서술과 깨진 참조 113건 정정(보관본 · 이력 무수정, 규칙 의미 변경 0 독립 확인), `.githooks/pre-push` 훅 소요 문구 18분 → 약 11분. 규칙끼리 어긋난 곳 10건은 owner 판단으로 `TODO.md` 에. ③ 손해율 구분 선택기 · 3분기 팝업은 `docs/changelog_designer.md`. ④ reach out 후보 신규 28건(미추적 파일, 발송 · 초안 없음). ⑤ 사업성 평가 `docs/business_assessment_20261018.md`(GA4 · 서치콘솔은 못 읽어 필요한 입력 목록만).
  모델 · 비용 한 줄: 에이전트 20개(Sonnet 계열, 손해율 · 팝업 · 정리 · 문서 · 후보 · 평가 6줄기), 토큰 약 400만, 소요 약 3.4시간. 검증이 잡아 고친 것: 손해율 IFRS17 합계 없는 사업구분의 죽은 선택지 · 근거 약한 팝오버 예시, 사업성 보고서의 과장 표현 다수.

- **2026-10-14 orchestrator 서브에이전트 정의 보강 + 문서 회전(owner 지시 「정의에 빠진 것 채우고 문서 리팩토링」, 토큰이 크게 들어 워크플로우는 감사 단계에서 중단)**: ① `.claude/agents` 6개(downloader · parser-kics · parser-ifrs17 · validation · designer · publishing)에 최근 2주 기록으로 확인된 빠진 규칙을 채웠다 -- 공통(python 은 스크립트 파일로만·고아 프로세스는 내 PID 만 종료, PC 한도 RAM 15.5GB, 커밋은 파일 명시·개인 문서와 50MB 초과 제외, TODO Status 3개 규칙), 레인별(최신 비교열·최신 공시 전기 칸 우선과 gold 영속 경로·3개월 열 오적재, `--refresh` 재실행 금지·판 선택 등재부, 재보사 8곳·별첨·현행판 대조·서울보증 종결, 독립 재독 감사·골든 `--update` 전 원인 증명, 공시 이름 그대로·회사코드 비노출·`?iq_internal=1`·JSON 플래그 먼저, 마스터 재동기화 순서·새 배포 파일 7곳·격리 클론 배포). 낡은 사실도 고쳤다: 읽는 순서 공통 틀을 레인별로 구체화, 상관행렬 경로(`src/solvency/validation/kics_json_rules.py`), 훅 18분 → 약 11분, downloader 소스 5개 → 4개 + 재보사, designer 4페이지 → 5페이지. 감사 원본(7명, 증거 포함)은 워크플로우 `wf_5091d231-d40` journal.
  ② 문서 회전 도구 `scripts/doc_rotate.py`(+ `tests/test_doc_rotate.py`)를 만들어 changelog 8개를 「최신 달과 그 전 달」만 남기고 `docs/changelog_archive/<stage>/<월>.md` 로 무수정 이동(343항목, 합계 약 2.0MB → 0.8MB, 독립 검산: 원본 줄 손실 0), `TODO_designer.md` Status 15개 → 3개와 배포 끝난 hand-off 절을 archive 로, 낡은 인용(소진율 도넛 `:783-789` 등) 교체, `docs/agents/doc-style.md` 를 실제 규칙으로 재작성, 루트 TODO 의 「inbox 열린 4건」을 실측 10건으로 정정. 월 1회 `doc_rotate.py --check` → `--apply`.
  ③ 같은 날 후속(워크플로우 없이 직접): 한 줄이 500자 넘는 열린 일 6줄을 ①②③ 하위 항목으로 분리(`TODO.md` 2 · `TODO_parser_ifrs17.md` 2 · `TODO_parser_kics.md` 2; 공백 외 글자 변화 0을 기계 검산), 참조 0건인 5~6월 일회성 문서 8개(`collection-status-*` 2 · `MORNING_REPORT` · `ir_visual_aids_research` · `pl_gold_needed` · `viz_proposals_fresh` · `viz_prototype_*` 2)를 `docs/archive/2026-06_oneshot/` 로 `git mv`(참조가 있는 `LESSONS`·`roadmap`·`*_matrix` 는 그대로), `docs/README.md` 색인 신설, TODO 에 인용된 경로 존재 점검으로 낡은 경로 4곳 정정(`TODO_validation.md` 유지율 티켓이 이미 `_resolved`, `TODO_downloader.md` `src/bonds/fsc_client.py` 는 `data/_archive/` 보관본, `TODO_parser_ifrs17.md` 상대 경로 4개). inbox 열린 10건은 `status_report.py --fast` 와 `TODO.md` 가 일치.
  미완: 열린 일 항목 하나하나의 실제 완료 여부(경로 존재와 inbox 수만 기계 대조했고, 골든·RED 수치 같은 주장은 안 돌려 봄).
- **2026-10-13 새벽 orchestrator 복원·적용·배포 라운드(owner 취침 중 「라이브 push 까지 쭉」, 작업 브랜치 `5414c81e` · main `970259b8`)**: ① 소진율 도넛·Forward Outlook 복원(발행현황 패널 유지, 3시트·루트 JSON 3개 재공개; 설계 `K-ICS.html` 순서 = 도넛 → 발행현황 → … → 전망). 신종 분류는 **발행사 처리 기준**(하나생명 제1회·교보 2024-11 → 기본자본형, 하나생명 기본자본 소진율 0.0 → 238.2, DB손보 5건 기본자본형 owner 확정), 보완자본 분자의 **경과조치 기발행 차감 = 채권 원장의 2022-12-31 이전 발행 중 첫 콜일이 기준일 이후인 잔액**(47사 독립 감사 PASS: 메리츠 37.5 · 흥국생명 37.0 · 농협생명 21.1 · 아이엠라이프 70.4, 정의 `data/_derived/capital_utilization_definition_20261012/definition_memo.md`). 독립 감사 지적 반영: 33사 기본자본 인정한도 인쇄 15% → 10%, DB손해 제1·2회 콜 금액 비움(원문 상충), 하나손해 추정 행, 예별·롯데 전망 가짜 개선 제거(자본잠식 해는 null · 툴팁 「자본잠식」 · 음수 △), 375px 도넛 툴팁.
  ② 「최신 공시 직전 컬럼 우선」 원칙 드라이런 2건(K-ICS · IFRS17) 후 owner 「확실히 검산 닫히는 것만」 적용: K-ICS 16블록 65칸(보류 10, 박제 예외 2 해제, 재작성 장부 +29, RED 56 → 54) · IFRS17 249셀(CSM 27 · PL 157 · BS 65, 3개월열→누적 정정 14셀, 예외 해제 10줄, gold-overlay로 영속화); 둘 다 validation 이 원 공시에서 전수 재독(65/65 · 249/249). 파생 산출물(NB 12칸 · 패널) 재생성.
  ③ 배포: 풀 훅 gate-clear 후 작업 브랜치 push, main 은 이 PC 의 격리 sparse 클론(`git clone --no-checkout --local` + remote 를 GitHub 로 교체 + sparse-checkout 로 스크립트만 체크아웃; MSYS 경로변환 때문에 sparse 패턴은 `.git/info/sparse-checkout` 에 직접 씀)에서 `android_push_and_deploy.sh --from-origin` 실행(기존 24 · 신규 6 파일), 라이브 확인(manifest `99c7ead7` · 값 일치 · 콘솔 오류 0). 한도 사고: 에이전트 4개 동시 + 질의가 겹쳐 API 사용량 한도(23:50 초기화)로 전원 중단 → 초기화 직후 재개(K-ICS 파서는 마스터 일부 적용 상태에서 끊겨 계획 대조부터 재시작).
- **2026-10-12 오후 orchestrator 화면·분류 결정 라운드(작업 브랜치 push 직전)**: owner 가 신종 분류 판단이 들어가는 숫자는 건조하게 못 뽑는다며 K-ICS 소진율 도넛과 Forward Outlook 을 화면에서 내리게 했다 → 발행연도별 신종자본증권(아래)+후순위채(위) 누적 막대와 큼직한 셀 2개(`securities_summary`: 최근 발행금리·총발행액 '23~·가장 가까운 콜 1건)로 교체(`e2c72cd`·`1dd02d5`, 막대 원천 `kics_capital_securities_timeline.json` `5a2b58f`), 소진율 2종·전망 시트는 다운로드 목록에서만 임시로 내림. 앞서 규정 근거 재정의(Opus, `c3ebcc3`)·한화생명 분류 추정 검증(항목 2·3 시계열)은 데이터에 남기되 화면 비노출, 분류 전수조사는 내부 작업(parser-kics `1230Z`). 공유 버튼 기록(`b3a2ae2`·`18bd037`, 디자인 전용 배포 `deploy/design-20261012`: `iq_internal` 이 브라우저에 남아 있으면 기록하지 않는다는 점이 owner 시험 무기록의 원인) · IFRS17 예실차 독립 섹션·시트(`356b7a8`·`0397ce4`) · 재보사 PL 7칸·처브·분할표(`3bf1690`)·퍼시픽/악사 K-ICS 칸(`acd351a`)·validation 등재(`f0535af`)·손해율 세그먼트 표준화·gz(`268002b`)·최종 재동기화(`538cbe7`~`263f760`). PC 부하: 멈춘 python3.13 출력 폭주 프로세스 4개(CPU 수 시간분) 강제 종료.
- **2026-10-12 orchestrator 재보사 전면 재스윕 + 화면 지시(owner 취침 중, 작업 브랜치 push)**: owner 가 스위스리 2025.4Q 화면의 「미공시」를 지적 → 원문 대조 후 재보사 8곳 재스윕. ① 손해율 가정(손해율 마스터에 재보사 행이 0 이었음 — PDF 격자 표를 기존 추출기가 못 읽음): master_loss_ratio +1,904·risk_premium +9,152·claims_ae_ratio 37→44사(`46f74f2`), 패널 `ae` 블록·xlsx(`66e6156`) ② PL 투자손익/영업이익/영업외손익 +303·BS +49·R1 정정 15행(`3727438`), 인쇄된 0 7칸은 owner 승인 전 보류 ③ CSM 계열: RGA·하노버 2025.4Q·퍼시픽 2023.4Q 워터폴 등(`57b7d78`) ④ 자본성증권 소진율 재확인: 8곳 발행 0 확인(마스터 불변, `d0514f5`) ⑤ validation: 재보사 PL 계보 허용(`6cb0577`), 게이트 PDF 텍스트 캐시로 훅 26분→약 11분(`c7f676b`) ⑥ 화면: K-ICS 시나리오 컬럼명을 공시 이름으로·듀레이션 주석 ? 안으로(`1a9a105`), IFRS17 통합 현황 박스·NB 표(`46d4a3a`·`8c8b43b`), 보험금 예실차비율 표(`8c07a59`), 모바일 재보험·보증 접기·홈 KPI 보조 문구 제거. PC 부하: 에이전트 종료 뒤 남은 python3.13·find 고아 프로세스(CPU 수 시간분)를 정리. 상세는 각 stage changelog.
- **2026-10-11 밤 orchestrator 마감 라운드(push 직전)**: ① 재보사 PL 항목 4(`원수CSM상각`, 전업 재보사는 사실상 수재 CSM 상각) 17버킷 + 라이나 9버킷을 감사보고서 주석에서 적재 -- `PL_CSM_AMORT_VS_WATERFALL` 예외 등재 대신 데이터로 닫음(`0a7632e`·`59dc684`) ② 라이나(KR0074) CSM 백필 전 분기 중 2023.3Q~2026.2Q 9분기(워터폴 +54칸·상각 스케줄 2025.1Q/2Q +20행·값_당분기 20칸, `6081de1`·`28b9e23`·`396faff`), 2023.1Q·2Q 는 옛 기준만 인쇄돼 보류(owner 결정) ③ 상각 스케줄 빌더가 전기말 표를 뽑던 결함 수정(`_current_period_twin`, 15사가 아니라 18사, 2025.4Q 172칸 값 정정, `cf66dce`) ④ validation: 항목 4 계보 허용·승인 등재 4건(`1db7c2d`) ⑤ designer: 재보사 PL 라벨 「원수」 제거(`dcac354`) ⑥ publishing: xlsx 4시트·NB 배수 마스터(라이나 실제 배수)·csm_combo/compare·public_exports(`5d320c9`·`812b007`). 홈 KPI 업계 총 기말 CSM 은 하드코딩 없이 `panel_csm_combo` 같은 분기 합(47사, 캐롯 제외, 하노버 직전 값)으로 계산(`49f8573`·`211e868`). 상세는 각 stage changelog.
- **2026-10-11 validation 23차**: PL 항목 4 재무제표 주석 계보 허용(`PL_FS_NOTE_LINEAGE`) + 법인세 0 확정 3칸 + 하노버 2025.3Q PL 원천부재 장치 `_PL_SOURCE_ABSENT` -- 데이터계약 RED 34→11. 상세 `docs/changelog_validation.md`.

> 보관: 이전 달 항목은 `docs/changelog_archive/cross_stage/` 에 월별로 무수정 보관한다(관리 `scripts/doc_rotate.py changelog`, 현행 = 최신 항목 달과 그 전 달).

## 2026-10-11 — 재보사 8곳 K-ICS 스윕 + IFRS17 섹션 3 콤보(발생사고요소) + 모바일 손해율 curve (orchestrator, 작업 브랜치 push `6841689`)

owner 지시: 외국 재보사 국내지점 7곳 + 마이브라운(KR1101~KR1108)을 K-ICS 마스터에 편입하고(기존 39사 25,522행 git HEAD 와 동일 유지), 새 8곳이 든 마스터를 라이브에 올리기 전에 index/compare 를 생보·손보·재보험사·보증 3분류로 나누며, IFRS17.html 섹션 3 을 묶음·누적 막대 콤보(잔여보장요소 + 발생사고요소)로 보강.

- **K-ICS 스윕**: parser-kics 단계 1~11(+ 퍼시픽 2023.3Q·4Q·2024.3Q, 스위스리아시아 2023.4Q 완성본, 금리민감도·듀레이션갭 재보사)·validation 단계 6~10. 새 게이트 장치 3종 — `_IDENT_ISSUER_INCONSISTENT`(룰 2·4·5·6 잔차 박제), `_CENSUS_SOURCE_ABSENT`(census 원천 부재, raw sha·매니페스트·근거 원장 재검증), `rs_pinned_exemptions`(금리민감도 RS1·RS5). 모두 「근거가 깨지면 다시 RED」. 승인 등재: 자기모순 21·원천 부재 8·census 8·퍼시픽 2023.3Q 1·예별 2025.3Q 법인세 1·금리민감도 5.
- **IFRS17 LIC**: 새 마스터 없이 `insurance_liability_portfolio.json` 항목 10~15(발생사고요소, 억원) 적재 + 2024.4Q·2023.4Q 백필(BEL·RA 는 DART 주석에 2023.1Q 부터 공시돼 있었음 — 「2025.1Q 부터」는 우리 마스터의 한계였음), 재작성 3사 FY2024 비교열 통일 + 사이드카. IBK연금 2-4 정정 48칸.
- **화면**: index·compare 3분류(`data/company_segment.json`), 섹션 3 콤보(CSM 키컬러·BEL→RA→CSM 표·기준 토글 따라 기간·2023 연말 구성 없는 회사 처리·재작성 †), compare 모바일 손해율 curve 안 A.
- **교훈**: ① 검증 단계에서 데이터계약 게이트만 재면 도메인 게이트(금리민감도·듀레이션갭) 차단을 놓친다 — push 훅 전체를 돌려야 한다 ② 에이전트가 `python -`(stdin heredoc)로 부른 맨 python 이 고아 CPU 스핀을 두 번 만들었다 ③ 개인 문서·77MB 파일은 전체 커밋 지시에도 add -A 금지(`data/loss_ratio/risk_premium_vs_expected_claims.json` 77MB 가 `78471c0` 으로 올라감 — 후속 판단).
- 라이브 `main` 배포는 owner 가 폰에서(`scripts/android_push_and_deploy.sh --from-origin --branch fix/csm-product-segmented-columns`).

---

## 2026-10-07 — 문서·컨텍스트 정리 (orchestrator, owner 지시 "전반적인 리팩토링")

owner 지시: TODO·changelog 비대화, 모델 성능 향상으로 불필요해진 장황한 지침, 끝났는데 열려 있는 티켓을 정리.

- **매 세션 읽히는 문서를 줄였다.** 루트 `TODO.md` 85KB → 3.4KB, stage TODO 7개 합 277KB → 22KB. validation 세션 시작 독해량은
  CLAUDE+TODO+stage TODO+프롬프트 기준 약 207KB → 46KB, parser-ifrs17 은 약 209KB → 45KB. TODO 에는 열린 일·휴면·결정만 두고
  Status 는 최신 3개·항목당 3줄(`CLAUDE.md` §2 개정). 정리 전 전문은 각 `docs/todo_archive_*.md` 맨 위에 무수정으로 있다.
- **할 일이 아닌 것을 TODO 밖으로**: K-ICS 게이트 documented exception 등재부(340줄) → `docs/kics_gate_exceptions.md`(참조처 6곳 갱신),
  2026.2Q 라운드 절차 → `docs/flows/kics_quarterly_round.md`(다음 분기 재사용).
- **3개월 넘게 진척 없는 항목은 「휴면」 한 줄**로 내렸고, 실측으로 이미 끝난 것은 닫았다(kics 중복키 94 → 0, gold 3종 추적, KR0004 PL 96행, FY2026_Q1 MD 39개 등).
- **inbox 활성 10 → 4**: 검증 후 종결 6(answered 4 · KR0004 질문은 DART 감사보고서로 답 · 자기 앞 백로그 1은 TODO 로), 일부만 끝난 4건은 맨 아래 「현황」.
- **프롬프트의 낡은 사실 교정**(경위 서술은 축약, 룰은 유지): designer §5.1 이 걷어낸 부트스트랩 팔레트를 정본으로 적고 있었다 → 팔레트 B·다크모드 ·
  publishing §9 가 공유 폴더에서 `git checkout main` 하는 옛 배포 절차를 적고 있었다 → `launch_runbook` + 폰 스크립트 · 두 프롬프트의 fetch 표에
  없어진 `csm_waterfall_history.json` · 아카이브된 `normalize_bond_schedule.py`·`build_lotte_series.py`·`liability_extractor.py` 참조 ·
  downloader 의 이미 고친 "KNOWN BUG"·거꾸로 적힌 MG/예별 관계 · validation §1.5.1 "삼성화재 1분기만 값 있음" · `CLAUDE.md` §5 의 게이트 밖 anomaly triage.
  validation 44 → 28KB, publishing 33 → 17KB, designer 19 → 15KB.
- **IFRS17 도메인 문서** 50KB → 19KB(서문 조사기록·2026-05 PoC·Q1–Q9 문답은 `docs/domains/claude-agent-ifrs17_history.md` 에 무수정 보관).
  LOB 택소노미 절을 §4.3 으로 바꿔 `validate_master_tables.py` 주석의 dangling 참조를 살렸다. IR 교차검증 계약(휴면)은 `docs/agents/ir-crosscheck-contract.md`.
- **`test_claude_md_mandatory_gate_is_wired` 가 9/12 이후 조용히 skip 되고 있었다** — CLAUDE.md 개편 때 §6 제목에서 그 테스트가 찾는 "(mandatory)" 가 빠졌다. 제목을 되돌려 다시 돈다(1 passed).
- 서브에이전트 정의 `model:` 을 `claude-sonnet-5`/`claude-opus-5` 고정에서 `sonnet`/`opus` 별칭으로 — 최신 모델을 따라간다.
- 위생: 티켓이 재현 명령으로 인용하던 미추적 probe 스크립트 74개 + fix/추출 스크립트 2개를 추적, `*.bak_*`·`data/_derived/_probe_*` ignore,
  루트 백업 2개(git 이력 `32ebfb0^`·`a03ac79^` 와 동일 확인)는 ignore 된 `archive/2026-10-07_root_backups/` 로.
- changelog 는 세션 시작 때 읽지 않으므로 손대지 않았다. jp 도메인 문서·스킬·postmortem 은 이번 범위 밖.

## 2026-10-06 — AIA 항목46 100배 정정 + 공개 다운로드 내부 진단 문자열 룰 (orchestrator)

- AIA생명 2024.4Q 항목46 `3607646 → 36076.46`(원문 p25 직접 대조). 상세 `docs/changelog_parser_kics.md` 2026-10-06.
- `PUBLIC_EXPORT_INTERNAL_JARGON` 룰 신설(`validate_live_artifacts`). 상세 `docs/changelog_validation.md` 17차.
- 별건 관측: `RUN_PL_GOLDEN=1` PL 골든이 라이나 KR0074 2023.4Q coverage 1행으로 실패 중(이번 변경과 무관, 원인 미규명).

## 2026-09-22 — K-ICS 금리 듀레이션 갭 마스터 신설 (orchestrator, owner 지시)

**분모를 바꾸라는 지시에서 시작해 '어느 자산이냐' 를 확정한 라운드.** owner 가 듀레이션 갭의
분모를 순자산에서 자산으로 바꾸라고 했고, 1차 산출은 건전성감독기준 요약 재무상태표의
자산총계를 썼다. owner 가 *"나는 금리위험액 현황 테이블의 자산총계를 썼는데 뭐가 맞냐"* 로
되물어 확인한 결과 **owner 쪽이 맞다**.

근거는 범위 일치다. 분자인 순자산가치 변동은 금리위험 측정 대상(금리부자산·금리부부채)
에서만 나온다. 특별계정(변액)·주식·부동산은 이 표에 0으로 들어가거나 빠져 있어 분자에
한 푼도 기여하지 않는데, 전체 자산을 분모에 넣으면 그 자산들이 분모만 불린다. 삼성생명
2026.2Q 로 검산하면 명확하다(백만원):

| | 충격전 | 금리상승 | 금리하락 |
|---|---:|---:|---:|
| Ⅰ.자산총계 | 260,043,785 | 246,120,709 | 276,993,798 |
| Ⅱ.부채총계 | 244,352,153 | 230,257,404 | 262,489,017 |
| Ⅲ.순자산가치 | 15,691,632 | 15,863,305 | 14,504,781 |

- 자산D = (276,993,798−246,120,709)/(2%×260,043,785) = **5.94년**
- 부채D(자산대비) = (262,489,017−230,257,404)/(2%×260,043,785) = **6.20년**
- 갭 = 5.94−6.20 = **△0.26년**, 순자산가치로 직접 구한 값과 일치

260조 분모에서만 `갭 = 자산D − 부채D` 항등식이 닫힌다. 전체자산 481조를 넣으면 같은 분자로
△0.14년이 나오는데 이건 어떤 듀레이션 차이로도 분해되지 않는 값이고, 같은 분모로 자산
듀레이션을 구하면 3.21년(실제 5.94년)이 나온다. 희석 배율이 회사마다 달라(삼성생명 1.85배,
변액 비중 낮은 회사는 1.1배) 회사 간 순위까지 뒤틀린다.

### 산출물

| 파일 | 내용 |
|---|---|
| `kics_duration_gap.json` (루트 마스터) | 39사 × 짝수분기 7기 = **270셀**. 자산·부채 6시나리오(억원) + 자산D·부채D·부채D_자산대비·갭·부채자산비율 |
| `insurequant_master_tables.xlsx` 시트 `금리듀레이션갭` | 위 마스터 270행 × 23열 (`sync_master_xlsx_sheet.py` 로 신규 시트 추가, 나머지 시트 값 불변 검증 통과) |
| `scripts/extract_kics_irr_balance.py` | 경영공시 PDF·MD 에서 금리위험액 현황 표 자동 추출 |
| `scripts/build_kics_duration_gap.py` | 병합·역검산·듀레이션 산출 (`--check` 로 검산만) |
| `data/_derived/kics_irr_balance.json` | 자동 추출 254셀 |
| `data/_gold/kics_irr_balance_vision.json` | 표가 이미지라 사람이 읽은 16셀 + 출처 페이지 |
| `data/_derived/kics_duration_gap_audit.json` | 마스터 항목41~46 역검산 불일치 9건 |

순자산가치(시나리오별)는 `K-ICS공시` 시트 항목 41~46 에 이미 있어 새 시트에 중복해 담지 않았다.

### 추출 — 앵커로 묶어서 자기검증시킨 방식

표 양식이 회사마다 달라 라벨만으로는 못 잡는다. 그래서 **순자산가치 행의 숫자열이 마스터
항목41/43/44 와 일치할 때만 표를 채택**했다. 이 매칭 하나가 (a) 어느 표가 당기인지 (b) 컬럼→
시나리오 사상 (c) 단위 배율(억원/백만원/천원)을 동시에 확정한다. 그 위에 `자산−부채=순자산`
2차 검산을 얹었다. 세 가지 함정을 이렇게 넘겼다.

- **반복 글리프**(한화생명: `자산총계자산총계`) → 라벨 주기 dedupe
- **라벨이 숫자행과 다른 줄**(동양생명: `Ⅲ.` / 숫자 / `순자산가치`) → 앞뒤 라벨전용 행 합성
- **OCR 로 행 라벨이 통째 소실**(KB손보) → 라벨 없이 `A−L=NAV` 가 성립하는 행 쌍을 탐색

표가 **다음 반기 보고서의 `직전반기` 열에만** 실려 있는 경우가 있어 교차분기 탐색도 넣었다
(6셀 회수). 그래도 안 되는 16셀은 표 전체가 글리프 이미지라 원본 PDF 를 렌더링해 사람이 읽었다.

### owner 2차 지시 (같은 날)

**ⓐ 부채듀레이션의 정의.** owner 지적 — *"부채듀레이션은 D_L 에서 끝나야 하는 거 아냐? L/A 곱하는 건
듀레이션 갭 구할 때 곱해주는 거 아닌가"*. 맞다. 초판은 `부채듀레이션`(부채로 나눈 D_L)과
`부채듀레이션_자산대비`((L/A)×D_L) 를 **둘 다** 컬럼으로 냈는데, 후자는 갭 식 안에서만 쓰이는
중간항이라 부채 듀레이션을 재정의한 것처럼 읽힌다. 중간열을 지우고 식을 `갭 = 자산D − (L/A)×부채D`
로 적었다(시트 23→22열). 숫자는 안 바뀐다 — 같은 산술의 표기 문제였다.
`L0 ≤ 0` 인 회사(라이나생명·AIG손해, 책임준비금이 음수)는 `D_L` 만 비우고 갭은 채운다.
`(L/A)×D_L` 은 전개하면 `(부채_하락−부채_상승)/(2%×A0)` 이라 L0 가 소거되기 때문이다.

**ⓑ 라이나생명 2023.4Q PL 20칸.** owner 질문 — *"라이나생명 2023년 감사보고서 DART 에 있는데 왜
보험손익/투자손익 breakdown 이 마스터에 없지"*. 실측 결과 원문·raw 둘 다 있고 **아무도 이 분기만
손으로 안 넣은 것**이었다.

| | 2023.4Q | 2024.4Q | 2025.4Q |
|---|---|---|---|
| FS-API | status 013 (전 연도 동일) | 013 | 013 |
| tier1 HTML | 미인식('Ⅰ−Ⅱ' 도출형 IS) | 미인식 | 미인식 |
| 조치 | **없었음 → 이번에 충전** | `_GOLD_CELL_OVERRIDE` | `_GOLD_CELL_OVERRIDE` |

계보 사이드카가 `source_id=DART · source_file=null · NO_PUBLISHED_VALUE_IN_BLOCK ·
published_items=0` 로 정확히 그 상태를 적고 있었다. 값은 FY2024 사업보고서
(`20250409002702_00760.xml`)의 **제21(전)기 포괄손익계산서 + 주석23 전기 컬럼**에서 뽑았다.
산식은 같은 회사 2024.4Q·2025.4Q 기존 override 로 전부 재현해 확인했다:

- `item5` = 주석23(1) 원수 '비금융위험에 대한 위험조정 변동분'
- `item6` = 주석23(1) 예상발생 − 주석23(2) 실제발생
- `item11` = 주석23(1) 출재 실제 − 주석23(2) 출재 예상
- `item10` = 주석23(2) 출재 위험조정 변동분(인쇄 부호 그대로 — 기존 두 분기 관행)
- `item7`/`item12` = 잔차

**기준 주의: FY2023 은 FY2024 보고서에서 소급재작성됐다.** 자기 보고서(제21기) 당기순이익
463,997 vs FY2024 보고서 전기 비교컬럼 511,309 — 차이 47,312(백만원). 이미 마스터에 있던
`item4`(443,127.76)·`item9`(−7,365.047)가 후자 기준이라(`inbox/parser/20260815T1400Z`)
나머지를 같은 기준에 맞췄다. 섞으면 `item7`/`item12` 잔차가 두 기준을 합산한다.

게이트가 제 역할을 했다 — 값만 넣고 계보를 안 고치자 `validate_data_contract` 가
`MISSING_PROVENANCE` + `SOURCE_ID_LINEAGE_MISMATCH` 로 **RED=2** 를 냈다. 계보 셀 1개를
`OWNER_GOLD / scripts/build_pl_breakdown.py / gold_cell_override` 로 고쳐 RED=0 복귀.
(`emit_pl_provenance.py` 통째 재발행은 쓰지 않았다 — 지금 사이드카는 그 뒤에 DISCLOSURE 계보
155셀이 더해진 상태라 재발행하면 그게 null 로 되돌아간다. `--dry-run` 으로 실측 확인.)
`validate_master_tables` pl_bridge 3309P→**3317P**, 실패 31F 불변 → `master_tables_golden`
`--update` 재생성.

### 남은 것 / 부수 발견

- **산출불가 3셀** — 카카오페이손보 2024.2Q~2025.2Q. 금리부자산 충격전이 △18백만원이라
  분모가 성립하지 않는다(정상 부재, 추출 실패 아님).
- **AIA 2024.4Q 항목46 단위 100배 오류** — 억원 자리에 백만원(`3607646` vs 정답 `36076.46`).
  `36_irr` 룰의 경사 항이 `max(base−steep,0)` 이라 틀린 값도 맞는 값도 0 을 내놔
  **룰이 구조적으로 못 보는 자리**다. `inbox/parser/20260922T1200Z` 발주.
- **발행사 표 불일치 2셀** — BNP카디프 2023.2Q(6시나리오 전부 0.74%)·DB생명 2025.2Q(금리하락·
  금리경사 2열). 원문 대조 결과 추출 오류가 아니라 발행사 표가 스스로 안 맞는다. 공시대로 두고
  갭은 자산·부채 행 기준으로 계산(그래야 항등식이 닫힌다), 해당 행 `비고` 에 박제.
- **단서** — K-ICS 의 금리상승/하락 충격은 평행이동이 아니라 만기별로 크기가 다른 기간구조
  충격이다. 2%로 나누는 것은 owner 가 정한 근사이고, 순위·상대크기는 유효하나 절대 연수는
  참고치다. 이 단서는 마스터 시트 설명에도 적어 뒀다.

---

## 2026-09-21 — 배포 HTML 의 JS 런타임 게이트 신설 (validation → designer·publishing 에 영향)

**designer 가 화면 JS 를 고치면 이제 push 게이트가 그 JS 를 읽는다.** 2026-09-20 designer 커밋
`2dbc4ca` 가 `K-ICS.html` 의 `function IQP(){…}` **한 줄**만 지우고 호출부 2곳을 남겨 라이브
금리민감도 패널이 `ReferenceError` 로 하루 넘게 죽어 있었는데 **모든 게이트가 초록**이었다 —
데이터는 100% 정상이었고(고칠 셀 0개) owner 가 눈으로 잡았다. 원인은 단순하다: 저장소에서 배포
HTML 의 `<script>` 내용을 읽는 검사기가 **0개**였다. 불변식 1번을 데이터 축에서만 지키고 화면
축에서는 한 번도 지킨 적이 없었던 자리다.

- 신설 `scripts/validate_deployed_js.py`(`DEPLOYED_JS_UNDEFINED_CALL`) → 훅 §1f
  (`prepush_check.py` L409 호출 · L581 `blocked` · L600 exit 2). 브라우저 없이 토큰 분석,
  인-프로세스 **0.09초**. 현 트리 **오탐 0**(토큰 73,175 · 참조 3,627), 정의삭제 전수 변이
  **172/183(94%) 검출**. 회귀·변이시험 `tests/test_deployed_js_gate.py`(24케이스 8.6초).
- **scope 영향**: 루트 `.html`·`.js` 는 §0 에서 이미 전체 게이트 강제라 범위 목록은 안 고쳤다.
  즉 **designer 가 화면만 고쳐도 전체 게이트(≈8분)가 돈다** — 종전과 같다.
- **publishing 은 배포 후 한 줄이 늘었다**:
  `validate_deployed_js.py --git-ref origin/main` 이 RED=0 이어야 배포 성공이다(현재 RED=2 —
  복구 커밋 `197d15e` 가 아직 main 에 안 나갔다).
- 상세 `docs/changelog_validation.md` 2026-09-21(14차) ·
  포스트모템 `docs/postmortems/PM-20260921_kics_sens_iqp_referenceerror.md`(closed, 잔여 UH-26·UH-27).

## 2026-09-20 — 경영공시 PL 백필 라운드: 병합 선행조건 ②③④ 배선 (parser ① → validation ②③④)

cross-stage 라운드(parser-ifrs17 → validation → publishing)의 2번째 구간. ① 사이드카 실물 발행은 parser 가 끝냈고(`fa08bfe`, `PL_breakdown_provenance.json` 638→748셀, 마스터 실재 셀과 1:1), validation 이 ②③④ 를 배선했다. **⑤ 병합·⑥ push 는 미착수.**

- **②** `_SOURCE_LINEAGE` 에 `data/disclosure/`·`md_inbox/`·`data/_gold/`·`scripts/build_pl_breakdown.py` 등재 + `SOURCE_ID_LINEAGE_MISMATCH` 를 capital-securities guard **밖으로**(전 마스터 공통). 그 결과 `kics_rate_sensitivity` 138셀이 **처음으로 계보 검증**을 받는다(그동안 코드 주석만 "검사한다" 였다). `PL_breakdown` 은 `verify_provenance_sidecar` 호출처가 **0** 이었는데 published 731셀 검증으로 들어왔다.
- **③** `coverage_holes` 기대 그리드를 **셀 계보별로**. 경영공시(§2-1)는 LOB 분해를 안 싣기 때문에, 계보가 `DISCLOSURE` 인 (회사,분기)는 5항목만 기대한다. 계보 미상은 엄격 쪽(fail-closed). 오늘은 DISCLOSURE 셀이 0 이라 산출이 **바이트 동일**(골든 불변).
- **④** `CONCEPT_REGISTRY["pl_disclosure_vs_dart"]` 등재 + **리더**. 등재만 하면 다음 라운드에 또 새므로, DISCLOSURE 계보 셀의 항목을 allowlist 로 강제한다(위반 = `CONCEPT_MIXED_DISCLOSURE_INTO_DART` RED).
- 전임 세션의 "병합하면 census RED 0→80" 예측은 배선 후 **0→3** 으로 줄었다(real hole 118→6, 그중 3건은 이미 있던 서울보증 원천부재). 남는 3건은 경영공시 탓이 아니라 **DART 추출 갭**이라 parser 로 발주했다.
- 검증: `validate_data_contract` RED=0 YELLOW=123(불변) · `--selftest` 57→**69** · `validate_master_tables --no-build` SUMMARY 불변 · `prepush_check.py` FULL 범위 gate-clear. 마스터 JSON·xlsx 미수정, push 없음.
- 상세: `docs/changelog_validation.md` 2026-09-20 (12차) · 회신 티켓 `inbox/parser/20260920T1500Z__validation__ALL_2023.1Q-2026.2Q__disclosure_pl_merge_authorized.md`.

---

## 2026-09-14 — jp 프리뷰 라이브 배포 · 폰 배포 스크립트 rot 2건 · 훅이 리눅스에서 무력

### 1. 라이브 배포 (jp 프리뷰 4개)

owner 가 폰(Termux)에서 `scripts/android_push_and_deploy.sh --from-origin` 으로 실행. 배포 커밋 `e797f61`.

| 검사 | 결과 |
|---|---|
| 배포 커밋 name-status | 4파일, 전부 `jp-f9027362/` — **한국 자산 미포함** |
| 브랜치 `jp/<f>` ↔ `origin/main:jp-f9027362/<f>` 블롭 | 4/4 일치 |
| **라이브에서 받은 실제 바이트 ↔ 커밋 블롭** (`git hash-object`) | **4/4 일치** |
| `generated_at` | 2026-09-13T07:36:23Z → **17:08:02Z** |
| 화면 회사수 ↔ census posted | 15 = 15 |

"배포했다" 를 커밋 존재가 아니라 **라이브 바이트를 되받아 해시로** 확인했다. 2026-09-03 BOM 사고(리다이렉션이
파일을 조용히 변형)의 교훈이 그것이다 — 중간 경로가 바꿔치기해도 커밋 로그로는 안 보인다.

### 2. `scripts/android_push_and_deploy.sh` — 썩은 것 2건 (커밋 `f35603f`·`a8de4ae`)

- **번들 강제**: 브랜치가 이미 origin 에 있으면(클라우드 세션이 직접 push 하는 지금 구도) 번들은 불필요한데
  인자가 필수라 스크립트를 돌릴 수가 없었다 → `--from-origin` 신설. origin 에서 fetch/checkout 하고
  번들 검증·fetch·merge·push 를 건너뛴다. cherry-push 본체(격리 워크트리·블롭 해시 대조·`git checkout <branch> -- <path>`)는 그대로.
- **하드코딩 기본 브랜치**: `BRANCH=fix/csm-product-segmented-columns` 로 굳어 있었다. 인자 없이 돌리면
  **옛 브랜치가 라이브로 나간다**. 문서에 경고를 다는 대신 **기본값을 없앴다** — `--from-origin` 은 `--branch` 필수(없으면 중단),
  번들 모드는 `git bundle list-heads` 로 번들에서 읽고 refs/heads 가 0개·2개 이상이면 중단하고 `--branch` 를 요구한다.
  *기본값은 시간이 지나면 반드시 썩는다. 정답을 들고 있는 쪽(번들·인자)에서 읽는 게 갱신이 필요 없다.*
- **헤더 사용법이 틀렸다**: `git clone → cd → bash scripts/...` 인데 clone 직후 HEAD 는 `main` 이고 main 은
  slim(실측 55파일, `scripts/` 없음)이라 그 자리에 스크립트가 없다. 브랜치 checkout 단계를 넣었다.
- 검증: `bash -n` + 인자 파싱 6케이스 + 가드 5경로 실측(브랜치 누락·없는 브랜치·번들 없음·단일헤드 자동인식·멀티헤드 중단).

### 3. UH-24 (신규, P1) — 훅이 리눅스 클론에서 실행되지 않는다

push 중에 git 이 직접 인쇄했다:

```
hint: The '.githooks/pre-push' hook was ignored because it's not set as executable.
```

`.githooks/pre-push` 가 저장소에 **mode 100644** 로 커밋돼 있다. `git config core.hooksPath .githooks`(CLAUDE.md §5 가
새 클론마다 시키는 그 설정)를 해도 git 은 실행권한이 없는 훅을 **조용히 건너뛴다**. 즉 **리눅스·macOS·Termux
클론에서 §5 의 "훅으로 강제" 는 강제가 아니다** — 이 클라우드 컨테이너도, 배포용 폰 클론도 해당된다.

2026-08-21 항목(`docs/todo_archive_root.md`)이 "실제 `git push` 차단 확인" 이라고 적은 것은 owner Windows PC
기준이다(Git for Windows 는 exec 비트를 보지 않는 경우가 많다). 그래서 3주 넘게 드러나지 않았다.
**UH-1("배선한 룰이 push 를 못 막았다")의 재발형** — 이 저장소가 반복해서 데이는 자리다.

**정정 — 처음에 이 항목을 "chmod 한 줄" 로 적었는데 틀렸다. chmod 만 하면 더 나빠진다.** 훅 본문이

```sh
PY="C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"
...
if [ ! -f "$PY" ]; then echo "pre-push: venv 인터프리터를 못 찾음: $PY" >&2; exit 1; fi
```

로 **owner Windows PC 의 venv 경로를 하드코딩**한다. 리눅스·Termux 에는 그 경로가 없으므로 실행권한만 주면
훅이 **게이트를 한 줄도 안 돌리고 `exit 1`** → push 가 통째로 막힌다. 정리하면:

| 상태 | 리눅스 클론에서 |
|---|---|
| 지금 (mode 100644) | git 이 훅을 건너뜀 → **무게이트로 push 통과** |
| chmod 만 적용 | 훅이 돌지만 PY 부재로 즉시 exit 1 → **push 전면 차단** |
| chmod + PY 이식 | 게이트가 실제로 돈다 ← 이게 목표 |

**두 상태 모두 게이트는 안 돈다** — 하나는 조용히 통과시키고 하나는 전부 막을 뿐이다. 제대로 된 수정은
① `git update-index --chmod=+x .githooks/pre-push` ② `PY` 를 이식 가능하게(Windows 경로가 있으면 그것, 없으면
`python3`) **둘 다**다. 폰 배포 경로에도 영향이 있다 — slim main 워크트리는 `$GATE` 부재로 먼저 exit 0 되어
라이브 배포 push 는 살아남지만, 번들 모드의 브랜치 push 는 막힌다.

`.githooks/` 는 `prepush_check.py` §0 에서 full-gate 경로로 분류되고, 이 컨테이너는 `data/disclosure` **0개**·
`data/kidi` **0개**라 full gate 가 못 돈다 → **작업 PC 에서 처리**. 게이트 범위를 느슨하게 고쳐서 밀지
않았다(그러면 고치려는 것과 같은 부류의 구멍을 하나 더 뚫는다).

### 4. 이번 라운드 커밋은 훅 없이 나간 게 아니다

`prepush_check.py` 를 손으로 돌려 `REDUCED(jp-scope)` 판정 + offline **240 passed** 를 확인하고 밀었다.
훅이 무시된다는 사실 자체가 위 UH-24 의 증거이므로, 그 상태에서 "게이트 통과" 라고 쓰지 않는다.

---

## 2026-09-13 (2차) — 게이트 범위 판정을 문서에서 코드로

owner 지적으로 시작: **"한국 거 안 고쳤는데 한국 게이트 때문에 일본 작업이 BLOCK 되면 안 되지."** 맞는 지적이었고,
원인은 규칙이 아니라 배선이었다 — CLAUDE.md §5 의 범위 규칙은 owner 가 2026-09-12 에 이미 정해 놨는데
`scripts/prepush_check.py` 가 그걸 **읽지 않고** 언제나 전부 돌렸다. 실측 사례: jp 만 고친 번들에서 `RED=197`
(전부 한국 원문 `data/disclosure/` 부재) 로 BLOCKED.

- `prepush_check.py` **§0 PUSH SCOPE** 신설. `classify_path`(경로 1개 → jp/full/unknown + 근거) ·
  `decide_scope`(git 을 안 부르는 순수 함수) · `collect_changed_paths`(merge-base(@{upstream},HEAD)..HEAD +
  스테이지 + 워킹트리 + 미추적) · `print_scope`(비교 ref·파일 수·**결정적 파일과 그 근거**를 매번 인쇄).
  한국 마스터 게이트 5종(1·1b·1c·1d·1e)은 `_run_korean_master_gates()` 한 함수로 묶어 호출 지점을 하나로 만들었다.
- **fail-closed**: `@{upstream}` 없음 · git 실패 · 빈 diff · 모르는 경로 1개 → 전부 전체 게이트. 우회 환경변수 없음.
  오버라이드는 `--full`·`--scope-only` 둘뿐이고 `--scope-only` 는 verdict 를 아예 안 찍는다(게이트 미실행임을 화면으로 구분).
- **실측**: jp 3파일 번들 → `REDUCED(jp-scope)` exit 0 **5초**, 한국 축 5종 전부 `SKIPPED(jp-scope)`(로그에 그 섹션 자체가 없다) ·
  같은 트리에 `kics_disclosure.json` 하나 추가 → 자동 `FULL` exit 2 · `--full` 강제도 동일.
- 회귀 `tests/test_prepush_scope.py` **65케이스**, 변이 **12/12 발화**(목록 삭제·fail-open·빈 diff 축소·git 실패 fail-open·
  `-z` 제거(한글 경로)·미추적 누락·축소 모드에서 한국 게이트 호출·SKIPPED 대신 pass 인쇄 등).
  `test_push_gate_wiring.py` 에 `test_wired_means_wired_in_the_full_gate_only` 추가 — WIRED 의 뜻이 "전체 게이트에서 돈다"로
  좁아진 것을 매니페스트가 모르면 오독이다.
- `CLAUDE.md` 를 jp 범위에 넣은 근거: 이 파일에서 **기계가 검사하는 주장**은 골든표 동기화와 게이트 배선 둘뿐이고 둘 다 축소 묶음에 있다.
  그 전제 자체를 `test_claude_md_guards_stay_in_the_reduced_bundle` 이 지킨다.
- `.githooks/pre-push` 안내 문구도 갱신(전체 ~18분 / jp 범위 ~5초).
- **UH-20 등재**: 훅이 git 이 stdin 으로 주는 refspec 을 버려서 범위가 근사다. 빗나가면 전체가 도는 안전 방향이라 P3.

## 2026-09-13 — 서브에이전트 정의가 저장소 밖에 있었다 (`.gitignore` 의 `.claude/` 한 줄)

CLAUDE.md §10 은 "독립 작업은 서브에이전트를 한 메시지에서 병렬 발사, 모델은 티켓 유형으로" 를
규정한다. 그런데 그 실행체인 `.claude/agents/*.md` 7개가 `.gitignore:91` 의 `.claude/` 에 걸려
**머신 밖으로 나간 적이 없었다.** 클라우드 세션(이 저장소를 clone 만 해서 도는 환경)은 규칙만 읽고
실행체를 못 읽어, 병렬 발사 없이 혼자 도는 상태였다 — owner 가 직접 지적해서 발견.

- `.claude/agents/` 7개 커밋: downloader · parser-kics · parser-ifrs17 · **validation(Opus 5)** ·
  publishing · designer · jp-collector (나머지 전부 Sonnet 5). `.claude/skills/` 5개도 함께
  (kics-parser · ifrs17-parser · a11y-audit · launch-runbook · incident-postmortem —
  종전엔 ifrs17-parser 하나만 들어와 있었다).
- `.gitignore` 를 좁혔다: `.claude/` → `settings.local.json` · `settings.json` · `launch.json` ·
  `*.local.json`(머신마다 다른 권한·IDE 실행설정만 제외). 비밀정보 스캔 결과 agents·skills 에는
  키가 없다(환경변수 *이름*만 언급).
- CLAUDE.md §10 에 정의 위치·모델 매핑 한 줄 추가. jp 도메인 문서의 "머신 로컬, push 안 됨" 문장 정정.
- 같은 라운드의 jp 레인 산출은 `docs/changelog_jp.md` (25)(26), validation 은
  `docs/changelog_validation.md` 2026-09-13 참조.

## 2026-09-11 — 지침 부채 정리 1차: TODO Status 이력 아카이브 분리

> 근거 기사(owner 공유): 앤트로픽 내부 비용 절감 — '지침 부채'(행동을 바꾸지 않는데 매 호출 실리는 지시·이력) 제거 + 캐싱. 이 저장소에서 매 세션·매 서브에이전트가 강제로 읽는 것은 코드가 아니라 `CLAUDE.md`+`TODO*.md`+stage 프롬프트다. 실측(토큰 근사): stage TODO 7개 288k(그중 `TODO_parser_ifrs17.md` 128k = 88개 pass 로그가 H1 아래 그대로 쌓임), stage 프롬프트 42k, changelog 344k(이미 deferred).
>
> **한 일:** `TODO.md`·`TODO_parser_ifrs17.md`·`TODO_parser_kics.md`·`TODO_validation.md`·`TODO_designer.md`·`TODO_downloader.md` 의 Status 이력(최신 5개 제외)을 `docs/todo_archive_{root,parser_ifrs17,parser_kics,validation,designer,downloader}.md` 로 이동. 순수 이동 — 줄 범위 타일링 검사 + 활성·아카이브를 원래 순서로 재조립해 HEAD 와 바이트 일치 확인(6/6). 각 활성 파일에 포인터 1블록, `CLAUDE.md` 핸드오프 절에 규칙 1문단. 결과 288k → 64k(−78%). `TODO_publishing.md`(178줄)는 손대지 않음. 코드는 매 세션 로드되지 않으므로 이 정리의 대상이 아님(별건).

---
