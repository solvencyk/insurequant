# -*- coding: utf-8 -*-
"""scripts/extract_kics_rate_sensitivity.py 의 2026-10-11 규칙 5개 — 재보사 금리민감도 수작업 정정 8쌍을 추출기가 스스로 재현하도록 한 것(runlog 13 §4).

  1. 잘린 라벨 「지급여력기준금」 = 기준금액 행 (제네럴 2024.4Q·2025.4Q)
  2. 쪽 넘김 첫 행: 머리행 바로 아래 6칸 행(구분 칸에 경과조치 라벨 없음)을 되살린다 (제네럴 2025.4Q p27→p28)
  3. 「0 인쇄 = 비어 있음」: 전 칸 0 인 블록은 빈 블록 (하노버 2025.2Q·2025.4Q·2026.2Q 후 블록)
  4. 단위 환산: 적용전 금액 base 대 헤드라인(억원)이 100·100000 배면 금액 계열만 나눈다 — 머리말 단위(「억원」 오기 포함)를 믿지 않는다 (뮌헨 2025.4Q·스위스리 2024.4Q 등)
  5. 비적용사 후 블록 미러: 등재부 NON_APPLIER_POST_MIRROR 에 있는 (회사, 분기)만 후 블록이 공란·0 일 때 적용전을 옮긴다 (하노버 4분기). 등재 안 된 회사는 그대로 후 구멍.
그리고 기존 동작 불변(7칸 표·정상 후 블록)을 같이 고정한다.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import extract_kics_rate_sensitivity as X  # noqa: E402

# 제네럴재보험 FY2025_Q4 MD 의 실제 모양(쪽 넘김으로 갈라진 두 표 + 잘린 라벨)
GENERAL_2025_4Q = """| 구분     |   기준금액 |   △ 100bp |   △ 50bp |   +50bp |   +100bp |
|--------|--------|-----------|----------|---------|----------|
| 지급여력비율 | 258.42 |    234.00 |   243.84 |  263.79 |   275.42 |

