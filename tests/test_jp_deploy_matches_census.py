# -*- coding: utf-8 -*-
"""불변식 1번의 jp 레인판 — **배포 JSON = census 를 지금 재빌드한 결과**여야 한다.

왜 (UH-19, 2026-09-13)
----------------------
census 를 고치고 `jp/jesr_esr.json` 을 재생성하지 않은 채 커밋한 라운드가 실제로 있었다
(커밋 `62eed63`: 2사 `basis` 정정과 SOMPO 목표레인지 정정이 census 에만 들어가고 배포본은
옛 값 `unconfirmed` · `high_pct=270` 그대로였다). jp 레인의 게이트는 **빌더를 돌릴 때만** 도는데
빌더를 안 돌리면 게이트도 안 돌므로, 그 상태는 어떤 검사에도 안 걸렸다.

그래서 "빌더를 돌렸는가" 자체를 게이트가 검사한다. 이 테스트는 네트워크를 쓰지 않는다 —
빌더가 완전 오프라인이라 그대로 재실행해 바이트 비교만 한다(`generated_at` 만 제외).

이 테스트가 깨지면 고치는 법은 하나다: `python3 J-ESR/build_jesr_page_json.py` 를 돌리고
그 산출을 같이 커밋한다. 테스트의 기대값을 손으로 맞추지 말 것.

`docs/postmortems/PM-2026-09-13_jp_secondary_source_and_dead_url.md` §5 / UH-19.
"""
from __future__ import annotations

import ast
import csv
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
JESR = ROOT / "J-ESR"
DEPLOY = ROOT / "jp" / "jesr_esr.json"
MASTER = JESR / "jesr_master.json"

pytestmark = pytest.mark.skipif(
    not (JESR / "build_jesr_page_json.py").exists() or not DEPLOY.exists(),
    reason="jp 레인 파일이 없는 slim 트리(main 등)",
)


def _strip_volatile(payload: dict) -> dict:
    meta = dict(payload.get("_meta", {}))
    meta.pop("generated_at", None)
    return {**payload, "_meta": meta}


def _rebuild(tmp_path: Path) -> tuple[dict, dict]:
    sys.path.insert(0, str(JESR))
    import build_jesr_page_json as builder  # noqa: E402

    master_out = tmp_path / "jesr_master.json"
    deploy_out = tmp_path / "jesr_esr.json"
    orig = (builder.MASTER_OUT, builder.DEPLOY_OUT)
    builder.MASTER_OUT, builder.DEPLOY_OUT = master_out, deploy_out
    try:
        rc = builder.main()
    finally:
        builder.MASTER_OUT, builder.DEPLOY_OUT = orig
    assert rc == 0, "빌더 self-check 가 실패했다 — 출처 게이트(RED) 메시지를 stderr 에서 확인해라"
    return (
        json.loads(master_out.read_text(encoding="utf-8")),
        json.loads(deploy_out.read_text(encoding="utf-8")),
    )


def test_deploy_json_is_current_rebuild_of_census(tmp_path):
    """`jp/jesr_esr.json` 이 커밋된 census 를 재빌드한 결과와 같아야 한다."""
    _, fresh_deploy = _rebuild(tmp_path)
    committed = json.loads(DEPLOY.read_text(encoding="utf-8"))
    a, b = _strip_volatile(committed), _strip_volatile(fresh_deploy)
    if a != b:
        diffs = []
        for rec_a, rec_b in zip(a.get("records", []), b.get("records", [])):
            for key in set(rec_a) | set(rec_b):
                if rec_a.get(key) != rec_b.get(key):
                    diffs.append(f"{rec_a.get('company_jp')}.{key}: 배포본={rec_a.get(key)!r} 재빌드={rec_b.get(key)!r}")
        meta_keys = [k for k in set(a["_meta"]) | set(b["_meta"]) if a["_meta"].get(k) != b["_meta"].get(k)]
        pytest.fail(
            "jp/jesr_esr.json 이 census 재빌드 결과와 다르다 — census 를 고치고 빌더를 안 돌렸다.\n"
            "  python3 J-ESR/build_jesr_page_json.py  를 돌리고 산출을 같이 커밋해라.\n"
            + ("\n".join(f"  - {d}" for d in diffs[:15]) or "")
            + (f"\n  _meta 차이: {meta_keys}" if meta_keys else "")
        )


