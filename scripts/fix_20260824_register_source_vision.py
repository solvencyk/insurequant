"""`SOURCE_UNREADABLE_NOT_VERIFIED` 10쌍의 **육안 판독 근거를 원장에 등재**한다 (2026-08-24).

## 왜 등재하나

`validate_data_contract.py` 가 매 라운드 같은 YELLOW 20줄을 찍는데, 그 20칸은 이미 원문으로
판정이 끝났다. 판정이 게이트에 안 들어가면 ① 같은 줄이 영원히 반복되고 ② 아무도 안 보게 되고
③ 나중에 진짜 미판독 칸이 그 20줄 사이에 섞여 들어와도 눈에 안 띈다. 선례는
`EXEMPTION_VERIFIED_BY_IMAGE_ONLY`(KR0079 2023.2Q) 다 — **조용히 지우는 게 아니라 근거를
적고 매 실행 재검산**한다.

## 무엇을 등재하나 (통째 skip 아님)

주장: "발행사가 경과조치를 적용하지 않았음이 원문에 인쇄돼 있다 → 적용후 = 적용전 이므로
item17후·item19후의 '세부결측(후=전)' 은 결함이 아니다."

게이트가 매 실행 다시 거는 것:
  · **claim 재검산** — 마스터에서 item1·14·15·17·19·27 의 `값` vs `값_적용후` 를 다시 읽어
    하나라도 다르면 `SOURCE_VISION_CLAIM_REFUTED` **RED**. 등재 주장 자체가 깨진 것이다.
  · **값 드리프트** — 박제한 셀 값이 움직이면 `SOURCE_VISION_PIN_DRIFT` YELLOW. 판독은 그때의
    숫자에 대해 한 것이라 다시 봐야 한다(주장은 아직 서 있으므로 차단은 안 한다).
  · **결측** — 박제 셀이 사라지면 `SOURCE_VISION_INPUT_MISSING` **RED**(결측은 SKIP 이 아니다).
  · **필수 필드** — 판독자·판독일·본 페이지·인쇄된 문구가 비면 `SOURCE_VISION_RECORD_INCOMPLETE`
    **RED**. "누군가 확인했다" 는 산문과 같다.
  · **무용해짐** — 등재했는데 그 축이 더 이상 미판독을 내지 않으면 `SOURCE_VISION_INERT` review
    로 "등재를 풀어라" 를 찍는다(죽은 핀 방지).

## 판독 깊이를 항목마다 적는다 — 게이트가 그대로 인쇄한다

10쌍 중 **validation(원 sender)이 직접 재현한 것은 4쌍**이다 — KR0010 2025.3Q · KR0079
2025.1Q · KR0080 2025.1Q · KR0087 2026.1Q, 즉 **등재된 4개 회사 전부에서 한 분기씩**이고
TFI=O · X · UNKNOWN 세 경우를 모두 포함한다. 나머지 6쌍은 parser-kics 의 판독이고, 같은
발행사의 다른 분기를 내가 재현했으므로 `sibling_quarter` 로 구분한다. 깊이를 뭉개면
"검증됐다" 한 단어 아래 서로 다른 강도의 근거가 섞인다 — 이 저장소가 `VERIFIED` 와
`VERIFIED_BY_IMAGE`·`VERIFIED_BY_OWNER` 를 갈라 놓은 것과 같은 이유다.

재현: python scripts/fix_20260824_register_source_vision.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "_gold" / "kics_source_vision_verified.json"
MASTER = ROOT / "kics_disclosure.json"

# 이 축의 주장은 "경과조치 미적용 → 전 항목 적용후=적용전" 이다. 그 주장이 참이면 아래 여섯
# 항목이 **전부** 전==후 여야 한다. 하나만 봐도 되는 것을 여섯 개 거는 이유: 항목 하나가
# 우연히 같을 수는 있어도 헤드라인·요구자본·비율이 동시에 같기는 어렵다(지급여력비율은
# 소수 8자리까지 저장된다).
CLAIM_ITEMS = (1, 14, 15, 17, 19, 27)

_Q_KB = ("* 당사는 자본감소분 경과조치를 적용하지 않아 경과조치 전·후 금액 및 비율이 동일함 "
         "(②장수·사업비·해지·대재해, ③주식위험(또는 금리위험)도 같은 문구). "
         "(1)공통적용 경과조치 표는 TFI 적용(O)이지만 순효과가 0이다 — 지급여력비율 191.19 · "
         "지급여력금액 12,377,040 · 보완자본 7,298,639 · 지급여력기준금액 6,473,686 이 "
         "적용전=적용후로 동일하다(한도 3,236,843 이 구속하지 않는다). "
         "요구자본이 안 움직이므로 item17후·item19후 = 적용전이 원문으로 확정된다. "
         "[2025.3Q 수치, validation 직접 판독]")
_Q_MIRAE = ("* 당사는 경과조치 전·후 금액 및 비율이 동일함 — (1)공통적용 경과조치 표 전 행 "
            "적용전=적용후 동일(지급여력기준금액 1,883,004 백만원), 그리고 '경과조치의 종류' "
            "표의 적용여부 칸이 공통 TFI·선택 TAC/TIR/TER/TIRR·적기시정조치 **전부 X**. "
            "[2025.1Q 수치, validation 직접 판독]")
_Q_AIA = ("당사는 경과조치를 적용하지 않아, 경과조치 전후 금액 및 비율이 동일합니다. "
          "— '경과조치의 종류' 표 적용여부 칸이 전 행 X. [2025.1Q, validation 직접 판독]")
_Q_TONGYANG = ("당사는 자본감소분 경과조치를 적용하지 않아 경과조치 전·후 금액 및 비율이 동일함 "
               "(②장수·사업비·해지·대재해, ③주식위험도 같은 문구). (1)공통적용 경과조치 표는 "
               "전 행 적용전=적용후 동일(지급여력기준금액 2,292,632 백만원 · 지급여력비율 189.6). "
               "[2026.1Q, validation 직접 판독]")

# (code, name, quarter, fy, pages_0idx, pages_printed, quote, read_by, depth, pages_verified)
#
# `pages_0idx` 는 **0-index** 다. parser 답변의 idx 는 2025.3Q 에서 실측과 한 칸 어긋났으므로
# (그쪽이 1-index 였던 것으로 보인다) 내가 직접 연 항목만 `pages_verified_by_sender=True` 다.
_V = "parser-kics 2026-08-24 / validation 2026-08-24 재현"
_P = "parser-kics 2026-08-24"
_P21 = "parser-kics 2026-08-21"
ENTRIES = [
    ("KR0010", "KB손해보험", "2025.3Q", "FY2025_Q3", [16, 17], ["15/26", "16/26"],
     _Q_KB, _V, "yes", True),
    ("KR0010", "KB손해보험", "2026.1Q", "FY2026_Q1", [16, 17, 18], ["17/27", "18/27", "19/27"],
     _Q_KB, _P, "sibling_quarter", False),
    # 2025.1Q 는 2026-08-21 라운드에 parser 가 판독한 최초 1쌍이다(이 티켓 §3 최초 답변).
    ("KR0010", "KB손해보험", "2025.1Q", "FY2025_Q1", [10, 15, 16], ["10/26", "15/26", "16/26"],
     _Q_KB, _P21, "sibling_quarter", False),
    ("KR0079", "미래에셋생명보험", "2025.1Q", "FY2025_Q1", [16, 17], ["17/31", "18/31"],
     _Q_MIRAE, _V, "yes", True),
    ("KR0079", "미래에셋생명보험", "2025.3Q", "FY2025_Q3", [17, 18, 19],
     ["18/35", "19/35", "20/35"], _Q_MIRAE, _P, "sibling_quarter", False),
    ("KR0079", "미래에셋생명보험", "2026.1Q", "FY2026_Q1", [17, 18, 19],
     ["18/32", "19/32", "20/32"], _Q_MIRAE, _P, "sibling_quarter", False),
    ("KR0080", "에이아이에이생명보험", "2025.1Q", "FY2025_Q1", [15, 16], ["16/32", "17/32"],
     _Q_AIA, _V, "yes", True),
    ("KR0080", "에이아이에이생명보험", "2025.3Q", "FY2025_Q3", [15, 16], ["16/33", "17/33"],
     _Q_AIA, _P, "sibling_quarter", False),
    ("KR0080", "에이아이에이생명보험", "2026.1Q", "FY2026_Q1", [16, 17], ["17/36", "18/36"],
     _Q_AIA, _P, "sibling_quarter", False),
    ("KR0087", "동양생명", "2026.1Q", "FY2026_Q1", [16], ["17/32"],
     _Q_TONGYANG, _V, "yes", True),
]


def _pdf_rel(fy: str, code: str) -> str:
    d = ROOT / "data" / "disclosure" / fy / "raw"
    hits = sorted(d.glob(f"{code}_*.pdf"))
    if not hits:
        raise SystemExit(f"raw PDF 를 못 찾았다: {fy} {code}")
    return hits[0].relative_to(ROOT).as_posix()


def main() -> None:
    rows = json.loads(MASTER.read_text(encoding="utf-8"))
    cells: dict[tuple, dict] = {}
    for r in rows:
        try:
            it = int(r.get("항목번호"))
        except (TypeError, ValueError):
            continue
        cells[(r.get("원보험사코드"), r.get("공시분기"), it)] = r

    out = []
    for code, name, q, fy, pages, printed, quote, read_by, depth, pv in ENTRIES:
        pinned = {}
        for it in CLAIM_ITEMS:
            r = cells.get((code, q, it))
            if r is None:
                raise SystemExit(f"{code} {q} item{it} 이 마스터에 없다 — 등재 전제가 깨졌다")
            pre, post = r.get("값"), r.get("값_적용후")
            if str(pre) != str(post):
                raise SystemExit(
                    f"{code} {q} item{it} 이 전({pre}) != 후({post}) 다 — "
                    "'경과조치 미적용' 주장과 어긋난다. 등재하지 않는다.")
            pinned[str(it)] = {"값": pre, "값_적용후": post}
        out.append({
            "company": code,
            "company_name": name,
            "quarter": q,
            "axis": "SOURCE_UNREADABLE_NOT_VERIFIED",
            "items": [17, 19],
            "claim": ("발행사가 경과조치를 적용하지 않았음이 원문에 인쇄돼 있다 → 적용후 = 적용전. "
                      "따라서 item17후·item19후의 '세부결측(후=전)' 은 유실·복사가 아니라 정당하다."),
            "method": "PyMuPDF(fitz) 200~240dpi 렌더링 후 육안 판독",
            "why_not_machine_verifiable": (
                "이 raw PDF 는 텍스트레이어가 깨져 fitz get_text() 가 인용 페이지에서 "
                "0~34자/p 만 돌려준다(문서 전체 평균보다도 낮다). 부분문자열 마커 검사를 걸면 "
                "마커를 절대 못 찾아 '주장 확인' 으로 끝나므로 검사처럼 보이는 무검사가 된다. "
                "래스터 스캔은 아니고 폰트 유니코드 매핑 실패라 렌더링하면 또렷하게 읽힌다."),
            "read_by": read_by,
            "read_date": "2026-08-24",
            "reproduced_by_sender": depth,
            "pdf": _pdf_rel(fy, code),
            "pages_0idx": pages,
            "pages_printed": printed,
            "pages_verified_by_sender": pv,
            "printed_quote": quote,
            "pinned_cells": pinned,
            "machine_corroboration": (
                "육안 판독과 **독립적으로**, 마스터에서 item1·14·15·17·19·27 여섯 항목이 전부 "
                "값 == 값_적용후 다(지급여력비율은 소수 8자리까지 동일). 경과조치가 실제로 "
                "적용됐다면 최소한 지급여력비율이 움직인다 — 여섯 항목이 동시에 같다는 것이 "
                "'미적용' 주장의 기계적 필요조건을 만족한다. "
                "재현: scripts/_probes/probe_20260824_unreadable_pairs_recheck.py"),
            "registered_by": (
                "validation 2026-08-24 (sender 종결, inbox/parser/20260821T0620Z §3). "
                "parser-kics 가 판독했고 원 sender 가 4개 회사 각 1분기씩 독립 재현했다 "
                "(KR0010 2025.3Q · KR0079 2025.1Q · KR0080 2025.1Q · KR0087 2026.1Q)."),
        })

    doc = {
        "_doc": ("K-ICS 원천 육안판독 근거 원장 (source vision-verification ledger). "
                 "validate_data_contract.py 의 SOURCE_UNREADABLE_NOT_VERIFIED 축이 소비한다."),
        "_why": ("텍스트레이어가 깨진 raw 에서 '적용후 세부결측(후=전)' 을 판정 불가로 두면 매 "
                 "라운드 같은 YELLOW 가 반복되고 아무도 안 보게 된다. 그렇다고 조용히 지우면 "
                 "진짜 미판독 칸이 섞여 들어와도 안 보인다. 그래서 **판독 근거를 적고 매 실행 "
                 "재검산**한다 — EXEMPTION_VERIFIED_BY_IMAGE_ONLY(KR0079 2023.2Q) 와 같은 형태다."),
        "_not_a_suppressor": (
            "이 원장은 '이 칸을 보지 마라' 가 아니다. 게이트는 매 실행 ① 등재 주장(전==후)을 "
            "마스터에서 재검산하고(깨지면 SOURCE_VISION_CLAIM_REFUTED RED) ② 박제 셀 값이 "
            "움직였는지 보고(SOURCE_VISION_PIN_DRIFT YELLOW) ③ 결측이면 RED 를 내고 "
            "④ 필수 필드가 비면 RED 를 내며 ⑤ 그 축이 더 이상 미판독을 안 내면 "
            "SOURCE_VISION_INERT review 로 '등재를 풀어라' 를 찍는다."),
        "_required_fields": ["company", "quarter", "claim", "method", "read_by", "read_date",
                             "pdf", "pages_0idx", "printed_quote", "pinned_cells"],
        "_reproduced_by_sender_values": {
            "yes": "원 sender(validation)가 그 (회사,분기) raw 를 직접 렌더링해 재현했다",
            "sibling_quarter": "같은 발행사의 다른 분기를 sender 가 재현했다 — 서식이 같다는 "
                               "추론이 한 겹 들어간다",
            "no": "parser-kics 판독만 있다. 게이트가 매 실행 이 깊이를 그대로 인쇄한다",
        },
        "entries": out,
    }
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    assert LEDGER.read_bytes()[:3] != b"\xef\xbb\xbf", "BOM 이 붙었다"
    print(f"wrote {LEDGER} ({len(out)} entries)")


if __name__ == "__main__":
    main()
