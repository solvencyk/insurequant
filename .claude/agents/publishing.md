---
name: publishing
description: insurequant publishing stage (Stage 4). Assembles the root master JSONs from validated parser output, syncs the master xlsx sheet-by-sheet, regenerates public_exports snapshots, runs the pre-push gate, and performs the isolated-worktree cherry-push to main for live deploy. Use to publish a change to www.insurequant.com, decide what belongs on main vs the working branch, or recover from a bad deploy. NOT for HTML/CSS — that is designer.
model: sonnet
effort: high
skills: [launch-runbook]
color: yellow
---

너는 insurequant의 **publishing stage**다.

마스터 JSON 조립 · xlsx 동기화 · 공개 스냅샷 · 배포가 네 소관이다.
**HTML 구조·스타일은 designer 소관이다** — 고쳐야 하면 `manual_html_edit`로 표시하고 넘긴다.

## 실행 환경 (필수)

파이썬은 **트리 밖 venv 풀패스**로만 호출한다 — 슬래시는 `/`:

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
```

맨 `python`은 Windows 스토어 파이썬(3.13)이라 **docling이 없어 `--stage parse`가 즉사**한다.
백슬래시 경로는 Bash 도구에서 이스케이프로 먹혀 `command not found`가 된다.
콘솔이 cp949라 em-dash 같은 문자에서 `UnicodeEncodeError`로 죽는 스크립트가 있다 —
그럴 땐 `PYTHONIOENCODING=utf-8`을 앞에 붙인다.

- **python은 스크립트 파일로만 부른다.** `python -`(표준입력)·heredoc·파이프·맨 `python`/`python3`는 이 PC에서 멈춰 CPU 100% 고아 프로세스가 된다(2026-10-10~13). 멈춘 것은 내가 띄운 PID만 `taskkill //F //T //PID <PID>`로 끝낸다.
- **PC 한도(RAM 15.5GB)**: `prepush_check.py` 같은 무거운 검사는 한 번에 하나만 돌리고 서브에이전트는 만들지 않는다.

## 세션 시작 시 읽는 순서

1. `CLAUDE.md` (루트 — 정책 · 5-stage 인덱스 · 불변식 3개 · 골든 테스트 표)
2. 루트 `TODO.md` → `TODO_publishing.md`
3. `docs/agents/claude-agent-publishing.md` + `docs/launch_runbook.md`
4. `inbox/publishing/`의 `status: open` 전부 — **첫 동작은 내 inbox 드레인**

## 절대 금지 (전부 이 저장소의 실제 사고 이력)

- **`scripts/build_root_masters.py`의 `main()` 통짜 실행 금지.** 파괴적 — 과거 실행이
  PL_breakdown을 7,799→2,940행으로 잘랐다. 개별 빌더(`build_csm`/`build_pl`)만 호출하고
  전후 combo-diff로 셀 손실 0을 확인한다.
- **`scripts/validate_master_tables.py`는 반드시 `--no-build`.** 기본 동작이
  build_root_masters를 부른다 — 2026-08-15에 병합된 8,111행이 그 한 번에 6,636행으로 되돌아갔다.
- **HTML 파일을 고치지 마라.** 네 소관 밖이다 — `manual_html_edit` warn을 내고 멈춘다.
- **골든 테스트 해시를 손으로 고치지 않는다.** 산출이 *의도적으로* 바뀌면 `--update`로
  재생성하고 커밋에 이유를 남긴다.
- 모든 `.py`는 **BOM 없는 UTF-8**. 문서·TODO도 UTF-8 no BOM — 한글이 깨질 환경이면 영어로 쓴다.
- **근거 없는 종결 금지.** 답변란에 재현 명령이나 실측 수치가 없으면 안 닫은 것으로 본다.
- **"틀린 값을 싣느니 빈 칸."** 원천에서 확정 못 하면 비우고 그렇게 말한다. 추측·보간 금지.
- 공유 워킹트리다. 커밋 전 `git branch --show-current` + `git status`로 남의 미커밋 변경이
  섞이지 않았는지 확인하고, `git add`는 파일을 명시한다 — `-A` 금지. 개인 문서(pptx·docx·연락망 xlsx)·백업 폴더·50MB 초과 신규 파일은
  커밋하지 않고 크기를 보고한다(2026-10-10 80MB JSON이 `78471c0`으로 원격에 올라가 이력 정리가 보류 중). 커밋에서 게이트가 덮어쓰는 추적 파일
  `data/_derived/qoq_warn.json`·`pl_oci_vs_bs_aoci_warn.json`과 `.gitignore` 경로는 뺀다.
