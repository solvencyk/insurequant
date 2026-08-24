# -*- coding: utf-8 -*-
"""Apply manually vision-confirmed overrides to
data/_derived/kics_transition_applicability.json for buckets that neither the
md_inbox regex pass nor the raw-PDF regex fallback could resolve (scanned PDFs
with no usable text layer, read via get_pixmap(dpi=200-240) + visual inspection
this session, 2026-08-22). Each override carries the PDF page cited and a short
note so the provenance is auditable — never a bare value.

Also reclassifies buckets confirmed this session to be backed by the WRONG /
a differently-scoped source document (large bundled annual-report PDF instead
of the focused 정기경영공시, or a fundamentally different disclosure structure
that doesn't cover TFI) — these are NOT vision-recoverable (the right content
isn't in the file) and are flagged as such for downloader/owner follow-up
rather than left with a generic 'not found' reason.

Idempotent: re-running just re-applies the same overrides. Does not touch
kics_disclosure.json or any validator/registry file.
"""
from __future__ import annotations
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
JSON_PATH = REPO / "data" / "_derived" / "kics_transition_applicability.json"

# (code, quarter) -> {kind: value, ...} plus "_evidence" (str) and "_method".
# Values are exactly what was read off the rendered page image — never inferred
# from a sibling quarter.
VISION_OVERRIDES = {
    ("KR0080", "2025.1Q"): {  # AIA생명, scan-only PDF (32p)
        "TFI": "X", "RPT": "X", "TAC": "X", "TIR": "X", "TER": "X", "TIRR": "X", "PCA_DEFER": "X",
        "_evidence": "raw PDF p16/32, get_pixmap dpi=240. 명시문: '당사는 경과조치를 적용하지 않아, "
                     "경과조치 전후 금액 및 비율이 동일합니다.' 표 7행 전부 X.",
    },
    ("KR0080", "2025.2Q"): {
        "TFI": "X", "RPT": "X", "TAC": "X", "TIR": "X", "TER": "X", "TIRR": "X", "PCA_DEFER": "X",
        "_evidence": "raw PDF p17/52, get_pixmap dpi=200. 동일 문구, 표 7행 전부 X.",
    },
    ("KR0080", "2025.3Q"): {
        "TFI": "X", "RPT": "X", "TAC": "X", "TIR": "X", "TER": "X", "TIRR": "X", "PCA_DEFER": "X",
        "_evidence": "raw PDF p16/33, get_pixmap dpi=200. 동일 문구, 표 7행 전부 X.",
    },
    ("KR0080", "2026.1Q"): {
        "TFI": "X", "RPT": "O", "TAC": "X", "TIR": "X", "TER": "X", "TIRR": "X", "PCA_DEFER": "X",
        "_evidence": "raw PDF p17/36, get_pixmap dpi=130/200. 표 7행: 업무보고서(RPT)만 O, 나머지 X "
                     "(다른 AIA 분기와 달리 RPT=O — 분기마다 O/X 실측대로 반영).",
    },
    ("KR0010", "2025.3Q"): {  # KB손해보험, scan-only
        "TFI": "O", "RPT": "O", "TAC": "X", "TIR": "X", "TER": "X", "TIRR": "X", "PCA_DEFER": "X",
        "_evidence": "raw PDF p16/26(내부표기 p14), get_pixmap dpi=220. TFI=O 확인 — 예별손해/코리안리류 "
                     "'TFI만 적용' 패턴. item47-51 breakdown 표 존재 여부는 이번 임무 범위 밖(별도 세션).",
    },
    ("KR0010", "2026.1Q"): {
        "TFI": "O", "RPT": "O", "TAC": "X", "TIR": "X", "TER": "X", "TIRR": "X", "PCA_DEFER": "X",
        "_evidence": "raw PDF p17/27(내부표기 p15), get_pixmap dpi=150/220. TFI=O 이중확증: 요약표 O + "
                     "바로 다음 페이지 '(1)공통적용 경과조치 관련' breakdown 표에서 보완자본 한도 적용 전 "
                     "1,397,123(전)->737,858(후) 실제 변동 확인(TAC/TIR/TER/TIRR 서술형 3항목도 전부 "
                     "'적용하지 않아... 동일함' 명시).",
    },
    ("KR0005", "2024.4Q"): {  # 흥국화재, scan-only (96p)
        "TFI": "O", "RPT": "X", "TAC": "X", "TIR": "O", "TER": "O", "TIRR": "O", "PCA_DEFER": "X",
        "_evidence": "raw PDF p39/96, get_pixmap dpi=200. registry _TRANSITION_KIND['KR0005']="
                     "{IR,EQ,INT}와 정확히 일치(TIR/TER/TIRR=O, TAC=X).",
    },
    ("KR1098", "2024.4Q"): {  # 카카오페이손해보험, scan-only, different section numbering (5-2, not 4-2-2)
        "TFI": "X", "TAC": "X", "TIR": "X", "TER": "X", "TIRR": "X",
        "_evidence": "raw PDF p26/61(내부표기 p26), get_pixmap dpi=200. 이 회사는 '4-2-2' 대신 "
                     "'5-2-2 지급여력비율의 경과조치 적용에 관한 세부사항' 번호체계. O/X 요약표는 없고 "
                     "명시문만: '당사는 경과조치 미적용에 따라 경과조치 후 지급여력비율은 경과조치 적용 전 "
                     "수치와 동일함' + [지급여력비율 총괄] 표에서 경과조치전=후 409.63 완전동일 확인. "
                     "RPT/PCA_DEFER는 이 문장이 명시적으로 다루지 않아 UNKNOWN 유지.",
    },
    ("KR0097", "2024.4Q"): {  # 하나생명보험 — 2026-08-22(tier2 데이터결함 17건 세션) 정정
        "TFI": "X",
        "_evidence": "raw PDF p48, get_pixmap dpi=200. '2) 지급여력비율의 경과조치 적용에 관한 세부 "
                     "사항' 표(공통적용/선택적용 O·X 그리드)에 명시: 공통적용·가용자본·TFI(제도시행前 "
                     "기발행자본증권가용자본 인정범위 확대) = X. TAC=O·TIR=O·TER=O·TIRR=X·적기시정조치"
                     "유예=X 도 같은 표에서 확인(참고용, 이번 세션은 TFI만 반영). 이전 세션의 "
                     "STRUCTURALLY_ABSENT 판정('키워드 4종 0회라 근거 없음')은 검색한 키워드가 이 "
                     "회사의 실제 절 제목('2) 지급여력비율의 경과조치 적용에 관한 세부 사항')과 달라 "
                     "빗나간 것 — 이 표가 존재하는데 못 찾은 것이었다.",
    },
}

