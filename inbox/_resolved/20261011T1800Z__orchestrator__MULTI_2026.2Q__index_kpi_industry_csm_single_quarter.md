---
from: orchestrator
to: designer
created: 20261011T1800Z
status: resolved
route: feature
company: MULTI
period: 2026.2Q
iter: 1
---

## 미결 (sender 작성)
owner 지시(2026-10-11): 「업계 26.2Q CSM 은 142조로 바꾸자.」 index.html 의 KPI 「업계 총 기말 CSM」은 지금 `totalClosingCsmEok()` 가 `CSM_waterfall.json` 항목 6 의 **회사별 최신 분기 값을 합산**한다(라이브 37사 139.7조, 새 마스터 44사 141.4조). 연 1회 공시사 21사는 2025.4Q(일부 2024.4Q)에서 멈춰 있어 **분기가 섞인 숫자**다. 보험계약부채 마스터(경영공시 2-4 표)에는 연 1회 공시사도 분기별 CSM 잔액이 있어, **전 회사를 같은 분기(2026.2Q)로** 합할 수 있다. 오케스트레이터 실측: `data/csm_combo/panel_csm_combo.json` 의 `csm_gen + csm_vfa`(억원) 합 = 2026.2Q **46사 142.2조** · 2026.1Q 46사 138.0조 · 2025.4Q 47사 133.7조.

### 해 줄 것
1. **KPI 원천 교체**: `totalClosingCsmEok()` 대신 `panel_csm_combo.json`(이미 fetch 하고 있는지 확인; 없으면 index.html 이 이 파일을 fetch 하도록 추가 — 배포 대상 목록 `scripts/android_push_and_deploy.sh` `NEW_FILES` 에 이미 있다)의 **가장 최신 분기**(전사 최신 `meta.quarters` 중 값이 있는 마지막 분기)에서 회사별 `csm_gen + csm_vfa` 를 합산. 두 열이 모두 null 인 회사는 제외. 결과: 2026.2Q 142조(소수 첫째 자리까지 보면 142.2조).
2. **표기**: KPI 라벨 옆(또는 서브라벨)에 「2026.2Q 기준 · 46사」처럼 **기준 분기와 회사 수를 데이터에서 도출**해 표기(하드코딩 금지). 짧은 설명은 `?` 팝오버(「경영공시 2-4 보험부채 현황표의 보험계약마진(일반모형+변동수수료접근법) 합. 연 1회 공시사도 분기별 잔액이 공시되어 같은 분기로 합산」). 데이터에 최신 분기가 일부 회사에만 있으면(예: 한 곳만 새 분기) 그 분기 대신 **회사 수가 충분한 최신 분기**를 쓰는 규칙(예: 전체의 80% 이상)과 그 규칙을 코드 주석에 남긴다.
3. **그 밖의 CSM 합계 표기**: index.html 안에 같은 방식(회사별 최신 분기 합)으로 업계 CSM 총합을 보여주는 곳이 더 있으면(`grep totalClosingCsmEok`, 보조표 요약 문장 등) 함께 같은 원천으로 맞추고 보고. 버블맵의 회사별 크기(기말 CSM)·배수·연1회 공시사 추정(회색 별표) 로직은 **이 티켓에서 바꾸지 않는다**(owner 별도 지시 시).
4. 확인: 라이트·다크, 모바일 375px 에서 KPI 줄 넘침 없음, 숫자 카운트업 애니메이션 유지, 음수 △(해당 없음), 콘솔 오류 0. 로컬 확인 시 `?iq_internal=1`.
5. **주의(배포 순서)**: `panel_csm_combo.json` 은 작업 브랜치 HEAD 의 새 판(48사·14분기)이 필요하다. 라이브 판(40사·8분기)에는 2026.2Q 가 없을 수 있으니, 새 판이 배포되기 전에 이 HTML 만 먼저 가면 KPI 가 옛 분기로 나온다 — 코드가 라이브 판에서도 깨지지 않고(빈 값이면 기존 `totalClosingCsmEok()` 로 폴백) 동작하게 하되, 폴백 사실을 코드 주석과 보고에 적는다.

### 규칙
- `index.html` 만 수정(필요 시 테스트). 마스터·패널 JSON·xlsx·`public_exports`·게이트 금지. 서브에이전트 금지, 공용 Browser pane 금지(headless). 테스트 `tests/test_deploy_assets.py` · `tests/test_push_gate_wiring.py`. push·배포 금지, 커밋은 자기 파일만(명시 경로, 끝에 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`). 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).
- 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 스크립트 파일만, UTF-8(BOM 없음).

### 보고
- KPI 새 원천·기준 분기 규칙·표시 문구, 값 확인(142.2조), 폴백 동작, 다른 CSM 합계 표기 유무, 스크린샷 경로, 테스트 결과, `TODO_designer.md` Status + `docs/changelog_designer.md`.

## 답변 (recipient 작성 — 처리 후)
(designer 49f8573, orchestrator 종결 2026-10-11) index.html KPI 「업계 총 기말 CSM」: 원천 `panel_csm_combo.json` 의 `csm_gen+csm_vfa` 합, 기준 분기 = 값 보유 회사가 80% 이상인 가장 늦은 분기(코드 주석), 표시 「2026.2Q 기준 · 46사」(데이터 도출) + ? 팝오버, 값 142.2조 확인(2026.1Q 138.0·2025.4Q 133.7), 패널 404·열 이름 없음 시 옛 `totalClosingCsmEok()` 폴백(141조·「회사별 최신 공시 분기 합」). `.rise` 애니메이션 fill both→backwards(팝오버 가려짐 방지). 배포 순서: 새 판 panel_csm_combo(48사·14분기)가 함께 올라가야 142조. 테스트 77 통과.
