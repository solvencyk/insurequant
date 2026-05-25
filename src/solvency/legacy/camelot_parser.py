import camelot
import pandas as pd
import os
from pathlib import Path
import re
import time
import signal
import warnings
import logging
import sys
import contextlib

from solvency.config import settings

class DisclosureParser:
    def __init__(self):
        # 환경변수를 통한 경고 억제
        os.environ['CAMELOT_QUIET'] = '1'
        os.environ['PDFMINER_QUIET'] = '1'
        
        # 경고 메시지 억제 설정
        warnings.filterwarnings('ignore', category=UserWarning)
        warnings.filterwarnings('ignore', category=FutureWarning)
        warnings.filterwarnings('ignore', category=DeprecationWarning)
        
        # camelot 관련 경고 억제
        logging.getLogger('camelot').setLevel(logging.CRITICAL)
        logging.getLogger('pdfminer').setLevel(logging.CRITICAL)
        logging.getLogger('PIL').setLevel(logging.CRITICAL)
        
        # 모든 로거의 레벨을 CRITICAL로 설정
        for logger_name in logging.root.manager.loggerDict:
            logging.getLogger(logger_name).setLevel(logging.CRITICAL)
        
        # 기본 경로 설정
        self.base_input_dir = str(settings.disclosure_dir)
        self.base_output_dir = str(settings.disclosure_dir)
        
        # 보험사 유형 판별을 위한 키워드
        self.life_insurance_keywords = ["생명보험", "생명", "수명", "종신", "정기", "연금"]
        self.damage_insurance_keywords = ["손해보험", "손해", "자동차", "화재", "해상", "재해"]
        # 손해보험사용 키워드 (한 테이블에 두 키워드 모두 포함)
        self.ratio_keywords_damage = ["비례성원칙", "지급여력금액"]
        
        # 생명보험사용 키워드 (두 테이블로 분리)
        self.ratio_keywords_life_1 = ["지급여력금액", "조정준비금"]  # 지급여력금액 테이블
        self.ratio_keywords_life_2 = ["지급여력금액", "비례성원칙"]  # 지급여력기준금액 테이블
        
        self.breakdown_keywords = ["사망위험"]
        
        # 처리할 폴더 리스트 (모든 원보험사)
        self.folders = self.get_all_company_folders()
    
    def get_all_company_folders(self):
        """disclosure 폴더에서 모든 원보험사 폴더를 가져옵니다 (스마트 처리)."""
        try:
            if not os.path.exists(self.base_input_dir):
                print(f"⚠️ 기본 입력 디렉토리가 존재하지 않습니다: {self.base_input_dir}")
                return []
            
            # disclosure 폴더 내의 모든 하위 폴더 가져오기
            all_company_folders = []
            life_company_folders = []
            damage_company_folders = []
            
            for item in os.listdir(self.base_input_dir):
                item_path = os.path.join(self.base_input_dir, item)
                if os.path.isdir(item_path):
                    # pdf 하위 폴더가 있는지 확인
                    pdf_subfolder = os.path.join(item_path, "pdf")
                    if os.path.exists(pdf_subfolder):
                        all_company_folders.append(item)
            
            # 알파벳 순서로 정렬
            all_company_folders.sort()
            
            # KR0068 이후의 원보험사만 필터링
            filtered_company_folders = []
            for item in all_company_folders:
                if item >= "KR0068":
                    filtered_company_folders.append(item)
                    # 보험사 유형 확인
                    insurance_type = self.detect_insurance_type(item)
                    if insurance_type == "life":
                        life_company_folders.append(item)
                    else:
                        damage_company_folders.append(item)
            
            print(f"📁 전체 원보험사 폴더 수: {len(all_company_folders)}")
            print(f"🎯 KR0068 이후 처리 대상 폴더 수: {len(filtered_company_folders)}")
            print(f"🏥 생명보험사 폴더 수: {len(life_company_folders)}")
            print(f"🚗 손해보험사 폴더 수: {len(damage_company_folders)}")
            print(f"🧠 KR0068 이후 원보험사들을 스마트하게 처리합니다 (테이블 구조 자동 파악)")
            
            return filtered_company_folders
            
        except Exception as e:
            print(f"❌ 원보험사 폴더 목록 가져오기 실패: {e}")
            return []
    
    def get_folder_paths(self, folder_name):
        """특정 폴더의 입력/출력 경로를 반환합니다."""
        input_dir = os.path.join(self.base_input_dir, folder_name, "pdf")
        output_dir = os.path.join(self.base_output_dir, folder_name, "parsed")
        
        # 출력 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)
        
        return input_dir, output_dir
    
    def find_pdf_files(self, input_dir):
        """PDF 파일들을 찾습니다."""
        pdf_files = []
        for file in os.listdir(input_dir):
            if file.endswith('.pdf'):
                pdf_files.append(os.path.join(input_dir, file))
        return pdf_files
    
    def extract_tables_with_keywords(self, pdf_path):
        """PDF에서 키워드들이 포함된 테이블을 추출합니다."""
        print(f"📄 PDF 처리 중: {os.path.basename(pdf_path)}")
        
        try:
            # PDF 처리 시작 시간 기록
            start_time = time.time()
            
            # 모든 경고 메시지와 stderr 출력 억제
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                # stderr를 완전히 억제하여 camelot 경고 메시지 차단
                with open(os.devnull, 'w') as devnull:
                    with contextlib.redirect_stderr(devnull):
                        # 로깅 레벨을 임시로 CRITICAL로 설정
                        import logging
                        original_levels = {}
                        for logger_name in ['camelot', 'pdfminer', 'PIL']:
                            logger = logging.getLogger(logger_name)
                            original_levels[logger_name] = logger.level
                            logger.setLevel(logging.CRITICAL)
                        
                        try:
                            # camelot을 사용하여 테이블 추출 (50페이지까지만 처리)
                            # stream flavor로 더 세밀한 추출 시도
                            tables = camelot.read_pdf(
                                pdf_path, 
                                flavor='stream', 
                                pages='1-50',  # 50페이지까지만 처리
                                edge_tol=500,
                                row_tol=5,  # 더 세밀한 행 분할
                                column_tol=5,  # 더 세밀한 열 분할
                                strip_text='\n',
                                split_text=True
                            )
                        finally:
                            # 로깅 레벨을 원래대로 복원
                            for logger_name, level in original_levels.items():
                                logging.getLogger(logger_name).setLevel(level)
            
            # 처리 시간 계산
            processing_time = time.time() - start_time
            print(f"    발견된 테이블 수: {len(tables)} (1-50페이지)")
            print(f"    ⏱️ PDF 처리 시간: {processing_time:.2f}초")
            
            # 처리 시간이 너무 오래 걸린 경우 경고
            if processing_time > 60:  # 60초 이상 걸린 경우
                print(f"    ⚠️ PDF 처리 시간이 {processing_time:.2f}초로 오래 걸렸습니다.")
            
            # 1단계: KICS Ratio 테이블 추출 (보험사 유형에 따라 다르게 처리)
            # PDF 파일 경로에서 폴더명 추출하여 보험사 유형 판별
            folder_name = os.path.basename(os.path.dirname(os.path.dirname(pdf_path)))
            insurance_type = self.detect_insurance_type(folder_name)
            
            # 보험사 유형에 관계없이 스마트하게 테이블 구조 파악
            print(f"    🧠 {folder_name} - 테이블 구조를 자동으로 파악하여 처리")
            ratio_tables = self.extract_smart_ratio_tables(tables)
            
            # 2단계: KICS Breakdown 테이블 추출 (사망위험)
            breakdown_tables = self.extract_breakdown_tables(tables)
            
            return {
                'ratio_tables': ratio_tables,
                'breakdown_tables': breakdown_tables
            }
            
        except Exception as e:
            print(f"    ❌ PDF 처리 실패: {e}")
            # PDF가 손상되었거나 읽을 수 없는 경우를 위한 추가 정보
            if "PDF" in str(e) and "damaged" in str(e).lower():
                print(f"    ⚠️ PDF 파일이 손상되었을 수 있습니다: {os.path.basename(pdf_path)}")
            elif "timeout" in str(e).lower() or "time out" in str(e).lower():
                print(f"    ⏰ PDF 처리 시간 초과: {os.path.basename(pdf_path)}")
            elif "memory" in str(e).lower():
                print(f"    💾 메모리 부족으로 PDF 처리 실패: {os.path.basename(pdf_path)}")
            
            return {'ratio_tables': [], 'breakdown_tables': []}
    
    def extract_damage_insurance_tables(self, tables):
        """손해보험사용 KICS Ratio 테이블들을 추출합니다 (한 테이블에 두 키워드 모두 포함)."""
        print("    🔍 KICS Ratio 테이블 추출 중...")
        
        found_tables = {}
        found_indices = set()
        
        # 0단계: 숫자 데이터가 있는 테이블만 먼저 필터링 (성능 최적화)
        numeric_tables = []
        for i, table in enumerate(tables):
            try:
                df = table.df
                if self.has_numeric_data(df):
                    numeric_tables.append((i, table, df))
                else:
                    print(f"    ⏭️ 테이블 {i+1}에 숫자 데이터가 없어서 패스 (행 수: {len(df)})")
            except Exception as e:
                print(f"    ⚠️ 테이블 {i+1} 숫자 데이터 확인 중 오류: {e}")
                continue
        
        print(f"    📊 숫자 데이터가 있는 테이블 수: {len(numeric_tables)}/{len(tables)}")
        
        # 1단계: 숫자가 있는 테이블들에서만 키워드 검색
        for i, table, df in numeric_tables:
            try:
                table_text = ' '.join(df.values.flatten())
                
                # 두 키워드가 모두 포함되어 있는지 확인
                if all(keyword in table_text for keyword in self.ratio_keywords_damage):
                    print(f"    ✅ 테이블 {i+1}에서 두 키워드 모두 발견! (행 수: {len(df)})")
                    cleaned_df = self.clean_table_data(df)
                    return [{
                        'table_index': i,
                        'table': cleaned_df,
                        'original_table': df,
                        'accuracy': table.accuracy,
                        'whitespace': table.whitespace,
                        'keyword': 'both_keywords'
                    }]
                        
            except Exception as e:
                print(f"    ⚠️ 테이블 {i+1} 처리 중 오류: {e}")
                continue
        
        # 2단계: 숫자가 있는 테이블들에서만 각 키워드별로 검색
        for i, table, df in numeric_tables:
            try:
                table_text = ' '.join(df.values.flatten())
                
                # 각 키워드별로 검색
                for keyword in self.ratio_keywords_damage:
                    if keyword in table_text and keyword not in found_tables:
                        print(f"    ✅ 테이블 {i+1}에서 '{keyword}' 키워드 발견! (행 수: {len(df)})")
                        
                        cleaned_df = self.clean_table_data(df)
                        found_tables[keyword] = {
                            'table_index': i,
                            'table': df,
                            'original_table': df,
                            'accuracy': table.accuracy,
                            'whitespace': table.whitespace,
                            'keyword': keyword
                        }
                        found_indices.add(i)
                        break  # 한 테이블에서 하나의 키워드만 찾으면 다음 테이블로
                        
            except Exception as e:
                print(f"    ⚠️ 테이블 {i+1} 처리 중 오류: {e}")
                continue
        
        # 3단계: 연속된 테이블인지 확인하고 rbind 처리
        return self.combine_ratio_tables(found_tables, found_indices)
    
    def extract_breakdown_tables(self, tables):
        """KICS Breakdown 테이블들을 추출합니다."""
        print("    🔍 KICS Breakdown 테이블 추출 중...")
        
        # 0단계: 숫자 데이터가 있는 테이블만 먼저 필터링 (성능 최적화)
        numeric_tables = []
        for i, table in enumerate(tables):
            try:
                df = table.df
                if self.has_numeric_data(df):
                    numeric_tables.append((i, table, df))
                else:
                    print(f"    ⏭️ 테이블 {i+1}에 숫자 데이터가 없어서 패스 (행 수: {len(df)})")
            except Exception as e:
                print(f"    ⚠️ 테이블 {i+1} 숫자 데이터 확인 중 오류: {e}")
                continue
        
        print(f"    📊 숫자 데이터가 있는 테이블 수: {len(numeric_tables)}/{len(tables)}")
        
        # 1단계: 숫자가 있는 테이블들에서만 키워드 검색
        for i, table, df in numeric_tables:
            try:
                table_text = ' '.join(df.values.flatten())
                
                # 사망위험 키워드 검색
                for keyword in self.breakdown_keywords:
                    if keyword in table_text:
                        print(f"    ✅ 테이블 {i+1}에서 '{keyword}' 키워드 발견! (행 수: {len(df)})")
                        
                        # 콜론(:)이 있는지 확인하여 줄글로 판단
                        if ':' in table_text:
                            print(f"    ⚠️ 테이블 {i+1}에 콜론이 포함되어 줄글로 판단, 다음 테이블 검색...")
                            continue
                        
                        print(f"    ✅ 테이블 {i+1}이 유효한 테이블로 판단되어 채택!")
                        cleaned_df = self.clean_table_data(df)
                        return [{
                            'table_index': i,
                            'table': cleaned_df,
                            'original_table': df,
                            'accuracy': table.accuracy,
                            'whitespace': table.whitespace,
                            'keyword': keyword
                        }]
                        
            except Exception as e:
                print(f"    ⚠️ 테이블 {i+1} 처리 중 오류: {e}")
                continue
        
        print("    ⚠️ 사망위험 키워드를 포함한 유효한 테이블을 찾을 수 없습니다.")
        return []
    
    def combine_ratio_tables(self, found_tables, found_indices):
        """KICS Ratio 테이블들을 합칩니다."""
        if not found_tables:
            print("    ⚠️ 지급여력금액과 비례성원칙 키워드를 포함하는 테이블을 찾을 수 없습니다.")
            return []
        
        # 연속된 테이블인지 확인
        indices_list = sorted(list(found_indices))
        is_consecutive = len(indices_list) == 2 and indices_list[1] - indices_list[0] == 1
        
        if is_consecutive and len(found_tables) == 2:
            print(f"    🔗 연속된 테이블 {indices_list[0]+1}, {indices_list[1]+1}을 rbind로 합칩니다.")
            
            # 두 테이블을 rbind로 합치기
            table1 = list(found_tables.values())[0]['table']
            table2 = list(found_tables.values())[1]['table']
            
            # 열 수 맞추기
            max_cols = max(len(table1.columns), len(table2.columns))
            
            if len(table1.columns) < max_cols:
                for i in range(len(table1.columns), max_cols):
                    table1[f'col_{i}'] = ''
            
            if len(table2.columns) < max_cols:
                for i in range(len(table2.columns), max_cols):
                    table2[f'col_{i}'] = ''
            
            combined_df = pd.concat([table1, table2], ignore_index=True)
            
            return [{
                'table_index': f"combined_ratio_{indices_list[0]+1}_{indices_list[1]+1}",
                'table': combined_df,
                'original_table': combined_df,  # 원본은 합친 결과로 설정
                'accuracy': (list(found_tables.values())[0]['accuracy'] + list(found_tables.values())[1]['accuracy']) / 2,
                'whitespace': (list(found_tables.values())[0]['whitespace'] + list(found_tables.values())[1]['whitespace']) / 2,
                'keyword': 'combined_ratio',
                'source_tables': indices_list
            }]
        else:
            # 연속되지 않거나 하나만 있는 경우, 테이블 출력하지 않고 종료
            print(f"    ⚠️ 연속되지 않은 테이블이거나 키워드가 하나만 발견되어 테이블을 출력하지 않습니다.")
            return []
    
    def combine_keyword_tables(self, keyword_tables):
        """키워드별 테이블들을 합칩니다."""
        combined_tables = []
        
        # 각 키워드별로 테이블 처리
        for keyword, tables in keyword_tables.items():
            if tables:
                # 같은 키워드의 테이블들이 여러 개 있다면 합치기
                if len(tables) > 1:
                    print(f"    🔗 '{keyword}' 키워드 테이블 {len(tables)}개를 합칩니다.")
                    combined_df = pd.concat([t['table'] for t in tables], ignore_index=True)
                    combined_original = pd.concat([t['original_table'] for t in tables], ignore_index=True)
                    
                    combined_tables.append({
                        'table_index': f"combined_{keyword}",
                        'table': combined_df,
                        'original_table': combined_original,
                        'accuracy': sum(t['accuracy'] for t in tables) / len(tables),
                        'whitespace': sum(t['whitespace'] for t in tables) / len(tables),
                        'keyword': keyword,
                        'source_tables': [t['table_index'] for t in tables]
                    })
                else:
                    # 단일 테이블
                    combined_tables.append(tables[0])
        
        # 서로 다른 키워드의 테이블들을 합치기 (rbind)
        if len(combined_tables) > 1:
            print(f"    🔗 서로 다른 키워드 테이블 {len(combined_tables)}개를 rbind로 합칩니다.")
            
            # 모든 테이블의 열 수를 맞추기
            max_cols = max(len(t['table'].columns) for t in combined_tables)
            
            aligned_tables = []
            for table_info in combined_tables:
                df = table_info['table'].copy()
                current_cols = len(df.columns)
                
                # 열 수가 부족하면 빈 열 추가
                if current_cols < max_cols:
                    for i in range(current_cols, max_cols):
                        df[f'col_{i}'] = ''
                
                aligned_tables.append(df)
            
            # rbind로 합치기
            final_df = pd.concat(aligned_tables, ignore_index=True)
            final_original = pd.concat([t['original_table'] for t in combined_tables], ignore_index=True)
            
            return [{
                'table_index': 'combined_all_keywords',
                'table': final_df,
                'original_table': final_original,
                'accuracy': sum(t['accuracy'] for t in combined_tables) / len(combined_tables),
                'whitespace': sum(t['whitespace'] for t in combined_tables) / len(combined_tables),
                'keyword': 'combined',
                'source_tables': [t['table_index'] for t in combined_tables]
            }]
        
        return combined_tables
    
    def extract_smart_ratio_tables(self, tables):
        """보험사 유형에 관계없이 테이블 구조를 자동으로 파악하여 KICS Ratio 테이블을 추출합니다."""
        print("    🔍 스마트 KICS Ratio 테이블 추출 중...")
        
        # 0단계: 숫자 데이터가 있는 테이블만 먼저 필터링
        numeric_tables = []
        for i, table in enumerate(tables):
            try:
                df = table.df
                if self.has_numeric_data(df):
                    numeric_tables.append((i, table, df))
                else:
                    print(f"    ⏭️ 테이블 {i+1}에 숫자 데이터가 없어서 패스 (행 수: {len(df)})")
            except Exception as e:
                print(f"    ⚠️ 테이블 {i+1} 숫자 데이터 확인 중 오류: {e}")
                continue
        
        print(f"    📊 숫자 데이터가 있는 테이블 수: {len(numeric_tables)}/{len(tables)}")
        
        # 1단계: 통합 테이블이 있는지 확인 (손해보험사 방식)
        # "비례성원칙" + "지급여력금액"이 같은 테이블에 있는 경우
        integrated_table = None
        for i, table, df in numeric_tables:
            try:
                table_text = ' '.join(df.values.flatten())
                if all(keyword in table_text for keyword in self.ratio_keywords_damage):
                    print(f"    ✅ 통합 테이블 발견! (테이블 {i+1}, 행 수: {len(df)})")
                    print(f"        📋 '비례성원칙'과 '지급여력금액'이 같은 테이블에 포함됨")
                    integrated_table = {
                        'table_index': i,
                        'table': self.clean_table_data(df),
                        'original_table': df,
                        'accuracy': table.accuracy,
                        'whitespace': table.whitespace,
                        'keyword': 'integrated_table',
                        'type': 'unified'
                    }
                    break
            except Exception as e:
                print(f"    ⚠️ 테이블 {i+1} 처리 중 오류: {e}")
                continue
        
        # 통합 테이블이 발견되면 바로 반환
        if integrated_table:
            return [integrated_table]
        
        # 2단계: 분리된 테이블이 있는지 확인 (생명보험사 방식)
        print(f"    🔍 통합 테이블이 없어서 분리된 테이블을 찾아보겠습니다...")
        
        # 지급여력금액 테이블 찾기 (지급여력금액 + 조정준비금)
        solvency_table = None
        for i, table, df in numeric_tables:
            try:
                table_text = ' '.join(df.values.flatten())
                if all(keyword in table_text for keyword in self.ratio_keywords_life_1):
                    print(f"    ✅ 지급여력금액 테이블 발견! (테이블 {i+1}, 행 수: {len(df)})")
                    solvency_table = {
                        'table_index': i,
                        'table': self.clean_table_data(df),
                        'original_table': df,
                        'accuracy': table.accuracy,
                        'whitespace': table.whitespace,
                        'keyword': 'solvency_amount',
                        'type': 'separated'
                    }
                    break
            except Exception as e:
                print(f"    ⚠️ 테이블 {i+1} 처리 중 오류: {e}")
                continue
        
        # 지급여력기준금액 테이블 찾기 (지급여력금액 + 비례성원칙)
        standard_table = None
        for i, table, df in numeric_tables:
            try:
                table_text = ' '.join(df.values.flatten())
                if all(keyword in table_text for keyword in self.ratio_keywords_life_2):
                    print(f"    ✅ 지급여력기준금액 테이블 발견! (테이블 {i+1}, 행 수: {len(df)})")
                    standard_table = {
                        'table_index': i,
                        'table': self.clean_table_data(df),
                        'original_table': df,
                        'accuracy': table.accuracy,
                        'whitespace': table.whitespace,
                        'keyword': 'solvency_standard',
                        'type': 'separated'
                    }
                    break
            except Exception as e:
                print(f"    ⚠️ 테이블 {i+1} 처리 중 오류: {e}")
                continue
        
        # 3단계: 분리된 테이블들을 rbind로 합치기
        if solvency_table and standard_table:
            print(f"    🔗 두 분리된 테이블을 rbind로 합칩니다.")
            
            # 열 수 맞추기
            max_cols = max(len(solvency_table['table'].columns), len(standard_table['table'].columns))
            
            solvency_df = solvency_table['table'].copy()
            standard_df = standard_table['table'].copy()
            
            if len(solvency_df.columns) < max_cols:
                for i in range(len(solvency_df.columns), max_cols):
                    solvency_df[f'col_{i}'] = ''
            
            if len(standard_df.columns) < max_cols:
                for i in range(len(standard_df.columns), max_cols):
                    standard_df[f'col_{i}'] = ''
            
            combined_df = pd.concat([solvency_df, standard_df], ignore_index=True)
            
            return [{
                'table_index': f"combined_separated_{solvency_table['table_index']+1}_{standard_table['table_index']+1}",
                'table': combined_df,
                'original_table': combined_df,
                'accuracy': (solvency_table['accuracy'] + standard_table['accuracy']) / 2,
                'whitespace': (solvency_table['whitespace'] + standard_table['whitespace']) / 2,
                'keyword': 'combined_separated_tables',
                'type': 'separated_combined',
                'source_tables': [solvency_table['table_index'], standard_table['table_index']]
            }]
        
        elif solvency_table:
            print(f"    ⚠️ 지급여력금액 테이블만 발견되었습니다.")
            return [solvency_table]
        
        elif standard_table:
            print(f"    ⚠️ 지급여력기준금액 테이블만 발견되었습니다.")
            return [standard_table]
        
        else:
            print(f"    ❌ 지급여력 관련 테이블을 찾을 수 없습니다.")
            return []
    
    def detect_insurance_type(self, folder_name):
        """폴더명을 기반으로 보험사 유형을 판별합니다."""
        folder_lower = folder_name.lower()
        
        # 생명보험사 키워드 확인
        for keyword in self.life_insurance_keywords:
            if keyword in folder_lower:
                return "life"
        
        # 손해보험사 키워드 확인
        for keyword in self.damage_insurance_keywords:
            if keyword in folder_lower:
                return "damage"
        
        # 기본값은 손해보험사로 설정 (기존 로직과 호환성 유지)
        return "damage"
    
    def has_numeric_data(self, df):
        """테이블에 숫자 데이터가 포함되어 있는지 확인합니다."""
        try:
            # 빈 DataFrame 체크
            if df.empty:
                return False
            
            # 각 셀을 확인하여 숫자 데이터가 있는지 검사
            numeric_count = 0
            total_cells = 0
            
            for col in df.columns:
                for cell in df[col]:
                    total_cells += 1
                    cell_str = str(cell).strip()
                    if cell_str and cell_str != '' and cell_str != 'nan':
                        # 숫자, 쉼표, 소수점, 마이너스 기호, 괄호만 포함된 셀인지 확인
                        cleaned_cell = cell_str.replace(',', '').replace('.', '').replace('-', '').replace('(', '').replace(')', '')
                        # 정수 또는 소수점이 포함된 숫자인지 확인
                        if cleaned_cell.isdigit() or (cleaned_cell.count('.') == 1 and cleaned_cell.replace('.', '').isdigit()):
                            numeric_count += 1
            
            # 숫자가 포함된 셀이 전체의 40% 이상이어야 유효한 테이블로 판단
            if total_cells > 0:
                numeric_ratio = numeric_count / total_cells
                has_enough_numbers = numeric_ratio >= 0.4  # 40% 이상
                
                if has_enough_numbers:
                    print(f"        📊 숫자 데이터 비율: {numeric_ratio:.1%} ({numeric_count}/{total_cells})")
                else:
                    print(f"        ⚠️ 숫자 데이터 부족: {numeric_ratio:.1%} ({numeric_count}/{total_cells})")
                
                return has_enough_numbers
            
            return False
            
        except Exception as e:
            print(f"    ⚠️ 숫자 데이터 확인 중 오류: {e}")
            return False
    
    def clean_table_data(self, df):
        """테이블 데이터를 정리합니다."""
        # 빈 행 제거
        df = df.dropna(how='all')
        
        # 각 셀의 텍스트 정리
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip()
        
        # 완전히 빈 행 제거
        df = df[~(df == '').all(axis=1)]
        
        # 숫자만 있는 행들만 필터링 (행 이름 부분 제거)
        numeric_rows = []
        for idx, row in df.iterrows():
            # 행의 모든 셀을 확인
            row_values = row.values
            has_numbers = False
            
            for cell in row_values:
                cell_str = str(cell).strip()
                # 숫자, 쉼표, 소수점, 마이너스 기호만 포함된 셀인지 확인
                if cell_str and cell_str.replace(',', '').replace('.', '').replace('-', '').replace('(', '').replace(')', '').isdigit():
                    has_numbers = True
                    break
            
            if has_numbers:
                numeric_rows.append(idx)
        
        # 숫자가 포함된 행들만 선택
        if numeric_rows:
            df = df.loc[numeric_rows].reset_index(drop=True)
        
        return df
    
    def save_tables_to_excel(self, pdf_path, extracted_data, output_dir):
        """추출된 테이블들을 엑셀 파일로 저장합니다."""
        ratio_tables = extracted_data.get('ratio_tables', [])
        breakdown_tables = extracted_data.get('breakdown_tables', [])
        
        if not ratio_tables and not breakdown_tables:
            print("    ⚠️ 저장할 테이블이 없습니다.")
            return None
        
        # PDF 파일명에서 기본 이름 추출
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        excel_filename = f"{pdf_name}_KICS_테이블.xlsx"
        excel_path = os.path.join(output_dir, excel_filename)
        
        try:
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                # 1. KICS Ratio 테이블 저장
                if ratio_tables:
                    ratio_df = ratio_tables[0]['table']
                    ratio_df.to_excel(writer, sheet_name='kics ratio', index=False, header=False)
                    print(f"    ✅ KICS Ratio 테이블 저장 완료 (행 수: {len(ratio_df)})")
                
                # 2. KICS Breakdown 테이블 저장
                if breakdown_tables:
                    breakdown_df = breakdown_tables[0]['table']
                    breakdown_df.to_excel(writer, sheet_name='kics breakdown', index=False, header=False)
                    print(f"    ✅ KICS Breakdown 테이블 저장 완료 (행 수: {len(breakdown_df)})")
                
                # 3. 추출 정보 저장
                info_data = []
                if ratio_tables:
                    for table_info in ratio_tables:
                        info_data.append({
                            '시트명': 'kics ratio',
                            '키워드': table_info.get('keyword', 'unknown'),
                            '행_수': len(table_info['table']),
                            '정확도': table_info['accuracy'],
                            '공백_비율': table_info['whitespace'],
                            '소스_테이블': str(table_info.get('source_tables', []))
                        })
                
                if breakdown_tables:
                    for table_info in breakdown_tables:
                        info_data.append({
                            '시트명': 'kics breakdown',
                            '키워드': table_info.get('keyword', 'unknown'),
                            '행_수': len(table_info['table']),
                            '정확도': table_info['accuracy'],
                            '공백_비율': table_info['whitespace'],
                            '소스_테이블': str(table_info.get('source_tables', []))
                        })
                
                if info_data:
                    info_df = pd.DataFrame(info_data)
                    info_df.to_excel(writer, sheet_name='추출_정보', index=False)
            
            print(f"    ✅ 엑셀 파일 저장 완료: {excel_filename}")
            return excel_path
            
        except Exception as e:
            print(f"    ❌ 엑셀 저장 실패: {e}")
            return None
    
    def process_folder(self, folder_name):
        """특정 폴더의 PDF들을 처리합니다."""
        print(f"\n{'='*60}")
        print(f"📁 폴더 처리 시작: {folder_name}")
        print(f"{'='*60}")
        
        # 폴더 처리 시작 시간 기록
        folder_start_time = time.time()
        
        # 폴더 경로 설정
        input_dir, output_dir = self.get_folder_paths(folder_name)
        
        # 보험사 유형에 따른 키워드 표시
        if self.detect_insurance_type(folder_name) == "life":
            print(f"🔍 생명보험사용 KICS Ratio 키워드:")
            print(f"   - 지급여력금액 테이블: {', '.join(self.ratio_keywords_life_1)}")
            print(f"   - 지급여력기준금액 테이블: {', '.join(self.ratio_keywords_life_2)}")
        else:
            print(f"🔍 손해보험사용 KICS Ratio 키워드: {', '.join(self.ratio_keywords_damage)}")
        
        print(f"🔍 KICS Breakdown 키워드: {', '.join(self.breakdown_keywords)}")
        print(f"📁 입력 디렉토리: {input_dir}")
        print(f"📁 출력 디렉토리: {output_dir}")
        
        # 입력 디렉토리가 존재하는지 확인
        if not os.path.exists(input_dir):
            print(f"⚠️ 입력 디렉토리가 존재하지 않습니다: {input_dir}")
            return 0, 0
        
        # PDF 파일들 찾기
        pdf_files = self.find_pdf_files(input_dir)
        
        if not pdf_files:
            print("⚠️ PDF 파일을 찾을 수 없습니다.")
            return 0, 0
        
        print(f"📄 발견된 PDF 파일 수: {len(pdf_files)}")
        
        # 이미 파싱된 PDF 파일들 확인
        already_parsed = set()
        if os.path.exists(output_dir):
            for excel_file in os.listdir(output_dir):
                if excel_file.endswith('.xlsx'):
                    # 엑셀 파일명에서 PDF 파일명 추출 (예: "CY2025 1／4분기_경영공시_KICS_테이블.xlsx" -> "CY2025 1／4분기_경영공시")
                    excel_name = excel_file.replace('_KICS_테이블.xlsx', '')
                    # PDF 파일명과 정확히 매칭되는지 확인
                    for pdf_file in pdf_files:
                        pdf_name = os.path.splitext(os.path.basename(pdf_file))[0]
                        if excel_name == pdf_name:  # 정확한 매칭
                            already_parsed.add(pdf_file)
                            print(f"    ⏭️ 이미 파싱됨: {os.path.basename(pdf_file)} -> {excel_file}")
                            break
        
        if already_parsed:
            print(f"⏭️ 이미 파싱된 PDF 파일 수: {len(already_parsed)}")
            # 파싱되지 않은 PDF만 필터링
            pdf_files = [pdf for pdf in pdf_files if pdf not in already_parsed]
            print(f"📄 파싱할 PDF 파일 수: {len(pdf_files)}")
        
        folder_processed = 0
        folder_tables_found = 0
        
        for pdf_path in pdf_files:
            print(f"\n{'='*50}")
            
            # 키워드가 포함된 테이블 추출
            extracted_data = self.extract_tables_with_keywords(pdf_path)
            
            if extracted_data['ratio_tables'] or extracted_data['breakdown_tables']:
                # 엑셀로 저장
                excel_path = self.save_tables_to_excel(pdf_path, extracted_data, output_dir)
                if excel_path:
                    folder_processed += 1
                    folder_tables_found += len(extracted_data['ratio_tables']) + len(extracted_data['breakdown_tables'])
            else:
                print(f"    ⚠️ 키워드가 포함된 테이블을 찾을 수 없습니다.")
        
        # 폴더 처리 완료 시간 계산
        folder_processing_time = time.time() - folder_start_time
        
        print(f"\n📊 {folder_name} 폴더 처리 완료!")
        print(f"📄 처리된 PDF 파일 수: {folder_processed}")
        print(f"📊 추출된 테이블 수: {folder_tables_found}")
        print(f"⏱️ 폴더 총 처리 시간: {folder_processing_time:.2f}초")
        
        return folder_processed, folder_tables_found
    
    def run(self):
        """메인 실행 함수"""
        print("🚀 PDF 테이블 추출기 시작")
        
        # 전체 실행 시작 시간 기록
        total_start_time = time.time()
        
        if not self.folders:
            print("❌ 처리할 원보험사 폴더를 찾을 수 없습니다.")
            print(f"📁 확인된 경로: {self.base_input_dir}")
            return
        
        print(f"📁 처리할 폴더: {', '.join(self.folders)}")
        
        total_processed = 0
        total_tables_found = 0
        
        # 각 폴더별로 순차 처리
        for folder in self.folders:
            folder_processed, folder_tables_found = self.process_folder(folder)
            total_processed += folder_processed
            total_tables_found += folder_tables_found
        
        # 전체 실행 완료 시간 계산
        total_processing_time = time.time() - total_start_time
        
        print(f"\n{'='*60}")
        print("🎉 전체 처리 완료!")
        print(f"📄 총 처리된 PDF 파일 수: {total_processed}")
        print(f"📊 총 추출된 테이블 수: {total_tables_found}")
        print(f"⏱️ 전체 총 실행 시간: {total_processing_time:.2f}초")
        print(f"📁 저장 위치: {self.base_output_dir}")

def main():
    """메인 함수"""
    try:
        # 전역적으로 모든 경고 메시지 억제
        warnings.filterwarnings('ignore')
        
        # 환경변수 설정으로 추가 경고 억제
        os.environ['PYTHONWARNINGS'] = 'ignore'
        os.environ['CAMELOT_QUIET'] = '1'
        
        # stderr를 임시로 억제
        with open(os.devnull, 'w') as devnull:
            with contextlib.redirect_stderr(devnull):
                parser = DisclosureParser()
                parser.run()
                
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"❌ 예상치 못한 오류 발생: {e}")

if __name__ == "__main__":
    main()
