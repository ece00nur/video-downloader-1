document.addEventListener('DOMContentLoaded', () => {
  // Elementler
  const urlInput = document.getElementById('urlInput');
  const pasteBtn = document.getElementById('pasteBtn');
  const analyzeBtn = document.getElementById('analyzeBtn');
  const alertBox = document.getElementById('alertBox');
  const alertMsg = document.getElementById('alertMsg');
  const previewCard = document.getElementById('previewCard');
  const previewThumb = document.getElementById('previewThumb');
  const previewTitle = document.getElementById('previewTitle');
  const previewAuthor = document.getElementById('previewAuthor');
  const previewDuration = document.getElementById('previewDuration');
  const previewPlatform = document.getElementById('previewPlatform');
  const previewQuality = document.getElementById('previewQuality');
  const startDownloadBtn = document.getElementById('startDownloadBtn');
  const downloadStatusText = document.getElementById('downloadStatusText');
  const installToggleBtn = document.getElementById('installToggleBtn');
  const installContent = document.getElementById('installContent');
  const toggleArrow = document.querySelector('.toggle-arrow');

  let currentVideoData = null;
  let selectedPlatform = 'auto';

  // Platform Seçici
  const platformButtons = document.querySelectorAll('.platform-btn');
  platformButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      platformButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedPlatform = btn.dataset.platform;
      
      const placeholders = {
        auto: 'Video veya Reels bağlantısını buraya yapıştırın...',
        instagram: 'Instagram Reels veya Gönderi linki yapıştırın...',
        pinterest: 'Pinterest Pin veya Video linki yapıştırın...',
        youtube: 'YouTube Video veya Shorts linki yapıştırın...',
        tiktok: 'TikTok video linki yapıştırın...',
        twitter: 'Twitter/X video linki yapıştırın...',
      };
      urlInput.placeholder = placeholders[selectedPlatform] || placeholders.auto;
    });
  });

  // Cihaz Seçici
  const deviceCards = document.querySelectorAll('.device-card');
  deviceCards.forEach(card => {
    card.addEventListener('click', () => {
      deviceCards.forEach(c => c.classList.remove('active'));
      card.classList.add('active');
      const radio = card.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;
    });
  });

  function getSelectedDevice() {
    const checked = document.querySelector('input[name="device"]:checked');
    return checked ? checked.value : 'ios';
  }

  // Panodan Yapıştır Butonu
  pasteBtn.addEventListener('click', async () => {
    try {
      if (navigator.clipboard && navigator.clipboard.readText) {
        const text = await navigator.clipboard.readText();
        if (text) {
          urlInput.value = text.trim();
          showAlert('', false);
          // Otomatik incelemeyi tetikle
          triggerAnalyze();
        }
      } else {
        urlInput.focus();
      }
    } catch (err) {
      urlInput.focus();
    }
  });

  // Enter tuşu ile inceleme
  urlInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      triggerAnalyze();
    }
  });

  // Bildirim gösterme
  function showAlert(msg, isError = true) {
    if (!msg) {
      alertBox.classList.add('hidden');
      return;
    }
    alertMsg.textContent = msg;
    alertBox.className = isError ? 'alert-box' : 'alert-box alert-success';
    alertBox.classList.remove('hidden');
  }

  function setButtonLoading(btn, isLoading, customText = '') {
    const textEl = btn.querySelector('.btn-text');
    const loaderEl = btn.querySelector('.btn-loader');
    btn.disabled = isLoading;
    if (isLoading) {
      textEl.classList.add('hidden');
      loaderEl.classList.remove('hidden');
    } else {
      textEl.classList.remove('hidden');
      loaderEl.classList.add('hidden');
    }
  }

  // Videoyu Analiz Et
  analyzeBtn.addEventListener('click', triggerAnalyze);

  async function triggerAnalyze() {
    const url = urlInput.value.trim();
    if (!url) {
      showAlert('Lütfen indirmek istediğiniz videonun bağlantısını yapıştırın.');
      return;
    }

    showAlert('', false);
    previewCard.classList.add('hidden');
    setButtonLoading(analyzeBtn, true);

    try {
      const res = await fetch('/api/info', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url })
      });

      const result = await res.json();
      if (!result.success) {
        throw new Error(result.detail || 'Video bilgileri alınamadı.');
      }

      currentVideoData = result.data;
      
      // Önizleme Kartını Doldur
      previewThumb.src = currentVideoData.thumbnail;
      previewTitle.textContent = currentVideoData.title;
      previewAuthor.textContent = currentVideoData.author;
      previewDuration.textContent = currentVideoData.duration;
      previewPlatform.textContent = currentVideoData.platform;
      previewQuality.textContent = currentVideoData.resolution;

      previewCard.classList.remove('hidden');
      // Kullanıcıyı önizlemeye kaydır
      previewCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } catch (err) {
      showAlert(err.message || 'Video bulunamadı. Bağlantıyı kontrol ediniz.');
    } finally {
      setButtonLoading(analyzeBtn, false);
    }
  }

  // İndirme İşlemi
  startDownloadBtn.addEventListener('click', async () => {
    if (!currentVideoData) return;

    const device = getSelectedDevice();
    const url = currentVideoData.original_url;

    showAlert('', false);
    setButtonLoading(startDownloadBtn, true);
    downloadStatusText.textContent = 'En Yüksek Kalitede Hazırlanıyor...';

    try {
      const res = await fetch('/api/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, device })
      });

      const result = await res.json();
      if (!result.success) {
        throw new Error(result.detail || 'İndirme sırasında bir hata oluştu.');
      }

      downloadStatusText.textContent = 'Cihaza İndiriliyor...';

      // İndirme Bağlantısını Tetikle
      const a = document.createElement('a');
      a.href = result.download_url;
      a.download = result.display_name;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);

      showAlert('✨ Videonuz başarıyla indirildi! Galerinizden veya İndirilenler klasöründen izleyebilirsiniz.', false);
    } catch (err) {
      showAlert(err.message || 'İndirme tamamlanamadı.');
    } finally {
      setButtonLoading(startDownloadBtn, false);
    }
  });

  // Telefona Kurma Rehberi Akordiyon
  if (installToggleBtn) {
    installToggleBtn.addEventListener('click', () => {
      const isHidden = installContent.classList.toggle('hidden');
      toggleArrow.classList.toggle('open', !isHidden);
    });
  }

  // PWA Service Worker Kaydı
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/static/sw.js').catch(err => {
        console.log('PWA ServiceWorker kaydı atlandı:', err);
      });
    });
  }
});
