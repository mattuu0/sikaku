import fitz
import re
import time
from io import BytesIO
import json,os

page_index = 1

def extract_data(pdfio:BytesIO,page_index:int = 0) -> list:
    return_list = []

    load_time = time.time()
    document = fitz.open(stream=pdfio)

    print(f"Load TIme : {time.time() - load_time}")

    find_time = time.time()

    tables = document[page_index].find_tables()

    if tables.tables:
        for table in tables:
            for data in table.extract():
                first_data = str(data[0])

                search_result = re.sub(r"\D","",first_data)
                print(search_result)
                if bool(search_result):
                    type_data = "None"
                    if len(data) == 3:
                        type_data = data[2]
                    
                    ans = data[1]

                    if ans == None:
                        ans = data[3]

                    return_list.append({"num":search_result,"ans":ans,"type":type_data})
                

    print(f"Find Time : {time.time() - find_time}")

    return return_list

with open("./datas/config.json","r",encoding="utf-8") as read_config:
    config_data = json.load(read_config)

for key in config_data.keys():
    ans_path = config_data[key]["ans"]

    with open(ans_path,"rb") as readpdf:
        read_data = readpdf.read()

    bio = BytesIO(read_data)
    result = extract_data(bio,1)

    if len(result) != 0:
        print(result)

    data_path = os.path.dirname(ans_path) + "/data.json"
    write_path = "./" + os.path.basename(os.path.dirname(ans_path)) + "/data.json"
    with open(data_path,"w",encoding="utf-8") as write_data:
        json.dump({
            "year" : config_data[key]["year"],
            "month" : config_data[key]["month"],
            "size" : len(result),
            "data" : result
        },write_data)

    config_data[key]["count"] = len(result)
    config_data[key]["datajson"] = write_path
    bio.close()

with open("./datas/config.json","w",encoding="utf-8") as write_config:
    json.dump(config_data,write_config)

"""
with open("./datas/20240128/tokurei_ans_20240128_FE.pdf","rb") as readpdf:
    read_data = readpdf.read()
    
    bio = BytesIO(read_data)
    result = extract_data(bio,1)

    print(result)
"""