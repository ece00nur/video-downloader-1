# 🌸 MelDownloader 

Instagram, Pinterest, YouTube, TikTok ve Twitter gibi platformlardaki videoları hiçbir reklam veya bekleme süresi olmadan, **en yüksek ve orijinal kalitede** indiren, toz pembe temalı modern PWA web uygulaması.

---

## ✨ Özellikler

- 🎀 **Toz Pembe & Pastel Estetik Tema**: Göz yormayan, zarif ve modern cam efektli (glassmorphism) tasarım.
- 📱 **Mobil ve PWA Desteği**: iPhone (Safari) ve Android (Chrome) üzerinden tek tıkla telefona uygulama olarak kurulur (App Store / Play Store gerekmez).
- 🎬 **Orijinal & Kayıpsız Kalite**: Arka plandaki `yt-dlp` ve `FFmpeg` motoru sayesinde videoları sıkıştırmadan en yüksek çözünürlükte (4K / 1080p) indirir.
- 🎯 **Cihaza Göre Format Seçimi**:
  - 🍏 **iPhone / iPad**: Apple Galeri ve QuickTime ile %100 uyumlu `H.264 + AAC MP4` (oynatmama veya siyah ekran sorunu yaşatmaz).
  - 🤖 **Android**: Yüksek kaliteli Android MP4.
  - 💻 **PC / Orijinal**: Maksimum çözünürlükte kayıpsız birleştirme.
  - 🎵 **Sadece Müzik (MP3)**: 320kbps kristal netliğinde ses ayıklama.
- 

---

## 💻 1. Kendi Bilgisayarınızda Çalıştırma

Bilgisayarınızda çalıştırmak için:
1. Klasördeki **`Baslat.bat`** dosyasına çift tıklayın.
2. Otomatik olarak tarayıcınız açılacak ve uygulama ekranı gelecektir (`http://localhost:8000`).

---



### Adım 1: Kodları GitHub'a Yükleyin
Klasörde bir terminal / komut satırı açarak şu komutları sırayla çalıştırın:
```bash
git init
git add .
git commit -m "video indirme uygulaması"
git branch -M main
```
GitHub'da (`github.com`) yeni bir repository açın (Örn: `video downloader`) ve oradaki yönlendirmeye göre bağlayıp gönderin:
```bash
git remote add origin https://github.com/KULLANICI_ADINIZ/video-downloader.git
git push -u origin main
```

### Adım 2: Render.com'da 1 Tıkla Yayına Alın
1. [Render.com](https://render.com) adresine gidin ve **"Sign in with GitHub"** diyerek ücretsiz kaydolun.
2. Dashboard'da sağ üstten **"New +" ➔ "Web Service"** seçeneğine tıklayın.
3. GitHub deponuzu (`video-downloader`) listeden seçin ve **"Connect"** deyin.
4. Ayarlar otomatik algılanır:
   - **Name**: `video downloader` (veya istediğiniz bir isim)
   - **Region**: Frankfurt (Avrupa - Türkiye'ye en hızlısı)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: **Free**
5. En alttaki **"Create Web Service"** butonuna basın.

Yaklaşık 1-2 dakika içinde size `https://video-downloader.onrender.com` gibi harika bir canlı link verecektir!

---


### 🍏 iPhone İçin:
1. Linki **Safari** tarayıcısında açsın.
2. Alttaki **Paylaş** simgesine (içinden yukarı ok çıkan kare) dokunsun.
3. Aşağı kaydırıp **"Ana Ekrana Ekle"** desin.
4. Artık telefonunun ana ekranında toz pembe **MelDownloader** simgesi belirecek ve tıkladığında tarayıcı çubuğu olmadan tam bir iPhone uygulaması gibi açılacak!

### 🤖 Android İçin:
1. Linki **Chrome** tarayıcısında açsın.
2. Sağ üstteki **üç noktaya** (⋮) dokunsun.
3. **"Uygulamayı Yükle"** veya **"Ana Ekrana Ekle"** seçeneğine dokunsun.
4. Uygulamalar listesine eklenecektir.

---

## 🛠️ Kullanılan Teknolojiler
- **Backend**: Python 3.12, FastAPI, Uvicorn
- **Video Motoru**: yt-dlp, FFmpeg (imageio-ffmpeg)
- **Frontend**: HTML5, CSS3 (Modern Glassmorphism), Responsive Vanilla JS
- **Mobil Entegrasyon**: PWA (Progressive Web App), Service Worker, Web App Manifest
