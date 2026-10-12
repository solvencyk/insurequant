# -*- coding: utf-8 -*-
"""Registry text-level edits (keeps the hand-formatted one-line-per-security layout)."""
import io, sys
from pathlib import Path
P = Path("data/bonds/capital_tier_registry.json")
t = P.read_text(encoding="utf-8")

def sub(old, new, count=1):
    global t
    assert t.count(old) == count, (t.count(old), old[:80])
    t = t.replace(old, new)

TK = "owner 확정 2026-10-12 채팅(티켓 20261012T2030Z 「분류 확정」)"

# --- header: new fields + dates
sub('"updated": "2026-10-12",', '"updated": "2026-10-12 (재공개 라운드: 하나생명·푸본·농협생명·코리안리 확정, issuer_type 신설)",')
sub('"unconfirmed_policy"',
    '"issuer_type_policy": "증권별 선택 필드 issuer_type = 발행사 K-ICS 표(항목 6·13-49·2·3 시계열)가 실제로 그 증권을 다룬 형. type(우리 분류, 소진율에 쓴다)과 다를 때만 적는다. forward 모델(scripts/forward_capital_simulation.py)의 **기본자본 경로**는 기준시점 기본자본이 회사 공시값이라 issuer_type 을 우선해 콜 차감 계정을 정하고(없으면 type), 그 회사 전망 행에 baseline_basis_flag=true 와 우리 분류 기준 대체 경로(basic_ratio_by_type_pct)를 같이 싣는다. 총자본(지급여력비율) 경로는 type 과 무관하다.",\n  "unconfirmed_policy"')

# --- 하나손해 (이미 tier2): 근거에 owner 확정 추가
sub('"evidence": "메모 §3.2: 2024.2Q 항목 6 +1,000 일 때 X +974(기본자본형이면 한도 266.7 초과분 +733) = 보완자본형."',
    '"evidence": "메모 §3.2: 2024.2Q 항목 6 +1,000 일 때 X +974(기본자본형이면 한도 266.7 초과분 +733) = 보완자본형. ' + TK + ': 스텝업은 없으나 배당가능이익이 없어 기본자본 요건 불충족 -> 보완자본형."')
sub('"evidence": "메모 §3.2: 2026.2Q 항목 6 +999 일 때 X +992 - 같은 모양 = 보완자본형. 채권원장(2025-12-31 기준)에는 아직 없다."',
    '"evidence": "메모 §3.2: 2026.2Q 항목 6 +999 일 때 X +992 - 같은 모양 = 보완자본형. 채권원장(2025-12-31 기준)에는 아직 없다. ' + TK + ': 2026-06 약 1,000억도 같은 이유로 보완자본형."')

# --- DB손해 5건: owner 확정 문구
sub('"evidence": "업계 최초 스텝업 없는 기본자본 신종자본증권, 신평사 비조건부 평가',
    '"evidence": "' + TK + ': DB손보 신종 5건 = 기본자본형(스텝업 없음, 국내 유일 기본자본 요건 충족). 업계 최초 스텝업 없는 기본자본 신종자본증권, 신평사 비조건부 평가')

# --- 하나생명: tier1 -> tier2 (+issuer_type)
sub('"type": "tier1", "type_unconfirmed": false, "evidence": "메모 §3.2: X(1,251~1,884) < 항목 6(1,799) - 한도 초과분만 재분류 = 기본자본형. a5: 보완자본형이면 13개 분기 중 12개에서 X 가 모자람(산술상 불가능)."}',
    '"type": "tier2", "type_unconfirmed": false, "issuer_type": "tier1", "evidence": "' + TK + ': 하나생명 제1회(1,800억, 2023-03-31)는 스텝업 구조 -> 보완자본형(기본자본 요건 불충족). 발행사 K-ICS 표는 다르게 다룬다: 메모 §3.2 X(1,251~1,884) < 항목 6(1,799) = 한도 초과분만 보완자본으로 재분류(나머지는 기본자본), 발행 직후 항목 47(1,885) < 액면. census 1차(c9)도 발행사 처리를 기본자본형으로 읽음(확정도 b). 즉 우리 분류(type=tier2)와 발행사 실제 처리(issuer_type=tier1)가 어긋난다 -> forward 모델은 기본자본 경로를 발행사 처리 기준으로 계산하고 baseline_basis_flag 를 단다."}')
