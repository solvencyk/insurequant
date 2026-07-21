"""Consolidator (validation stage, MECHANICAL step) — turn validator output JSONs into
inbox/ handoff messages so the human's only job is to tell the next stage "check inbox".

This replaces the former agent/by-hand conversion (inbox/README.md previously said
"이 변환을 자동화하는 consolidator는 향후 작업"). Division of labour: this script does the
mechanical finding -> message conversion; the parser/validation AGENTS stay judgment-only
(diagnosis, routing real_error vs justified vs no_anchor).

Idempotent: a finding already represented by a message in inbox/parser/ OR inbox/_resolved/
(any timestamp) is skipped — re-running never duplicates and never re-raises a resolved
thread. So the loop is: validator runs -> `python scripts/consolidate_inbox.py` -> human
tells parser "check inbox".

Currently consolidates (VALIDATORS): CSM continuity (csm_continuity_validation.json),
K-ICS rate sensitivity RS1/RS2 RED (data/_derived/kics_rate_sensitivity_validation.json),
and CSM waterfall must_reparse (csm_waterfall_validation.json). The RS and waterfall handlers
are PRE-WIRED per owner 2026-06-12 backlog #2: all three RED buckets are empty post-build, so
they emit nothing today — but the moment a RED appears the consolidator auto-routes it to the
parser (no schema-discovery delay). Schemas are known: RS from the runner's explicit dict keys
(validate_kics_rate_sensitivity.py), waterfall from the `failed` bucket (same object, bucketed
only by the must_reparse flag).
To add a validator: write a `_<name>_findings(by_co)` returning the finding dicts (must carry
to/route/topic/company/name/period/rule/detail/section/body/request) and append to VALIDATORS.

Also (owner 2026-06-16 B): every run, after consolidation, `_archive_resolved()` moves any
`status: resolved` message from a stage folder to inbox/_resolved/ (answered=stays). So
"끝난 스레드를 손으로 안 옮겨도" — resolved threads auto-archive on each run.

Run:  python scripts/consolidate_inbox.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
INBOX = ROOT / "inbox"
MASTER = ROOT / "CSM_waterfall.json"
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ")
STAGES = ("downloader", "parser", "validation", "publishing", "designer")


def _load_master():
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    by_co: dict[str, dict] = {}
    for r in rows:
        by_co.setdefault(r["원보험사코드"], {}).setdefault(r["공시분기"], {})[r["항목번호"]] = r.get("값")
    return by_co


def _identity(qd):
    """Internal closing-identity for one quarter: 기초+신+이+가+상 vs 기말."""
    v = {k: qd.get(k) for k in range(1, 7)}
    if any(v[k] is None for k in range(1, 7)):
        return "n/a (missing item)"
    lhs = v[1] + v[2] + v[3] + v[4] + v[5]
    tag = "OK" if abs(lhs - v[6]) <= max(1.0, abs(v[6]) * 0.01) else "BREAK"
    return f"{tag} (기초{v[1]:.1f}+신{v[2]:.1f}+이{v[3]:.1f}+가{v[4]:.1f}+상{v[5]:.1f}={lhs:.1f} vs 기말{v[6]:.1f})"


def _continuity_findings(by_co):
    src = ROOT / "data" / "dart" / "viz" / "csm_continuity_validation.json"
    if not src.exists():
        return []
    flagged = json.loads(src.read_text(encoding="utf-8")).get("flagged", {})
    out = []
    for co, info in flagged.items():
        cod = by_co.get(co, {})
        for f in info["findings"]:
            rule = f["rule"]
            if rule == "WITHIN_FY_OPENING_DRIFT":
                fy = f["fy"]
                pslug = f"FY{fy}"
                periods = sorted([p for p in cod if p.startswith(str(fy))])
                lines = [f"FY{fy} 내 분기별 기초 CSM + 내부 closing-identity:"]
                for p in periods:
                    lines.append(f"- {p}: 기초={cod[p].get(1)} | identity {_identity(cod[p])}")
            else:  # FY_BOUNDARY_DISCONTINUITY
                p = f["period"]
                pslug = p
                prev = f"{int(p[:4]) - 1}.4Q"
                lines = [
                    f"FY 경계: {prev} 기말={cod.get(prev, {}).get(6)} vs {p} 기초={cod.get(p, {}).get(1)}",
                    f"- {prev}: identity {_identity(cod.get(prev, {}))}",
                    f"- {p}: identity {_identity(cod.get(p, {}))}",
                ]
            nh = info["name"].replace("보험", "")[:4]
            out.append({
                "to": "parser", "route": "reparse", "topic": "continuity",
                "company": co, "name": info["name"], "period": pslug, "rule": rule,
                "detail": f["detail"], "body": "\n".join(lines),
                "section": "마스터(CSM_waterfall.json) 값 + 내부 정합",
                "request": (
                    f"extracted_history(또는 extracted)에서 {info['name']} 해당 분기 raw 재독 "
                    f"(hint: `data/dart/extracted_history/*{nh}*csm.json`; 롤포워드는 보통 `*_measurement.json`).\n"
                    "내부 identity가 OK면 워터폴 내부정합 → break는 오차 아닌 불연속(연도경계/별도·연결/재진술). raw 롤포워드(기초행)로 앵커 확인.\n"
                    "분류 회신: real_error / justified_restatement / no_anchor(→escalate) / refetch(raw 누락)."
                ),
            })
    return out


_NAME2CODE: dict[str, str] | None = None


def _name2code():
    """원수사명 -> 원보험사코드 (kics_disclosure.json = 정본 회사 레지스트리). RS/waterfall은
    검증 JSON에 코드가 없고 한글 사명만 있어 매핑 — 미스매치 시 사명 자체를 토큰으로 폴백."""
    global _NAME2CODE
    if _NAME2CODE is None:
        src = ROOT / "kics_disclosure.json"
        m: dict[str, str] = {}
        if src.exists():
            for r in json.loads(src.read_text(encoding="utf-8")):
                n, c = r.get("원수사명"), r.get("원보험사코드")
                if n and c:
                    m[n] = c
        _NAME2CODE = m
    return _NAME2CODE


def _rate_sensitivity_findings(by_co):
    """RS1/RS2 RED -> parser reparse 메시지. 현재 두 버킷 0건(선배선, owner 2026-06-10 발주).
    스키마는 validate_kics_rate_sensitivity.py가 dict 키를 명시 생성(151-152행)."""
    src = ROOT / "data" / "_derived" / "kics_rate_sensitivity_validation.json"
    if not src.exists():
        return []
    d = json.loads(src.read_text(encoding="utf-8"))
    n2c = _name2code()
    out = []
    for r in d.get("RS1_ratio_identity", []):
        co, q = r["회사"], r["분기"]
        out.append({
            "to": "parser", "route": "reparse", "topic": "rs1_ratio",
            "company": n2c.get(co, co), "name": co, "period": q, "rule": "RS1_RATIO_IDENTITY",
            "detail": f"{r['경과조치']} {r['컬럼']} 비율 {r['비율']} ≠ 금액/기준금액×100 (expected {r['expected']})",
            "section": "금리민감도 마스터(kics_rate_sensitivity.json) 항등식",
            "body": f"- 경과조치 {r['경과조치']} / 컬럼 {r['컬럼']}: 공시비율={r['비율']} vs expected(금액/기준금액×100)={r['expected']}",
            "request": ("kics_rate_sensitivity.json 해당 (사,분기,경과조치) 행 재독 — 비율/금액/기준금액 셀 오매핑·% 미파싱·delta 오변환 확인. "
                        "`scripts/extract_kics_rate_sensitivity.py` 재실행. 분류: real_error / justified(basis차이) / refetch(MD 누락)."),
        })
    for r in d.get("RS2_base_anchor", []):
        co, q = r["회사"], r["분기"]
        out.append({
            "to": "parser", "route": "reparse", "topic": "rs2_base",
            "company": n2c.get(co, co), "name": co, "period": q, "rule": "RS2_BASE_ANCHOR",
            "detail": f"{r['measure']} base {r['base']} vs 공시 {r['disclosure']} (diff {r['diff']})",
            "section": "금리민감도 base vs kics_disclosure 앵커(item1/14/27)",
            "body": f"- {r['measure']}: 민감도표 base={r['base']} / kics_disclosure={r['disclosure']} / diff={r['diff']}",
            "request": ("민감도표 base 컬럼이 헤드라인(item1/14/27)과 불일치 — 별도/연결 basis 차이면 RS2_EXCEPTIONS 등재 요청, "
                        "아니면 base행 오매핑 reparse. 분류: justified(basis) / real_error / refetch."),
        })
    return out


def _waterfall_findings(by_co):
    """CSM 워터폴 must_reparse 버킷 -> parser reparse 메시지. 현재 0건(선배선).
    스키마는 같은 빌더(validate_csm_waterfall.py)의 `failed` 버킷과 동일 객체(must_reparse 플래그로만 분기)."""
    src = ROOT / "data" / "dart" / "viz" / "csm_waterfall_validation.json"
    if not src.exists():
        return []
    d = json.loads(src.read_text(encoding="utf-8"))
    n2c = _name2code()
    out = []
    for r in d.get("must_reparse", []):
        co = r["company"]
        rcept = str(r.get("rcept_no") or "")
        period = r.get("period_hint") or (f"FY{int(rcept[:4]) - 1}" if rcept[:4].isdigit() else rcept or "annual")
        bal = r.get("balance", {}) or {}
        miss = ",".join(bal.get("missing_stages") or [])
        issues = "; ".join(r.get("issues") or []) or "balance break"
        out.append({
            "to": "parser", "route": "reparse", "topic": "waterfall",
            "company": n2c.get(co, co), "name": co, "period": str(period), "rule": "CSM_WATERFALL_MUST_REPARSE",
            "detail": f"waterfall_status={r.get('waterfall_status')} / {issues}",
            "section": "CSM 워터폴 검증(csm_waterfall_validation.json)",
            "body": "\n".join([
                f"- rcept_no: {rcept}",
                f"- caption: {r.get('caption')}",
                f"- balance.ok={bal.get('ok')} missing_stages=[{miss}] residual={bal.get('residual_mn_krw')} tol={bal.get('tolerance_mn_krw')}",
                f"- new_business={r.get('new_business_mn_krw')} (ok={r.get('new_business_ok')})",
            ]),
            "request": ("해당 공시(rcept_no)의 측정요소별 변동표 재독 — 누락 stage(assumption/amortization 등) 재추출 또는 표 분할/이미지 스티칭 확인. "
                        "워터폴 추출기 재실행 후 must_reparse 해소. 분류: real_error / justified(미공시) / refetch."),
        })
    return out


def _data_contract_findings(by_co):
    """data-contract 게이트(validate_data_contract.py) RED -> route별 메시지. 게이트가
    `data/_derived/data_contract_report.json`을 emit하면 활성(현재 미emit = pre-wired, [] 반환 —
    RS/waterfall 핸들러와 동일 패턴, owner 2026-06-16 #2). kind별 라우팅:
    EFFECTIVE_LIST_* -> downloader refetch(채권 유효목록); 그 외(STALE_AS_OF/MISSING_FILER/
    PARENT_ZERO/MASTER_HOLE/MISSING_PROVENANCE 등) -> parser reparse. 기존 K-ICS/master 핸들러와
    중복 가능한 census/등식 RED은 idempotent _exists()가 흡수."""
    src = ROOT / "data" / "_derived" / "data_contract_report.json"
    if not src.exists():
        return []
    d = json.loads(src.read_text(encoding="utf-8"))
    n2c = _name2code()
    downloader_kinds = {"EFFECTIVE_LIST_NOT_FILTERED", "MISSING_EFFECTIVE_LIST"}
    out = []
    for r in d.get("reds", []):
        kind = str(r.get("kind") or r.get("code") or "DATA_CONTRACT")
        co = r.get("company_code") or r.get("company") or ""
        name = r.get("name") or co
        if co and not str(co).startswith("KR"):
            co = n2c.get(co, co)
        q = r.get("quarter") or "ALL"
        to = "downloader" if kind in downloader_kinds else "parser"
        route = "refetch" if to == "downloader" else "reparse"
        detail = r.get("detail") or kind
        out.append({
            "to": to, "route": route, "topic": f"dc_{kind.lower()}",
            "company": co or name, "name": name, "period": q, "rule": kind,
            "detail": detail,
            "section": "data-contract 게이트(validate_data_contract.py)",
            "body": f"- {detail}",
            "request": ("data-contract RED 해소 — 해당 (사,분기) 재추출/재페치 또는 provenance 사이드카 emit. "
                        "RED 1건이라도 있으면 push 불가(owner). 분류: real_error / refetch / escalate(진짜 unfixable)."),
        })
    return out


VALIDATORS = [_continuity_findings, _rate_sensitivity_findings, _waterfall_findings,
              _data_contract_findings]


def _frontmatter_status(path):
    """md frontmatter의 'status:' 값(첫 --- 블록만)."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return None
    in_fm = False
    for i, line in enumerate(text.splitlines()):
        s = line.strip()
        if i == 0 and s == "---":
            in_fm = True
            continue
        if in_fm and s == "---":
            break
        if in_fm and s.lower().startswith("status:"):
            return s.split(":", 1)[1].strip().lower()
    return None


def _archive_resolved():
    """완료(status: resolved) 스레드를 stage 폴더 -> inbox/_resolved/ 자동 이동(owner 2026-06-16 B).
    `answered`는 sender 재확인 대기라 남김 — resolved만. idempotent(이미 _resolved/면 stage에 없음;
    동명 충돌 skip). 추적파일이면 git mv(이력보존), 아니면 plain move. 한글 파일명 안전."""
    import shutil
    import subprocess
    resolved_dir = INBOX / "_resolved"
    resolved_dir.mkdir(exist_ok=True)
    moved = []
    for stage in STAGES:
        d = INBOX / stage
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.md")):
            if _frontmatter_status(p) != "resolved":
                continue
            dest = resolved_dir / p.name
            if dest.exists():
                # 동명이 이미 _resolved/에 있음(동시 세션 등) = 이 stage 사본은 superseded 중복.
                # stage 폴더에 resolved를 남기지 않도록 중복 제거(resolved=완료라 안전, owner 2026-06-16).
                try:
                    subprocess.run(["git", "rm", "-f", str(p)], cwd=str(ROOT),
                                   capture_output=True, check=True)
                except Exception:
                    p.unlink()
                moved.append(f"{stage}/{p.name} (중복 제거; _resolved에 이미 있음)")
                continue
            try:
                subprocess.run(["git", "mv", str(p), str(dest)], cwd=str(ROOT),
                               capture_output=True, check=True)
            except Exception:
                shutil.move(str(p), str(dest))
            moved.append(f"{stage}/{p.name}")
    return moved


TEMPLATE = """---
from: validation
to: {to}
created: {stamp}
status: open
route: {route}
company: {company}
period: {period}
rule: {rule}
iter: 1
---

## 미결 (sender 작성)
{name} ({company}) {rule} — {detail}

### {section}
{body}

### 요청
{request}

## 답변 (recipient 작성 — 처리 후)
"""


def _exists(company, period, topic):
    """True if a message for this (company, period, topic) already lives in parser/ or _resolved/."""
    pat = f"*__validation__{company}_{period}__{topic}.md"
    return any(list((INBOX / sub).glob(pat)) for sub in ("parser", "_resolved"))


def main():
    by_co = _load_master()
    findings = [f for v in VALIDATORS for f in v(by_co)]
    written, skipped = [], 0
    for f in findings:
        if _exists(f["company"], f["period"], f["topic"]):
            skipped += 1
            continue
        fn = INBOX / f["to"] / f"{STAMP}__validation__{f['company']}_{f['period']}__{f['topic']}.md"
        fn.write_text(TEMPLATE.format(stamp=STAMP, **f), encoding="utf-8")
        written.append(fn.name)
    print(f"[consolidate] findings={len(findings)} written={len(written)} skipped(existing)={skipped}")
    for w in written:
        print("  +", w)
    if not written:
        print("  (inbox already up to date — nothing new)")

    moved = _archive_resolved()
    print(f"[archive] resolved threads moved to inbox/_resolved/: {len(moved)}")
    for m in moved:
        print("  ->", m)


if __name__ == "__main__":
    main()