| 경과조치전   | 지급여력금액   |    840 |    861 |    850 |    831 |    823 |
|---------|----------|--------|--------|--------|--------|--------|
|         | 지급여력기준금액 |    325 |    368 |    349 |    315 |    299 |
|         | 지급여력비율   | 258.42 | 234.00 | 243.84 | 263.79 | 275.42 |
| 경과조치후   | 지급여력금액   |    840 |    861 |    850 |    831 |    823 |
|         | 지급여력기준금  |    325 |    368 |    349 |    315 |    299 |""".splitlines()

# 하노버재보험 FY2025_Q2 MD 의 실제 모양(백만원 + 후 블록 0 인쇄)
HANNOVER_2025_2Q = """| 구분   | 구분       | 기준금액    | △ 100bp   | △ 50bp   | +50bp   | +100bp   |
|------|----------|---------|-----------|----------|---------|----------|
| 경    | 지급여력비율   | 193.63% | 177.51%   | 185.52%  | 201.85% | 210.25%  |
| 과 조  | 지급여력금액   | 57,910  | 57,910    | 57,910   | 57,910  | 57,910   |
| 치 전  | 지급여력기준금액 | 29,907  | 32,624    | 31,215   | 28,689  | 27,543   |
| 경    | 지급여력비율   | 0       | 0         | 0        | 0       | 0        |
| 과 조  | 지급여력금액   | 0       | 0         | 0        | 0       | 0        |
| 치 후  | 지급여력기준금액 | 0       | 0         | 0        | 0       | 0        |""".splitlines()


def test_truncated_measure_label_is_the_criterion_amount():
    assert X.match_measure("지급여력기준금") == "지급여력기준금액"
    assert X.match_measure("지급 여력 기준 금") == "지급여력기준금액"
    assert X.match_measure("지급여력기준금액") == "지급여력기준금액"
    assert X.match_measure("지금여력기준금액") == "지급여력기준금액"       # 지금/지급 오탈자
    assert X.match_measure("지급여력금액") == "지급여력금액"
    assert X.match_measure("지급여력비율") == "지급여력비율"


def test_page_break_first_row_and_truncated_label_give_full_blocks():
    rows = X.measure_rows(GENERAL_2025_4Q)
    assert [m for _f, m, _v in rows] == ["지급여력비율", "지급여력금액", "지급여력기준금액", "지급여력비율", "지급여력금액", "지급여력기준금액"]
    assert rows[0][0] == "" and rows[0][2] == [258.42, 234.0, 243.84, 263.79, 275.42]
    blocks = X.split_blocks(rows)
    assert [X.block_phase(b) for b in blocks] == ["적용전", "적용후"]
    pre, post = (X.block_dict(b) for b in blocks)
    assert set(pre) == set(post) == {"지급여력비율", "지급여력금액", "지급여력기준금액"}
    assert post["지급여력기준금액"] == [325.0, 368.0, 349.0, 315.0, 299.0]


def test_six_cell_row_is_only_revived_directly_under_a_header_row():
    # 머리행이 아닌 곳의 6칸 행(예: 표 중간)은 종전처럼 버린다
    tbl = ["| 경과조치전 | 지급여력비율 | 1 | 2 | 3 | 4 | 5 |", "| 지급여력금액 | 1 | 2 | 3 | 4 | 5 |"]
    assert [m for _f, m, _v in X.measure_rows(tbl)] == ["지급여력비율"]


def test_standard_seven_cell_table_is_unchanged():
    tbl = ["| 구분 | 구분 | 기준금액 | △ 100bp | △ 50bp | +50bp | +100bp |", "|---|---|---|---|---|---|---|",
           "| 경과조치전 | 지급여력비율 | 200.0 | 190.0 | 195.0 | 205.0 | 210.0 |",
           "|  | 지급여력금액 | 2,000 | 1,900 | 1,950 | 2,050 | 2,100 |"]
    rows = X.measure_rows(tbl)
    assert rows == [("경과조치전", "지급여력비율", [200.0, 190.0, 195.0, 205.0, 210.0]), ("", "지급여력금액", [2000.0, 1900.0, 1950.0, 2050.0, 2100.0])]


def test_all_zero_block_is_an_empty_block():
    assert X.block_dict([("", "지급여력비율", [0.0] * 5), ("", "지급여력금액", [0.0] * 5)]) is None
    assert X.block_dict([("", "지급여력비율", [None] * 5)]) is None                         # 대시·공란은 종전대로
    d = X.block_dict([("", "지급여력비율", [0.0, 0.0, 1.5, 0.0, 0.0])])
    assert d == {"지급여력비율": [0.0, 0.0, 1.5, 0.0, 0.0]}                                  # 하나라도 값이 있으면 블록이다


def test_unit_factor_from_headline_anchors():
    A = {"지급여력금액": 2919.0, "지급여력기준금액": 1076.0}
    assert X.unit_factor({"지급여력금액": 291894.0, "지급여력기준금액": 107560.0}, A) == 100.0          # 백만원 (머리말이 억원이라 적혀 있어도)
    assert X.unit_factor({"지급여력금액": 291894.0 * 1000, "지급여력기준금액": 107560.0 * 1000}, A) == 100000.0   # 천원
    assert X.unit_factor({"지급여력금액": 2918.94, "지급여력기준금액": 1075.6}, A) == 1.0              # 이미 억원
    assert X.unit_factor({"지급여력금액": 291894.0, "지급여력기준금액": 1075.6}, A) == 1.0            # 두 금액이 서로 다른 배율이면 환산하지 않는다
    assert X.unit_factor({"지급여력금액": 291894.0}, {"지급여력금액": None, "지급여력기준금액": None}) == 1.0   # 앵커 없음
    assert X.unit_factor({"지급여력금액": 5000.0, "지급여력기준금액": 3700.0}, A) == 1.0              # 100 도 100000 도 아닌 배율은 건드리지 않는다


def test_scale_amounts_exact_and_ratio_untouched():
    d = {"지급여력비율": [258.42, 234.0, 243.84, 263.79, 275.42], "지급여력금액": [306931.0, 299412.0, None, 284923.0, 277951.0],
         "지급여력기준금액": [882478577.0, 1.0, 2.0, 3.0, 4.0]}
    s = X.scale_amounts(d, 100.0)
    assert s["지급여력비율"] == d["지급여력비율"]
    assert s["지급여력금액"] == [3069.31, 2994.12, None, 2849.23, 2779.51]
    assert X.scale_amounts({"지급여력기준금액": [882478577.0]}, 100000.0)["지급여력기준금액"] == [8824.78577]
    assert X.scale_amounts(d, 1.0) is d


def _run_main(tmp_path, monkeypatch, code, md_text, anchors):
    md_dir = tmp_path / "md_inbox" / "FY2025_Q2"
    md_dir.mkdir(parents=True)
    (md_dir / f"{code}_회사.md").write_text("# 6-8\n\n## 3) 금리 민감도 분석\n\n( 단위 : 백만원 , %)\n\n" + md_text + "\n\n## 다음\n", encoding="utf-8")
    disc = [{"원보험사코드": code, "원수사명": "회사", "티커": "X", "생손보여부": "생명보험", "공시분기": "2025.2Q", "항목번호": i, "항목명": n, "값": str(v), "값_적용후": str(v)}
            for i, n, v in anchors]
    (tmp_path / "kics_disclosure.json").write_text(json.dumps(disc, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(X, "MD_INBOX", tmp_path / "md_inbox")
    monkeypatch.setattr(X, "DISC_JSON", tmp_path / "kics_disclosure.json")
    monkeypatch.setattr(X, "OUT_JSON", tmp_path / "out.json")
    monkeypatch.setattr(X, "DIAG_JSON", tmp_path / "diag.json")
    # main() 은 첫 줄에서 sys.stdout 을 새 TextIOWrapper 로 갈아 끼운다 — pytest 의 캡처 스트림이 닫히지 않게 버퍼가 따로인 가짜 stdout 을 둔다.
    fake_stdout = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")   # 참조를 잡아 둔다: 가비지 컬렉션되면 공유 버퍼가 닫혀 main() 의 새 래퍼가 쓰지 못한다
    monkeypatch.setattr(sys, "stdout", fake_stdout)
    assert X.main(["--period", "FY2025_Q2", "--only", code]) == 0
    assert fake_stdout is not None
    rows = json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))
    return rows, json.loads((tmp_path / "diag.json").read_text(encoding="utf-8"))


ANCHORS = [(1, "가. 지급여력금액", 579.1), (14, "나. 지급여력기준금액", 299.07), (27, "다. 지급여력비율", 193.63)]


def test_registered_non_applier_zero_post_block_is_mirrored_and_unit_scaled(tmp_path, monkeypatch):
    monkeypatch.setitem(X.NON_APPLIER_POST_MIRROR, ("KR9999", "2025.2Q"), "test evidence")
    rows, diag = _run_main(tmp_path, monkeypatch, "KR9999", "\n".join(HANNOVER_2025_2Q), ANCHORS)
    by = {(r["경과조치여부"], r["measure구분"]): r for r in rows}
    assert set(by) == {(ph, m) for ph in ("적용전", "적용후") for m in ("지급여력비율", "지급여력금액", "지급여력기준금액")}
    assert by[("적용전", "지급여력금액")]["base"] == 579.1 and by[("적용전", "지급여력기준금액")]["base"] == 299.07       # 백만원 -> 억원
    assert by[("적용전", "지급여력비율")]["base"] == 193.63
    for m in ("지급여력비율", "지급여력금액", "지급여력기준금액"):
        a, b = by[("적용전", m)], by[("적용후", m)]
        assert all(a[f] == b[f] for f in ("-100bp", "-50bp", "base", "+50bp", "+100bp", "듀레이션", "컨벡서티"))     # 후 = 전 그대로
    assert diag["KR9999|2025.2Q"] == "post_mirrored"


def test_unregistered_company_zero_post_block_is_a_hole_not_zero_rows(tmp_path, monkeypatch):
    rows, diag = _run_main(tmp_path, monkeypatch, "KR9998", "\n".join(HANNOVER_2025_2Q), ANCHORS)
    assert {r["경과조치여부"] for r in rows} == {"적용전"}          # 후 블록 0 은 행으로 싣지 않는다(종전엔 0 행 3개가 RS2 RED 가 됐다)
    assert diag["KR9998|2025.2Q"] == "post_dash"


def test_registered_company_with_a_real_post_block_keeps_the_document_values(tmp_path, monkeypatch):
    md = HANNOVER_2025_2Q[:5] + ["| 경    | 지급여력비율   | 190.00 | 170.00 | 180.00 | 200.00 | 205.00 |",
                                 "| 과 조  | 지급여력금액   | 57,000 | 57,000 | 57,000 | 57,000 | 57,000 |",
                                 "| 치 후  | 지급여력기준금액 | 29,907 | 32,624 | 31,215 | 28,689 | 27,543 |"]
    monkeypatch.setitem(X.NON_APPLIER_POST_MIRROR, ("KR9999", "2025.2Q"), "test evidence")
    rows, diag = _run_main(tmp_path, monkeypatch, "KR9999", "\n".join(md), ANCHORS)
    by = {(r["경과조치여부"], r["measure구분"]): r for r in rows}
    assert by[("적용후", "지급여력비율")]["base"] == 190.0 and by[("적용후", "지급여력금액")]["base"] == 570.0     # 문서 값(÷100)이 이긴다, 미러 아님
    assert diag["KR9999|2025.2Q"] != "post_mirrored"
