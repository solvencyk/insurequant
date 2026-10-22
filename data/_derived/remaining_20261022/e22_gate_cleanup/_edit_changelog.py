from pathlib import Path
p = Path(__file__).resolve().parents[4] / "docs" / "changelog_validation.md"
raw = p.read_bytes()
txt = raw.decode("utf-8")
assert not txt.startswith("\ufeff")
nl = "\r\n" if "\r\n" in txt else "\n"
marker = "## 2026-10-22 (31차)"
assert txt.count(marker) == 1
entry = """## 2026-10-23 (32차) -- 최신 비교열 적재 뒤 죽은 등재 7줄 철거 + `PL_OCI_VS_BS_AOCI` 「공란 칸을 비교가능으로 센다」 계수 결함 수정 (대상 HEAD `62ba44ed`, 티켓 `20261023T0030Z`, 증거 `data/_derived/remaining_20261022/e22_gate_cleanup/`)

- **범위**: 마스터·골드 오버레이 값 파일·예외는 건드리지 않았다. 등재는 **삭제만** 했고(추가 0, 허용오차 확대 0) 게이트 코드 1곳 · 시험 2곳 · fixture 1개를 바꿨다. 커밋·push 없음.
- **JOB 1 철거 7줄(전부 게이트가 먼저 죽었다고 인쇄한 것)**: `pl_bridge_baseline.json` 5줄 -- master_tables 2d 가 `FIXED?` 로 인쇄(KB라이프 2024.1Q 보험손익(dual) · 롯데손해 2023.2Q · 메리츠화재 2023.2Q(dual) · 한화생명 2023.1Q · 2023.2Q 보험손익(leg-coverage)) ·
  `pl_csm_amort_missing_ledger.json` 롯데손해 2023.1Q 1줄 -- data_contract 가 `PL_CSM_AMORT_MISSING_LEDGER_INERT` 로 인쇄(마스터를 직접 읽어 확인: PL 원수CSM상각 39,284백만 = 392.84억 = 워터폴 상각 -392.84억, 실제로 채워졌다) ·
  `WFY_EXCEPTIONS` 한화생명 FY2023 · 메리츠화재 FY2023 2줄 -- 게이트가 인쇄하는 문구는 없다(면제는 걸려야만 WFYEX 로 보인다). 그래서 `probe_wfy_exceptions.py` 로 면제 8개를 비우고 두 소비처(master_tables WFY 축 · `validate_csm_continuity` within-FY 축)를 직접 돌렸다:
  적재 직전 마스터(`3e53aef8`)에서는 메리츠 FY2023(양쪽 걸림) · 한화생명 FY2023(master_tables 걸림) 이 필요했고, 지금은 둘 다 안 걸린다(`probe_wfy_exceptions_before_loads.txt` 대 `probe_wfy_exceptions.txt`). 교보 FY2023 은 두 축 모두 여전히 걸려 유지.
- **철거 전후 게이트**: `validate_master_tables --no-build` exit 2 -> 2 · SUMMARY 한 글자도 안 움직임 · 2d `등재부에만 남은 것` 5 -> 0 · 기지 18 / 신규 0 불변. `validate_data_contract` RED 0 -> 0 · YELLOW 169 -> 168(INERT 1줄 소멸, 나머지 168줄은 정렬 후 동일). `validate_csm_continuity` red 0 · flagged 1(교보) 불변. 시험 248 통과 · 1 skip.
- **철거 안 한 것(근거)**: `WFY_EXCEPTIONS` 의 KB라이프 FY2024 · 교보 FY2024 · 에이비엘 FY2023 · KDB생명 FY2023 · 현대해상 FY2023 5줄은 **적재 전(`3e53aef8`)에도 이미 안 걸렸다** -- 이번 적재가 죽인 것이 아니고 게이트가 죽었다고 말하지도 않는다(owner 등재라 이 세션 범위 밖, 아래 owner 결정). `GOLD_OVERLAY_REDUNDANT`(CSM 77 · PL 22칸이 소스와 같음)는 오버레이 값 파일이라 무수정. `EXEMPTION_ABSENCE_PIN_VALUE_PRESENT` KR0097 2024.4Q 는 K-ICS 장부라 이번 적재와 무관.
- **JOB 2 결함**: `_check_pl_oci_vs_bs_aoci` 가 PL 항목25 `값_당분기` 가 None 인 칸을 건너뛰면서도(`continue`) 「비교가능 N건은 tol 이내」를 `len(pl_dangi) - n_skip - len(rows)` 로 세어 공란 칸이 통과로 집계됐다. `load_pl_dangi` 소비처는 이 함수 하나뿐이고, 값_당분기를 읽는 다른 `_check_*` 는 없다(grep 전수) -- 같은 모양의 계수 결함은 이 칸 하나.
- **전 버킷 시뮬레이션(`sim_oci_counting.py`, 항목25 374버킷 x 적재 8단계 + 작업트리)**: 작업트리 기준 현행 인쇄 「비교가능 340」 = 실제 비교 232 + 공란 108. 정정 후 = 비교한 258건 중 tol 이내 232 · flag 26 · 비교 못 함 = 공란 108 + BS 결측 8(2023.1Q 5칸은 직전 분기가 없어 구조적). 단계별 과대집계 = 공란 수(`b8c37fff` 109 · `5419a817` 122 · 지금 108). flag 집합은 두 계수에서 동일(판정식 불변; 게이트 줄 26개 diff 0).
  공란 때문에 YELLOW 에서 사라진 행(적재 전후 단계 비교): 4건 -- NH농협손해 2023.4Q(resid +40,909.6) · 농협생명 2024.4Q(-31,361.1) · 동양생명 2024.4Q(+35,860.7) · KB손해 2023.4Q(+77,358.0). 값이 고쳐져서 닫힌 행은 교보 2023.4Q 1건. 참고용 그림자(게이트 입력 아님): 지금 공란 108칸 중 BS 두 분기+누계 값이 있어 누계 차로 재구성 가능한 17칸 중 6칸이 tol 을 넘는다(농협생명 2024.4Q -39,298 · 미래에셋생명 2023.4Q -36,084 · 동양생명 2024.4Q +32,151 · 한화생명 2025.3Q -22,291 · 농협생명 2025.3Q · 흥국생명 2025.3Q).
- **수정**: 공란 칸을 `n_blank` 로 따로 세고 인쇄를 `비교한 N건 중 tol 이내 M건 | 비교 못 함: 단일분기 공란 B건 + BS 결측 S건` 으로 바꿨다. SUMMARY 필드 `oci_vs_bs_aoci:26Y` -> `26Y/108blank/8bsskip`(`counts_out` 인자 방식, 반환값 불변이라 호출자 영향 0).
- **시험**: `tests/test_master_tables_golden.py::test_oci_vs_bs_aoci_counts_blank_cells_as_not_compared` 신설 -- 합성 마스터(통과 1 · 공란 1 · 진짜 불일치 1 · BS 결측 1)로 계수 `{compared 2, blank 1, bs_skip 1, flagged 1}` 와 flag 집합 `[(A, 2024.4Q)]` 를 박제한다. 변이(`n_compared` 에서 `n_blank` 제외 삭제)를 넣으면 FAIL 하는 것을 확인했다. 기존 단언은 하나도 약화하지 않았다. `tests/test_identity_registry.py` 의 `pl_oci_vs_bs_aoci` reason 에 새 SUMMARY 형식을 적었다.
- **골든**: `tests/fixtures/master_tables_golden.json` 은 `--update` 로 재생성. 이동 원인 = 새 SUMMARY 필드 `oci_vs_bs_aoci` 뿐(수정 전 fixture 가 직전 상태와 일치했고, JOB 1 철거는 SUMMARY 를 움직이지 않았다).
- **부작용 파일**: 게이트 실행이 `data/_derived/nb_csm_validation.json` · `data/dart/viz/csm_continuity_validation.json`(메리츠 FY2023 면제 표시 소멸 = 위 철거의 실제 효과) · `csm_waterfall_validation.json` 을 다시 썼다(커밋 판은 적재 이전). `qoq_warn.json` · `pl_oci_vs_bs_aoci_warn.json` 은 바이트 불변.

"""
txt = txt.replace(marker, entry.replace("\n", nl) + marker, 1)
txt = txt.replace("> Last updated: 2026-10-22 (31차", "> Last updated: 2026-10-23 (32차 죽은 등재 7줄 철거 + OCI 대 BS AOCI 공란 계수 수정 · 31차", 1)
p.write_bytes(txt.encode("utf-8"))
print("ok")