def test_master_json_is_current_rebuild_of_census(tmp_path):
    """`J-ESR/jesr_master.json`(누가 posted 인가의 정본)도 같은 조건이다."""
    fresh_master, _ = _rebuild(tmp_path)
    committed = json.loads(MASTER.read_text(encoding="utf-8"))
    assert _strip_volatile(committed) == _strip_volatile(fresh_master), (
        "J-ESR/jesr_master.json 이 census 재빌드 결과와 다르다 — "
        "python3 J-ESR/build_jesr_page_json.py 를 돌리고 같이 커밋해라"
    )


# ===========================================================================
# census 파생 항등식 — "posted 가 15사" 라는 **숫자**를 지키던 자리 (TODO_jp(27) ②)
#
# 종전 self-check 는 `len(records) != 15` 였다. 10월 말 J-ICS 공시기한 직후 census 의 posted
# 가 15사 -> 60~70사로 뒤집히면(2026-09-13 현재 not_yet 62사) 그 리터럴은 **정상 데이터를
# RED 로 막는다**. 실측 재현(2026-09-13): HEAD 의 빌더에 합성 census(posted 77)를 물리면
# `SELF-CHECK FAIL: records count = 77, expected 15` · exit 1.
#
# 2026-08-29 의 분기 지평 사고와 같은 형태다 — 게이트 세 곳이 각자 분기 목록을 리터럴로 들고
# 있다가 2026.2Q 를 순회조차 안 했고, 그래서 `tests/test_quarter_horizon.py` 가 생겼다.
# 거기 적힌 교훈: **하드코딩 자체가 재발 구조다.**
#
# 아래 테스트는 두 방향을 다 본다. 한쪽만 보면 고장난 룰이 통과한다:
#   · posted 가 15가 아닌 census 로도 **통과**하는가 (거짓 RED 가 사라졌는가)
#   · 항등식을 깨면 **실제로 RED 가 나는가** (검사가 없어진 게 아닌가)
# 합성 census 는 pytest tmp 에만 쓴다 — 저장소 파일은 읽기만 한다.
# ===========================================================================

_RULE_ID = re.compile(r"^\[([A-Z_]+)\]")


def _ids(errors: list[str]) -> list[str]:
    return sorted({m.group(1) for e in errors if (m := _RULE_ID.match(e))})


def _builder():
    sys.path.insert(0, str(JESR))
    import build_jesr_page_json as builder  # noqa: E402

    return builder


def _synthetic_census(tmp_path: Path, *, extra_posted: int) -> tuple[Path, int]:
    """실제 census 의 `not_yet` 행 `extra_posted` 개를 posted 로 뒤집은 합성 census.

    10/31 라운드의 실제 모양(같은 기간·같은 파일에 회사만 늘어난다)을 그대로 흉내 낸다.
    **이 fixture 에도 리터럴을 심지 않는다** — as_of·scope 어휘·esr_pct 범위·checked_at 은
    전부 빌더 상수와 실제 census 에서 가져온다. 여기에 날짜를 적어 두면 이 테스트가 다음
    기간에 스스로 썩는다(고치려는 병을 테스트가 앓는 꼴).
    """
    b = _builder()
    with (JESR / "fy2025_esr_census_20260912.csv").open(encoding="utf-8-sig", newline="") as fh:
        rdr = csv.DictReader(fh, restkey="_overflow")
        fields = rdr.fieldnames
        rows = list(rdr)

    posted = b.census_posted_rows(rows)
    urls = [(r.get("source_url") or "").strip() for r in posted]
    checked = max((r.get("checked_at") or "").strip()[:10] for r in rows)
    span = b.ESR_PCT_MAX - b.ESR_PCT_MIN - 20

    flipped = 0
    for i, r in enumerate(rows):
        if flipped >= extra_posted:
            break
        if b.census_status(r) != "not_yet":
            continue
        r["fy2025_esr_status"] = b.POSTED_STATUS
        r["esr_pct"] = f"{b.ESR_PCT_MIN + 10 + (i * 37) % span + (i % 10) / 10:.1f}"
        r["esr_scope"] = b.SCOPE_VALUES[i % len(b.SCOPE_VALUES)]
        r["as_of"] = b.AS_OF_TARGET
        r["source_url"] = urls[i % len(urls)]
        r["doc_type"] = "決算説明資料"
        r["checked_at"] = checked
        r["preliminary"] = b.PRELIM_FALSE[0]
        r["notes"] = "10/31 J-ICS flip simulation (synthetic)"
        flipped += 1
    assert flipped == extra_posted, f"not_yet 행이 모자라다: {flipped} < {extra_posted}"

    out = tmp_path / "synthetic_census.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return out, len(posted) + extra_posted


