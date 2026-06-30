# StatPharm Insight

**StatPharm Insight** adalah project aplikasi Python berbasis Streamlit untuk membantu analisis data penelitian. Aplikasi ini dapat digunakan untuk membaca data CSV, menampilkan statistik deskriptif, menjalankan uji asumsi, memilih uji beda, menjalankan post hoc bila perlu, membuat visualisasi, dan menghasilkan narasi hasil otomatis.

Project ini cocok untuk mahasiswa farmasi, kesehatan, biologi, pangan, kimia, atau bidang lain yang sering membandingkan beberapa kelompok/formula/perlakuan.

---

## Fitur Utama

1. Upload file CSV sendiri atau gunakan data contoh.
2. Pilih kolom kelompok, misalnya formula/perlakuan.
3. Pilih parameter numerik, misalnya transmitan, ukuran partikel, kadar, zona hambat, atau nilai absorbansi.
4. Statistik deskriptif otomatis: n, mean, SD, median, min, max.
5. Visualisasi otomatis:
   - boxplot,
   - grafik rata-rata ± SD.
6. Uji asumsi:
   - Shapiro-Wilk untuk normalitas,
   - Levene untuk homogenitas.
7. Uji beda otomatis:
   - One-Way ANOVA bila data normal dan homogen,
   - Kruskal-Wallis bila asumsi parametrik tidak terpenuhi.
8. Post hoc:
   - Tukey HSD setelah ANOVA signifikan,
   - pairwise Mann-Whitney + koreksi Bonferroni setelah Kruskal-Wallis signifikan.
9. Narasi hasil otomatis yang bisa diedit untuk laporan atau artikel.
10. Export hasil analisis ke Excel dan TXT.

---

## Struktur Folder

```text
statpharm_insight/
│
├── app.py
├── requirements.txt
├── README.md
│
├── data/
│   └── contoh_data_penelitian.csv
│
└── outputs/
```

---

## Cara Menjalankan di Windows

Buka Command Prompt atau Terminal pada folder project, lalu jalankan:

```bash
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run app.py
```

Setelah itu browser akan terbuka otomatis. Bila tidak terbuka, salin alamat lokal yang muncul di terminal, biasanya:

```text
http://localhost:8501
```

---

## Format CSV yang Disarankan

Contoh format data:

```csv
formula,transmitan,ukuran_partikel,pdi,zeta
F1,94.22,88.4,0.342,-22.1
F1,94.35,91.0,0.355,-21.9
F2,95.10,75.3,0.318,-25.4
F2,95.05,73.8,0.321,-25.1
```

Syarat sederhana:

- Minimal ada 1 kolom kelompok, misalnya formula, perlakuan, kelompok, atau konsentrasi.
- Minimal ada 1 kolom angka.
- Untuk Shapiro-Wilk, tiap kelompok idealnya punya minimal 3 data.

---

## Ide Pengembangan agar Layak Publikasi

Judul artikel yang bisa dikembangkan:

**“Development of an Open-Source Python-Based Dashboard for Automated Statistical Analysis of Experimental Research Data”**

Atau versi Indonesia:

**“Pengembangan Dashboard Python Open-Source untuk Analisis Statistik Otomatis pada Data Penelitian Eksperimental”**

Bagian yang bisa dibahas dalam artikel:

1. Latar belakang masalah: banyak mahasiswa/peneliti kesulitan memilih uji statistik yang sesuai.
2. Tujuan: membuat aplikasi sederhana yang membantu analisis data penelitian eksperimental.
3. Metode pengembangan: Python, Streamlit, SciPy, statsmodels, pandas, dan matplotlib.
4. Validasi aplikasi: bandingkan hasil output aplikasi dengan SPSS/JASP/Jamovi untuk beberapa dataset.
5. Hasil: aplikasi dapat membaca data, menghitung deskriptif, menjalankan uji asumsi, uji beda, post hoc, dan export hasil.
6. Kesimpulan: aplikasi dapat menjadi alat bantu analisis awal, terutama untuk pendidikan dan penelitian eksperimental sederhana.

---

## Catatan Penting

Aplikasi ini adalah alat bantu analisis awal. Interpretasi akhir tetap harus disesuaikan dengan desain penelitian, jumlah sampel, karakter data, dan arahan pembimbing atau reviewer.
