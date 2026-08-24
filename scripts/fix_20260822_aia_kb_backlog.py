# -*- coding: utf-8 -*-
"""inbox 발주 후속 — AIA(KR0080) 6분기 + KB손해(KR0010) 5분기의 item47-51
([지급여력비율의 경과조치 적용에 관한 사항] "1) 공통적용 경과조치 관련" 6줄 표) 신규 UPSERT.

두 회사 다 IMAGE_OCR_COMPANIES 판정(또는 그에 준하는 라벨-이미지화) 코호트라 fitz 텍스트/Docling MD
전부 이 섹션에서 실패한다(표 자체가 래스터이거나, 라벨 폰트의 ToUnicode CMap이 깨져 숫자만 간간이
살아있고 라벨은 빈칸/"∙"로 나온다). `get_pixmap(dpi=300)` 렌더링 육안 판독으로 11분기 전부 확정했다
(owner 승인 방식, KR0010 2025.1Q 선례 `fix_20260821_kr0010_2025q1_vision.py`와 동일 기법).

## 페이지 위치 (회사·분기별로 다름 — 짧은형식은 "4-2 지급여력비율" 상세표 2페이지 뒤,
## AIA 연차(4Q) 풀폼은 TOC의 "5-2.지급여력비율" 페이지 뒤 약 5페이지, KB 연차(4Q)는
## "Ⅴ.경영지표 5-2.지급여력비율" 섹션 안)

AIA(KR0080), 전부 raw PDF p(0-idx) 렌더 dpi300 육안판독, 단위 백만원, **경과조치 전=후 항상 동일**
(각주 "당사는 경과조치를 적용하지 않아 경과조치 전·후 금액 및 비율이 동일함", 6분기 전부 재확인):
  2024.4Q  FY2024_Q4/raw p54(printed55/112)
  2025.1Q  FY2025_Q1/raw p17(printed18/32)
  2025.2Q  FY2025_Q2/raw p18(printed19/52)
  2025.3Q  FY2025_Q3/raw p17(printed18/33)
  2025.4Q  FY2025_Q4/raw p59(printed60/115)
  2026.1Q  FY2026_Q1/raw p19(printed20/36)

KB손해(KR0010), 전부 raw PDF 렌더 dpi300 육안판독, 단위 백만원:
  2024.1Q  FY2024_Q1/raw(_amended) p14(문서쪽 13/25)  -- 47/48/49/50/51 전부 전=후 동일
  2024.3Q  FY2024_Q3/raw(_amended) p14(문서쪽 13/23)  -- 상동, 전=후 동일
  2025.3Q  FY2025_Q3/raw          p17(문서쪽 16/26)  -- item47(보완자본한도적용전)만 전≠후
                                                          (전=1,416,518 / 후=740,103), 나머지 전=후
  2025.4Q  FY2025_Q4/raw          p69(문서쪽 68/136) -- 상동 패턴(연차 풀폼, "Ⅴ.경영지표 5-2" 섹션)
  2026.1Q  FY2026_Q1/raw          p18(문서쪽 17/27)  -- 상동 패턴

KB 2025.3Q/2025.4Q/2026.1Q에서 item47이 전≠후인 이유: 이 세 분기부터 공통적용 경과조치 중
TFI(제도시행前 기발행자본증권 가용자본 인정범위 확대)가 실질 O(적용)로 전환됐다(2024.1Q/2024.3Q는
표 앞부분의 "(1)공통적용 경과조치 관련" 적용여부 표를 안 봤지만 47-51 전부 전=후로 나온 것과 대조됨,
2025.3Q/2026.1Q는 적용여부 표에서 TFI·업무보고서 O 직접 확인). 그래도 지급여력비율·지급여력금액·
기본자본·보완자본·보완자본한도·초과분·지급여력기준금액은 세 분기 다 전=후 동일하게 인쇄된다 —
TFI 효과가 "보완자본 한도 적용 전"(pre-cap pool 구성)에만 나타나고 최종 booked 보완자본에는
반영 안 되는 것으로 보이나, 이건 관찰된 사실을 그대로 옮긴 것이지 재구성한 값이 아니다.

## 자체검산 (전부 아래 스크립트 실행 시 재출력됨, dry-run 로그 참고)

- item50+item51 ≈ 마스터 기존 item1 (전·후 각각): 11분기 전부 diff<=0.44(억원) 이내.
- item48(보완자본한도) ≈ 마스터 기존 item14(전) x 50%: 11분기 전부 근사(원문 인쇄값 자체가 SCR x
  50% 공식과 정합 — 마스터 값과 별개로 원문 자체 내적 일관성).
- item51 과의 관계는 **회사·분기마다 다른 두 패턴**으로 나뉜다(강제로 하나로 맞추지 않음, 원문 그대로):
    UNCAPPED(item51==item47, 자리수까지 정확히 일치): AIA 6분기 전부, KB 2024.1Q, KB 2024.3Q
    MIN+초과분(item51==min(item47_전,item48)+item49, item47은 "전" 컬럼값 사용):
      KB 2025.3Q(72986.39==72986.39) · KB 2025.4Q(71808.71≈71808.72,diff0.01) ·
      KB 2026.1Q(72777.51≈72777.52,diff0.01) — 전부 소수점 둘째자리까지 정확.

## 스코프 밖(발견했지만 손대지 않음)

- 이 조사 중 IMAGE_OCR_COMPANIES = {"KR0010","KR0079"} (src/solvency/validation/kics_json_rules.py
  L70)에 KR0080(AIA)은 **등록돼 있지 않다** — 발주 지문의 "둘 다 이미지/스캔 코호트로 등록돼 있다"는
  설명은 이 레지스트리 기준으로는 부정확하다(KR0079=미래에셋생명, AIA와 무관). KR0080은 실제로는
  "라벨 텍스트만 이미지/CMap-broken, 본문 서술은 정상 추출"이라는 별개 패턴이라 이 레지스트리 소속
  여부와 무관하게 vision이 필요했다 — 다만 이 사실 자체는 validation/orchestrator에 보고할 사항이라
  이 스크립트는 건드리지 않는다(레지스트리 수정은 이 티켓 범위 밖).
- KB의 "(기발행 후순위채무)" 행(2024.1Q=659,282 / 2024.3Q=667,264 / 2025.3Q=676,415 /
  2025.4Q=672,249 / 2026.1Q=659,265, 백만원)은 기존 스키마에 대응 항목번호가 없어 적재하지 않는다
  (참고용으로 이 주석에만 기록). AIA는 이 행이 전부 "-"(0)이라 애초에 무관.

Usage:
  ...python scripts/fix_20260822_aia_kb_backlog.py --dry-run
  ...python scripts/fix_20260822_aia_kb_backlog.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

TARGET = REPO / "kics_disclosure.json"

ITEM_LABELS = {
    47: "보완자본 한도 적용 전",
    48: "보완자본 한도",
    49: "해약환급금 부족분 상당액 중 해약환급금 상당액 초과분",
    50: "기본자본(TFI표, 공통적용경과조치)",
    51: "보완자본(TFI표, 공통적용경과조치)",
}

# raw 값은 전부 (단위: 백만원) 원문 인쇄 그대로. (pre, post) 튜플 -- 대다수는 pre==post.
# code -> quarter -> item -> (pre_raw_million, post_raw_million)
RAW_MILLION: dict[str, dict[str, dict[int, tuple[float, float]]]] = {
    "KR0080": {
        "2024.4Q": {
            47: (329101, 329101), 48: (681301, 681301), 49: (327777, 327777),
            50: (2922184, 2922184), 51: (329101, 329101),
        },
        "2025.1Q": {
            47: (304808, 304808), 48: (683692, 683692), 49: (303717, 303717),
            50: (2905493, 2905493), 51: (304808, 304808),
        },
        "2025.2Q": {
            47: (378228, 378228), 48: (710262, 710262), 49: (377370, 377370),
            50: (2857546, 2857546), 51: (378228, 378228),
        },
        "2025.3Q": {
            47: (387109, 387109), 48: (744190, 744190), 49: (386485, 386485),
            50: (2745954, 2745954), 51: (387109, 387109),
        },
        "2025.4Q": {
            47: (395736, 395736), 48: (742483, 742483), 49: (393733, 393733),
            50: (2642453, 2642453), 51: (395736, 395736),
        },
        "2026.1Q": {
            47: (427964, 427964), 48: (767495, 767495), 49: (426182, 426182),
            50: (2533765, 2533765), 51: (427964, 427964),
        },
    },
    "KR0010": {
        "2024.1Q": {
            47: (5732948, 5732948), 48: (2870521, 2870521), 49: (4951923, 4951923),
            50: (5884321, 5884321), 51: (5732948, 5732948),
        },
        "2024.3Q": {
            47: (6607913, 6607913), 48: (3045224, 3045224), 49: (5675506, 5675506),
            50: (5799178, 5799178), 51: (6607913, 6607913),
        },
        "2025.3Q": {
            47: (1416518, 740103), 48: (3236843, 3236843), 49: (5882121, 5882121),
            50: (5078401, 5078401), 51: (7298639, 7298639),
        },
        "2025.4Q": {
            47: (1413832, 741583), 48: (3182316, 3182316), 49: (5767039, 5767039),
            50: (5009995, 5009995), 51: (7180872, 7180872),
        },
        "2026.1Q": {
            47: (1397123, 737858), 48: (3331903, 3331903), 49: (5880628, 5880628),
            50: (5108092, 5108092), 51: (7277752, 7277752),
        },
    },
}

# 원문 근거(회사, 분기) -> raw PDF 상대경로 + 0-idx 페이지 (get_pixmap dpi=300 로 재확인 가능)
SOURCE_PAGE = {
    ("KR0080", "2024.4Q"): (r"data\disclosure\FY2024_Q4\raw\KR0080_에이아이에이생명보험.pdf", 54),
    ("KR0080", "2025.1Q"): (r"data\disclosure\FY2025_Q1\raw\KR0080_에이아이에이생명보험.pdf", 17),
    ("KR0080", "2025.2Q"): (r"data\disclosure\FY2025_Q2\raw\KR0080_에이아이에이생명보험.pdf", 18),
    ("KR0080", "2025.3Q"): (r"data\disclosure\FY2025_Q3\raw\KR0080_에이아이에이생명보험.pdf", 17),
    ("KR0080", "2025.4Q"): (r"data\disclosure\FY2025_Q4\raw\KR0080_에이아이에이생명보험.pdf", 59),
    ("KR0080", "2026.1Q"): (r"data\disclosure\FY2026_Q1\raw\KR0080_에이아이에이생명보험.pdf", 19),
    ("KR0010", "2024.1Q"): (r"data\disclosure\FY2024_Q1\raw\KR0010_KB손해보험_amended.pdf", 14),
    ("KR0010", "2024.3Q"): (r"data\disclosure\FY2024_Q3\raw\KR0010_KB손해보험_amended.pdf", 14),
    ("KR0010", "2025.3Q"): (r"data\disclosure\FY2025_Q3\raw\KR0010_KB손해보험.pdf", 17),
    ("KR0010", "2025.4Q"): (r"data\disclosure\FY2025_Q4\raw\KR0010_KB손해보험.pdf", 69),
    ("KR0010", "2026.1Q"): (r"data\disclosure\FY2026_Q1\raw\KR0010_KB손해보험.pdf", 18),
}


def _fmt(x: float) -> str:
    return str(int(round(x))) if abs(x - round(x)) < 1e-6 else f"{x:.2f}".rstrip("0").rstrip(".")


def _num(v) -> float | None:
    if v is None:
        return None
    try:
        return float(str(v).replace(",", ""))
    except ValueError:
        return None


def main() -> int:
    dry = "--dry-run" in sys.argv
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    print(f"로드 전 row_count = {len(data):,}")

    meta: dict[str, dict] = {}
    existing: set[tuple[str, str, int]] = set()
    m1: dict[tuple[str, str], tuple[float | None, float | None]] = {}
    m14: dict[tuple[str, str], float | None] = {}
    for r in data:
        c, q = r["원보험사코드"], r["공시분기"]
        if c not in meta:
            meta[c] = {"원수사명": r.get("원수사명"), "티커": r.get("티커"),
                       "생손보여부": r.get("생손보여부")}
        it = int(r["항목번호"])
        existing.add((c, q, it))
        if it == 1:
            m1[(c, q)] = (_num(r.get("값")), _num(r.get("값_적용후")))
        if it == 14:
            m14[(c, q)] = _num(r.get("값"))

    new_rows = []
    census = []
    for code, quarters in RAW_MILLION.items():
        if code not in meta:
            print(f"  [WARN] {code} 마스터에 행 자체 없음 -- 건너뜀")
            continue
        for q, items in quarters.items():
            src_rel, src_page = SOURCE_PAGE[(code, q)]
            n_ins = n_skip = 0
            for it in (47, 48, 49, 50, 51):
                if (code, q, it) in existing:
                    n_skip += 1
                    continue
                pre_raw, post_raw = items[it]
                pre = round(pre_raw / 100.0, 2)
                post = round(post_raw / 100.0, 2)
                row = {
                    "원보험사코드": code,
                    "원수사명": meta[code]["원수사명"],
                    "티커": meta[code]["티커"],
                    "생손보여부": meta[code]["생손보여부"],
                    "항목번호": it,
                    "항목명": ITEM_LABELS[it],
                    "공시분기": q,
                    "값": _fmt(pre),
                    "값_적용후": _fmt(post),
                }
                new_rows.append(row)
                n_ins += 1
                print(f"  INSERT {code} {q} item{it}({ITEM_LABELS[it]}) "
                      f"값={row['값']} 값_적용후={row['값_적용후']}  "
                      f"(source: {src_rel} p{src_page}[0-idx])")

            # 자체검산 -- item50+51 vs 기존 item1
            v50pre, v50post = (round(items[50][0] / 100.0, 2), round(items[50][1] / 100.0, 2))
            v51pre, v51post = (round(items[51][0] / 100.0, 2), round(items[51][1] / 100.0, 2))
            v47pre = round(items[47][0] / 100.0, 2)
            v48pre = round(items[48][0] / 100.0, 2)
            v49pre = round(items[49][0] / 100.0, 2)
            m1pre, m1post = m1.get((code, q), (None, None))
            m14pre = m14.get((code, q))
            sum_pre = v50pre + v51pre
            sum_post = v50post + v51post
            diff_pre = (sum_pre - m1pre) if m1pre is not None else None
            diff_post = (sum_post - m1post) if m1post is not None else None
            uncapped_match = abs(v51pre - v47pre) < 0.02
            mincap_val = min(v47pre, v48pre) + v49pre
            mincap_match = abs(v51pre - mincap_val) < 0.05
            cap50pct = (m14pre * 0.5) if m14pre is not None else None
            print(f"    검산 {code} {q}: 50+51(전)={sum_pre:.2f} vs item1(전)={m1pre} "
                  f"diff={diff_pre}  |  50+51(후)={sum_post:.2f} vs item1(후)={m1post} diff={diff_post}")
            print(f"    검산 {code} {q}: item48(전)={v48pre:.2f} vs item14(전)x50%={cap50pct}  |  "
                  f"UNCAPPED(51==47)={'OK' if uncapped_match else 'no'}  "
                  f"MIN+49(51==min(47,48)+49)={'OK' if mincap_match else 'no'}(계산값={mincap_val:.2f})")

            census.append((code, q, n_ins, n_skip))

    print(f"\n합계: INSERT {len(new_rows)}건")
    print("\n=== (회사,분기)별 요약 ===")
    for code, q, n_ins, n_skip in census:
        print(f"  {code} {q}: 신규 {n_ins} / 스킵(기존존재) {n_skip}")

    if dry:
        print("\n(dry-run; 파일 안 씀)")
        return 0
    if not new_rows:
        print("쓸 셀 없음")
        return 0

    data.extend(new_rows)
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{len(new_rows)}행 INSERT, wrote {TARGET.name} "
          f"(row_count {len(data) - len(new_rows):,} -> {len(data):,})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
