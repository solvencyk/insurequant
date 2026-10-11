# -*- coding: utf-8 -*-
"""`latest_disclosure_pdfs` / `prefer_latest_edition` / `manifest_latest_name` -- 같은 (분기, 회사)에 판이 둘 이상일 때 "쓸 판"을 다운로더 매니페스트로 정하는 공통 헬퍼.

배경(2026-10-11): `disclosure_pdfs()` 는 모든 판을 이름순으로 돌려주므로 `pdfs[0]` 을 쓰는 도구가 옛 판을 골랐다(스위스리 2023.4Q: 옛 60쪽 `공시 예정` 판 대 새 85쪽 K-ICS 완성본
`_v20240510`). 반대로 뮌헨 2023.1Q·2Q 는 K-ICS 정정본이 주 파일이고 옛 원본이 `_v20230101` 로 병존해서, "최대 크기 · 마지막 이름" 규칙은 옛 원본을 골랐다.
이 테스트는 (a) 매니페스트 없는 회사의 종전 동작 불변 (b) `versions` 마지막 > `file` 규칙 (c) `latest` 우선 (d) `alternates` 무시 (e) 디스크에 없는 판 지정은 종전 목록으로 폴백
(f) MD 도 같은 stem 짝으로 고른다 를 고정한다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from _disclosure_pdf_paths import (  # noqa: E402
    disclosure_pdfs, latest_disclosure_pdfs, manifest_latest_name, prefer_latest_edition,
)

PERIOD = "FY2023_Q4"


def _mk(tmp_path: Path, names, manifest=None, code="KR1102"):
    raw = tmp_path / PERIOD / "raw"
    raw.mkdir(parents=True)
    for n in names:
        (raw / n).write_bytes(b"%PDF-" + n.encode("utf-8"))
    if manifest is not None:
        meta = tmp_path / "_meta"
        meta.mkdir()
        (meta / f"reinsurer_{code}_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")


OLD, NEW = "KR1102_스위스리아시아.pdf", "KR1102_스위스리아시아_v20240510.pdf"


def test_no_manifest_keeps_legacy_list(tmp_path):
    _mk(tmp_path, [OLD, NEW])
    assert [p.name for p in latest_disclosure_pdfs(PERIOD, "KR1102", root=tmp_path)] == [p.name for p in disclosure_pdfs(PERIOD, "KR1102", root=tmp_path)] == [OLD, NEW]
    assert manifest_latest_name(PERIOD, "KR1102", root=tmp_path) is None


def test_versions_last_wins_over_file(tmp_path):
    man = {"periods": [{"period": "2023.4Q", "file": f"data/disclosure/{PERIOD}/raw/{OLD}",
                        "versions": [{"file": f"data/disclosure/{PERIOD}/raw/{NEW}"}]}]}
    _mk(tmp_path, [OLD, NEW], man)
    assert manifest_latest_name(PERIOD, "KR1102", root=tmp_path) == NEW
    assert [p.name for p in latest_disclosure_pdfs(PERIOD, "KR1102", root=tmp_path)] == [NEW]


def test_primary_file_wins_when_only_alternates(tmp_path):
    """뮌헨 형: `file` = K-ICS 정정본, 옛 원본은 alternates 로만 적힌다 -> 주 파일."""
    base, orig = "KR1101_뮌헨재보험.pdf", "KR1101_뮌헨재보험_v20230101.pdf"
    man = {"periods": [{"period": "2023.4Q", "file": f"data/disclosure/{PERIOD}/raw/{base}", "alternates": [{"file": f"data/disclosure/{PERIOD}/raw/{orig}"}]}]}
    _mk(tmp_path, [base, orig], man, code="KR1101")
    assert [p.name for p in latest_disclosure_pdfs(PERIOD, "KR1101", root=tmp_path)] == [base]


def test_explicit_latest_key_beats_versions(tmp_path):
    third = "KR1102_스위스리아시아_v20240601.pdf"
    man = {"periods": [{"period": "2023.4Q", "file": OLD, "versions": [{"file": NEW}], "latest": {"file": third}}]}
    _mk(tmp_path, [OLD, NEW, third], man)
    assert [p.name for p in latest_disclosure_pdfs(PERIOD, "KR1102", root=tmp_path)] == [third]
    man["periods"][0]["latest"] = NEW   # plain string form
    (tmp_path / "_meta" / "reinsurer_KR1102_manifest.json").write_text(json.dumps(man, ensure_ascii=False), encoding="utf-8")
    assert [p.name for p in latest_disclosure_pdfs(PERIOD, "KR1102", root=tmp_path)] == [NEW]


def test_manifest_names_file_not_on_disk_falls_back_to_legacy_list(tmp_path):
    man = {"periods": [{"period": "2023.4Q", "file": OLD, "versions": [{"file": "KR1102_스위스리아시아_v99999999.pdf"}]}]}
    _mk(tmp_path, [OLD, NEW], man)
    assert [p.name for p in latest_disclosure_pdfs(PERIOD, "KR1102", root=tmp_path)] == [OLD, NEW]


def test_other_period_or_company_untouched(tmp_path):
    man = {"periods": [{"period": "2024.1Q", "file": NEW}]}      # a different quarter's entry must not decide this one
    _mk(tmp_path, [OLD, NEW], man)
    assert [p.name for p in latest_disclosure_pdfs(PERIOD, "KR1102", root=tmp_path)] == [OLD, NEW]
    assert latest_disclosure_pdfs(PERIOD, "KR9999", root=tmp_path) == []


def test_single_file_group_is_returned_as_is(tmp_path):
    _mk(tmp_path, [OLD], {"periods": [{"period": "2023.4Q", "file": NEW, "versions": [{"file": NEW}]}]})
    assert [p.name for p in latest_disclosure_pdfs(PERIOD, "KR1102", root=tmp_path)] == [OLD]


def test_prefer_latest_edition_pairs_md_by_stem(tmp_path):
    man = {"periods": [{"period": "2023.4Q", "file": OLD, "versions": [{"file": NEW}]}]}
    _mk(tmp_path, [OLD, NEW], man)
    mds = [tmp_path / "KR1102_스위스리아시아.md", tmp_path / "KR1102_스위스리아시아_v20240510.md"]
    assert [p.name for p in prefer_latest_edition(PERIOD, "KR1102", mds, root=tmp_path)] == ["KR1102_스위스리아시아_v20240510.md"]
    # no sibling MD of the latest edition -> candidates unchanged
    assert prefer_latest_edition(PERIOD, "KR1102", mds[:1] + [tmp_path / "KR1102_스위스리아시아_amended.md"], root=tmp_path) == mds[:1] + [tmp_path / "KR1102_스위스리아시아_amended.md"]


# K-ICS 레인에서 "한 판만 읽는" 도구 — 전부 `latest_disclosure_pdfs` 를 거쳐야 한다(`disclosure_pdfs()[0]` 은 옛 판일 수 있다). 우회하면 이 테스트가 깨진다.
K_ICS_SINGLE_PICK_SCRIPTS = [
    "build_kics_source_textlayer.py", "extract_market_section_pages.py", "fill_market_irr_from_pdf.py", "fill_market_subs_from_pdf.py",
    "market_subrisk_pdf_recover.py", "recover_market_subs_parallel.py", "append_kics_detail_from_pdf.py", "backfill_life_subrisk_from_pdf.py",
    "emit_rate_sensitivity_provenance.py", "extract_transition_applicability.py", "fill_post_transition_adjust_items.py",
    "rebuild_combined_transition_after.py", "fill_market_subitems_to_disclosure.py", "extract_kics_rate_sensitivity.py", "extract_kics_irr_balance.py",
]


def test_k_ics_single_pick_tools_resolve_through_the_latest_edition_helper():
    import re
    pat = re.compile(r"(?<![A-Za-z_])disclosure_pdfs\(")          # bare `disclosure_pdfs(` (latest_disclosure_pdfs( 는 앞이 `_` 라 걸리지 않는다)
    for name in K_ICS_SINGLE_PICK_SCRIPTS:
        src = (REPO / "scripts" / name).read_text(encoding="utf-8")
        assert not pat.search(src), f"{name}: bare disclosure_pdfs() call — use latest_disclosure_pdfs()/prefer_latest_edition() (판이 둘이면 매니페스트가 정한 최신 판)"
        assert "latest_disclosure_pdfs" in src or "prefer_latest_edition" in src, f"{name}: does not use the latest-edition helper"


def test_corrupt_manifest_is_ignored(tmp_path):
    _mk(tmp_path, [OLD, NEW])
    (tmp_path / "_meta").mkdir()
    (tmp_path / "_meta" / "reinsurer_KR1102_manifest.json").write_text("{not json", encoding="utf-8")
    assert [p.name for p in latest_disclosure_pdfs(PERIOD, "KR1102", root=tmp_path)] == [OLD, NEW]
