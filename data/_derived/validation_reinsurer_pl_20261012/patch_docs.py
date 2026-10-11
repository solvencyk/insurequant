# -*- coding: utf-8 -*-
"""TODO_validation.md Status: 새 항목을 맨 위에 넣고 가장 오래된 23차 블록을 archive 로 무수정 이동. changelog 항목 추가."""
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
todo_p = ROOT / "TODO_validation.md"
arch_p = ROOT / "docs" / "todo_archive_validation.md"
chg_p = ROOT / "docs" / "changelog_validation.md"

todo = todo_p.read_text(encoding="utf-8")
lines = todo.split("\n")
# 23차 블록 = '- **2026-10-11 (23차)' 로 시작하는 줄부터 다음 빈 줄 직전까지
start = next(i for i, l in enumerate(lines) if l.startswith("- **2026-10-11 (23차)"))
end = start
while end + 1 < len(lines) and lines[end + 1].startswith("  "):
    end += 1
block = lines[start:end + 1]
del lines[start:end + 1]

new_status = [
    "- **2026-10-12 재보사 PL 계보 허용 + 마감 골든 4종 `--update` — 데이터계약 RED 102→0(전부 `CONCEPT_MIXED_DISCLOSURE_INTO_DART`, 신규 0)** — `PL_DISCLOSURE_REINSURER_LINEAGE`"
    "(how=`disclosure_summary_pl_reinsurer`, 항목 17·20·21)을 「DART 계보 PL 셀이 없는 회사」(데이터 조건 · 8곳 KR1101~KR1108)·income_statement·쪽·**항목별** 인쇄값이 있을 때만 §3d 에서 뺀다(102셀/299값).",
    "  변이시험 pytest 14건 + selftest 92→102(Q11 가족)·훅 묶음 편입. 골든 `--update`: master_tables(재보사 적재 반영)·17BS(+49칸, 빌더 산출=마스터 sha)·입력지문 / PL·viz 2종·kics·post_transition·dividend 는 무이동. 훅 대체 `prepush_check.py --full` = **gate-clear exit 0**(데이터계약 RED 0 · K-ICS clear · 도메인 7종 pass · 지문 pass · JS clear · inbox 위반 0 · 오프라인 795 통과 1 skip). 남은 것: owner 결정표(티켓 §5).",
]
# 맨 위에 삽입
head_idx = next(i for i, l in enumerate(lines) if l.startswith("## Status"))
lines[head_idx + 2:head_idx + 2] = new_status
lines[2] = "> 갱신 2026-10-12 (재보사 PL 계보 허용) · 프롬프트 `docs/agents/claude-agent-validation.md` · 이력 `docs/changelog_validation.md`"
todo_p.write_text("\n".join(lines), encoding="utf-8", newline="")

arch = arch_p.read_text(encoding="utf-8")
marker = "# TODO archive — `TODO_validation.md` (Status 이력, 읽기 지연)\n\n"
assert arch.startswith(marker)
section = "## 2026-10-12 Status 밀림 (재보사 PL 계보 허용 항목 추가로 밀려난 항목, 무수정)\n\n" + "\n".join(block) + "\n\n"
arch_p.write_text(marker + section + arch[len(marker):], encoding="utf-8", newline="")

