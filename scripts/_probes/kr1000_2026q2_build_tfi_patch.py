"""Build/merge item 47/48(fix)/49/50/51/52(post-fill)/53/54 cells for KR1000 2026.2Q
into the existing data/_derived/_patch_2026q2_KR1000.json (which already carries
items 16-46 from the market-section docling-window-drop recovery).

Source: raw PDF p.11 (== md_inbox/FY2026_Q2/KR1000_*.md lines 367-384), table
"[지급여력비율의 경과조치 적용에 관한 사항] (1) 공통적용 경과조치 관련" (단위: 백만원, %).
Cross-checked byte-for-byte against md_inbox MD (identical digits) and against
raw PDF fitz text extraction (identical digits) -- not a docling-window-drop case,
the table is fully present in both; this is a fill-script gap (47/49/50/51/53/54
were simply never populated for this quarter) plus a mis-mapped item48 (currently
holds the TFI table's own "보완자본" row value, not "보완자본 한도").

Labels are pulled programmatically from the live master's own 2026.1Q KR1000 rows
(same items, same company) to avoid hand-typing Korean look-alike characters.
"""
import json
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "kics_disclosure.json"
PATCH_PATH = ROOT / "data" / "_derived" / "_patch_2026q2_KR1000.json"

master = json.loads(MASTER.read_text(encoding="utf-8"))
labels = {}
for r in master:
    if r.get("원보험사코드") == "KR1000" and r.get("공시분기") == "2026.1Q" and r.get("항목번호") in range(47, 55):
        labels[r["항목번호"]] = r["항목명"]

assert len(labels) == 8, f"expected 8 labels from 2026.1Q, got {labels}"
for i in range(47, 55):
    print(f"label item{i}: {labels[i]!r}")

# raw PDF p.11 / MD lines 373-384, 단위 백만원 -> /100 = 억원
# row: (전, 후 or None)
raw_mn = {
    47: (1_040_518, 711_321),        # 보완자본 한도 적용 전
    48: (1_167_669, 1_167_669),      # 보완자본 한도  <- FIX (master currently holds wrong row's value)
    49: (106_967, 106_967),          # 해약환급금 부족분 상당액 중 해약환급금 상당액 초과분
    50: (3_773_213, 4_102_410),      # 기본자본 (TFI표)
    51: (1_147_485, 818_288),        # 보완자본 (TFI표)
    52: (4_920_698, 4_920_698),      # 지급여력금액 (TFI표) -- only 값_적용후 is missing; 값 left as-is
    53: (329_197, None),             # (기발행 신종자본증권) -- no 후 column printed
    54: (0, None),                   # (기발행 후순위채무) -- printed "-", no 후 column
}


def to_eok_str(mn):
    if mn is None:
        return None
    v = mn / 100
    return str(v)


cells = []
for item in (47, 49, 50, 51, 53, 54):  # brand-new rows
    pre_mn, post_mn = raw_mn[item]
    cell = {
        "항목번호": item,
        "항목명": labels[item],
        "값": to_eok_str(pre_mn),
    }
    if post_mn is not None:
        cell["값_적용후"] = to_eok_str(post_mn)
    cell["근거"] = (
        f"raw PDF p.11(=md_inbox/FY2026_Q2 L373-384) '[지급여력비율의 경과조치 적용에 관한 사항] "
        f"(1) 공통적용 경과조치 관련' 표(단위 백만원) '{labels[item].split('(')[0].strip()}' 행 "
        f"전={pre_mn:,}백만원" + (f" 후={post_mn:,}백만원" if post_mn is not None else " (후 컬럼 공란, 인쇄 없음)")
        + f" -> /100 억원 = {to_eok_str(pre_mn)}"
        + (f" / {to_eok_str(post_mn)}" if post_mn is not None else "")
        + ". fitz 직접추출로 MD와 바이트 단위 동일 확인(docling 누락 아님, fill 스크립트가 이 표 자체를 "
          "이번 분기 대상에서 빠뜨린 갭). 재검산: item51=min(47,48)+49 => "
        + "전 min(10405.18,11676.69)+1069.67=11474.85(일치) / 후 min(7113.21,11676.69)+1069.67=8182.88(일치, "
          "CAPPED 서식·비구속). 같은 표 기본자본/보완자본 적용후는 이미 로드된 헤드라인 item2_적용후=41024.1·"
          "item3_적용후=8182.88 과 정확히 일치(교차검증)."
    )
    cells.append(cell)

