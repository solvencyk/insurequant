# -*- coding: utf-8 -*-
"""Merge KR0005 (items 47-54, incl. item48 correction) and KR0075 (items 50-51)
TFI cells into the existing 2026.2Q patch files. Does NOT touch the live master.

KR0005: labels byte-copied from this company's own 2026.1Q rows (live master) --
never retyped by hand, per the U+318D-vs-U+00B7 lookalike trap.
KR0075: labels byte-copied from the sibling item50/51 rows already present in
this company's 2026.1Q rows (same source convention).
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(r"C:\Users\sangwook.cho\Desktop\insurequant")
MASTER = ROOT / "kics_disclosure.json"

data = json.loads(MASTER.read_text(encoding="utf-8"))


def label_1q(code: str, item: int) -> str:
    row = next(r for r in data
               if r.get("원보험사코드") == code and r.get("공시분기") == "2026.1Q"
               and r.get("항목번호") == item)
    return row["항목명"]


# ---------------------------------------------------------------------------
# KR0005 -- raw source: data/disclosure/FY2026_Q2/pdf/KR0005_흥국화재.pdf p17
# (fitz-confirmed page; md_inbox/FY2026_Q2/KR0005_흥국화재.md L405-422),
# table "[지급여력비율의 경과조치 적용에 관한 사항] (1) 공통적용 경과조치 관련"
# (단위: 백만원,%) -> /100 for 억원. Raw printed rows (전/후):
#   지급여력비율(%)        157.56 / 157.56
#   지급여력금액          3,569,265 / 3,569,265   (already in live as item52=35693)
#   기본자본               631,302 /   843,302   -> item50
#   보완자본             2,937,963 / 2,725,963   -> item51
#   보완자본 한도 적용 전    743,932 /   512,875   -> item47
#   보완자본 한도        1,132,703 / 1,132,703   -> item48
#   해약환급금 부족분 상당액 중 해약환급금 상당액 초과분
#                       2,194,032 / 2,194,032   -> item49
#   (기발행 신종자본증권)    212,000 /  (blank)    -> item53
#   (기발행 후순위채무)       19,057 /  (blank)    -> item54
#   지급여력기준금액      2,265,405 / 2,265,405
#
# item53_후/item54_후 blanks verified NOT a docling drop: fitz word-level dump
# of PDF p17 (scripts/_probes/probe_kr0005_pdf_page.py run this session) shows
# each memo row is only 2 label words with zero numeric word tokens following
# in that row's block -- the PDF itself prints one column only for these two
# memo rows. Left absent (None), not filled.
#
# item48 correction: LIVE master currently holds item48=29380 (no 값_적용후).
# 29380 == item3(헤드라인 보완자본, raw md L379, 단위 억원, 당분기)=29,380 exactly
# -- the same "보완자본 한도" mislabeled-as-"보완자본" copy bug confirmed on 7
# other 2026.2Q onboardings (inbox 20260831T0705Z). Independent check:
# item48 == item14_적용전 x 50%: item14_전(live)=22654 (억원) x 0.5 = 11327,
# vs raw TFI table's own "보완자본 한도" row 1,132,703백만원/100 = 11327.03 --
# matches (diff 0.03, rounding only). 11327.03 is correct; 29380 is not.
#
# TFI type: axis-B/_tier2_branch replicated by hand (EXCL scope, target=item3):
#   debt=item47_전=7439.32, min(debt,item48)=7439.32 (debt<limit already),
#   +item49_전=21940.32 -> 29379.64 vs item3=29380 (diff 0.36, matches).
#   uncapped test |29380-7439.32|=21940.68 (fails). -> branch=CAPPED.
# axis-F cross-check (target=item51, same-table, tighter): min(7439.32,11327.03)
#   +21940.32=29379.64 vs item51_전=29379.63 (diff 0.01, near-exact).
# POST column does not need to close this formula (code: axis-F post branch is
# YELLOW-only on a non-reconciling formula, never RED -- kics_json_rules.py
# _validate_tfi_tier_rows L1663-1678 "적용후는 YELLOW다").
# -> KR0005 = CAPPED type (EXCL scope).
KR0005_CELLS = [
    (47, 7439.32, 5128.75,
     "PDF p17(fitz-confirmed) / md_inbox/FY2026_Q2/KR0005_흥국화재.md L417 "
     "'[지급여력비율의 경과조치 적용에 관한 사항] (1) 공통적용 경과조치 관련' 표(단위 백만원,%): "
     "보완자본 한도 적용 전 743,932/512,875 (/100 -> 억원) = 7439.32/5128.75. "
     "TFI 유형 판정(축 B, EXCL scope, target=item3=29380): debt=item47_전=7439.32<item48_전"
     "(11327.03)이라 min이 그대로 47을 반환, +item49_전(21940.32)=29379.64 (item3=29380과 "
     "diff 0.36) -> branch=CAPPED. uncapped 시험 |29380-7439.32|=21940.68 로 실패, capped만 "
     "성립 확정."),
    (48, 11327.03, 11327.03,
     "PDF p17(fitz-confirmed) / md L418 같은 표: 보완자본 한도 1,132,703/1,132,703 (전=후, "
     "표 자체가 두 컬럼 동일하게 인쇄) /100 -> 11327.03/11327.03. **기존 라이브 값 29380 "
     "정정** -- 29380은 item3(헤드라인 보완자본, md L379 '[경과조치 적용 전 지급여력비율 세부]' "
     "표, 단위 억원, 당분기)=29,380 을 그대로 복사한 오염값(2026.2Q 온보딩 라벨매칭 버그, "
     "inbox 20260831T0705Z 가 이미 확인한 7사 KR0050/KR0095/KR0002/KR0074/KR0049/KR0075/"
     "KR0008 과 동일 패턴 -- KR0005 는 8번째 케이스). 독립검산(축 D, item48==item14_적용전x50%): "
     "item14_전(live)=22654 x 0.5 = 11327, raw 11327.03 과 diff 0.03(반올림) 로 일치 -- "
     "11327.03이 정답, 29380은 오염값임을 재확인."),
    (49, 21940.32, 21940.32,
     "PDF p17(fitz-confirmed) / md L419 같은 표: 해약환급금 부족분 상당액 중 해약환급금 상당액 "
     "초과분 2,194,032/2,194,032 (전=후) /100 -> 21940.32/21940.32."),
    (50, 6313.02, 8433.02,
     "PDF p17(fitz-confirmed) / md L415 같은 표: 기본자본 631,302/843,302 (전/후) /100 -> "
     "6313.02/8433.02. 축 E 검산(같은 표 item52=35693): item50+item51 전=6313.02+29379.63="
     "35692.65, 후=8433.02+27259.63=35692.65 -- 둘 다 item52(35693)와 diff 0.35(반올림 범위)."),
    (51, 29379.63, 27259.63,
     "PDF p17(fitz-confirmed) / md L416 같은 표: 보완자본 2,937,963/2,725,963 (전/후) /100 -> "
     "29379.63/27259.63. 축 F(51_tfi_tier2_composition, target=item51 자신, EXCL scope) 적용전: "
     "min(item47_전=7439.32,item48_전=11327.03)+item49_전(21940.32)=29379.64, diff 0.01(근접 "
     "일치) -> branch=CAPPED, 축 B 와 일치. 적용후는 min(5128.75,11327.03)+21940.32=27069.07 "
     "vs item51_후=27259.63 (diff 190.56, 미확립/YELLOW 대상 -- kics_json_rules.py L1663-1678 "
     "문서화된 대로 축 F 적용후는 이 잔차를 RED 아닌 YELLOW로 처리, 강제 아님). 항등식을 억지로 "
     "닫으려 값을 조정하지 않고 원문 그대로 실었다."),
    (53, 2120.0, None,
     "PDF p17(fitz-confirmed) / md L420 같은 표: (기발행 신종자본증권) 212,000/(공백) /100 -> "
     "2120.0/(결측). 값_적용후 공백은 docling 유실이 아님 -- fitz word-level dump(해당 세션 "
     "probe_kr0005_pdf_page.py, PDF p17 words) 로 그 행의 블록에 라벨 토큰 2개("
     "'(기발행'/'신종자본증권)')만 있고 숫자 토큰이 하나도 없음을 확인 -- 원문 자체가 "
     "적용후 컬럼을 인쇄하지 않는다. 값이 정말 없어 채우지 않음(추측/보간 금지 원칙)."),
    (54, 190.57, None,
     "PDF p17(fitz-confirmed) / md L421 같은 표: (기발행 후순위채무) 19,057/(공백) /100 -> "
     "190.57/(결측). 값_적용후 공백은 docling 유실이 아님 -- fitz word-level dump(해당 세션 "
     "probe_kr0005_pdf_page.py, PDF p17 words) 로 그 행의 블록에 라벨 토큰 2개("
     "'(기발행'/'후순위채무)')만 있고 숫자 토큰이 하나도 없음을 확인 -- 원문 자체가 적용후 "
     "컬럼을 인쇄하지 않는다. 값이 정말 없어 채우지 않음(추측/보간 금지 원칙)."),
]

kr0005_new_cells = []
for item, v_pre, v_post, reason in KR0005_CELLS:
    kr0005_new_cells.append({
        "항목번호": item,
        "항목명": label_1q("KR0005", item),
        "값": v_pre,
        "값_적용후": v_post,
        "근거": reason,
    })
    print(f"KR0005 item{item} 항목명={label_1q('KR0005', item)!r} 값={v_pre} 값_적용후={v_post}")

kr0005_patch_path = ROOT / "data" / "_derived" / "_patch_2026q2_KR0005.json"
kr0005_patch = json.loads(kr0005_patch_path.read_text(encoding="utf-8"))
existing_items = {c["항목번호"] for c in kr0005_patch["cells"]}
overlap = existing_items & {c["항목번호"] for c in kr0005_new_cells}
if overlap:
    raise SystemExit(f"ABORT: KR0005 patch already has items {overlap} -- would collide")
kr0005_patch["cells"].extend(kr0005_new_cells)
kr0005_patch["notes"] = kr0005_patch["notes"] + (
    "\n\n[2026-08-31 추가] items 47-54(TFI 표, '(1) 공통적용 경과조치 관련')를 같은 세션에서 "
    "추가로 백필 -- 자동추출기가 47-54를 다루지 않아(KR1000 티켓에서 확인된 사실) 별도 백필 "
    "필요했음. 라이브 마스터의 기존 item48=29380 은 item3(보완자본,헤드라인) 오염 복사값이라 "
    "11327.03(item14_적용전x50% 및 원문 '보완자본 한도' 행과 모두 일치)으로 정정. item53/54 "
    "값_적용후는 원문 자체가 공백(fitz word-dump로 확인, docling 유실 아님)이라 결측 유지. "
    "TFI 유형=CAPPED(EXCL scope) -- 축 B(target=item3) diff 0.36, 축 F(target=item51) diff "
    "0.01로 둘 다 근접 재현. 계산 근거는 각 셀 '근거' 필드 참조."
)
kr0005_patch_path.write_text(
    json.dumps(kr0005_patch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"\nwrote {kr0005_patch_path} (cells now {len(kr0005_patch['cells'])})")


# ---------------------------------------------------------------------------
# KR0075 -- items 50/51 turn out to be PRESENT in raw (patch2's "absent" claim
# was wrong). md_inbox/FY2026_Q2/KR0075_비엔피파리바카디프생명보험.md L411-412,
# same table already cited by the existing patch2 (PDF p21):
#   기본자본  176,419 / 176,419  (전/후, 백만원) -> item50 = 1764.19 / 1764.19
#   보완자본   23,386 /  23,386  (전/후, 백만원) -> item51 =  233.86 /  233.86
# Axis E cross-check (same table, item52=1998 already live): item50+item51 =
# 1764.19+233.86 = 1998.05, matches item52 (1998.05 raw / 1998 rounded live)
# almost exactly both columns (전=후 here since this company's TFI table is
# uniformly 전=후, matching its "경과조치 미적용" disclosure already used for
# items 1-49/53/54). Axis F (target=item51=233.86, INCL scope per patch2):
# uncapped test |233.86-233.86|=0 exact -> branch=I49_IN_I47_UNCAPPED, excess=0,
# consistent with the existing 47/48/49 UNCAPPED finding already in patch2.
KR0075_CELLS = [
    (50, 1764.19, 1764.19,
     "md_inbox/FY2026_Q2/KR0075_비엔피파리바카디프생명보험.md L411 '[지급여력비율의 경과조치 "
     "적용에 관한 사항] 1) 공통적용 경과조치 관련' 표(단위 백만원,%, PDF p21 -- 기존 patch2가 "
     "이미 같은 표를 인용한 페이지): 기본자본 176,419/176,419 (전/후) /100 -> 1764.19/1764.19. "
     "**patch2(_patch2_2026q2_KR0075.json)의 '50/51은 원문에 없다' 주장을 정정** -- 실제로는 "
     "같은 표에 두 행 다 인쇄돼 있다(md L410-412, 지급여력금액/기본자본/보완자본 세 행이 "
     "연속으로 존재). 축 E 검산: item50+item51 = 1764.19+233.86 = 1998.05, 같은 표의 "
     "item52(지급여력금액, 이미 라이브에 1998로 적재)와 diff 0.05로 거의 정확히 일치."),
    (51, 233.86, 233.86,
     "md_inbox/FY2026_Q2/KR0075_비엔피파리바카디프생명보험.md L412 같은 표: 보완자본 "
     "23,386/23,386 (전/후) /100 -> 233.86/233.86 (item47='보완자본 한도 적용 전'과 소수점까지 "
     "동일 -- patch2가 이미 문서화한 이 회사의 지배적 패턴 'item47==item51 10/13분기'와 부합). "
     "축 F(51_tfi_tier2_composition, target=item51, INCL scope): uncapped 시험 "
     "|233.86-233.86|=0 정확히 성립 -> branch=I49_IN_I47_UNCAPPED, excess=0 -- patch2가 이미 "
     "적재한 47/48/49의 UNCAPPED 판정과 완전히 같은 갈래로 재확인."),
]

kr0075_new_cells = []
for item, v_pre, v_post, reason in KR0075_CELLS:
    label = label_1q("KR0075", item)
    kr0075_new_cells.append({
        "항목번호": item,
        "항목명": label,
        "값": v_pre,
        "값_적용후": v_post,
        "근거": reason,
    })
    print(f"KR0075 item{item} 항목명={label!r} 값={v_pre} 값_적용후={v_post}")

kr0075_patch2_path = ROOT / "data" / "_derived" / "_patch2_2026q2_KR0075.json"
kr0075_patch2 = json.loads(kr0075_patch2_path.read_text(encoding="utf-8"))
existing_items_75 = {c["항목번호"] for c in kr0075_patch2["cells"]}
overlap_75 = existing_items_75 & {c["항목번호"] for c in kr0075_new_cells}
if overlap_75:
    raise SystemExit(f"ABORT: KR0075 patch2 already has items {overlap_75} -- would collide")
kr0075_patch2["cells"].extend(kr0075_new_cells)
kr0075_patch2["notes"] = kr0075_patch2["notes"] + (
    "\n\n[2026-08-31 정정] 위 notes 의 'Items 50/51 remain absent... out of scope' 주장은 "
    "틀렸다 -- 재확인 결과 같은 raw 표(md L410-412, PDF p21)에 기본자본/보완자본 두 행이 "
    "전/후 컬럼 모두 인쇄돼 있다(176,419/176,419 및 23,386/23,386, 백만원). item50=1764.19, "
    "item51=233.86 (양쪽 컬럼 동일, /100). 축 E(item50+item51==item52) 검산 diff 0.05로 거의 "
    "정확히 닫히고, 축 F(target=item51) uncapped 시험도 diff 0 으로 정확히 성립 -- 기존 47/48/49 "
    "UNCAPPED 판정과 같은 갈래(I49_IN_I47_UNCAPPED)로 재확인된다. 이전 SKIP(TFI_TIER_ROWS_"
    "ABSENT_BACKLOG) 판정의 원인은 47/48/49만 채우고 50/51을 같은 표에서 마저 읽지 않은 것이지, "
    "원문 결측이 아니었다."
)
kr0075_patch2_path.write_text(
    json.dumps(kr0075_patch2, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"\nwrote {kr0075_patch2_path} (cells now {len(kr0075_patch2['cells'])})")
