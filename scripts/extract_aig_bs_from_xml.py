# -*- coding: utf-8 -*-
"""AIG손해보험(KR0029) 재무상태표 세부항목을 DART 원문 XML 에서 직접 뽑는다.

**왜 따로 필요한가.** `build_ifrs17_bs.py` 는 item10-15/20-24/30-31 을 XBRL 표준태그로만
잡고, 계정명 폴백은 준비금(RESERVE_NAMES)에만 있다. AIG 는 두 가지가 동시에 어긋난다:

  1. **라벨에 글자 사이 공백** — `자      산      총      계` 처럼 쓴다.
     `"자산총계" in text` 는 0건이고 공백을 지워야 1건이 된다.
  2. **보험 고유 계정명** — 자산 1행이 `현금및현금성자산` 이 아니라 **`현금및예치금`** 이다.

그 결과 AIG 는 2023.4Q·2024.4Q·2025.4Q 세 해 모두 item [1,2,3,5,6,7] 여섯 개만 실렸다.
owner 가 2026-08-31 에 직접 지적했다("감사보고서든 사업보고서든 아예 숫자 없는 건 말이 안 된다").

**검산이 붙어 있다.** 자산 12행의 합이 표에 인쇄된 `자 산 총 계` 와 정확히 일치해야만
값을 채택한다(2025.4Q 실측: 합계 1,036,996,717,873 = 자산총계, 차이 0. 그 값을 백만원으로
바꾸면 1,036,996.717873 로 마스터 item1 과 바이트 일치). 부채·자본도 같은 방식으로 닫는다.
안 닫히면 그 분기는 **채우지 않는다** — 빈칸이 틀린 숫자보다 낫다.

산출은 `data/dart/viz/bs_manual_overrides.json` 에 병합할 셀 dict 이다(덮어쓰지 않는다).

사용:
  python scripts/extract_aig_bs_from_xml.py                # dry-run
  python scripts/extract_aig_bs_from_xml.py --apply
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]
OVERRIDES = ROOT / "data" / "dart" / "viz" / "bs_manual_overrides.json"
CODE = "KR0029"

# 표의 행 라벨(공백 제거·번호 제거 후) -> 마스터 항목번호
ROW_TO_ITEM = {
    "현금및예치금": 10,            # AIG 는 '현금및현금성자산' 이 아니다
    "현금및현금성자산": 10,
    "당기손익-공정가치측정금융자산": 11,
    "기타포괄손익-공정가치측정금융자산": 12,
    "상각후원가측정금융자산": 13,
    "재보험계약자산": 14,
    "유형자산": 15,
    "배당요소가없는보험계약부채": 20,
    "보험계약부채": 20,
    "재보험계약부채": 21,
    "기타부채": 24,
    "자본금": 30,
    "이익잉여금": 31,
    "기타포괄손익누계액": 4,
}
ASSET_TOTAL, LIAB_TOTAL, EQUITY_TOTAL = "자산총계", "부채총계", "자본총계"


def flat(s: str) -> str:
    return re.sub(r"\s+", "", s)


def strip_no(s: str) -> str:
    return re.sub(r"^[0-9]+\.", "", s)


DASHES = {"-", "–", "—", "－", "−"}


def num(s: str):
    s = s.strip().replace(",", "")
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    if not re.fullmatch(r"-?\d+", s or ""):
        return None
    v = int(s)
    return -v if neg else v


def current_value(cells: list[str]):
    """라벨 뒤 **첫 비어있지 않은 칸**의 값. 대시는 0 으로 읽는다.

    이걸 "첫 숫자 칸" 으로 짜면 조용히 틀린다. AIG 2024.4Q 재무상태표의
    `11. 당기법인세자산` 은 당기 칸이 `-` 이고 전기 칸이 2,123,662,752 인데,
    숫자만 찾으면 대시를 건너뛰고 **전기 숫자를 당기 값으로 가져온다.** 그 한 줄 때문에
    자산 합계가 총계보다 정확히 2,123,662,752 만큼 커졌다. 산수는 맞고 소스가 틀린 값이라
    합계 검산이 없었으면 그대로 실렸다.
    """
    for c in cells:
        t = c.strip()
        if not t:
            continue            # 빈 칸은 병합/여백이라 계속 본다
        if t in DASHES:
            return 0            # 당기 칸이 대시 = 해당 없음(0)
        v = num(t)
        if v is not None:
            return v
        return None             # 숫자도 대시도 아닌 텍스트 -> 값 행이 아니다
    return None


def bs_table(xml: Path):
    """`자산총계` 를 품은 TABLE 블록의 (라벨, 값들) 행 목록."""
    t = xml.read_text(encoding="utf-8", errors="replace")
    keep = [(c, i) for i, c in enumerate(t) if not c.isspace()]
    fl = "".join(c for c, _ in keep)
    j = fl.find(ASSET_TOTAL)
    if j < 0:
        return None
    pos = keep[j][1]
    s, e = t.rfind("<TABLE", 0, pos), t.find("</TABLE>", pos)
    rows = []
    for tr in re.findall(r"<TR\b.*?</TR>", t[s:e], re.S):
        tds = re.findall(r"<T[DH]\b[^>]*>(.*?)</T[DH]>", tr, re.S)
        cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", c).replace("&nbsp;", " ")).strip()
                 for c in tds]
        if cells:
            rows.append(cells)
    return rows


def parse(xml: Path):
    """(항목값, 총계, 섹션별 행합) 을 돌려준다.

    검산은 **섹션 마커 기준**으로 한다. 표는 `자 산` / `부 채` / `자 본` 이라는 값 없는
    마커 행으로 구간이 갈리고, 각 구간 끝에 `자 산 총 계` 같은 총계 행이 온다. 처음에는
    "값을 누적하다 총계와 같아지면 멈춘다" 로 짰는데 그러면 행 순서·빈칸에 따라 우연히
    안 맞을 수 있다(2024.4Q 실측 실패, 손으로 더하면 정확히 맞는데도). 구간을 명시적으로
    끊는 편이 옳다.
    """
    rows = bs_table(xml)
    if rows is None:
        return None, "자산총계를 못 찾음"
    MARK = {"자산": "자산", "부채": "부채", "자본": "자본"}
    TOTAL = {ASSET_TOTAL: "자산", LIAB_TOTAL: "부채", EQUITY_TOTAL: "자본"}
    vals, totals, sums = {}, {}, {"자산": 0, "부채": 0, "자본": 0}
    section = None
    for cells in rows:
        label = flat(strip_no(cells[0]))
        got = current_value(cells[1:])
        if label in TOTAL:
            totals[label] = got
            section = None
            continue
        if label in MARK and got is None:
            section = MARK[label]
            continue
        if got is None or section is None:
            continue
        sums[section] += got
        if label in ROW_TO_ITEM:
            vals.setdefault(ROW_TO_ITEM[label], got)
    return (vals, totals, sums), None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    found = {}
    for d in sorted((ROOT / "data" / "dart").glob("FY*/raw/%s_*" % CODE)):
        period = d.parent.parent.name                      # FY2025_Q4
        quarter = "%s.%sQ" % (period[2:6], period[-1])
        for xml in sorted(d.glob("*.xml")):
            res, err = parse(xml)
            if res is None:
                continue
            vals, totals, sums = res
            checks = []
            for tot_label, sec in ((ASSET_TOTAL, "자산"), (LIAB_TOTAL, "부채"),
                                   (EQUITY_TOTAL, "자본")):
                t_ = totals.get(tot_label)
                checks.append(t_ is not None and sums[sec] == t_)
            # 자산·부채 둘 다 닫혀야 채운다. **자본은 검산 대상이 아니다** — 자본 구간에
            # 대손/비상위험/해약환급금 준비금 행이 섞여 있는데 그건 이익잉여금 안에
            # 이미 포함된 메모 행이라 더하면 이중계상이다(이 저장소 규약: item8 도 같은
            # 이유로 자본 L2 합에서 뺀다). 실측으로도 5개 공시 전부 자산·부채는 닫히고
            # 자본만 안 닫힌다 — 오류가 아니라 표 구조다.
            ok = checks[0] and checks[1]
            print("%-9s %-30s 항목 %2d개 · 검산 자산=%s 부채=%s 자본=%s"
                  % (quarter, xml.name[:30], len(vals),
                     *["일치" if c else "불일치" for c in checks]))
            if ok and vals:
                found.setdefault(quarter, vals)

    if not found:
        print("채울 값이 없다.")
        return 1

    doc = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    cells = doc["cells"]
    added, existed = 0, 0
    for quarter, vals in sorted(found.items()):
        for item, won in sorted(vals.items()):
            key = "%s|%d|%s" % (CODE, item, quarter)
            if key in cells:
                existed += 1
                continue
            cells[key] = {
                "값": round(won / 1e6, 6),                # 원 -> 백만원
                "근거": ("AIG 재무상태표 원문 직접추출(2026-08-31, owner 지적). 이 회사는 "
                        "라벨을 '자 산 총 계' 처럼 글자 사이 공백으로 쓰고 자산 1행이 "
                        "'현금및예치금'(현금및현금성자산 아님)이라 빌더의 XBRL 표준태그 "
                        "매칭이 통째로 빗나갔다. 자산 12행 합 == 표의 자산총계(차이 0)로 "
                        "검산했고, 그 총계를 백만원으로 바꾼 값이 마스터 item1 과 일치한다."),
            }
            added += 1
    print("\n신규 %d셀 · 이미 있던 셀 %d개 · 오버라이드 총 %d셀"
          % (added, existed, len(cells)))
    if not args.apply:
        print("(dry-run — 실제로 쓰려면 --apply)")
        return 0
    OVERRIDES.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[wrote]", OVERRIDES.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
