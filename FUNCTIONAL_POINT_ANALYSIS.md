# Functional Point Analysis (FPA)
# Mangrove Visualization System
# Project: nlplab/Prabu/mangroveviz
# Date: March 30, 2026
# Language: Python/Django
# Analysis Basis: Current implemented features after user-role UI, vector CRUD, raster queue, dashboard, export, and AOI guidance improvements

## 1. Executive Summary

### Project Overview
Mangrove Viewer adalah aplikasi web GIS berbasis Django untuk visualisasi, analisis, dan manajemen data mangrove. Versi saat ini sudah berkembang dari viewer raster sederhana menjadi aplikasi operasional yang mencakup autentikasi user, pemisahan role `viewer/editor/admin`, UI untuk assign role user, upload raster dengan validasi dan progress, queue sederhana untuk job raster berat, status background polling, basemap switcher, klasifikasi klik peta, perhitungan luas raster dan ROI polygon, metadata raster terperinci, CRUD data vektor pada halaman management, export data, dashboard statistik, dan audit trail aktivitas raster.

### Current Size Metrics
- Total Lines of Code: 1455 LOC Python
- Number of Python Files: 19
- Number of HTML Templates: 9
- Main Stack: Django, Django REST Framework, GeoDjango, Leaflet, GDAL, Docker, PostGIS
- Estimated Functional Size: 188 UFP

## 2. Functional Point Count

### 2.1 External Inputs (EI)
External Inputs adalah data atau kontrol yang masuk ke sistem dari user atau sistem eksternal.

| No | Function Name | Description | DET | FTR | Complexity | FP |
|----|---------------|-------------|-----|-----|------------|----|
| 1 | User Registration | Pembuatan akun user baru | 5 | 2 | Average | 4 |
| 2 | User Login | Autentikasi user | 4 | 2 | Average | 4 |
| 3 | User Logout | Terminasi sesi user | 2 | 1 | Simple | 3 |
| 4 | Assign User Role | Admin mengubah role user via UI | 4 | 2 | Average | 4 |
| 5 | Upload Raster via UI/API | Upload GeoTIFF dari management page | 7 | 3 | Average | 4 |
| 6 | Delete Raster | Hapus raster dan artefak terkait | 3 | 2 | Average | 4 |
| 7 | Create/Update Vector Data | Simpan data vektor mangrove dari management page | 7 | 2 | Average | 4 |
| 8 | Delete Vector Data | Hapus data vektor | 2 | 2 | Average | 4 |
| 9 | Search Mangrove Data | Pencarian by name/species/source | 3 | 1 | Simple | 3 |
| 10 | Filter by Bounding Box | Filter vektor berdasarkan extent peta | 4 | 1 | Simple | 3 |
| 11 | Opacity Control | Kontrol opacity raster | 1 | 1 | Simple | 3 |
| 12 | Raster Selection | Pemilihan raster aktif | 2 | 1 | Simple | 3 |
| 13 | Basemap Switching | Ganti street/terrain/satellite basemap | 2 | 1 | Simple | 3 |
| 14 | ROI Polygon Drawing | Gambar polygon untuk analisis area | 5 | 2 | Average | 4 |
| **Total EI** | | | | | | **50** |

### 2.2 External Outputs (EO)
External Outputs adalah data atau informasi yang dihasilkan sistem untuk user.

| No | Function Name | Description | DET | FTR | Complexity | FP |
|----|---------------|-------------|-----|-----|------------|----|
| 1 | Interactive Map Display | Tampilan peta interaktif dengan raster dan vektor | 10 | 3 | Complex | 7 |
| 2 | Raster List API | Daftar raster untuk viewer dan management | 8 | 2 | Average | 5 |
| 3 | Mangrove GeoJSON API | Keluaran data vektor mangrove | 7 | 2 | Average | 5 |
| 4 | Raster Area Output | Luas mangrove/non-mangrove per raster | 6 | 2 | Average | 5 |
| 5 | ROI Area Output | Luas mangrove/non-mangrove pada polygon terpilih | 6 | 2 | Average | 5 |
| 6 | Management Data Page | Tabel raster, vektor, user role, status, dan aksi role-based | 12 | 4 | Complex | 7 |
| 7 | Authentication Pages | Login/register dan status sesi | 5 | 2 | Average | 5 |
| 8 | Raster Metadata Display | Tanggal upload, model, EPSG, ukuran, bbox, status | 8 | 2 | Average | 5 |
| 9 | Audit History Display | Riwayat upload/delete, user, version | 7 | 2 | Average | 5 |
| 10 | Dashboard Statistics | Ringkasan raster, vektor, users, cached area | 8 | 3 | Average | 5 |
| 11 | Export Raster CSV | Keluaran CSV metadata raster | 7 | 2 | Average | 5 |
| 12 | Export Vector GeoJSON | Keluaran GeoJSON data vektor | 7 | 2 | Average | 5 |
| **Total EO** | | | | | | **64** |

