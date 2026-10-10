---
from: orchestrator
to: parser
created: 20261011T0420Z
status: open
route: backfill
company: MULTI
period: 2023.1Q-2026.2Q
lane: kics
iter: 1
---

## 미결 (sender 작성)
owner 지시(2026-10-11, 밤새 처리): 「다음 round 로 미뤄 놨던 거 **전부** 스윕해라.」 K-ICS 레인에서 미뤄 둔 것(재보사 스윕 단계 9~11 보고·`TODO.md` 열린 일)을 한 번에 처리한다. 런로그 `data/disclosure/_meta/reinsurer_runlog_KR1101-1108_9.md`·`_11.md`·`_12.md` 가 출발점.

### 작업 (우선순위 순, 단계마다 디스크 저장·런로그 `reinsurer_runlog_KR1101-1108_13.md` 맨 위 「중간 결과」 갱신)
1. **기존 6셀 IRR 잔액 시나리오 열 뒤바뀜 정정**(owner 승인: 이 라운드에 고친다): 카카오페이손보(KR1098) 2023.2Q·2023.4Q·2024.4Q·2025.2Q·2026.2Q, 하나손보(KR0050) 2025.2Q — `data/_derived/kics_irr_balance.json`·`kics_duration_gap.json`(하나손보 2025.2Q 자산듀레이션 2.25 대 원문 열 순서 4.78). 원문 PDF 렌더링으로 열 순서를 확인하고 **셀 단위 + 옛 값 guard + 백업**으로 정정, 파생 마스터(`kics_duration_gap.json` 등)를 같은 방식으로 맞춘다. 기존 39사 중 이 6셀 외 변경 0 증명. 단계 11 에서 고친 재보사 값은 건드리지 않는다.
2. **퍼시픽 KR1107 금리민감도 2024.4Q·2025.2Q**(MD 에는 있고 마스터에 없는 12행)와 **KR1107 비율 정밀값 4칸**(단계 9 결정 2) 적재. 단계 11 의 단위·적용후 규칙을 따른다.
3. **스위스리아시아 KR1102 2023.2Q 전기 열 적재**: 단계 9 보고 — 새 완성본(v20240510)의 전기 열로 1~46 을 모두 채울 수 있고 새 RED 0. 적재하면 validation 의 census 면제(`_CENSUS_SOURCE_ABSENT` KR1102 2023.2Q 등재)가 「등재를 풀어라」 RED 가 되므로 **적재한 뒤 validation 정리 대상으로 보고**한다(등재부 수정은 하지 않는다). **2023.3Q 는 새 RED 2건(룰 4, `8_life_census`)이라 적재하지 않고** 근거만 보고(owner 등재 필요).
4. **수작업 정정 8쌍이 추출기를 다시 돌리면 되살아나는 문제**(단계 11 §10): 추출기(`extract_kics_rate_sensitivity.py`·`extract_kics_irr_balance.py` 등)에 단위 머리말 오기(「억원」으로 잘못 적힌 표)·잘린 라벨·쪽 넘김·「0 인쇄 = 비어 있음」 같은 규칙을 반영해 재실행 결과가 현재 마스터와 동일하게 한다(재현 불가능한 수작업 정정 0 목표). 기존 39사 추출 결과 불변 증명.
5. **같은 분기에 raw PDF 가 둘일 때(예: KR1102 2023.4Q 옛 60쪽/새 85쪽) 일부 도구가 옛 파일을 고르는 문제**: 어떤 도구가 어떤 규칙으로 고르는지 확인하고, 매니페스트의 `versions`/`latest` 를 따르도록 공통 헬퍼로 고친다(`src/solvency/parser`·scripts 중 해당). 고쳐도 기존 결과 불변이어야 한다.
6. **재보사 문서의 남은 census 구멍 재점검**: `kics_disclosure.json` 재보사 버킷을 (회사×분기×항목 1~54) 전수 census 해서 비어 있는 칸 목록을 만들고, 원천이 있는데 못 뽑은 칸이 있으면 채운다(원천 부재는 근거와 함께 보고 — 등재는 validation/owner).

### 규칙
- 모든 마스터 쓰기는 **셀 단위 + guard + 백업**(`data/_derived/reinsurer_backup_<날짜>/`), 통짜 read-modify-write 금지, `build_root_masters.py main()` 금지, `validate_master_tables.py` 는 `--no-build`. **기존 39사(KR0001~KR1000 등) 변경은 위 1번 6셀과 4·5번 도구 개선 결과 동일뿐**. 게이트·예외 등재부·골든(`--update` 금지)·HTML·xlsx·`public_exports`·`insurance_liability_portfolio*`·`IFRS17_BS.json`·`PL_breakdown*`·`CSM_*` 금지. 커밋·push 금지. 서브에이전트 금지, docling 은 한 번에 1개.
- 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 멀티라인 `python -c` 금지(스크립트 파일), **맨 `python`·`python -`(stdin heredoc) 절대 금지**(고아 CPU 스핀 전례 3회), `encoding` 명시, UTF-8(BOM 없음). RAM 15.5GB, 다른 에이전트 2~3개 동시 실행. 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).

### 보고
- 단계별 결과(정정 6셀 전후, 적재 행 수, 추출기 재현성 증명, 도구 수정 내용), 새 RED/등재 풀 대상, census 구멍 목록, 게이트 전후, `TODO_parser_kics.md` Status + `docs/changelog_parser_kics.md`.

## 답변 (recipient 작성 — 처리 후)
(오케스트레이터가 종결한다)
