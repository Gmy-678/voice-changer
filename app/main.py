from dotenv import load_dotenv
load_dotenv()  # 加载 .env 文件

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.config.settings import OUTPUTS_DIR
import os


app = FastAPI(title="Voice Changer API")

# CORS 配置
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# Mount static outputs directory at /outputs
app.mount("/outputs", StaticFiles(directory=OUTPUTS_DIR), name="outputs")


@app.get("/healthz")
async def healthz():
	return {"status": "ok"}
