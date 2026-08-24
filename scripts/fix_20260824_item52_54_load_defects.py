# -*- coding: utf-8 -*-
"""orchestrator 발주(2026-08-24) -- item52/53/54 적재 결함 A~E 정정.

Source ticket: inbox/parser/20260824T0400Z__validation__MULTI__item52_54_load_defects.md
전체 재현·판정 근거는 세션 답변(`## 답변 (parser-kics)`, 같은 파일) 참조. 여기서는 조치만 요약.

## A. 카카오페이(KR1098) 5분기 -- item52 100배 축소 (근본원인 수정 + 기존 5셀 직접정정)
근본원인: `fix_20260824_tfi_capital_memo_rows.py::_infer_scale()`의 ALL_ZERO_TRIVIAL 숏컷이
"47/48/49/51 이 전부 0 이라 그 넷의 스케일은 무관하다"는 판정을 같은 버킷의 item52(대개
실값, 채무성자본 0 인 회사도 지급여력금액 자체는 억대)에도 그대로 적용했다. 그 스크립트에
패치를 넣어(ALL_ZERO_TRIVIAL 이어도 item52 vs 마스터 item1 앵커로 재확인) 460버킷 전수
재스캔 -- **변경은 정확히 이 5버킷뿐**(`scripts/_probes/probe_20260824_scale_diff.py` 로
전후 대조, 나머지 455버킷 scale_method 완전 동일 -- 전후 전수 무손상 확인).
이미 로드된 5셀은 재실행으로 자동 정정되지 않으므로(idempotent guard) 여기서 직접 UPDATE.
raw 재확인(5분기 전부, 이 세션에서 fitz 좌표 직접 재추출): item50(기본자본)과 item52가
같은 값으로 인쇄(보완자본=0인 회사), item50 은 이미 올바르게 /100 되어 있었다 -- item52 도
같은 배율을 적용.

## B. 삼성화재(KR0008) 2025.3Q item52_적용후 -- owner 예외 승인 (2026-08-24)
저장소 기본원칙("발행사 자기모순이면 원문대로 싣는다", feedback_issuer_inconsistent_keep_as_
disclosed)의 명시적 예외. owner: "삼성은 너무 자기모순이 자명해 보이는데 걔만 올바른 숫자로
우리가 고쳐서 올리고 나머지는 원수사 모순 그대로 가자." raw p16(FY2025_Q3) 재확인:
  지급여력금액   28,650,195   28,605,195   <- 자릿수 전치(650 <-> 605), 605쪽이 인쇄오류
  기본자본       17,928,794   17,928,794
  보완자본       10,721,402   10,721,402
  지급여력기준금액 10,383,339  10,383,339
  주1) 당사는 기발행 신종자본증권 및 후순위채무가 없어 공통적용 경과조치 전·후
       지급여력비율이 동일함
검산: 28,650,195/10,383,339=275.926%(인쇄 지급여력비율 275.92 와 일치) vs
28,605,195/10,383,339=275.492%(불일치). 기본자본+보완자본=28,650,196(오차 1, 반올림)도
650,195 쪽과만 맞는다. item1(헤드라인, 전=후 286502)·item50·item51 은 이미 정확 -- 안 건드림.

## C. 농협생명(KR0104) 2024.3Q item53/54_적용후 -- 삭제(결측 복귀)
raw p8(FY2024_Q3) 재확인: "(기발행 신종자본증권) 250,000 [칸2는 빈칸-전각공백뿐]" /
"(기발행 후순위채무) 939,171 [칸2는 빈칸]". 마스터의 값_적용후(37,913.42 / 19,008.63)는
원문 어디에도 없다 -- **원인 규명**: 이 페이지는 "(1)공통적용경과조치"(좌) + "②장수위험
경과조치"(우) 2단 좌우 배치 레이아웃인데, y좌표만으로 행을 묶는 클러스터링이 같은 높이의
서로 다른 표 값을 한 행으로 합쳤다(우측 표의 "기본요구자본" PRE=3,791,342 / "생명·장기
손해보험위험액" PRE=1,900,863 이 좌측 표의 신종자본증권/후순위채무 행에 섞여 들어와
classify()의 "len(vals)>=2 -> 앞 2개를 pre/post로" 로직이 그걸 집었다. 3,791,342/100=
37,913.42, 1,900,863/100=19,008.63 -- 정확히 일치, 원인 확정).

## (opportunistic, 원 티켓 B) 처브라이프(KR0100) 2023.1Q item54 -- 같은 원인, 같이 정정
raw p6(FY2023_Q1) 재확인: 같은 2단 레이아웃 버그. "(기발행 후순위채무)" 행이 우측 표의
"해지위험" PRE=84,006 을 주워 item54[값]=840.06 으로 잘못 실렸다(원문 자체는 대시=0).
item53 은 우연히 이 페이지에서 해당 행에 우측표 값이 안 섞여 이미 0/0 으로 정확했다(안 건드림).

## D. 푸본현대(KR0083) 2024.3Q -- **티켓 주장과 반대, 변경 없음**
raw p15(FY2024_Q3) 를 dpi=400 으로 확대한 결과, 신종자본증권/후순위채무 두 메모행의
"적용전" 칸이 대각선 취소선으로 명시적으로 병합/공란 처리돼 있고, 실값(40,000 · 505,185)은
"적용후" 칸에 인쇄돼 있다(좌표로도 재확인: x1=547.9, 후행 전각공백 보정시 ~537.9 -- 적용후
컬럼 우측정렬 앵커 536.9~537.2 와 거의 정확히 일치, 적용전 앵커 389.5~389.8 과는 148pt
이상 이격). 현재 마스터(값=결측, 값_적용후=400.00/5,051.85)가 이미 원문과 일치 --
**스왑하지 않는다.** (티켓의 아스키 표는 좌표 없는 평문 추출로 보이며 육안상 첫 줄=PRE로
오판했을 가능성 -- validation 재확인 요청, 답변 참고.)

## E. 행 유실 3건 -- 좌표로 컬럼 확정 후 INSERT (전부 PRE 단일컬럼, POST 완전공란)
  - 롯데손해(KR0003) 2026.1Q item53: 라벨 손상 확인("신〮자본증권", U+302E 혼입).
    raw p22, PRE=45,370(x1=397.9, PRE 앵커와 일치) -> 453.70. item54(이미 적재)와 동일패턴.
  - 동양생명(KR0087) 2024.1Q item53/54: raw p14, PRE=344,567/0(x1=377.1, PRE 앵커 일치)
    -> 3445.67 / 0.0.
  - 하나생명(KR0097) 2025.2Q item53: raw p20, PRE=dash=0(x1=389.4, PRE 앵커 일치) -> 0.0.
    item54(이미 적재, 값=0)와 동일패턴.

## (opportunistic, 원 티켓 F) 동양생명(KR0087) 2024.3Q item54 -- raw 재판독으로 확정, INSERT
원 티켓은 "페이지 경계로 판독불가"라 했으나, 다음 페이지(14) 맨 위에서 발견:
"(기발행 후순위채무) 0"(x1=377.1, PRE 앵커 일치, POST 완전공란) -> 0.0.

전부 raw 좌표 재확인(fitz get_text("words") + D 는 get_pixmap(dpi=400) 시각대조까지) 후
반영. idempotent(이미 반영됐으면 스킵) + --dry-run 지원.

Usage:
  ...python scripts/fix_20260824_item52_54_load_defects.py --dry-run
  ...python scripts/fix_20260824_item52_54_load_defects.py
"""
from __future__ import annotations

