import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(sys.argv[0])))

import re,json
from bs4 import BeautifulSoup
import requests,time
from cachecontrol import CacheControl 
from cachecontrol.caches.file_cache import FileCache
import fitz
from io import BytesIO
from urllib.parse import urljoin

def extract_data(pdfio:BytesIO,page_index:int = 0) -> list:
    return_list = []

    document = fitz.open(stream=pdfio)

    tables = document[page_index].find_tables()

    if tables.tables:
        for table in tables:
            for data in table.extract():
                first_data = str(data[0])

                search_result = re.sub(r"\D","",first_data)
                if bool(search_result):
                    type_data = "None"
                    if len(data) == 3:
                        type_data = data[2]

                    return_list.append({"num":search_result,"ans":data[1],"type":type_data})
                

    document.close()
    return return_list

session = requests.Session()
# sessionをラップしたcached_sessionを作る。
# キャッシュはファイルとして .webcache ディレクトリ内に保存する。
cached_session = CacheControl(session, cache=FileCache('./datas/.webcache'))

# 最新の一覧を IPA から取得 (失敗時は保存済み HTML にフォールバック)
IPA_PAGE_URL = os.environ.get("IPA_PAGE_URL", "https://www.ipa.go.jp/shiken/about/menjo-fe.html")
try:
    page_res = session.get(IPA_PAGE_URL, timeout=30)
    page_res.raise_for_status()
    page_res.encoding = page_res.apparent_encoding
    read_data = page_res.text
except Exception as e:
    print(f"ページ取得失敗、ローカル HTML を使用: {e}")
    with open("./ipa_fe_html.html","r",encoding="utf-8") as readhtml:
        read_data = readhtml.read()

soup = BeautifulSoup(read_data,"html.parser")

elems = soup.find_all(href=re.compile(r"(www\.ipa\.go\.jp)?/shiken/about/.*tokurei"))

base_dir = "./datas"

def is_target(elem):
    parts = os.path.basename(urljoin(IPA_PAGE_URL, elem.attrs['href'])).split("_")
    return parts[0] == "tokurei" and parts[-1].endswith(".pdf") and len(parts) > 2 and parts[1] in ("Mondai", "ans")

def fmt(sec):
    sec = int(sec)
    return f"{sec // 60}分{sec % 60:02d}秒" if sec >= 60 else f"{sec}秒"

total = sum(1 for e in elems if is_target(e))
done = 0
start = time.time()
print(f"取得対象: {total} 件", flush=True)

datass = {}
for elem in elems:
    href = urljoin(IPA_PAGE_URL, elem.attrs['href'])

    file_name = str(href.split("/")[-1])

    name_splits = file_name.split("_")

    if name_splits[0] != "tokurei":
        continue
    
    if not name_splits[-1].endswith(".pdf"):
        continue
    
    data_number = str(name_splits[2])

    putdir = os.path.join(base_dir,data_number)

    if data_number in datass:
        add_data = datass[data_number]
    else:
        #print(data_number[4:6])
        add_data = {
            "year":str(data_number[:4]),
            "month":str(data_number[4:6]),
        }
    
    try:
        os.makedirs(putdir)
    except:
        pass
    
    is_ans = False

    if name_splits[1] == "Mondai":
        mondai_path = os.path.join(putdir,file_name).replace("\\","/")
        add_data["mondai"] = mondai_path
        add_data["mondai_url"] = href
    elif name_splits[1] == "ans":
        ans_path = os.path.join(putdir,file_name).replace("\\","/")
        add_data["ans"] = ans_path
        add_data["ans_url"] = href
        is_ans = True
    else:
        continue
    
    res = cached_session.get(href)

    urlData = res.content

    with open(os.path.join(putdir,file_name),"wb") as writepdf:
        writepdf.write(urlData)

    if is_ans:
        bio = BytesIO(urlData)
        add_data["count"] = len(extract_data(bio))
        bio.close()

    datass[data_number] = add_data

    time.sleep(1)

    done += 1
    elapsed = time.time() - start
    remaining = elapsed / done * (total - done)
    print(f"[{done}/{total}] {file_name} | 経過 {fmt(elapsed)} / 残り約 {fmt(remaining)}", flush=True)

with open(os.path.join(base_dir,"config.json"),"w",encoding="utf-8") as write_config:
    json.dump(datass,write_config)
