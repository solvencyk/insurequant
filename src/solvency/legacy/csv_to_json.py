"""DEPRECATED 2026-05-30: legacy CSV -> insurance_data.json converter.

This is the original early-pipeline path (kics_disclosure.csv ->
insurance_data.json). The active K-ICS master is kics_disclosure.json
(populated by the Docling -> MD -> JSON merge pipeline, read directly by
K-ICS.html). The ``insurance_data.json`` output is no longer consumed
anywhere. File was removed from repo root on 2026-05-30 (cleanup pass).
Module kept under ``src/solvency/legacy/`` for historical reference;
do not call from new code.
"""

import pandas as pd
import json
import os

def convert_csv_to_json():
    try:
        # CSV 파일 읽기 (여러 인코딩 시도)
        encodings = ['utf-8', 'cp949', 'euc-kr', 'latin-1', 'utf-8-sig']
        df = None
        used_encoding = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv('kics_disclosure.csv', encoding=encoding)
                used_encoding = encoding
                print(f"✅ {encoding} 인코딩으로 파일 읽기 성공")
                break
            except (UnicodeDecodeError, UnicodeError) as e:
                print(f"⚠️ {encoding} 인코딩 실패: {e}")
                continue
            except Exception as e:
                print(f"⚠️ {encoding} 인코딩 시도 중 오류: {e}")
                continue
        
        if df is None:
            print("❌ 모든 인코딩 시도 실패")
            return False
        
        print(f"CSV 데이터 로드 완료: {len(df)}개 행 (인코딩: {used_encoding})")
        print(f"컬럼명: {list(df.columns)}")
        
        # JSON으로 변환
        data = df.to_dict('records')
        
        # JSON 파일로 저장
        with open('insurance_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print("JSON 파일 저장 완료: insurance_data.json")
        return True
        
    except Exception as e:
        print(f"변환 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    convert_csv_to_json()


