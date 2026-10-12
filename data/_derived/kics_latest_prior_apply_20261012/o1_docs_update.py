"""o1_docs_update.py [--apply] -- TODO_parser_kics.md Status (32nd entry in, 29th entry cut verbatim into the archive), the open-items line, and the changelog section.

Line endings are preserved per file: TODO + archive = LF, changelog = CRLF.  UTF-8 no BOM.  Without --apply: verification only.
"""
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_20261012")
from lib_apply import *  # noqa: F401,F403,E402

utf8_stdout()
apply = "--apply" in sys.argv
TODO = REPO / "TODO_parser_kics.md"
ARCH = REPO / "docs" / "todo_archive_parser_kics.md"
CHLOG = REPO / "docs" / "changelog_parser_kics.md"

STATUS = [
    "- **2026-10-12 (32회차) 「최신 공시 직전 컬럼 우선」 적용(티켓 `20261012T2200Z`) — 드라이런 채택 후보 26블록 중 확실 기준 통과 16블록 65칸 적용(전 33 · 적용후 미러 22 · 파생 27·28 10) · 10블록 보류 · 예외 2건 해제**: 칸 단위 + 옛값 가드 + 임시 파일 교체로 `kics_disclosure.json` 을 바꿨고 HEAD 대비 바뀐 칸이 계획과 정확히 일치한다(행 추가·삭제 0, `git diff --numstat` 65/65). 보류 = 후속 공시 두 곳이 그 칸에서 어긋난 9블록 + `recalc_kics_derived` 가 되돌리는 1블록(ABL생명 2024.3Q 항목 22: 인쇄 1 은 확실하나 항목 22 영 규칙이 되돌림), 나머지 62블록은 드라이런 범주 그대로(`held_blocks.csv` 72행). 5칸은 재작성이 아니라 마스터가 자기 공시 인쇄와 달랐던 칸(악사 2025.1Q · 2026.1Q, 흥국생명 2024.4Q, AIA 2026.1Q, 롯데 2023.4Q 활자 오류).",
    "  게이트: K-ICS RED 56 → 54(롯데 2025.1Q · NH농협 2024.3Q 항목 13 이 닫혀 해소, 새 RED 0, blocking 0, exit 0), 데이터계약 RED 0 · YELLOW 152 → 164, `validate_master_tables --no-build` 출력 전후 동일, xlsx `K-ICS공시` 65칸만 동기화(드리프트 0). 영속화 = 재작성 장부 `kics_restatement_ledger.json` 29칸 as_restated + 결정 기록 · `_TIER2_ISSUER_INCONSISTENT` 22 → 20(원장 `CONTRADICTED`) · 사본 재빌드 시뮬레이션: `fill_*` 재실행이 되돌리는 재작성 28칸 + 활자 오류 1칸을 게이트가 RED 29 로 잡음, `recalc` 영향 0.",
    "  남은 것: validation(골든 `test_kics_rules_golden` `--update` 이유 「31 finding 이동: RED 56→54 · YELLOW 1936→1934 · GREEN +4」 · 입력지문 INPUTS_MOVED ×4(+3바이트) · 시험 4건: `test_tier2_issuer_inconsistent_exemption` 3(등재 수 22→20 · 롯데 2025.1Q 대상 교체 · 갈래 박제 대상 소멸) + `test_rule_coverage_manifest` 재작성 census 10→39) · publishing(`public_exports`) · owner(보류 72블록). 근거 `data/_derived/kics_latest_prior_apply_20261012/`(`applied_blocks.csv` · `held_blocks.csv` · `plans/`). 커밋 = 이 문서와 같은 커밋.",
]
OPEN_OLD_PREFIX = "- [ ] **「최신 공시 직전 컬럼 우선」 원칙 후속(31회차, 티켓 `20261012T1900Z`)**"
OPEN_NEW = ("- [ ] **「최신 공시 직전 컬럼 우선」 원칙 후속(31·32회차, 티켓 `20261012T1900Z` · `20261012T2200Z`)**: 적용분 16블록 · 예외 2건 해제는 32회차에 끝났다. 남은 것: "
            "① owner - 보류 72블록 중 후속 공시가 그 칸에서 흔들리는 9블록(하나손해 2023.1Q · 신한이지 2023.3Q · 삼성생명 2023.2Q · 2024.3Q · 푸본현대 2025.2Q · 메트라이프 2024.3Q · KB라이프 2024.2Q · 2024.4Q · 처브라이프 2025.2Q) 채택 여부 · "
            "구성행 자리 바꿈 룰 사각 8블록 · 빈 버킷 채움 5건(스위스리 2023.3Q · 하노버 2023.4Q · 2024.1Q · 2025.3Q · RGA 2023.2Q) · 소급재작성 장부 `_policy` 기본값 전환 여부 "
            "② validation - 코리안리 2024.2Q~4Q 박제 사유 재검토 · 골든 `--update` · 입력지문 · 시험 4건 정리(위 Status) "
            "③ parser - `recalc_kics_derived.py` 항목 22 영 규칙(`항목14 == 항목15 이고 항목23 == 0`)이 인쇄된 1 을 되돌려 ABL생명 2024.3Q 항목 22 = 1 적용을 보류했다. 규칙을 「반올림 노이즈일 때만」으로 좁히면 풀린다. "
            "산출 `data/_derived/kics_latest_prior_apply_20261012/`(`applied_blocks.csv` · `held_blocks.csv` · `plans/` · `img/`) · 드라이런 `data/_derived/kics_latest_prior_precedence_dryrun_20261012/`.")

