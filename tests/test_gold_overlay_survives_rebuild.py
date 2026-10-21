#!/usr/bin/env python3
"""Regression test for the gold-overlay unification (owner 20260620T0859Z,
inbox/_resolved/20260620T0859Z__owner__MULTI__gold_overlay_durable_ownerfix.md).

Guards the property the ticket asked for: a rebuild of PL_breakdown.json /
CSM_waterfall.json can NEVER clobber an owner correction recorded in
data/_gold/user_pl_cells.json / user_csm_cells.json, because build_root_masters
applies that gold overlay unconditionally as the last step before 당분기
recompute -- every time build_pl()/build_csm() runs, no matter what the
upstream extraction (SRC) currently says.

Runs entirely against tmp_path -- never touches the real repo's root masters
or gold files. build_root_masters.py's module-level path constants are
monkeypatched for the duration of each test.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import build_root_masters as brm  # noqa: E402


def _write(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def test_pl_gold_survives_rebuild(tmp_path, monkeypatch):
    src = tmp_path / "pl_breakdown_master.json"
    out = tmp_path / "PL_breakdown.json"
    ovr = tmp_path / "user_pl_cells.json"

    # Fresh extraction says 43 (a known-wrong mis-extract) for this cell.
    _write(src, [{"원보험사코드": "KR1000", "원수사명": "코리안리재보험", "티커": "003690",
                  "생손보여부": "손해보험", "항목번호": 11,
                  "항목명": "기타생명장기재보험손익", "공시분기": "2026.1Q", "값": 43}])
    # Owner's durable correction: the real value is -11817.
    _write(ovr, {"set": [{"원보험사코드": "KR1000", "항목번호": 11,
                           "공시분기": "2026.1Q", "값": -11817}]})

    monkeypatch.setattr(brm, "PL_SRC", src)
    monkeypatch.setattr(brm, "PL_OUT", out)
    monkeypatch.setattr(brm, "PL_OVR", ovr)

    brm.build_pl()
    rows = json.loads(out.read_text(encoding="utf-8"))
    assert rows[0]["값"] == -11817, "gold overlay did not win over fresh extraction"

    # Rebuild again with the SAME (still-wrong) SRC, as if extraction hasn't been
    # fixed upstream yet -- this is the exact failure mode from 2026-08-14/15
    # (build_root_masters silently reverting to the fresh/upstream value).
    brm.build_pl()
    rows2 = json.loads(out.read_text(encoding="utf-8"))
    assert rows2[0]["값"] == -11817, "gold overlay did not survive a second rebuild"


def test_csm_gold_survives_rebuild(tmp_path, monkeypatch):
    src = tmp_path / "csm_waterfall_master_diag.json"
    out = tmp_path / "CSM_waterfall.json"
    ovr = tmp_path / "user_csm_cells.json"

    _write(src, [{"원보험사코드": "KR0069", "원수사명": "삼성생명보험", "티커": "032830",
                  "생손보여부": "생명보험", "항목번호": 1,
                  "항목명": "기초 CSM", "공시분기": "2025.4Q", "값": 999999}])
    _write(ovr, {"set": [{"원보험사코드": "KR0069", "항목번호": 1,
                           "공시분기": "2025.4Q", "값": 260000}]})

    monkeypatch.setattr(brm, "CSM_SRC", src)
    monkeypatch.setattr(brm, "CSM_OUT", out)
    monkeypatch.setattr(brm, "CSM_OVR", ovr)

    brm.build_csm()
    rows = json.loads(out.read_text(encoding="utf-8"))
    assert rows[0]["값"] == 260000, "gold overlay did not win over fresh extraction"

    brm.build_csm()
    rows2 = json.loads(out.read_text(encoding="utf-8"))
    assert rows2[0]["값"] == 260000, "gold overlay did not survive a second rebuild"


def test_pl_gold_path_is_data_gold_convention():
    """Guards the file *location*, not just the mechanism: owner asked for the
    data/_gold/ convention (matching K-ICS's user_kics_cells.json) specifically
    so corrections live in one discoverable place, not scattered under
    data/dart/viz/ where this used to be (pl_manual_overrides.json)."""
    assert brm.PL_OVR == REPO / "data" / "_gold" / "user_pl_cells.json"
    assert brm.CSM_OVR == REPO / "data" / "_gold" / "user_csm_cells.json"


def test_pl_null_dangi_blanks_only_the_listed_single_quarter(tmp_path, monkeypatch):
    """gold `null_dangi.cells` forces 값_당분기 -> None for exactly the listed (code, quarter, item) cells; the cumulative 값 stays, the neighbours
    (same item other quarter, other item same quarter) keep their derived single quarter, and the blank survives a second rebuild."""
    src = tmp_path / "pl_breakdown_master.json"
    out = tmp_path / "PL_breakdown.json"
    ovr = tmp_path / "user_pl_cells.json"

    def row(item, q, v):
        return {"원보험사코드": "KR9999", "원수사명": "테스트생명", "티커": None, "생손보여부": "생명보험", "항목번호": item,
                "항목명": f"항목{item}", "공시분기": q, "값": v}

    _write(src, [row(1, "2023.1Q", 100), row(1, "2023.2Q", 250), row(1, "2023.3Q", 600),
                 row(20, "2023.1Q", 10), row(20, "2023.2Q", 30), row(20, "2023.3Q", 70)])
    _write(ovr, {"set": [], "null_dangi": {"cells": [["KR9999", "2023.3Q", 1]]}})
    monkeypatch.setattr(brm, "PL_SRC", src)
    monkeypatch.setattr(brm, "PL_OUT", out)
    monkeypatch.setattr(brm, "PL_OVR", ovr)

    def check():
        rows = {(r["항목번호"], r["공시분기"]): r for r in json.loads(out.read_text(encoding="utf-8"))}
        assert rows[(1, "2023.3Q")]["값"] == 600, "the cumulative 값 must stay"
        assert rows[(1, "2023.3Q")]["값_당분기"] is None, "listed cell must be blank"
        assert rows[(1, "2023.2Q")]["값_당분기"] == 150, "same item, other quarter must keep its derived value"
        assert rows[(20, "2023.3Q")]["값_당분기"] == 40, "other item, same quarter must keep its derived value"
        assert rows[(1, "2023.1Q")]["값_당분기"] == 100

    brm.build_pl()
    check()
    brm.build_pl()          # second rebuild: the committed master is read back by _additive_merge; the blank must hold
    check()


def test_pl_without_null_dangi_key_is_unchanged(tmp_path, monkeypatch):
    """no `null_dangi` key (every gold file before 2026-10-22) -> old behaviour: every derivable single quarter is filled."""
    src = tmp_path / "pl_breakdown_master.json"
    out = tmp_path / "PL_breakdown.json"
    ovr = tmp_path / "user_pl_cells.json"
    _write(src, [{"원보험사코드": "KR9999", "원수사명": "테스트생명", "티커": None, "생손보여부": "생명보험", "항목번호": 1,
                  "항목명": "항목1", "공시분기": q, "값": v} for q, v in (("2023.1Q", 100), ("2023.2Q", 250), ("2023.3Q", 600))])
    _write(ovr, {"set": []})
    monkeypatch.setattr(brm, "PL_SRC", src)
    monkeypatch.setattr(brm, "PL_OUT", out)
    monkeypatch.setattr(brm, "PL_OVR", ovr)
    brm.build_pl()
    got = {r["공시분기"]: r["값_당분기"] for r in json.loads(out.read_text(encoding="utf-8"))}
    assert got == {"2023.1Q": 100, "2023.2Q": 150, "2023.3Q": 350}


def test_pl_set_dangi_uses_the_printed_single_quarter(tmp_path, monkeypatch):
    """gold `set_dangi.cells` forces 값_당분기 to the printed value for exactly the listed cell (값 stays; neighbours keep their derived single quarter; a cell listed in null_dangi stays
    blank; the result survives a second rebuild)."""
    src = tmp_path / "pl_breakdown_master.json"
    out = tmp_path / "PL_breakdown.json"
    ovr = tmp_path / "user_pl_cells.json"

    def row(item, q, v):
        return {"원보험사코드": "KR9999", "원수사명": "테스트생명", "티커": None, "생손보여부": "생명보험", "항목번호": item,
                "항목명": f"항목{item}", "공시분기": q, "값": v}

    _write(src, [row(1, "2023.1Q", 100), row(1, "2023.2Q", 250), row(1, "2023.3Q", 600),
                 row(20, "2023.1Q", 10), row(20, "2023.2Q", 30), row(20, "2023.3Q", 70),
                 row(21, "2023.1Q", 1), row(21, "2023.2Q", 2), row(21, "2023.3Q", 3)])
    _write(ovr, {"set": [], "set_dangi": {"cells": [["KR9999", "2023.3Q", 1, 123.5, "test"]]}, "null_dangi": {"cells": [["KR9999", "2023.3Q", 21]]}})
    monkeypatch.setattr(brm, "PL_SRC", src)
    monkeypatch.setattr(brm, "PL_OUT", out)
    monkeypatch.setattr(brm, "PL_OVR", ovr)

    def check():
        rows = {(r["항목번호"], r["공시분기"]): r for r in json.loads(out.read_text(encoding="utf-8"))}
        assert rows[(1, "2023.3Q")]["값"] == 600, "the cumulative 값 must stay"
        assert rows[(1, "2023.3Q")]["값_당분기"] == 123.5, "listed cell must carry the printed value"
        assert rows[(1, "2023.2Q")]["값_당분기"] == 150, "same item, other quarter must keep its derived value"
        assert rows[(20, "2023.3Q")]["값_당분기"] == 40, "other item, same quarter must keep its derived value"
        assert rows[(21, "2023.3Q")]["값_당분기"] is None, "a null_dangi cell must stay blank"
        assert rows[(21, "2023.3Q")]["값"] == 3

    brm.build_pl()
    check()
    brm.build_pl()
    check()


def test_pl_null_dangi_and_set_dangi_overlap_is_refused(tmp_path, monkeypatch):
    """the same cell in null_dangi and set_dangi is a contradiction -> the build refuses instead of picking one silently."""
    import pytest

    src = tmp_path / "pl_breakdown_master.json"
    out = tmp_path / "PL_breakdown.json"
    ovr = tmp_path / "user_pl_cells.json"
    _write(src, [{"원보험사코드": "KR9999", "원수사명": "테스트생명", "티커": None, "생손보여부": "생명보험", "항목번호": 1,
                  "항목명": "항목1", "공시분기": q, "값": v} for q, v in (("2023.1Q", 100), ("2023.2Q", 250), ("2023.3Q", 600))])
    _write(ovr, {"set": [], "set_dangi": {"cells": [["KR9999", "2023.3Q", 1, 123.5, "test"]]}, "null_dangi": {"cells": [["KR9999", "2023.3Q", 1]]}})
    monkeypatch.setattr(brm, "PL_SRC", src)
    monkeypatch.setattr(brm, "PL_OUT", out)
    monkeypatch.setattr(brm, "PL_OVR", ovr)
    with pytest.raises(ValueError):
        brm.build_pl()
