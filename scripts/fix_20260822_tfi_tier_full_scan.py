# -*- coding: utf-8 -*-
"""inbox 20260821T1425Z (validation, iter-3) 후속 — "같은 표를 반쯤만 읽는다" 문제를 닫는다.

[지급여력비율의 경과조치 적용에 관한 사항] 1) 공통적용 경과조치 표는 6줄이다:
    지급여력금액 (헤더)
    기본자본                              <- item50 (신규, 이 스크립트가 추가)
    보완자본                              <- item51 (신규, 이 스크립트가 추가)
    보완자본 한도 적용 전                  <- item47 (기존, fix_20260821_tier2_limit_lines.py)
    보완자본 한도                         <- item48 (기존)
    해약환급금 부족분 상당액 중 초과분      <- item49 (기존)
    지급여력기준금액 (종결, 스케일 앵커)

기존 스크립트는 아래 3줄(47/48/49)만 읽었다. 이 스크립트는 **같은 표를 한 번 열 때 위 2줄도
같이 읽는다** — extract_tier2 의 페이지탐색 로직은 그대로 재사용하고(재발명 아님, import),
item47 라벨이 매칭된 위치에서 **거꾸로** 가장 가까운 "기본자본"/"보완자본" 단독 행을 찾는다.

## 두 용도

  A) 430버킷(38개사) — 이미 47/48/49 는 마스터에 있고 50/51 만 없다. 이 스크립트는 47/48/49
     텍스트도 다시 추출하지만(같은 lines 리스트에서 같이 나옴), 쓰기 단계에서 이미 존재하는
     항목은 절대 덮어쓰지 않는다(idempotent, 기존 스크립트와 동일한 existing-guard) — 50/51 만
     신규 INSERT.
  B) 38버킷(13개사) — 47/48/49 도 마스터에 없다(TIER2_TABLE_ABSENT_INTERMITTENT, 2026-08-22
     RED 승격분). 이 스크립트가 이번에 표를 찾으면 47/48/49/50/51 **5줄 다** INSERT. 여전히
     못 찾으면(스캔본 등) 미검출로 남고, 사유를 census 에 남긴다 — 이 그룹은 회사별로 원인이
     다양해(스캔본/라벨완전분리/구조적 결측) 이 스크립트 하나로 전부 안 풀린다. 사람이 직접
     본 vision 판독분은 별도 스크립트(fix_20260822_tfi_manual_*.py)로 UPSERT한다.

## 스케일

기존과 동일한 방법론 재사용(재발명 아님) — item48(보완자본 한도) vs 마스터 기존 item14전×50%
를 1차 앵커, 표 자신의 "지급여력기준금액" 종결행 vs item14전을 2차(SCR_ANCHOR_FALLBACK)로 쓴다.
50/51 은 47/48/49 와 **같은 표·같은 컬럼**이라 별도 스케일 판별이 필요 없다 — 47/48/49 에 쓴
배율을 그대로 곱한다. **430버킷(이미 47/48/49 존재)에서는 교차검증을 추가한다**: 이번에 새로
추출한 raw47/48 에 그 배율을 곱한 값이 마스터에 이미 있는 item47/48 값과 (반올림 이내로) 같은지
확인하고, 다르면(=이번 페이지선택이 원래 로드와 다른 곳을 짚었다는 신호) 50/51 을 쓰지 않고
"MISMATCH_VS_EXISTING" 으로 보고만 한다 — 확인 안 된 값을 실을 수는 없다.

Usage:
  ...python scripts/fix_20260822_tfi_tier_full_scan.py --dry-run
  ...python scripts/fix_20260822_tfi_tier_full_scan.py --dry-run --only KR0002
  ...python scripts/fix_20260822_tfi_tier_full_scan.py
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(REPO / "scripts"))

import fitz  # noqa: E402

import fix_20260821_tier2_limit_lines as T2  # noqa: E402  (reuse: _num, _collect_values, ZERO, etc.)

TARGET = REPO / "kics_disclosure.json"
DISCLOSURE = REPO / "data" / "disclosure"
PROVENANCE_OUT = REPO / "data" / "_derived" / "tfi_tier_full_scan_provenance.json"

ITEM_LABELS = {
    47: "보완자본 한도 적용 전",
    48: "보완자본 한도",
    49: "해약환급금 부족분 상당액 중 해약환급금 상당액 초과분",
    50: "기본자본(TFI표, 공통적용경과조치)",
    51: "보완자본(TFI표, 공통적용경과조치)",
}


def norm(s: str) -> str:
    return s.replace(" ", "")


def extract_tfi_full(pdf: Path):
    """extract_tier2 의 페이지탐색+lines 구성을 재사용해 47/48/49 **와** 50/51 을 함께 읽는다.

    -> (found: dict[47..51] -> (pre,post) 원문 그대로(스케일 미확정), anchor, reason_if_empty)
    """
    doc = fitz.open(pdf)
    try:
        page_texts = [doc[i].get_text() for i in range(doc.page_count)]
    finally:
        doc.close()

    matched = {i for i, t in enumerate(page_texts)
               if "공통적용" in t and "보완자본" in t and "한도" in t}
    if not matched:
        total_chars = sum(len(t) for t in page_texts)
        n = len(page_texts)
        density = total_chars / n if n else 0
        if density < 400:
            return {}, None, f"UNREADABLE(스캔본 의심, {density:.1f}자/p, {n}p)"
        return {}, None, "'공통적용'+'보완자본'+'한도' 3키워드 동시 페이지 없음"

    include = set(matched)
    for i in matched:
        if i + 1 < len(page_texts):
            include.add(i + 1)

    lines: list[str] = []
    for i in sorted(include):
        lines.extend(x.strip() for x in page_texts[i].splitlines())

    # △/▲/▽/▼/− -> '-' 정규화. T2.NUMRE 는 ASCII 하이픈만 음수로 인식해서, 이 치환 없이는
    # "△52,265" 같은 토큰이 숫자로 안 잡히고 라벨/문구로 오인돼 _collect_values 가 그 자리에서
    # 멈춘다(실측: IBK연금 2023.1Q 기본자본 "△52,265" 두 컬럼 다 이 사유로 결측 처리될 뻔함).
    # item47/48/49 는 구조상 음수가 거의 없지만(한도·초과분은 정의상 0 이상) item50(기본자본)은
    # 자본잠식 회사에서 실제로 음수다 — 이 스크립트가 새로 보는 행이라 여기서 정규화한다.
    lines = [l.replace("△", "-").replace("▲", "-").replace("▽", "-").replace("▼", "-")
              .replace("−", "-") for l in lines]

    # 마침표를 천단위 구분자로 쓴 줄(실측: 삼성생명 2023.3Q "6.705.864" — 바로 옆줄은 정상
    # "6,705,864") 을 쉼표로 정규화한다. `\d{1,3}(\.\d{3})+` (3자리씩 반복되는 마침표그룹)
    # **만** 대상으로 좁혀서, 진짜 소수(예: "12.34")를 잘못 건드리지 않는다. 안 하면 NUMRE 가
    # 마침표 두 개짜리 토큰을 숫자로 인식 못 해 그 줄에서 값 수집이 멈춘다.
    _EURO_THOUSANDS = re.compile(r"^-?\d{1,3}(\.\d{3})+$")
    lines = [(l.replace(".", ",") if _EURO_THOUSANDS.match(l.strip()) else l) for l in lines]

    if norm("보완자본 한도 적용 전") in {norm(l) for l in lines}:
        idx = next(i for i, l in enumerate(lines) if norm(l) == norm("보완자본 한도 적용 전"))
        if idx + 1 < len(lines) and norm(lines[idx + 1]) == norm("보완자본 한도 적용 전"):
            deduped = []
            for l in lines:
                if deduped and deduped[-1].strip() == l.strip():
                    continue
                deduped.append(l)
            lines = deduped

    targets = {47: norm("보완자본 한도 적용 전"), 48: norm("보완자본 한도")}
    LABEL49_HEAD = norm("해약환급금 부족분 상당액 중")
    LABEL_KIBON = norm("기본자본")
    LABEL_BOWAN = norm("보완자본")
    found: dict[int, tuple] = {}
    pos47_label = None
    pos48_label = None
    pos_48_end = None
    k = 0
    while k < len(lines):
        s = norm(lines[k])
        hit_it = None
        if s == targets[47]:
            hit_it = 47
            if pos47_label is None:
                pos47_label = k
        elif s == targets[48]:
            hit_it = 48
            if pos48_label is None:
                pos48_label = k
        elif s != "" and (s.startswith(LABEL49_HEAD) or LABEL49_HEAD.startswith(s)):
            acc = s
            j = k + 1
            while "초과분" not in acc and j < len(lines):
                nxt = lines[j].replace(" ", "")
                if nxt == "" or nxt in T2.DECOR:
                    j += 1
                    continue
                if T2.NUMRE.match(nxt) or nxt in T2.ZERO:
                    break
                acc += norm(lines[j])
                j += 1
            if "초과분" in acc:
                hit_it = 49
                k = j - 1
            else:
                k += 1
                continue
        if hit_it and hit_it not in found:
            vals, j = T2._collect_values(lines, k + 1, need=2)
            if len(vals) == 2:
                found[hit_it] = (vals[0], vals[1])
            elif len(vals) == 1:
                found[hit_it] = (vals[0], vals[0])
            if hit_it == 48:
                pos_48_end = j
            k = j
            continue
        k += 1

    # --- item50/51: item47 라벨 위치를 1순위 기준점으로 쓰고(47이 안 잡힌 버킷은 48 위치로
    # 대체), 그 **앞뒤 20줄** 안에서 "기본자본"/"보완자본" 단독행을 찾는다. 정상 레이아웃은
    # 두 라벨이 바로 위 인접행이라 좁은 backward 탐색으로 충분하지만, 일부 필링(코리안리
    # 2023.1Q/2025.1Q 등)은 페이지 텍스트스트림 자체가 여러 표(경과조치 전후 트렌드표 +
    # 공통적용표)가 뒤섞여 인접성이 깨진다 — 그런 필링에서는 라벨이 item47 **뒤**에 나오기도
    # 한다(실측: 코리안리 2023.1Q "기본자본"이 item47 매칭 위치보다 6줄 뒤). 그래서 방향을
    # 고정하지 않고 가장 가까운(전/후 무관) occurrence 를 쓴다 — 대신 이 값을 실제로 쓸지는
    # main() 의 item50+51==item1 자체검산 게이트가 최종 결정한다(틀린 표를 집었으면 그 합이
    # item1 과 안 맞아 자동으로 거부된다 — "값을 지어내지 마라" 원칙을 검산으로 강제).
    ref = pos47_label if pos47_label is not None else pos48_label
    if ref is not None:
        window = 20
        lo, hi = max(0, ref - window), min(len(lines), ref + window)

        def _closest(label: str, exclude=()):
            best = None
            for idx in range(lo, hi):
                if idx in exclude:
                    continue
                if norm(lines[idx]) == label:
                    if best is None or abs(idx - ref) < abs(best - ref):
                        best = idx
            return best

        pos51 = _closest(LABEL_BOWAN)
        if pos51 is not None:
            vals, _j = T2._collect_values(lines, pos51 + 1, need=2)
            if len(vals) == 2:
                found[51] = (vals[0], vals[1])
            elif len(vals) == 1:
                found[51] = (vals[0], vals[0])
            pos50 = _closest(LABEL_KIBON, exclude={pos51})
            if pos50 is not None:
                vals2, _j2 = T2._collect_values(lines, pos50 + 1, need=2)
                if len(vals2) == 2:
                    found[50] = (vals2[0], vals2[1])
                elif len(vals2) == 1:
                    found[50] = (vals2[0], vals2[0])

    if not found:
        return {}, None, "라벨 매칭 실패(페이지는 찾았으나 못 읽음)"

    anchor = None
    if pos_48_end is not None:
        k2 = pos_48_end
        while k2 < len(lines):
            if norm(lines[k2]) != "지급여력기준금액":
                k2 += 1
                continue
            vals, j = T2._collect_values(lines, k2 + 1, need=2)
            if len(vals) == 2:
                anchor = (vals[0], vals[1])
                break
            if len(vals) == 1:
                anchor = (vals[0], vals[0])
                break
            k2 += 1
    return found, anchor, None


def main() -> int:
    dry = "--dry-run" in sys.argv
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None

    data = json.loads(TARGET.read_text(encoding="utf-8"))
    print(f"로드 전 row_count = {len(data):,}")

    by_c: dict[str, set] = {}
    info: dict[str, dict] = {}
    existing = set()
    m14: dict[tuple, tuple] = {}
    m1: dict[tuple, tuple] = {}
    m47_48: dict[tuple, tuple] = {}  # (code,q) -> {47:(pre,post),48:(pre,post)} existing master
    for r in data:
        c, q = r["원보험사코드"], r["공시분기"]
        by_c.setdefault(c, set()).add(q)
        info.setdefault(c, {"원수사명": r.get("원수사명"), "티커": r.get("티커"),
                             "생손보여부": r.get("생손보여부")})
        it = int(r["항목번호"])
        existing.add((c, q, it))
        if it == 14:
            m14[(c, q)] = (T2._num(r.get("값")), T2._num(r.get("값_적용후")))
        if it == 1:
            m1[(c, q)] = (T2._num(r.get("값")), T2._num(r.get("값_적용후")))
        if it in (47, 48):
            m47_48.setdefault((c, q), {})[it] = (T2._num(r.get("값")), T2._num(r.get("값_적용후")))

    new_rows = []
    census = []
    provenance = []
    mismatches = []  # bucket 이미 47/48/49 있는데 이번 재추출값이 마스터와 안 맞는 경우
    selfcheck = []   # item50+51 vs item1 (모든 신규기록 대상)

    for c in sorted(by_c):
        if only and c != only:
            continue
        for q in sorted(by_c[c]):
            pdf = T2._pdf(T2.q2p(q), c)
            if pdf is None:
                census.append((c, info[c]["원수사명"], q, "raw없음", ""))
                continue
            found, anchor, reason = extract_tfi_full(pdf)
            if not found:
                census.append((c, info[c]["원수사명"], q, "미검출", reason or ""))
                continue

            m14_pre, _m14_post = m14.get((c, q), (None, None))
            f47, f48, f49 = found.get(47), found.get(48), found.get(49)
            f50, f51 = found.get(50), found.get(51)
            scale = None
            method = None
            ratio_used = None
            ratio48 = f48[0] / (m14_pre * 0.5) if (
                f48 is not None and f48[0] is not None and m14_pre and m14_pre * 0.5) else None
            ratio_scr = anchor[0] / m14_pre if (anchor is not None and anchor[0] and m14_pre) else None

            if (f48 is not None and f48[0] is not None and abs(f48[0]) < 0.005
                    and T2._trivial(f47) and T2._trivial(f49)):
                scale = 1.0
                method = "ALL_ZERO_TRIVIAL"
            elif f48 is not None and f48[0] is not None and abs(f48[0]) >= 0.005 and ratio48 is not None:
                if 0.98 < ratio48 < 1.02:
                    scale, method, ratio_used = 1.0, "ITEM48_ANCHOR", ratio48
                elif 98 < ratio48 < 102:
                    scale, method, ratio_used = 0.01, "ITEM48_ANCHOR", ratio48
            if scale is None and ratio_scr is not None:
                if 0.98 < ratio_scr < 1.02:
                    scale, method, ratio_used = 1.0, "SCR_ANCHOR_FALLBACK", ratio_scr
                elif 98 < ratio_scr < 102:
                    scale, method, ratio_used = 0.01, "SCR_ANCHOR_FALLBACK", ratio_scr

            clean_target = 1.0 if scale == 1.0 else (100.0 if scale == 0.01 else None)
            ambiguous = (
                method == "SCR_ANCHOR_FALLBACK"
                or (ratio_used is not None and clean_target is not None
                    and abs(ratio_used - clean_target) / clean_target > 0.005)
            )
            provenance.append({
                "원보험사코드": c, "원수사명": info[c]["원수사명"], "공시분기": q,
                "method": method, "scale": scale, "ratio_used": ratio_used,
                "ambiguous": bool(ambiguous) if scale is not None else None,
                "resolved": scale is not None,
                "raw_47": f47, "raw_48": f48, "raw_49": f49, "raw_50": f50, "raw_51": f51,
                "raw_anchor_scr": anchor, "m14_pre": m14_pre,
                "already_had_47_48_49": bool((c, q, 47) in existing or (c, q, 48) in existing),
                # 50/51 은 별도 앵커(item1)로 스케일을 다시 판별한다 -- 아래에서 채워짐.
                "scale_5051": None, "method_5051": None, "scale_5051_vs_scale_diff": None,
            })

            if scale is None:
                census.append((c, info[c]["원수사명"], q, "스케일불명",
                                f"item48={f48} m14전x50%={m14_pre*0.5 if m14_pre else None}"))
                continue

            # 교차검증: 이미 47/48 이 마스터에 있으면, 이번 재추출값*scale 이 기존 마스터
            # 값과 같은지 확인한다 -- 다르면 이번 page selection 이 원래 로드와 다른 곳을
            # 짚었다는 뜻이라 50/51 을 못 믿는다(값을 지어내지 마라 원칙).
            had_master = m47_48.get((c, q), {})
            mismatch_detail = []
            for it, fpair in ((47, f47), (48, f48)):
                if it in had_master and fpair is not None:
                    mp, mpost = had_master[it]
                    rp = None if fpair[0] is None else round(fpair[0] * scale, 2)
                    rpost = None if fpair[1] is None else round(fpair[1] * scale, 2)
                    if mp is not None and rp is not None and abs(mp - rp) > 0.5:
                        mismatch_detail.append(f"item{it}값 기존={mp:g} 재추출={rp:g}")
                    if mpost is not None and rpost is not None and abs(mpost - rpost) > 0.5:
                        mismatch_detail.append(f"item{it}값_적용후 기존={mpost:g} 재추출={rpost:g}")
            if mismatch_detail:
                mismatches.append((c, q, "; ".join(mismatch_detail)))
                census.append((c, info[c]["원수사명"], q, "MISMATCH_VS_EXISTING",
                                "; ".join(mismatch_detail) + " -- 50/51 보류"))
                continue

            # 50/51 스케일 — **47/48/49 의 scale 을 맹신하지 않는다.** 47/48/49 가 전부
            # 사실상 0(TFI_NA 회사군, 메트라이프·카카오페이 등)이면 위의 ALL_ZERO_TRIVIAL
            # 분기가 scale=1.0 을 "0×어떤 배율도 0이니 상관없다"는 이유로 임의로 고른다 —
            # 47/48/49 에는 맞지만 50/51(기본자본/보완자본, 절대 0 아닌 실값)에 그 배율을
            # 그대로 물려주면 틀린다(실측: 카카오페이 2023.1Q 기본자본 38,147백만 를 ÷100 안
            # 하고 그대로 써서 100배 튀었다 — 2026-08-22 이 스크립트 첫 dry-run에서 발견).
            # 그래서 50/51 은 **item1(마스터 기존, 이미 검증됨) 을 앵커로 별도 스케일을 다시
            # 판별**한다 — 47/48/49 스케일과 원래 같아야 정상이고(TFI표는 한 표·한 컬럼이라),
            # 다르면 그 자체가 "이번 backward/forward 탐색이 다른 표를 집었다"는 신호다.
            scale_5051 = None
            method_5051 = None
            if 50 in found and 51 in found:
                i1_pre, i1_post = m1.get((c, q), (None, None))
                s50, s51 = found[50], found[51]
                sumpre = (s50[0] + s51[0]) if (s50[0] is not None and s51[0] is not None) else None
                ratio1 = sumpre / i1_pre if (sumpre and i1_pre) else None
                if ratio1 is not None:
                    if 0.98 < ratio1 < 1.02:
                        scale_5051, method_5051 = 1.0, "ITEM1_ANCHOR"
                    elif 98 < ratio1 < 102:
                        scale_5051, method_5051 = 0.01, "ITEM1_ANCHOR"
                if scale_5051 is None:
                    # item1 앵커로 못 정하면(예: item1 자체가 결측) 47/48/49 스케일로 대체
                    # 시도하되, 이 경우는 검증되지 않은 대체이므로 아래 자체검산 게이트가
                    # 최종 결정한다(실패하면 안 쓴다).
                    scale_5051, method_5051 = scale, "FALLBACK_TIER2_SCALE"
                provenance[-1]["scale_5051"] = scale_5051
                provenance[-1]["method_5051"] = method_5051
                provenance[-1]["scale_5051_vs_scale_diff"] = (
                    None if scale_5051 == scale else f"scale(47/48/49)={scale} vs scale_5051={scale_5051}"
                )

            # 50/51 쓰기 게이트: item50+item51==item1(적용전) 자체검산을 통과해야만 쓴다.
            # **적용전만 게이트로 쓴다.** 적용후는 회사에 따라 실패하는 게 오히려 정상이다 —
            # 선택경과조치(TAC/TIR/TER/TIRR)를 함께 신청한 회사는 마스터 item1_후가 TFI+선택
            # **전체결합** 스코프인데 이 표의 50/51_후는 TFI **단독** 스코프라(item48_후 vs
            # item14_후 가 같은 이유로 못 맞는 것과 동일 구조, kics_json_rules.py 축D 참고),
            # 그 항등식은 애초에 안 맞는 게 정상이다(실측: 에이비엘·KDB생명·푸본현대·하나생명·
            # IBK연금 — 전부 "선택경과조치 상시적용" 등록 회사군, 적용전은 전부 성립·적용후만
            # 회사·연도별 일정한 오프셋으로 어긋남 — 무작위 오류가 아니라 스코프차 구조 신호).
            # 적용후 값은 원문 그대로 쓰되(지어낸 게 아니다) 검사는 안 건다.
            block_5051 = False
            selfcheck_detail = None
            if 50 in found and 51 in found and scale_5051 is not None:
                i1_pre, i1_post = m1.get((c, q), (None, None))
                p50 = None if found[50][0] is None else round(found[50][0] * scale_5051, 2)
                p51 = None if found[51][0] is None else round(found[51][0] * scale_5051, 2)
                q50 = None if found[50][1] is None else round(found[50][1] * scale_5051, 2)
                q51 = None if found[51][1] is None else round(found[51][1] * scale_5051, 2)
                checks = []
                if i1_pre is not None and p50 is not None and p51 is not None:
                    checks.append(("전", p50 + p51, i1_pre, (p50 + p51) - i1_pre))
                if i1_post is not None and q50 is not None and q51 is not None:
                    checks.append(("후", q50 + q51, i1_post, (q50 + q51) - i1_post))
                pre_checks = [ch for ch in checks if ch[0] == "전"]
                if not pre_checks:
                    block_5051 = True
                    selfcheck_detail = "ITEM1_PRE_MISSING_CANT_VERIFY"
                else:
                    # 쓰기 차단선은 **완화된 상대오차**(5%, 최소 5.0억)다 — 3.0억(절대)은 보고용
                    # 문턱일 뿐이다. 이유: scale_5051 이 이미 ITEM1_ANCHOR(자기 자신의 2% 밴드
                    # 검증) 나 FALLBACK_TIER2_SCALE(47/48/49 로 이미 검증된 배율)로 신뢰할 만하게
                    # 정해진 상태에서, 남은 잔차는 "잘못 짚은 표"가 아니라 **발행사 원본 자체의
                    # 불일치**일 확률이 높다(실측: 롯데손해 KR0003 2023.1Q diff=18/25846=0.07%·
                    # 2026.1Q diff=-896.51/26955=3.3% — 둘 다 이 티켓에서 원문 대조로 이미 확정된
                    # 발행사 자기모순/전기표 재게시 사례와 정확히 같은 규모다). "안 맞는 버킷은
                    # 강제로 맞추지 말고 원문 값 그대로 두고 목록으로 내라"— 값을 지어내지 않는
                    # 한 안 싣는 것도 "맞춘다"의 일종이다고 판단해, 스케일이 신뢰됐으면 쓰고
                    # 목록만 남긴다. 반면 스케일 앵커가 실패한 버킷(카카오페이류, 이미 위에서
                    # scale_5051 자체가 None 이 되어 여기 도달 못 함)이나 자릿수가 통째로 다른
                    # 경우(수백~수천 % 급)는 이 문턱을 넘어 확실히 차단된다.
                    block_tol = max(5.0, abs(pre_checks[0][2]) * 0.05)
                    bad_pre_block = [ch for ch in pre_checks if abs(ch[3]) > block_tol]
                    if bad_pre_block:
                        block_5051 = True
                        selfcheck_detail = "SELFCHECK_FAIL(전,차단): " + "; ".join(
                            f"50+51={got:g} item1={exp:g} diff={diff:g}"
                            for _col, got, exp, diff in bad_pre_block)
                    bad = [ch for ch in checks if abs(ch[3]) > 3.0]  # 보고용(후 포함, 3.0억 고정)
                    selfcheck.append((c, q, checks, bad))
            elif 50 in found and 51 in found and scale_5051 is None:
                block_5051 = True
                selfcheck_detail = "SCALE_5051_UNRESOLVED"
            elif (50 in found) != (51 in found):
                # 같은 표의 연속 2행 중 한쪽만 잡혔다 -- 행 유실 신호, 반쪽만 싣지 않는다.
                block_5051 = True
                selfcheck_detail = "PARTIAL_ROW_50_51_ONLY_ONE_FOUND"

            n_written = 0
            written_items = []
            for it in (47, 48, 49, 50, 51):
                if it not in found:
                    continue
                if it in (50, 51) and block_5051:
                    continue
                if (c, q, it) in existing:
                    continue
                pre_raw, post_raw = found[it]
                use_scale = scale_5051 if it in (50, 51) else scale
                pre = None if pre_raw is None else round(pre_raw * use_scale, 2)
                post = None if post_raw is None else round(post_raw * use_scale, 2)
                if pre is None and post is None:
                    continue
                row = {
                    "원보험사코드": c, "원수사명": info[c]["원수사명"],
                    "티커": info[c]["티커"], "생손보여부": info[c]["생손보여부"],
                    "항목번호": it, "항목명": ITEM_LABELS[it], "공시분기": q,
                }
                if pre is not None:
                    row["값"] = _fmt(pre)
                if post is not None:
                    row["값_적용후"] = _fmt(post)
                new_rows.append(row)
                n_written += 1
                written_items.append(it)

            already_had_5051 = (c, q, 50) in existing and (c, q, 51) in existing
            if n_written == 0:
                if already_had_5051:
                    census.append((c, info[c]["원수사명"], q, "이미완비", ""))
                elif block_5051:
                    census.append((c, info[c]["원수사명"], q, "50/51_거부", selfcheck_detail))
                elif 50 not in found or 51 not in found:
                    have_47_49 = any(it in found for it in (47, 48, 49))
                    census.append((c, info[c]["원수사명"], q,
                                    "50/51_미검출" if have_47_49 else "미검출", ""))
                else:
                    census.append((c, info[c]["원수사명"], q, "이미완비", ""))
            else:
                status = "OK" if not block_5051 else "OK(50/51거부)"
                detail = f"{n_written}개 항목 신규 {written_items} scale={scale}"
                if block_5051:
                    detail += f" | {selfcheck_detail}"
                census.append((c, info[c]["원수사명"], q, status, detail))

    ok = sum(1 for *_x, s, _d in [(c, n, q, s, d) for c, n, q, s, d in census]
             if s in ("OK", "OK(50/51거부)"))
    print(f"\n스캔 (회사,분기) = {len(census)} | 신규기록 OK = {ok} | 이미완비 = "
          f"{sum(1 for *_x,s,_d in census if s=='이미완비')} | raw없음 = "
          f"{sum(1 for *_x,s,_d in census if s=='raw없음')} | 미검출 = "
          f"{sum(1 for *_x,s,_d in census if s=='미검출')} | 50/51_미검출 = "
          f"{sum(1 for *_x,s,_d in census if s=='50/51_미검출')} | 50/51_거부(자체검산실패) = "
          f"{sum(1 for *_x,s,_d in census if s in ('50/51_거부','OK(50/51거부)'))} | 스케일불명 = "
          f"{sum(1 for *_x,s,_d in census if s=='스케일불명')} | MISMATCH = "
          f"{sum(1 for *_x,s,_d in census if s=='MISMATCH_VS_EXISTING')}")
    print(f"신규 셀 = {len(new_rows)}건")

    if mismatches:
        print(f"\n=== MISMATCH_VS_EXISTING ({len(mismatches)}건, 50/51 보류) ===")
        for c, q, d in mismatches:
            print(f"  {c} {q}: {d}")

    rejected_5051 = [(c, n, q, s, d) for c, n, q, s, d in census
                      if s in ("50/51_거부", "OK(50/51거부)")]
    if rejected_5051:
        print(f"\n=== 50/51 자체검산 거부 ({len(rejected_5051)}건, 원문 값 안 실음) ===")
        for c, n, q, s, d in rejected_5051:
            print(f"  {c} {n} {q}: {d}")

    print("\n=== 회사별 신규기록 커버리지 (OK / 스캔분기수) ===")
    by_company: dict[str, list] = {}
    for c, n, q, s, d in census:
        by_company.setdefault(c, []).append((q, s, d))
    for c in sorted(by_company):
        entries = by_company[c]
        ok_n = sum(1 for _q, s, _d in entries if s in ("OK", "OK(50/51거부)"))
        already = sum(1 for _q, s, _d in entries if s == "이미완비")
        problems = [f"{q}({s})" for q, s, d in entries if s not in ("OK", "이미완비")]
        print(f"  {c} {info[c]['원수사명']:<16} 신규{ok_n:>2} 기완비{already:>2} 문제{len(problems):>2}"
              + (f"  -> {', '.join(problems)}" if problems else ""))

    all_checks = [(c, q, col, got, exp, diff)
                  for c, q, checks, _bad in selfcheck for col, got, exp, diff in checks]
    bad = [row for row in all_checks if abs(row[5]) > 3.0]
    print(f"\n=== item50+item51 == item1 자체검산 ({len(all_checks)}건 -- 시도한 모든 컬럼,"
          f" 거부돼서 안 실린 것 포함) ===")
    print(f"  성립(|잔차|<=3.0) {len(all_checks)-len(bad)} / 불일치 {len(bad)}")
    if bad:
        for c, q, col, got, exp, diff in bad:
            print(f"  [불일치] {c} {q} [{col}] 50+51={got:g} item1={exp:g} diff={diff:g}")
    max_abs = max((abs(r[5]) for r in all_checks), default=0.0)
    print(f"  최대 |잔차| = {max_abs:g}")

    if only is None:
        PROVENANCE_OUT.parent.mkdir(parents=True, exist_ok=True)
        PROVENANCE_OUT.write_text(
            json.dumps({
                "generated_at_note": "scripts/fix_20260822_tfi_tier_full_scan.py 실행 시 갱신",
                "총건수": len(provenance),
                "resolved": sum(1 for p in provenance if p["resolved"]),
                "ambiguous(review 필요)": sum(1 for p in provenance if p.get("ambiguous")),
                "mismatch_vs_existing": len(mismatches),
                "selfcheck_item50_51_vs_item1": {
                    "n": len(all_checks), "n_bad": len(bad), "max_abs_diff": max_abs,
                    "n_buckets_rejected": len(rejected_5051),
                },
                "records": provenance,
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\nprovenance -> {PROVENANCE_OUT}")

    if dry:
        print("\n(dry-run; 파일 안 씀)")
        return 0
    if not new_rows:
        print("쓸 셀 없음")
        return 0

    data.extend(new_rows)
    TARGET.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{len(new_rows)}행 INSERT, wrote {TARGET.name} "
          f"(row_count {len(data)-len(new_rows):,} -> {len(data):,})")
    return 0


def _fmt(x: float) -> str:
    return str(int(round(x))) if abs(x - round(x)) < 1e-6 else f"{x:.2f}".rstrip("0").rstrip(".")


if __name__ == "__main__":
    raise SystemExit(main())