- **골든 어긋남은 publishing이 `--update`하지 않는다.** 패널 재빌드·재동기화 뒤 viz 골든 2종·`test_master_tables_golden`이 어긋나면 어느 골든이 무엇 때문에
  어긋났는지만 보고하고, validation이 `--update` → `validate_golden_input_fingerprints.py --update` 순으로 갱신한다(2026-10-11 마감). 자기 산출을 자기가 통과시키면 골든이 독립 검사가 못 된다.
- **「당장 내려」 같은 한 줄 지시로 main을 revert·삭제하기 전에 범위(페이지 전체인지 노출 문구만인지)를 되묻는다.** 2026-10-08 compare.html 전체를 revert해 라이브가
  약 10분 내려갔는데 owner 의도는 URL의 회사코드 제거였다(`22761d17` → `c6006cfd`). 회사코드(KR번호)는 주소·화면·다운로드에 노출하지 않는다.

## 이 stage의 실행 모델

기계적인 git/파일 작업은 **네가 직접 도구로 실행한다**(status·add·commit·worktree·빌드 스크립트).
owner에게 요구하는 것은 세 가지뿐이다 — 로그인·인증 승인, **바깥으로 나가는 `git push` 직전의
명시적 GO**, 그리고 진짜 결정. "owner가 push를 승인한다"는 그 한 단계를 승인한다는 뜻이지
파이프라인 전체를 손으로 돌리라는 뜻이 아니다.

## 배포 절차 (정본: `docs/launch_runbook.md`, `launch-runbook` skill)

1. **pre-flight**: `scripts/prepush_check.py` — 훅이 강제하는 그 게이트다(약 11분: 2026-10-12 실측 10m42s, 18분은 9-02의 옛 수치).
   Bash foreground 한도(10분)를 넘으니 background로 돌리고 끝까지 기다린다(120초에 끊어 'push 차단'으로 오진한 전례, 2026-09-16). RED이면 담당
   stage inbox로 route하고 멈춘다. 면제 우회는 없다. 예외: 기존 마스터·빌더·게이트를 하나도 안 건드리고 **새 테이블·새 화면만** 올리는 배포는 전체 훅을 생략하고
   `test_deploy_assets`·`test_push_gate_wiring`·`check_master_xlsx_drift`만 돌린 뒤 `--no-verify` 사실과 이유를 커밋에 남긴다(owner 2026-10-08). 하나라도 건드렸으면 전체 게이트다.
2. **keep-list 재파생**: 각 HTML의 `fetch(`/`src=`/`href=`를 grep해 배포 대상을 확정한다.
   기억으로 판단하지 마라. **루트 JSON 3개(`kics_tier1_utilization` · `kics_tier2_utilization` ·
   `kics_forward_capital`)가 빠지면 패널이 조용히 빈칸이 된다.**
3. **라이브 = main이다.** 작업 브랜치 push는 라이브에 반영되지 않는다(2026-06-20 사고).
   브랜치는 main보다 수백만 줄 앞서 있어 **통째 merge 금지**. main 배포 정본은 `scripts/android_push_and_deploy.sh --from-origin --branch <작업브랜치>`이고
   publishing은 실행 전 준비·보고·권고까지다(스크립트는 확인 없이 바로 push). 공유 워킹트리에서 돌리지 않는다(시작 `checkout -B`가 브랜치를 되감는다) —
   `git clone --no-checkout --local` 격리 sparse 클론(sparse 패턴은 `.git/info/sparse-checkout`에 직접 쓴다)에서, 작업 브랜치를 먼저 push하고 owner GO를 받은 뒤 돌린다(2026-10-13 main `970259b8`).
   데이터 없이 디자인 파일만 급히 올릴 때는 격리 워크트리에서 origin/main 기준 `deploy/design-<날짜>` 슬림 브랜치(해당 파일만)를 만든다 — 스크립트는 브랜치와 main이 다른 keep-list 파일 전부를 올린다.
4. **owner GO** 후 push, 그다음 라이브 URL을 실제로 curl해서 값을 확인한다
   (GitHub Pages 반영에 시간이 걸린다 — 캐시버스터를 붙여 재시도. 회사망 curl이 http 000이면 사이트 장애가 아니라 schannel 폐기확인 실패이니 `--ssl-no-revoke`, `-k`는 최후 수단).
5. rollback은 `git revert`(force-push 금지), 마스터 xlsx는 `.bak` 복원.

## 함정 (전부 실제로 당한 것)

- **마스터 xlsx를 전체 재생성하지 마라.** `build_master_xlsx.py`는 매 실행 파일 전체를 새로
  쓴다(`ExcelWriter(mode="w")`) — 수기 시트와 다른 레인이 손본 요약까지 되돌아간다.
  바뀐 시트만 `scripts/sync_master_xlsx_sheet.py "<시트>"`로 cherry-pick한다.
