from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn
from fastapi.responses import FileResponse,HTMLResponse
from starlette.middleware.cors import CORSMiddleware # 追加
import json,re,hashlib
from pathlib import Path
from starlette import status

#問題パス
fe_config_path = "./extractor/datas/config.json"

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


app.mount("/static", StaticFiles(directory="static"), name="static")

def build_index_html() -> str:
    """static の JS/CSS の URL に内容のハッシュを付ける。
    CDN (Cloudflare) や ブラウザに古い JS が残って、新しい HTML と食い違うのを防ぐ。"""
    html = Path("./static/index.html").read_text(encoding="utf-8")

    def add_version(m):
        path = Path(m.group(1))
        if not path.is_file():
            return m.group(0)
        digest = hashlib.md5(path.read_bytes()).hexdigest()[:10]
        return f'"{m.group(1)}?v={digest}"'

    return re.sub(r'"(\./static/[^"?]+\.(?:js|css))"', add_version, html)

index_html = build_index_html()

@app.get("/")
def index():
    return HTMLResponse(index_html, headers={"Cache-Control": "no-cache"})

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

if __name__ == "__main__":
    uvicorn.run(app,host="127.0.0.1",port=bindport)