# (code, quarter) confirmed this session to be backed by the WRONG source document
# (a large bundled report, not the focused 정기경영공시) — TFI etc. genuinely absent
# from THIS PDF; vision cannot recover content that isn't in the file. Distinct from
# a plain "not found" so downloader/owner can triage as a re-fetch candidate.
#
# 2026-08-22 정정 — 이 4건 전부 여기서 빠졌다. 원래 판정 근거는 텍스트 키워드 검색 0회뿐이었는데,
# 4건 모두 실제로는 그 큰 번들 문서("OOO보험회사의 현황", 보험업법 124조 연간 종합공시) **안에**
# 스캔(이미지) 페이지로 표준 tier2 표가 들어 있었다(예: 흥국생명 p49, 해당 세션에서 렌더링 확인).
# `kics_disclosure.json`에 items 1-51이 이미 정상 적재돼 있는 것이 그 증거 — 파일이 틀린 게
# 아니라 예전 텍스트 전용 스캔이 스캔 구간까지 못 들어간 것이었다. 다운로더 재수집 불필요.
# (신규 TFI 값 O/X는 이번 세션에서 확정하지 않음 — 아래 UNKNOWN 유지, 별도 세션 필요.)
WRONG_DOCUMENT: dict[tuple[str, str], str] = {}

# (code, quarter): TFI genuinely not covered anywhere in an otherwise-correct,
# text-bearing document — different failure mode from WRONG_DOCUMENT (the right
# filing IS there, TAC/TIR were successfully read from it; the '4-2-2' style
# summary table just isn't part of THIS quarter's structure).
#
# KR0097 2024.4Q was here (STRUCTURALLY_ABSENT) until 2026-08-22 — retracted, see
# VISION_OVERRIDES above: p48 has the exact O/X grid this dict's note said didn't
# exist, just under a section title the earlier keyword search didn't try.
STRUCTURALLY_ABSENT: dict[tuple[str, str], str] = {}

