# -*- coding: utf-8 -*-
"""TODO_publishing.md Status (latest 3, oldest verbatim to the archive) + docs/changelog_publishing.md entry. usage: s18_docs.py <commitA-hash>"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
H = sys.argv[1]


def rd(p):
    b = (ROOT / p).read_bytes().decode("utf-8")
    crlf = "\r\n" in b
    return b.replace("\r\n", "\n"), crlf


def wr(p, t, crlf):
    if crlf:
        t = t.replace("\n", "\r\n")
    (ROOT / p).write_bytes(t.encode("utf-8"))


# ---- TODO_publishing.md
t, crlf = rd("TODO_publishing.md")
lines = t.split("\n")
start = next(i for i, l in enumerate(lines) if l.startswith("## Status"))
end = next(i for i, l in enumerate(lines) if l.startswith("## 열린 일"))
body = lines[start + 1:end]
# bullets: a bullet = line starting with "- **" plus following lines until the next blank-line-separated bullet
blocks, cur = [], []
for l in body:
    if l.startswith("- **") and cur:
        blocks.append(cur)
        cur = []
    cur.append(l)
blocks.append(cur)
blocks = [b for b in blocks if any(x.strip() for x in b)]
strip = lambda b: [x for x in b]
new_bullet = [
    f"- **2026-10-13 독립 감사 티켓 `20261012T2235Z` 요청 1·2·3 + owner 결정 8(커밋 `{H}` · push 보류)** — ① DB손보 제1·2회 콜일 원문 상충(FY2025 둘 다 09-01 / 2026 1Q·반기 09-25·09-01): 타임라인 잔액 null 로 날짜만 표시 + 공개 시트 콜일 비움 ② 하나손해 원장에 2026-06-29 추정 행(999억, 금리·콜일 없음, `estimated`) ③ 기본자본 인쇄 한도: 결속 갈래 없는 33사 15% -> 10%(소진율 47사 불변) ④ 보완자본 분자의 기발행 차감 = 원장 2022-12-31 이전 잔액(47사 공통, 21사 변동: 메리츠 0.2 -> 30.8 · 흥국생명 10.6 -> 37.0 · 한화생명 70.5 -> 74.8 · 푸본 86.6 -> 73.1 · 농협생명 18.8 -> 4.8).",
    "  남은 것: ① owner: 농협생명 4.8(원장 2022년 이전 후순위 11,100 대 인쇄 8,700 - 원장 상환 반영 여부)·아이엠라이프 56.9(원장에 전환우선주 없음, 기준일 2025-12-31) 확인 ② designer: 티켓 `20261013T0030Z`(DB손보 셀 눈 확인, 하나손해 추정 툴팁) ③ 증빙 `data/_derived/capsec_reinstate_20261012/z3·z4·z6·y1`.",
    "",
]
# keep the first two existing bullets + the new one on top; the oldest (3rd) goes to the archive
kept = blocks[:2]
dropped = blocks[2:]
newbody = [""] + new_bullet
for b in kept:
    newbody += b if (b and b[-1] == "") else b + [""]
lines2 = lines[:start + 1] + newbody + lines[end:]
t2 = "\n".join(lines2)
t2 = t2.replace("> 갱신 2026-10-12 ·", "> 갱신 2026-10-13 ·", 1)
wr("TODO_publishing.md", t2, crlf)
print("TODO moved to archive:", sum(len(b) for b in dropped), "lines")

a, acrlf = rd("docs/todo_archive_publishing.md")
al = a.split("\n")
ins = []
for b in dropped:
    ins += b if (b and b[-1] == "") else b + [""]
# insert right under the title (line 0) + blank line (line 1)
al2 = al[:2] + ins + al[2:]
wr("docs/todo_archive_publishing.md", "\n".join(al2), acrlf)

# ---- changelog
c, ccrlf = rd("docs/changelog_publishing.md")
entry = f"""## 2026-10-13 — 독립 감사 티켓 `20261012T2235Z` 요청 1·2·3 + owner 결정 8: 콜일 상충 · 하나손해 추정 행 · 기본자본 인쇄 한도 · 보완자본 기발행 차감 (커밋 `{H}` + 공개본 커밋, 커밋만 · push 보류)

- **요청 1 (DB손해보험 제1·2회 콜일).** 원 공시 전수 대조(`y1_db_call_dates_all_filings.txt`): FY2025 3Q·사업보고서는 두 회차 모두 2030년 9월 1일, FY2026 1Q·반기보고서는 제1회 9월 25일·제2회 9월 1일, 발행일+5년이면 제1회 09-01·제2회 09-25 - 발행사 문서끼리 어긋나 확정 불가.
  바뀐 필드: `data/bonds/capital_securities_fy2026h1.json` KR0011 두 건 `call_source` disclosed -> `conflicting_filings`, 신규 `call_date_unconfirmed`·`call_date_candidates`·`call_date_note` (`call_date` 는 forward 가 연 단위로 읽어 그대로).
  `kics_capital_securities_timeline.json` 두 건: `outstanding_eok` 7,470/1,200 -> **null** + `call_date_unconfirmed: true`(커밋된 K-ICS.html `75234ddf` 가 잔액 null 인 콜 후보는 날짜만 그리므로 셀이 「콜 상환 도래일 : 2030-09-01」 만 보인다). 공개 시트 `자본성증권발행현황` 두 행: 콜만기도래일 비움, 콜근거 「공시 원문 상충(콜일 미확정)」. 검사기 `CAPTL_FIELDS`·잔액 null 허용(표지와 함께일 때만).
