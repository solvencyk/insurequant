#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Disclosure 파일들을 통합하여 kics disclosure.xlsx 파일 생성
"""

import pandas as pd
import os
import re
from pathlib import Path

from solvency.config import settings

class DisclosureMerger:
    def __init__(self):
        self.base_dir = str(settings.disclosure_dir)
        self.output_file = "kics disclosure.xlsx"
        
        # 보험사 유형 판별을 위한 키워드
        self.life_insurance_keywords = ["생명보험", "생명", "수명", "종신", "정기", "연금"]
        self.damage_insurance_keywords = ["손해보험", "손해", "자동차", "화재", "해상", "재해"]
        
        # KR0100 기준 행이름 매핑 (항목번호 1-27)
        self.reference_row_mapping = {
            1: '가. 지급여력금액',
            2: '기본자본',
            3: '보완자본',
            4: 'Ⅰ. 건전성감독기준 재무상태표 상의 순자산',
            5: '1. 보통주',
            6: '2. 자본항목 중 보통주 이외의 자본증권',
            7: '3. 이익잉여금',
            8: '4. 자본조정',
            9: '5. 기타포괄손익누계액',
            10: '6. 비지배지분',
            11: '7. 조정준비금',
            12: 'Ⅱ. 지급여력금액으로 불인정하는 항목 (지급이 예정된 주주배당액 등)',
            13: 'Ⅲ. 보완자본으로 재분류하는 항목 (기본자본 자본증권의 인정한도를 초과한 금액 등)',
            14: '나. 지급여력기준금액 (Ⅰ-Ⅱ+Ⅲ)',
            15: 'Ⅰ. 기본요구자본',
            16: '- 분산효과 : (1+2+3+4+5) - Ⅰ',
            17: '1. 생명장기손해보험위험액',
            18: '2. 일반손해보험위험액',
            19: '3. 시장위험액',
            20: '4. 신용위험액',
            21: '5. 운영위험액',
            22: 'Ⅱ. 법인세조정액',
            23: 'Ⅲ. 기타 요구자본(1+2+3)',
            24: '1. 업권별 자본규제를 활용한 종속회사의 요구자본 환산치',
            25: '2. 비례성원칙을 적용한 종속회사의 요구자본 대응치',
            26: '3. 업권별 자본규제를 활용한 관계회사의 요구자본 환산치',
            27: '다. 지급여력비율 : 가 ÷ 나 × 100'
        }
        
        # 항목명 통일을 위한 매핑 규칙
        self.item_mapping = {
            # 지급여력금액 관련
            '지급여력금액': ['지급여력금액', '가. 지급여력금액', '가 지급여력금액', '지급여력 금액'],
            '기본자본': ['기본자본', '1. 기본자본', '1 기본자본', '기본 자본'],
            '보완자본': ['보완자본', '2. 보완자본', '2 보완자본', '보완 자본'],
            
            # 건전성감독기준 관련
            '건전성감독기준순자산': ['건전성감독기준 재무상태표 상의 순자산', 'Ⅰ. 건전성감독기준 재무상태표 상의 순자산', 
                                   '건전성감독기준 순자산', '순자산'],
            '보통주': ['보통주', '1. 보통주', '1 보통주', '1.  보통주'],
            '자본항목중보통주이외의자본증권': ['자본항목 중 보통주 이외의 자본증권', '2. 자본항목 중 보통주 이외의 자본증권', 
                                        '2.  자본항목  중  보통주  이외의  자본증권', '자본증권'],
            '이익잉여금': ['이익잉여금', '3. 이익잉여금', '3 이익잉여금', '3.  이익잉여금'],
            '자본조정': ['자본조정', '4. 자본조정', '4 자본조정', '4.  자본조정'],
            '기타포괄손익누계액': ['기타포괄손익누계액', '5. 기타포괄손익누계액', '5 기타포괄손익누계액', '5.  기타포괄손익누계액'],
            '비지배지분': ['비지배지분', '6. 비지배지분', '6 비지배지분', '6.  비지배지분'],
            '조정준비금': ['조정준비금', '7. 조정준비금', '7 조정준비금', '7.  조정준비금'],
            
            # 보완자본 재분류 관련
            '보완자본재분류항목': ['보완자본으로 재분류하는 항목', 'Ⅲ. 보완자본으로 재분류하는 항목', 
                              '보완자본 재분류 항목', '재분류 항목'],
            
            # 분산효과 관련
            '분산효과': ['분산효과', '- 분산효과', '분산 효과', '분산효과 : (1+2+3+4+5) - Ⅰ'],
            '생명장기손해보험위험액': ['생명장기손해보험위험액', '1. 생명장기손해보험위험액', '1 생명장기손해보험위험액'],
            '일반손해보험위험액': ['일반손해보험위험액', '2. 일반손해보험위험액', '2.  일반손해보험위험액', '2 일반손해보험위험액'],
            '시장위험액': ['시장위험액', '3. 시장위험액', '3.  시장위험액', '3 시장위험액'],
            '신용위험액': ['신용위험액', '4. 신용위험액', '4.  신용위험액', '4 신용위험액'],
            '운영위험액': ['운영위험액', '5. 운영위험액', '5.  운영위험액', '5 운영위험액'],
            '기본요구자본': ['기본요구자본', 'Ⅰ. 기본요구자본', 'Ⅰ.  기본요구자본', '기본 요구자본'],
            
            # 지급여력기준금액 관련
            '지급여력기준금액': ['지급여력기준금액', '나. 지급여력기준금액', '나 지급여력기준금액', 
                              '지급여력기준금액 (Ⅰ-Ⅱ+Ⅲ)', '지급여력 기준금액'],
            '법인세조정액': ['법인세조정액', 'Ⅱ. 법인세조정액', 'Ⅱ.  법인세조정액', '법인세 조정액'],
            '기타요구자본': ['기타요구자본', 'Ⅲ. 기타요구자본', 'Ⅲ.  기타요구자본', 
                          '기타요구자본(1+2+3)', '기타 요구자본'],
            
            # 기타요구자본 구성요소
            '업권별자본규제종속회사요구자본환산치': ['업권별 자본규제를 활용한 종속회사의 요구자본 환산치', 
                                        '1. 업권별 자본규제를 활용한 종속회사의 요구자본 환산치', '종속회사 요구자본'],
            '비례성원칙종속회사요구자본대응치': ['비례성원칙을 적용한 종속회사의 요구자본 대응치', 
                                      '2. 비례성원칙을 적용한 종속회사의 요구자본 대응치', '비례성원칙 요구자본'],
            '업권별자본규제관계회사요구자본환산치': ['업권별 자본규제를 활용한 관계회사의 요구자본 환산치', 
                                        '3. 업권별 자본규제를 활용한 관계회사의 요구자본 환산치', '관계회사 요구자본'],
            
            # 지급여력비율 관련
            '지급여력비율': ['지급여력비율', '다. 지급여력비율', '다 지급여력비율', 
                          '지급여력비율 : 가 ÷ 나 × 100', '지급여력 비율']
        }
    
    def get_disclosure_files(self):
        """disclosure.xlsx 파일들을 찾습니다."""
        disclosure_files = []
        
        if not os.path.exists(self.base_dir):
            print(f"❌ 기본 디렉토리가 존재하지 않습니다: {self.base_dir}")
            return disclosure_files
        
        try:
            items = os.listdir(self.base_dir)
            print(f"📁 디렉토리 내 항목 수: {len(items)}")
            
            for item in items:
                item_path = os.path.join(self.base_dir, item)
                if os.path.isdir(item_path):
                    try:
                        sub_items = os.listdir(item_path)
                        for sub_item in sub_items:
                            if sub_item.endswith('.xlsx') and 'disclosure' in sub_item.lower():
                                file_path = os.path.join(item_path, sub_item)
                                disclosure_files.append({
                                    'folder': item,
                                    'file': sub_item,
                                    'full_path': file_path
                                })
                                print(f"✅ 발견: {item} -> {sub_item}")
                                break  # 한 폴더당 하나의 disclosure 파일만 처리
                    except Exception as e:
                        print(f"⚠️ {item} 폴더 검색 중 오류: {e}")
            
            print(f"📊 총 발견된 disclosure 파일 수: {len(disclosure_files)}")
            
        except Exception as e:
            print(f"❌ 디렉토리 검색 중 오류: {e}")
        
        return disclosure_files
    
    def standardize_item_name(self, item_name):
        """항목명을 표준화합니다."""
        if not item_name or pd.isna(item_name):
            return item_name
        
        item_name = str(item_name).strip()
        
        # 매핑 규칙에 따라 표준화
        for standard_name, variations in self.item_mapping.items():
            for variation in variations:
                if variation in item_name or item_name in variation:
                    return standard_name
        
        # 매핑되지 않은 경우, 유사한 항목 찾기
        for standard_name, variations in self.item_mapping.items():
            for variation in variations:
                # 핵심 키워드가 포함된 경우
                core_keywords = self.extract_core_keywords(variation)
                if core_keywords and all(keyword in item_name for keyword in core_keywords):
                    return standard_name
        
        # 여전히 매핑되지 않은 경우 원본 반환
        return item_name
    
    def extract_core_keywords(self, text):
        """텍스트에서 핵심 키워드를 추출합니다."""
        if not text:
            return []
        
        # 특수문자와 공백을 제거하고 핵심 단어만 추출
        cleaned = re.sub(r'[^\w가-힣]', ' ', str(text))
        words = cleaned.split()
        
        # 2글자 이상의 단어만 필터링
        keywords = [word for word in words if len(word) >= 2]
        
        # 너무 많은 키워드가 있으면 상위 3개만 선택
        if len(keywords) > 3:
            keywords = keywords[:3]
        
        return keywords
    
    def find_matching_reference_row(self, row_name):
        """행이름을 KR0100 기준으로 매칭하여 항목번호와 표준 행이름을 반환합니다."""
        if not row_name or pd.isna(row_name):
            return None, None
        
        row_name = str(row_name).strip()
        
        # 1. 정확한 매칭
        for item_num, ref_name in self.reference_row_mapping.items():
            if row_name == ref_name:
                return item_num, ref_name
        
        # 2. 부분 매칭 (핵심 키워드 기반)
        row_keywords = self.extract_core_keywords(row_name)
        
        best_match = None
        best_score = 0
        
        for item_num, ref_name in self.reference_row_mapping.items():
            ref_keywords = self.extract_core_keywords(ref_name)
            
            # 공통 키워드 수 계산
            common_keywords = set(row_keywords) & set(ref_keywords)
            score = len(common_keywords)
            
            # 핵심 키워드가 포함된 경우 가중치 부여
            if any(keyword in ref_name for keyword in ['지급여력금액', '기본자본', '보완자본', '보통주', '이익잉여금', '자본조정', '기타포괄손익누계액', '비지배지분', '조정준비금', '분산효과', '생명장기손해보험위험액', '일반손해보험위험액', '시장위험액', '신용위험액', '운영위험액', '법인세조정액', '기타요구자본', '지급여력비율']):
                score += 1
            
            if score > best_score:
                best_score = score
                best_match = (item_num, ref_name)
        
        # 매칭 점수가 2 이상인 경우만 반환
        if best_score >= 2:
            return best_match
        
        return None, None
    
    def detect_insurance_type(self, folder_name):
        """폴더명을 기반으로 보험사 유형을 판별합니다."""
        folder_lower = folder_name.lower()
        
        # 생명보험사 키워드 확인
        for keyword in self.life_insurance_keywords:
            if keyword in folder_lower:
                return "생명보험"
        
        # 손해보험사 키워드 확인
        for keyword in self.damage_insurance_keywords:
            if keyword in folder_lower:
                return "손해보험"
        
        # 기본값은 손해보험사로 설정
        return "손해보험"
    
    def extract_company_code(self, folder_name):
        """폴더명에서 원보험사코드를 추출합니다."""
        # KR0001_메리츠화재해상보험 -> KR0001
        if '_' in folder_name:
            return folder_name.split('_', 1)[0]
        return folder_name
    
    def extract_company_name(self, folder_name):
        """폴더명에서 회사명을 추출합니다."""
        # KR0001_메리츠화재해상보험 -> 메리츠화재해상보험
        if '_' in folder_name:
            return folder_name.split('_', 1)[1]
        return folder_name
    
    def extract_ticker(self, company_name):
        """회사명에서 티커를 추출합니다."""
        # 주요 보험사 티커 매핑
        ticker_mapping = {
            '메리츠화재해상보험': '000060',
            '한화손해보험': '000370',
            '롯데손해보험': '000400',
            '흥국화재': '000650',
            '삼성화재해상보험': '000810',
            '현대해상': '001450',
            'KB손해보험': '002380',
            'DB손해보험': '005830',
            'NH농협손해보험': '005940',
            '악사손해보험': '006260',
            '하나손해보험': '000720',
            '신한이지손해보험': '001570',
            '한화생명': '000370',
            '에이비엘생명보험': '003850',
            '흥국생명보험': '000650',
            '케이디비생명보험': '005830',
            '교보생명보험': '000720',
            '라이나생명보험': '000400',
            '비엔피파리바카디프생명보험': '006260',
            '아이엠라이프생명보험': '003850',
            'DB생명보험': '005830',
            '푸본현대생명보험': '001450',
            '처브라이프생명보험': '000370'
        }
        
        # 정확한 매칭
        if company_name in ticker_mapping:
            return ticker_mapping[company_name]
        
        # 부분 매칭 (회사명에 키워드가 포함된 경우)
        for key, ticker in ticker_mapping.items():
            if any(keyword in company_name for keyword in key.split()):
                return ticker
        
        # 매핑되지 않은 경우 빈 문자열 반환
        return ""
    
    def read_disclosure_file(self, file_info):
        """disclosure.xlsx 파일을 읽어서 모든 시트를 반환합니다."""
        file_path = file_info['full_path']
        folder_name = file_info['folder']
        file_name = file_info['file']
        
        try:
            # 모든 시트 읽기
            df_dict = pd.read_excel(file_path, sheet_name=None)
            print(f"✅ {folder_name}/{file_name} 파일 읽기 성공 - 시트 수: {len(df_dict)}")
            return df_dict
        except Exception as e:
            print(f"❌ {folder_name}/{file_name} 파일 읽기 실패: {e}")
            return None
    
    def find_kics_ratio_sheet(self, df_dict):
        """kics_ratio 시트를 찾습니다."""
        for sheet_name in df_dict.keys():
            if 'kics_ratio' in sheet_name.lower():
                return sheet_name
        return list(df_dict.keys())[0]  # 첫 번째 시트 반환
    
    def extract_quarter_columns(self, df):
        """분기 컬럼들을 찾아서 반환합니다."""
        quarter_columns = []
        
        # 분기 패턴들
        quarter_patterns = [
            r'202[0-9]\.?[1-4]Q?',  # 2025.1Q, 2025.1, 2025Q1 등
            r'202[0-9]년\s*[1-4]분기',  # 2025년 1분기
            r'202[0-9]\s*[1-4]분기',  # 2025 1분기
            r'CY202[0-9]\s*[1-4]',  # CY2025 1
            r'FY202[0-9]-[1-4]',  # FY2025-1
        ]
        
        for col in df.columns:
            col_str = str(col).strip()
            for pattern in quarter_patterns:
                if re.search(pattern, col_str):
                    quarter_columns.append(col)
                    break
        
        return quarter_columns
    
    def process_single_file(self, file_info):
        """단일 파일을 처리하여 melt 형태로 변환합니다."""
        folder_name = file_info['folder']
        file_name = file_info['file']
        
        print(f"\n📊 처리 중: {folder_name}")
        
        # 파일 읽기
        df_dict = self.read_disclosure_file(file_info)
        if df_dict is None:
            return None
        
        # kics_ratio 시트 찾기
        target_sheet = self.find_kics_ratio_sheet(df_dict)
        df = df_dict[target_sheet]
        
        print(f"   📋 시트 '{target_sheet}' 사용 (행: {len(df)}, 열: {len(df.columns)})")
        
        # 분기 컬럼 찾기
        quarter_columns = self.extract_quarter_columns(df)
        print(f"   📅 분기 컬럼 발견: {quarter_columns}")
        
        if not quarter_columns:
            print(f"   ⚠️ 분기 컬럼을 찾을 수 없어 첫 5개 컬럼 사용")
            quarter_columns = df.columns[1:6].tolist()  # 첫 번째 컬럼(행명) 제외
        
        # 회사 정보
        company_code = self.extract_company_code(folder_name)
        company_name = self.extract_company_name(folder_name)
        ticker = self.extract_ticker(company_name)
        insurance_type = self.detect_insurance_type(folder_name)
        
        # melt 형태로 변환
        melted_data = []
        
        for idx, row in df.iterrows():
            if pd.notna(row.iloc[0]):  # 첫 번째 열에 값이 있는 경우
                row_name = str(row.iloc[0]).strip()
                
                # KR0100 기준으로 행이름 매칭
                item_number, standardized_name = self.find_matching_reference_row(row_name)
                
                # 매칭되지 않은 경우 원본 이름 사용
                if not standardized_name:
                    standardized_name = row_name
                    item_number = None
                
                for col in quarter_columns:
                    if col in df.columns:
                        value = row[col]
                        melted_data.append({
                            '원보험사코드': company_code,
                            '원수사명': company_name,
                            '티커': ticker,
                            '생손보여부': insurance_type,
                            '항목번호': item_number,
                            '항목명': standardized_name,
                            '공시분기': str(col).strip(),
                            '값': value
                        })
        
        if melted_data:
            result_df = pd.DataFrame(melted_data)
            print(f"   ✅ 변환 완료: {len(result_df)}행")
            return result_df
        else:
            print(f"   ⚠️ 변환할 데이터가 없음")
            return None
    
    def merge_all_files(self):
        """모든 파일을 병합합니다."""
        print("🚀 Disclosure 파일 통합 시작")
        print("="*60)
        
        # 파일 목록 가져오기
        disclosure_files = self.get_disclosure_files()
        
        if not disclosure_files:
            print("❌ 처리할 파일을 찾을 수 없습니다.")
            return
        
        all_data = []
        
        # 각 파일 처리
        for i, file_info in enumerate(disclosure_files, 1):
            print(f"\n[{i}/{len(disclosure_files)}] 처리 중...")
            
            result_df = self.process_single_file(file_info)
            if result_df is not None:
                all_data.append(result_df)
        
        if not all_data:
            print("❌ 처리된 데이터가 없습니다.")
            return
        
        # 모든 데이터 병합
        print(f"\n📊 데이터 병합 중...")
        merged_df = pd.concat(all_data, ignore_index=True)
        
        print(f"✅ 병합 완료: {len(merged_df)}행")
        print(f"📊 회사 수: {merged_df['원수사명'].nunique()}")
        print(f"📊 공시분기 수: {merged_df['공시분기'].nunique()}")
        print(f"📊 항목 수: {merged_df['항목명'].nunique()}")
        
        # 엑셀 파일로 저장
        self.save_to_excel(merged_df)
        
        return merged_df
    
    def save_to_excel(self, df):
        """데이터를 엑셀 파일로 저장합니다."""
        try:
            print(f"\n💾 엑셀 파일 저장 중: {self.output_file}")
            
            with pd.ExcelWriter(self.output_file, engine='openpyxl') as writer:
                # 1. 전체 데이터 시트
                df.to_excel(writer, sheet_name='전체데이터', index=False)
                
                # 2. 회사별 요약 시트
                company_summary = df.groupby(['원보험사코드', '원수사명', '티커', '생손보여부']).agg({
                    '공시분기': 'nunique',
                    '항목명': 'nunique',
                    '항목번호': 'nunique',
                    '값': 'count'
                }).reset_index()
                company_summary.columns = ['원보험사코드', '원수사명', '티커', '생손보여부', '공시분기수', '항목수', '매칭된항목수', '데이터수']
                company_summary.to_excel(writer, sheet_name='회사별요약', index=False)
                
                # 3. 공시분기별 요약 시트
                quarter_summary = df.groupby('공시분기').agg({
                    '원수사명': 'nunique',
                    '항목명': 'nunique',
                    '값': 'count'
                }).reset_index()
                quarter_summary.columns = ['공시분기', '회사수', '항목수', '데이터수']
                quarter_summary.to_excel(writer, sheet_name='분기별요약', index=False)
                
                # 4. 생손보별 요약 시트
                type_summary = df.groupby('생손보여부').agg({
                    '원수사명': 'nunique',
                    '공시분기': 'nunique',
                    '항목명': 'nunique',
                    '값': 'count'
                }).reset_index()
                type_summary.columns = ['생손보여부', '회사수', '공시분기수', '항목수', '데이터수']
                type_summary.to_excel(writer, sheet_name='생손보별요약', index=False)
                
                # 5. 표준화된 항목명 통계 시트
                item_stats = df.groupby(['항목번호', '항목명']).agg({
                    '원수사명': 'nunique',
                    '공시분기': 'nunique',
                    '값': 'count'
                }).reset_index()
                item_stats.columns = ['항목번호', '항목명', '회사수', '공시분기수', '데이터수']
                item_stats = item_stats.sort_values('항목번호')
                item_stats.to_excel(writer, sheet_name='항목별통계', index=False)
            
            print(f"✅ 저장 완료: {self.output_file}")
            
            # 저장된 파일 정보 출력
            print(f"\n📊 저장된 파일 정보:")
            print(f"   📁 파일명: {self.output_file}")
            print(f"   📊 총 행 수: {len(df):,}")
            print(f"   📊 회사 수: {df['원수사명'].nunique()}")
            print(f"   📊 공시분기 수: {df['공시분기'].nunique()}")
            print(f"   📊 항목 수: {df['항목명'].nunique()}")
            
        except Exception as e:
            print(f"❌ 저장 실패: {e}")

def main():
    """메인 함수"""
    try:
        merger = DisclosureMerger()
        merged_df = merger.merge_all_files()
        
        if merged_df is not None:
            print(f"\n🎉 통합 완료!")
            print(f"📁 결과 파일: {merger.output_file}")
            
            # 샘플 데이터 출력
            print(f"\n📋 샘플 데이터 (처음 10행):")
            print(merged_df.head(10).to_string())
            
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"❌ 예상치 못한 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
