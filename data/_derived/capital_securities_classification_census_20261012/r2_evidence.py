"""r2_evidence.py (parser-kics, ticket 20261012T2000Z, round 2) -- evidence added in round 2 (data only, imported by r2_apply.py / r2_selfcheck.py).

Round 1 evidence stays in c6_evidence.py (ids R*, C9, F-*, W1..W11).  Round 2 adds:
  O1..O3  = the owner's own press excerpts (2026-10-12).  The original article of O1 / O2 could NOT be located verbatim with WebSearch
            (see SEARCH_LOG); O3 is the same wording as W11 (Asia Economy 2023-04-05), which round 1 had already found.
  W12..   = public press / rating-agency items found with WebSearch in round 2.
IMPORTANT (how these were read): WebSearch returns result lists (title + URL) plus a model-written summary of the hits.  The article bodies were
NOT opened (WebSearch only; no WebFetch/browser, per the ticket).  Every statement below is a paraphrase of what the search summary reported for that
URL, so a quoted wording must be re-read at the URL before it is used outside this folder.  `date_basis` says how sure the date is.
"""
from __future__ import annotations

OWNER = [
    dict(id="O1", kind="OWNER", strength="owner-provided", date="2026-10-12",
         src="ticket inbox/parser/20261012T2000Z item 4 (owner chat 2026-10-12): press excerpt about DB Non-life; outlet/date not given to us",
         date_basis="owner chat date",
         statement="(paraphrase) DB손보는 국내 보험사 중 기본자본 요건을 충족하는 신종자본증권을 발행하는 유일한 사례로 서술됨; 기본자본 인정 = 조기상환 시점 스텝업 없음 + 이자는 배당가능이익 범위 안에서 지급; "
                   "전월 발행분 금리 5.3%, 이자 부담이 크지만 기본자본 확보 목적",
         original="most likely W2 = IB Tomato 2026-07-09 'redeem -> capital cut, do not -> credit hit: insurer perpetual dilemma' https://www.newstomato.com/ReadNews.aspx?no=1306331 "
                   "(same piece: https://www.ibtomato.com/ExternalView.aspx?type=1&no=18833). Matched by CONTENT, not verbatim (SEARCH_LOG #33): since K-ICS only DB issued no-step-up hybrids; "
                   "issuing needs distributable profit; DB's 2nd basic-capital issue priced at the top (5.3%) of the 4.7~5.3% band in June 2026. Not verbatim: 9 earlier tries (SEARCH_LOG #1, #4-#8, #17-#19) "
                   "did not return the sentences, and the #33 summary was built from the lead and part of the body only. Other public items saying the same about DB: W1, W3, W4, W12, W14-W16, W18"),
    dict(id="O2", kind="OWNER", strength="owner-provided", date="2026-10-12",
         src="user message to this run (owner evidence 2026-10-12): press excerpt about Hana Non-life",
         date_basis="owner message date",
         statement="(paraphrase) 하나손보는 올해 6월 이자율 6.20%, 1,000억원 신종자본증권을 추가 발행(하나금융 전액 인수); 그간 신종자본증권으로 조달한 2,000억원은 전액 보완자본; "
                   "스텝업 조항 등은 없으나 배당가능이익이 없어 기본자본 인정 요건을 충족하지 못함",
         original="not located verbatim (SEARCH_LOG #2, #9, #11-#16, #21); the 6.20% / 1,000억 / 전량 인수 / 보완자본 분류 parts are corroborated by W19-W23, "
                  "the 'no step-up but no distributable profit' sentence only exists in the owner excerpt"),
    dict(id="O3", kind="OWNER", strength="owner-provided", date="2026-10-12",
         src="user message to this run (owner evidence 2026-10-12): press excerpt about Hana Life 제1회 신종 1,800억 (2023-03-31)",
         date_basis="owner message date",
         statement="(paraphrase) 하나생명 1,800억 신종: 주관 KB증권, 만기 30년 연장 가능 영구채, 5년 후 콜, 콜 미행사 시 금리가 단계적으로 오르는 스텝업 구조 -> 스텝업 = 보완자본형",
         original="= the wording of W11 (Asia Economy 2023-04-05, https://core.asiae.co.kr/article/2023040506543817834), found again by SEARCH_LOG #3; round 1 had read it and set it aside "
                  "because the issuer's K-ICS table looked partly tier1 and the DART note has no step-up wording"),
]

