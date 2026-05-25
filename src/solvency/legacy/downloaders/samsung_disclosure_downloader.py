import requests
from bs4 import BeautifulSoup
import os
import time
import random
from datetime import datetime
import re
from urllib.parse import urljoin, urlparse
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
import zipfile
import shutil

from solvency.config import settings

class SamsungPDFDownloader:
    def __init__(self):
        self.base_url = "https://www.samsungfire.com"
        self.disclosure_url = "https://www.samsungfire.com/v2/html/publication/02/J_020_010_001.html"
        self.download_dir = str(settings.disclosure_dir / "KR0008" / "pdf")
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.driver = None
        
    def setup_driver(self):
        """Chrome 드라이버 설정"""
        try:
            chrome_options = Options()
            # chrome_options.add_argument("--headless")  # 디버깅을 위해 헤드리스 모드 비활성화
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-logging")
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_argument("--silent")
            
            # 다운로드 설정
            prefs = {
                "download.default_directory": os.path.abspath(self.download_dir),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
                "download.open_pdf_in_system_reader": False,
                "download.directory_upgrade": True,
                "profile.default_content_setting_values.automatic_downloads": 1
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ Chrome 드라이버 설정 완료")
            return True
        except Exception as e:
            print(f"❌ Chrome 드라이버 설정 실패: {e}")
            return False
    
    def create_download_directory(self):
        """다운로드 디렉토리 생성"""
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
            print(f"📁 다운로드 디렉토리 생성: {self.download_dir}")
    
    def get_page_with_selenium(self, url):
        """Selenium을 사용하여 JavaScript가 실행된 페이지 가져오기"""
        try:
            print("🌐 페이지 로딩 중...")
            self.driver.get(url)
            
            # 페이지가 완전히 로드될 때까지 대기
            wait = WebDriverWait(self.driver, 30)
            
            # 삼성화재 경영공시 테이블이 로드될 때까지 대기
            try:
                wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id='baseMain']/div[2]/section[2]/div/div/table")))
                print("✅ 페이지 로딩 완료")
            except TimeoutException:
                print("⚠️ 테이블을 찾을 수 없습니다. 페이지 구조를 확인합니다.")
            
            # 추가 대기 시간
            time.sleep(5)
            
            return True
            
        except Exception as e:
            print(f"❌ Selenium 페이지 로드 실패: {e}")
            return False
    
    def find_disclosure_links(self):
        """경영공시 PDF 링크들 찾기"""
        try:
            # 삼성화재 경영공시 테이블에서 PDF 링크 찾기
            # 실제 구조에 맞는 선택자 사용
            table = self.driver.find_element(By.XPATH, "//*[@id='baseMain']/div[2]/section[2]/div/div/table")
            rows = table.find_elements(By.TAG_NAME, "tr")
            
            print(f"📋 테이블에서 {len(rows)}개의 행 발견")
            
            disclosure_links = []
            
            for row_idx, row in enumerate(rows):
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    print(f"    행 {row_idx + 1}: {len(cells)}개의 셀 발견")
                    
                    if len(cells) >= 2:
                        # 첫 번째 셀에서 연도 정보 추출
                        year_cell = cells[0]
                        year_text = year_cell.text.strip()
                        print(f"    연도 텍스트: '{year_text}'")
                        
                        # 연도가 유효한지 확인 (FY로 시작하는 패턴)
                        if not re.match(r'FY\s*\d+', year_text):
                            print(f"    ⏭️ 유효하지 않은 연도 형식: {year_text}")
                            continue
                        
                        # 나머지 셀들에서 PDF 링크 찾기
                        for i, cell in enumerate(cells[1:], 1):
                            # 버튼 요소들 찾기
                            buttons = cell.find_elements(By.TAG_NAME, "button")
                            print(f"    셀 {i}: {len(buttons)}개의 버튼 발견")
                            
                            for button_idx, button in enumerate(buttons):
                                button_text = button.text.strip()
                                print(f"      버튼 {button_idx + 1}: '{button_text}'")
                                
                                # 모든 버튼을 PDF 다운로드 버튼으로 간주 (버튼이 있다면 다운로드 버튼일 가능성이 높음)
                                if button_text:  # 텍스트가 있는 버튼은 모두 다운로드 버튼으로 간주
                                    # 분기 정보 추출
                                    quarter_info = self.extract_quarter_info(button_text, i)
                                    
                                    disclosure_links.append({
                                        'year': year_text,
                                        'quarter': quarter_info,
                                        'link_text': button_text,
                                        'element': button
                                    })
                                    print(f"      ✅ PDF 링크 추가: {year_text} {quarter_info}")
                                else:
                                    print(f"      ⚠️ 빈 텍스트 버튼 스킵")
                    
                except Exception as e:
                    print(f"    ❌ 행 {row_idx + 1} 처리 중 오류: {e}")
                    continue
            
            print(f"📋 총 {len(disclosure_links)}개의 PDF 링크 발견")
            return disclosure_links
            
        except Exception as e:
            print(f"❌ 경영공시 링크 찾기 실패: {e}")
            return []
    
    def extract_quarter_info(self, button_text, cell_index):
        """버튼 텍스트에서 분기 정보 추출"""
        print(f"        분기 정보 추출: '{button_text}' (셀 {cell_index})")
        
        # 버튼 텍스트에서 분기 정보 추출
        quarter_patterns = [
            r'(\d+)분기',
            r'(\d+)/\d+분기',
            r'상반기',
            r'하반기',
            r'결산'
        ]
        
        for pattern in quarter_patterns:
            match = re.search(pattern, button_text)
            if match:
                if pattern == r'상반기':
                    result = '상반기'
                elif pattern == r'하반기':
                    result = '하반기'
                elif pattern == r'결산':
                    result = '결산'
                else:
                    result = f"{match.group(1)}분기"
                print(f"        패턴 매치: {pattern} -> {result}")
                return result
        
        # 셀 인덱스로 분기 추정 (삼성화재 테이블 구조에 맞게)
        quarter_map = {
            1: '1분기',
            2: '2분기',
            3: '3분기',
            4: '결산'
        }
        
        result = quarter_map.get(cell_index, f'분기{cell_index}')
        print(f"        셀 인덱스 기반 추정: {result}")
        return result
    
    def is_2023_or_later(self, year_text):
        """연도가 2023년도 이후인지 확인"""
        try:
            # FY25, FY24, FY23 등에서 연도 추출
            year_match = re.search(r'FY\s*(\d+)', year_text)
            if year_match:
                year = int(year_match.group(1))
                # FY25 = 2025년, FY24 = 2024년, FY23 = 2023년
                return year >= 23  # FY23 이상
            return False
        except Exception as e:
            return False
    
    def download_pdf_file(self, disclosure_info):
        """PDF 파일 다운로드"""
        try:
            print(f"🔍 파일 다운로드 시도: {disclosure_info['year']} {disclosure_info['quarter']}")
            
            # 다운로드될 파일명 결정 (ZIP 파일일 가능성 고려)
            filename = f"{disclosure_info['year']}_{disclosure_info['quarter']}"
            pdf_file_path = os.path.join(self.download_dir, filename + ".pdf")
            zip_file_path = os.path.join(self.download_dir, filename + ".zip")
            
            # 기존 파일 존재 여부 확인 (PDF와 ZIP 모두 확인)
            existing_files = []
            for i in range(1, 10):  # (1)부터 (9)까지 확인
                numbered_pdf = os.path.join(self.download_dir, f"{filename}({i}).pdf")
                numbered_zip = os.path.join(self.download_dir, f"{filename}({i}).zip")
                if os.path.exists(numbered_pdf):
                    existing_files.append(f"{filename}({i}).pdf")
                if os.path.exists(numbered_zip):
                    existing_files.append(f"{filename}({i}).zip")
            
            if os.path.exists(pdf_file_path):
                existing_files.append(filename + ".pdf")
            if os.path.exists(zip_file_path):
                existing_files.append(filename + ".zip")
            
            if existing_files:
                print(f"    ⏭️ 스킵 (기존 파일 존재): {', '.join(existing_files)}")
                return {
                    'filename': existing_files[0],
                    'status': 'skipped'
                }
            
            # 기존 파일이 없으면 다운로드
            print(f"    📎 다운로드 중...")
            
            # 버튼 클릭
            disclosure_info['element'].click()
            time.sleep(random.uniform(0.5, 1.0))  # 0.5-1.0초 랜덤 대기
            
            # 다운로드 완료 확인 (여러 번 시도)
            download_success = False
            actual_filename = None
            
            # 최대 15초까지 대기하면서 파일 확인
            for attempt in range(15):
                # PDF 파일 확인
                if os.path.exists(pdf_file_path):
                    download_success = True
                    actual_filename = filename + ".pdf"
                    break
                
                # ZIP 파일 확인
                if os.path.exists(zip_file_path):
                    download_success = True
                    actual_filename = filename + ".zip"
                    break
                
                # (1), (2) 등이 붙은 파일 확인
                for i in range(1, 10):
                    numbered_pdf = os.path.join(self.download_dir, f"{filename}({i}).pdf")
                    numbered_zip = os.path.join(self.download_dir, f"{filename}({i}).zip")
                    
                    if os.path.exists(numbered_pdf):
                        download_success = True
                        actual_filename = f"{filename}({i}).pdf"
                        break
                    if os.path.exists(numbered_zip):
                        download_success = True
                        actual_filename = f"{filename}({i}).zip"
                        break
                
                if download_success:
                    break
                
                time.sleep(1)  # 1초씩 대기
            
            if download_success:
                print(f"    ✅ 다운로드 완료: {actual_filename}")
                
                # ZIP 파일인 경우 자동 처리
                if actual_filename.endswith('.zip'):
                    print(f"    📦 ZIP 파일 자동 처리 시작...")
                    zip_path = os.path.join(self.download_dir, actual_filename)
                    success, file_count = self.process_zip_file(zip_path)
                    if success:
                        print(f"    ✅ ZIP 파일 처리 완료: {file_count}개 파일 추출")
                        return {
                            'filename': f"ZIP에서 {file_count}개 파일 추출",
                            'status': 'downloaded_and_processed'
                        }
                    else:
                        print(f"    ⚠️ ZIP 파일 처리 실패")
                
                return {
                    'filename': actual_filename,
                    'status': 'downloaded'
                }
            else:
                print(f"    ❌ 다운로드 실패: 파일이 생성되지 않음")
                return {
                    'filename': filename,
                    'status': 'failed'
                }
            
        except Exception as e:
            print(f"    ❌ 다운로드 실패: {e}")
            return {
                'filename': filename if 'filename' in locals() else 'unknown',
                'status': 'failed'
            }
    
    def process_zip_file(self, zip_file_path):
        """ZIP 파일을 압축 해제하고 경영공시 파일만 남기기"""
        try:
            print(f"📦 ZIP 파일 처리 중: {os.path.basename(zip_file_path)}")
            
            # 압축 해제할 임시 디렉토리 생성
            temp_dir = os.path.join(self.download_dir, "temp_extract")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)
            
            # ZIP 파일 압축 해제
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            print(f"    📁 압축 해제 완료: {temp_dir}")
            
            # 경영공시 파일만 찾기
            disclosure_files = []
            all_files = []
            
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    all_files.append(file_path)
                    
                    # 파일명에 '경영공시'가 포함된 파일 찾기
                    if '경영공시' in file:
                        disclosure_files.append(file_path)
                        print(f"    ✅ 경영공시 파일 발견: {file}")
            
            # 경영공시 파일이 있으면 처리
            if disclosure_files:
                # 기존 ZIP 파일 삭제
                os.remove(zip_file_path)
                print(f"    🗑️ 원본 ZIP 파일 삭제: {os.path.basename(zip_file_path)}")
                
                # 경영공시 파일들을 다운로드 디렉토리로 이동
                for file_path in disclosure_files:
                    filename = os.path.basename(file_path)
                    new_path = os.path.join(self.download_dir, filename)
                    
                    # 중복 파일 처리
                    counter = 1
                    while os.path.exists(new_path):
                        name, ext = os.path.splitext(filename)
                        new_path = os.path.join(self.download_dir, f"{name}({counter}){ext}")
                        counter += 1
                    
                    shutil.move(file_path, new_path)
                    print(f"    📄 파일 이동: {filename}")
                
                # 임시 디렉토리 삭제
                shutil.rmtree(temp_dir)
                print(f"    🗑️ 임시 디렉토리 삭제")
                
                return True, len(disclosure_files)
            else:
                print(f"    ⚠️ 경영공시 파일을 찾을 수 없습니다.")
                # 임시 디렉토리 삭제
                shutil.rmtree(temp_dir)
                return False, 0
                
        except Exception as e:
            print(f"    ❌ ZIP 파일 처리 실패: {e}")
            # 임시 디렉토리 정리
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return False, 0
    
    def check_and_process_zip_files(self):
        """다운로드 디렉토리에서 ZIP 파일들을 찾아서 처리"""
        try:
            zip_files = [f for f in os.listdir(self.download_dir) if f.endswith('.zip')]
            
            if not zip_files:
                print("📦 처리할 ZIP 파일이 없습니다.")
                return
            
            print(f"📦 {len(zip_files)}개의 ZIP 파일 발견")
            
            total_processed = 0
            total_files_extracted = 0
            
            for zip_file in zip_files:
                zip_path = os.path.join(self.download_dir, zip_file)
                success, file_count = self.process_zip_file(zip_path)
                
                if success:
                    total_processed += 1
                    total_files_extracted += file_count
                else:
                    print(f"    ❌ {zip_file} 처리 실패")
            
            print(f"📦 ZIP 파일 처리 완료: {total_processed}개 처리, {total_files_extracted}개 파일 추출")
            
        except Exception as e:
            print(f"❌ ZIP 파일 처리 중 오류: {e}")
    
    def save_download_info(self, download_results):
        """다운로드 정보를 CSV 파일로 저장"""
        if not download_results:
            return
        
        data = []
        for result in download_results:
            data.append({
                '연도': result['year'],
                '분기': result['quarter'],
                '파일명': result['filename'],
                '상태': result['status'],
                '다운로드_시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        if data:
            df = pd.DataFrame(data)
            csv_path = os.path.join(self.download_dir, f"samsung_download_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"📊 다운로드 정보 저장: {csv_path}")
    
    def run(self):
        """메인 실행 함수"""
        print("🚀 삼성화재 PDF 다운로더 시작")
        print(f"📋 대상 URL: {self.disclosure_url}")
        
        # Chrome 드라이버 설정
        if not self.setup_driver():
            return
        
        try:
            # 다운로드 디렉토리 생성
            self.create_download_directory()
            
            # 페이지 로딩
            if not self.get_page_with_selenium(self.disclosure_url):
                return
            
            # 경영공시 PDF 링크들 찾기
            disclosure_links = self.find_disclosure_links()
            
            if not disclosure_links:
                print("⚠️ 경영공시 PDF 링크를 찾을 수 없습니다.")
                return
            
            print(f"📋 총 {len(disclosure_links)}개의 PDF 링크 발견")
            
            # 2023년도 이후 링크만 필터링
            filtered_links = [link for link in disclosure_links if self.is_2023_or_later(link['year'])]
            
            if not filtered_links:
                print("⚠️ 2023년도 이후 경영공시를 찾을 수 없습니다.")
                return
            
            print(f"📋 2023년도 이후 {len(filtered_links)}개의 PDF 링크 필터링됨")
            
            # PDF 다운로드
            download_results = []
            total_downloaded = 0
            total_skipped = 0
            total_failed = 0
            
            for i, disclosure_info in enumerate(filtered_links, 1):
                print(f"\n📄 PDF {i}/{len(filtered_links)}: {disclosure_info['year']} {disclosure_info['quarter']}")
                
                # PDF 다운로드 시도
                download_result = self.download_pdf_file(disclosure_info)
                
                download_results.append({
                    'year': disclosure_info['year'],
                    'quarter': disclosure_info['quarter'],
                    'filename': download_result['filename'],
                    'status': download_result['status']
                })
                
                # 상태별 카운트
                status = download_result['status']
                if status == 'downloaded':
                    total_downloaded += 1
                elif status == 'skipped':
                    total_skipped += 1
                elif status == 'failed':
                    total_failed += 1
                
                time.sleep(random.uniform(0.5, 1.0))  # 0.5-1.0초 랜덤 대기
            
            # 다운로드 정보 저장
            self.save_download_info(download_results)
            
            # ZIP 파일 처리 (남은 ZIP 파일들 정리)
            print(f"\n📦 남은 ZIP 파일 처리 중...")
            self.check_and_process_zip_files()
            
            print(f"\n🎉 다운로드 완료!")
            print(f"📁 다운로드 위치: {os.path.abspath(self.download_dir)}")
            print(f"📄 새로 다운로드된 파일 수: {total_downloaded}")
            print(f"⏭️ 스킵된 파일 수: {total_skipped}")
            print(f"❌ 실패한 파일 수: {total_failed}")
            print(f"📊 총 처리된 파일 수: {total_downloaded + total_skipped + total_failed}")
            
        finally:
            # 드라이버 정리
            if self.driver:
                self.driver.quit()
                print("🔧 Chrome 드라이버 정리 완료")

def main():
    """메인 함수"""
    print("🚀 삼성화재 PDF 다운로더 시작")
    downloader = SamsungPDFDownloader()
    
    try:
        downloader.run()
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"❌ 예상치 못한 오류 발생: {e}")

if __name__ == "__main__":
    main()
