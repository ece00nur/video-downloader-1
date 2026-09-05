import os
import socket
import urllib.parse
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from downloader import fetch_media_info, download_media, cleanup_old_downloads, DOWNLOAD_DIR

app = FastAPI(title="Nisa Video İndirici", version="1.0.0")

# CORS izinleri
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

class InfoRequest(BaseModel):
    url: str

class DownloadRequest(BaseModel):
    url: str
    device: str = "ios"  # ios, android, pc, audio

def get_local_ip() -> str:
    """Yerel ağ IP adresini tespit eder."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/health")
async def health():
    return {"status": "ok", "message": "Nisa Video İndirici Aktif 🌸"}

@app.post("/api/info")
async def get_info(req: InfoRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Lütfen geçerli bir video bağlantısı girin.")
    
    try:
        data = fetch_media_info(url)
        return {"success": True, "data": data}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "detail": str(e)}
        )

@app.post("/api/download")
async def process_download(req: DownloadRequest, background_tasks: BackgroundTasks):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Lütfen geçerli bir video bağlantısı girin.")
    
    device = req.device.lower()
    if device not in ["ios", "android", "pc", "audio"]:
        device = "ios"
        
    try:
        result = download_media(url, target_device=device)
        # 30 dk sonra eski dosyaları arka planda temizle
        background_tasks.add_task(cleanup_old_downloads)
        
        return {
            "success": True,
            "filename": result["filename"],
            "display_name": result["display_name"],
            "size_bytes": result["size_bytes"],
            "download_url": f"/api/file/{urllib.parse.quote(result['filename'])}?name={urllib.parse.quote(result['display_name'])}"
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )

@app.get("/api/file/{filename}")
async def get_file(filename: str, name: str = "video.mp4"):
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Dosya bulunamadı veya süresi doldu.")
    
    # Doğru MIME türü
    media_type = "audio/mpeg" if filename.endswith(".mp3") else "video/mp4"
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=name,
        headers={"Content-Disposition": f'attachment; filename="{name}"'}
    )

if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
        
    port = int(os.environ.get("PORT", 8000))
    local_ip = get_local_ip()
    print("=" * 60)
    print("NISA HANIMA OZEL VIDEO INDIRICI BASLATILDI (MelDownloader)")
    print(f"Bilgisayardan erisim: http://localhost:{port}")
    print(f"Telefonda ayni Wi-Fi uzerinden erisim: http://{local_ip}:{port}")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=port)