import json
import sys
import os
from pathlib import Path

sys.stdout = os.fdopen(1, "w", encoding="utf-8", closefd=False)

REPO = Path(__file__).resolve().parents[1]
TARGET = REPO / "kics_disclosure.json"

LABEL53 = "(기발행 신종자본증권)(TFI표, 공통적용경과조치)"
LABEL54 = "(기발행 후순위채무)(TFI표, 공통적용경과조치)"


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
    raise SystemExit(f"FATAL: {code} 메타를 찾을 수 없음(전체 마스터에 이 회사 행이 없음)")


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    n0 = len(data)
    print(f"로드 전 row_count = {n0:,}")

    log = []  # (op, code, q, item, field, old, new)

    def upd(code, q, item_no, field, new_val, expect_old):
        r = find_row(data, code, q, item_no)
        if r is None:
            raise SystemExit(f"FATAL: UPDATE 대상 없음 {code} {q} item{item_no}")
        old = r.get(field)
        if old == new_val:
            log.append(("SKIP(이미반영)", code, q, item_no, field, old, new_val))
            return
        if expect_old is not None and str(old) != str(expect_old):
            raise SystemExit(
                f"FATAL: {code} {q} item{item_no}.{field} 현재값({old!r})이 예상값"
                f"({expect_old!r})과 다름 -- 동시편집 의심, 중단")
        r[field] = new_val
        log.append(("UPDATE", code, q, item_no, field, old, new_val))

    def delfield(code, q, item_no, field, expect_old):
        r = find_row(data, code, q, item_no)
        if r is None:
            raise SystemExit(f"FATAL: DELETE 대상 없음 {code} {q} item{item_no}")
        if field not in r:
            log.append(("SKIP(이미없음)", code, q, item_no, field, None, None))
            return
        old = r[field]
        if expect_old is not None and str(old) != str(expect_old):
            raise SystemExit(
                f"FATAL: {code} {q} item{item_no}.{field} 현재값({old!r})이 예상값"
                f"({expect_old!r})과 다름 -- 동시편집 의심, 중단")
        del r[field]
        log.append(("DELETE", code, q, item_no, field, old, None))

    def ins(code, q, item_no, label, vals: dict):
        existing = find_row(data, code, q, item_no)
        if existing is not None:
            log.append(("SKIP(이미존재)", code, q, item_no, "row", existing, None))
            return
        meta = find_company_meta(data, code)
        row = {
            "원보험사코드": code, "원수사명": meta["원수사명"],
            "티커": meta["티커"], "생손보여부": meta["생손보여부"],
            "항목번호": item_no, "항목명": label, "공시분기": q,
        }
        row.update(vals)
        data.append(row)
        log.append(("INSERT", code, q, item_no, "row", None, row))

    # ---------------- A. 카카오페이 item52 /100 (5분기, 값+값_적용후 둘다) ----------------
    kakaopay_item52 = [
        ("2023.1Q", "38147", "381.47"),
        ("2023.2Q", "31350", "313.5"),
        ("2023.3Q", "119870", "1198.7"),
        ("2023.4Q", "97416", "974.16"),
        ("2024.1Q", "86725", "867.25"),
    ]
    for q, old, new in kakaopay_item52:
        upd("KR1098", q, 52, "값", new, expect_old=old)
        upd("KR1098", q, 52, "값_적용후", new, expect_old=old)

    # ---------------- B. 삼성화재 item52_적용후 (owner 예외 승인 2026-08-24) ----------------
    upd("KR0008", "2025.3Q", 52, "값_적용후", "286501.95", expect_old="286051.95")

    # ---------------- opportunistic: 처브라이프 item54[값] (2단 레이아웃 버그, C와 동일원인) ----------------
    upd("KR0100", "2023.1Q", 54, "값", "0", expect_old="840.06")

    # ---------------- C. 농협생명 item53/54_적용후 삭제 (2단 레이아웃 버그) ----------------
    delfield("KR0104", "2024.3Q", 53, "값_적용후", expect_old="37913.42")
    delfield("KR0104", "2024.3Q", 54, "값_적용후", expect_old="19008.63")

    # ---------------- D. 푸본현대 -- 변경 없음 (검증만, 코드 없음) ----------------

    # ---------------- E. 행 유실 3건 INSERT (전부 PRE 단일컬럼) ----------------
    ins("KR0003", "2026.1Q", 53, LABEL53, {"값": "453.7"})
    ins("KR0087", "2024.1Q", 53, LABEL53, {"값": "3445.67"})
    ins("KR0087", "2024.1Q", 54, LABEL54, {"값": "0"})
    ins("KR0097", "2025.2Q", 53, LABEL53, {"값": "0"})

    # ---------------- opportunistic (원 티켓 F): 동양생명 2024.3Q item54 ----------------
    ins("KR0087", "2024.3Q", 54, LABEL54, {"값": "0"})

    # ---------------- 리포트 ----------------
    print(f"\n=== 변경 로그 ({len(log)}건) ===")
    for op, code, q, item_no, field, old, new in log:
        if op == "INSERT":
            print(f"  {op:14s} {code} {q} item{item_no} {field} = {new}")
        else:
            print(f"  {op:14s} {code} {q} item{item_no}.{field}: {old!r} -> {new!r}")

    n_update = sum(1 for r in log if r[0] == "UPDATE")
    n_delete = sum(1 for r in log if r[0] == "DELETE")
    n_insert = sum(1 for r in log if r[0] == "INSERT")
    n_skip = sum(1 for r in log if r[0].startswith("SKIP"))
    print(f"\nUPDATE={n_update} DELETE={n_delete} INSERT={n_insert} SKIP={n_skip}")

    if dry:
        print("\n(dry-run; 파일 안 씀)")
        return 0

    if n_update == 0 and n_delete == 0 and n_insert == 0:
        print("변경 없음 -- 파일 안 씀")
        return 0

    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {TARGET.name} (row_count {n0:,} -> {len(data):,})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