sub('"note": "소진율 = 1,799 / SCR x 10% = 238.2%(초과분은 보완자본 재분류)."',
    '"note": "소진율 = 기본자본형 신규 0 / SCR x 10% = 0%(재분류 2026-10-12: 종전 238.2%). 발행사는 일부를 기본자본으로 인정(issuer_type=tier1)."')

# --- 푸본 600억 -> tier2 확정
sub('"issue_date": "2023-02-28", "amount_eok": 600.0, "amount_basis": "채권원장 잔액", "type": "tier1", "type_unconfirmed": true, "evidence": "보수적 상한(기본자본형, 분모 10%).", "unconfirmed_reason": "공개 자료(WebSearch 2026-10-12: 2023-02 신종 600억 발행 보도만 있음)에 스텝업·이자지급 재량 조건이 없다. 10% 한도(1,291~1,559억)가 신규분(600~650억)보다 늘 커서 한도 초과 재분류가 생기지 않아 시계열 X·실현가능성 검정으로 형을 가를 수 없다(a5: 두 가설 모두 가능). 확정에는 발행조건(사모 계약서 또는 사업보고서 주석의 금리조정 조항)이 필요하다."}',
    '"issue_date": "2023-02-28", "amount_eok": 600.0, "amount_basis": "채권원장 잔액", "type": "tier2", "type_unconfirmed": false, "evidence": "' + TK + ': 푸본현대 신규 신종 = 보완자본형(사업보고서 스텝업 문구). 분류 census 1차(data/_derived/capital_securities_classification_census_20261012/census_securities.csv, 확정도 a, 근거 issuer_filing(indirect)) 일치. 종전 미확정 상한 처리 해제."}')
sub('"note": "미확정: 소진율 범위 17.3%(신규분이 보완자본형일 때) ~ 42.1%(기본자본형일 때). 상한 42.1% 를 싣는다."',
    '"note": "소진율 = max(기발행 400 / SCR x 15% = 17.3%, 기본자본형 신규 50 / SCR x 10% = 3.2%) = 17.3%. 600억은 보완자본형 확정, 항목 6 - 항목 53 - 600 = 50억(2024.4Q~, 채권원장에 없음)만 미확정이라 type_unconfirmed 를 남긴다(결속하지 않아 숫자에는 영향 없음)."')

# --- 농협생명 제5회 -> tier2 확정
sub('"issue_date": "2023-01-31", "amount_eok": 2500.0, "amount_basis": "채권원장 잔액", "type": "tier1", "type_unconfirmed": true, "evidence": "보수적 상한(기본자본형, 분모 10%).", "unconfirmed_reason": "공개 자료(WebSearch 2026-10-12)는 2023년 초 2,500억 신종 발행(대주주 NH농협금융지주 대상 보도)과 지급여력비율 개선만 전하고 스텝업·이자지급 재량 조건은 없다. 10% 한도(2,749~4,229억)가 신규분 2,500억보다 늘 커서 시계열 X·실현가능성 검정으로 형을 가를 수 없다(a5: 두 가설 모두 가능). 확정에는 발행조건(사모 계약서 또는 사업보고서 주석)이 필요하다."}',
    '"issue_date": "2023-01-31", "amount_eok": 2500.0, "amount_basis": "채권원장 잔액", "type": "tier2", "type_unconfirmed": false, "evidence": "' + TK + ': 농협생명 신규 신종 = 보완자본형(사업보고서 스텝업 문구). census 1차(확정도 a, 근거 issuer_filing) 일치. 종전 미확정 상한 처리 해제."}')
sub('"note": "미확정: 소진율 범위 48.5%(보완자본형일 때) ~ 72.7%(기본자본형일 때). 상한 72.7% 를 싣는다."',
    '"note": "소진율 = 기발행 2,500 / SCR x 15% = 48.5%(제5회 2,500억은 보완자본형 확정이라 기본자본 자본증권에서 제외; 종전 상한 72.7%)."')

