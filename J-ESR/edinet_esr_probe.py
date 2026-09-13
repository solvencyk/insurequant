# -*- coding: utf-8 -*-
"""EDINET 有価証券報告書 본문에서 ESR 서술을 뽑아 화면 수치와 대조한다.

왜 (2026-09-13)
---------------
키가 생겨 실측해 보니 **有報 본문에 ESR 이 서술로 들어 있다.** FY2024 probe 에서
"ESR 태그 0건" 이라 XBRL 루트를 접었던 판정은 *태그* 기준으로는 여전히 맞지만,
본문(iXBRL htm)에는 수치가 문장으로 있다 — J-ICS 신규제가 2026-03-31 부터라
FY2025 有報(2026년 6월 제출)가 첫 사이클이다.

이게 두 가지를 한꺼번에 푼다.
1. **영구 URL**. 회사 IR PDF 는 개편 때 사라진다(리허설에서 404 3건). EDINET 문서
   URL 은 안 사라지므로 1차 출처로 인용하기에 TDnet/IR PDF 보다 낫다.
2. **교차검증**. 화면에 띄운 ESR 을 감사받은 공시서류 본문과 맞춰볼 수 있다.

한계: 有報 제출의무가 있는 14사뿐이다(相互会社·비상장 자회사는 EDINET 에 없다 —
`edinet_codelist.py` 참고). 나머지는 각사 디스클로저 PDF 가 계속 1차 출처다.

사용법
------
  python J-ESR/edinet_esr_probe.py                    # 스캔 인덱스의 有報 전부
  python J-ESR/edinet_esr_probe.py --doc S100YLS8     # 한 건만
산출: J-ESR/edinet_esr_probe.json (추적) · zip 캐시는 J-ESR/raw/edinet/(gitignore)
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jesr_http  # noqa: E402

HERE = Path(__file__).resolve().parent
RAW = HERE / "raw" / "edinet"
PAGE_JSON = HERE.parent / "jp" / "jesr_esr.json"
OUT_JSON = HERE / "edinet_esr_probe.json"
API = "https://api.edinet-fsa.go.jp/api/v2"

# 본문에서 ESR 을 부르는 표기 전부. 회사마다 다르다(東京海上=エコノミック・ソルベンシー・
# レシオ, MS&AD=ESR, 第一生命=経済価値ベースのソルベンシー比率 …).
ESR_TERMS = ("ESR", "ＥＳＲ", "エコノミック・ソルベンシー", "経済価値ベースのソルベンシー",
             "経済価値ベースソルベンシー", "ソルベンシー比率")
# "…ESR は 268％" / "ESR：268%" / "268％となり" 류를 같은 문장 안에서만 잡는다.
PCT_NEAR_ESR = re.compile(
    r"(?:ESR|ＥＳＲ|エコノミック・ソルベンシー・レシオ|経済価値ベースのソルベンシー比率)"
    r"[^。]{0,120}?(\d{2,3}(?:\.\d)?)\s*[％%]"
)
TARGET_RE = re.compile(r"(?:ターゲット|目標)[^。]{0,60}?(\d{2,3})\s*[％%]\s*(以上|～|~|-)?")


def log(msg: str) -> None:
    sys.stdout.buffer.write((msg + "\n").encode("utf-8", errors="replace"))
    sys.stdout.buffer.flush()


def strip_tags(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"[\s　]+", " ", text)


def fetch_doc(key: str, doc_id: str) -> bytes:
    """문서 zip(type=1: XBRL 一式). 캐시가 있으면 그대로 쓴다."""
    RAW.mkdir(parents=True, exist_ok=True)
    cached = RAW / f"{doc_id}.zip"
    if cached.exists():
        return cached.read_bytes()
    url = f"{API}/documents/{doc_id}?type=1&Subscription-Key={key}"
    resp = requests.get(url, timeout=180, verify=jesr_http.verify_setting())
    resp.raise_for_status()
    cached.write_bytes(resp.content)
    return resp.content


def extract_esr(blob: bytes) -> dict:
    """zip 안 본문에서 ESR 문장·수치를 뽑는다."""
    zf = zipfile.ZipFile(io.BytesIO(blob))
    sentences: list[str] = []
    pcts: list[float] = []
    targets: list[str] = []
    for name in zf.namelist():
        if not name.lower().endswith((".htm", ".html")):
            continue
        if "/PublicDoc/" not in name and "PublicDoc" not in name:
            continue
        text = strip_tags(zf.read(name).decode("utf-8", errors="ignore"))
        if not any(t in text for t in ESR_TERMS):
            continue
        for chunk in text.split("。"):
            if any(t in chunk for t in ESR_TERMS):
                chunk = chunk.strip()
                if chunk and chunk not in sentences:
                    sentences.append(chunk + "。")
        for m in PCT_NEAR_ESR.finditer(text):
            pcts.append(float(m.group(1)))
        for m in TARGET_RE.finditer(text):
            targets.append(m.group(0).strip())
    return {
        "esr_pct_candidates": sorted(set(pcts)),
        "target_mentions": sorted(set(targets))[:5],
        "sentences": sentences[:8],
        "sentence_count": len(sentences),
    }


def page_records() -> dict[str, dict]:
    if not PAGE_JSON.exists():
        return {}
    data = json.loads(PAGE_JSON.read_text(encoding="utf-8"))
    return {r["company_jp"]: r for r in data.get("records", [])}


def main() -> int:
    ap = argparse.ArgumentParser(description="EDINET 有報 ESR 대조")
    ap.add_argument("--key", default=os.environ.get("EDINET_KEY"))
    ap.add_argument("--scan", default=None, help="스캔 인덱스 json (기본: 가장 최근 scan_*.json)")
    ap.add_argument("--doc", help="docID 한 건만")
    ap.add_argument("--out", default=str(OUT_JSON))
    args = ap.parse_args()
    if not args.key:
        log("[FATAL] EDINET_KEY 없음")
        return 2

    scans = sorted(RAW.glob("scan_*.json"))
    if args.scan:
        scan_path = Path(args.scan)
    elif scans:
        scan_path = scans[-1]
    else:
        log("[FATAL] 스캔 인덱스가 없다 — 먼저 jesr_edinet_fetch.py --scan")
        return 2
    hits = json.loads(scan_path.read_text(encoding="utf-8"))["hits"]
    if args.doc:
        hits = [h for h in hits if h["doc_id"] == args.doc]
    # 訂正有報(130)이 있으면 그쪽이 최신이지만, 본문 전량 재게재라 원본과 같이 본다.
    hits = [h for h in hits if h["doc_type_code"] in ("120", "130")]

    page = page_records()
    rows = []
    for h in hits:
        log(f"[GET] {h['edinet_code']} {h['company_jp']} {h['doc_id']} ({h['doc_description'][:30]})")
        try:
            blob = fetch_doc(args.key, h["doc_id"])
        except Exception as exc:
            log(f"   ERROR {exc}")
            rows.append({**h, "status": "fetch_error", "error": str(exc)})
            continue
        found = extract_esr(blob)
        rec = page.get(h["company_jp"])
        row = {
            "edinet_code": h["edinet_code"],
            "company_jp": h["company_jp"],
            "doc_id": h["doc_id"],
            "doc_type_code": h["doc_type_code"],
            "submit_datetime": h["submit_datetime"],
            "period_end": h["period_end"],
            "edinet_doc_url": f"https://disclosure2.edinet-fsa.go.jp/WZEK0040.html?"
                              f"uji.bean=ee.bean.W1E63011.EEW1E63011Bean&{h['doc_id']}",
            "page_esr_pct": (rec or {}).get("esr_pct"),
            "page_source_url": (rec or {}).get("source_url"),
            **found,
        }
        cands = found["esr_pct_candidates"]
        if rec and rec.get("esr_pct") is not None and cands:
            row["agrees_with_page"] = any(abs(c - float(rec["esr_pct"])) <= 0.5 for c in cands)
        else:
            row["agrees_with_page"] = None
        rows.append(row)
        log(f"   ESR 후보 {cands} · 문장 {found['sentence_count']}개 · 화면 {row['page_esr_pct']}"
            f" · 일치 {row['agrees_with_page']}")

    payload = {
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "scan_index": scan_path.name,
        "docs": len(rows),
        "with_esr_text": sum(1 for r in rows if r.get("sentence_count")),
        "mismatch": [r["company_jp"] for r in rows if r.get("agrees_with_page") is False],
        "rows": rows,
    }
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log(f"\n[out] {args.out} · 有報 {len(rows)}건 중 ESR 서술 {payload['with_esr_text']}건 "
        f"· 화면과 불일치 {len(payload['mismatch'])}건 {payload['mismatch']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
