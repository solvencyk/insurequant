# -*- coding: utf-8 -*-
"""비공개 시트 3종 + 자본성증권발행현황 공개 열 제한 (owner 2026-10-12).

① `기본자본소진율`·`보완자본소진율`·`자본비율전망` 은 공개 사이트에서 접근 불가여야 한다. 저장소(마스터 JSON ·
   마스터 xlsx · 내부 산출)에는 남고, main(라이브)에서만 지워진다.
   - 공개 스냅샷(`public_exports/<시트>.json`)을 만들지 않고 manifest 에도 싣지 않는다.
   - 배포 스크립트 `PRIVATE_PATHS` 가 main 에서 그 경로(+ 루트 JSON)를 `git rm` 한다.
   - 두 목록(exporter 의 `private_paths()` / 스크립트의 `PRIVATE_PATHS`)은 같아야 한다.
② 공개 `자본성증권발행현황` 에는 한도·인정액 계산 열이 없고 발행 사실 열은 있다.

배포 시험은 로컬 bare 저장소 2개로 스크립트를 실제로 돌린다(네트워크·실제 origin 불필요). 변이시험: 비공개 목록에서
경로 하나를 빼면 그 경로가 main 에 남아 시험이 실패해야 한다.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

SCRIPT = ROOT / "scripts" / "android_push_and_deploy.sh"
PE = ROOT / "public_exports"

CAPSEC = "자본성증권발행현황"
CAPSEC_DROPPED = {"기본자본인정액_억", "보완자본인정액_억", "기본자본한도_억", "SCR_억",
                  "보완자본인정율", "경과조치", "경과조치종료일"}
CAPSEC_KEPT = {"회사명", "구분", "종류", "발행일", "콜만기도래일", "법정만기일", "콜근거",
               "액면가_억", "잔액_억", "공시분기", "잔액기준일", "출처"}


def _sh_private_paths(text: str | None = None) -> list[str]:
    text = text if text is not None else SCRIPT.read_text(encoding="utf-8")
    m = re.search(r'^PRIVATE_PATHS="([^"]*)"', text, re.M)
    assert m, "배포 스크립트에 PRIVATE_PATHS=\"...\" 가 없다"
    return m.group(1).split()


def test_script_private_paths_match_exporter():
    from export_public_sheets import private_paths
    assert sorted(_sh_private_paths()) == sorted(private_paths()), (
        "배포 스크립트 PRIVATE_PATHS 와 export_public_sheets.private_paths() 가 다르다 — 한쪽만 고치면 "
        "비공개 시트가 main 에 남거나(스크립트 쪽 누락) 공개 스냅샷이 계속 생긴다(exporter 쪽 누락)")


def test_private_sheets_have_no_public_snapshot_and_no_manifest_entry():
    from export_public_sheets import PRIVATE_SHEETS
    man = json.loads((PE / "manifest.json").read_text(encoding="utf-8"))
    for s in PRIVATE_SHEETS:
        assert not (PE / f"{s}.json").exists(), f"비공개 시트 {s} 의 공개 스냅샷이 있다"
        assert s not in man["sheets"], f"manifest 에 비공개 시트 {s} 가 있다"


def test_private_sheets_stay_in_repo_masters():
    """저장소 내부 보관: 마스터 JSON 과 내부 xlsx 시트 정의(MASTERS)는 그대로다."""
    from build_master_xlsx import MASTERS
    from export_public_sheets import PRIVATE_SHEETS, PRIVATE_ROOT_JSONS
    sheets = {m[1] for m in MASTERS}
    for s in PRIVATE_SHEETS:
        assert s in sheets, f"내부 xlsx 시트 정의에서 {s} 가 빠졌다(비공개는 내부 보관이다)"
    for j in PRIVATE_ROOT_JSONS:
        assert (ROOT / j).exists(), f"루트 JSON {j} 가 저장소에서 지워졌다(내부 보관이어야 한다)"


def test_private_paths_not_downloadable_from_survey_js():
    js = (ROOT / "download-survey.js").read_text(encoding="utf-8")
    live = "\n".join(l for l in js.splitlines() if not l.lstrip().startswith("//"))
    from export_public_sheets import PRIVATE_SHEETS
    for s in PRIVATE_SHEETS:
        assert f"public_exports/{s}.json" not in live, f"download-survey.js 가 비공개 시트 {s} 를 아직 내려준다"


# ---------------------------------------------------------------- 자본성증권발행현황 공개 열

def test_capsec_public_snapshot_drops_computed_columns():
    rows = json.loads((PE / f"{CAPSEC}.json").read_text(encoding="utf-8"))
    assert rows
    cols = {k for r in rows for k in r}
    assert not (cols & CAPSEC_DROPPED), f"공개본에 계산 열이 있다: {sorted(cols & CAPSEC_DROPPED)}"
    assert CAPSEC_KEPT <= cols, f"공개본에서 발행 사실 열이 빠졌다: {sorted(CAPSEC_KEPT - cols)}"


def test_capsec_drop_list_matches_declared_and_master_keeps_columns():
    from export_public_sheets import drop_cols
    assert CAPSEC_DROPPED <= drop_cols(CAPSEC)
    assert not (CAPSEC_KEPT & drop_cols(CAPSEC))
    master = json.loads((ROOT / "kics_capital_securities.json").read_text(encoding="utf-8"))
    rows = master["rows"] if isinstance(master, dict) else master
    cols = {k for r in rows for k in r}
    assert CAPSEC_DROPPED <= cols, "마스터 JSON 에서 계산 열이 사라졌다 — 내부 보관이어야 한다(소진율·전망 내부 계산이 쓴다)"


def _gate_rows(out_dir):
    import validate_live_artifacts as L
    fd = L.Findings()
    L.check_public_exports(fd, out_dir=out_dir)
    return fd.rows


def test_mutation_capsec_dropped_column_leak_fires(tmp_path):
    pe = tmp_path / "public_exports"
    shutil.copytree(PE, pe)
    p = pe / f"{CAPSEC}.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    d[0]["기본자본인정액_억"] = 1.0
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    assert "PUBLIC_EXPORT_INTERNAL_COL_LEAKED" in {r["rule"] for r in _gate_rows(pe)}


def test_mutation_capsec_drop_list_shrunk_is_caught(monkeypatch, tmp_path):
    """제외 목록에서 열 하나를 빼면(게이트가 기대하는 공개 열이 늘어나) 현재 스냅샷과 어긋나 발견이 나와야 한다."""
    import export_public_sheets as E
    pe = tmp_path / "public_exports"
    shutil.copytree(PE, pe)
    monkeypatch.setitem(E._SHEET_DROP_COLS, CAPSEC, frozenset(CAPSEC_DROPPED - {"SCR_억"}))
    assert {r["rule"] for r in _gate_rows(pe)} & {"PUBLIC_EXPORT_DRIFT", "PUBLIC_EXPORT_MISSING_CELL"}


def test_mutation_private_snapshot_present_fires(tmp_path):
    pe = tmp_path / "public_exports"
    shutil.copytree(PE, pe)
    (pe / "자본비율전망.json").write_text("[]", encoding="utf-8")
    assert "PUBLIC_EXPORT_PRIVATE_SHEET_PRESENT" in {r["rule"] for r in _gate_rows(pe)}


# ---------------------------------------------------------------- 배포 스크립트 건조 실행 (로컬 bare 저장소)

def _bash():
    for c in (r"C:\Program Files\Git\bin\bash.exe", "/usr/bin/bash"):
        if Path(c).exists():
            return c
    return shutil.which("bash")


def _git(cwd, *a, check=True):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)
    r = subprocess.run(["git", "-c", "core.quotePath=false", "-c", "user.name=t", "-c", "user.email=t@t",
                        "-c", "core.autocrlf=false", *a], cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", env=env)
    if check and r.returncode != 0:
        raise AssertionError(f"git {a} failed: {r.stderr}")
    return r


PRIVATE_SAMPLE = ["public_exports/기본자본소진율.json", "public_exports/보완자본소진율.json",
                  "public_exports/자본비율전망.json", "kics_tier1_utilization.json", "kics_tier2_utilization.json",
                  "kics_forward_capital.json"]
KEPT_SAMPLE = ["public_exports/자본성증권발행현황.json", "other.json", "kics_disclosure.json"]
UPDATED_SAMPLE = ["public_exports/manifest.json", "other.json"]


def _run_deploy(tmp_path, script_text):
    """origin(bare) <- main(옛 공개본) / work(새 브랜치) 를 만들고 clone 안에서 스크립트를 돌린다. 반환 = (rc, out, bare)."""
    bash = _bash()
    if not bash or not shutil.which("git"):
        pytest.skip("bash/git 없음")
    bare = tmp_path / "origin.git"
    seed = tmp_path / "seed"
    clone = tmp_path / "phone"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(bare)], check=True)
    seed.mkdir()
    _git(seed, "init", "-q", "-b", "main")
    _git(seed, "remote", "add", "origin", str(bare))

    def put(rel, text):
        p = seed / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="\n")

    for rel in PRIVATE_SAMPLE + KEPT_SAMPLE + UPDATED_SAMPLE:
        put(rel, f"old {rel}\n")
    put("index.html", "old\n")
    _git(seed, "add", "-A")
    _git(seed, "commit", "-q", "-m", "main old")
    _git(seed, "push", "-q", "origin", "main")
    _git(seed, "checkout", "-q", "-b", "work")
    for rel in PRIVATE_SAMPLE + UPDATED_SAMPLE + KEPT_SAMPLE:
        put(rel, f"new {rel}\n")                      # 브랜치에서는 전부 갱신됨(비공개도 저장소에는 남는다)
    put("scripts/android_push_and_deploy.sh", script_text)
    _git(seed, "add", "-A")
    _git(seed, "commit", "-q", "-m", "work")
    _git(seed, "push", "-q", "origin", "work")

    _git(tmp_path, "clone", "-q", str(bare), str(clone))
    _git(clone, "fetch", "-q", "origin", "work")
    _git(clone, "checkout", "-q", "-B", "work", "origin/work")
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull,
               GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    r = subprocess.run([bash, "scripts/android_push_and_deploy.sh", "--from-origin", "--branch", "work"],
                       cwd=clone, capture_output=True, text=True, encoding="utf-8", env=env, timeout=900)
    return r, bare


def _main_files(bare):
    r = _git(bare, "ls-tree", "-r", "--name-only", "main")
    return set(r.stdout.splitlines())


def _main_blob(bare, rel):
    return _git(bare, "show", f"main:{rel}").stdout


def _script_text():
    return SCRIPT.read_text(encoding="utf-8").replace("\r\n", "\n")


def test_deploy_removes_private_paths_from_main_and_keeps_the_rest(tmp_path):
    # 시험용 PRIVATE_PATHS 는 실제 스크립트의 것 그대로(샘플 경로가 같은지 먼저 확인).
    assert sorted(_sh_private_paths()) == sorted(PRIVATE_SAMPLE)
    r, bare = _run_deploy(tmp_path, _script_text())
    assert r.returncode == 0, r.stdout + r.stderr
    files = _main_files(bare)
    for rel in PRIVATE_SAMPLE:
        assert rel not in files, f"{rel} 가 main 에 남았다"
    for rel in KEPT_SAMPLE + UPDATED_SAMPLE:
        assert rel in files, f"{rel} 가 main 에서 사라졌다"
    # 비공개가 아닌 파일은 브랜치의 새 내용으로 갱신 경로를 탄다.
    assert _main_blob(bare, "other.json") == "new other.json\n"
    assert _main_blob(bare, "public_exports/manifest.json") == "new public_exports/manifest.json\n"
    assert _main_blob(bare, "kics_disclosure.json") == "new kics_disclosure.json\n"
    # 작업 브랜치(저장소)에는 비공개 파일이 그대로 있다.
    assert set(_git(bare, "ls-tree", "-r", "--name-only", "work").stdout.splitlines()) >= set(PRIVATE_SAMPLE)


@pytest.mark.parametrize("missing", [PRIVATE_SAMPLE[0], PRIVATE_SAMPLE[3]])   # 공개 스냅샷 1개 + 루트 JSON 1개(전수는 느리다: git 호출 수십 회)
def test_mutation_private_path_removed_from_list_leaves_it_on_main(tmp_path, missing):
    text = _script_text()
    m = re.search(r'^PRIVATE_PATHS="([^"]*)"', text, re.M)
    mutated = text.replace(m.group(0), 'PRIVATE_PATHS="' + " ".join(
        p for p in m.group(1).split() if p != missing) + '"')
    assert mutated != text
    r, bare = _run_deploy(tmp_path, mutated)
    assert r.returncode == 0, r.stdout + r.stderr
    # 목록에서 빠진 경로는 비공개로 처리되지 않고 일반 갱신 대상이 되어 main 에 남는다(이 시험이 위 시험의 변이 대조다).
    assert missing in _main_files(bare)


def test_no_deployed_page_fetches_a_private_root_json():
    """비공개로 main 에서 지우는 루트 JSON 을 라이브 HTML/JS 가 fetch 하면 그 패널이 조용히 빈칸이 된다."""
    from export_public_sheets import PRIVATE_ROOT_JSONS
    pages = [p for p in list(ROOT.glob("*.html")) + list(ROOT.glob("*.js")) if p.is_file()]
    assert pages
    hits = []
    for p in pages:
        t = p.read_text(encoding="utf-8", errors="replace")
        t = "\n".join(l for l in t.splitlines() if not l.lstrip().startswith("//"))
        hits += [f"{p.name}:{j}" for j in PRIVATE_ROOT_JSONS if j in t]
    assert not hits, f"비공개 루트 JSON 을 아직 참조하는 페이지: {hits}"
