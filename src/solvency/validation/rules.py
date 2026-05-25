import pandas as pd
import os
import re
from pathlib import Path
import warnings

from solvency.config import settings

class DisclosureValidator:
    def __init__(self):
        """정합성 검증기 초기화"""
        self.base_dir = str(settings.disclosure_dir)
        self.tolerance = 1.0  # 허용 오차 (1 이하)
        
        # 검증할 키워드들 정의
        self.validation_rules = {
            'a': {
                'description': '가. 지급여력금액 = 기본자본 + 보완자본',
                'target_row': '가. 지급여력금액',
                'component_rows': ['기본자본', '보완자본'],
                'operation': 'sum'
            },
            'b': {
                'description': 'Ⅰ. 건전성감독기준 재무상태표 상의 순자산 = 1.보통주 + 2.자본항목중보통주이외의자본증권 + 3.이익잉여금 + 4.자본조정 + 5.기타포괄손익누계액 + 6.비지배지분 + 7.조정준비금',
                'target_row': 'Ⅰ. 건전성감독기준 재무상태표 상의 순자산',
                'component_rows': ['1.  보통주', '2.  자본항목  중  보통주  이외의  자본증권', '3.  이익잉여금', '4.  자본조정', '5.  기타포괄손익누계액', '6.  비지배지분', '7.  조정준비금'],
                'operation': 'sum',
                'optional_rows': ['6.  비지배지분', '7.  조정준비금']  # 선택적 행들
            },
            'c': {
                'description': 'Ⅲ. 보완자본으로 재분류하는 항목 ≤ 보완자본',
                'target_row': 'Ⅲ. 보완자본으로 재분류하는 항목 (기본자본 자본증권의 인정한도를 초과한 금액 등)',
                'component_rows': ['보완자본'],
                'operation': 'less_than_or_equal'
            },
            'd': {
                'description': '- 분산효과 : (1+2+3+4+5) - Ⅰ = 1.생명장기손해보험위험액 + 2.일반손해보험위험액 + 3.시장위험액 + 4.신용위험액 + 5.운영위험액 - Ⅰ.기본요구자본',
                'target_row': '- 분산효과 : (1+2+3+4+5) - Ⅰ',
                'component_rows': ['1. 생명장기손해보험위험액', '2.  일반손해보험위험액', '3.  시장위험액', '4.  신용위험액', '5.  운영위험액', 'Ⅰ.  기본요구자본'],
                'operation': 'complex_calculation',
                'formula': 'sum_positive - basic_requirement'
            },
            'e': {
                'description': '나. 지급여력기준금액 (Ⅰ-Ⅱ+Ⅲ) = Ⅰ.기본요구자본 - Ⅱ.법인세조정액 + Ⅲ.기타요구자본(1+2+3)',
                'target_row': '나. 지급여력기준금액 (Ⅰ-Ⅱ+Ⅲ)',
                'component_rows': ['Ⅰ.  기본요구자본', 'Ⅱ.  법인세조정액', 'Ⅲ.  기타  요구자본(1+2+3)'],
                'operation': 'complex_calculation',
                'formula': 'basic_requirement - tax_adjustment + other_requirement'
            },
            'f': {
                'description': 'Ⅲ. 기타요구자본(1+2+3) = 1.업권별자본규제를활용한종속회사의요구자본환산치 + 2.비례성원칙을적용한종속회사의요구자본대응치 + 3.업권별자본규제를활용한관계회사의요구자본환산치',
                'target_row': 'Ⅲ.  기타  요구자본(1+2+3)',
                'component_rows': ['1. 업권별 자본규제를 활용한 종속회사의 요구자본 환산치', '2. 비례성원칙을 적용한 종속회사의 요구자본 대응치', '3. 업권별 자본규제를 활용한 관계회사의 요구자본 환산치'],
                'operation': 'sum',
                'optional_rows': ['1. 업권별 자본규제를 활용한 종속회사의 요구자본 환산치', '2. 비례성원칙을 적용한 종속회사의 요구자본 대응치', '3. 업권별 자본규제를 활용한 관계회사의 요구자본 환산치']
            },
            'g': {
                'description': '다. 지급여력비율 : 가 ÷ 나 × 100 = 가.지급여력금액 / 나.지급여력기준금액(Ⅰ-Ⅱ+Ⅲ) × 100',
                'target_row': '다.  지급여력비율  :  가  ÷  나  × 100',
                'component_rows': ['가. 지급여력금액', '나. 지급여력기준금액 (Ⅰ-Ⅱ+Ⅲ)'],
                'operation': 'ratio_calculation',
                'formula': 'solvency_amount / solvency_standard * 100'
            }
        }
    
    def get_company_folders(self):
        """disclosure 폴더에서 'disclosure.xlsx'가 포함된 모든 엑셀 파일을 찾습니다."""
        company_files = []
        
        if not os.path.exists(self.base_dir):
            print(f"❌ 기본 디렉토리가 존재하지 않습니다: {self.base_dir}")
            return company_files
        
        print(f"🔍 검색 중인 디렉토리: {self.base_dir}")
        
        try:
            items = os.listdir(self.base_dir)
            print(f"📁 디렉토리 내 항목 수: {len(items)}")
            
            for item in items:
                item_path = os.path.join(self.base_dir, item)
                if os.path.isdir(item_path):
                    # 폴더 내에서 'disclosure.xlsx'가 포함된 파일 찾기
                    try:
                        sub_items = os.listdir(item_path)
                        for sub_item in sub_items:
                            if sub_item.endswith('.xlsx') and 'disclosure' in sub_item.lower():
                                file_path = os.path.join(item_path, sub_item)
                                company_files.append({
                                    'folder': item,
                                    'file': sub_item,
                                    'full_path': file_path
                                })
                                print(f"✅ 발견: {item} -> {sub_item}")
                                break  # 한 폴더당 하나의 disclosure 파일만 처리
                    except Exception as e:
                        print(f"⚠️ {item} 폴더 검색 중 오류: {e}")
            
            print(f"📊 총 발견된 disclosure 파일 수: {len(company_files)}")
            
        except Exception as e:
            print(f"❌ 디렉토리 검색 중 오류: {e}")
        
        return company_files
    
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
    
    def find_value_by_row_name(self, df, row_name, column_index=1):
        """DataFrame에서 특정 행 이름으로 값을 찾습니다."""
        try:
            # 첫 번째 열에서 행 이름 검색 (정확한 매칭과 부분 매칭 모두 시도)
            for idx, row in df.iterrows():
                if pd.notna(row.iloc[0]):
                    cell_value = str(row.iloc[0]).strip()
                    
                    # 정확한 매칭
                    if cell_value == row_name:
                        value_str = str(row.iloc[column_index]).strip()
                        return self.extract_numeric_value(value_str)
                    
                    # 부분 매칭 (키워드가 포함된 경우)
                    if row_name in cell_value or cell_value in row_name:
                        value_str = str(row.iloc[column_index]).strip()
                        return self.extract_numeric_value(value_str)
            
            # 정확한 매칭이 실패한 경우, 유사한 행명 검색
            similar_rows = []
            for idx, row in df.iterrows():
                if pd.notna(row.iloc[0]):
                    cell_value = str(row.iloc[0]).strip()
                    # 공백과 특수문자를 제거하고 비교
                    clean_cell = re.sub(r'[^\w가-힣]', '', cell_value)
                    clean_target = re.sub(r'[^\w가-힣]', '', row_name)
                    
                    if clean_cell and clean_target and (clean_cell in clean_target or clean_target in clean_cell):
                        similar_rows.append((idx, cell_value))
            
            if similar_rows:
                print(f"    🔍 '{row_name}'과 유사한 행 발견: {[row[1] for row in similar_rows[:3]]}")
                # 가장 유사한 행 선택 (첫 번째)
                best_match_idx = similar_rows[0][0]
                value_str = str(df.iloc[best_match_idx, column_index]).strip()
                return self.extract_numeric_value(value_str)
            
            # 더 유연한 검색: 핵심 키워드만으로 검색
            core_keywords = self.extract_core_keywords(row_name)
            if core_keywords:
                for idx, row in df.iterrows():
                    if pd.notna(row.iloc[0]):
                        cell_value = str(row.iloc[0]).strip()
                        # 핵심 키워드가 모두 포함된 경우
                        if all(keyword in cell_value for keyword in core_keywords):
                            print(f"    🔍 핵심 키워드로 '{row_name}' 발견: '{cell_value}'")
                            value_str = str(row.iloc[column_index]).strip()
                            return self.extract_numeric_value(value_str)
            
            return None
        except Exception as e:
            print(f"    ⚠️ 행 '{row_name}' 검색 중 오류: {e}")
            return None
    
    def extract_core_keywords(self, row_name):
        """행 이름에서 핵심 키워드를 추출합니다."""
        # 특수문자와 공백을 제거하고 핵심 단어만 추출
        cleaned = re.sub(r'[^\w가-힣]', ' ', row_name)
        words = cleaned.split()
        
        # 2글자 이상의 단어만 필터링
        keywords = [word for word in words if len(word) >= 2]
        
        # 너무 많은 키워드가 있으면 상위 3개만 선택
        if len(keywords) > 3:
            keywords = keywords[:3]
        
        return keywords
    
    def extract_numeric_value(self, value_str):
        """문자열에서 숫자 값을 추출합니다."""
        if pd.isna(value_str) or value_str == '' or value_str == 'nan':
            return 0
        
        # 문자열로 변환하고 공백 제거
        str_value = str(value_str).strip()
        
        # '—' 또는 '-' 문자만 있는 경우 0으로 처리
        if str_value in ['—', '-', '–', '―']:
            return 0
        
        # 괄호는 음수로 처리
        is_negative = '(' in str_value and ')' in str_value
        
        # 숫자만 추출 (쉼표, 소수점 제거)
        cleaned = re.sub(r'[^\d.-]', '', str_value)
        
        try:
            if cleaned:
                value = float(cleaned)
                return -value if is_negative else value
            return 0
        except ValueError:
            return 0
    
    def validate_rule_a(self, df):
        """규칙 a: 가. 지급여력금액 = 기본자본 + 보완자본"""
        print("    🔍 규칙 a 검증 중...")
        
        target_value = self.find_value_by_row_name(df, '가. 지급여력금액')
        basic_capital = self.find_value_by_row_name(df, '기본자본')
        supplementary_capital = self.find_value_by_row_name(df, '보완자본')
        
        print(f"    📊 찾은 값들: 지급여력금액={target_value}, 기본자본={basic_capital}, 보완자본={supplementary_capital}")
        
        if target_value is None or basic_capital is None or supplementary_capital is None:
            missing_items = []
            if target_value is None: missing_items.append('지급여력금액')
            if basic_capital is None: missing_items.append('기본자본')
            if supplementary_capital is None: missing_items.append('보완자본')
            
            return {
                'rule': 'a',
                'passed': False,
                'error': f'필요한 행을 찾을 수 없음: {", ".join(missing_items)}',
                'details': {
                    'target_value': target_value,
                    'basic_capital': basic_capital,
                    'supplementary_capital': supplementary_capital
                }
            }
        
        expected_value = basic_capital + supplementary_capital
        difference = abs(target_value - expected_value)
        
        passed = difference <= self.tolerance
        
        print(f"    📊 계산: {basic_capital} + {supplementary_capital} = {expected_value}, 차이: {difference}")
        
        return {
            'rule': 'a',
            'passed': passed,
            'target_value': target_value,
            'expected_value': expected_value,
            'difference': difference,
            'tolerance': self.tolerance,
            'details': {
                'basic_capital': basic_capital,
                'supplementary_capital': supplementary_capital
            }
        }
    
    def validate_rule_b(self, df):
        """규칙 b: Ⅰ. 건전성감독기준 재무상태표 상의 순자산 = 구성요소들의 합"""
        print("    🔍 규칙 b 검증 중...")
        
        target_value = self.find_value_by_row_name(df, 'Ⅰ. 건전성감독기준 재무상태표 상의 순자산')
        
        if target_value is None:
            return {
                'rule': 'b',
                'passed': False,
                'error': '대상 행을 찾을 수 없음',
                'details': {}
            }
        
        component_values = {}
        total_expected = 0
        found_components = 0
        
        # 필수 구성요소들 (1-5번)
        required_components = self.validation_rules['b']['component_rows'][:5]
        # 선택적 구성요소들 (6-7번: 비지배지분, 조정준비금)
        optional_components = self.validation_rules['b']['component_rows'][5:]
        
        # 필수 구성요소들 검증
        for row_name in required_components:
            value = self.find_value_by_row_name(df, row_name)
            component_values[row_name] = value
            if value is not None:
                total_expected += value
                found_components += 1
            else:
                print(f"    ⚠️ 필수 구성요소 '{row_name}'을 찾을 수 없습니다.")
        
        # 선택적 구성요소들 검증 (없으면 0으로 처리)
        for row_name in optional_components:
            value = self.find_value_by_row_name(df, row_name)
            component_values[row_name] = value
            if value is not None:
                total_expected += value
                found_components += 1
            else:
                print(f"    ⚠️ 선택적 구성요소 '{row_name}'을 찾을 수 없어 0으로 처리합니다.")
                component_values[row_name] = 0
        
        # 필수 구성요소가 모두 없으면 실패
        if found_components == 0:
            return {
                'rule': 'b',
                'passed': False,
                'error': '필수 구성요소를 찾을 수 없음',
                'details': component_values
            }
        
        difference = abs(target_value - total_expected)
        passed = difference <= self.tolerance
        
        return {
            'rule': 'b',
            'passed': passed,
            'target_value': target_value,
            'expected_value': total_expected,
            'difference': difference,
            'tolerance': self.tolerance,
            'details': {
                **component_values,
                'found_components': found_components,
                'required_components_found': sum(1 for name in required_components if component_values.get(name) is not None)
            }
        }
    
    def validate_rule_c(self, df):
        """규칙 c: Ⅲ. 보완자본으로 재분류하는 항목 ≤ 보완자본"""
        print("    🔍 규칙 c 검증 중...")
        
        target_value = self.find_value_by_row_name(df, 'Ⅲ. 보완자본으로 재분류하는 항목 (기본자본 자본증권의 인정한도를 초과한 금액 등)')
        supplementary_capital = self.find_value_by_row_name(df, '보완자본')
        
        if target_value is None or supplementary_capital is None:
            return {
                'rule': 'c',
                'passed': False,
                'error': '필요한 행을 찾을 수 없음',
                'details': {
                    'target_value': target_value,
                    'supplementary_capital': supplementary_capital
                }
            }
        
        passed = target_value <= supplementary_capital
        
        return {
            'rule': 'c',
            'passed': passed,
            'target_value': target_value,
            'supplementary_capital': supplementary_capital,
            'details': {}
        }
    
    def validate_rule_d(self, df):
        """규칙 d: 분산효과 계산"""
        print("    🔍 규칙 d 검증 중...")
        
        target_value = self.find_value_by_row_name(df, '- 분산효과 : (1+2+3+4+5) - Ⅰ')
        
        if target_value is None:
            return {
                'rule': 'd',
                'passed': False,
                'error': '대상 행을 찾을 수 없음',
                'details': {}
            }
        
        # 양수 항목들의 합
        positive_sum = 0
        positive_values = {}
        for row_name in ['1. 생명장기손해보험위험액', '2.  일반손해보험위험액', '3.  시장위험액', '4.  신용위험액', '5.  운영위험액']:
            value = self.find_value_by_row_name(df, row_name)
            positive_values[row_name] = value
            if value is not None:
                positive_sum += value
        
        # 기본요구자본
        basic_requirement = self.find_value_by_row_name(df, 'Ⅰ.  기본요구자본')
        
        if basic_requirement is None:
            return {
                'rule': 'd',
                'passed': False,
                'error': '기본요구자본을 찾을 수 없음',
                'details': positive_values
            }
        
        expected_value = positive_sum - basic_requirement
        difference = abs(target_value - expected_value)
        passed = difference <= self.tolerance
        
        return {
            'rule': 'd',
            'passed': passed,
            'target_value': target_value,
            'expected_value': expected_value,
            'difference': difference,
            'tolerance': self.tolerance,
            'details': {
                'positive_sum': positive_sum,
                'basic_requirement': basic_requirement,
                'positive_values': positive_values
            }
        }
    
    def validate_rule_e(self, df):
        """규칙 e: 나. 지급여력기준금액 계산"""
        print("    🔍 규칙 e 검증 중...")
        
        target_value = self.find_value_by_row_name(df, '나. 지급여력기준금액 (Ⅰ-Ⅱ+Ⅲ)')
        
        if target_value is None:
            return {
                'rule': 'e',
                'passed': False,
                'error': '대상 행을 찾을 수 없음',
                'details': {}
            }
        
        basic_requirement = self.find_value_by_row_name(df, 'Ⅰ.  기본요구자본')
        tax_adjustment = self.find_value_by_row_name(df, 'Ⅱ.  법인세조정액')
        other_requirement = self.find_value_by_row_name(df, 'Ⅲ.  기타  요구자본(1+2+3)')
        
        # 기본요구자본과 법인세조정액은 필수
        if basic_requirement is None or tax_adjustment is None:
            return {
                'rule': 'e',
                'passed': False,
                'error': '필수 행을 찾을 수 없음 (기본요구자본 또는 법인세조정액)',
                'details': {
                    'basic_requirement': basic_requirement,
                    'tax_adjustment': tax_adjustment,
                    'other_requirement': other_requirement
                }
            }
        
        # 기타요구자본이 없으면 0으로 처리
        if other_requirement is None:
            print("    ⚠️ 'Ⅲ. 기타요구자본(1+2+3)' 행을 찾을 수 없어 0으로 처리합니다.")
            other_requirement = 0
        
        expected_value = basic_requirement - tax_adjustment + other_requirement
        difference = abs(target_value - expected_value)
        passed = difference <= self.tolerance
        
        return {
            'rule': 'e',
            'passed': passed,
            'target_value': target_value,
            'expected_value': expected_value,
            'difference': difference,
            'tolerance': self.tolerance,
            'details': {
                'basic_requirement': basic_requirement,
                'tax_adjustment': tax_adjustment,
                'other_requirement': other_requirement,
                'other_requirement_found': other_requirement is not None and other_requirement != 0
            }
        }
    
    def validate_rule_f(self, df):
        """규칙 f: Ⅲ. 기타요구자본(1+2+3) 계산"""
        print("    🔍 규칙 f 검증 중...")
        
        target_value = self.find_value_by_row_name(df, 'Ⅲ.  기타  요구자본(1+2+3)')
        
        # 기타요구자본 행이 없으면 0으로 처리하고 통과로 판단
        if target_value is None:
            print("    ⚠️ 'Ⅲ. 기타요구자본(1+2+3)' 행을 찾을 수 없어 0으로 처리합니다.")
            return {
                'rule': 'f',
                'passed': True,  # 행이 없으면 0으로 처리하여 통과
                'target_value': 0,
                'expected_value': 0,
                'difference': 0,
                'tolerance': self.tolerance,
                'details': {'note': '기타요구자본 행이 없어 0으로 처리됨'}
            }
        
        component_values = {}
        total_expected = 0
        found_components = 0
        
        # 각 구성요소를 검색하고 없으면 0으로 처리
        for row_name in self.validation_rules['f']['component_rows']:
            value = self.find_value_by_row_name(df, row_name)
            if value is not None:
                component_values[row_name] = value
                total_expected += value
                found_components += 1
                print(f"    ✅ '{row_name}': {value}")
            else:
                component_values[row_name] = 0
                print(f"    ⚠️ '{row_name}'을 찾을 수 없어 0으로 처리합니다.")
        
        # 모든 구성요소가 없으면 0으로 처리
        if found_components == 0:
            print("    ⚠️ 기타요구자본 구성요소를 모두 찾을 수 없어 0으로 처리합니다.")
            total_expected = 0
        
        difference = abs(target_value - total_expected)
        passed = difference <= self.tolerance
        
        return {
            'rule': 'f',
            'passed': passed,
            'target_value': target_value,
            'expected_value': total_expected,
            'difference': difference,
            'tolerance': self.tolerance,
            'details': {
                **component_values,
                'found_components': found_components,
                'total_components': len(self.validation_rules['f']['component_rows']),
                'note': f'구성요소 {found_components}/{len(self.validation_rules["f"]["component_rows"])}개 발견'
            }
        }
    
    def validate_rule_g(self, df):
        """규칙 g: 다. 지급여력비율 계산"""
        print("    🔍 규칙 g 검증 중...")
        
        target_value = self.find_value_by_row_name(df, '다.  지급여력비율  :  가  ÷  나  × 100')
        
        if target_value is None:
            return {
                'rule': 'g',
                'passed': False,
                'error': '대상 행을 찾을 수 없음',
                'details': {}
            }
        
        solvency_amount = self.find_value_by_row_name(df, '가. 지급여력금액')
        solvency_standard = self.find_value_by_row_name(df, '나. 지급여력기준금액 (Ⅰ-Ⅱ+Ⅲ)')
        
        if solvency_amount is None or solvency_standard is None or solvency_standard == 0:
            return {
                'rule': 'g',
                'passed': False,
                'error': '필요한 행을 찾을 수 없거나 분모가 0',
                'details': {
                    'solvency_amount': solvency_amount,
                    'solvency_standard': solvency_standard
                }
            }
        
        expected_value = (solvency_amount / solvency_standard) * 100
        difference = abs(target_value - expected_value)
        passed = difference <= self.tolerance
        
        return {
            'rule': 'g',
            'passed': passed,
            'target_value': target_value,
            'expected_value': expected_value,
            'difference': difference,
            'tolerance': self.tolerance,
            'details': {
                'solvency_amount': solvency_amount,
                'solvency_standard': solvency_standard
            }
        }
    
    def validate_company(self, file_info):
        """특정 회사의 disclosure 파일을 검증합니다."""
        folder_name = file_info['folder']
        file_name = file_info['file']
        
        print(f"\n{'='*60}")
        print(f"🏢 {folder_name} 검증 시작")
        print(f"📄 파일: {file_name}")
        print(f"{'='*60}")
        
        # 파일 읽기
        df_dict = self.read_disclosure_file(file_info)
        if df_dict is None:
            return None
        
        results = {
            'company': folder_name,
            'file': file_name,
            'total_rules': 7,
            'passed_rules': 0,
            'failed_rules': 0,
            'rule_results': {}
        }
        
        # kics_ratio 시트에서만 검증 수행
        target_sheet = None
        for sheet_name, df in df_dict.items():
            if 'kics_ratio' in sheet_name.lower():
                target_sheet = sheet_name
                break
        
        if target_sheet is None:
            print(f"⚠️ 'kics_ratio' 시트를 찾을 수 없습니다. 사용 가능한 시트: {list(df_dict.keys())}")
            # 첫 번째 시트를 사용
            target_sheet = list(df_dict.keys())[0]
            print(f"📊 첫 번째 시트 '{target_sheet}'를 사용합니다.")
        
        print(f"\n📊 시트 '{target_sheet}' 검증 중...")
        df = df_dict[target_sheet]
        
        # 각 규칙별로 검증
        rule_functions = {
            'a': self.validate_rule_a,
            'b': self.validate_rule_b,
            'c': self.validate_rule_c,
            'd': self.validate_rule_d,
            'e': self.validate_rule_e,
            'f': self.validate_rule_f,
            'g': self.validate_rule_g
        }
        
        for rule_id, rule_func in rule_functions.items():
            try:
                result = rule_func(df)
                results['rule_results'][f"{target_sheet}_{rule_id}"] = result
                
                if result['passed']:
                    results['passed_rules'] += 1
                    print(f"    ✅ 규칙 {rule_id}: 통과")
                else:
                    results['failed_rules'] += 1
                    print(f"    ❌ 규칙 {rule_id}: 실패 - {result.get('error', '계산 오차')}")
                    if 'difference' in result:
                        print(f"        차이: {result['difference']:.2f} (허용오차: {result['tolerance']})")
            
            except Exception as e:
                print(f"    ⚠️ 규칙 {rule_id} 검증 중 오류: {e}")
                results['failed_rules'] += 1
                results['rule_results'][f"{target_sheet}_{rule_id}"] = {
                    'rule': rule_id,
                    'passed': False,
                    'error': str(e)
                }
        
        # 결과 요약
        print(f"\n📊 {folder_name} 검증 결과:")
        print(f"   총 규칙 수: {results['total_rules']}")
        print(f"   통과: {results['passed_rules']}")
        print(f"   실패: {results['failed_rules']}")
        print(f"   통과율: {(results['passed_rules'] / results['total_rules'] * 100):.1f}%")
        
        return results
    
    def validate_all_companies(self):
        """모든 회사의 disclosure 파일을 검증합니다."""
        print("🚀 Disclosure 파일 정합성 검증 시작")
        print("="*60)
        
        # disclosure 파일 목록 가져오기
        company_files = self.get_company_folders()
        
        if not company_files:
            print("❌ 검증할 disclosure 파일을 찾을 수 없습니다.")
            print("💡 수동으로 폴더 목록을 확인해보세요:")
            print(f"   경로: {self.base_dir}")
            return
        
        print(f"📁 발견된 disclosure 파일 수: {len(company_files)}")
        print(f"🏢 검증 대상: {', '.join([f['folder'] for f in company_files[:5]])}{'...' if len(company_files) > 5 else ''}")
        
        all_results = []
        
        # 각 파일별로 검증 수행
        for i, file_info in enumerate(company_files, 1):
            print(f"\n[{i}/{len(company_files)}] 처리 중...")
            result = self.validate_company(file_info)
            if result:
                all_results.append(result)
        
        # 전체 결과 요약
        self.print_summary(all_results)
        
        # 결과를 엑셀 파일로 저장
        self.save_results_to_excel(all_results)
    
    def print_summary(self, all_results):
        """전체 검증 결과를 요약하여 출력합니다."""
        print(f"\n{'='*80}")
        print("📊 전체 검증 결과 요약")
        print(f"{'='*80}")
        
        total_companies = len(all_results)
        total_rules = sum(r['total_rules'] for r in all_results)
        total_passed = sum(r['passed_rules'] for r in all_results)
        total_failed = sum(r['failed_rules'] for r in all_results)
        
        print(f"🏢 검증된 회사 수: {total_companies}")
        print(f"📋 총 규칙 수: {total_rules}")
        print(f"✅ 통과한 규칙: {total_passed}")
        print(f"❌ 실패한 규칙: {total_failed}")
        print(f"📈 전체 통과율: {(total_passed / total_rules * 100):.1f}%")
        
        # 테이블 형태로 결과 출력
        self.print_results_table(all_results)
    
    def print_results_table(self, all_results):
        """검증 결과를 테이블 형태로 출력합니다."""
        print(f"\n{'='*100}")
        print("📊 검증 결과 테이블 (✅: 통과, ❌: 실패, ⚠️: 오류)")
        print(f"{'='*100}")
        
        # 규칙 목록
        rules = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        rule_descriptions = {
            'a': '지급여력금액',
            'b': '건전성감독기준',
            'c': '보완자본재분류',
            'd': '분산효과',
            'e': '지급여력기준금액',
            'f': '기타요구자본',
            'g': '지급여력비율'
        }
        
        # 헤더 출력
        print(f"{'회사명':<25} {'파일명':<20} ", end="")
        for rule in rules:
            print(f"{rule_descriptions[rule]:<8}", end="")
        print(f"{'통과율':<8}")
        
        # 구분선
        print("-" * 100)
        
        # 각 회사별 결과 출력
        for result in all_results:
            company = result['company']
            file_name = result.get('file', '')
            
            # 파일명이 너무 길면 줄임
            if len(file_name) > 18:
                file_name = file_name[:15] + "..."
            
            print(f"{company:<25} {file_name:<20} ", end="")
            
            # 각 규칙별 결과 확인
            rule_results = {}
            for rule_key, rule_result in result['rule_results'].items():
                if '_' in rule_key:
                    sheet_name, rule_id = rule_key.split('_', 1)
                    if rule_id in rules:
                        rule_results[rule_id] = rule_result
            
            # 각 규칙별 상태 출력
            for rule in rules:
                if rule in rule_results:
                    rule_result = rule_results[rule]
                    if rule_result.get('passed', False):
                        status = "✅"
                    else:
                        if 'error' in rule_result and rule_result['error']:
                            status = "⚠️"  # 오류
                        else:
                            status = "❌"  # 실패
                else:
                    status = "⚠️"  # 규칙을 찾을 수 없음
                
                print(f"{status:<8}", end="")
            
            # 통과율 계산
            pass_rate = (result['passed_rules'] / result['total_rules'] * 100)
            print(f"{pass_rate:>6.1f}%")
        
        print("-" * 100)
        
        # 하단 요약 통계
        print(f"\n📊 규칙별 통과 현황:")
        for rule in rules:
            rule_name = rule_descriptions[rule]
            passed_count = 0
            total_count = 0
            
            for result in all_results:
                for rule_key, rule_result in result['rule_results'].items():
                    if '_' in rule_key:
                        sheet_name, rule_id = rule_key.split('_', 1)
                        if rule_id == rule:
                            total_count += 1
                            if rule_result.get('passed', False):
                                passed_count += 1
            
            if total_count > 0:
                rule_pass_rate = (passed_count / total_count * 100)
                print(f"   {rule}. {rule_name}: {passed_count}/{total_count} ({rule_pass_rate:.1f}%)")
            else:
                print(f"   {rule}. {rule_name}: 데이터 없음")
    
    def save_results_to_excel(self, all_results):
        """검증 결과를 엑셀 파일로 저장합니다."""
        try:
            output_file = "disclosure_validation_results.xlsx"
            
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # 1. 테이블 형태 결과 시트
                self.create_results_table_sheet(writer, all_results)
                
                # 2. 요약 시트
                summary_data = []
                for result in all_results:
                    pass_rate = (result['passed_rules'] / result['total_rules'] * 100)
                    summary_data.append({
                        '회사': result['company'],
                        '파일명': result.get('file', ''),
                        '총규칙수': result['total_rules'],
                        '통과규칙수': result['passed_rules'],
                        '실패규칙수': result['failed_rules'],
                        '통과율(%)': round(pass_rate, 1),
                        '상태': '통과' if pass_rate >= 80 else '주의' if pass_rate >= 60 else '실패'
                    })
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='요약', index=False)
                
                # 3. 상세 결과 시트
                detail_data = []
                for result in all_results:
                    for rule_key, rule_result in result['rule_results'].items():
                        detail_data.append({
                            '회사': result['company'],
                            '파일명': result.get('file', ''),
                            '규칙키': rule_key,
                            '규칙ID': rule_result.get('rule', ''),
                            '통과여부': '통과' if rule_result.get('passed', False) else '실패',
                            '오류메시지': rule_result.get('error', ''),
                            '대상값': rule_result.get('target_value', ''),
                            '예상값': rule_result.get('expected_value', ''),
                            '차이': rule_result.get('difference', ''),
                            '허용오차': rule_result.get('tolerance', '')
                        })
                
                detail_df = pd.DataFrame(detail_data)
                detail_df.to_excel(writer, sheet_name='상세결과', index=False)
            
            print(f"\n💾 검증 결과가 저장되었습니다: {output_file}")
            
        except Exception as e:
            print(f"❌ 결과 저장 실패: {e}")
    
    def create_results_table_sheet(self, writer, all_results):
        """테이블 형태의 결과 시트를 생성합니다."""
        rules = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        rule_descriptions = {
            'a': '지급여력금액',
            'b': '건전성감독기준',
            'c': '보완자본재분류',
            'd': '분산효과',
            'e': '지급여력기준금액',
            'f': '기타요구자본',
            'g': '지급여력비율'
        }
        
        # 테이블 데이터 생성
        table_data = []
        
        for result in all_results:
            row_data = {
                '회사명': result['company'],
                '파일명': result.get('file', '')
            }
            
            # 각 규칙별 결과 확인
            rule_results = {}
            for rule_key, rule_result in result['rule_results'].items():
                if '_' in rule_key:
                    sheet_name, rule_id = rule_key.split('_', 1)
                    if rule_id in rules:
                        rule_results[rule_id] = rule_result
            
            # 각 규칙별 상태 추가
            for rule in rules:
                if rule in rule_results:
                    rule_result = rule_results[rule]
                    if rule_result.get('passed', False):
                        status = "통과"
                    else:
                        if 'error' in rule_result and rule_result['error']:
                            status = "오류"
                        else:
                            status = "실패"
                else:
                    status = "오류"
                
                row_data[f"{rule}. {rule_descriptions[rule]}"] = status
            
            # 통과율 추가
            pass_rate = (result['passed_rules'] / result['total_rules'] * 100)
            row_data['통과율(%)'] = round(pass_rate, 1)
            
            table_data.append(row_data)
        
        # DataFrame 생성 및 엑셀 저장
        table_df = pd.DataFrame(table_data)
        table_df.to_excel(writer, sheet_name='검증결과테이블', index=False)
        
        # 규칙별 통계 시트도 추가
        self.create_rule_statistics_sheet(writer, all_results, rules, rule_descriptions)
    
    def create_rule_statistics_sheet(self, writer, all_results, rules, rule_descriptions):
        """규칙별 통계 시트를 생성합니다."""
        stats_data = []
        
        for rule in rules:
            rule_name = rule_descriptions[rule]
            passed_count = 0
            failed_count = 0
            error_count = 0
            total_count = 0
            
            for result in all_results:
                for rule_key, rule_result in result['rule_results'].items():
                    if '_' in rule_key:
                        sheet_name, rule_id = rule_key.split('_', 1)
                        if rule_id == rule:
                            total_count += 1
                            if rule_result.get('passed', False):
                                passed_count += 1
                            else:
                                if 'error' in rule_result and rule_result['error']:
                                    error_count += 1
                                else:
                                    failed_count += 1
            
            if total_count > 0:
                pass_rate = (passed_count / total_count * 100)
                stats_data.append({
                    '규칙ID': rule,
                    '규칙명': rule_name,
                    '총검증수': total_count,
                    '통과수': passed_count,
                    '실패수': failed_count,
                    '오류수': error_count,
                    '통과율(%)': round(pass_rate, 1)
                })
            else:
                stats_data.append({
                    '규칙ID': rule,
                    '규칙명': rule_name,
                    '총검증수': 0,
                    '통과수': 0,
                    '실패수': 0,
                    '오류수': 0,
                    '통과율(%)': 0
                })
        
        stats_df = pd.DataFrame(stats_data)
        stats_df.to_excel(writer, sheet_name='규칙별통계', index=False)

def main():
    """메인 함수"""
    try:
        validator = DisclosureValidator()
        validator.validate_all_companies()
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"❌ 예상치 못한 오류 발생: {e}")

if __name__ == "__main__":
    main()