### 2.3 External Inquiries (EQ)
External Inquiries adalah query yang mengembalikan informasi tanpa memperbarui file logis internal.

| No | Function Name | Description | DET | FTR | Complexity | FP |
|----|---------------|-------------|-----|-----|------------|----|
| 1 | Map Click Classification | Klik peta untuk deteksi mangrove/non-mangrove | 4 | 2 | Simple | 3 |
| 2 | Health Check | Pemeriksaan status service | 3 | 1 | Simple | 3 |
| 3 | Cached Area Retrieval | Ambil hasil luas raster dari cache | 4 | 1 | Simple | 4 |
| 4 | Raster Status Polling | Auto-refresh status queued/processing/ready/error | 5 | 1 | Simple | 4 |
| 5 | AOI Guidance Inquiry | Instruksi penggunaan AOI di panel viewer | 3 | 1 | Simple | 3 |
| **Total EQ** | | | | | | **17** |

### 2.4 Internal Logical Files (ILF)
Internal Logical Files adalah data logis yang dikelola aplikasi.

| No | File Name | Description | DET | RET | Complexity | FP |
|----|-----------|-------------|-----|-----|------------|----|
| 1 | MangroveSite | Data geometri dan atribut lokasi mangrove | 6 | 3 | Average | 10 |
| 2 | RasterLayer | Metadata raster, status tiles, file reproyeksi, cache area | 12 | 4 | Average | 10 |
| 3 | Audit Log Store | Riwayat upload/delete raster, user, version, timestamp | 7 | 2 | Average | 10 |
| 4 | User Role State | Role user viewer/editor/admin dan kontrol akses | 5 | 2 | Average | 10 |
| **Total ILF** | | | | | | **40** |

### 2.5 External Interface Files (EIF)
External Interface Files adalah file atau layanan eksternal yang direferensikan sistem.

| No | File Name | Description | DET | RET | Complexity | FP |
|----|-----------|-------------|-----|-----|------------|----|
| 1 | GeoTIFF Raster Files | File raster klasifikasi dari proses eksternal | 10 | 1 | Average | 7 |
| 2 | Basemap Tile Services | Street, terrain, satellite tile services | 6 | 1 | Simple | 5 |
| 3 | GDAL Toolchain | gdalinfo, gdalwarp, gdal_calc, gdal2tiles | 6 | 1 | Simple | 5 |
| **Total EIF** | | | | | | **17** |

## 3. Functional Point Calculation

### Unadjusted Function Points (UFP)
- External Inputs (EI): 50 FP
- External Outputs (EO): 64 FP
- External Inquiries (EQ): 17 FP
- Internal Logical Files (ILF): 40 FP
- External Interface Files (EIF): 17 FP
- Total UFP: 50 + 64 + 17 + 40 + 17 = 188 FP

### Value Adjustment Factor (VAF)
Degree of Influence (DI): 45

VAF = 0.65 + (0.01 x DI) = 0.65 + 0.45 = 1.10

### Adjusted Function Points (AFP)
AFP = UFP x VAF = 188 x 1.10 = 206.8

Rounded adjusted size: 207 FP

## 4. Productivity Analysis

### Code Metrics
- LOC: 1455
- UFP: 188
- AFP: 207
- LOC per FP: 1455 / 207 = 7.03 LOC/FP

### Productivity Indicators
- Estimated language productivity: 8-10 FP per person-month for Python/Django
- Estimated effort: 207 / 9 = about 23.0 person-months
- Project size classification: Medium-Large

## 5. Technical Complexity Factors