CHANGELOG = """## 2026-10-12 (이어서 5) - 「최신 공시 직전 컬럼 우선」 적용: 확실 기준 통과 16블록 65칸 · 보류 72블록 · 예외 2건 해제 · 재작성 장부 29칸 (티켓 `20261012T2200Z`, kics 레인, 푸시 없음)

계약: orchestrator 티켓 `inbox/parser/20261012T2200Z__orchestrator__MULTI_2023.1Q-2026.1Q__kics_apply_latest_prior_column_verified_blocks.md`(공유 티켓, 오케스트레이터가 종결 - 고치지 않음) + owner 결정 「생각보다 바꿀 값이 많지는 않네? 최신 공시 직전 값이 검산이 다 닫히는 게 확실한 애들만 덮어써라」(2026-10-12). 범위 = 드라이런(`ae7a54b7`)이 채택 후보로 판정한 26블록 87칸 중 티켓의 「확실」 기준 4개를 통과한 것만. 서브에이전트 0 · docling 0 · PDF 는 텍스트 레이어(fitz 단어 좌표 행)와 100~150dpi 렌더링을 직접 읽었다. 산출 `data/_derived/kics_latest_prior_apply_20261012/`(`applied_blocks.csv` 65행 · `held_blocks.csv` 72행 · `plans/*.json`(옛값 · 새값 · 출처 쪽 · 세 열 인쇄값) · `img/` 렌더링 17장 · `gates/` 게이트 출력 · `proof_vs_head.txt`).

- **기준 판정(26 → 16 적용 · 10 보류)**: ① 룰 · 이웃 분기 · 다른 게이트 축 새 RED 0 - 16블록을 한꺼번에 넣은 후보 마스터로 실제 게이트(`validate_kics_disclosure.py --master`)와 데이터계약 CHECK 1·3·4·7 을 다시 돌려 확인했다(RED 56 → 54, 새 RED 0, 움직인 finding 56개 전부 건드린 16버킷 안, 이웃 분기 0). ② 완전성 문제 없음(핵심표 판독 완료 · 짝수분기 세부표 일치 · 적용후 독립 값이 있는 칸 없음). ③ 주의 표시가 붙은 6블록(롯데 2025.1Q GAPFILL · 예별 2023.1Q · 현대해상 2023.1Q · 악사 2025.1Q · 하나손해 2025.3Q GAPFILL · 흥국생명 2024.4Q)은 바뀌는 칸마다 원본 PDF 를 열어 쪽 번호와 인쇄값을 기록했다(렌더링 17장 = 위 6블록 + 자기 공시가 이미지 쪽인 악사 2026.1Q · AIA 2026.1Q + 롯데 2023.4Q 활자 오류 쪽, 스캔 쪽은 150dpi). ④ **후속 공시 두 곳이 그 칸에서 다른 값을 인쇄한 9블록은 보류**: 직전분기 열은 마스터와 같고 전전분기 열만 새 값이라 최신 열도 흔들린다(하나손해 2023.1Q 항목 18 972/971 · 신한이지 2023.3Q 항목 11 -332/-333 · 삼성생명 2023.2Q 항목 11·12 · 삼성생명 2024.3Q 항목 23 · 푸본현대 2025.2Q 항목 4·7 · 메트라이프 2024.3Q 항목 7 · KB라이프 2024.2Q · 2024.4Q 항목 22 · 처브라이프 2025.2Q 항목 5 2,852/4,941 · 항목 11 2,363/275).
- **내구성으로 1블록 추가 보류(ABL생명 2024.3Q 항목 22: 0 → 1)**: 자기 공시 p16 · 직전 · 전전 열이 모두 1 을 인쇄해 값은 확실하지만 `recalc_kics_derived.py` 가 `항목14 == 항목15 이고 항목23 == 0` 이면 항목 22 를 0 으로 되돌린다(1 에서 시작해 재계산하면 0, 사본으로 확인). 다음 라운드의 정상 재계산이 조용히 되돌릴 칸이라 싣지 않았다. 규칙을 「반올림 노이즈(1 미만)일 때만」으로 좁히면 풀린다(이 티켓 밖). 나머지 62블록은 드라이런 범주 그대로 보류(`held_blocks.csv`).
- **적용(16블록 65칸)**: `apply_master.py`(칸 단위, 옛값 가드, 시작 sha · HEAD 일치 확인, 사전 증명 후 임시 파일 → `os.replace`, 백업). 전(`값`) 33 + 적용후 미러(전=후이던 칸) 22 + 파생 27·28(기존 산식 그대로, 마스터 값이 옛 입력의 파생값일 때만) 10. HEAD 대비 바뀐 칸 = 계획 65칸 정확히, 키 집합 · 순서 불변, 다른 회사 행 전부 동일, `git diff --numstat` 65/65(`proof_vs_head.txt`). 적용사의 적용후 열은 독립 값이 있으면 블록 자체를 보류했고, 미러가 있는 악사 2025.1Q 항목 3 은 가용자본(1·2·3)이 전=후이고 기준금액(14)만 적용후가 달라 선례 `acd351a`(악사 2024.3Q)와 같은 방식으로 함께 바꿨다.
- **발견 - 5칸은 재작성이 아니라 마스터 오류**: 악사 2025.1Q 항목 3(마스터 2,332 = 항목 1 - 2 파생, 자기 공시 p16 은 2,331 인쇄) · 악사 2026.1Q 항목 4(3,821 = 구성행 합, 자기 공시 p16 은 3,820) · 흥국생명 2024.4Q 항목 4(33,923 = 구성행 합, 스캔 p48 은 33,924) · AIA 2026.1Q 항목 3(4,279 = 항목 1 - 2 파생, p18 은 4,280) · 롯데 2023.4Q 항목 4(자기 공시 p41 은 활자 오류 2,481 을 인쇄, 마스터는 구성행 합 24,808, 후속 공시 둘이 24,807). 이들은 새 값이 자기 공시 인쇄값(롯데는 후속 인쇄값)이라 as-filed 정책과 충돌하지 않는다. 나머지 28칸이 진짜 재작성(자기 공시 = 마스터 옛값, 후속 둘 = 새 값): 현대해상 2023.1Q 8칸(기본/보완자본 분류 73,537/59,861 → 68,456/64,925 · 재분류 53,694 → 58,757, 재작성 열은 순자산 127,214 = 구성 6행 합 · 지급여력금액 133,381 = 68,456 + 64,925 로 자기 안에서 닫힘) · 예별 2023.1Q 3칸(순자산 구성 1,211/36/3,823 → 1,686/161/3,224, 헤드라인 합계는 두 판이 같고 2023 세부표는 달력월 헤더) · 삼성생명 2024.2Q 6칸 · 롯데 2025.1Q · NH농협 2024.3Q 항목 13 등.
- **KDB생명 2025.2Q 항목 12(0 → 328)**: 자기 공시는 대시, 후속 둘(FY2025_Q3 v20261011 p18 · FY2025_Q4 p63)이 328 을 인쇄한다. 자기 공시 TFI 표(마스터 항목 47 - 48)의 한도초과분 6,767.35 - 6,439.67 = 327.68억이 328 과 일치하고 기본자본 다리 `2_tier1_bridge` 는 GREEN 을 유지한다.
- **예외 해제 2건(owner 승인 = 이 티켓)**: 롯데손해 2025.1Q 항목 13: 19,202 → 17,997(후속 둘 FY2025_Q2 p20 · FY2025_Q3 p20, 15,657 - 8 - 17,997 = -2,348 = 같은 열 기본자본) · NH농협손해 2024.3Q 항목 13: 8,867 → 9,390(FY2024_Q4 p43 · FY2025_Q1 v20261011 p15, 23,478 - 0 - 9,390 = 14,088 ~ 기본자본 14,089). 박제 `cells` 가 움직여 `TIER2_EXEMPTION_INPUT_DRIFT` · `INERT` 가 발화하므로 `scripts/validate_kics_disclosure.py` 의 `_TIER2_ISSUER_INCONSISTENT` 에서 두 항목을 뺐다(22 → 20, 해제 이력 주석을 남김, 파일의 다른 줄 변경 0). 원장 `kics_exemption_provenance.json` 두 항목은 status `CONTRADICTED`(+ `refuted_by` · `resolved_note`)로 남겼다(재등재 즉시 RED, 한화생명 2025.2Q 선례). `docs/kics_gate_exceptions.md` 를 코드와 맞췄다(표 1행 삭제 · 낡은 「NH농협 2024.3Q 미조사 RED 유지」 항목 교체 · 현행 건수 주석). 다른 예외는 건드리지 않았다.
- **영속화(선례 = 교보 2026.1Q 재작성 장부 `adopted_basis: as_restated`)**: `kics_restatement_ledger.json` 에 재작성 28칸 + 롯데 2023.4Q 활자 오류 1칸(as_filed 2,481 → 24,807) = 29칸을 `adopted_by: owner 2026-10-12` 로 등재하고 `_policy_decisions` 에 결정(인용문 · 범위 · 보류 사유)을 기록했다(기본값 as_filed 불변, 정책 전환 없음, 마스터 값이 자기 공시 인쇄와 이미 달랐던 4칸은 재작성이 아니라 장부에 안 올림). 재빌드 확인(마스터는 안 씀): 사본에 `fill_period --refresh` → `fill_subitems --refresh` → `fill_market_subitems` → `fill_post_transition` 을 11개 분기에 돌린 결과 65칸 중 되돌아감 30(재작성 28 + 삼성생명 2024.2Q 적용후 2) · 활자 오류 2,481 로 바뀜 1(롯데 2023.4Q) · 인쇄 비율로 대체 3(파생 27: 현대해상 2023.1Q · 삼성생명 2024.2Q 전/후, 원래 `recalc` 영역) · 유지 31. 그 사본에 데이터계약 CHECK 7 을 돌리면 `KICS_RESTATEMENT_MASTER_REVERTED_TO_FILED` RED 29(= 장부 29칸)로 전부 잡힌다(조용한 되돌림 없음). `recalc_kics_derived.recalc` 는 65칸 어느 것도 바꾸지 않는다(라이브 · 후보 모두 0). 정기 분기 라운드는 새 분기만 채우므로 영향이 없다. **`fill_*` 를 이 11개 분기에 `--refresh` 로 다시 돌리지 말 것**(알려진 위험: 사본에서 다른 칸 1,881개 · 행 +34 가 함께 움직인다).
- **게이트(전 → 후, 한 번에 하나씩 끝까지)**: K-ICS RED 56 → 54 · YELLOW 1,936 → 1,934 · GREEN 13,705 → 13,709 · SKIP 3,323 불변 · blocking 0 · exit 0(tier2 면제 22 → 20버킷 · finding 42 → 40 · RED 면제 37 → 35). 움직인 status 31건 = GREEN→YELLOW 13 · YELLOW→GREEN 16 · RED→GREEN 1 · RED→YELLOW 1(대부분 ±1~2억 반올림 잔차, 전부 16버킷 안). 데이터계약 RED 0 → 0 · YELLOW 152 → 164(재작성 PINNED 12버킷 신규). `validate_master_tables.py --no-build` 출력 전체가 전후 동일(exit 2 = IFRS17 레인 PL 다리 FAIL, 기존). 마스터 xlsx: 드리프트 65칸(`K-ICS공시` 만) → `sync_master_xlsx_sheet.py "K-ICS공시"` → 0, 나머지 18시트 값이 HEAD 와 같음을 확인(`m1_verify_state.py`).
- **골든 · 시험(고치지 않고 보고, validation 몫)**: `test_kics_rules_golden` 실패 - 픽스처는 변경 전 엔진 출력과 정확히 일치했고(sha · 건수 · by_status 전부) 이 변경만으로 31 finding 이 움직였다(by_status RED 56→54 · YELLOW 1936→1934 · GREEN 13705→13709, buckets 634 · findings 19020 불변). `--update` 이유 문구는 이 항목을 쓴다. `validate_golden_input_fingerprints.py` RED 4(`INPUTS_MOVED`: ifrs17_bs · pl_breakdown · dividend · post_transition, 마스터 +3바이트). 통과: `test_post_transition_golden` · `test_dividend_golden` · `test_master_tables_golden` · `test_golden_input_fingerprint` · 면제 · 식별 · 부재 · 항목 등록부 시험 7파일 · `test_rule_coverage_manifest` 101건(실패 1건은 아래). 등재 해제로 실패하는 시험 3건 - `test_tier2_issuer_inconsistent_exemption`: 등재 수 고정 22 → 20 · `test_a_missing_input_is_red_not_skip[KR0003-2025.1Q-4]` 가 해제된 버킷을 대상으로 씀 · `test_a_pin_that_names_a_branch_catches_a_branch_change_not_only_a_residual` 의 대상이던 NH농협 2024.3Q 가 살아 있는 유일한 갈래 박제였음(대상 소멸, 합성 픽스처 필요). 장부 증가로 1건 - `test_rule_coverage_manifest::test_kics_restatement_census_matches_manifest` 선언 (10, 1, 39, 0) → 실측 (39, 1, 39, 0). (참고: `test_data_contract_selftest` 는 단독 실행 시 `validate_master_tables` 의 import 시점 `sys.stdout.reconfigure` 가 redirect 와 충돌해 실패하나 `validate_data_contract.py --selftest` 직접 실행은 102/102 통과 - 이 변경과 무관.)
- **되돌리는 방법**: `apply_master.py --revert --apply`(계획의 옛값, 마스터 바이트가 시작 sha `bede3bcc0bc6…` 로 정확히 복원됨을 드라이런으로 확인) + 장부 29칸 · 해제 2건 · xlsx 시트가 같이 되돌아가야 하므로 이 변경의 커밋을 `git revert` 하는 것이 가장 단순하다.
- **내 실수(수습 완료)**: 멀티라인 `python -c` 1회(zip 목록, 인코딩 오류로 즉시 종료, 잔류 프로세스 없음). 이후 모든 python 은 스크립트 파일로만 호출했다. `validate_master_tables.py --no-build` 가 다시 쓰는 `data/_derived/qoq_warn.json` 은 다른 레인의 기존 수정 파일이라 커밋에서 제외했다. 작업 중간에 API 한도로 세션이 한 번 끊겼고, 재개 때 마스터 · 장부 · 등재부 · xlsx 를 계획 · `applied_blocks.csv` 와 셀 단위로 다시 대조해 계획 밖 변경 0 을 확인했다(`m1_verify_state.py`).
- **재현**(저장소 루트, python = `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`): `d1_build_plans.py` → 후보 평가 `f0_build_candidate.py` · `f1_gate_candidate.py` · `f2_compare.py` · `f3_datacontract_candidate.py` → `apply_master.py --apply` → `h1_release_registry.py --apply` · `h2_release_provenance.py --apply` · `g1_ledger_update.py --apply` · `g1b_ledger_add_typo.py --apply` → `scripts/sync_master_xlsx_sheet.py "K-ICS공시"` → 게이트 4종 → 확인 `proof_vs_head.py` · `m1_verify_state.py` · `e2_recalc_survival_live.py` · `j1_repro_scratch.py`(사본, 마스터 불변 확인 포함).
"""


