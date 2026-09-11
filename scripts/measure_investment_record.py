# -*- coding: utf-8 -*-
"""Measure (never estimate) the "substantial investment" evidence behind InsureQuant's
database-producer right and write it to docs/ip/investment_record.md.

Why this exists (2026-09-11, artifacts/legal/ip_protection_report_20260911.md §6-7):
저작권법 제2조 제20호 / 제93조 — 데이터베이스제작자의 권리는 "상당한 투자"를 입증해야
한다. 그 증거는 추정이 아니라 git 과 저장소에서 잰 숫자여야 하므로, 이 스크립트가 매
분기 같은 축을 같은 방법으로 다시 잰다. 숫자를 손으로 고치지 말고 이 스크립트를 돌려라.

Usage:
    C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/measure_investment_record.py
Reads only committed masters (git show HEAD:) so a concurrent session's half-written
working-tree file cannot skew the count.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs" / "ip" / "investment_record.md"
sys.path.insert(0, str(REPO / "scripts"))
from export_public_sheets import MASTERS, FLATTEN, read_committed_json  # noqa: E402


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, check=True,
                          encoding="utf-8", errors="replace").stdout.strip()


def count_files_lines(root: Path, suffixes: tuple[str, ...], skip_dirs: set[str] = frozenset()) -> tuple[int, int]:
    files = lines = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs and d != "__pycache__"]
        for fn in filenames:
            if fn.endswith(suffixes):
                files += 1
                lines += sum(1 for _ in (Path(dirpath) / fn).open(encoding="utf-8", errors="replace"))
    return files, lines


def main() -> None:
    today = date.today().isoformat()
    branch = git("branch", "--show-current")
    head = git("rev-parse", "--short", "HEAD")

    # --- 1. git history -----------------------------------------------------------------
    first_commit = git("log", "--reverse", "--format=%as").splitlines()[0]
    last_commit = git("log", "-1", "--format=%as")
    commit_count = int(git("rev-list", "--count", "HEAD"))
    commit_days = len(set(git("log", "--format=%as").splitlines()))
    span_days = (date.fromisoformat(last_commit) - date.fromisoformat(first_commit)).days + 1

    # --- 2. code ------------------------------------------------------------------------
    scripts_f, scripts_l = count_files_lines(REPO / "scripts", (".py",), {"_probes"})
    probes_f, probes_l = count_files_lines(REPO / "scripts" / "_probes", (".py",))
    src_f, src_l = count_files_lines(REPO / "src", (".py",))
    tests_f, tests_l = count_files_lines(REPO / "tests", (".py",))
    site_files = ["index.html", "K-ICS.html", "IFRS17.html", "공시보고서.html", "privacy.html",
                  "common.css", "download-survey.js", "report-widget.js", "forms-config.js"]
    site_l = sum(sum(1 for _ in (REPO / f).open(encoding="utf-8", errors="replace"))
                 for f in site_files if (REPO / f).exists())
    docs_f, docs_l = count_files_lines(REPO / "docs", (".md",))

    # --- 3. validation rules & tests ----------------------------------------------------
    kics_golden = json.loads((REPO / "tests/fixtures/kics_rules_golden.json").read_text(encoding="utf-8"))
    kics_rule_ids = len(kics_golden.get("by_rule", {}))
    kics_findings = len(kics_golden.get("findings", [])) if isinstance(kics_golden.get("findings"), list) \
        else sum(kics_golden.get("by_status", {}).values())
    rule_lit = re.compile(r"""rule=["']([A-Z][A-Z0-9_]+)["']|"([A-Z][A-Z0-9_]{6,})":""")
    validator_rules: set[str] = set()
    validator_files = sorted((REPO / "scripts").glob("validate_*.py"))
    for p in validator_files:
        for a, b in rule_lit.findall(p.read_text(encoding="utf-8", errors="replace")):
            validator_rules.add(a or b)
    golden_tests = sorted(p.name for p in (REPO / "tests").glob("test_*_golden.py"))
    test_funcs = sum(len(re.findall(r"^def test_", p.read_text(encoding="utf-8", errors="replace"), re.M))
                     for p in (REPO / "tests").glob("test_*.py"))

    # --- 4. master datasets (committed HEAD) --------------------------------------------
    master_rows = []
    all_companies: set[str] = set()
    all_quarters: set[str] = set()
    qre = re.compile(r"^\d{4}\.\dQ$")
    for json_name, sheet in MASTERS:
        try:
            rows = read_committed_json(json_name)
        except subprocess.CalledProcessError:
            master_rows.append((sheet, json_name, None, None, None))
            continue
        fl = FLATTEN.get(json_name)
        if fl is not None:
            rows = fl(rows)
        # 회사 키는 13개 마스터 공통으로 `원보험사코드`(export 에서는 드롭되지만 HEAD 원본엔 있다).
        # 분기는 표준 "YYYY.NQ" 만 범위 계산에 쓴다(자본비율전망은 전망연도라 표준형이 아니다).
        cos = {r.get("원보험사코드") for r in rows if r.get("원보험사코드")}
        qs_all = {str(r.get("공시분기")) for r in rows if r.get("공시분기")}
        qs = {q for q in qs_all if qre.match(q)}
        all_companies |= cos
        all_quarters |= qs
        master_rows.append((sheet, json_name, len(rows), len(cos), len(qs_all)))
    total_rows = sum(r[2] for r in master_rows if r[2] is not None)

    # --- 5. raw sources on disk (untracked, regenerable, but they were fetched+parsed here) ---
    disc_pdf = sum(1 for _ in (REPO / "data/disclosure").rglob("*.pdf")) if (REPO / "data/disclosure").exists() else 0
    disc_q = sorted(p.name for p in (REPO / "data/disclosure").glob("FY*")) if (REPO / "data/disclosure").exists() else []
    dart_raw = sum(1 for p in (REPO / "data/dart").rglob("*") if p.is_file() and "raw" in p.parts) \
        if (REPO / "data/dart").exists() else 0
    dart_q = sorted(p.name for p in (REPO / "data/dart").glob("FY*")) if (REPO / "data/dart").exists() else []
    kidi_files = sum(1 for p in (REPO / "data/kidi").rglob("*") if p.is_file()) if (REPO / "data/kidi").exists() else 0
    ir_files = sum(1 for p in (REPO / "data/ir").rglob("*") if p.is_file()) if (REPO / "data/ir").exists() else 0

    # --- 6. human review loop ------------------------------------------------------------
    gold_xlsx = len(list((REPO / "gold").glob("*.xlsx"))) if (REPO / "gold").exists() else 0
    gold_json = len(list((REPO / "data/_gold").glob("*.json"))) if (REPO / "data/_gold").exists() else 0
    inbox_resolved = sum(1 for p in (REPO / "inbox").rglob("*.md") if "_resolved" in p.parts) \
        if (REPO / "inbox").exists() else 0
    postmortems = len([p for p in (REPO / "docs/postmortems").glob("PM-*.md")]) \
        if (REPO / "docs/postmortems").exists() else 0
    changelog_l = sum(sum(1 for _ in p.open(encoding="utf-8", errors="replace"))
                      for p in (REPO / "docs").glob("*changelog*.md"))

    # --- write ----------------------------------------------------------------------------
    L: list[str] = []
    L.append("# InsureQuant 제작·검증 투자 기록 (investment record)")
    L.append("")
    L.append("이 문서는 저작권법 제2조 제20호 '상당한 투자' 입증용 내부 기록이다 (데이터베이스제작자의 권리, "
             "제93조·제95조; 부정경쟁방지법 제2조 제1호 파목 병행).")
    L.append("")
    L.append(f"> 측정일 {today} · 브랜치 `{branch}` · HEAD `{head}` · 전부 `git`/저장소에서 기계로 잰 값이다. "
             "추정치 없음. 손으로 고치지 말고 아래 갱신 명령으로 다시 잰다.")
    L.append("")
    L.append("## 갱신 명령 (분기마다)")
    L.append("")
    L.append("```bash")
    L.append("C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/measure_investment_record.py")
    L.append("```")
    L.append("")
    L.append("마스터 JSON 은 작업트리가 아니라 **커밋된 HEAD**(`git show HEAD:`)에서 읽는다 — 동시 세션이 "
             "반쯤 쓴 파일이 숫자를 흔들지 못하게. 원천 파일(data/disclosure, data/dart raw)은 git 미추적이라 "
             "**이 PC 디스크 기준**이며, 다른 머신에서 돌리면 0 으로 나올 수 있다(그때는 이 문서의 이전 값이 증거).")
    L.append("")
    L.append("## 1. 제작 기간·작업량 (git)")
    L.append("")
    L.append("| 항목 | 값 | 측정 방법 |")
    L.append("|---|---|---|")
    L.append(f"| 첫 커밋일 | {first_commit} | `git log --reverse --format=%as \\| head -1` |")
    L.append(f"| 최근 커밋일 | {last_commit} | `git log -1 --format=%as` |")
    L.append(f"| 기여 기간 | {span_days}일 (첫 커밋 ~ 최근 커밋) | 날짜 차이 + 1 |")
    L.append(f"| 커밋 수 (HEAD 도달) | {commit_count:,} | `git rev-list --count HEAD` |")
    L.append(f"| 커밋이 있는 날 수 | {commit_days} | `git log --format=%as \\| sort -u \\| wc -l` |")
    L.append("| 최초 공개 push | 2026-05-25 (CLAUDE.md 기록) | — |")
    L.append("")
    L.append("## 2. 코드 (파이프라인·검증·화면)")
    L.append("")
    L.append("| 영역 | 파일 수 | 줄 수 | 비고 |")
    L.append("|---|---:|---:|---|")
    L.append(f"| `scripts/` (파이프라인·게이트, `_probes/` 제외) | {scripts_f} | {scripts_l:,} | 다운로드·파싱·검증·빌드 |")
    L.append(f"| `scripts/_probes/` (1회성 조사 스크립트) | {probes_f} | {probes_l:,} | 조사 이력 |")
    L.append(f"| `src/` (파서 엔진·룰 엔진) | {src_f} | {src_l:,} | K-ICS Docling MD 파서, IFRS17 DART XML 파서, `kics_json_rules.py` |")
    L.append(f"| `tests/` | {tests_f} | {tests_l:,} | 골든 + 룰 커버리지 매니페스트 |")
    L.append(f"| 배포 화면 (HTML/CSS/JS {len(site_files)}개) | {len(site_files)} | {site_l:,} | 차트·표·다운로드·제보 위젯 |")
    L.append(f"| `docs/` (설계·도메인·이력 md) | {docs_f} | {docs_l:,} | 그중 changelog {changelog_l:,}줄 |")
    L.append("")
    L.append("## 3. 검증 체계")
    L.append("")
    L.append("| 항목 | 값 | 측정 방법 |")
    L.append("|---|---:|---|")
    L.append(f"| K-ICS 룰 엔진 rule id 수 | {kics_rule_ids} | `tests/fixtures/kics_rules_golden.json` `by_rule` 키 수 |")
    L.append(f"| K-ICS 룰 엔진 findings (골든 고정) | {kics_findings:,} | 같은 파일 `findings`/`by_status` |")
    L.append(f"| 게이트 validator rule id 수 (`scripts/validate_*.py` {len(validator_files)}개) | {len(validator_rules)} | `rule=\"…\"` 리터럴 + 룰표 키, 중복 제거 |")
    L.append(f"| 골든 테스트 파일 | {len(golden_tests)} | `tests/test_*_golden.py` |")
    L.append(f"| 테스트 함수 수 | {test_funcs} | `tests/test_*.py` 의 `def test_` |")
    L.append("| push 강제 | `.githooks/pre-push` → `scripts/prepush_check.py` | 데이터계약·K-ICS 룰·anomaly·inbox 위생·오프라인 테스트 |")
    L.append("")
    L.append("골든 테스트: " + ", ".join(f"`{g}`" for g in golden_tests))
    L.append("")
    L.append("## 4. 데이터베이스 규모 (커밋된 마스터 JSON, HEAD)")
    L.append("")
    L.append("| 시트 | 파일 | 행 | 회사 수 | 분기 수 |")
    L.append("|---|---|---:|---:|---:|")
    for sheet, jn, n, c, q in master_rows:
        if n is None:
            L.append(f"| {sheet} | `{jn}` | (HEAD 에 없음) | | |")
        else:
            L.append(f"| {sheet} | `{jn}` | {n:,} | {c} | {q} |")
    L.append(f"| **합계** | {len(master_rows)}개 마스터 | **{total_rows:,}** | 합집합 {len(all_companies)} | "
             f"합집합 {len(all_quarters)} ({min(all_quarters) if all_quarters else '-'} ~ {max(all_quarters) if all_quarters else '-'}) |")
    L.append("")
    L.append("행 = (회사 × 분기 × 항목) 셀 단위. 각 셀은 원문 PDF/XML 에서 자동 추출 → 룰 게이트 → "
             "필요 시 owner 수기 검토(gold)를 거쳤다.")
    L.append("")
    L.append("## 5. 원천 자료 (이 PC 디스크, git 미추적)")
    L.append("")
    L.append("| 원천 | 파일 수 | 비고 |")
    L.append("|---|---:|---|")
    L.append(f"| 정기경영공시 PDF (`data/disclosure/**/*.pdf`) | {disc_pdf:,} | 분기 폴더 {len(disc_q)}개 "
             f"({disc_q[0] if disc_q else '-'} ~ {disc_q[-1] if disc_q else '-'}) → Docling MD → 파서 |")
    L.append(f"| DART raw (`data/dart/**/raw/**`) | {dart_raw:,} | 분기 폴더 {len(dart_q)}개, XML/zip 원문 |")
    L.append(f"| KIDI 통계 (`data/kidi/`) | {kidi_files:,} | 월별 보험료 통계 |")
    L.append(f"| IR 자료 (`data/ir/`) | {ir_files:,} | 팩트시트·시리즈 JSON (xlsx 는 2026-09-11 부터 git 미추적) |")
    L.append("")
    L.append("## 6. 사람 검토 루프")
    L.append("")
    L.append("| 항목 | 값 | 비고 |")
    L.append("|---|---:|---|")
    L.append(f"| owner 답지 xlsx (`gold/`) | {gold_xlsx} | 손으로 검증한 정답지, git 추적 |")
    L.append(f"| 셀 단위 정정 레지스트리 (`data/_gold/*.json`) | {gold_json} | owner 확정 셀·예외 등재 |")
    L.append(f"| 스테이지 간 처리 완료 티켓 (`inbox/**/_resolved/*.md`) | {inbox_resolved:,} | 검증→파서 재작업 왕복 기록 |")
    L.append(f"| 포스트모템 (`docs/postmortems/PM-*.md`) | {postmortems} | 게이트가 놓친 사고의 룰 배선 기록 |")
    L.append("")
    L.append("## 7. 이 기록의 쓰임")
    L.append("")
    L.append("- 데이터베이스제작자의 권리(저작권법 제93조)는 등록 없이 제작 완료 시 생기지만, 분쟁에서 "
             "\"소재의 수집·검증·갱신에 인적·물적으로 상당한 투자\"를 한 쪽이 입증한다. 위 표가 그 1차 증거다.")
    L.append("- 저작권 등록(한국저작권위원회)이나 상표 출원 시 첨부 자료로도 쓴다. "
             "배경: `artifacts/legal/ip_protection_report_20260911.md`.")
    L.append("- 분기 라운드가 끝날 때마다 갱신 명령을 돌리고 이 파일을 커밋한다 (publishing 스테이지).")
    L.append("")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(L), encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(REPO)} ({len(L)} lines, HEAD {head})")


if __name__ == "__main__":
    main()
