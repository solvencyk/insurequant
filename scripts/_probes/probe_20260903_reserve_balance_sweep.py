# -*- coding: utf-8 -*-
"""경영공시 '해약환급금준비금 등의 적립' 표에서 법정준비금 4종의 **잔액**을 전사·전분기 추출.

owner 결정 2026-09-03: 잔액 = **기적립액 + 적립예정액**. 경영공시 PDF 하나만 본다(DART 아님).

세 가지 형식이 섞여 있다(같은 회사 안에서도 분기마다 다르다):
  A. 표에 두 행     — '해약환급금준비금 기적립액 794' / '(해약환급금준비금 적립예정액) 189'
  B. 표에 한 행     — '해약환급금준비금 773' (예정액은 표에 없음)
  C. B + 주석 문장  — '추가 적립예정액은 해약환급금준비금 66억원 … 적립할 경우 839억원'
C 는 문장이 알려주는 **합계값을 우선 채택**한다(발행사가 계산한 잔액이라 우리가 더하다 틀릴
여지가 없다). 합계 문장이 없으면 기적립+예정을 더하되 환입(음수) 부호를 지킨다.

owner 지적 2026-09-03: 비교 허용오차는 **±50백만(0.5억) 절대값**이다. 경영공시가 억원
반올림이라 정당한 차이는 그뿐이고, 상대오차(0.5%/1%)를 쓰면 큰 항목에서 수억짜리 실오차가
샌다(삼성생명 2026.1Q 대손준비금 579백만이 실제로 그렇게 샜다).

추출은 좌표 기반이다 — 라벨 단어의 y중심 ±2.5pt 안 숫자를 x순으로. 텍스트 순서 방식은
회사·분기마다 라벨/값 순서가 뒤집혀(값이 라벨보다 먼저 오는 페이지가 있다) 한 칸씩 밀린다.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.stdout.reconfigure(encoding='utf-8')
import fitz
from _disclosure_pdf_paths import disclosure_pdfs

ITEM = {'해약환급금준비금': 5, '비상위험준비금': 6, '대손준비금': 7, '보증준비금': 8}
TOL = 50.0                      # 백만원
NUM = re.compile(r'^\(?-?[\d,]+\)?$')
DASH = ('-', '–', '—')
norm = lambda s: s.replace(' ', '').replace('\u3000', '')


def to_eok(tok):
    if tok in DASH:
        return 0.0
    v = tok.replace(',', '')
    neg = v.startswith('(') or v.startswith('-')
    v = v.strip('()-')
    if not v.isdigit():
        return None
    return -float(v) if neg else float(v)


def _rows(words):
    """y로 묶은 행 -> (라벨문자열, [x순 숫자토큰])."""
    buckets = {}
    for x0, y0, x1, y1, w, *_ in words:
        buckets.setdefault(round((y0 + y1) / 2 / 2.5), []).append((x0, w))
    out = []
    for _, ws in sorted(buckets.items()):
        ws.sort()
        label = norm(''.join(w for _, w in ws
                             if not (NUM.fullmatch(norm(w)) or norm(w) in DASH)))
        nums = [norm(w) for _, w in ws if NUM.fullmatch(norm(w)) or norm(w) in DASH]
        out.append((label, nums))
    return out


def row_vals(words, want_norm):
    """라벨이 여러 단어로 쪼개져도 잇는다. 완전일치 우선, 없으면 시작일치."""
    rows = _rows(words)
    for exact in (True, False):
        best = []
        for label, nums in rows:
            hit = (label == want_norm) if exact else (label.startswith(want_norm) and nums)
            if hit and len(nums) > len(best):
                best = nums
        if best:
            return best
    return []


def sentence_total(text, base):
    """'… 적립할 경우 … 해약환급금준비금은 839 억원' 형태의 합계값(억)."""
    pat = re.compile(r'적립(?:\(환입\))?할\s*경우.{0,120}?%s[은는]?\s*([\d,]+)\s*억' % re.escape(base), re.S)
    m = pat.search(re.sub(r'\s+', ' ', text))
    return float(m.group(1).replace(',', '')) if m else None


def sentence_pending(text, base):
    """'추가 적립(환입)예정액은 해약환급금준비금 66 억원' 형태의 예정액(억)."""
    pat = re.compile(r'적립(?:\(환입\))?예정액[은는]?.{0,80}?%s\s*(-?[\d,]+)\s*억' % re.escape(base), re.S)
    m = pat.search(re.sub(r'\s+', ' ', text))
    return float(m.group(1).replace(',', '')) if m else None


def extract(pg):
    """{item: (잔액_억, 형식)} — 형식 = A(표2행)/B(표1행)/C(표+문장)."""
    words = pg.get_text('words')
    text = pg.get_text()
    out = {}
    for base, item in ITEM.items():
        acc = row_vals(words, base + '기적립액')
        pend = row_vals(words, '(' + base + '적립예정액)') or row_vals(words, base + '적립예정액')
        if acc:                                        # 형식 A
            a = to_eok(acc[0])
            p = to_eok(pend[0]) if pend else 0.0
            if a is not None and p is not None:
                out[item] = (a + p, 'A')
            continue
        plain = row_vals(words, base) or row_vals(words, base + '(*)')
        if not plain:
            continue
        a = to_eok(plain[0])
        if a is None:
            continue
        tot = sentence_total(text, base)               # 형식 C: 합계 문장 우선
        if tot is not None:
            out[item] = (tot, 'C')
            continue
        pv = sentence_pending(text, base)
        out[item] = ((a + pv, 'C') if pv is not None else (a, 'B'))
    return out


def main():
    master = json.loads((ROOT / 'IFRS17_BS.json').read_text(encoding='utf-8'))
    mi = {(r['원보험사코드'], r['공시분기'], r['항목번호']): r['값'] for r in master}
    name = {r['원보험사코드']: r['원수사명'] for r in master}
    codes = sorted({r['원보험사코드'] for r in master})

    rows, forms, diffs, notab = [], {'A': 0, 'B': 0, 'C': 0}, [], 0
    for period in sorted((ROOT / 'data' / 'disclosure').glob('FY*')):
        q = f'{period.name[2:6]}.{period.name[-1]}Q'
        for code in codes:
            pdfs = disclosure_pdfs(period.name, code)
            if not pdfs:
                continue
            doc = fitz.open(pdfs[0])
            hit = None
            try:
                for i, pg in enumerate(doc):
                    if i < 2:
                        continue
                    t = pg.get_text()
                    if '해약환급금준비금' in t and '적립' in t and '대손준비금' in t:
                        hit = pg
                        break
                if hit is None:
                    notab += 1
                    continue
                got = extract(hit)
            finally:
                doc.close()
            for item, (eok, form) in got.items():
                forms[form] += 1
                disc = eok * 100.0
                mv = mi.get((code, q, item))
                rows.append((code, q, item, disc, mv, form))
                if mv is not None and abs(disc - mv) > TOL:
                    diffs.append((code, q, item, disc, mv, form))

    print(f'표 못 찾은 (회사,분기): {notab}')
    print(f'추출 셀 {len(rows)} · 형식 A(표2행)={forms["A"]} B(표1행)={forms["B"]} C(표+문장)={forms["C"]}')
    print(f'마스터와 ±{TOL:.0f}백만 초과 차이: **{len(diffs)}칸**\n')
    for code, q, item, disc, mv, form in sorted(diffs, key=lambda r: -abs(r[3] - r[4]))[:60]:
        print(f'  {name.get(code, code):<14} {q} item{item} [{form}] '
              f'공시={disc:>12,.0f}  마스터={mv:>12,.0f}  차이={disc-mv:>+11,.0f}')
    json.dump([{'code': c, 'quarter': q, 'item': i, 'disclosure': d, 'master': m, 'form': f}
               for c, q, i, d, m, f in rows],
              open(ROOT / 'data' / '_derived' / 'reserve_balance_sweep.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
