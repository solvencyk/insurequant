# -*- coding: utf-8 -*-
"""parser-kics 발주(2026-08-25) -- item52(TFI표 자신의 지급여력금액 행) 잔여 30버킷 갭 중
텍스트로 안 읽히는(font-remap/스캔) 18버킷을 vision 판독으로 INSERT한다.

Group2(fix_20260825_item52_gap_group2_textread.py, 12버킷 텍스트추출)의 나머지 절반.
이 18버킷은 fitz.get_text()로 "공통적용"+"보완자본"+"한도" 3키워드 동시매치가 전부 0회
(NO_MATCHED_PAGE, fix_20260824_tfi_capital_memo_rows.py --dry-run 재확인)라 페이지 자체가
텍스트로 안 읽힌다. 원인 확인(read-only, scripts/_probes/probe_20260825_group1_triage.py):
  - KR0005/KR0010(5)/KR0087(2026.1Q)/KR0097(2024.2Q)/KR1098(3): fitz 문자밀도 0~33자/p
    (KR0097은 완전 0자 -- 순수 스캔). KR0010 2025.4Q만 예외로 230자/p인데도 5개 키워드
    전부 0회 -- vision 렌더(scripts/_probes/render_20260825_item52_vision_targets.py)로
    확인해보니 화면은 완전 정상 텍스트다(폰트 ToUnicode CMap 깨짐, KB손해 2025.1Q 계열
    선례와 동일 -- reference-kics-company-quirks 메모리 참고).
  - KR0080(AIA, 6분기): 문자밀도는 100~500자/p로 준수한데 "공통적용" 리터럴이 전체 문서에
    0회. 페이지 171/330(2024.4Q)을 직접 열어보니 "보완자본"+"한도"+"지급여력금액"이 전부
    있는 건 재무제표 주석 4.3 자본위험관리의 **서술형 문단**(제도 설명, TFI표 아님)이었다
    -- 3키워드 필터가 정확히 걸러낸 것이 맞고, 실제 TFI표는 라벨이 이미지화된 별도 섹션에
    있다(과거 fix_20260822_aia_kb_backlog.py가 이미 vision으로 47-51을 확정한 바로 그 표).
  - KR0071(흥국생명) 2024.4Q: p1-112가 래스터 스캔(538p 문서의 앞부분).

## 페이지 출처 (전부 이전 세션이 vision으로 이미 확정한 자리 재사용 + 이번 세션 재확인)

  KR0080(AIA) 6분기 + KR0010(KB손해) 5분기: `fix_20260822_aia_kb_backlog.py`의 SOURCE_PAGE
    (item47-51을 vision으로 이미 확정한 표 -- 이번 세션이 같은 페이지를 dpi=300 재렌더링해서
    "지급여력금액" 헤더행(기본자본 바로 위 행)만 추가로 읽었다. 렌더 파일:
    scripts/_probes/render_20260825_item52_vision_targets.py 산출물, 육안 재확인함).
  KR0005(흥국화재) 2024.4Q: `fix_20260822_singles_backlog.py`가 잡은 p41(1-idx)=p40(0-idx),
    이번 세션이 dpi=280으로 재렌더링해 직접 읽음(같은 표, 기본자본 바로 위 행).
  KR1098(카카오페이) 3분기 + KR0097(하나생명) 2024.2Q + KR0071(흥국생명) 2024.4Q: 이번
    세션은 재렌더링하지 않았다 -- `fix_20260822_kakaopay_hana_heungkuk_backlog.py`의
    docstring이 **이미 vision으로 읽은 "지급여력금액" 값을 원문 그대로 인용**해 놓았다
    (해당 스크립트의 코드(VALUES dict)는 47-51만 담았지만, 조사 당시 서술 텍스트에
    "지급여력금액 NN,NNN/NN,NNN" 문구가 그대로 남아있다 -- 새 vision 세션 없이 그 인용을
    그대로 옮긴다).

## 교차검산 (item50 + item51 vs 이번에 적재하는 item52/100, 전부 억원 기준 오차 0.3 이내)

  KR0080(AIA) 6분기: 29221.84+3291.01=32512.85 vs 32512.85(diff 0.00) ... 6분기 전부 diff<=0.01
  KR0010(KB) 5분기: 58843.21+57329.48=116172.69 vs 116172.69(diff 0.00) ... 5분기 전부 diff<=0.01
  KR0005 2024.4Q: 전 5301.83+22591.82=27893.65 vs 27893.65(diff 0.00) / 후 7421.83+20471.82=
    27893.65 vs 27893.65(diff 0.00, item52 자체가 전=후 동일하게 인쇄됨 -- 원문 그대로)
  KR1098 2024.2Q: 774.40+0=774.40 vs 774.40(diff 0.00)
  KR1098 2024.3Q: 666.24+0=666.24 vs 666.24(diff 0.00)
  KR1098 2024.4Q: 535.61+7.86=543.47 vs 543.46(diff 0.01, 반올림)
  KR0097 2024.2Q: 2468.53+2811.44=5279.97 vs 5279.97(diff 0.00)
  KR0071 2024.4Q: 전 19013.70+16144.38=35158.08 vs 35158.08(diff 0.00) / 후 19510.19+15647.88=
    35158.07 vs 35158.08(diff 0.01, 반올림 -- 원문에도 전=후 지급여력금액이 3,515,808으로
    동일하게 인쇄됨, `fix_20260822_kakaopay_hana_heungkuk_backlog.py` D절 각주 참고)
  KR0087 2026.1Q: 15920.06+27537.20=43457.26 vs 43457.26(diff 0.00)

Usage:
  ...python scripts/fix_20260825_item52_gap_group1_vision.py --dry-run
  ...python scripts/fix_20260825_item52_gap_group1_vision.py
"""
from __future__ import annotations