# item48 fix (existing wrong row) + item52 gap-fill (existing 값 kept, only 값_적용후 added)
pre_mn, post_mn = raw_mn[48]
cells.append({
    "항목번호": 48,
    "항목명": labels[48],
    "값": to_eok_str(pre_mn),
    "값_적용후": to_eok_str(post_mn),
    "근거": (
        "FIX(오적재 정정): 현재 마스터 item48 값=11475 는 같은 표의 '보완자본' 행(1,147,485백만원/100="
        "11474.85, item51과 동일값)이 잘못 들어간 것이지 '보완자본 한도' 행이 아니다. raw PDF p.11 "
        "'보완자본 한도' 행 전=1,167,669 후=1,167,669백만원 -> 11676.69/11676.69억원. 독립검산: "
        "item48 == item14(적용전,23353) x 50% = 11676.5 (TIER2_LIMIT_RATIO, kics_json_rules.py L216) "
        "-- 11676.69 는 이 앵커와 0.19 차이(반올림), 기존 오적재값 11475 는 1201.5 차이로 이 앵커를 "
        "완전히 벗어난다. 항등식 51_tfi_tier2_composition(item51=min(47,48)+49)도 47/48/49 모두 "
        "정정후에만 닫힌다(오적재 상태로는 min(47,11475)+49=47+49 로 한도가 전혀 안 걸려 다른 회사향 "
        "CAPPED 갈래가 우연히도 성립은 하지만 48_tier2_limit YELLOW 축이 11475 vs 11676.5 로 어긋난다)."
    ),
})

pre_mn, post_mn = raw_mn[52]
cells.append({
    "항목번호": 52,
    "항목명": labels[52],
    "값": None,  # leave existing 값=49207 untouched (already correct, minor 0.02 rounding vs table's 49206.98)
    "값_적용후": to_eok_str(post_mn),
    "근거": (
        "GAP-FILL(적용후만 결측): 마스터 item52 값=49207 는 이미 정확(raw p.11 '지급여력금액' 전=4,920,698"
        "백만원/100=49206.98, 반올림 49207 -- 4-2-3표(억원 단위) 헤드라인 49,207 과도 일치). 값_적용후만 "
        "결측이었다. raw p.11 같은 행 후=4,920,698백만원(전과 동일 인쇄, TFI 는 총액을 안 바꾸고 재분류만 "
        "한다) -> 49206.98. 검산: item50_후+item51_후 = 41024.1+8182.88 = 49206.98, 정확 일치."
    ),
})

new_item_nums = {c["항목번호"] for c in cells}
existing = json.loads(PATCH_PATH.read_text(encoding="utf-8"))
existing_item_nums = {c["항목번호"] for c in existing["cells"]}
overlap = new_item_nums & existing_item_nums
assert not overlap, f"overlap with existing patch cells: {overlap}"

existing["cells"].extend(cells)
existing["notes"] = (
    existing["notes"]
    + " || [2차 추가, TFI 경과조치표 47/49/50/51/53/54 신규 + 48 오적재정정 + 52 적용후 결측충전] "
    "이 6항목은 docling 누락이 아니라(raw PDF p.11 텍스트가 MD 에 온전히 남아있음, 6-4시장위험 절과 "
    "다른 실패양식) fill 스크립트가 이 분기 이 회사에 대해 TFI 공통적용경과조치 표 자체를 아예 안 읽은 "
    "갭이다(다른 회사들의 47-54 는 과거 세션 vision/textread 백필 스크립트가 개별 처리했는데 2026.2Q "
    "온보딩엔 그 패스가 없었다). item48 은 부수적으로 발견한 오적재(같은 표의 다른 행 값이 들어가 "
    "있었음) 라 같이 정정한다 -- item47/49/50/51 을 새로 넣으면서 51_tfi_tier2_composition 항등식이 "
    "열리는데 item48 이 틀린 채면 그 항등식도 48_tier2_limit YELLOW 축도 새 RED/YELLOW 를 만들기 때문에 "
    "같은 표 안에서 분리해 넣을 수 없다."
)

PATCH_PATH.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"\nmerged. total cells now: {len(existing['cells'])}")
print(f"new items added: {sorted(new_item_nums)}")