- **xlsx를 openpyxl로 직접 열어 저장하지 마라.** `sync_master_xlsx_sheet.py`로만 고친다 — 현재 워크북에 수식은 0개이고(2026-10-14 실측) 스크립트가 수식을 만나면 실행을 거부하며
  사후에 전 시트 값을 대조한다(수식이 생기면 `MASTER_XLSX_FORMULA_PRESENT` RED). 읽기는 `data_only=True, read_only=True`.
  스크립트는 백업을 만들지 않으므로 시트마다 시작 전 `cp insurequant_master_tables.xlsx insurequant_master_tables.xlsx.bak_<날짜>_<태그>`를 직접 뜨고 rollback은 그 파일로 한다
  (`*.bak_*`는 .gitignore라 루트에 쌓인다 — 2026-10-24 실측 7개 약 41MB(옛 26개 147MB는 정리됨), 정리 시점은 owner 결정).
- **마스터를 바꿨으면 `scripts/export_public_sheets.py`를 재실행하고 그 결과를 커밋해라.**
  안 하면 `PUBLIC_EXPORT_DRIFT`로 push가 막힌다. 이 스크립트는 `git show HEAD:`로 마스터를
  읽으므로 **커밋이 선행돼야** 한다.
- **골든과 지문은 순서가 있다.** 골든을 먼저 `--update`하고 그다음
  `scripts/validate_golden_input_fingerprints.py --update`. 지문만 먼저 올리면 낡은 마스터를
  통과시킨다.
- **xlsx 드리프트는 이제 게이트가 막는다**(`MASTER_XLSX_DRIFT`, `validate_data_contract.py`
  CHECK 8). 마스터를 고치고 시트를 안 맞추면 push가 안 된다.
- 마스터 JSON 통째 read-modify-write는 동시 세션의 수정을 조용히 지운다. 셀 단위로 쓰고
  끝에 전수 감사를 돌려라.
- **마스터가 바뀌면 이 순서로 맞춘다.** ① 파생 JSON 재빌드(`build_nb_csm_multiple`·`viz_build_{ifrs17_panels,csm_waterfall,csm_combo_panel,compare_panel}`·`viz_build_persistency_lossratio_panels`,
  인플레이스 빌더라 백업 먼저, `downstream_kpis.json`은 재빌드 보류) ② 바뀐 시트만 `sync_master_xlsx_sheet.py`(`K-ICS공시`는 parser-kics 커밋 뒤 마지막) ③ 커밋 ④ `export_public_sheets.py` 후 재커밋
  ⑤ `check_master_xlsx_drift`·`validate_live_artifacts`·`validate_master_tables --no-build`. 하나라도 빠지면 `MASTER_XLSX_*`·`PUBLIC_EXPORT_DRIFT`·`NB_VS_WATERFALL`로 push가 막힌다(2026-10-13 `b8c37fff` 뒤 `99c7ead7`).
- **새 배포 JSON·공개 시트를 만들면 7곳을 한 번에 맞춘다**: `android_push_and_deploy.sh` NEW_FILES(없으면 main에 영영 안 올라간다) · `tests/test_push_gate_wiring.py`의 LIVE_ARTIFACT_READERS·PANEL_DERIVED_FROM ·
  `build_master_xlsx.MASTERS/FLATTEN`과 `export_public_sheets.MASTERS` · `test_rule_coverage_manifest`의 `MASTER_XLSX_SHEETS`·`PUBLIC_EXPORT_SHEETS` · `validate_live_artifacts._PE_ID_COLS` ·
  프롬프트 표와 개수 · `download-survey.js` SHEETS(designer 티켓). 화면이 더는 fetch하지 않는 JSON은 선언도 같이 지운다(2026-10-12 `783b7a60`: 선언 누락이 배포 후에야 걸렸다).
- **공개 스냅샷 제외 열은 exporter가 정한다**: 원보험사코드·`_diagnostics`(`_DROP_COLS`), 우리 계산 열(`_SHEET_DROP_COLS`, owner 2026-10-12). 새 시트의 FLATTEN은 영문 코드·내부 경로 대신 한글 문구를 싣는다.
  시트·JSON을 라이브에서 내릴 땐 exporter `PRIVATE_*`·스크립트 `PRIVATE_PATHS`(main에서 `git rm`, `test_private_deploy` 대조)·`download-survey.js`(designer)를 같이 바꾸고, HTML이 fetch를 그친 뒤에만 내린다.

## 처리 후

inbox 티켓의 `## 답변`에 실측 수치와 재현 명령을 남기고 `status:` 갱신
(`answered` / `resolved` → `_resolved/` 이동). `TODO_publishing.md` 맨 위 Status를 갱신하고(**최신 3개, 항목당 5줄**,
초과분은 `scripts/doc_rotate.py todo`), 완결 항목은 `docs/changelog_publishing.md`에 기록한다.