def _synthetic_esr_evidence(tmp_path: Path, census_path: Path) -> Path:
    """합성 census 에 맞는 `esr_in_source_health.json`.

    10/31 flip 시뮬레이션은 census 만 뒤집는 것이 아니라 **선행 단계 두 개를 다시 돌린
    라운드 전체**를 흉내 내야 한다. census 만 뒤집으면 '아무도 원문을 확인한 적 없는 posted
    행' 이라는, 실제로는 존재해서는 안 되는 상태가 되고 `JP_ESR_NOT_IN_SOURCE` 의 증거 커버리지
    룰(`JP_SOURCE_EVIDENCE_INCOMPLETE`)이 정당하게 RED 를 낸다 — 그건 거짓 RED 가 아니라
    게이트가 제 일을 한 것이다(2026-09-13 실측: 이 fixture 를 안 고치면 1·30·62 세 케이스가
    전부 그 이유로 실패한다). 그래서 게이트를 느슨하게 하지 않고 **fixture 를 완성한다**.

    URL 생존 증거(`source_url_health.json`)는 합성 행이 실제 census 의 `source_url` 을
    돌려쓰므로 실제 파일이 그대로 덮는다 — 그쪽은 손댈 필요가 없다.
    """
    b = _builder()
    with census_path.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh, restkey="_overflow"))
    ev_rows = []
    for r in b.census_posted_rows(rows):
        ev_rows.append({
            "origin": census_path.name, "company": r["company_jp"], "field": "source_url",
            "url": (r.get("source_url") or "").strip(),
            "esr_pct": b._norm_pct(r.get("esr_pct")),
            "verdict": "found", "match_rule": "text_window", "page": 1, "distance": 0,
            "label": "ESR", "pages": 1, "evidence": "(synthetic) ESR は ... %",
        })
    checked = max((r.get("checked_at") or "").strip()[:10] for r in rows)
    path = tmp_path / "esr_in_source_health.json"
    path.write_text(json.dumps(
        {"checked_at": f"{checked}T23:59Z", "scope": "all", "targets": len(ev_rows),
         "rows": ev_rows}, ensure_ascii=False), encoding="utf-8")
    return path


@pytest.mark.parametrize("extra_posted", [1, 30, 62])
def test_record_count_follows_census_not_a_literal(tmp_path, monkeypatch, extra_posted):
    """posted 가 15가 아닌 census 로도 빌더가 통과하고, 산출 회사 수가 census 를 따라간다.

    62 는 2026-09-13 현재 `not_yet` 전체 = 10/31 에 실제로 뒤집힐 최대치다(posted 77).
    """
    b = _builder()
    census_path, want_posted = _synthetic_census(tmp_path, extra_posted=extra_posted)
    assert want_posted != 15, "합성 census 가 옛 리터럴과 같으면 이 테스트는 아무것도 안 잰다"

    monkeypatch.setattr(b, "CENSUS_CSV", census_path)
    monkeypatch.setattr(b, "MASTER_OUT", tmp_path / "jesr_master.json")
    monkeypatch.setattr(b, "DEPLOY_OUT", tmp_path / "jesr_esr.json")
    # 선행 단계(check_esr_in_source.py)도 같이 돌린 라운드를 흉내 낸다 — 이유는 헬퍼 docstring.
    monkeypatch.setattr(b, "ESR_HEALTH_PATH", _synthetic_esr_evidence(tmp_path, census_path))
    rc = b.main()
    assert rc == 0, "정상 census 인데 빌더가 RED 다(거짓 RED — stderr 확인)"

    master = json.loads((tmp_path / "jesr_master.json").read_text(encoding="utf-8"))
    deploy = json.loads((tmp_path / "jesr_esr.json").read_text(encoding="utf-8"))
    assert len(master["records"]) == want_posted
    assert master["_meta"]["census"]["posted"] == want_posted
    assert len(deploy["records"]) + len(deploy["_meta"]["excluded_subsidiaries"]) == want_posted


