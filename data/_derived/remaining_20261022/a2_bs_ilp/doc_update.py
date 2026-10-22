import io
R = "C:/Users/sangwook.cho/Desktop/insurequant/"
E = "data/_derived/remaining_20261022/a2_bs_ilp/"
# ---- TODO status
p = R + "TODO_parser_ifrs17.md"
raw = open(p, "rb").read().decode("utf-8")
crlf = "\r\n" in raw
t = raw.replace("\r\n", "\n")
marker = "## Status (최신 3개)\n\n"
assert marker in t
entry = (
"- **2026-10-22 17차: 교보생명 KR0073 2023.4Q 재무상태표·보험계약부채 블록을 재작성 전기말 열로 이동(오케스트레이터 지시, 9칸 한 묶음)** — `IFRS17_BS` 2023.4Q 항목 1·2·3·20·31 + 2024.4Q 항목 1(2026-10-12 부분 블록 완결) · ILP 2023.4Q 항목 10·14·15. "
"FY2024·FY2025 사업보고서 별도 재무상태표 2023-12-31 열(두 필링 동일) 줄 번호 재독, 1=2+3 잔차 0, 이익잉여금 롤(5,920,420+632,201-51,250-74,245)=6,427,126=항목 31, 효과표 note 44-2 수정전=옛 마스터값.\n"
"  경로: `bs_manual_overrides.json` +6 → 저장소 `build_ifrs17_bs.py`(마스터는 HEAD 대비 정확히 6셀만 변동, 11,016행 불변) · ILP는 가드 적재(`scripts/apply_kr0073_bs_ilp_restated_20261022.py`: 오버레이·ILP 3셀·출처표 셀·사이드카 `ilp_restated_comparative.json` +1셀). BS 골든 `--update`(해시 8383552c→d585abe2)·입력 지문 `--update`(ifrs17_bs만 변동)·BS 골든 재실행 통과(506초).\n"
"  게이트 전→후: 데이터계약 RED 1→4(전부 xlsx 시트 `17BS` · `보험계약부채` 동기화 지연) · master_tables 출력 동일(PL_OCI_VS_BS_AOCI 불변: 항목 4 미접촉) · ILP 두 검증기 RED 0 불변 · 연속성/뷰 골든 2종/master_tables 골든 통과 · rule_coverage 실패 2건은 전과 동일(xlsx·public_exports 청결 상태).\n"
"  남은 것: publishing = xlsx `17BS` 6셀·`보험계약부채` 4행 동기화, `panel_csm_combo`·`panel_compare`·`public_exports` 재생성(화면 반영) / 보류 그대로: AOCI 5칸(티어 B)·중간분기 자본·ILP 2023.1Q~3Q 14/15(티어 C)·FY2025 기초(ALT, owner 결정). 커밋 안 함.\n"
"  근거·재현 `" + E + "`(`v1_verify_filing.py` · `d1_bs_diff.txt` · `gate_before_*`/`gate_after_*` · `apply_kr0073_bs_ilp_restated_20261022.py --revert --backup-dir <dir>`) · `docs/changelog_parser_ifrs17.md` 17차.\n"
)
t = t.replace(marker, marker + entry, 1)
open(p, "wb").write((t.replace("\n", "\r\n") if crlf else t).encode("utf-8"))
# ---- changelog
c = R + "docs/changelog_parser_ifrs17.md"
raw = open(c, "rb").read().decode("utf-8"); crlf = "\r\n" in raw; t = raw.replace("\r\n", "\n")
m = "## 2026-10-22 (16차:"
assert m in t
body = (
"## 2026-10-22 (17차: 교보생명 KR0073 2023.4Q BS·ILP 재작성 블록 — 오케스트레이터 지시)\n\n"
"커밋 안 함, push 안 함. 서브에이전트·docling 안 씀. `build_root_masters.main()`·xlsx·public_exports·viz 패널 미접촉(panel_csm_combo 재생성 안 함). 증거 `" + E + "`.\n\n"
"- **확인**: 사업보고서 XML(FY2025_Q4 L46626-46774, FY2024_Q4 L49707-50117·L63748-63775)을 ACODE·ACONTEXT(별도)·줄 번호로 독립 재독(`v1_verify_filing.py`) — FY2024 전기 열 = FY2025 3번째 열 5항목 일치, 1=2+3 잔차 0원, SOCE 이익잉여금 롤 `v2_re_roll.py` 차이 0, 소급재작성 효과표(L75166-75301) 수정전 = 옛 마스터값 5개 일치, ILP 마감행 83,536,489+1,013,643+2,692,746 → 14=845,501.32억, 15=BS20/100=872,428.79억.\n"
"- **적재**: `apply_kr0073_bs_ilp_restated_20261022.py --apply`(가드·백업·적재 후 셀 단위 검증): 오버레이 +6, ILP 3셀(항목 10 +0.01은 10+14=15 반올림 폐합, 항목 13 인쇄 LIC는 26927.46 유지), 출처표 `original_basis_value` 등, 사이드카 +1셀(화면 구간3에 재작성 표시). BS 마스터는 `build_ifrs17_bs.py` 산출 그대로 — HEAD 대비 6셀(값 필드만), 11,016행, `bs_carry_forward_cells.json` 불변(`d1_bs_diff.py`).\n"
"- **골든**: `tests/test_ifrs17_bs_golden.py --update`(sha256 8383552c→d585abe2) 후 재실행 통과 506초, `validate_golden_input_fingerprints.py --update` 로 ifrs17_bs 항목만 갱신(RED 2→0).\n"
"- **게이트 전→후**: 데이터계약 RED 1→4(xlsx `17BS` 6셀, `보험계약부채` 행 4건 누락/초과 = 시트 동기화 지연), YELLOW 169 불변 · master_tables 출력 동일 · ILP lic/portfolio RED 0 불변 · 연속성 불변 · 뷰 골든 2종·master_tables 골든 통과 · rule_coverage 2건 실패는 적재 전과 같음.\n"
"- **화면(억원)**: IFRS17.html 패널 1, 교보 2023.4Q — 자산총계 115조 796억→115조 25억 · 부채총계 105조 3,172억→105조 268억 · 자본총계 9조 7,624억→9조 9,758억 · 보험계약부채 87조 5,333억→87조 2,429억 · 이익잉여금 6조 2,138억→6조 4,271억; 2024.4Q 자산총계 122조 4,090억→122조 4,086억. compare.html ROE(연환산) 2024.1Q 14.6→14.5 · 2Q 15.2→15.0 · 3Q 14.3→14.1 · 4Q 8.2→8.1(2025.1Q~ 불변).\n"
"- **남은 것**: publishing xlsx 두 시트·`panel_csm_combo`·`panel_compare`·`public_exports` / 보류: AOCI 5칸·중간분기 자본·ILP 2023.1Q~3Q 14/15·FY2025 기초(ALT).\n\n"
)
t = t.replace(m, body + m, 1)
open(c, "wb").write((t.replace("\n", "\r\n") if crlf else t).encode("utf-8"))
print("ok", crlf)
