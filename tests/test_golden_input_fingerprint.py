# -*- coding: utf-8 -*-
"""골든 입력지문(`scripts/validate_golden_input_fingerprints.py`)의 매니페스트 + 변이시험.

**왜 있나.** 지문 게이트 자체가 조용히 좁아지는 것이 이 저장소의 반복 사고형태다. 명세에서
입력 패턴 하나를 빼거나, 새 골든을 등재 안 하거나, 축 하나를 비교에서 빠뜨리면 게이트는
여전히 `RED=0` 을 찍는다 — 그게 false-green 이다. 그래서 세 가지를 기계로 못 박는다:

  ① **등재 강제** — 빌더를 재실행하는 `tests/test_*_golden.py` 는 전부 `SPECS` 에 있거나
     사유와 함께 `NOT_FINGERPRINTED` 에 있어야 한다. 새 골든이 생기면 여기서 막힌다.
  ② **관측 대조** — 선언한 입력 패턴이 **런타임으로 관측된 읽기 전부**를 덮는지.
     트레이스는 `tests/fixtures/builder_read_traces/` 에 박제돼 있다(감사훅으로 뜬 실측,
     `scripts/_probes/probe_20260829_trace_builder_reads.py`). 나중에 누가 패턴을 좁히면
     여기서 걸린다. 코드 폐포도 같은 방식으로 관측치와 대조한다.
  ③ **변이시험** — 입력/코드/산출/fixture 네 축을 각각 흔들어 RED 이 실제로 나오는지.
     "룰이 0이라고 말한다"와 "그 축이 실제로 살아 있다"는 다른 말이다.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path, PurePosixPath

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_golden_input_fingerprints as V  # noqa: E402

TRACES = ROOT / "tests" / "fixtures" / "builder_read_traces"

# 명세 이름 -> 그 명세의 런타임 트레이스 파일 stem
TRACE_OF = {
    "ifrs17_bs": "build_ifrs17_bs",
    "pl_breakdown": "build_pl_breakdown",
    "viz_csm_waterfall": "viz_build_csm_waterfall",
    "viz_ifrs17_panels": "viz_build_ifrs17_panels",
    "dividend": "build_dividend",
    "post_transition": "test_post_transition_golden._derive",
}

# 관측됐지만 **일부러** 지문에서 뺀 읽기. 사유 없이 여기 넣지 말 것.
DELIBERATELY_UNFINGERPRINTED = {
    ".env": "OpenDART API 키. 오프라인 빌드의 산출을 결정하지 않고, 비밀값 파일을 해시해 "
            "fixture 에 남기는 것도 옳지 않다.",
}

# 빌더를 재실행하지 **않는** 골든 — 지문이 필요 없는 이유를 적는다.
NOT_FINGERPRINTED = {
    "test_kics_rules_golden": "룰 엔진 findings 매트릭스를 박제한다. 빌더를 재실행하지 않고 "
                              "<1초라 이미 훅의 오프라인 묶음에서 매 push 마다 돈다.",
    "test_master_tables_golden": "게이트 SUMMARY+exit code 를 박제한다. 빌더 재실행 없음(<1초)이고 "
                                 "이미 훅의 오프라인 묶음에 있다.",
}


def _golden_files() -> dict[str, str]:
    return {p.stem: p.read_text(encoding="utf-8")
            for p in sorted((ROOT / "tests").glob("test_*_golden.py"))}


def _reruns_a_builder(src: str) -> bool:
    """골든이 빌더/추출기를 실제로 다시 돌리는가 (= 지문이 필요한가)."""
    return bool(re.search(r"def _run_builder\(|BUILDER\s*=|_derive\(\)", src))


def test_every_builder_rerunning_golden_is_declared():
    """새 골든이 등재 없이 태어나는 것을 막는다 — 그 질문을 아무도 안 해서 생긴 구멍이다."""
    declared = {s["golden"].rsplit("/", 1)[-1][:-3] for s in V.SPECS.values()}
    undeclared = []
    for stem, src in _golden_files().items():
        if not _reruns_a_builder(src):
            continue
        if stem in declared or stem in NOT_FINGERPRINTED:
            continue
        undeclared.append(stem)
    assert not undeclared, (
        f"빌더를 재실행하는데 입력지문 등재가 없는 골든 {sorted(undeclared)} — "
        f"scripts/validate_golden_input_fingerprints.py 의 SPECS 에 넣거나, 지문이 필요 없다면 "
        f"이 파일의 NOT_FINGERPRINTED 에 사유와 함께 넣어라."
    )
    ghost = sorted(set(NOT_FINGERPRINTED) - set(_golden_files()))
    assert not ghost, f"선언에만 있고 파일이 없는 골든 {ghost}"


@pytest.mark.parametrize("name", sorted(NOT_FINGERPRINTED))
def test_unfingerprinted_golden_has_a_reason(name):
    assert len(NOT_FINGERPRINTED[name]) >= 60, (
        f"{name}: 지문 미적용 사유가 너무 짧다 — '나중에' 로 축을 빼는 것을 막는 최소 길이다")


@pytest.mark.parametrize("spec_name", sorted(TRACE_OF))
def test_declared_patterns_cover_every_observed_read(spec_name):
    """②a 선언한 입력 패턴이 **관측된 읽기 전부**를 덮어야 한다.

    빠뜨리면 그대로 false-green 이다 — 입력이 바뀌었는데 지문이 안 움직인다."""
    trace = TRACES / f"{TRACE_OF[spec_name]}.json"
    if not trace.is_file():
        pytest.skip(f"트레이스 없음: {trace.name}")
    reads = [r for r in json.loads(trace.read_text(encoding="utf-8"))["reads"]
             if not r.endswith((".py", ".pyc"))]
    patterns = V.SPECS[spec_name]["inputs"]
    uncovered = [r for r in reads
                 if r not in DELIBERATELY_UNFINGERPRINTED
                 and not any(PurePosixPath(r).full_match(p) for p in patterns)]
    assert not uncovered, (
        f"{spec_name}: 빌더가 읽는 것이 관측됐는데 어떤 입력 패턴에도 안 걸리는 파일 "
        f"{sorted(uncovered)[:10]} (총 {len(uncovered)}개). 패턴을 넓히거나, 일부러 뺀 것이면 "
        f"DELIBERATELY_UNFINGERPRINTED 에 사유와 함께 넣어라."
    )


@pytest.mark.parametrize("spec_name", sorted(TRACE_OF))
def test_code_closure_matches_runtime_observation(spec_name):
    """②b AST 폐포가 런타임으로 실제 로드된 프로젝트 모듈을 전부 포함해야 한다.

    이 대조가 `src/__init__.py` 누락을 실제로 잡아냈다(정적 해석만으로는 안 보였다)."""
    trace = TRACES / f"{TRACE_OF[spec_name]}.json"
    if not trace.is_file():
        pytest.skip(f"트레이스 없음: {trace.name}")
    observed = set(json.loads(trace.read_text(encoding="utf-8"))["project_modules"])
    observed.discard("scripts/_probes/probe_20260829_trace_builder_reads.py")   # 프로브 자신
    observed.discard(f"tests/{TRACE_OF[spec_name].split('.')[0]}.py")           # --call 진입점
    static = {p.relative_to(ROOT).as_posix()
              for p in V._code_closure(V.SPECS[spec_name]["code_entries"])}
    missing = sorted(observed - static)
    assert not missing, (
        f"{spec_name}: 런타임에 로드되는데 코드 폐포에 없는 모듈 {missing} — "
        f"그 파일을 고쳐도 지문이 안 움직인다(입력이 그대로여도 마스터는 낡는다)."
    )


# ---------------------------------------------------------------------------
# ③ 변이시험 — 네 축이 실제로 발화하는지
# ---------------------------------------------------------------------------
SMALL = "dividend"          # 8.9MB/626파일. 변이시험은 싼 명세로 돈다


@pytest.fixture(autouse=True)
def _clear_memo():
    V._MEMO.clear()
    yield
    V._MEMO.clear()


def _baseline(name=SMALL):
    return V.compute(name, V.SPECS[name])


def test_input_mutation_flips_the_input_axis():
    base = _baseline()
    spec = V.SPECS[SMALL]
    victim = V._match(spec["inputs"][0])[0]          # 캐시 파일 하나의 내용을 바꾼 셈
    V._MEMO[victim] = ("00" * 32, 1)
    mutated = V.compute(SMALL, spec)
    assert mutated["inputs_sha256"] != base["inputs_sha256"], (
        "입력 파일 내용을 바꿨는데 입력축 지문이 그대로다 — 축이 죽어 있다")
    reds = V.check(SMALL, spec, base, mutated)
    assert any("INPUTS_MOVED" in r for r in reds), reds


def test_code_mutation_flips_the_code_axis():
    base = _baseline()
    spec = V.SPECS[SMALL]
    victim = V._code_closure(spec["code_entries"])[0]
    V._MEMO[victim] = ("11" * 32, 1)
    mutated = V.compute(SMALL, spec)
    assert mutated["code_sha256"] != base["code_sha256"], (
        "빌더 코드를 바꿨는데 코드축 지문이 그대로다 — 입력이 그대로여도 마스터는 낡는다")
    assert any("CODE_MOVED" in r for r in V.check(SMALL, spec, base, mutated))


def test_pattern_going_empty_is_reported():
    """디렉터리가 옮겨지면 지문은 '안정적으로 빈' 값이 되어 조용히 통과한다 — 그걸 막는다."""
    base = _baseline()
    actual = json.loads(json.dumps(base))
    pat = next(iter(actual["input_files_per_pattern"]))
    actual["input_files_per_pattern"][pat] = 0
    reds = V.check(SMALL, V.SPECS[SMALL], base, actual)
    assert any("INPUT_PATTERN_EMPTY" in r for r in reds), reds


def test_output_drift_is_reported():
    base = _baseline()
    actual = json.loads(json.dumps(base))
    key = next(iter(actual["outputs"]))
    actual["outputs"][key]["ondisk_sha256"] = "22" * 32
    reds = V.check(SMALL, V.SPECS[SMALL], base, actual)
    assert any("OUTPUT_DRIFT" in r for r in reds), reds


def test_fixture_regenerated_without_update_is_reported():
    base = _baseline()
    actual = json.loads(json.dumps(base))
    actual["fixture_sha256"] = "33" * 32
    reds = V.check(SMALL, V.SPECS[SMALL], base, actual)
    assert any("FIXTURE_MOVED" in r for r in reds), reds


def test_unrecorded_spec_is_reported():
    """등재가 없는 명세를 조용히 통과시키면 새 골든이 무검사로 산다."""
    reds = V.check(SMALL, V.SPECS[SMALL], None, _baseline())
    assert reds and "등재가 없다" in reds[0]


def test_this_manifest_itself_runs_in_the_push_hook():
    """④ 이 파일이 훅의 오프라인 묶음에 실제로 들어 있는지.

    지문 게이트(1e)만 걸고 이 매니페스트를 안 돌리면, 명세를 좁히는 변경이 아무 저항 없이
    통과한다 — 게이트는 계속 RED=0 을 찍고, 그게 false-green 이다. "배선했다 ≠ 강제된다"."""
    src = (ROOT / "scripts" / "prepush_check.py").read_text(encoding="utf-8")
    assert '"tests/test_golden_input_fingerprint.py"' in src, (
        "이 매니페스트가 scripts/prepush_check.py 의 오프라인 테스트 묶음에서 빠졌다 — "
        "지문 게이트의 명세를 좁혀도 아무도 못 잡는 상태가 된다. 묶음에 다시 넣어라.")
    assert "goldenfp.main(" in src, (
        "prepush_check.py 가 지문 게이트를 호출하지 않는다 — 매니페스트만 남고 게이트가 죽었다.")


def test_record_file_declares_every_spec():
    record = json.loads(V.RECORD.read_text(encoding="utf-8"))
    missing = sorted(set(V.SPECS) - set(record.get("specs", {})))
    assert not missing, (
        f"등재 파일에 없는 명세 {missing} — "
        f"`python scripts/validate_golden_input_fingerprints.py --update` 를 돌려라")