def test_flipped_census_without_fresh_esr_evidence_is_red(tmp_path, monkeypatch):
    """**음성대조군.** 위 테스트가 fixture 로 게이트를 덮어 버린 게 아님을 보증한다.

    같은 합성 census 인데 `esr_in_source_health.json` 만 실제(=옛) 파일 그대로면, 뒤집은
    행들은 아무도 원문을 확인한 적이 없으므로 RED 여야 한다. 여기가 통과해 버리면
    `JP_ESR_NOT_IN_SOURCE` 는 census 를 늘리는 것만으로 우회된다.
    """
    b = _builder()
    census_path, _ = _synthetic_census(tmp_path, extra_posted=3)
    monkeypatch.setattr(b, "CENSUS_CSV", census_path)
    monkeypatch.setattr(b, "MASTER_OUT", tmp_path / "m.json")
    monkeypatch.setattr(b, "DEPLOY_OUT", tmp_path / "d.json")
    assert b.main() == 1, "증거 없이 posted 를 늘렸는데 빌더가 통과했다"


def test_builder_has_no_literal_record_count():
    """빌더 안에 `len(...) == <숫자>` 꼴 회사 수 리터럴을 **다시 심지 못하게** 한다.

    `test_quarter_horizon.py` 가 게이트의 리터럴 분기 지평에 대해 하는 일과 같다.
    (`== 0` 은 예외다 — '0 으로 닫히는 등식' 을 막는 검사가 그 형태라 오히려 있어야 한다.)
    """
    tree = ast.parse((JESR / "build_jesr_page_json.py").read_text(encoding="utf-8"))
    bad = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        sides = [node.left] + list(node.comparators)
        has_len = any(isinstance(s, ast.Call) and isinstance(s.func, ast.Name)
                      and s.func.id == "len" for s in sides)
        nums = [s.value for s in sides
                if isinstance(s, ast.Constant) and isinstance(s.value, int)
                and not isinstance(s.value, bool)]
        if has_len and any(n >= 2 for n in nums):
            bad.append(f"line {node.lineno}: len(...) 을 상수 {nums} 와 비교한다")
    assert not bad, (
        "회사 수 기대값을 다시 리터럴로 심었다 — census 에서 파생시켜라:\n  " + "\n  ".join(bad))


# ---------------------------------------------------------------------------
# 이빨: 항등식을 깨면 RED 가 나는가 (변이는 전부 메모리 안에서만)
# ---------------------------------------------------------------------------
def _census_rows(n: int, status: str = "posted") -> list[dict]:
    return [{"company_jp": f"社{i}", "company_en": f"Co{i}", "fy2025_esr_status": status,
             "preliminary": "", "checked_at": "2026-09-13"} for i in range(n)]


def _out_for(rows: list[dict], records=None) -> dict:
    b = _builder()
    recs = [{"company_jp": r["company_jp"]} for r in b.census_posted_rows(rows)] \
        if records is None else records
    return {"_meta": {"census": b.census_counts(rows)}, "records": recs}


def test_identity_passes_on_consistent_input():
    """음성대조군 — 뒤의 RED 가 '무조건 발화' 가 아님을 보증한다."""
    rows = _census_rows(4)
    assert _builder().check_census_identity(_out_for(rows), rows) == []


def test_missing_record_is_red_even_when_the_count_is_right():
    """한 건 빠지고 한 건 중복되면 **수는 맞는다** — 그래서 집합으로 건다."""
    b = _builder()
    rows = _census_rows(4)
    recs = [{"company_jp": "社0"}, {"company_jp": "社0"}, {"company_jp": "社2"}, {"company_jp": "社3"}]
    errors = b.check_census_identity(_out_for(rows, recs), rows)
    assert "JP_CENSUS_RECORDS" in _ids(errors)
    assert any("社1" in e for e in errors), errors


