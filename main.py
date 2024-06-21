from fastapi import FastAPI,File,status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
from fastapi.responses import FileResponse
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
from io import BytesIO
from starlette.middleware.cors import CORSMiddleware # 追加
import time,fitz,re,json
import os

#問題パス
fe_config_path = "./extractor/datas/config.json"

class LimitUploadSize(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, max_upload_size: int) -> None:
        super().__init__(app)
        self.max_upload_size = max_upload_size

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method == 'POST':
            if 'content-length' not in request.headers:
                return Response(status_code=status.HTTP_411_LENGTH_REQUIRED)
            content_length = int(request.headers['content-length'])
            if content_length > self.max_upload_size:
                return Response(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        return await call_next(request)

bindip = "0.0.0.0"
bindport = 11188

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,   # 追記により追加
    allow_methods=["*"],      # 追記により追加
    allow_headers=["*"]       # 追記により追加
)


app.add_middleware(LimitUploadSize, max_upload_size=10000000)  # ~50MB

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def index():
    return FileResponse(path="./static/index.html", media_type="text/html")

@app.get("/ping")
def index():
    return {"message":"pong"}

def read_config(config_path):
    with open(config_path,"r",encoding="utf-8") as read_config:
        read_data = json.load(read_config)

    return_data = {}
    for year_key in read_data.keys():
        year_str = read_data[year_key]["year"]
        month_str = read_data[year_key]["month"]
        mondai_count = read_data[year_key]["count"]

        if mondai_count == 0:
            continue

        return_data[str(year_key)] = f"{year_str}年 {month_str}月\t問題数 : {mondai_count}問"

    return return_data


@app.get("/get_fe_mondais")
async def get_mondais():
    return read_config(fe_config_path)

@app.get("/get_mondai/{mondai_type}/{mondai_index}")
async def get_mondais(mondai_type : str,mondai_index : str):
    return_data = {}

    if mondai_type == "fe":
        with open(fe_config_path,"r",encoding="utf-8") as read_config:
            read_data = json.load(read_config)
            
        if not mondai_index in read_data.keys():
            return JSONResponse({
                "message":"Not Found",
            },status_code=status.HTTP_404_NOT_FOUND)

        with open("./extractor/datas/" + read_data[mondai_index]["datajson"],"r",encoding="utf-8") as read_mondai:
            mondai_data = json.load(read_mondai)
        
        return_data["data"] = mondai_data["data"]
        return_data["mondai_url"] = read_data[mondai_index]["mondai_url"]

    return return_data

@app.post("/upload")
async def upload_file(file: bytes = File(...)):
    try:
        fio = BytesIO(file)
        
        score_sorted = extract_data(fio,1)

        fio.close()
        return {"data":score_sorted}

    except:
        import traceback
        traceback.print_exc()

        return {"Error":"server error"}


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
                if bool(search_result):
                    type_data = "None"
                    if len(data) == 3:
                        type_data = data[2]

                    return_list.append({"num":search_result,"ans":data[1],"type":type_data})
                

    print(f"Find Time : {time.time() - find_time}")

    document.close()
    return return_list

if __name__ == "__main__":
    uvicorn.run(app,host="127.0.0.1",port=bindport)