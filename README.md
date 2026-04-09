# 🚗 Road Damage Detection System

Website deteksi kerusakan jalan menggunakan **YOLOv11** dan **SAHI (Sliced Aided Hyper Inference)** untuk skripsi S1.

## 📋 Fitur Utama

- ✅ **Dual Detection Mode**:

  - **Baseline**: Inferensi langsung YOLOv11 (cepat ~2-3 detik)
  - **SAHI**: Sliced inference untuk deteksi objek kecil lebih akurat (~5-10 detik)

- 🎯 **Deteksi 4 Kelas Kerusakan Jalan** (RDD2022 Dataset):

  - **D00** - Longitudinal Crack (Retak Memanjang)
  - **D10** - Transverse Crack (Retak Melintang)
  - **D20** - Alligator Crack (Retak Buaya)
  - **D40** - Pothole (Lubang)

- 🎨 **Interface Modern**:

  - Upload gambar via drag-drop atau browse
  - Preview gambar real-time
  - Konfigurasi parameter deteksi dengan slider
  - Visualisasi hasil dengan bounding boxes berwarna
  - Statistik deteksi lengkap
  - Export hasil (PNG + JSON)

- 🔧 **Teknologi Stack**:
  - Backend: Flask 3.0, Python 3.9+, PyTorch 2.1
  - AI/ML: YOLOv11, SAHI, OpenCV
  - Frontend: Bootstrap 5, Vanilla JavaScript
  - Arsitektur: MVC + OOP dengan Singleton Pattern

## 🛠️ Instalasi

### Prasyarat

- Python 3.9 atau lebih tinggi
- pip (Python package manager)
- GPU NVIDIA dengan CUDA (opsional, untuk performa lebih cepat)
- Visual Studio Code (recommended)
- Model YOLOv11 terlatih (`best.pt`)

### Langkah Instalasi

#### 1. Clone atau Download Project

```bash
# Jika menggunakan Git
git clone <repository-url>
cd road-damage-detection

# Atau extract ZIP file ke folder road-damage-detection
```

#### 2. Buat Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Catatan**:

- Install PyTorch dengan CUDA jika punya GPU:
  ```bash
  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
  ```
- Untuk CPU only, gunakan requirements.txt yang sudah ada.

#### 4. Setup Model

Letakkan file model YOLOv11 terlatih Anda (`best.pt`) di folder `weights/`:

```
road-damage-detection/
└── weights/
    └── best.pt    <-- Letakkan model di sini
```

#### 5. Struktur Folder (Akan dibuat otomatis)

```
road-damage-detection/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── routes.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── detector.py
│   │   ├── sahi_processor.py
│   │   └── visualizer.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── detection_service.py
│   │   ├── file_handler.py
│   │   └── image_processor.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── validators.py
│   │   └── helpers.py
│   ├── templates/
│   │   ├── base.html
│   │   └── index.html
│   └── static/
│       ├── css/
│       │   └── style.css
│       └── js/
│           └── main.js
├── uploads/          # Temp uploaded files (auto-created)
├── outputs/          # Detection results (auto-created)
├── weights/          # Model weights
│   └── best.pt      # Your trained model
├── requirements.txt
├── run.py
└── README.md
```

## 🚀 Cara Menjalankan

### Development Mode

```bash
# Pastikan virtual environment aktif
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Jalankan aplikasi
python run.py
```

Aplikasi akan berjalan di: **http://localhost:5000**

### Production Mode (Opsional)

Untuk production, gunakan gunicorn (Linux/Mac) atau waitress (Windows):

```bash
# Install gunicorn (Linux/Mac)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app

# Install waitress (Windows)
pip install waitress
waitress-serve --port=5000 run:app
```

## 📖 Cara Penggunaan

### 1. Upload Gambar

- Klik area upload atau drag-drop gambar
- Format yang didukung: JPG, JPEG, PNG, BMP
- Maksimal ukuran file: 10MB
- Preview akan muncul otomatis

### 2. Konfigurasi Deteksi

**Pilih Mode**:

- **Baseline**: Cepat, cocok untuk gambar resolusi rendah
- **SAHI**: Lebih akurat, cocok untuk objek kecil dan gambar resolusi tinggi

**Atur Parameter**:

- **Confidence Threshold** (0.1-0.9): Ambang batas kepercayaan deteksi
- **Slice Size** (320-1024): Ukuran potongan gambar untuk SAHI
- **Overlap Ratio** (0.1-0.5): Tumpang tindih antar potongan
- **Match Threshold** (0.3-0.7): Threshold IoU untuk merge deteksi

