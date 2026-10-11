#!/bin/bash
cd /c/Users/sangwook.cho/Desktop/insurequant
PY=C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
for s in "손익분해PL" "CSM워터폴" "CSM상각"; do
  echo "##### $s"
  PYTHONIOENCODING=utf-8 $PY scripts/sync_master_xlsx_sheet.py "$s" 2>&1 | grep -v "^    INSERT" | cut -c1-220 | head -40
  echo "exit=${PIPESTATUS[0]}"
done
echo ALLDONE