| Factor | Description | Rating | Impact |
|--------|-------------|--------|--------|
| Data Communications | REST API, GeoJSON, AJAX upload, export, status polling | 4 | High |
| Distributed Processing | Docker, Nginx, DB, web separation | 3 | Medium |
| Performance | Raster processing, queue, tile generation, ROI computation | 5 | High |
| Heavily Used Configuration | Django settings and environment variables | 2 | Low |
| Transaction Rate | Moderate request volume with polling and export | 3 | Medium |
| Online Data Entry | Login, register, upload raster, vector CRUD, role assignment, ROI draw | 5 | High |
| End-user Efficiency | Interactive map, basemap switcher, dashboard, management UI | 5 | High |
| Online Update | UI-based raster/vector management and role-based actions | 5 | High |
| Complex Processing | GDAL reprojection, validation, ROI cutline, tile build, queue handling | 5 | High |
| Reusability | Modular app structure and utility helpers | 3 | Medium |
| Installation Ease | Docker Compose deployment | 4 | High |
| Operational Ease | Health check, cache reuse, audit log, status refresh | 4 | High |
| Multiple Sites | Single deployment target | 1 | Low |
| Facilitate Change | Django modularity and isolated app logic | 3 | Medium |

Total DI: 45

## 6. Quality and Maintainability Notes

### Strengths
- Arsitektur Django tetap modular meskipun fitur bertambah signifikan.
- Management page kini menangani raster, vektor, user role, statistik, export, dan audit dalam satu alur operasional.
- Queue sederhana untuk raster berat membuat processing lebih tertib dibanding thread bebas tanpa antrean.
- AOI/ROI kini lebih jelas dari sisi instruksi pengguna.
- Sistem sudah semakin dekat ke aplikasi operasional GIS, bukan sekadar demo viewer.

### Risks / Gaps
- Queue raster masih berbasis file lock lokal, belum message queue penuh.
- Audit trail masih berbasis file JSONL, belum di database.
- Belum ada automated test suite.
- Role management sudah tersedia di UI tetapi belum punya approval workflow.
- Dokumentasi API masih perlu disinkronkan dengan endpoint dan permission terbaru.

## 7. Current Functional Enhancements Reflected in This Update

1. UI assign role user (`viewer`, `editor`, `admin`).
2. CRUD data vektor pada halaman management.
3. Queue sederhana untuk job raster berat.
4. Dashboard statistik untuk raster, vektor, user, dan cached area.
5. Export data ke CSV dan GeoJSON.
6. AOI guidance yang lebih jelas di halaman peta.
7. Basemap switcher untuk street, terrain, dan satellite.
8. Upload raster dengan progress, validasi, dan status polling.
9. Metadata raster detail dan audit trail aktivitas.

## 8. Recommendations

### Short-Term
1. Sinkronkan API documentation dengan endpoint dan permission terbaru.
2. Tambahkan test untuk role assignment, vector CRUD, dan export.
3. Tambahkan confirmation/logging lebih detail untuk perubahan role user.
4. Tambahkan indikator posisi toolbar AOI yang lebih visual di peta.

### Medium-Term
1. Ganti queue berbasis file lock ke worker queue yang lebih kuat.
2. Pindahkan audit trail ke database agar mudah dicari dan difilter.
3. Tambahkan pagination dan filter di halaman management yang kini semakin padat.
4. Tambahkan export audit log dan statistik dashboard.

### Quality Improvements
1. Bangun test suite untuk views, API, upload validation, vector CRUD, dan workflow raster.
2. Tambahkan monitoring proses GDAL dan timeout handling.
3. Tambahkan retry policy untuk job raster berat.

## 9. Conclusion

Versi terbaru Mangrove Viewer telah berkembang menjadi aplikasi operasional GIS dengan manajemen user, raster, vektor, statistik, export, dan analitik area berbasis ROI. Dibanding versi sebelumnya, functional size meningkat signifikan karena fitur administrasi dan data management sudah masuk ke antarmuka utama aplikasi. Dengan ukuran sekitar 207 adjusted function points, sistem ini berada pada kategori medium-large dan menunjukkan kematangan fungsional yang jauh lebih tinggi dibanding tahap awalnya.

Final Assessment:
- Size: Medium-Large (207 AFP)
- Complexity: High
- Quality: Good
- Maintainability: Good
- Growth Potential: High

---

Analysis updated on March 30, 2026 based on the latest repository implementation.