### 3. Jalankan Deteksi

- Klik tombol "Run Detection"
- Tunggu proses selesai (progress akan ditampilkan)
- Hasil akan muncul otomatis

### 4. Lihat Hasil

Hasil deteksi menampilkan:

- Gambar dengan bounding boxes berwarna
- Total deteksi
- Confidence rata-rata
- Waktu inferensi
- Jumlah potongan (untuk SAHI)
- Breakdown per kelas kerusakan

### 5. Export Hasil

- **Download Image**: Simpan gambar hasil deteksi (PNG)
- **Download JSON**: Simpan data deteksi lengkap (JSON)

## 🔧 Konfigurasi

Edit `app/config.py` untuk mengubah pengaturan:

```python
# Device (CUDA/CPU)
DEVICE = 'cuda'  # Ubah ke 'cpu' jika tidak punya GPU

# File settings
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # Max 10MB
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp'}

# Default detection parameters
DEFAULT_CONF_THRESHOLD = 0.25
DEFAULT_SLICE_HEIGHT = 640
DEFAULT_SLICE_WIDTH = 640
DEFAULT_OVERLAP_RATIO = 0.2
DEFAULT_MATCH_THRESHOLD = 0.5
```

## 📊 API Endpoints

Aplikasi menyediakan REST API:

### POST /upload

Upload gambar untuk deteksi

```json
Request: multipart/form-data with 'file'
Response: {
  "success": true,
  "data": {
    "filepath": "path/to/file",
    "filename": "image.jpg",
    "size": 2.5,
    "resolution": "1920x1080"
  }
}
```

### POST /detect

Jalankan deteksi

```json
Request: {
  "filepath": "path/to/image.jpg",
  "mode": "baseline" | "sahi",
  "confidence": 0.25,
  "slice_height": 640,      // untuk SAHI
  "slice_width": 640,       // untuk SAHI
  "overlap_ratio": 0.2,     // untuk SAHI
  "match_threshold": 0.5    // untuk SAHI
}

Response: {
  "success": true,
  "data": {
    "detections": {...},
    "statistics": {...},
    "output": {
      "image": "path/to/result.png",
      "json": "path/to/data.json"
    }
  }
}
```

### GET /download/<path>

Download hasil deteksi

### GET /health

Cek status aplikasi dan model

### GET /config

Ambil konfigurasi aplikasi

## 🐛 Troubleshooting

### Model tidak ditemukan

```
Error: Model weights not found at weights/best.pt
```

**Solusi**: Pastikan file `best.pt` ada di folder `weights/`

### CUDA tidak tersedia

```
CUDA not available. Falling back to CPU.
```

**Solusi**: Normal jika tidak punya GPU NVIDIA. Aplikasi akan jalan di CPU (lebih lambat).

### Import error saat install

```
ERROR: Could not find a version that satisfies the requirement torch
```

**Solusi**:

```bash
# Install PyTorch terlebih dahulu
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Lalu install sisanya
pip install -r requirements.txt
```

### Port sudah digunakan

```
OSError: [Errno 48] Address already in use
```

**Solusi**: Ubah port di `run.py` atau kill process yang menggunakan port 5000

### File terlalu besar

**Solusi**: Kompres gambar atau ubah `MAX_CONTENT_LENGTH` di `config.py`

## 📝 Pengembangan Lebih Lanjut

Beberapa ide untuk pengembangan:

1. **Multi-image batch processing**
2. **Video detection dengan frame extraction**
3. **Database untuk menyimpan history deteksi**
4. **User authentication & management**
5. **Visualisasi statistik dashboard**
6. **Export hasil ke PDF report**
7. **RESTful API documentation (Swagger)**
8. **Deploy ke cloud (Heroku, AWS, GCP)**

## 📄 Lisensi

Project ini untuk keperluan skripsi/penelitian pendidikan.

## 👨‍💻 Author

**Undergraduate Thesis Project**
Sistem Deteksi Kerusakan Jalan Menggunakan YOLOv11 dan SAHI

---

## 🙏 Acknowledgments

- **YOLOv11** - Ultralytics
- **SAHI** - Sliced Aided Hyper Inference
- **Flask** - Web Framework
- **Bootstrap** - UI Framework
- **RDD2022** - Road Damage Dataset

---

Jika ada pertanyaan atau masalah, silakan buat issue atau hubungi maintainer.

**Happy Detecting! 🚗💨**