PRESS = [
    # ------------------------------------------------------------------ DB Non-life
    dict(id="W12", kind="PRESS", strength="secondary", date="2025-09-25", date_basis="Daum URL timestamp 20250925 19:51",
         src="Digital Times (via Daum) '기본자본 확충 노력...보험사, 건전성 제고 총력' https://v.daum.net/v/20250925195125275 (outlet per search summary)",
         statement="DB손보 9월 신종 합계 8,670억(1일 공모 7,470억 + 25일 사모 1,200억): 두 증권 모두 중도상환 안 할 때 금리를 올리는 스텝업 조항이 없어 기본자본을 늘리는 수단이 됨; "
                   "기본자본 신종은 배당가능이익 범위 안에서만 이자 지급"),
    dict(id="W13", kind="PRESS", strength="secondary", date="2026-02-11", date_basis="URL path 2026/02/11",
         src="Invest Chosun '美 포테그라 인수하는 DB손보, 사모 신종자본증권 4420억 발행' https://www.investchosun.com/site/data/html_dir/2026/02/11/2026021180227.html",
         statement="2026-02-11 DB손보 사모 신종 4,420억(4.4%, 만기 30년, 5년 후 콜), 이 발행으로 DB 신종 발행 잔액 약 1조3,090억 추정. 검색 요약에는 기본자본/보완자본 분류 문구가 없음(조건 확인용으로만 사용)"),
    dict(id="W14", kind="PRESS", strength="secondary", date="2026-05-28~06-01", date_basis="article no. 1302283 sits next to W5 (no. 1302227, 2026-06-01); body says the demand forecast is on 'the 1st' (future) -> about 2026-05-28..06-01",
         src="IB Tomato '(Deal monitor) DB손해보험, 기본자본 또 발행...K-ICS 방어 고삐' https://www.newstomato.com/ReadNews.aspx?no=1302283 (same piece: https://www.ibtomato.com/ExternalView.aspx?type=1&no=18446)",
         statement="제4회 공모 신종 3,000억(수요예측 결과에 따라 최대 6,000억), 만기 30년, 수요예측 6/1; 기본자본 인정 신종으로 소개, 2025년 업계 최초 발행 이후 두 번째; 기본자본 K-ICS 92.1% -> 93.3% 효과 추정"),
    dict(id="W15", kind="PRESS", strength="secondary", date="2026-06-02~03", date_basis="body: 'confirmed on the 2nd', issue on the 9th -> about 2026-06-02/03",
         src="FETV 'DB손보, 신종자본증권 4100억 증액 발행...콜옵션 행사' https://www.fetv.co.kr/news/articleView.html?idxno=303621",
         statement="6/2 확정 공시, 6/9 공모 4,100억 발행(당초 3,000억에서 증액), 기본자본 규제 선제 대응 + 2021-06 후순위 4,990억 콜 행사 재원. "
                   "최종 금리 5.30%(공모희망 4.7~5.3% 최상단)는 같은 시기 보도군(SEARCH_LOG #7·#8 요약)과 DART 목록(F-KR0011 제4회 5.30%)이 일치"),
    dict(id="W16", kind="PRESS", strength="primary-via-summary", date="2026-05-27", date_basis="KIND URL path 2026/05/27 (filing date)",
         src="KRX KIND 증권신고서 DB손해보험 제4회 공모 신종자본증권 https://kind.krx.co.kr/external/2026/05/27/000851/20260527002054/10002.htm (page not opened; per search summary)",
         statement="증권신고서: 모집총액 3,000억, 공모희망금리 4.70~5.30%, 만기 30년 5년 콜, AA(안정적), 본문에 기본자본 요건을 충족한다는 취지의 문장이 있다고 요약됨"),
    dict(id="W17", kind="PRESS", strength="secondary", date="2026-06-16", date_basis="summary: decision date 'the 16th', 118 days before the search",
         src="Investing.com Korea filing digest 'DB손해보험, 신종자본증권 추가 발행 결정...총 한도 1조 5,000억 원' https://kr.investing.com/news/global-filings/article-93CH-1985744",
         statement="추가 발행 결정(국내 무기명식 무보증 사모채권형, 만기 30년, 대표주관 KB증권), 2026-02-04 이사회 승인 1.5조 한도 안의 잔여 한도 사용, 목적 지급여력비율 제고; 금액은 요약에 없음(제5회 300억과 같은 건으로 판단)"),
    dict(id="W18", kind="PRESS", strength="secondary", date="2026-05-26", date_basis="file name rs20260526",
         src="Korea Investors Service rating report on DB Insurance https://m.kisrating.com/fileDown.do?menuCd=R8&gubun=2&fileName=rs20260526-15.pdf (PDF not opened; per search summary)",
         statement="2025년 중 기본자본 인정 신종자본증권 8,670억(= 7,470억 + 1,200억)을 발행했다는 문장이 있다고 요약됨"),
    # ------------------------------------------------------------------ Hana Non-life / Hana Life
    dict(id="W19", kind="PRESS", strength="secondary", date="2026-06~09 (unknown)", date_basis="not shown in the summary; mentions the July rights offering, so it is after 2026-07",
         src="Financial Today '하나금융 보험계열사 한 달 새 4500억 자본확충...킥스 방어 나섰다' https://www.ftoday.co.kr/news/articleView.html?idxno=362777",
         statement="하나손보 6월 신종 1,000억 발행: 만기 2056년 6월, 표면금리 연 6.20%(올해 보험사 자본성증권 중 최고), 연 이자 약 62억; 7월 하나금융 대상 유상증자 2,000억"),
    dict(id="W20", kind="PRESS", strength="secondary", date="2026-09-30", date_basis="URL date 20260930",
         src="Metro Seoul '하나금융 보험형제, 기본자본 50% 밑돈다' https://www.metroseoul.co.kr/article/20260930500268",
         statement="하나생명·하나손보가 발행한 신종자본증권 2,500억은 K-ICS상 보완자본으로 분류되며 전체 K-ICS 비율은 높이나 기본자본 비율에는 직접 반영되지 않음; 하나금융은 두 회사의 신종 3,800억도 인수"),
    dict(id="W21", kind="PRESS", strength="secondary", date="2026-09-15", date_basis="summary: entered 2026-09-15",
         src="Sisa Journal-e '하나금융 보험사, 잇단 자본확충...자강 이룰까' https://www.sisajournal-e.com/news/articleView.html?idxno=423719",
         statement="하나손보 사모 신종 1,000억은 최대주주 하나금융지주가 전량 인수; 하나생명 1,500억(연 6%) 신종; 신종은 보완자본으로 분류돼 기본자본 확충 효과가 제한적"),
    dict(id="W22", kind="PRESS", strength="secondary", date="2026-06 (unknown day)", date_basis="after the board decision (mid-June) and before the 6/29 issue",
         src="Dealsite '[보험사 자본구조 진단] 하나손보, 체질개선 나섰지만...자본의 질 흔들' https://dealsite.co.kr/articles/163530",
         statement="하나손보가 사모 1,000억 신종 발행을 의결, 하나금융지주가 전량 인수; 신종은 보완자본이라 기본자본 확충 효과가 제한적; 1분기 기본자본비율 28.6%"),
    dict(id="W23", kind="PRESS", strength="secondary", date="2026-06-mid (unknown day)", date_basis="summary: about 116 days before the search date",
         src="FETV '중소형 손보사, 릴레이 채권 발행...하나손보도 1000억' https://www.fetv.co.kr/news/articleView.html?idxno=304575",
         statement="하나손보 이사회가 신종 1,000억 발행 의결: 발행일 29일(2026-06-29), 만기 30년(2056-06-29), 5년 후 콜, 물량 전부 최대주주 하나금융지주 인수"),
    dict(id="W24", kind="PRESS", strength="secondary", date="2026-09-15~16", date_basis="body: private placement on the 15th; headline about the lowest K-ICS",
         src="FETV '하나생명, 1500억 신종자본증권 발행...K-ICS 역대 최저' https://www.fetv.co.kr/news/articleView.html?idxno=310160 (post-period bond, after 2026-06-30)",
         statement="하나생명 2026-09-15 사모 신종 1,500억: 연 6%, 만기 2056-09-15, 5년 후 콜; 회사 설명 = 기본자본 비율 개선 목적이 아니라 내년 규제 대비"),
    dict(id="W25", kind="PRESS", strength="secondary", date="2026-09 (unknown day)", date_basis="after 2026-09-15",
         src="Dealsite '[보험사 자본구조 진단] 신종자본증권 꺼낸 하나생명...기본자본 제자리' https://dealsite.co.kr/articles/166664",
         statement="하나생명 신종(2026-09)은 보완자본으로 분류돼 K-ICS 비율은 개선하나 기본자본 비율은 못 올림"),
    # ------------------------------------------------------------------ subordinated: former exception candidates
    dict(id="W26", kind="PRESS", strength="secondary", date="2025-03-31", date_basis="body: '31st ... last 28th'",
         src="Smart Today 'iM라이프, 750억원 후순위채권 발행..4개월 만' https://www.smarttoday.co.kr/news/articleView.html?idxno=76665; The Bell 2025-04-01 https://www.thebell.co.kr/free/content/ArticleView.asp?key=202504011501341760102086",
         statement="iM라이프 2025-03-28 납입 무보증 후순위채 750억: 표면 5.5%, 만기 10년, 사모, 대표주관 KB증권 (= 아이엠라이프 2025-03-28 750억 '사모사채'; 법적 후순위로 확인)"),
    dict(id="W27", kind="PRESS", strength="secondary", date="2026-03-12", date_basis="MT URL date 20260312; result article IB Tomato no. 1295009 (late March)",
         src="Money Today '흥국화재, 연 5% 매달 지급 1000억 규모 후순위채 발행' https://www.mt.co.kr/finance/2026/03/12/2026031210380720349; Newsis NISX20260312_0003545339; IB Tomato https://www.newstomato.com/ReadNews.aspx?no=1295009",
         statement="흥국화재 1,000억 무보증 후순위사채(제23회로 보도): 만기 10년(2036-03), 5년 후 콜, 월이표, 최종 5.50%, 수요예측 3/17, 발행 예정 3/25(상장 3/26); 라운드 1 표의 발행일 2026-03-31 은 BS 재현으로 도출한 값이라 보도와 며칠 어긋남"),
    dict(id="W28", kind="PRESS", strength="secondary", date="2023-06 (about 06-14)", date_basis="a title dated 2023.06.14 appears in the summary; outlet not identified",
         src="press items in the search results (outlet of the wording not identified in the summary): Sisa Journal-e idxno 301004 and 303180 (titles only: Industrial Bank guarantee / KDB Life) "
             "https://www.sisajournal-e.com/news/articleView.html?idxno=301004 , https://www.sisajournal-e.com/news/articleView.html?idxno=303180 ; and a report titled 'KDB Life 900억 subordinated bond ... cost saving and capital build-up' dated 2023.06.14",
         statement="KDB생명 2023-06 보증부 후순위 900억: 만기 10년, 5년 후 콜, 산업은행이 원리금 지급 보증(AAA); 보도는 이를 자본성증권으로 분류하고 조달금은 전액 자본으로 인정된다고 설명 -> 반대 근거 없음"),
    dict(id="W29", kind="PRESS", strength="secondary", date="2025-09-01", date_basis="Bell URL key 20250901",
         src="The Bell '[보험사 기본자본 확충 스타트] 기본자본 신종 발행, 첫째도 둘째도 배당가능이익' https://www.thebell.co.kr/free/content/ArticleView.asp?key=202509010910057180106519 (title only)",
         statement="기본자본 신종 발행의 1차 조건이 배당가능이익이라는 제목 - 스텝업 없음만으로 기본자본이 되지 않는다는 점의 배경"),
]

