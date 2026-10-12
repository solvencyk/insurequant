# -*- coding: utf-8 -*-
"""TODO_publishing.md Status 갱신(최신 3개 유지, 밀린 것은 archive 맨 위로 그대로) + changelog_publishing.md 항목."""
from pathlib import Path


def rd(p):
    b = Path(p).read_bytes().decode("utf-8")
    return b.replace("\r\n", "\n"), "\r\n" in b


def wr(p, t, crlf):
    Path(p).write_bytes((t.replace("\n", "\r\n") if crlf else t).encode("utf-8"))


NEW_STATUS = """- **2026-10-12 소진율 도넛 + Forward Outlook 재공개(커밋만 · push 보류)** — 티켓 `20261012T2030Z`: 등재부 재분류(하나생명 제1회·푸본 600·농협생명 제5회·코리안리 제5/6회 -> tier2 확정, 교보 2024-11 type=tier2 + `issuer_type`=tier1) -> 소진율 tier1 만 4사 변경(하나생명 238.2->0.0 · 코리안리 205.1->94.0 · 농협생명 72.7->48.5 · 푸본 42.1->17.3), tier2 불변. forward 가 증권별 계층(기발행 15% · 기본자본형 10% · 보완자본형 기본자본 0)을 따르고 총자본 경로는 47사 불변. 비공개 목록 3종 비움 + 공개 스냅샷 3시트 재생성 (`ef62969`·`2729a53`).
  남은 것: ① designer: K-ICS.html fetch 복원과 같은 커밋에서 `LIVE_ARTIFACT_READERS` 에 루트 JSON 3개 선언(`tests/test_push_gate_wiring.py`) · `tests/test_deploy_assets.py` 의 「fetch 안 함」 단정 뒤집기 · `download-survey.js` 주석 해제 · `report-widget.js` 목록 ② owner: DB손보 2026 신종 3건·하나손해·하나생명은 census 1차가 다르게 읽음(아래 changelog), census 최종본 대조 ③ 증빙 `data/_derived/capsec_reinstate_20261012/`.

"""

# --- TODO
t, crlf = rd("TODO_publishing.md")
head, rest = t.split("## Status (최신 3개)\n\n", 1)
blocks = rest.split("\n\n## 열린 일", 1)
status, tail = blocks[0], "\n\n## 열린 일" + blocks[1]
items = [b for b in status.split("\n\n") if b.strip()]
assert len(items) == 3, len(items)
oldest = items[-1]
status_new = NEW_STATUS + "\n\n".join(items[:2])
t2 = head + "## Status (최신 3개)\n\n" + status_new + tail
t2 = t2.replace("> 갱신 2026-10-12 ·", "> 갱신 2026-10-12 ·", 1)
wr("TODO_publishing.md", t2, crlf)

# --- archive: 제목 바로 아래에 한 글자도 안 고치고
a, acrlf = rd("docs/todo_archive_publishing.md")
title, body = a.split("\n\n", 1)
wr("docs/todo_archive_publishing.md", title + "\n\n" + oldest + "\n\n" + body, acrlf)

