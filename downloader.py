import os
import re
import glob
import time
import shutil
import logging
import subprocess
from typing import Dict, Any, Optional
import yt_dlp
import imageio_ffmpeg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
logger.info(f"FFmpeg binary: {FFMPEG_PATH}")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def cleanup_old_downloads(max_age_seconds: int = 1800):
    """30 dakikadan eski geçici ve indirilmiş dosyaları temizler."""
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
    """Temel yt-dlp seçenekleri - format kısıtlaması olmadan."""
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
    """Video önizleme ve meta verilerini çeker."""
    opts = get_base_ydl_opts()
    opts["noplaylist"] = True
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except Exception as e:
            err_msg = str(e)
            logger.error(f"Bilgi çekme hatası: {err_msg}")
            if "Private video" in err_msg or "login" in err_msg.lower():
                raise RuntimeError("Bu içerik gizli veya kısıtlı bir hesapta olduğu için erişilemiyor.")
            elif "Video unavailable" in err_msg:
                raise RuntimeError("Video yayından kaldırılmış veya bağlantı geçersiz.")
            else:
                raise RuntimeError(f"Video bilgisi alınamadı: {err_msg}")

    if not info:
        raise RuntimeError("Video detayları tespit edilemedi.")

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

    thumbnail = info.get("thumbnail")
    if not thumbnail and info.get("thumbnails"):
        thumbnail = info["thumbnails"][-1].get("url")

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

def convert_to_target_format(input_path: str, output_path: str, target_device: str):
    """
    İndirilen ham videoyu FFmpeg ile seçilen cihaz profiline dönüştürür.
    
    - 'ios': iPhone/iPad için Apple Photos & Safari ile %100 uyumlu H.264 + AAC + yuv420p MP4.
    - 'android': Android galerileriyle uyumlu yüksek kalite MP4.
    - 'pc': Kayıpsız orijinal en yüksek kalite MP4.
    - 'audio': 320kbps kristal netliğinde MP3 ses dosyası.
    """
    logger.info(f"Dönüştürme başlatıldı: {input_path} -> {output_path} ({target_device})")

    if target_device == "audio":
        cmd = [
            FFMPEG_PATH, "-y",
            "-i", input_path,
            "-vn",
            "-acodec", "libmp3lame",
            "-b:a", "320k",
            output_path
        ]
    elif target_device == "ios":
        # Apple cihazları için katı H.264 Baseline/High + AAC + yuv420p kuralı
        cmd = [
            FFMPEG_PATH, "-y",
            "-i", input_path,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            "-crf", "18",  # Görsel olarak kayıpsız en yüksek kalite
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            output_path
        ]
    elif target_device == "android":
        cmd = [
            FFMPEG_PATH, "-y",
            "-i", input_path,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            "-crf", "18",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            output_path
        ]
    else:  # PC / Orijinal
        cmd = [
            FFMPEG_PATH, "-y",
            "-i", input_path,
            "-c", "copy",
            "-movflags", "+faststart",
            output_path
        ]

    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        logger.warning(f"FFmpeg özel dönüştürme başarısız oldu, genel dönüştürme deneniyor: {proc.stderr[:200]}")
        # Yedek dönüştürme komutu (fail-safe)
        fallback_cmd = [
            FFMPEG_PATH, "-y",
            "-i", input_path,
            output_path
        ]
        fallback_proc = subprocess.run(fallback_cmd, capture_output=True, text=True)
        if fallback_proc.returncode != 0:
            raise RuntimeError(f"FFmpeg dönüştürme hatası: {proc.stderr}")

def download_media(url: str, target_device: str = "ios") -> Dict[str, Any]:
    """
    2 AŞAMALI İNDİRME VE DÖNÜŞTÜRME MOTORU:
    1. Aşama: Orijinal video hangi platformda hangi formattaysa hiçbir kısıtlama olmadan indirilir.
    2. Aşama: İndirilen dosya FFmpeg ile seçilen cihazın (iPhone, Android, PC vb.) formatına dönüştürülür.
    """
    cleanup_old_downloads()

    timestamp = int(time.time() * 1000)
    raw_template = os.path.join(DOWNLOAD_DIR, f"raw_{timestamp}_%(id)s.%(ext)s")

    # 1. AŞAMA: Orijinali neyse en yüksek kalitede çek
    opts = get_base_ydl_opts()
    opts["outtmpl"] = raw_template
    opts["noplaylist"] = True
    opts["format"] = "bestvideo+bestaudio/best"

    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
        except Exception as e:
            logger.error(f"Ham indirme hatası: {e}")
            raise RuntimeError(f"Video indirilemedi: {e}")

    # İndirilen ham dosyayı bul
    raw_matches = glob.glob(os.path.join(DOWNLOAD_DIR, f"raw_{timestamp}_*"))
    if not raw_matches:
        raise RuntimeError("İndirilen ham video dosyası bulunamadı.")

    raw_file = raw_matches[0]
    
    # Temiz başlık oluştur
    raw_title = info.get("title") or "video"
    clean_title = re.sub(r'[\\/*?:"<>|]', "", raw_title).strip()[:50] or "video"

    ext = ".mp3" if target_device == "audio" else ".mp4"
    final_filename = f"{timestamp}_{clean_title}{ext}"
    final_path = os.path.join(DOWNLOAD_DIR, final_filename)

    # 2. AŞAMA: Hedef cihaza göre FFmpeg dönüştürme
    try:
        convert_to_target_format(raw_file, final_path, target_device)
    finally:
        # Ham geçici dosyayı hemen temizle
        if os.path.exists(raw_file):
            try:
                os.remove(raw_file)
            except Exception:
                pass

    if not os.path.exists(final_path):
        raise RuntimeError("Format dönüştürme sonucunda dosya üretilemedi.")

    return {
        "file_path": final_path,
        "filename": final_filename,
        "display_name": f"{clean_title}{ext}",
        "size_bytes": os.path.getsize(final_path),
    }
