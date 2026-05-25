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

from solvency.config import settings

class ShinhanezPDFClickDownloader:
    def __init__(self):
        self.base_url = "https://www.shinhanez.co.kr"
        self.disclosure_url = "https://www.shinhanez.co.kr/static/pub/PUB10000T01.html"
        self.download_dir = str(settings.disclosure_dir / "KR0051")
        
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
            
            # 테이블이 로드될 때까지 대기 (신한EZ손보용 선택자)
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
                print("✅ 페이지 로딩 완료")
            except TimeoutException:
                print("⚠️ 테이블을 찾을 수 없습니다. 페이지 구조를 확인합니다.")
            
            # 추가 대기 시간
            time.sleep(5)
            
            return True
            
        except Exception as e:
            print(f"❌ Selenium 페이지 로드 실패: {e}")
            return False
    
    def find_disclosure_rows(self):
        """경영공시 행들 찾기"""
        try:
            # 신한EZ손보용 선택자 (일반적인 테이블 구조)
            table = self.driver.find_element(By.CSS_SELECTOR, "table")
            rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
            
            disclosure_rows = []
            title_groups = {}  # 제목별로 그룹화
            
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    if len(cells) >= 4:
                        # 제목 셀 (두 번째 셀)
                        title_cell = cells[1]
                        title_text = title_cell.text.strip()
                        
                        # 날짜 셀 (마지막 셀)
                        date_cell = cells[-1]
                        date_text = date_cell.text.strip()
                        
                        # PDF 링크들 찾기 (경영공시만)
                        pdf_links = []
                        
                        # 모든 셀에서 PDF 링크 찾기
                        for cell in cells:
                            links = cell.find_elements(By.CSS_SELECTOR, "a[href*='.pdf'], a[href*='download']")
                            for link in links:
                                href = link.get_attribute('href')
                                if href and ('.pdf' in href.lower() or 'download' in href.lower()):
                                    pdf_links.append({
                                        'type': '경영공시',
                                        'element': link,
                                        'download_attr': link.get_attribute('download') or link.text.strip()
                                    })
                    
                    if title_text and pdf_links:
                        # 제목에서 연도와 기본 제목 추출
                        base_title = self.extract_base_title(title_text)
                        
                        if base_title not in title_groups:
                            title_groups[base_title] = []
                        
                        title_groups[base_title].append({
                            'date': date_text,
                            'title': title_text,
                            'pdf_links': pdf_links,
                            'row': row,
                            'is_supplement': self.is_supplement_title(title_text)
                        })
                        
                except Exception as e:
                    continue
            
            # 각 그룹에서 보완 버전이 있으면 보완 버전만, 없으면 원본 선택
            for base_title, group in title_groups.items():
                if len(group) == 1:
                    # 단일 버전이면 그대로 추가
                    disclosure_rows.append(group[0])
                else:
                    # 여러 버전이 있으면 보완 버전 우선 선택
                    supplement_versions = [item for item in group if item['is_supplement']]
                    if supplement_versions:
                        # 보완 버전이 있으면 보완 버전만 선택
                        selected_item = supplement_versions[0]
                        disclosure_rows.append(selected_item)
                    else:
                        # 보완 버전이 없으면 첫 번째 버전 선택
                        selected_item = group[0]
                        disclosure_rows.append(selected_item)
            
            return disclosure_rows
            
        except Exception as e:
            return []
    
    def extract_base_title(self, title):
        """제목에서 기본 제목 추출 (보완 표시 제거)"""
        # 보완 표시 패턴들
        supplement_patterns = [
            r'\s*\(지급여력비율\s*보완\)\s*$',
            r'\s*\(보완\)\s*$',
            r'\s*\(수정\)\s*$',
            r'\s*\(재공시\)\s*$',
            r'\s*\(추가\)\s*$'
        ]
        
        base_title = title
        for pattern in supplement_patterns:
            base_title = re.sub(pattern, '', base_title, flags=re.IGNORECASE)
        
        return base_title.strip()
    
    def is_supplement_title(self, title):
        """보완/수정 표시가 있는 제목인지 확인"""
        supplement_patterns = [
            r'\(지급여력비율\s*보완\)',
            r'\(보완\)',
            r'\(수정\)',
            r'\(재공시\)',
            r'\(추가\)'
        ]
        
        for pattern in supplement_patterns:
            if re.search(pattern, title, re.IGNORECASE):
                return True
        
        return False
    
    def go_to_next_page(self, current_page_num):
        """다음 페이지로 이동 (직접 페이지 번호 클릭)"""
        try:
            # 다음 페이지 번호 계산
            next_page_num = current_page_num + 1
            
            # 페이지네이션 요소 찾기 (신한EZ손보용)
            pagination_selectors = [
                f"a[href*='page={next_page_num}']",
                f"a[onclick*='{next_page_num}']",
                f"//a[contains(text(), '{next_page_num}')]",
                f"//a[text()='{next_page_num}']"
            ]
            
            next_page_button = None
            for selector in pagination_selectors:
                try:
                    if selector.startswith("//"):
                        # XPath
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        # CSS Selector
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    if elements:
                        next_page_button = elements[0]
                        break
                except:
                    continue
            
            if next_page_button:
                # 다음 페이지 버튼 클릭
                next_page_button.click()
                time.sleep(3)  # 페이지 로딩 대기
                
                # 페이지가 로드될 때까지 대기
                wait = WebDriverWait(self.driver, 10)
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))
                    print(f"    ✅ 페이지 {next_page_num} 로딩 완료")
                    return True
                except TimeoutException:
                    print(f"    ⚠️ 페이지 {next_page_num} 로딩 시간 초과")
                    return False
            else:
                print(f"    ⚠️ 페이지 {next_page_num} 버튼을 찾을 수 없습니다.")
                return False
                
        except Exception as e:
            print(f"    ❌ 페이지 {next_page_num} 이동 실패: {e}")
            return False
    
    def is_2023_or_later(self, title_text):
        """제목에서 연도를 추출하여 2023년도 이후인지 확인"""
        try:
            # 제목에서 연도 패턴 찾기
            year_patterns = [
                r'CY(\d{4})',  # CY2023, CY2024 등
                r'(\d{4})년',  # 2023년, 2024년 등
                r'(\d{4})',    # 2023, 2024 등 (단독)
                r'(\d{4})\s*1분기',  # 2023 1분기, 2024 1분기 등
                r'(\d{4})\s*2분기',  # 2023 2분기, 2024 2분기 등
                r'(\d{4})\s*3분기',  # 2023 3분기, 2024 3분기 등
                r'(\d{4})\s*4분기',  # 2023 4분기, 2024 4분기 등
                r'(\d{4})\s*1/4분기',  # 2023 1/4분기, 2024 1/4분기 등
                r'(\d{4})\s*2/4분기',  # 2023 2/4분기, 2024 2/4분기 등
                r'(\d{4})\s*3/4분기',  # 2023 3/4분기, 2024 3/4분기 등
                r'(\d{4})\s*4/4분기',  # 2023 4/4분기, 2024 4/4분기 등
                r'(\d{4})\s*결산',   # 2023 결산, 2024 결산 등
                r'CY(\d{4})\s*1/4분기',  # CY2023 1/4분기, CY2024 1/4분기 등
                r'CY(\d{4})\s*2/4분기',  # CY2023 2/4분기, CY2024 2/4분기 등
                r'CY(\d{4})\s*3/4분기',  # CY2023 3/4분기, CY2024 3/4분기 등
                r'CY(\d{4})\s*4/4분기',  # CY2023 4/4분기, CY2024 4/4분기 등
            ]
            
            for pattern in year_patterns:
                year_match = re.search(pattern, title_text)
                if year_match:
                    year = int(year_match.group(1))
                    return year >= 2023
            
            return False
            
        except Exception as e:
            return False
    
    def download_pdf_files(self, disclosure_info):
        """PDF 파일들 다운로드"""
        try:
            print(f"🔍 PDF 다운로드 시도: {disclosure_info['title']}")
            
            downloaded_files = []
            
            for pdf_info in disclosure_info['pdf_links']:
                try:
                    # 다운로드될 파일명 결정
                    filename = pdf_info['download_attr'] or f"{disclosure_info['title']}_{pdf_info['type']}.pdf"
                    file_path = os.path.join(self.download_dir, filename)
                    
                    # 기존 파일 존재 여부 확인 (원본 파일명)
                    if os.path.exists(file_path):
                        print(f"    ⏭️ {pdf_info['type']} 스킵 (기존 파일 존재): {filename}")
                        downloaded_files.append({
                            'type': pdf_info['type'],
                            'filename': filename,
                            'status': 'skipped'
                        })
                        continue
                    
                    # (1), (2) 등이 붙은 파일도 확인
                    base_name, ext = os.path.splitext(filename)
                    file_exists = False
                    existing_filename = None
                    
                    for i in range(1, 10):  # (1)부터 (9)까지 확인
                        numbered_filename = f"{base_name}({i}){ext}"
                        numbered_file_path = os.path.join(self.download_dir, numbered_filename)
                        if os.path.exists(numbered_file_path):
                            file_exists = True
                            existing_filename = numbered_filename
                            break
                    
                    if file_exists:
                        print(f"    ⏭️ {pdf_info['type']} 스킵 (기존 파일 존재): {existing_filename}")
                        downloaded_files.append({
                            'type': pdf_info['type'],
                            'filename': filename,
                            'status': 'skipped'
                        })
                        continue
                    
                    # 기존 파일이 없으면 다운로드
                    print(f"    📎 {pdf_info['type']} 다운로드 중...")
                    
                    # PDF 링크 클릭
                    pdf_info['element'].click()
                    time.sleep(random.uniform(0.25, 0.75))  # 0.25-0.75초 랜덤 대기
                    
                    # 다운로드 완료 확인 (여러 번 시도)
                    download_success = False
                    actual_filename = None
                    
                    # 최대 10초까지 대기하면서 파일 확인
                    for attempt in range(10):
                        # 원본 파일명 확인
                        if os.path.exists(file_path):
                            download_success = True
                            actual_filename = filename
                            break
                        
                        # (1), (2) 등이 붙은 파일 확인
                        for i in range(1, 10):
                            numbered_filename = f"{base_name}({i}){ext}"
                            numbered_file_path = os.path.join(self.download_dir, numbered_filename)
                            if os.path.exists(numbered_file_path):
                                download_success = True
                                actual_filename = numbered_filename
                                break
                        
                        if download_success:
                            break
                        
                        time.sleep(1)  # 1초씩 대기
                    
                    if download_success:
                        print(f"    ✅ {pdf_info['type']} 다운로드 완료: {actual_filename}")
                        downloaded_files.append({
                            'type': pdf_info['type'],
                            'filename': actual_filename,
                            'status': 'downloaded'
                        })
                    else:
                        print(f"    ❌ {pdf_info['type']} 다운로드 실패: 파일이 생성되지 않음")
                        downloaded_files.append({
                            'type': pdf_info['type'],
                            'filename': filename,
                            'status': 'failed'
                        })
                    
                except Exception as e:
                    print(f"    ❌ {pdf_info['type']} 다운로드 실패: {e}")
                    downloaded_files.append({
                        'type': pdf_info['type'],
                        'filename': filename if 'filename' in locals() else 'unknown',
                        'status': 'failed'
                    })
            
            return downloaded_files
            
        except Exception as e:
            print(f"❌ PDF 다운로드 실패: {e}")
            return []
    
    def save_download_info(self, download_results):
        """다운로드 정보를 CSV 파일로 저장"""
        if not download_results:
            return
        
        data = []
        for result in download_results:
            files_info = []
            for file_info in result['files']:
                status_text = file_info.get('status', 'unknown')
                files_info.append(f"{file_info['type']}: {file_info['filename']} ({status_text})")
            
            data.append({
                '공시일': result['date'],
                '제목': result['title'],
                '다운로드된_파일': ' | '.join(files_info) if files_info else '다운로드 실패',
                '다운로드_시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        if data:
            df = pd.DataFrame(data)
            csv_path = os.path.join(self.download_dir, f"download_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"📊 다운로드 정보 저장: {csv_path}")
    
    def run(self):
        """메인 실행 함수"""
        print("🚀 신한EZ손보 PDF 클릭 다운로더 시작")
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
            
            # 페이지별로 바로 다운로드
            page_num = 1
            reached_2023 = False
            download_results = []
            total_downloaded = 0
            total_skipped = 0
            total_failed = 0
            
            while True:
                print(f"\n📄 페이지 {page_num} 처리 중...")
                
                # 현재 페이지의 경영공시 행들 찾기
                disclosure_rows = self.find_disclosure_rows()
                
                if not disclosure_rows:
                    print(f"⚠️ 페이지 {page_num}에서 공시를 찾을 수 없습니다.")
                    break
                
                # 2023년도 이후 공시만 필터링하고 바로 다운로드
                filtered_rows = []
                for row in disclosure_rows:
                    title_text = row['title']
                    if self.is_2023_or_later(title_text):
                        filtered_rows.append(row)
                        reached_2023 = True
                
                print(f"    📋 페이지 {page_num}에서 {len(filtered_rows)}개 공시 발견")
                
                # 현재 페이지의 공시들을 바로 다운로드
                for i, disclosure_info in enumerate(filtered_rows, 1):
                    print(f"\n📄 공시 {i}/{len(filtered_rows)}: {disclosure_info['title']}")
                    
                    # PDF 다운로드 시도
                    downloaded_files = self.download_pdf_files(disclosure_info)
                    
                    download_results.append({
                        'date': disclosure_info['date'],
                        'title': disclosure_info['title'],
                        'files': downloaded_files
                    })
                    
                    # 상태별 카운트
                    for file_info in downloaded_files:
                        status = file_info.get('status', 'unknown')
                        if status == 'downloaded':
                            total_downloaded += 1
                        elif status == 'skipped':
                            total_skipped += 1
                        elif status == 'failed':
                            total_failed += 1
                    
                    time.sleep(random.uniform(0.25, 0.75))  # 0.25-0.75초 랜덤 대기
                
                # 2023년도 이전 페이지에 도달했으면 중단
                if reached_2023 and not filtered_rows:
                    print("✅ 2023년도 이전 페이지에 도달했습니다. 수집을 중단합니다.")
                    break
                
                # 다음 페이지로 이동
                if not self.go_to_next_page(page_num):
                    print("⚠️ 다음 페이지가 없습니다.")
                    break
                
                page_num += 1
                time.sleep(2)  # 페이지 로딩 대기
            
            if not download_results:
                print("⚠️ 2023년도 이후 경영공시를 찾을 수 없습니다.")
                return
            
            # 다운로드 정보 저장
            self.save_download_info(download_results)
            
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
    downloader = ShinhanezPDFClickDownloader()
    
    try:
        downloader.run()
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"❌ 예상치 못한 오류 발생: {e}")

if __name__ == "__main__":
    main()








