# MangroveViz

MangroveViz adalah aplikasi web berbasis Django untuk visualisasi dan manajemen data mangrove berbentuk raster dan vektor. Aplikasi ini menyediakan peta interaktif, upload raster GeoTIFF, manajemen data vektor, statistik ringkas, serta kontrol akses berbasis role.

## Fitur Utama

- Visualisasi raster mangrove pada peta interaktif Leaflet
- Upload raster GeoTIFF melalui antarmuka web
- Validasi raster sebelum diproses
- Pembuatan tiles raster dan status proses `queued / processing / ready / error`
- Perhitungan luas mangrove dan non-mangrove dalam hektare dan km2
- Perhitungan luas berbasis AOI/ROI polygon di peta
- CRUD data vektor mangrove melalui halaman management
- Dashboard statistik dan export data CSV/GeoJSON
- Role user `viewer`, `editor`, dan `admin`
- Audit log sederhana untuk upload dan delete raster
- Basemap switcher untuk kebutuhan interpretasi spasial

## Stack

- Django 5
- Django REST Framework
- GeoDjango
- PostgreSQL + PostGIS
- Leaflet
- Gunicorn
- Nginx
- Docker Compose

## Role Akses

- `viewer`: melihat halaman peta
- `editor`: upload raster dan mengelola data vektor
- `admin`: semua hak editor, hapus data, dan ubah role user

## Menjalankan Dengan Docker

1. Siapkan file `.env` di root project.
2. Jalankan:

```bash
docker compose up --build
```

3. Aplikasi tersedia di:

- Web app: `http://localhost:3031`
- pgAdmin: `http://localhost:5050` jika service pgAdmin diaktifkan

Service utama:

- `db`: PostGIS
- `web`: Django + Gunicorn
- `nginx`: reverse proxy dan static/media server
- `pgadmin`: opsional

## Konfigurasi Environment

Contoh variabel penting di `.env`:

```env
DJANGO_SECRET_KEY=replace-with-a-long-random-string
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=mangrove_db
POSTGRES_USER=mangrove_user
POSTGRES_PASSWORD=change_this_strong_pw
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE_URL=postgis://mangrove_user:change_this_strong_pw@db:5432/mangrove_db
```

## Alur Penggunaan

1. Register akun baru atau login.
2. Admin dapat mengubah role user di halaman `Management Data`.
3. Editor mengunggah raster GeoTIFF dari halaman management.
4. Sistem memvalidasi file, membaca metadata, dan memproses tiles di background.
5. User membuka halaman peta untuk memilih raster, melihat metadata, dan menghitung luas.
6. AOI dapat digambar di peta untuk menghitung luas hanya pada area tertentu.

## Export Data

- Raster summary: CSV
- Data vektor mangrove: GeoJSON

## Struktur Folder Penting

```text
mangroveviz/
├── docker-compose.yml
├── nginx.conf
├── web/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── mangroveviz/
│   │   ├── settings.py
│   │   └── urls.py
│   └── mangroves/
│       ├── models.py
│       ├── views.py
│       ├── forms.py
│       ├── serializers.py
│       ├── utils.py
│       └── templates/mangroves/
├── data/
└── reports/
```

## API dan Dokumen Lain

- [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- [FUNCTIONAL_POINT_ANALYSIS.md](./FUNCTIONAL_POINT_ANALYSIS.md)

## Catatan

- Raster yang diunggah idealnya berupa GeoTIFF biner untuk klasifikasi mangrove.
- File media, tiles, dan data runtime tidak disimpan ke Git.
- Jika menggunakan deployment publik, sesuaikan `DJANGO_ALLOWED_HOSTS`, secret key, dan kredensial database.