def test_empty_census_is_red_not_a_closed_equation():
    """posted 0건이면 산수는 전부 맞고 화면만 빈다 — 0 으로 닫히는 등식은 등식이 아니다."""
    b = _builder()
    rows = _census_rows(4, status="not_yet")
    errors = b.check_census_identity(_out_for(rows), rows)
    assert "JP_CENSUS_EMPTY" in _ids(errors)


def test_unknown_status_is_red():
    b = _builder()
    rows = _census_rows(3) + [{"company_jp": "社X", "company_en": "CoX",
                               "fy2025_esr_status": "posted?", "preliminary": ""}]
    errors = b.check_census_identity(_out_for(rows), rows)
    assert "JP_CENSUS_STATUS" in _ids(errors)


def test_hand_edited_census_meta_is_red():
    """`_meta.census` 만 손으로 고치면 잡히는가(파일 재계수와 대조)."""
    b = _builder()
    rows = _census_rows(4)
    out = _out_for(rows)
    out["_meta"]["census"]["posted"] = 15
    assert "JP_CENSUS_COUNT" in _ids(b.check_census_identity(out, rows))


def test_ragged_posted_row_is_red():
    """따옴표 없는 쉼표로 열이 넘친 posted 행 — 마지막 열이 잘린 채 실린다."""
    b = _builder()
    rows = _census_rows(2)
    rows[1][None] = [" 잘려서 흘러넘친 조각"]
    assert "JP_CENSUS_SHAPE" in _ids(b.check_census_identity(_out_for(rows), rows))


def test_unknown_preliminary_value_is_red():
    """`preliminary=Y` 는 조용히 키워드 폴백으로 떨어진다 — 결측이 아니라 오독이다."""
    b = _builder()
    rows = _census_rows(2)
    rows[0]["preliminary"] = "Y"
    assert "JP_CENSUS_PRELIM" in _ids(b.check_census_identity(_out_for(rows), rows))
    rows[0]["preliminary"] = b.PRELIM_TRUE[0].upper()   # 대소문자는 정상
    assert "JP_CENSUS_PRELIM" not in _ids(b.check_census_identity(_out_for(rows), rows))


def test_dropping_excluded_breaks_the_deploy_identity():
    """배포 항등식의 이빨: excluded 를 누락하면 RED 가 나는가.

    `census posted == master == deploy + excluded` 에서 excluded 를 빼면 좌우가 안 맞는다.
    dedup 이 꺼져 있는 지금(SUBSIDIARY_DEDUP=False)은 excluded 가 늘 0건이라 **이 경로는
    실데이터로는 한 번도 안 밟힌다** — 그래서 여기서 직접 잰다.
    """
    b = _builder()
    rows = _census_rows(3)
    master = [{"company_en": f"Co{i}"} for i in range(3)]
    deploy = [{"company_en": "Co0"}, {"company_en": "Co1"}]
    excluded = [{"company_en": "Co2", "parent": "Co0"}]
    assert b.check_deploy_identity(master, deploy, excluded, rows) == []

    errors = b.check_deploy_identity(master, deploy, [], rows)
    assert "JP_DEPLOY_COUNT" in _ids(errors)
    assert "JP_DEPLOY_SET" in _ids(errors), "조용히 사라진 회사를 집합 검사가 잡아야 한다"


def test_company_silently_swapped_between_master_and_deploy_is_red():
    """수는 맞는데 배포에 마스터에 없는 회사가 있는 경우."""
    b = _builder()
    rows = _census_rows(2)
    master = [{"company_en": "Co0"}, {"company_en": "Co1"}]
    deploy = [{"company_en": "Co0"}, {"company_en": "CoX"}]
    errors = b.check_deploy_identity(master, deploy, [], rows)
    assert "JP_DEPLOY_SET" in _ids(errors)
    assert any("CoX" in e for e in errors)