# --- changelog
c, ccrlf = rd("docs/changelog_publishing.md")
ENTRY = """## 2026-10-12 — 소진율 도넛 · Forward Outlook 재공개 (티켓 `20261012T2030Z`, 커밋 `ef62969`·`2729a53`, 커밋만 · push 보류)

owner 「분류 근거가 확정돼 소진율 도넛과 Forward Outlook 을 다시 살린다」, 정의(계정 단위 · 해설서 p13 각주 ⑴)는 불변. 증빙 `data/_derived/capsec_reinstate_20261012/`.

- **등재부** `data/bonds/capital_tier_registry.json`: tier2 확정 4사(하나생명 제1회 1,799 · 푸본 2023-02 600 · 농협생명 제5회 2,500 · 코리안리 제5/6회 2,500+2,300) = 증권 6건, `type_unconfirmed` 5건 해제(푸본의 채권원장에 없는 50억만 미확정으로 남음). 교보 2024-11 6,000억은 `type`=tier2(발행조건 스텝업) + 새 필드 `issuer_type`=tier1(발행사 K-ICS 표 처리), 하나생명은 `type`=tier2 + `issuer_type`=tier1. DB손보 5건·하나손해 2건은 분류 불변, 근거 문구에 owner 확정 추가. 새 필드 `issuer_type` 은 `type` 과 다를 때만 적는다(시험이 하나생명·교보 두 건임을 강제).
- **소진율** (`apply_disclosure_utilization.py --quarter 2026.2Q`): tier1 4사만 변경 - 하나생명 238.2->0.0 · 코리안리 205.1->94.0 · 농협생명 72.7->48.5 · 푸본 42.1->17.3. 교보 70.1(결속 쪽이 기발행이라 불변)·tier2 47사 불변. 전후 47사 표 `utilization_before_after_47.csv`, 분자 자기검산 47사 불일치 0(`r7_numerator_selfcheck.txt`).
- **Forward Outlook** (`forward_capital_simulation.py`): 신종 기본자본 기여 = legacy_tfi `min(잔액, SCR_y x 15%)` + tier1 `min(잔액, SCR_y x 10%)`, tier2(보완자본형)는 0 -> 콜은 총자본에서만 빠진다. 한도는 매 연말 SCR 로 다시 계산하므로 「한도 초과로 재분류된 부분이 먼저, 그다음 기본자본」이 자동으로 나온다. 계층 정본은 `issuer_type`(없으면 `type`): 기준시점 기본자본이 회사 공시값이라 콜 차감 계정은 발행사 실제 처리를 따른다. **총자본(지급여력비율) 경로: 47사 전 연도 바이트 동일**(`forward_before_after_summary.txt`: total-path diffs 0, confidence diffs 0). 기본자본비율 경로가 바뀐 회사 11곳. 한화생명 56.76 -> 56.76 -> 56.76 -> 54.97(2029) -> 41.76(2030) 이던 것이 2026~2030 내내 56.76 (신종 4건 전부 보완자본형). 표 `forward_before_after_47.csv`, 손계산(한화생명·DB손보·하나손해·하나생명·교보·메리츠) 불일치 0(`handcheck.txt`).
- **새 필드(additive, 기존 이름·뜻 불변)**: 회사 행 `baseline_basis_flag`(하나생명·교보만 true) · `baseline_basis_note`(기본자본 경로를 발행사 처리 기준으로 계산했고 우리 분류 기준 경로는 `basic_ratio_by_type_pct` 라는 한 줄) · `type_unconfirmed` · `outstanding_hybrid_by_type_eok` · `hybrid_classification[]`(증권별 type/issuer_type/출처). 연도 행 `hybrid_legacy_remaining_eok` · `hybrid_tier1type_remaining_eok` · `hybrid_tier2type_remaining_eok` · `hybrid_limit_tier1type_eok`(SCR x 10%) · `basic_capital_by_type_eok` · `basic_ratio_by_type_pct`(어긋난 회사만) · `basic_ratio_if_tier2_type_pct`(미확정 증권이 있는 회사만). 기존 `hybrid_tier1_eok` = 기본자본 인정분 합, `hybrid_tier2_overflow_eok` = 두 한도 초과 재분류분 합, `hybrid_limit_eok` = SCR x 15% 그대로.
- **재공개**: `export_public_sheets.PRIVATE_SHEETS`·`PRIVATE_ROOT_JSONS`·`android_push_and_deploy.sh PRIVATE_PATHS` 를 비움(메커니즘·시험은 합성 목록 주입으로 유지). main 이 비공개 배포로 6개 경로를 이미 지웠으므로 `NEW_FILES` 에 `kics_tier1_utilization.json` `kics_tier2_utilization.json` `kics_forward_capital.json` `public_exports/{기본자본소진율,보완자본소진율,자본비율전망}.json` 추가. `public_exports` 3시트 신규 + manifest, 다른 13시트 바이트 동일. xlsx 시트 `기본자본소진율`(10칸·6행 교체)·`자본비율전망`(127칸·3행 교체)은 `sync_master_xlsx_sheet.py` 로, 열 구성 불변, `check_master_xlsx_drift` 드리프트 0.
- **되돌리는 방법**: `PRIVATE_SHEETS = ("기본자본소진율", "보완자본소진율", "자본비율전망")` · `PRIVATE_ROOT_JSONS = (3개 파일)` 복원 + 배포 스크립트 `PRIVATE_PATHS` 에 같은 6개 경로 복원(+ NEW_FILES 에서 6개 제거) + exporter 재실행. 분류만 되돌리려면 registry 커밋 `ef62969` 의 해당 줄을 되돌리고 `apply_disclosure_utilization.py` -> `forward_capital_simulation.py` 순으로 재실행.
- **미결/불일치 보고**: (a) census 최종본 `census_securities_final.csv` 는 작업 시작·종료 시점에 없었다(1차 census 로 대조). 1차 census 는 DB손보 2026 신종 3건(4,420+4,100+300)을 tier2(확정도 b, 발행사 항목 47 +4,536 ~ 액면)로, 하나생명 제1회를 tier1(확정도 b, 발행사 표 항목 47 < 액면)로 읽어 owner 확정(DB 5건 tier1 · 하나생명 tier2)과 다르다 - 등재부는 owner 확정을 따랐다(DB 3건은 `issuer_type` 도 달지 않았다: 항목 2 시계열이 기본자본 처리와 모순되지 않아 발행사 처리를 단정하지 못함). (b) 하나생명·교보는 발행사 처리와 분류가 달라 `baseline_basis_flag`. (c) 경과조치 기발행분 15% 는 2032 까지라 전망 범위(2026~2030) 안이다 - 2032 이후 처리는 범위 밖이라 모델에 넣지 않았다. (d) 한도 분모는 종전대로 보간한 SCR_y (규정상 Ⅵ.1.라 경과조치 적용 전 총요구자본과의 차이는 종전 모델과 같다). (e) 하나손해 2026-06 신규 신종(약 1,000억)은 채권원장 미등재라 콜 차감에 안 들어간다(콜 2031 이후라 범위 밖).
- 시험: `tests/unit/test_capital_utilization_rules.py`(재분류 이유로 값 4개 갱신 + 변이 3건 추가) · 신규 `tests/unit/test_forward_capital_tiers.py` 13건(한도 분리·보완자본형 기본자본 불변·총자본 불변·종전식 재현·issuer_type 플래그·미확정 대체 경로·한도 비율 변이·유형 뒤집기 변이·배포본 == 모델) · `test_private_deploy` 14 · `test_push_gate_wiring` 63(1 skip) · `test_deploy_assets` 12 · `test_rule_coverage_manifest` 102. 게이트 `validate_data_contract` RED=0 · `validate_live_artifacts` RED=0(baselined 25) · `check_master_xlsx_drift` 0.

"""
marker = "---\n\n"
i = c.index(marker) + len(marker)
c = c[:i] + ENTRY + c[i:]
wr("docs/changelog_publishing.md", c, ccrlf)
print("docs ok")