# (code, quarter) that used to carry a WRONG_DOCUMENT reason (above) and no longer
# do — explicit retraction so a stale on-disk reason from a prior run of this
# script doesn't survive just because the key left the dict above. TFI itself is
# left UNKNOWN (not asserted O/X in this pass); only the false "wrong document"
# claim is retracted.
RETRACTED_WRONG_DOCUMENT = {
    ("KR0080", "2024.4Q"): "정정: WRONG_OR_BUNDLED_SOURCE_DOCUMENT 아니었음. kics_disclosure.json에 "
                           "items 1-51 이미 정상 적재(출처: 이 raw 파일의 스캔 페이지, 이전 세션 vision "
                           "추출 — 텍스트 키워드 검색만으로는 스캔 구간을 못 봐서 '문서 없음'으로 오판됨).",
    ("KR0080", "2025.4Q"): "정정: 위와 동일 사유. items 1-51 이미 정상 적재.",
    ("KR0010", "2025.4Q"): "정정: 위와 동일 사유. items 1-51(일부 memo행 제외) 이미 정상 적재.",
    ("KR0071", "2024.4Q"): "정정: 위와 동일 사유. p49 [지급여력비율의 경과조치 적용에 관한 사항] 표를 "
                           "이번 세션에서 직접 렌더링해 재확인 — items 47-51 값이 마스터와 정확히 일치.",
}


def main():
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    records = {(r["code"], r["quarter"]): r for r in data["records"]}
    applied, wrongdoc = 0, 0

    for key, override in VISION_OVERRIDES.items():
        r = records.get(key)
        if r is None:
            print(f"WARN: {key} not found in records, skipping")
            continue
        for k, v in override.items():
            if k == "_evidence":
                continue
            r[k] = v
        r["format"] = (r.get("format") or "NONE") + "+vision"
        r["evidence"]["vision"] = override["_evidence"]
        r["unknown_reason"] = None if r.get("TFI") != "UNKNOWN" else r.get("unknown_reason")
        applied += 1

    for key, note in WRONG_DOCUMENT.items():
        r = records.get(key)
        if r is None:
            print(f"WARN: {key} not found in records, skipping")
            continue
        r["unknown_reason"] = "WRONG_OR_BUNDLED_SOURCE_DOCUMENT: " + note
        r["evidence"]["wrong_document_note"] = note

    retracted = 0
    for key, note in RETRACTED_WRONG_DOCUMENT.items():
        r = records.get(key)
        if r is None:
            print(f"WARN: {key} not found in records, skipping")
            continue
        r["unknown_reason"] = note
        r["evidence"].pop("wrong_document_note", None)
        r["evidence"]["retraction"] = note
        retracted += 1

    structabsent = 0
    for key, note in STRUCTURALLY_ABSENT.items():
        r = records.get(key)
        if r is None:
            print(f"WARN: {key} not found in records, skipping")
            continue
        r["unknown_reason"] = "STRUCTURALLY_ABSENT_FROM_DISCLOSED_SECTION: " + note
        r["evidence"]["structurally_absent_note"] = note
        structabsent += 1

    # recompute _meta counts
    KNOWN_KINDS = ("TFI", "RPT", "TAC", "TIR", "TER", "TIRR", "PCA_DEFER")
    counts = {k: {"O": 0, "X": 0, "NA": 0, "UNKNOWN": 0} for k in KNOWN_KINDS}
    unknown_reasons: dict[str, int] = {}
    fmt_counts: dict[str, int] = {}
    for r in records.values():
        for k in KNOWN_KINDS:
            counts[k][r[k]] += 1
        fmt_counts[r["format"] or "NONE"] = fmt_counts.get(r["format"] or "NONE", 0) + 1
        if r["unknown_reason"]:
            unknown_reasons[r["unknown_reason"]] = unknown_reasons.get(r["unknown_reason"], 0) + 1
    data["_meta"]["counts_by_kind"] = counts
    data["_meta"]["format_counts"] = fmt_counts
    data["_meta"]["unknown_reason_counts"] = unknown_reasons
    data["_meta"]["vision_overrides_applied"] = applied
    data["_meta"]["wrong_document_flagged"] = wrongdoc
    data["_meta"]["wrong_document_retracted"] = retracted
    data["_meta"]["structurally_absent_flagged"] = structabsent
    data["records"] = sorted(records.values(), key=lambda r: (r["code"], r["quarter"]))

    JSON_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"applied {applied} vision overrides, flagged {wrongdoc} wrong-document buckets, "
          f"retracted {retracted} previously-flagged wrong-document buckets, "
          f"{structabsent} structurally-absent buckets")
    print(json.dumps(counts, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