# ---------------------------------------------------------------------------
# 어휘 조기경보 — 10/31 에 posted 로 뒤집힐 행의 어휘를 **지금** 본다
# ---------------------------------------------------------------------------
def test_sector_map_covers_every_sector_in_the_census():
    """census 전 행(posted 아닌 행 포함)의 sector 를 SECTOR_MAP 이 아는가.

    빌더는 posted 행만 보므로, 모르는 업권이 `not_yet` 행에 들어와 있으면 뒤집히는 날에야
    `bad sector: ... = None` 로 터진다. 그 하루 전에 알자는 것이 이 테스트다.
    """
    b = _builder()
    with (JESR / "fy2025_esr_census_20260912.csv").open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh, restkey="_overflow"))
    unknown = sorted({(r.get("sector") or "").strip() for r in rows} - set(b.SECTOR_MAP) - {""})
    assert not unknown, f"SECTOR_MAP 이 모르는 업권이 census 에 있다: {unknown}"


def test_census_scope_and_status_vocabulary_is_known():
    b = _builder()
    with (JESR / "fy2025_esr_census_20260912.csv").open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh, restkey="_overflow"))
    bad_scope = sorted({(r.get("esr_scope") or "").strip() for r in rows}
                       - set(b.SCOPE_VALUES) - {""})
    bad_status = sorted({b.census_status(r) for r in rows} - set(b.CENSUS_STATUSES))
    assert not bad_scope, f"모르는 esr_scope: {bad_scope}"
    assert not bad_status, f"모르는 fy2025_esr_status: {bad_status}"


# ---------------------------------------------------------------------------
# "배선했다" 가 아니라 **실제로 exit code 를 바꾼다**
#
# 위의 이빨 테스트는 검사 함수를 직접 부른다 — 그래서 누가 self_check 에서 호출 한 줄을
# 지워도 전부 통과한다(이 저장소가 UH-18 에서 정확히 그 구분에 데였다). 아래는 진짜 빌더를
# 돌려 exit code 를 잰다. census 파일로 만들 수 있는 위반만 여기 올 수 있다.
# ---------------------------------------------------------------------------
def _real_census() -> tuple[list[dict], list[str]]:
    with (JESR / "fy2025_esr_census_20260912.csv").open(encoding="utf-8-sig", newline="") as fh:
        rdr = csv.DictReader(fh, restkey="_overflow")
        return list(rdr), list(rdr.fieldnames)


def _write_census(tmp_path: Path, rows: list[dict], fields: list[str]) -> Path:
    out = tmp_path / "census.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return out


def _run_main(tmp_path, monkeypatch, census_path: Path) -> int:
    b = _builder()
    monkeypatch.setattr(b, "CENSUS_CSV", census_path)
    monkeypatch.setattr(b, "MASTER_OUT", tmp_path / "m.json")
    monkeypatch.setattr(b, "DEPLOY_OUT", tmp_path / "d.json")
    return b.main()


def test_unmutated_census_copy_builds_green(tmp_path, monkeypatch):
    """음성대조군 — 아래 exit 1 이 사본 탓이 아님을 보증한다."""
    rows, fields = _real_census()
    assert _run_main(tmp_path, monkeypatch, _write_census(tmp_path, rows, fields)) == 0


def test_empty_posted_census_changes_exit_code(tmp_path, monkeypatch, capsys):
    """posted 0 건이면 등식은 전부 닫히고 화면만 빈다 — 그래도 exit 1 이어야 한다."""
    b = _builder()
    rows, fields = _real_census()
    for r in rows:
        if b.census_status(r) == b.POSTED_STATUS:
            r["fy2025_esr_status"] = "not_yet"
    rc = _run_main(tmp_path, monkeypatch, _write_census(tmp_path, rows, fields))
    assert rc == 1, "빈 census 로 초록이 나왔다 — 0 == 0 으로 닫히는 등식"
    assert "JP_CENSUS_EMPTY" in capsys.readouterr().err


def test_unknown_preliminary_changes_exit_code(tmp_path, monkeypatch, capsys):
    b = _builder()
    rows, fields = _real_census()
    b.census_posted_rows(rows)[0]["preliminary"] = "Y"
    rc = _run_main(tmp_path, monkeypatch, _write_census(tmp_path, rows, fields))
    assert rc == 1
    assert "JP_CENSUS_PRELIM" in capsys.readouterr().err


