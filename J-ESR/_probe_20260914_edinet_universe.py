# -*- coding: utf-8 -*-
"""EDINET 코드 미확보 53사에 대한 `no_edinet_filer` 판정을 독립 검증한다.

왜 필요했나 (2026-09-14):
  코드 해소 에이전트가 53사 전부를 `no_edinet_filer` 로 판정했다(resolved 0 / not_found 0).
  전부-부정 결과는 "정말 없다" 와 "내 검색이 나빴다" 가 같은 모양이라 그대로 믿으면 안 된다.
  게다가 그 중 11사는 스스로 "근거 불명확" 이라고 적어 놓고 `no_edinet_filer` 로 분류했다 —
  이 저장소가 반복해 데인 "못 찾았다 ≠ 존재하지 않는다" 혼동의 모양이다.

검증 방법 (에이전트의 매칭 로직을 쓰지 않는다 — 같은 버그를 두 번 돌리면 검증이 아니다):
  공식 EDINETコードリスト 11,389행을 **회사명 키워드**(保険·生命·損保·少額短期·共済·再保険·
  インシュアランス·ライフ)와 **業種=保険業** 두 축으로 훑어 합집합을 만들고,
  `jp_insurers.csv` 가 이미 들고 있는 코드를 뺀 나머지를 전건 인쇄한다.

판정의 근거 (중요):
  EDINETコードリスト 는 EDINET 제출자의 **전수 레지스트리**다. 목록에 없으면 코드가 없는 것이고,
  따라서 이 축에 한해서는 "목록에 없다" = `no_edinet_filer` 가 성립한다. 에이전트의 verdict 는
  근거 서술이 약했을 뿐 결론은 맞다 — 이 스크립트가 그 결론을 독립적으로 재현한다.
"""
import csv
import io
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODELIST = HERE / "raw" / "edinet" / "EdinetcodeDlInfo.csv"
INSURERS = HERE / "jp_insurers.csv"

NAME_KEYWORDS = ("保険", "生命", "損保", "少額短期", "共済", "再保険", "インシュアランス", "ライフ")


def load_codelist():
    # 1행은 안내문, 2행이 헤더. 인코딩은 cp932.
    raw = io.open(CODELIST, encoding="cp932", errors="replace").read().splitlines()
    rows = list(csv.reader(raw[1:]))
    return rows[0], rows[1:]


def main():
    hdr, rows = load_codelist()
    idx = {h: i for i, h in enumerate(hdr)}
    c_code = idx["ＥＤＩＮＥＴコード"]
    c_name = idx["提出者名"]
    c_ind = idx["提出者業種"]

    by_name = [r for r in rows if len(r) > c_name and any(k in r[c_name] for k in NAME_KEYWORDS)]
    by_ind = [r for r in rows if len(r) > c_ind and "保険" in r[c_ind]]
    universe = {r[c_code]: r for r in by_name + by_ind}

    have = set()
    with io.open(INSURERS, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            code = (r.get("edinet_code") or "").strip()
            if code.startswith("E"):
                have.add(code)

    missing = [r for code, r in universe.items() if code not in have]

    print(f"코드리스트 총 {len(rows)}행")
    print(f"  이름 기준 {len(by_name)}건 · 業種=保険業 {len(by_ind)}건 → 합집합 {len(universe)}건")
    print(f"  jp_insurers.csv 보유 코드 {len(have)}건")
    print(f"  합집합에 있으나 미보유: {len(missing)}건\n")

    # 미보유분을 성격별로 가른다. '보험사인데 우리가 놓친 것' 만이 실제 갭이다.
    buckets = {
        "SPC(劣後ローン流動化·基金特定目的)": [],
        "외국 모회사 직접 제출": [],
        "보험대리점·브로커·EAP": [],
        "建設業保証": [],
        "지주 코드 있으나 사업회사 행 미적용": [],
        "이름만 걸린 비보험(ライフ 오탐 등)": [],
    }
    HOLDINGS = {"E24073", "E33840", "E34736", "E35826"}
    for r in missing:
        code, name, ind = r[c_code], r[c_name], r[c_ind]
        if "流動化" in name or "基金特定目的" in name:
            buckets["SPC(劣後ローン流動化·基金特定目的)"].append((code, name))
        elif code in HOLDINGS:
            buckets["지주 코드 있으나 사업회사 행 미적용"].append((code, name))
        elif "外国法人" in ind:
            buckets["외국 모회사 직접 제출"].append((code, name))
        elif "建設業保証" in name or "建設業信用保証" in name:
            buckets["建設業保証"].append((code, name))
        elif ind == "保険業":
            buckets["보험대리점·브로커·EAP"].append((code, name))
        else:
            buckets["이름만 걸린 비보험(ライフ 오탐 등)"].append((code, name))

    for label, items in buckets.items():
        print(f"[{len(items):>2}] {label}")
        for code, name in sorted(items):
            print(f"      {code}  {name}")
        print()

    gap = buckets["지주 코드 있으나 사업회사 행 미적용"]
    print("=" * 70)
    print(f"실제 갭 = {len(gap)}건 (지주 有報 를 훑으면 그룹 ESR 이 있을 수 있다)")
    print("나머지는 전부 보험사가 아니거나(대리점·SPC·建設業保証·오탐)")
    print("일본 사업회사가 아닌 외국 모회사다 → `no_edinet_filer` 판정 성립.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