def main():
    # ---------------- TODO + archive (LF)
    traw = TODO.read_bytes()
    assert not traw.startswith(b"\xef\xbb\xbf") and b"\r\n" not in traw
    tl = traw.decode("utf-8").split("\n")
    i_status = tl.index("## Status (최신 3개)")
    assert tl[i_status + 1] == ""
    first = i_status + 2
    items = [i for i in range(first, len(tl)) if tl[i].startswith("- **2026-10-12 (")]
    assert len(items) == 3, items
    assert tl[items[2]].startswith("- **2026-10-12 (29회차)"), tl[items[2]][:60]
    i_open = tl.index("## 열린 일")
    cut = tl[items[2]:i_open - 1]            # 29th entry (3 lines), the blank line before '## 열린 일' stays
    assert len(cut) == 3 and tl[i_open - 1] == "", (len(cut), tl[i_open - 1])
    new_tl = tl[:first] + STATUS + tl[first:items[2]] + tl[i_open - 1:]
    # open-items line
    oi = [i for i, l in enumerate(new_tl) if l.startswith(OPEN_OLD_PREFIX)]
    assert len(oi) == 1, oi
    new_tl[oi[0]] = OPEN_NEW
    t2 = "\n".join(new_tl)
    araw = ARCH.read_bytes()
    assert not araw.startswith(b"\xef\xbb\xbf") and b"\r\n" not in araw
    al = araw.decode("utf-8").split("\n")
    assert al[0].startswith("# TODO archive")
    new_al = [al[0]] + cut + [""] + al[1:]
    a2 = "\n".join(new_al)
    # ---------------- changelog (CRLF)
    craw = CHLOG.read_bytes()
    assert not craw.startswith(b"\xef\xbb\xbf")
    ct = craw.decode("utf-8")
    marker = "## 2026-10-12 (이어서 4) - 「최신 공시 직전 컬럼 우선」 원칙 드라이런"
    pos = ct.index(marker)
    assert "이어서 5" not in ct[:pos + 200]
    ins = CHANGELOG.rstrip("\n").replace("\n", "\r\n") + "\r\n\r\n"
    c2 = ct[:pos] + ins + ct[pos:]
    print(f"TODO_parser_kics.md {len(traw)} -> {len(t2.encode('utf-8'))} bytes | archive +{len(a2.encode('utf-8')) - len(araw)} bytes (29th entry cut verbatim: {len(cut)} lines) | changelog +{len(c2.encode('utf-8')) - len(craw)} bytes")
    # verbatim check: the cut lines are exactly the old 29th entry and appear unchanged at the archive top
    assert new_al[1:4] == cut == tl[items[2]:items[2] + 3]
    for l in STATUS:
        assert "\r" not in l
    # no kana / no BOM
    for name, s in (("todo", t2), ("archive", a2), ("changelog", c2)):
        assert not any("\u3040" <= ch <= "\u30ff" for ch in s[:0]) or True
    for l in STATUS + [OPEN_NEW] + CHANGELOG.split("\n"):
        assert not any("\u3040" <= ch <= "\u30ff" for ch in l), l[:80]
    if not apply:
        print("dry run: nothing written")
        return
    assert sha_file(TODO) == sha_bytes(traw) and sha_file(ARCH) == sha_bytes(araw) and sha_file(CHLOG) == sha_bytes(craw)
    TODO.write_bytes(t2.encode("utf-8"))
    ARCH.write_bytes(a2.encode("utf-8"))
    CHLOG.write_bytes(c2.encode("utf-8"))
    for p in (TODO, ARCH, CHLOG):
        b = p.read_bytes()
        assert not b.startswith(b"\xef\xbb\xbf")
        b.decode("utf-8")
    print("WROTE TODO_parser_kics.md, docs/todo_archive_parser_kics.md, docs/changelog_parser_kics.md")


main()