chg = chg_p.read_text(encoding="utf-8")
anchor = "## 2026-10-12 -- 게이트 속도"
assert chg.count(anchor) == 1
entry = (
    "## 2026-10-12 -- 재보사 PL 경영공시 계보 허용 + 마감 골든 (티켓 `20261012T0600Z`)\n\n"
    "- **원인**: parser `3727438` 이 재보사 8곳(KR1101~KR1108)의 PL 투자손익(17)·영업이익(20)·영업외손익(21)을 경영공시 §2-1 요약 포괄손익계산서에서 적재했다. §3d `CONCEPT_MIXED_DISCLOSURE_INTO_DART` 는 DISCLOSURE 계보 PL 셀을 동일개념 5항목(1·16·22·23·24)으로 제한해 **102건 RED**(셀 102 / 값 299). "
    "17·20·21 이 reference_only 인 이유는 같은 회사 시계열에 DART 개념과 경영공시 개념이 섞이기 때문인데, 이 8곳은 DART 사업보고서가 없어 원천이 하나뿐이다(항목 4 주석 허용 `1db7c2d` 와 같은 구조).\n"
    "- **수정(좁게)**: `validate_data_contract.py` `PL_DISCLOSURE_REINSURER_LINEAGE = {disclosure_summary_pl_reinsurer: {17,20,21}}` + `_pl_dartless_companies`(사이드카 셀이 전부 DISCLOSURE 계보이고 마스터 발행 블록이 전부 사이드카에 정확 키로 있는 회사 -- 코드 목록이 아니라 데이터 조건) + `_pl_reinsurer_exempt_items`"
    "(income_statement · 등재 how · DISCLOSURE 경로 · 쪽 · **항목별** 인쇄값 dict). 그 entry 의 items ∩ 등재 항목 **한 칸씩**만 뺀다. 항목 4 때와 달리 셀 `resolution` 은 기본 적재 라벨(`disclosure_summary_pl`)이라 how==resolution 비교는 못 한다 -- 대신 항목별 인쇄값을 요구한다. 매 실행 건수·회사를 notes 에 인쇄한다.\n"
    "- **시뮬레이션(양방향)**: 데이터계약 RED 102 -> **0**, YELLOW 147 -> 147, 새 RED 0. 게이트가 센 수혜 = 102셀/299값/8곳 = 사이드카 `how` 사용 105 entry 중 17/20/21 포함분과 일치. 라이브 사이드카 전체에서 「DART 계보 없는 회사」 = 정확히 KR1101~KR1108 8곳.\n"
    "- **변이시험**: `tests/test_pl_reinsurer_disclosure_lineage.py` 14건(허용 삭제·항목 확대·how 검사 제거·항목별 인쇄값 제거·dict 검사 제거·쪽 검사 제거·블록 검사 제거·**회사 조건 제거**·AND->OR·발행블록 검사 제거·entry 밖 항목까지 제외 = 11 변이 + 대조군 + 범위 박제 + 라이브 사이드카 대조/트립와이어). selftest 92 -> 102(Q11~Q11j). `prepush_check.py` 오프라인 묶음에 편입.\n"
    "- **관측(미수정)**: `verify_provenance_sidecar` 가 (회사,분기) 블록불문 폴백 매칭을 해서, 마스터가 발행하는 블록이 사이드카에 정확 키로 없어도 `MISSING_PROVENANCE` 가 안 난다. 라이브는 발행 1,040블록 전부 정확 키가 있어 지금은 무해(probe `data/_derived/validation_reinsurer_pl_20261012/probe_fallback.txt`). 허용 쪽은 정확 키로 따로 막았다.\n"
    "- **골든**: `--update` 3종 = `master_tables`(closing 390->393P, pl_bridge 3456->3653P(진짜 1177->1278·구성상 1944->2040)·S 2945->2748, csm_amort_identity 380->383P, qoq_warn 262->267Y; F/NEW 불변) · `ifrs17_bs`(빌더 산출 sha = 현 마스터 sha `ef70b02`, 10,967->11,016행 = BS +49칸) · 입력지문(`ifrs17_bs` 재생성 + `viz_ifrs17_panels` 입력 5.4KB 이동 -- 산출 바이트 불변이라 지문만). "
    "무이동: PL 골든(`RUN_PL_GOLDEN=1`, 해시 전부 일치) · viz 2종(4패널·csm_waterfall 바이트 동일) · kics 룰 · post_transition · dividend.\n"
    "- **훅**: `prepush_check.py --full` 직접 실행 = gate-clear, exit 0 (오프라인 795 통과 · 1 skip, 부하 큰 PC 에서 34분). push 는 안 함.\n"
    "- `PL_YTD_COLLAPSE_TO_ZERO` RED 0 (parser 가 인쇄된 0 7칸을 보류 -- 등재 안 함).\n\n"
)
chg = chg.replace(anchor, entry + anchor)
chg = chg.replace("> Last updated: 2026-10-11 (24차)", "> Last updated: 2026-10-12 (재보사 PL 계보 허용)", 1)
chg_p.write_text(chg, encoding="utf-8", newline="")
print("ok", len(block), "lines moved")