# --- 코리안리 제5·6회 -> tier2 확정
sub('"issue_date": "2023-03-16", "amount_eok": 2500.0, "amount_basis": "채권원장 잔액", "type": "tier1", "type_unconfirmed": true, "evidence": "보수적 상한(기본자본형, 분모 10%).", "unconfirmed_reason": "공개 자료(WebSearch 2026-10-12: 2024 차환 발행 보도 - 30년 만기·5년 콜, 신평사 등급 보고서 - 이자지급 정지 특약)에서 스텝업 조항 유무를 확인하지 못했다. 시계열 검정은 갈리지 않는다(a5·a5b): 발행사 경과조치 표에서 경과조치 효과가 2023.1Q~2024.4Q 는 SCR x 5%(경과조치 전 열에도 신종 일부가 기본자본으로 남음), 2025.1Q 부터는 기발행 신종 전액으로 바뀌어, 어느 쪽 가설도 한두 분기씩 설명이 어긋난다. 확정에는 제5회·제6회 증권신고서(투자설명서)의 금리조정(스텝업) 조항 확인이 필요하다."}',
    '"issue_date": "2023-03-16", "amount_eok": 2500.0, "amount_basis": "채권원장 잔액", "type": "tier2", "type_unconfirmed": false, "evidence": "' + TK + ': 코리안리 신규 신종 = 보완자본형(사업보고서 스텝업 문구). census 1차(확정도 a, 근거 issuer_filing) 일치. 종전 미확정 상한 처리 해제."}')
sub('"issue_date": "2024-10-11", "amount_eok": 2300.0, "amount_basis": "채권원장 잔액", "type": "tier1", "type_unconfirmed": true, "evidence": "보수적 상한(기본자본형, 분모 10%).", "unconfirmed_reason": "제5회와 같다(2019년 발행분 콜 차환 목적의 2024년 발행, 스텝업 조항 미확인)."}',
    '"issue_date": "2024-10-11", "amount_eok": 2300.0, "amount_basis": "채권원장 잔액", "type": "tier2", "type_unconfirmed": false, "evidence": "' + TK + ': 코리안리 제6회도 보완자본형(사업보고서 스텝업 문구; census 1차 확정도 a). 2019년 발행분 콜 차환 목적."}')
sub('"note": "미확정: 소진율 범위 94.0%(신규 4,790억이 보완자본형일 때 = 기발행 3,292 / SCR x 15%) ~ 205.1%(기본자본형일 때 = 4,790 / SCR x 10%). 상한 205.1% 를 싣는다."',
    '"note": "소진율 = 기발행 3,292 / SCR x 15% = 94.0%(신규 4,800억 두 건은 보완자본형 확정이라 제외; 종전 상한 205.1%)."')

# --- 교보 2024-11-12: 발행조건 스텝업 -> tier2, 발행사 처리 tier1 (issuer_type)
sub('"type": "tier1", "type_unconfirmed": false, "evidence": "메모 §3.2: 2024.4Q 항목 6 +5,983 일 때 X +89 = 기본자본형. 결속하는 쪽은 기발행(70.1%)이라 이 판정은 소진율 숫자를 바꾸지 않는다(5,983 / SCR x 10% = 56.8%)."}',
    '"type": "tier2", "type_unconfirmed": false, "issuer_type": "tier1", "evidence": "' + TK + ': 교보 2024-11-12 6,000억은 발행조건이 스텝업이라 보완자본형. 그러나 발행사 K-ICS 표는 기본자본형으로 처리했다(메모 §3.2: 2024.4Q 항목 6 +5,983 일 때 X +89; census 1차 c9: 보완자본형으로 보면 other 가 8,310 -> 2,416 급락, 확정도 a 인데 발행사 처리 INCONSISTENT). 우리 분류(type=tier2)와 발행사 실제 처리(issuer_type=tier1)가 어긋나는 유일 케이스 -> census 최종본이 나오면 대조. 결속하는 쪽은 기발행(70.1%)이라 소진율 숫자는 type 에 관계없이 같다."}')
sub('"note": "소진율 = max(11,089 / SCR x 15% = 70.1%, 5,983 / SCR x 10% = 56.8%) = 70.1%."',
    '"note": "소진율 = max(기발행 11,089 / SCR x 15% = 70.1%, 기본자본형 신규 0) = 70.1%(2024-11 건을 발행사처럼 기본자본형으로 보면 5,983 / SCR x 10% = 56.8% 로 여전히 기발행이 결속 - 숫자 불변)."')

P.write_text(t, encoding="utf-8", newline="\n")
print("ok")