import json
import sys
import os
from pathlib import Path

sys.stdout = os.fdopen(1, "w", encoding="utf-8", closefd=False)

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "kics_disclosure.json"

LABEL52 = "지급여력금액(TFI표, 공통적용경과조치)"


def _fmt(x: float) -> str:
    return str(int(round(x))) if abs(x - round(x)) < 1e-6 else f"{x:.2f}".rstrip("0").rstrip(".")


# (code, quarter, raw_pre_백만원, raw_post_백만원) -- 이번 세션 vision 재확인(AIA/KB/KR0005) 또는
# 이전 세션 vision 조사기록의 직접 원문인용(KR1098/KR0097/KR0071) 그대로.
RAW = [
    ("KR0080", "2024.4Q", 3251285, 3251285),
    ("KR0080", "2025.1Q", 3210301, 3210301),
    ("KR0080", "2025.2Q", 3235773, 3235773),
    ("KR0080", "2025.3Q", 3133063, 3133063),
    ("KR0080", "2025.4Q", 3038189, 3038189),
    ("KR0080", "2026.1Q", 2961729, 2961729),
    ("KR0010", "2024.1Q", 11617269, 11617269),
    ("KR0010", "2024.3Q", 12407091, 12407091),
    ("KR0010", "2025.3Q", 12377040, 12377040),
    ("KR0010", "2025.4Q", 12190866, 12190866),
    ("KR0010", "2026.1Q", 12385844, 12385844),
    ("KR0005", "2024.4Q", 2789365, 2789365),
    ("KR1098", "2024.2Q", 77440, 77440),
    ("KR1098", "2024.3Q", 66624, 66624),
    ("KR1098", "2024.4Q", 54346, 54346),
    ("KR0097", "2024.2Q", 527997, 527997),
    ("KR0071", "2024.4Q", 3515808, 3515808),
    ("KR0087", "2026.1Q", 4345726, 4345726),
]


