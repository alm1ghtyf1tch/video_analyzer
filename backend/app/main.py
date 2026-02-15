from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Video Analyzer (No AI)")
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",
                   "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "web" / "static")),
    name="static",
)

INDEX_HTML = (BASE_DIR / "web" / "templates" / "index.html").read_text(encoding="utf-8")

@app.get("/", response_class=HTMLResponse)
def home():
    return HTMLResponse(content=INDEX_HTML)
