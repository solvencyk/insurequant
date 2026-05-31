# -*- coding: utf-8 -*-
"""Probe Content-Disposition filenames for a few Hana crossDownload.do IDs to learn
the period naming, without saving files. Read-only (HEAD/partial GET)."""
import sys, ssl, urllib.request, urllib.parse
sys.stdout.reconfigure(encoding="utf-8")
CTX = ssl.create_default_context(); CTX.check_hostname=False; CTX.verify_mode=ssl.CERT_NONE
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

def cd(idv):
    url=f"https://www.hanafn.com:8002/download/{idv}/crossDownload.do"
    req=urllib.request.Request(url, headers={"User-Agent":UA,"Referer":"https://www.hanafn.com/ir/financial/databookDetail.do","Accept":"*/*","Range":"bytes=0-3"})
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=40) as r:
            disp=r.headers.get("Content-Disposition","")
            ct=r.headers.get("Content-Type","")
            data=r.read(4)
            # try decode disp filename
            name=disp
            try:
                # RFC5987 filename*=UTF-8''...
                if "filename*" in disp:
                    part=disp.split("filename*",1)[1]
                    part=part.split("''",1)[-1].strip('";')
                    name=urllib.parse.unquote(part)
                elif "filename=" in disp:
                    raw=disp.split("filename=",1)[1].strip().strip('";')
                    # often latin1-encoded utf8/euc-kr
                    try: name=raw.encode("latin1").decode("utf-8")
                    except:
                        try: name=raw.encode("latin1").decode("euc-kr")
                        except: name=raw
            except Exception as e:
                name=f"{disp} ||decodeerr {e}"
            print(f"{idv}\t{ct}\t{data!r}\t{name}")
    except Exception as e:
        print(f"{idv}\tERR {e}")

if __name__=="__main__":
    ids=sys.argv[1:]
    for i in ids: cd(i)