def find_row(data, code, q, item_no):
    hits = [r for r in data if r.get("원보험사코드") == code and r.get("공시분기") == q
            and int(r.get("항목번호", -1)) == item_no]
    if len(hits) > 1:
        raise SystemExit(f"FATAL: 중복행 {code} {q} item{item_no}: {len(hits)}건")
    return hits[0] if hits else None


def find_company_meta(data, code):
    for r in data:
        if r.get("원보험사코드") == code:
            return {"원수사명": r.get("원수사명"), "티커": r.get("티커"),
                    "생손보여부": r.get("생손보여부")}
    raise SystemExit(f"FATAL: {code} 메타를 찾을 수 없음")


def _num(r, field):
    v = r.get(field) if r else None
    if v is None or v == "":
        return None
    return float(v)


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    n0 = len(data)
    print(f"로드 전 row_count = {n0:,}")

    log = []
    warn = []

    for code, q, raw_pre, raw_post in RAW:
        existing = find_row(data, code, q, 52)
        if existing is not None:
            log.append(("SKIP(이미존재)", code, q, existing))
            continue

        r50 = find_row(data, code, q, 50)
        r51 = find_row(data, code, q, 51)
        if r50 is None or r51 is None:
            raise SystemExit(f"FATAL: {code} {q} item50/51 이 없음 -- 이 스크립트 스코프 밖")

        pre = round(raw_pre / 100.0, 2)
        post = round(raw_post / 100.0, 2)

        sum_pre = sum_post = None
        p50, p51 = _num(r50, "값"), _num(r51, "값")
        if p50 is not None and p51 is not None:
            sum_pre = p50 + p51
        p50p, p51p = _num(r50, "값_적용후"), _num(r51, "값_적용후")
        if p50p is not None and p51p is not None:
            sum_post = p50p + p51p

        if sum_pre is not None and abs(sum_pre - pre) > 0.3:
            warn.append(f"{code} {q}: PRE 교차검산 어긋남 item50+51={sum_pre:.2f} vs 신규 item52={pre:.2f}")
        if sum_post is not None and abs(sum_post - post) > 0.3:
            warn.append(f"{code} {q}: POST 교차검산 어긋남 item50+51={sum_post:.2f} vs 신규 item52={post:.2f}")

        meta = find_company_meta(data, code)
        row = {
            "원보험사코드": code, "원수사명": meta["원수사명"],
            "티커": meta["티커"], "생손보여부": meta["생손보여부"],
            "항목번호": 52, "항목명": LABEL52, "공시분기": q,
            "값": _fmt(pre), "값_적용후": _fmt(post),
        }
        data.append(row)
        log.append(("INSERT", code, q, row))

    print(f"\n=== 변경 로그 ({len(log)}건) ===")
    for entry in log:
        op = entry[0]
        if op == "INSERT":
            _, code, q, row = entry
            print(f"  INSERT  {code} {q} item52 값={row['값']} 값_적용후={row['값_적용후']}")
        else:
            _, code, q, existing = entry
            print(f"  {op}  {code} {q} item52 (현재 값={existing.get('값')} 값_적용후={existing.get('값_적용후')})")

    if warn:
        print(f"\n=== 교차검산 경고 ({len(warn)}건) ===")
        for w in warn:
            print(f"  !! {w}")

    n_insert = sum(1 for e in log if e[0] == "INSERT")
    n_skip = sum(1 for e in log if e[0].startswith("SKIP"))
    print(f"\nINSERT={n_insert} SKIP={n_skip}")

    if warn:
        print("\n교차검산 경고가 있어 안전을 위해 파일을 쓰지 않는다 -- 원인 규명 후 재실행할 것.")
        return 1

    if dry:
        print("\n(dry-run; 파일 안 씀)")
        return 0
    if n_insert == 0:
        print("쓸 셀 없음")
        return 0

    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{n_insert}행 INSERT, wrote {TARGET.name} (row_count {n0:,} -> {len(data):,})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
