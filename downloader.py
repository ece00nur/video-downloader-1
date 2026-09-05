import os
import re
import glob
import time
import shutil
import logging
from typing import Dict, Any, Optional
import yt_dlp
import imageio_ffmpeg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FFmpeg yolunu imageio-ffmpeg üzerinden dinamik olarak alalım
FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
logger.info(f"FFmpeg binary bulundu: {FFMPEG_PATH}")

DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def cleanup_old_downloads(max_age_seconds: int = 1800):
    """30 dakikadan eski geçici dosyaları temizler."""
    try:
        current_time = time.time()
        for filename in os.listdir(DOWNLOAD_DIR):
            file_path = os.path.join(DOWNLOAD_DIR, filename)
            if os.path.isfile(file_path):
                if current_time - os.path.getmtime(file_path) > max_age_seconds:
                    os.remove(file_path)
                    logger.info(f"Eski dosya temizlendi: {filename}")
    except Exception as e:
        logger.warning(f"Temizlik sırasında hata: {e}")

def detect_platform(url: str) -> str:
    """Verilen URL'den platformu otomatik tespit eder."""
    url_lower = url.lower()
    if "instagram.com" in url_lower:
        return "instagram"
    elif "youtube.com" in url_lower or "youtu.be" in url_lower:
        return "youtube"
    elif "pinterest." in url_lower or "pin.it" in url_lower:
        return "pinterest"
    elif "tiktok.com" in url_lower:
        return "tiktok"
    elif "twitter.com" in url_lower or "x.com" in url_lower:
        return "twitter"
    return "auto"

def get_base_ydl_opts() -> Dict[str, Any]:
    """Temel yt-dlp seçenekleri."""
    return {
        "ffmpeg_location": FFMPEG_PATH,
        "quiet": True,
        "no_warnings": True,
        "no_color": True,
        "extract_flat": False,
        "ignoreerrors": False,
        "socket_timeout": 30,
        "retries": 5,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9,tr;q=0.8",
        },
    }

def fetch_media_info(url: str) -> Dict[str, Any]:
    """
    Video/Medya bilgilerini çeker: başlık, kapak resmi, süre, kanal adı vb.
    """
    opts = get_base_ydl_opts()
    opts["noplaylist"] = True
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except Exception as e:
            err_msg = str(e)
            logger.error(f"Bilgi çekme hatası: {err_msg}")
            if "Private video" in err_msg or "login" in err_msg.lower():
                raise RuntimeError("Bu içerik gizli/özel bir hesapta olduğu için erişilemiyor.")
            elif "Video unavailable" in err_msg:
                raise RuntimeError("Video yayından kaldırılmış veya bağlantı geçersiz.")
            else:
                raise RuntimeError(f"Video bilgisi alınamadı: {err_msg}")

    if not info:
        raise RuntimeError("Video detayları tespit edilemedi.")

    # Süre biçimlendirme
    duration_secs = info.get("duration")
    if duration_secs:
        mins, secs = divmod(int(duration_secs), 60)
        hours, mins = divmod(mins, 60)
        if hours > 0:
            duration_str = f"{hours}:{mins:02d}:{secs:02d}"
        else:
            duration_str = f"{mins}:{secs:02d}"
    else:
        duration_str = "Kısa Video / Belirsiz"

    # En iyi kapak görselini bulma
    thumbnail = info.get("thumbnail")
    if not thumbnail and info.get("thumbnails"):
        thumbnail = info["thumbnails"][-1].get("url")

    # Çözünürlük ve kalite tespiti
    resolution = "En Yüksek Kalite (Orijinal)"
    if info.get("resolution"):
        resolution = info["resolution"]
    elif info.get("width") and info.get("height"):
        resolution = f"{info['width']}x{info['height']}"

    return {
        "title": info.get("title", "İsimsiz Video"),
        "thumbnail": thumbnail or "/static/default-thumb.png",
        "duration": duration_str,
        "duration_seconds": duration_secs or 0,
        "author": info.get("uploader") or info.get("channel") or info.get("creator") or "İçerik Üreticisi",
        "platform": detect_platform(url),
        "resolution": resolution,
        "original_url": url,
    }

def download_media(url: str, target_device: str = "ios") -> Dict[str, Any]:
    """
    Medyayı belirtilen cihaz profiline göre en yüksek kalitede indirir.
    
    Cihaz Profilleri:
    - 'ios': iPhone/iPad ile %100 uyumlu MP4 (H.264 video + AAC ses).
             iOS Fotoğraflar uygulaması ve Safari'de doğrudan oynatılabilir.
    - 'android': Android cihazlar için yüksek uyumlu MP4.
    - 'pc': Kayıpsız orijinal en yüksek kalite (4K/1080p, en iyi video + en iyi ses).
    - 'audio': Sadece MP3 (320kbps kristal netliğinde ses).
    """
    cleanup_old_downloads()
    
    timestamp = int(time.time() * 1000)
    out_template = os.path.join(DOWNLOAD_DIR, f"{timestamp}_%(title).50s.%(ext)s")

    opts = get_base_ydl_opts()
    opts["outtmpl"] = out_template
    opts["noplaylist"] = True

    if target_device == "audio":
        opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }],
        })
    elif target_device == "ios":
        # iOS Fotoğraflar / Safari için H.264 ve AAC uyumu
        opts.update({
            "format": "bestvideo[vcodec^=avc1]+bestaudio[acodec^=mp4a]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
            "postprocessors": [{
                "key": "FFmpegVideoRemuxer",
                "preferedformat": "mp4",
            }],
        })
    elif target_device == "android":
        opts.update({
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
        })
    else:  # PC / Universal
        opts.update({
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
        })

    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
        except Exception as e:
            logger.error(f"İndirme hatası: {e}")
            raise RuntimeError(f"İndirme başarısız oldu: {e}")

    # İndirilen dosyayı bulalım
    matches = glob.glob(os.path.join(DOWNLOAD_DIR, f"{timestamp}_*"))
    if not matches:
        raise RuntimeError("İndirilen dosya sistemde bulunamadı.")

    downloaded_file = matches[0]
    filename = os.path.basename(downloaded_file)
    clean_display_name = re.sub(r"^\d+_", "", filename)

    return {
        "file_path": downloaded_file,
        "filename": filename,
        "display_name": clean_display_name,
        "size_bytes": os.path.getsize(downloaded_file),
    }
