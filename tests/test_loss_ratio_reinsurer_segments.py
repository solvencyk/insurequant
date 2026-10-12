"""Loss-ratio domain: reinsurer segment standard (ticket 20261012T0900Z) + gz storage of the long source. Offline, a few seconds.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -m pytest tests/test_loss_ratio_reinsurer_segments.py -q
"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_loss_ratio_master as M  # noqa: E402
import extract_loss_ratio as X  # noqa: E402

LR = ROOT / "data" / "loss_ratio"
NEW = [f"KR110{i}" for i in range(1, 8)]
STD_SEGS = {"", "생명보험", "장기손해보험"}


def _master():
    return json.loads((LR / "master_loss_ratio.json").read_text(encoding="utf-8"))


def test_long_source_is_gz_only():
    assert (LR / "risk_premium_vs_expected_claims.json.gz").exists()
    assert not (LR / "risk_premium_vs_expected_claims.json").exists()
    rows = M.read_json(M.SRC_B)
    assert M.SRC_B.suffix == ".gz" and len(rows) > 160_000


def test_gz_writer_is_deterministic_and_lossless(tmp_path):
    rows = M.read_json(M.SRC_B)[:500]
    a, b = tmp_path / "a.json.gz", tmp_path / "b.json.gz"
    X.atomic_write_json(a, rows)
    X.atomic_write_json(b, rows)
    assert a.read_bytes() == b.read_bytes()
    assert json.loads(gzip.decompress(a.read_bytes()).decode("utf-8")) == rows
    assert M.read_json(a) == rows


def test_reinsurer_segments_are_standard():
    m = _master()
    re_rows = [r for r in m if r["원보험사코드"] in NEW]
    assert len(re_rows) == 1904
    assert {r["세그먼트"] for r in re_rows} <= STD_SEGS
    assert not [r for r in re_rows if r["상품구분"] in ("생명", "장기")]
    by = {}
    for r in re_rows:
        by.setdefault(r["원보험사코드"], set()).add(r["세그먼트"])
    assert by["KR1101"] == {"", "생명보험", "장기손해보험"} and by["KR1103"] == {"", "생명보험", "장기손해보험"}
    assert by["KR1102"] == {"생명보험", "장기손해보험"}
    assert by["KR1104"] == {"장기손해보험"} and by["KR1105"] == {"장기손해보험"}
    assert by["KR1106"] == {""}                                     # 채택 블록이 생명+장기손해 합산 한 덩어리 -> 분리 불가, 공란
    assert by["KR1107"] == {"", "생명보험", "장기손해보험"}
    # 원문 라벨은 그대로 보존
    assert any(r["원문포트폴리오"] == "생명사망" and r["세그먼트"] == "생명보험" and r["포트폴리오"] == "사망" and r["상품구분"] == "" for r in re_rows)
    assert any(r["원보험사코드"] == "KR1102" and r["세그먼트"] == "장기손해보험" for r in re_rows)


def test_existing_companies_untouched_segments():
    m = _master()
    kor = {r["세그먼트"] for r in m if r["원보험사코드"] == "KR1000"}
    assert kor == {"생명/공동재보험", "생명/전통형재보험", "장기손해/전통형재보험", "장기손해/공동재보험"}


def test_std_assign_rules():
    items = {("", "Non-Par", "생명", "사망"), ("", "Non-Par", "장기", "복합"), ("", "합계", "", "합계")}
    out = M.std_assign("KR1101", items)
    assert out[("", "Non-Par", "생명", "사망")] == ("생명보험", "")
    assert out[("", "Non-Par", "장기", "복합")] == ("장기손해보험", "")
    assert out[("", "합계", "", "합계")] == ("", "")                  # 혼합 합계 -> 공란
    one = M.std_assign("KR1105", {("", "Non-Par", "무배당", "사망"), ("", "합계", "", "합계")})
    assert one[("", "합계", "", "합계")] == ("장기손해보험", "")      # 단일 세그먼트 -> 합계도 같은 값
    sw = M.std_assign("KR1102", {("손해보험", "Non-Par", "무배당", "상해"), ("손해보험", "합계", "", "합계")})
    assert sw[("손해보험", "합계", "", "합계")] == ("장기손해보험", "")
    unk = M.std_assign("KR1107", {("", "Non-Par", "무배당", "미지"), ("", "합계", "", "합계")})
    assert unk[("", "합계", "", "합계")] == ("", "")                  # 규칙 밖 라벨 -> 항등(추정 안 함)
    assert M.std_assign("KR0001", {("", "Non-Par", "무배당", "사망")}) == {("", "Non-Par", "무배당", "사망"): ("", "무배당")}


def test_builder_verify_passes_on_committed_files():
    errs, warns, stats = M.run_verify_files()
    assert errs == []
    assert stats["rows"] == 38248
