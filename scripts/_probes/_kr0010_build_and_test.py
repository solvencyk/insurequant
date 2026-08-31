# -*- coding: utf-8 -*-
import json, io, sys, copy, shutil, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

MASTER = "kics_disclosure.json"
SCRATCH = r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\a2eaf685-d24e-438d-8f71-52ff9b5cfb3b\scratchpad\kics_disclosure_scratch.json"

with open(MASTER, "r", encoding="utf-8") as f:
    data = json.load(f)

NAME, TICKER, LS, CODE, Q = "KB손해보험", "002550", "손해보험", "KR0010", "2026.2Q"

def row(item, label, val, val_post):
    r = {
        "원보험사코드": CODE, "원수사명": NAME, "티커": TICKER, "생손보여부": LS,
        "항목번호": item, "항목명": label, "공시분기": Q, "값": val,
    }
    if val_post is not None:
        r["값_적용후"] = val_post
    return r

L = {
 1: '가. 지급여력금액', 2: '기본자본', 3: '보완자본',
 4: 'Ⅰ. 건전성감독기준 재무상태표 상의 순자산', 5: '1. 보통주',
 6: '2. 자본항목 중 보통주 이외의 자본증권', 7: '3. 이익잉여금', 8: '4. 자본조정',
 9: '5. 기타포괄손익누계액', 10: '6. 비지배지분', 11: '7. 조정준비금',
 12: 'Ⅱ. 지급여력금액으로 불인정하는 항목 (지급이 예정된 주주배당액 등)',
 13: 'Ⅲ. 보완자본으로 재분류하는 항목 (기본자본 자본증권의 인정한도를 초과한 금액 등)',
 14: '나. 지급여력기준금액 (Ⅰ-Ⅱ+Ⅲ)', 15: 'Ⅰ. 기본요구자본',
 16: '- 분산효과 : (1+2+3+4+5) - Ⅰ', 17: '1. 생명장기손해보험위험액',
 18: '2. 일반손해보험위험액', 19: '3. 시장위험액', 20: '4. 신용위험액',
 21: '5. 운영위험액', 22: 'Ⅱ. 법인세조정액', 23: 'Ⅲ. 기타 요구자본(1+2+3)',
 25: '2. 비례성원칙을 적용한 종속회사의 요구자본 대응치',
 27: '다. 지급여력비율 : 가 ÷ 나 × 100', 28: '기본자본비율',
 36: '3-1. 금리위험액', 37: '3-2. 주식위험액', 38: '3-3. 부동산위험액',
 39: '3-4. 외환위험액', 40: '3-5. 자산집중위험액',
 41: '3-1-0. 금리위험 순자산가치(충격전)', 42: '3-1-1. 금리위험 순자산가치(평균회귀)',
 43: '3-1-2. 금리위험 순자산가치(금리상승)', 44: '3-1-3. 금리위험 순자산가치(금리하락)',
 45: '3-1-4. 금리위험 순자산가치(금리평탄)', 46: '3-1-5. 금리위험 순자산가치(금리경사)',
 47: '보완자본 한도 적용 전', 48: '보완자본 한도',
 49: '해약환급금 부족분 상당액 중 해약환급금 상당액 초과분',
 50: '기본자본(TFI표, 공통적용경과조치)', 51: '보완자본(TFI표, 공통적용경과조치)',
 52: '지급여력금액(TFI표, 공통적용경과조치)',
 53: '(기발행 신종자본증권)(TFI표, 공통적용경과조치)',
 54: '(기발행 후순위채무)(TFI표, 공통적용경과조치)',
}

item27 = round(135316/72187*100, 8)
item28 = round(54815/72187*100, 8)

patch_rows = [
    row(1, L[1], 135316, 135316),
    row(2, L[2], 54815, 54815),
    row(3, L[3], 80500, 80500),
    row(4, L[4], 127185, 127185),
    row(5, L[5], 665, 665),
    row(6, L[6], 0, 0),
    row(7, L[7], 74102, 74102),
    row(8, L[8], 0, 0),
    row(9, L[9], -11787, -11787),
    row(10, L[10], 65, 65),
    row(11, L[11], 64140, 64140),
    row(12, L[12], 552, 552),
    row(13, L[13], 71817, 71817),
    row(14, L[14], 72187, 72187),
    row(15, L[15], 99164, 99164),
    row(16, L[16], 37196, 37196),
    row(17, L[17], 69561, 69561),
    row(18, L[18], 10829, 10829),
    row(19, L[19], 34792, 34792),
    row(20, L[20], 15076, 15076),
    row(21, L[21], 6103, 6103),
    row(22, L[22], 27111, 27111),
    row(23, L[23], 133, 133),
    row(25, L[25], 133, 133),
    row(27, L[27], item27, item27),
    row(28, L[28], item28, item28),
    # market subs 36-40 (백만원 -> 억원, /100), mirrored (TAC/TIR/TER/TIRR = X)
    row(36, L[36], 10321.24, 10321.24),
    row(37, L[37], 30435.06, 30435.06),
    row(38, L[38], 1361.21, 1361.21),
    row(39, L[39], 8293.05, 8293.05),
    row(40, L[40], 0.0, 0.0),
    # IRR 41-46
    row(41, L[41], 142869.70, 142869.70),
    row(42, L[42], 143967.39, 143967.39),
    row(43, L[43], 131998.01, 131998.01),
    row(44, L[44], 153298.87, 153298.87),
    row(45, L[45], 139377.12, 139377.12),
    row(46, L[46], 144955.57, 144955.57),
    # TFI table 47-54
    row(47, L[47], 10244.19, 7343.08),
    row(48, L[48], 36093.38, 36093.38),
    row(49, L[49], 70256.09, 70256.09),
    row(50, L[50], 54815.45, 54815.45),
    row(51, L[51], 80500.28, 80500.28),
    row(52, L[52], 135315.73, 135315.73),
    row(53, L[53], 0, None),
    row(54, L[54], 2901.11, None),
]

print(f"patch has {len(patch_rows)} rows for {CODE} {Q}")

# splice: remove existing KR0010 2026.2Q rows, insert patch rows in their place
new_data = [r for r in data if not (r["원보험사코드"] == CODE and r["공시분기"] == Q)]
removed = len(data) - len(new_data)
print(f"removed {removed} existing corrupted rows")
insert_at = next(i for i, r in enumerate(data) if r["원보험사코드"] == CODE and r["공시분기"] == Q)
# recompute insert_at against new_data (position where old rows started, clipped)
insert_at = min(insert_at, len(new_data))
new_data[insert_at:insert_at] = patch_rows
print(f"new total rows: {len(new_data)} (was {len(data)}, delta {len(new_data)-len(data)})")

with open(SCRATCH, "w", encoding="utf-8") as f:
    json.dump(new_data, f, ensure_ascii=False, indent=2)
print("wrote scratch ->", SCRATCH)

# also dump the patch_rows alone for inspection
with open(r"C:\Users\sangwook.cho\AppData\Local\Temp\claude\C--Users-sangwook-cho-Desktop-insurequant\a2eaf685-d24e-438d-8f71-52ff9b5cfb3b\scratchpad\kr0010_patch_rows_only.json", "w", encoding="utf-8") as f:
    json.dump(patch_rows, f, ensure_ascii=False, indent=2)
