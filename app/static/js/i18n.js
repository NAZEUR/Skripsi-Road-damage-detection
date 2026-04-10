const translations = {
    en: {
        "app.title": "Road Damage Detection - Undergraduate Thesis System",
        "app.title.short": "Road Damage Detection",
        "nav.home": "Home",
        "nav.about": "About",
        "user.label": "User: [Student Name]",
        "sidebar.input_config": "INPUT CONFIGURATION",
        "upload.label": "Road Imagery",
        "upload.hint": "JPG/PNG, Max 10MB",
        "info.file": "File:",
        "info.size": "Size:",
        "info.resolution": "Resolution:",
        "btn.clear": "Clear",
        "sidebar.model": "DETECTION MODEL",
        "model.baseline": "Baseline",
        "model.sahi": "Sliced Inference",
        "sidebar.confidence": "CONFIDENCE THRESHOLD",
        "sidebar.slice": "SLICE SIZE",
        "sidebar.overlap": "OVERLAP RATIO",
        "sidebar.match": "MATCH THRESHOLD",
        "btn.run": "Run Analysis",
        "status.system": "System Status: ",
        "status.online": "Online",
        "status.gpu": "GPU: ",
        "header.original": "ORIGINAL IMAGE PREVIEW",
        "header.result": "DETECTION RESULT",
        "empty.original": "No image uploaded",
        "btn.upload": "Upload Image",
        "empty.result": "Detection not run yet",
        "loading.text": "Processing detection...",
        "sidebar.session": "SESSION ANALYSIS",
        "defects.total": "Total Defects",
        "metrics.avg_conf": "Avg Confidence",
        "metrics.time": "Inference Time",
        "sidebar.details": "CATEGORIZED DETAILS",
        "cat.pothole": "D40 Potholes",
        "cat.long": "D00 Longitudinal Cracks",
        "cat.trans": "D10 Transverse Cracks",
        "cat.allig": "D20 Alligator Cracks",
        "btn.download": "Download Results (PNG/JSON)",
        "btn.stats": "View Statistics",
        "sidebar.blocks": "DETECTION CLASSES",
        "leg.pothole": "D40 - Pothole",
        "leg.long": "D00 - Longitudinal Crack",
        "leg.trans": "D10 - Transverse Crack",
        "leg.allig": "D20 - Alligator Crack",
        "modal.title": "Detection Statistics",
        "btn.close": "Close",
        "btn.export": "Export JSON",
        "footer.text": "© 2024 Road Damage Detection System | Undergraduate Thesis Project"
    },
    id: {
        "app.title": "Deteksi Kerusakan Jalan - Sistem Skripsi",
        "app.title.short": "Deteksi Kerusakan Jalan",
        "nav.home": "Beranda",
        "nav.about": "Tentang",
        "user.label": "Pengguna: [Nama Mahasiswa]",
        "sidebar.input_config": "KONFIGURASI INPUT",
        "upload.label": "Citra Jalan",
        "upload.hint": "JPG/PNG, Maks 10MB",
        "info.file": "Berkas:",
        "info.size": "Ukuran:",
        "info.resolution": "Resolusi:",
        "btn.clear": "Hapus",
        "sidebar.model": "MODEL DETEKSI",
        "model.baseline": "Dasar (Baseline)",
        "model.sahi": "Inferensi Terbagi (SAHI)",
        "sidebar.confidence": "AMBANG KEPERCAYAAN",
        "sidebar.slice": "UKURAN POTONGAN",
        "sidebar.overlap": "RASIO TUMPANG TINDIH",
        "sidebar.match": "AMBANG KECOCOKAN",
        "btn.run": "Jalankan Analisis",
        "status.system": "Status Sistem: ",
        "status.online": "Daring",
        "status.gpu": "GPU: ",
        "header.original": "PRATINJAU CITRA ASLI",
        "header.result": "HASIL DETEKSI",
        "empty.original": "Belum ada citra terunggah",
        "btn.upload": "Unggah Citra",
        "empty.result": "Deteksi belum dijalankan",
        "loading.text": "Memproses deteksi... Mohon tunggu",
        "sidebar.session": "ANALISIS SESI",
        "defects.total": "Total Kerusakan",
        "metrics.avg_conf": "Rerata Kepercayaan",
        "metrics.time": "Waktu Inferensi",
        "sidebar.details": "RINCIAN KATEGORI",
        "cat.pothole": "D40 Lubang",
        "cat.long": "D00 Retak Memanjang",
        "cat.trans": "D10 Retak Melintang",
        "cat.allig": "D20 Retak Buaya",
        "btn.download": "Unduh Hasil (PNG/JSON)",
        "btn.stats": "Lihat Statistik",
        "sidebar.blocks": "KELAS DETEKSI",
        "leg.pothole": "D40 - Lubang (Pothole)",
        "leg.long": "D00 - Retak Memanjang",
        "leg.trans": "D10 - Retak Melintang",
        "leg.allig": "D20 - Retak Buaya",
        "modal.title": "Statistik Deteksi",
        "btn.close": "Tutup",
        "btn.export": "Ekspor JSON",
        "footer.text": "© 2024 Sistem Deteksi Kerusakan Jalan | Proyek Skripsi"
    }
};

let currentLang = localStorage.getItem('appLang') || 'en';

function setLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('appLang', lang);
    applyTranslations();
    
    // Update language dropdown UI if exists
    const langLabel = document.getElementById('currentLangLabel');
    if (langLabel) {
        langLabel.textContent = lang.toUpperCase();
    }
}

function t(key) {
    return translations[currentLang][key] || key;
}

function applyTranslations() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[currentLang][key]) {
            el.textContent = translations[currentLang][key];
        }
    });

    // Handle Title specifically
    const titleKey = "app.title";
    if (translations[currentLang][titleKey]) {
        document.title = translations[currentLang][titleKey];
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    applyTranslations();
    const langLabel = document.getElementById('currentLangLabel');
    if (langLabel) {
        langLabel.textContent = currentLang.toUpperCase();
    }
});
