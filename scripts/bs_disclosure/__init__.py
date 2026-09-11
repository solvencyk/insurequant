# -*- coding: utf-8 -*-
"""17BS 경영공시 백필(2026-09-11, inbox/parser/20260911T0109Z) 공용 패키지.

data/disclosure (정기경영공시 raw PDF) 에서 IFRS17_BS.json 의 21개 항목을 채우는 추출기.
common.py 가 전사 공통 규칙(표 고정·열 고정·축척 판정·라벨 매칭·산술/QoQ 게이트)을 갖고,
회사별 특이사항은 scripts/extract_bs_from_disclosure.py 의 회사별 실행에서 처리한다.
"""
