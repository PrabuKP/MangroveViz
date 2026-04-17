from django.contrib.gis.db import models
from django.conf import settings
from django.db import close_old_connections

import os
import re
import json
import shlex
import fcntl
import tempfile
import threading
import subprocess
from pathlib import Path


# ===================== #
#  MODEL: MANGROVE SITE #
# ===================== #
class MangroveSite(models.Model):
    name = models.CharField(max_length=200)
    species = models.CharField(max_length=200, blank=True)
    canopy_cover = models.FloatField(null=True, blank=True)  # 0..100
    source = models.CharField(max_length=200, blank=True)
    geometry = models.GeometryField(srid=4326)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["species"]),
        ]

    def __str__(self) -> str:
        return self.name


# ==================== #
#  MODEL: RASTER LAYER #
# ==================== #
class RasterLayer(models.Model):
    # --- metadata dasar raster ---
    name  = models.CharField(max_length=200)
    file  = models.FileField(upload_to="rasters/")  # GeoTIFF asli
    epsg  = models.IntegerField(null=True, blank=True)
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    minx  = models.FloatField(null=True, blank=True)
    miny  = models.FloatField(null=True, blank=True)
    maxx  = models.FloatField(null=True, blank=True)
    maxy  = models.FloatField(null=True, blank=True)
    # hasil reproyeksi ke 4326 (absolute path di server)
    reprojected_path = models.CharField(max_length=500, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    # --- status pembuatan tiles ---
    TILE_STATUS_CHOICES = [
        ("none", "None"),
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("ok", "OK"),
        ("error", "Error"),
    ]
    tiles_status  = models.CharField(max_length=16, choices=TILE_STATUS_CHOICES, default="none")
    tiles_message = models.TextField(blank=True, default="")
    tiles_dir     = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name or os.path.basename(self.file.name)

    # ---------- URL helper ----------
    @property
    def url(self) -> str:
        """
        URL publik untuk digunakan Leaflet/klien.
        Jika ada file reproj di dalam MEDIA_ROOT → /media/<relpath>
        jika tidak, pakai path upload aslinya.
        """
        base = settings.MEDIA_URL.rstrip("/")
        media_root = str(settings.MEDIA_ROOT)
        if self.reprojected_path and self.reprojected_path.startswith(media_root):
            rel = str(Path(self.reprojected_path).relative_to(settings.MEDIA_ROOT)).replace("\\", "/")
            return f"{base}/{rel}"
        return f"{base}/{self.file.name}"

    @property
    def tile_dir_abs(self) -> str:
        """Direktori tiles absolut di server (/app/media/tiles/raster_<id>/)."""
        return os.path.join(settings.MEDIA_ROOT, f"tiles/raster_{self.id}")

    @property
    def tile_url_template(self) -> str:
        """Template URL XYZ untuk Leaflet."""
        return f"{settings.MEDIA_URL.rstrip('/')}/tiles/raster_{self.id}" + "/{z}/{x}/{y}.png"

    @property
    def area_cache_path(self) -> str:
        return os.path.join(settings.MEDIA_ROOT, "cache", f"raster_area_{self.id}.json")

    @property
    def processing_lock_path(self) -> str:
        return os.path.join(settings.MEDIA_ROOT, "queue", "raster_processing.lock")

    @property
    def source_label(self) -> str:
        return Path(self.file.name).name if self.file else "Tidak diketahui"

    # ---------- util internal ----------
    def _gdalinfo_json(self, path: str, include_histogram: bool = False) -> dict:
        hist_flag = " -hist" if include_histogram else ""
        cmd = f"gdalinfo{hist_flag} -json {shlex.quote(path)}"
        out = subprocess.check_output(cmd, shell=True)
        return json.loads(out)

    def _parse_epsg(self, srs: dict) -> int | None:
        txt = srs.get("wkt") or srs.get("wktPretty") or ""
        m = re.search(r"EPSG[^\d]*(\d+)", txt)
        return int(m.group(1)) if m else None

    def _pick_bbox(self, corners: dict):
        """Ambil (minx,miny,maxx,maxy) dari cornerCoordinates gdalinfo-json."""
        ur, ll = corners.get("upperRight"), corners.get("lowerLeft")
        if ur and ll:
            return ll[0], ll[1], ur[0], ur[1]
        return None

    def _load_cached_areas(self, src_path: str) -> tuple[float | None, float | None] | None:
        cache_path = self.area_cache_path
        if not os.path.exists(cache_path):
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            src_mtime = os.path.getmtime(src_path)
            if (
                data.get("src_path") == src_path
                and abs(float(data.get("src_mtime", -1)) - float(src_mtime)) < 0.000001
            ):
                return data.get("mangrove_area_ha"), data.get("non_mangrove_area_ha")
        except Exception:
            return None
        return None

    def _save_cached_areas(self, src_path: str, mangrove_area_ha: float | None, non_mangrove_area_ha: float | None) -> None:
        cache_path = self.area_cache_path
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        payload = {
            "src_path": src_path,
            "src_mtime": os.path.getmtime(src_path),
            "mangrove_area_ha": mangrove_area_ha,
            "non_mangrove_area_ha": non_mangrove_area_ha,
        }
        with open(cache_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)

    def compute_class_areas(self) -> tuple[float | None, float | None]:
        """
        Hitung luas kelas biner dalam hektare:
          - nilai > 0 dianggap mangrove
          - nilai 0 dianggap non-mangrove

        Raster sementara direproject ke EPSG:6933 agar perhitungan luas berbasis meter.
        """
        src_path = self.reprojected_path or os.path.abspath(os.path.join(settings.MEDIA_ROOT, self.file.name))
        cached = self._load_cached_areas(src_path)
        if cached is not None:
            return cached

        tmpdir = tempfile.mkdtemp(prefix="area_")
        equal_area_path = os.path.join(tmpdir, "equal_area.tif")
        binary_path = os.path.join(tmpdir, "binary.tif")

        try:
            warp_cmd = (
                f"gdalwarp -t_srs EPSG:6933 -r near -of GTiff "
                f"{shlex.quote(src_path)} {shlex.quote(equal_area_path)}"
            )
            subprocess.run(warp_cmd, shell=True, check=True)

            binary_cmd = (
                f"gdal_calc.py -A {shlex.quote(equal_area_path)} "
                f"--calc \"1*(A>0)\" --outfile {shlex.quote(binary_path)} "
                f"--type=Byte --NoDataValue=0 --format=GTiff"
            )
            subprocess.run(binary_cmd, shell=True, check=True)

            info = self._gdalinfo_json(binary_path, include_histogram=True)
            geo_transform = info.get("geoTransform") or []
            bands = info.get("bands") or []
            histogram = (bands[0].get("histogram") if bands else None) or {}
            buckets = histogram.get("buckets") or []

            if len(geo_transform) < 6 or len(buckets) < 2:
                return None, None

            pixel_width_m = abs(float(geo_transform[1]))
            pixel_height_m = abs(float(geo_transform[5]))
            pixel_area_ha = (pixel_width_m * pixel_height_m) / 10000.0

            non_mangrove_pixels = float(buckets[0])
            mangrove_pixels = float(sum(buckets[1:]))
            mangrove_area_ha = mangrove_pixels * pixel_area_ha
            non_mangrove_area_ha = non_mangrove_pixels * pixel_area_ha
            self._save_cached_areas(src_path, mangrove_area_ha, non_mangrove_area_ha)
            return mangrove_area_ha, non_mangrove_area_ha
        finally:
            try:
                for path in (equal_area_path, binary_path):
                    if os.path.exists(path):
                        os.remove(path)
                os.rmdir(tmpdir)
            except Exception:
                pass

    def compute_class_areas_for_roi(self, roi_geojson: dict) -> tuple[float | None, float | None]:
        src_path = self.reprojected_path or os.path.abspath(os.path.join(settings.MEDIA_ROOT, self.file.name))
        tmpdir = tempfile.mkdtemp(prefix="roi_")
        cutline_path = os.path.join(tmpdir, "roi.geojson")
        clipped_path = os.path.join(tmpdir, "roi_clipped.tif")

        try:
            with open(cutline_path, "w", encoding="utf-8") as fh:
                json.dump(roi_geojson, fh)

            warp_cmd = (
                f"gdalwarp -of GTiff -cutline {shlex.quote(cutline_path)} "
                f"-crop_to_cutline -dstnodata 0 {shlex.quote(src_path)} {shlex.quote(clipped_path)}"
            )
            subprocess.run(warp_cmd, shell=True, check=True)
            return self._compute_class_areas_from_path(clipped_path)
        finally:
            try:
                for path in (cutline_path, clipped_path):
                    if os.path.exists(path):
                        os.remove(path)
                os.rmdir(tmpdir)
            except Exception:
                pass

    def _compute_class_areas_from_path(self, src_path: str) -> tuple[float | None, float | None]:
        tmpdir = tempfile.mkdtemp(prefix="area_")
        equal_area_path = os.path.join(tmpdir, "equal_area.tif")
        binary_path = os.path.join(tmpdir, "binary.tif")

        try:
            warp_cmd = (
                f"gdalwarp -t_srs EPSG:6933 -r near -of GTiff "
                f"{shlex.quote(src_path)} {shlex.quote(equal_area_path)}"
            )
            subprocess.run(warp_cmd, shell=True, check=True)

            binary_cmd = (
                f"gdal_calc.py -A {shlex.quote(equal_area_path)} "
                f"--calc \"1*(A>0)\" --outfile {shlex.quote(binary_path)} "
                f"--type=Byte --NoDataValue=0 --format=GTiff"
            )
            subprocess.run(binary_cmd, shell=True, check=True)

            info = self._gdalinfo_json(binary_path, include_histogram=True)
            geo_transform = info.get("geoTransform") or []
            bands = info.get("bands") or []
            histogram = (bands[0].get("histogram") if bands else None) or {}
            buckets = histogram.get("buckets") or []

            if len(geo_transform) < 6 or len(buckets) < 2:
                return None, None

            pixel_width_m = abs(float(geo_transform[1]))
            pixel_height_m = abs(float(geo_transform[5]))
            pixel_area_ha = (pixel_width_m * pixel_height_m) / 10000.0

            non_mangrove_pixels = float(buckets[0])
            mangrove_pixels = float(sum(buckets[1:]))
            mangrove_area_ha = mangrove_pixels * pixel_area_ha
            non_mangrove_area_ha = non_mangrove_pixels * pixel_area_ha
            return mangrove_area_ha, non_mangrove_area_ha
        finally:
            try:
                for path in (equal_area_path, binary_path):
                    if os.path.exists(path):
                        os.remove(path)
                os.rmdir(tmpdir)
            except Exception:
                pass

    # ---------- konversi RGBA untuk biner (0/1) ----------
    def _rgba_from_binary(self, src_path: str, out_path: str) -> None:
        """
        Ubah raster 0/1 menjadi RGBA:
          1 → hijau (0,200,83) alpha 255
          0 → transparan
        """
        tmpdir = tempfile.mkdtemp(prefix="rgba_")
        try:
            R = os.path.join(tmpdir, "R.tif")
            G = os.path.join(tmpdir, "G.tif")
            B = os.path.join(tmpdir, "B.tif")
            A = os.path.join(tmpdir, "A.tif")
            VRT = os.path.join(tmpdir, "rgba.vrt")

            cmds = [
                f"gdal_calc.py -A {shlex.quote(src_path)} --calc \"0*(A>=0)\" --outfile {shlex.quote(R)} --type=Byte --NoDataValue=0 --format=GTiff",
                f"gdal_calc.py -A {shlex.quote(src_path)} --calc \"200*(A>0)\" --outfile {shlex.quote(G)} --type=Byte --NoDataValue=0 --format=GTiff",
                f"gdal_calc.py -A {shlex.quote(src_path)} --calc \"83*(A>0)\"  --outfile {shlex.quote(B)} --type=Byte --NoDataValue=0 --format=GTiff",
                f"gdal_calc.py -A {shlex.quote(src_path)} --calc \"255*(A>0)\" --outfile {shlex.quote(A)} --type=Byte --NoDataValue=0 --format=GTiff",
                f"gdalbuildvrt -separate {shlex.quote(VRT)} {shlex.quote(R)} {shlex.quote(G)} {shlex.quote(B)} {shlex.quote(A)}",
                f"gdal_translate {shlex.quote(VRT)} {shlex.quote(out_path)} -of GTiff -co TILED=YES -co COMPRESS=LZW -colorinterp red,green,blue,alpha",
            ]
            for c in cmds:
                subprocess.run(c, shell=True, check=True)
        finally:
            # bersihkan tmp
            try:
                for p in (R, G, B, A, VRT):
                    if os.path.exists(p):
                        os.remove(p)
                os.rmdir(tmpdir)
            except Exception:
                pass

    # ---------- lifecycle utama ----------
    def save(self, *args, **kwargs):
        """
        - simpan file,
        - baca metadata (gdalinfo),
        - reproject ke EPSG:4326 jika perlu,
        - update bbox,
        - simpan ulang metadata,
        - trigger pembuatan tiles (thread background).
        """
        update_fields = kwargs.get("update_fields")
        internal_update_fields = {
            "epsg", "width", "height",
            "minx", "miny", "maxx", "maxy",
            "reprojected_path",
            "tiles_status", "tiles_message", "tiles_dir",
        }

        if update_fields is not None and set(update_fields).issubset(internal_update_fields):
            super().save(*args, **kwargs)
            return

        needs_processing = self._state.adding
        if not needs_processing and self.pk:
            previous = type(self).objects.filter(pk=self.pk).values_list("file", flat=True).first()
            needs_processing = previous != self.file.name

        super().save(*args, **kwargs)  # simpan dulu agar file tersedia

        if not needs_processing:
            return

        # path absolut file upload
        src_path = os.path.abspath(os.path.join(settings.MEDIA_ROOT, self.file.name))

        # 1) gdalinfo awal
        info = self._gdalinfo_json(src_path)
        self.width  = (info.get("size") or [None, None])[0]
        self.height = (info.get("size") or [None, None])[1]
        self.epsg   = self._parse_epsg(info.get("coordinateSystem", {}))

        bb = self._pick_bbox(info.get("cornerCoordinates") or {})
        if bb:
            self.minx, self.miny, self.maxx, self.maxy = bb

        # 2) Reproject ke 4326 jika perlu
        if (self.epsg is None) or (self.epsg != 4326):
            src_rel = Path(self.file.name)
            out_rel = src_rel.with_name(src_rel.stem + "_epsg4326.tif")
            reproj_path = os.path.abspath(os.path.join(settings.MEDIA_ROOT, str(out_rel)))
            os.makedirs(os.path.dirname(reproj_path), exist_ok=True)
            cmd = (
                f"gdalwarp -t_srs EPSG:4326 -r bilinear -of GTiff "
                f"{shlex.quote(src_path)} {shlex.quote(reproj_path)}"
            )
            subprocess.check_call(cmd, shell=True)
            self.reprojected_path = reproj_path
            self.epsg = 4326

            # metadata baru dari hasil reproj
            info = self._gdalinfo_json(reproj_path)
            bb = self._pick_bbox(info.get("cornerCoordinates") or {})
            if bb:
                self.minx, self.miny, self.maxx, self.maxy = bb

        # 3) simpan metadata final
        super().save(update_fields=[
            "epsg", "width", "height",
            "minx", "miny", "maxx", "maxy",
            "reprojected_path",
        ])

        # 4) trigger pembuatan tiles (asinkron)
        self.trigger_tiles_generation()

    # ---------- trigger tiles ----------
    def trigger_tiles_generation(self) -> None:
        # tandai pending + message
        self.tiles_status  = "pending"
        self.tiles_message = "Queued, waiting for processing slot..."
        super().save(update_fields=["tiles_status", "tiles_message"])

        t = threading.Thread(target=self._generate_tiles_worker, daemon=True)
        t.start()

    def _generate_tiles_worker(self) -> None:
        """
        Worker background:
          - buat RGBA dari binary
          - jalankan gdal2tiles --xyz
          - update status
        """
        # Tutup koneksi DB lama untuk thread ini (best practice di Django)
        close_old_connections()
        rgba_tif = None

        try:
            os.makedirs(os.path.dirname(self.processing_lock_path), exist_ok=True)
            with open(self.processing_lock_path, "w", encoding="utf-8") as lock_file:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
                self.tiles_status  = "processing"
                self.tiles_message = "Generating tiles..."
                self.save(update_fields=["tiles_status", "tiles_message"])

                src = self.reprojected_path or os.path.join(settings.MEDIA_ROOT, self.file.name)

                # RGBA intermediat
                rgba_tif = os.path.join(
                    settings.MEDIA_ROOT, "rasters",
                    f"{Path(src).stem}_rgba_{self.id}.tif"
                )
                # direktori tiles
                dst = self.tile_dir_abs
                os.makedirs(dst, exist_ok=True)

                # 1) konversi warna → RGBA
                self._rgba_from_binary(src, rgba_tif)

                # 2) generate tiles XYZ zoom 5..14
                cmd = f"gdal2tiles.py --xyz -z 5-14 -r bilinear {shlex.quote(rgba_tif)} {shlex.quote(dst)}"
                subprocess.run(cmd, shell=True, check=True)

                # update status OK
                self.tiles_status  = "ok"
                self.tiles_message = "Tiles generated successfully."
                self.tiles_dir = os.path.relpath(dst, settings.BASE_DIR).replace("\\", "/")
                self.save(update_fields=["tiles_status", "tiles_message", "tiles_dir"])

        except subprocess.CalledProcessError as e:
            self.tiles_status  = "error"
            self.tiles_message = f"GDAL error: {e}"
            self.save(update_fields=["tiles_status", "tiles_message"])
        except Exception as e:
            self.tiles_status  = "error"
            self.tiles_message = str(e)
            self.save(update_fields=["tiles_status", "tiles_message"])
        finally:
            # bersihkan RGBA sementara
            try:
                if rgba_tif and os.path.exists(rgba_tif):
                    os.remove(rgba_tif)
            except Exception:
                pass