EVIDENCE_R2 = OWNER + PRESS
EV2 = {e["id"]: e for e in EVIDENCE_R2}

# Every WebSearch call of this run, in order.  mode: s = standard, x = extended.  result: HIT = found what the query aimed at, PART = related items only, MISS = nothing usable.
SEARCH_LOG = [
    (1, "s", "DB 'only insurer with a tier-1-eligible hybrid' + 5.3% + distributable profit (owner excerpt O1, joined keywords)", "PART: W3/W4/W7/W1 family and the dealsite/IB Tomato DB pieces; the sentence itself not found"),
    (2, "s", "Hana Non-life 6.20% / 1,000억 / June / Hana Financial buys all (O2)", "PART: 2024 purchase news and W8; 6.20% not in that run"),
    (3, "s", "Hana Life 1,800억 KB Securities arranger 30y 5y call step-up (O3)", "HIT: Asia Economy 2023-04-05 (= W11) wording re-found: arranger, perpetual-like, call, step-up, 5.62% first 5y"),
    (4, "s", "DB 'last month issued hybrid rate 5.3% interest burden but securing basic capital' (O1)", "PART: confirms 5.30% belongs to the June-2026 DB issue (fnnews 2026-07-22 roundup seen only as a title); sentence not found"),
    (5, "s", "hybrid counts as basic capital only with no step-up and interest within distributable profit, DB only (O1)", "PART: W1/W2/W3 and Daily Ian 2026 piece (W6); 'only' not found"),
    (6, "x", "DB June 2026 hybrid 5.3% basic capital report + Portegra", "HIT: FETV 303621 (W15), IB Tomato Deal monitor (W14), KIND filing (W16), Investing.com digest (W17); 4,100억 on 06-09 at 5.30%"),
    (7, "x", "DB 2Q K-ICS 204% basic capital hybrid 5.3% 'only' domestic insurer", "PART: 2Q K-ICS 204.4% / basic 95.95%; '6월2일 4100억 연 5.30% 발행' reported; 'only' not found (articles say 'first')"),
    (8, "x", "DB target price Portegra K-ICS hybrid 5.3% interest burden 'only domestic insurer' (O1)", "PART: KB Securities report 2026-08-13 etc.; sentence not found"),
    (9, "x", "Hana Non-life rights offering + hybrids 2,000억 all supplementary, no step-up but no distributable profit (O2)", "PART: 2,000억 in the results is the July rights offering; hybrids 1,000억; supplementary classification confirmed (W20/W21)"),
    (10, "x", "Dealsite series: Hana Life took out a hybrid, basic capital unchanged", "HIT: Hana Life 2026-09-15 1,500억 hybrid, supplementary (W24/W25)"),
    (11, "x", "Dealsite series: Hana Non-life, quality of capital shaken, 6.20%, supplementary", "HIT: W22 + 6.20% via Financial Today (W19)"),
    (12, "x", "Hana Non-life 'hybrids raised so far 2,000억 all supplementary; no step-up but no distributable profit' (O2 exact sentence)", "MISS for the exact sentence; W19-W21 corroborate supplementary classification"),
    (13, "x", "Metro Seoul 'Hana Financial insurance siblings, basic capital below 50%'", "HIT: W20 (2026-09-30): 2,500억 hybrids of the two companies are supplementary"),
    (14, "x", "Money Today 'Hana Financial, extra capital for Hana Non-life' + 6.20% + bought entirely", "HIT: 6.20%, maturity 2056-06, all taken by Hana Financial (W19, W21)"),
    (15, "x", "Sisa Journal-e 'Hana Financial insurers, successive capital increases'", "HIT: W21 (2026-09-15)"),
    (16, "x", "Korea Financial Times series 'insurer basic capital check' Hana Non-life CEO", "MISS: Hana Non-life edition of the series not found"),
    (17, "x", "Tax & Finance News 'high K-ICS is not everything' + DB hybrid only", "PART: 'first' not 'only'; The Bell says only a handful of insurers can issue"),
    (18, "s", "DB 5.3% + 'only' with the news-site allow-list (hankyung, edaily, sedaily, news1, thebell, fnnews, asiae, mt, etoday, newsis, bizwatch)", "PART: DB 2025 issue articles; first run with mk.co.kr / yna.co.kr in the allow-list failed with API 400 (domains not accessible), rerun without them"),
    (19, "x", "exact phrase 'securing basic capital' + DB + 5.3%", "PART: W14/W15 give the June issue purpose as pre-emptive basic-capital regulation response; exact phrase not found"),
    (20, "x", "IB Tomato Deal monitor 'DB, basic capital again' 4,100억 + February private 4,420억", "HIT: W14; February 4,420억 article gives terms only (W13), classification not stated"),
    (21, "x", "Hana Non-life 1,000억 issue on June 29, maturity 2056-06, 6.20%, Hana Financial takes all", "HIT: FETV 304575 (W23): issue date 06-29, maturity 2056-06-29, 5y call, all taken by Hana Financial"),
    (22, "x", "headline 'Hana Life, hybrid 1,800억 issued ... capital soundness all-out' (2023-03-20)", "MISS: headline not found; Hana Life 2023-03-31 1,800억 confirmed by a business-report history table (summary)"),
    (23, "x", "Hana Life 2023-03 1,800억 RBC defence perpetual call step-up 5.62%", "PART: issue fact confirmed; step-up / 5.62% not re-found in this run (found in run #3)"),
    (24, "x", "Heungkuk Fire subordinated 1,000억 (March 2026) call / Series 20 redemption", "HIT: W27 (10y, 5.50%, 5y call, issue about 03-25); 450억 Series 20 redemption consistent with the H1 builder"),
    (25, "x", "iM Life 750억 subordinated March 2025 KB Securities", "HIT: W26 (unsecured subordinated, 5.5%, 10y, private, paid 03-28)"),
    (26, "x", "KDB Life guaranteed subordinated 900억 Industrial Bank guarantee June 2023", "HIT: W28 (10y, 5y call, bank guarantee, treated as capital)"),
    (27, "x", "AXA General JPY subordinated debt from AXA Life Japan, private", "MISS: no public item; stays an owner-default tier2 with no counter-evidence"),
    (28, "x", "DB 1,200억 private hybrid 2025-09-25 (제2회) basic capital no step-up", "HIT: two items - DB filing table (제2회 3.80%, 2025-09-25, private) and a press line that both September bonds lack step-up (W12)"),
    (29, "x", "Digital Times piece 'basic capital build-up effort' DB 25th private 1,200억", "HIT: W12 confirmed (Daum 20250925)"),
    (30, "x", "DB additional hybrid decision 300억 private 6월 29일 1.5조 limit (제5회)", "PART: W17 gives the decision (06-16, private, 30y, KB Securities); amount and 06-29 date not in the summary (DART list has them)"),
    (31, "x", "Invest Chosun 2026-02-11 DB private 4,420억 classification", "PART: terms only (W13); no basic/supplementary wording in the summary"),
    (32, "x", "Kyobo Life new hybrid 3,000억 September 2026 (post-period check)", "PART: demand forecast 08-24 (4,460억 orders), refinancing the 2021 4,700억; described as step-up -> fully supplementary; final amount/rate unconfirmed (post-period, not tabled)"),
    (33, "x", "IB Tomato 2026-07-09 'redeem -> capital cut, do not -> credit hit: insurer perpetual dilemma' + DB 5.3% + basic capital + interest burden (candidate original of O1; this is W2 of round 1)",
     "HIT by content (not verbatim): since K-ICS only DB issued no-step-up hybrids; issuing needs distributable profit; the 2026 'no. 2' basic-capital issue priced at the top of the 4.7~5.3% band = 5.3%; capital effect about 1pp of K-ICS per 1,000억"),
]