def test_duplicate_company_en_changes_exit_code(tmp_path, monkeypatch, capsys):
    """2026-09-13 `6e051be` 의 실사고(다른 회사 영문명)를 재생한다 — 그땐 게이트가 침묵했다."""
    b = _builder()
    rows, fields = _real_census()
    posted = b.census_posted_rows(rows)
    posted[1]["company_en"] = posted[0]["company_en"]
    rc = _run_main(tmp_path, monkeypatch, _write_census(tmp_path, rows, fields))
    assert rc == 1
    assert "duplicate company_en" in capsys.readouterr().err


def test_ragged_posted_row_changes_exit_code(tmp_path, monkeypatch, capsys):
    """따옴표 없는 쉼표로 열이 넘친 posted 행 — CSV 를 **날것으로** 훼손해서 잰다."""
    b = _builder()
    rows, fields = _real_census()
    victim = b.census_posted_rows(rows)[0]["company_jp"]
    path = _write_census(tmp_path, rows, fields)
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    hit = 0
    for i, line in enumerate(lines):
        if line.startswith(victim + ","):
            lines[i] = line + ",넘쳐흐른 조각"
            hit += 1
    assert hit == 1, f"대상 행을 못 찾았다: {victim}"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")

    rc = _run_main(tmp_path, monkeypatch, path)
    assert rc == 1, "열이 넘친 posted 행인데 초록이다 — 마지막 열이 잘린 채 실린다"
    assert "JP_CENSUS_SHAPE" in capsys.readouterr().err


def test_identity_checks_are_wired_into_self_check_and_main():
    """호출 한 줄이 지워지면 위 exit-code 테스트가 잡지 못하는 축이 있다(배포 항등식).

    dedup 이 꺼져 있어 `excluded` 는 늘 0건이고, 그래서 `check_deploy_identity` 가 main()
    에서 빠져도 **어떤 데이터로도 재현되지 않는다**. 데이터가 닿지 못하는 배선은 정적으로
    못 박는다(`tests/test_push_gate_wiring.py` 와 같은 이유).
    """
    tree = ast.parse((JESR / "build_jesr_page_json.py").read_text(encoding="utf-8"))
    calls = {}
    for fn in tree.body:
        if isinstance(fn, ast.FunctionDef):
            calls[fn.name] = {n.func.id for n in ast.walk(fn)
                              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert "check_census_identity" in calls.get("self_check", set()), \
        "self_check 이 census 항등식을 안 부른다 — 룰은 있는데 아무도 안 돌린다"
    assert "source_gate_check" in calls.get("self_check", set()), \
        "self_check 이 출처 게이트를 안 부른다(UH-18 배선)"
    assert {"self_check", "check_deploy_identity"} <= calls.get("main", set()), \
        "main() 이 self_check/check_deploy_identity 를 안 부른다 — exit code 가 안 바뀐다"


def test_missing_esr_pct_is_a_named_red_not_a_traceback(tmp_path, monkeypatch, capsys):
    """posted 로 뒤집혔는데 값을 안 채운 행 — 10/31 에 가장 흔할 실수다.

    막히는 것 자체는 예전에도 같았다(정렬이 TypeError 로 죽었다). 다른 것은 **무엇이 찍히냐**
    다: 트레이스백이 아니라 회사 이름이 붙은 RED 여야 사람이 그 행을 고칠 수 있다.
    """
    b = _builder()
    rows, fields = _real_census()
    victim = b.census_posted_rows(rows)[0]
    victim["esr_pct"] = ""
    rc = _run_main(tmp_path, monkeypatch, _write_census(tmp_path, rows, fields))
    assert rc == 1
    err = capsys.readouterr().err
    assert "esr_pct" in err and victim["company_jp"] in err, err


def test_as_of_label_is_derived_from_as_of_target():
    """라벨을 손으로 또 적으면(같은 사실 두 벌) 기간을 바꿀 때 한쪽만 고쳐진다."""
    b = _builder()
    assert b.AS_OF_LABEL_JA == b._as_of_label_ja(b.AS_OF_TARGET)
    assert b._as_of_label_ja("2026-03-31") == "2026年3月31日"
    assert b._as_of_label_ja("2026-09-30") == "2026年9月30日"
