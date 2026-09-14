# -*- coding: utf-8 -*-
"""jp 레인 — census not_yet/not_found 회사 중 EDINET 有価証券報告書 본문에 ESR 이
실제로 실려 있는지 훑는 스윕. 오케스트레이터 지시(inbox 없이 직접 프롬프트로 발주,
2026-09-14) 산출물이며 census/jesr_esr.json/마스터는 건드리지 않는다 — 증거만 만든다.

대상
----
`fy2025_esr_census_20260912.csv` 의 `fy2025_esr_status` in (not_yet, not_found) 이면서
`jp_insurers.csv` 에 실제 EDINET 코드(`E?????`, "none" 아님)가 있는 회사. 코드 미확보사는
건드리지 않는다(다른 에이전트가 병렬로 해소 중).

방법
----
1. `J-ESR/raw/edinet/scan_*.json` (기존 4개 + 이 라운드에 새로 만든 2026-04-01~오늘)에서
   대상 코드의 FY2025(period_end=2026-03-31) docTypeCode 120(有報)/130(訂正有報) 문서를 찾는다.
2. EDINET API 로 zip(type=1, XBRL 一式)을 받는다(캐시: `J-ESR/raw/edinet/<docID>.zip`).
3. `PublicDoc/*.htm` 텍스트에서 ESR 라벨(도메인 문서 §3 정본, `check_esr_in_source.ESR_LABELS_STRONG`
   재사용 — 라벨을 다시 타이핑하지 않는다) 동반 산문 조각을 뽑고, 조각마다 값(%)·한정어(§3 정본
   `ADJUSTED_QUALIFIERS` 재사용)·연결/단체 표지·산정기준 표지를 같이 읽는다.
4. 한정어 없는 조각의 값 = 헤드라인 후보. 전부 한정어면 `all_qualified`, 라벨 자체가 없으면
   `no_esr_in_doc`, 문서를 못 찾으면 `doc_not_found`, 받다가 죽으면 `error`.

산출: `J-ESR/edinet_esr_sweep.json` (봉투 `checked_at`/`scope`/`rows`, 기존 증거 파일과 같은 모양).
10개 회사마다 디스크 저장 — CLAUDE.md §4 처리규칙(회사단위 통째 제외 금지)을 지킨다.

사용법
------
  python3 J-ESR/edinet_esr_sweep.py
  python3 J-ESR/edinet_esr_sweep.py --code E03823   # 디버그 1건
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
import unicodedata
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jesr_http  # noqa: E402
# 라벨·한정어 목록은 §3 정본의 기계본을 그대로 재사용한다 — 여기서 다시 타이핑하지 않는다
# (K-ICS 상관행렬을 재타이핑하지 말라는 CLAUDE.md 관행과 같은 이유).
import check_esr_in_source as _src  # noqa: E402

HERE = Path(__file__).resolve().parent
RAW_EDINET = HERE / "raw" / "edinet"
CENSUS_CSV = HERE / "fy2025_esr_census_20260912.csv"
INSURERS_CSV = HERE / "jp_insurers.csv"
OUT_JSON = HERE / "edinet_esr_sweep.json"
API = "https://api.edinet-fsa.go.jp/api/v2"
FY2025_PERIOD_END = "2026-03-31"

VERDICTS = ("found", "no_esr_in_doc", "doc_not_found", "error")

SCOPE_GROUP_RE = re.compile(r"連結")
SCOPE_SOLO_RE = re.compile(r"単体")

BASIS_PATTERNS = (
    ("regulatory_standard", re.compile(r"標準(的)?(手法|モデル|式)|標準式")),
    ("internal_model", re.compile(r"内部モデル")),
    ("internal_management", re.compile(r"内部管理")),
)

DATE_RE = re.compile(r"(20\d\d)年(\d{1,2})月(\d{1,2})日")

#: "100%" 가 회사 실측값이 아니라 **규제 최저기준 정의문/유예공시 상투문구**로 붙는 경우가
#: 실측에서 반복됐다(三井住友海上·あいおい 니세이도와·共栄火災 — 전부 "당해 실적은 2026年10月末
#: 開示 예정" + "100%는 상회할 전망" 뿐이고 실수치가 없다). 값=100 이고 아래 표지가 같이 있으면
#: **실측 공시가 아니라 정의/유예문구**로 보고 헤드라인 후보에서 뺀다(candidates 목록엔 남긴다 —
#: 증거를 지우지 않는다, 헤드라인 선정에서만 뺀다).
BOILERPLATE_100_MARKERS = ("早期是正措置", "規制上の最低水準", "を上回る見込み", "以上であれば",
                            "開示は", "公表予定", "2026年10月末", "経営の健全性を判断するため")


def is_boilerplate_100(frag: str, pct: float) -> bool:
    if pct != 100.0:
        return False
    return any(m in frag for m in BOILERPLATE_100_MARKERS)


def log(msg: str) -> None:
    sys.stdout.buffer.write((msg + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()


def norm_text(s: str) -> str:
    return unicodedata.normalize("NFKC", s or "")


def strip_tags(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"[\s　]+", " ", text)


def load_targets() -> list[dict]:
    """census not_yet/not_found × jp_insurers 실제 edinet_code 조인."""
    with CENSUS_CSV.open(encoding="utf-8-sig", newline="") as fh:
        census = list(csv.DictReader(fh))
    with INSURERS_CSV.open(encoding="utf-8-sig", newline="") as fh:
        insurers = list(csv.DictReader(fh))
    by_en: dict[str, list[dict]] = {}
    for row in insurers:
        by_en.setdefault(row["company_en"].strip(), []).append(row)

    targets = []
    for c in census:
        status = (c.get("fy2025_esr_status") or "").strip()
        if status not in ("not_yet", "not_found"):
            continue
        en = c["company_en"].strip()
        ins_rows = by_en.get(en, [])
        code = None
        eligible = None
        for m in ins_rows:
            v = (m.get("edinet_code") or "").strip()
            if v and v.lower() != "none" and v.upper().startswith("E"):
                code = v
                eligible = (m.get("edinet_eligible") or "").strip()
                break
        if not code:
            continue
        targets.append({
            "company_jp": c["company_jp"], "company_en": en,
            "edinet_code": code, "edinet_eligible": eligible,
            "census_status": status, "sector": c.get("sector", ""),
            "category": c.get("category", ""),
        })
    return targets


def load_scan_hits(codes: set[str]) -> dict[str, list[dict]]:
    """모든 scan_*.json 을 합쳐 코드별 FY2025(120/130, period_end=2026-03-31) 히트만 남긴다."""
    by_code: dict[str, list[dict]] = {}
    for path in sorted(RAW_EDINET.glob("scan_*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for h in data.get("hits", []):
            code = h.get("edinet_code")
            if code not in codes:
                continue
            if h.get("doc_type_code") not in ("120", "130"):
                continue
            if h.get("period_end") != FY2025_PERIOD_END:
                continue
            by_code.setdefault(code, []).append(h)
    # 회사당 doc_id 중복 제거(같은 파일이 여러 scan 구간에 걸칠 수 있다)
    for code, hits in by_code.items():
        seen = set()
        uniq = []
        for h in sorted(hits, key=lambda x: x.get("submit_datetime") or ""):
            if h["doc_id"] in seen:
                continue
            seen.add(h["doc_id"])
            uniq.append(h)
        by_code[code] = uniq
    return by_code


def fetch_doc_zip(key: str, doc_id: str) -> bytes:
    RAW_EDINET.mkdir(parents=True, exist_ok=True)
    cached = RAW_EDINET / f"{doc_id}.zip"
    if cached.exists() and cached.stat().st_size > 0:
        return cached.read_bytes()
    url = f"{API}/documents/{doc_id}?type=1&Subscription-Key={key}"
    resp = requests.get(url, timeout=180, verify=jesr_http.verify_setting())
    resp.raise_for_status()
    cached.write_bytes(resp.content)
    return resp.content


def public_doc_texts(blob: bytes) -> list[tuple[str, str]]:
    """[(파일명, 정규화 텍스트)] — PublicDoc(공시 본문)만. AuditDoc 등은 제외."""
    zf = zipfile.ZipFile(io.BytesIO(blob))
    out = []
    for name in zf.namelist():
        if not name.lower().endswith((".htm", ".html")):
            continue
        if "PublicDoc" not in name:
            continue
        text = norm_text(strip_tags(zf.read(name).decode("utf-8", errors="ignore")))
        if text.strip():
            out.append((name, text))
    return out


def doc_as_of(all_text: str) -> str | None:
    """문서 전역에서 '2026年3月31日' 류 결산기준일을 찾는다(최빈값이 아니라 첫 매치 — 有報
    표지는 대개 대상기간 말일을 가장 먼저 언급한다)."""
    for m in DATE_RE.finditer(all_text):
        y, mo, d = m.groups()
        if y == "2026" and mo == "3":
            return f"2026-03-31"
    return None


def classify_scope(frag: str) -> str:
    has_g = bool(SCOPE_GROUP_RE.search(frag))
    has_s = bool(SCOPE_SOLO_RE.search(frag))
    if has_g and not has_s:
        return "group"
    if has_s and not has_g:
        return "solo"
    if has_g and has_s:
        return "both_mentioned"
    return "unclear"


def classify_basis(frag: str, wide: str) -> tuple[str, str]:
    """조각 안에서 먼저, 없으면 조각을 포함하는 넓은 창(앞뒤 400자)에서 산정기준 표지를 찾는다."""
    for basis, pat in BASIS_PATTERNS:
        m = pat.search(frag)
        if m:
            return basis, frag.strip()[:160]
    for basis, pat in BASIS_PATTERNS:
        m = pat.search(wide)
        if m:
            start = max(0, m.start() - 60)
            return basis, wide[start:m.end() + 60].strip()[:160]
    return "unstated", ""


#: iXBRL 본문 htm 은 PDF 의 "페이지" 개념이 없다 — 한 파일이 통째로 수만 자다. `check_esr_in_source`
#: 의 구기준 라벨(§3 「同じページ」) 동시출현 판정을 파일 전체에 그대로 적용하면 동떨어진 절(임원
#: 보수표·구규제 설명 등)의 우연한 「ソルベンシー・マージン比率」가 전부 라벨로 잡힌다(실측,
#: 第一ライフグループ 시험추출에서 10건 중 6건이 이 오탐). "같은 페이지" 를 로컬 창으로 근사한다.
LOCAL_WINDOW = 1500


def _fragments_with_offsets(text: str) -> list[tuple[str, int]]:
    """`。`·개행으로 자른 조각과 그 시작 offset. `_src._prose_fragments` 와 같은 분할 규칙."""
    out = []
    pos = 0
    for piece in re.split(r"([。\n])", text):
        if piece in ("。", "\n"):
            pos += len(piece)
            continue
        if piece.strip():
            start = text.find(piece, pos)
            out.append((piece, start if start >= 0 else pos))
        pos += len(piece)
    return out


def extract_company(blob: bytes) -> dict:
    """zip 안 PublicDoc 전체에서 ESR 라벨동반 조각을 전부 뽑아 후보/헤드라인을 가른다."""
    docs = public_doc_texts(blob)
    all_candidates: list[dict] = []
    label_seen = False
    label_sentences: list[str] = []
    full_text_all = "\n".join(t for _, t in docs)
    as_of = doc_as_of(full_text_all)

    for fname, text in docs:
        has_strong_file = any(_src.norm_text(lab) in text for lab in _src.ESR_LABELS_STRONG)
        has_ambig_file = _src.norm_text(_src.ESR_LABEL_AMBIGUOUS) in text
        if not (has_strong_file or has_ambig_file):
            continue
        for frag, off in _fragments_with_offsets(text):
            has_strong = any(lab in frag for lab in _src.ESR_LABELS_STRONG)
            local = text[max(0, off - LOCAL_WINDOW):off + len(frag) + LOCAL_WINDOW]
            has_ambig = (_src.ESR_LABEL_AMBIGUOUS in frag
                         and any(k in local for k in _src.ESR_NEW_STANDARD_MARKERS))
            if not (has_strong or has_ambig):
                continue
            label_seen = True
            # 라벨 위치 근접창(§4c-pre 문턱 그대로, PROXIMITY_CHARS=200)만 값으로 인정한다 —
            # 조각 전체를 훑으면 표가 개행 없이 한 조각으로 뭉개졌을 때(第一ライフグループ
            # 임원보수 KPI 표, 2026-09-14 실측) 무관한 셀의 %까지 다 잡힌다.
            label_positions = [m.start() for lab in _src.ESR_LABELS_STRONG
                                for m in re.finditer(re.escape(lab), frag)]
            if has_ambig:
                label_positions += [m.start() for m in re.finditer(
                    re.escape(_src.ESR_LABEL_AMBIGUOUS), frag)]
            vals = []
            for raw in _src.FRAG_PCT_RE.finditer(frag):
                fv = float(raw.group(1))
                if not (_src.ADJ_PCT_MIN <= fv <= _src.ADJ_PCT_MAX):
                    continue
                if any(abs(raw.start() - lp) <= _src.PROXIMITY_CHARS for lp in label_positions):
                    vals.append("%g" % fv)
            if not vals:
                if len(label_sentences) < 3:
                    label_sentences.append(frag.strip()[:200])
                continue
            quals = [q for q in _src.ADJUSTED_QUALIFIERS if q in frag]
            basis, basis_ev = classify_basis(frag, local)
            scope = classify_scope(frag)
            if scope == "unclear":
                scope = classify_scope(local)
            label_txt = ("ESR" if has_strong and "ESR" in frag else
                         (next((lab for lab in _src.ESR_LABELS_STRONG if lab in frag), None)
                          or _src.ESR_LABEL_AMBIGUOUS + "(신기준 근접표지)"))
            for v in vals:
                all_candidates.append({
                    "pct": float(v), "label": label_txt, "qualifiers": quals,
                    "scope": scope, "basis": basis, "basis_evidence": basis_ev,
                    "sentence": frag.strip()[:200], "source_file": fname, "as_of": as_of,
                    "boilerplate_100": is_boilerplate_100(frag, float(v)),
                })

    if not all_candidates:
        if label_seen:
            ev = ("ESR 라벨은 있으나 동반 문장에 수치(%)가 없다(정의·방법론 서술만) — "
                  + " / ".join(label_sentences))
        else:
            ev = "ESR 라벨 자체가 본문 PublicDoc 어디에도 없다"
        return {"verdict": "no_esr_in_doc", "candidates": [], "headline_candidates": [],
                "evidence": ev}

    # 값별로 묶어 "한정어 없고 상투문구(100%규제최저) 도 아닌 조각이 하나라도 있는 값" = 헤드라인 후보
    real = [c for c in all_candidates if not c["boilerplate_100"]]
    by_val: dict[float, list[dict]] = {}
    for c in real:
        by_val.setdefault(c["pct"], []).append(c)
    headline = []
    for v, cs in by_val.items():
        unq = [c for c in cs if not c["qualifiers"]]
        if unq:
            headline.append(unq[0])
    if not headline and not real:
        # 전부 "100%가 규제 최저기준" 상투문구뿐 — 실수치 미공시(대개 2026-10-31 유예)
        ev = ("ESR/구기준 라벨은 있으나 동반 수치는 전부 '규제 최저기준 100%' 정의·유예공시 "
              "상투문구뿐, 실제 자사 수치는 없다 — " + all_candidates[0]["sentence"])
        return {"verdict": "no_esr_in_doc", "candidates": all_candidates,
                "headline_candidates": [], "evidence": ev}
    verdict = "found"
    notes = None
    if not headline:
        notes = "라벨동반 조각은 있으나 전부 한정어 — 헤드라인 미확정(사람 판단 필요)"
    return {"verdict": verdict, "candidates": all_candidates,
            "headline_candidates": sorted(headline, key=lambda c: c["pct"]),
            "evidence": notes or f"헤드라인 후보 {len(headline)}건"}


def process_one(key: str, target: dict, hits: list[dict]) -> dict:
    row = {**target, "doc_id": None, "doc_type_code": None, "submit_datetime": None,
           "period_end": None, "edinet_doc_url": None}
    if not hits:
        row["verdict"] = "doc_not_found"
        row["evidence"] = (f"scan 인덱스(2025-06~2026-09 다수 구간)에 FY2025(120/130, "
                            f"period_end={FY2025_PERIOD_END}) 有報가 없다"
                            + ("" if target["edinet_eligible"] == "yes"
                               else f" — edinet_eligible={target['edinet_eligible']}(有報 의무 없음 가능성)"))
        row["candidates"] = []
        row["headline_candidates"] = []
        return row
    # 訂正(130)이 있으면 최신을 쓴다(본문 전량 재게재) — 없으면 최초 120
    hit = hits[-1]
    row.update({"doc_id": hit["doc_id"], "doc_type_code": hit["doc_type_code"],
                "submit_datetime": hit["submit_datetime"], "period_end": hit["period_end"],
                "edinet_doc_url": f"https://disclosure2.edinet-fsa.go.jp/WZEK0040.html?"
                                  f"uji.bean=ee.bean.W1E63011.EEW1E63011Bean&{hit['doc_id']}"})
    try:
        blob = fetch_doc_zip(key, hit["doc_id"])
    except Exception as exc:
        row["verdict"] = "error"
        row["evidence"] = f"{type(exc).__name__}: {str(exc)[:200]}"
        row["candidates"] = []
        row["headline_candidates"] = []
        return row
    try:
        res = extract_company(blob)
    except Exception as exc:
        row["verdict"] = "error"
        row["evidence"] = f"추출 중 예외 {type(exc).__name__}: {str(exc)[:200]}"
        row["candidates"] = []
        row["headline_candidates"] = []
        return row
    row.update(res)
    return row


def save(rows: list[dict], scope: str) -> None:
    payload = {
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "scope": scope,
        "source": "EDINET 有価証券報告書(docTypeCode 120)/訂正有報(130), PublicDoc 본문",
        "rows_count": len(rows),
        "summary": {v: sum(1 for r in rows if r["verdict"] == v) for v in VERDICTS},
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log(f"[save] {OUT_JSON} ({len(rows)}건)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", default=os.environ.get("EDINET_KEY"))
    ap.add_argument("--code", action="append", default=[], help="디버그: 특정 edinet_code 만")
    args = ap.parse_args()
    if not args.key:
        log("[FATAL] EDINET_KEY 없음")
        return 2

    targets = load_targets()
    if args.code:
        targets = [t for t in targets if t["edinet_code"] in set(args.code)]
    codes = {t["edinet_code"] for t in targets}
    log(f"[targets] not_yet/not_found × edinet_code 실보유 {len(targets)}건 · 고유코드 {len(codes)}")
    scan_hits = load_scan_hits(codes)

    rows: list[dict] = []
    for i, t in enumerate(targets, 1):
        hits = scan_hits.get(t["edinet_code"], [])
        log(f"[{i}/{len(targets)}] {t['edinet_code']} {t['company_en']} "
            f"({t['company_jp']}) hits={len(hits)}")
        row = process_one(args.key, t, hits)
        rows.append(row)
        hc = row.get("headline_candidates") or []
        hc_str = ", ".join(f"{h['pct']}%({h['scope']},{h['basis']})" for h in hc)
        log(f"   -> {row['verdict']}  headline=[{hc_str}]  {row.get('evidence', '')[:100]}")
        if i % 10 == 0:
            save(rows, scope="partial_in_progress")

    save(rows, scope="all" if not args.code else "partial")

    log("")
    log("[summary] " + " · ".join(f"{k}={v}" for k, v in
        ({v: sum(1 for r in rows if r["verdict"] == v) for v in VERDICTS}).items()))
    for r in rows:
        if r["verdict"] == "found" and r.get("headline_candidates"):
            for h in r["headline_candidates"]:
                log(f"  FOUND {r['company_en']}: {h['pct']}% scope={h['scope']} "
                    f"basis={h['basis']} as_of={h.get('as_of')} doc={r['doc_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