- **요청 2 (하나손해 원장).** 선택: 추정 행(`estimated`) - 「원장 미갱신」 표식은 HTML 이 필요해 제외. KR0050 에 2026-06-29 발행·999억(항목 6 +999)·금리/콜/만기 null 한 건 추가(회사 합계 199,900백만), 등재부 2026.2Q 항목의 `issue_date` 를 2026-06-29 로 맞춤. 결과: 신종 발행잔액 1,000 -> 1,999억(`hybrid_outstanding_eok`), 총발행액·2026 막대 반영, 최근 발행금리는 「—」. forward: 콜일이 없어 이벤트가 안 생기므로 투영 전 항목 동일(KR0050 행의 `confidence` 만 갱신: 기본자본 격차 -50% -> 0%), 나머지 46행 불변.
- **요청 3 (기본자본 인쇄 한도).** `capital_utilization_rules.tier1_binding`: 결속 갈래 없음(기발행 0·기본자본형 신규 0)이면 `binding_limit_eok` = SCR x 10%(예전 15%). 33사 `tier1_hybrid_limit_eok` 변경(한화생명 22,517 -> 15,011 · 하나손해 702 -> 468), `utilization_pct` 47사 전부 불변(`z4_tier1_limit_before_after_47.csv`). 공개 시트 `기본자본소진율` 은 이 필드를 읽지 않아 셀 변동 0. 시험: 독립 사례 + 47사 배포본(결속 갈래별 한도) 단정 신설.
- **요청 8 (owner 최종 규칙 2026-10-12 밤).** 보완자본 분자의 기발행 차감액 = 채권원장의 2022-12-31 이전 발행 잔액(신종·후순위 각각), 인쇄 항목 53/54 는 `grandfathered_*_printed_eok` 로만 보존(맹목 min·증거 판정·회사별 예외 없음). 분자 = 항목 47(적용 전) - 항목 49 - 원장 신종 - 원장 후순위, R0~R5 이름은 발행사 인쇄 관행 표지로 유지(DB생명·미래에셋 특례 흡수, 숫자 불변·이름 R3). 21사 변동(`z3_tier2_before_after_47.csv`): 메리츠 0.2 -> 30.8 · 흥국생명 10.6 -> 37.0 · 한화생명 70.5 -> 74.8 · 푸본 86.6 -> 73.1 · 농협생명 18.8 -> 4.8 · 아이엠라이프 49.5 -> 56.9 · 현대해상 70.5 -> 64.2 · DB손해 38.9 -> 36.0 · 롯데 53.5 -> 50.1 · 농협손해 103.9 -> 102.8 · 악사/KB라이프 -> 0.0 외. 화면 필드: `grandfathered_subordinated_eok`(K-ICS.html 「경과조치 기발행 후순위 X억원」)가 차감액(원장)을 싣는다 - HTML 변경 불필요. tier1·forward 값 불변.
  보고 전용(변경 없음): 15% 갈래 항목 53 인쇄값이 원장 2022년 이전 신종보다 큰 회사는 아이엠라이프 1곳(+1,517 = 원장 밖 전환우선주, 등재부엔 있음)뿐, 나머지 10곳은 인쇄 <= 원장(`z6_item53_vs_ledger_report_only.txt`).
- **재동기화.** `insurequant_master_tables.xlsx` 시트 4개(`보완자본소진율` 178행 교체 · `자본성증권발행현황` 4칸+1행 · `자본비율전망` 55칸 · `기본자본소진율` 0)를 `sync_master_xlsx_sheet.py` 로 시트별 반영, `보완자본소진율` 비고/`경과조치 인정 후순위·신종(레거시)` 비고에 원장 기준을 적음. 증빙 패널 `x1_panel`·`x2` 는 parser 의 최신 전기 칸 반영(`74a415bf`)으로 낡아 재생성(판정 불변). 공개본 `public_exports/` 재생성 커밋 별도.
"""
marker = "---\n\n"
i = c.index(marker) + len(marker)
c2 = c[:i] + entry + "\n" + c[i:]
c2 = c2.replace("> Last updated: 2026-10-12", "> Last updated: 2026-10-13", 1)
wr("docs/changelog_publishing.md", c2, ccrlf)
print("ok")
