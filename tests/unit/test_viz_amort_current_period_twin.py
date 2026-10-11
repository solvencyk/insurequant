# -*- coding: utf-8 -*-
"""Unit test for viz_build_ifrs17_panels._current_period_twin / _pick_amort_block (inbox/parser/20261011T1900Z).

An annual filing prints the CSM amortisation schedule twice -- 당기말 table first, 전기말 table second -- with identical caption, header and
row labels (the extractor hands both the caption of the last descriptive paragraph).  Every score ties and the old last-resort tiebreak
`line_no` picked the LATER table, i.e. the prior-year schedule.  The fix moves the chosen table to its first-printed twin and must change
nothing else.  Pure functions on synthetic blocks: no file I/O, no raw XML.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import viz_build_ifrs17_panels as V  # noqa: E402

HDR = [["구분", "포트폴리오", "1년", "2년", "3년", "합계"]]


def blk(line_no, rows=None, src="a_00760.xml", caption="(10) 기대상각기간별 보험계약마진 금액은 다음과 같습니다.<당기말>", header=None, score=6):
    rows = rows if rows is not None else [["Non-Par", "무배당질병", "10", "9", "8", "27"], ["Non-Par", "무배당상해", "5", "4", "3", "12"], ["합계", "", "15", "13", "11", "39"]]
    return {"caption": caption, "header": header if header is not None else HDR, "rows": rows, "line_no": line_no, "score": score, "_source_xml": src}


def test_prior_year_table_is_replaced_by_its_first_printed_twin():
    cur, prior = blk(100), blk(200)
    assert V._pick_amort_block([prior, cur]) is cur          # list order must not matter
    assert V._pick_amort_block([cur, prior]) is cur


def test_already_first_or_single_table_is_returned_unchanged():
    cur = blk(100)
    assert V._pick_amort_block([cur]) is cur
    reins_family = blk(50, rows=[["합계", "", "1", "1", "1", "3"]], caption="(5) 출재보험 기대상각기간별 보험계약마진은 다음과 같습니다.")
    assert V._pick_amort_block([cur, reins_family]) is cur


def test_scoring_still_chooses_the_table_family_before_the_twin_swap():
    # a 재보험 table (caption score < 0) printed EARLIER than the 원수 pair must not win just because it is first
    reins = blk(10, caption="(5) 보유하고 있는 재보험계약의 보험계약마진은 다음과 같습니다.", rows=[["재보험계약", "", "1", "1", "1", "3"]])
    cur, prior = blk(100), blk(200)
    assert V._pick_amort_block([reins, prior, cur]) is cur


def test_twin_needs_same_source_file_caption_and_header():
    cur_sep, prior_sep = blk(100, src="a_00760.xml"), blk(200, src="a_00760.xml")
    cur_con, prior_con = blk(10, src="a_00761.xml"), blk(20, src="a_00761.xml")     # 연결 copy printed earlier in its OWN file
    # 별도/연결 are different files: the 연결 copy's smaller line_no is not "earlier" than the 별도 pair
    assert V._current_period_twin(prior_sep, [cur_sep, prior_sep, cur_con, prior_con]) is cur_sep
    other_header = blk(50, header=[["구분", "포트폴리오", "4년", "5년", "6년", "합계"]])
    assert V._current_period_twin(prior_sep, [other_header, cur_sep, prior_sep]) is cur_sep
    other_caption = blk(50, caption="(6) 다른 표는 다음과 같습니다.")
    assert V._current_period_twin(prior_sep, [other_caption, prior_sep]) is prior_sep


def test_period_tags_in_caption_or_header_do_not_split_a_pair():
    cur = blk(100, caption="(9) 보험계약마진 인식 예상은 다음과 같습니다.<당기말>", header=[["구 분", "제 39(당)기"], ["1년", "2년"]])
    prior = blk(200, caption="(9) 보험계약마진 인식 예상은 다음과 같습니다.<전기말>", header=[["구 분", "제 38(전)기"], ["1년", "2년"]])
    assert V._current_period_twin(prior, [prior, cur]) is cur


def test_row_labels_guard_keeps_different_sub_tables_apart():
    a = blk(100, rows=[[f"포트폴리오{i}", "1", "1", "1", "1", "4"] for i in range(10)])
    other = blk(50, rows=[[f"다른표{i}", "1", "1", "1", "1", "4"] for i in range(10)])   # same caption/header, disjoint labels (Jaccard 0)
    assert V._current_period_twin(a, [other, a]) is a


def test_one_changed_row_still_counts_as_a_twin():
    labels = [f"포트폴리오{i}" for i in range(10)]
    cur = blk(100, rows=[[x, "1", "1", "1", "1", "4"] for x in labels])                    # 10 labels
    prior = blk(200, rows=[[x, "1", "1", "1", "1", "4"] for x in labels[:-1]])             # 9 labels: Jaccard 0.9
    assert V._current_period_twin(prior, [cur, prior]) is cur


def test_unknown_or_tied_line_numbers_never_swap():
    # lxml `sourceline` saturates at 65535 in big files: equal numbers = unknown order = keep the scored pick
    a, b = blk(65535), blk(65535)
    assert V._current_period_twin(b, [a, b]) is b
    zero = blk(0)
    chosen = blk(300)
    assert V._current_period_twin(chosen, [zero, chosen]) is chosen                          # line_no 0 = unknown, ignored
    assert V._current_period_twin(zero, [zero, chosen]) is zero


def test_unlabelled_single_row_tables_pair_by_shape():
    # Lina FY2023: one numeric row without any label cell
    cur = blk(100, rows=[["661,957,884", "1,053,414,874", "804,061,286", "1,302,128,929", "1,693,985,343", "5,515,548,316"]])
    prior = blk(200, rows=[["451,375,405", "678,310,477", "425,243,184", "407,659,009", "245,659,242", "2,208,247,317"]])
    assert V._current_period_twin(prior, [cur, prior]) is cur
