from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.contrib.gis.geos import Point

import json
import os
import shlex
import subprocess
import tempfile

from .models import MangroveSite, RasterLayer


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class RasterUploadForm(forms.ModelForm):
    def clean_file(self):
        upload = self.cleaned_data["file"]
        suffix = os.path.splitext(upload.name)[1].lower()
        if suffix not in {".tif", ".tiff"}:
            raise ValidationError("File harus berformat GeoTIFF (.tif atau .tiff).")

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                for chunk in upload.chunks():
                    tmp.write(chunk)
                temp_path = tmp.name

            info_cmd = f"gdalinfo -hist -json {shlex.quote(temp_path)}"
            info = json.loads(subprocess.check_output(info_cmd, shell=True))

            if info.get("driverShortName") != "GTiff":
                raise ValidationError("File bukan GeoTIFF yang valid.")

            bands = info.get("bands") or []
            if len(bands) != 1:
                raise ValidationError("Raster harus memiliki tepat 1 band.")

            band = bands[0]
            histogram = band.get("histogram") or {}
            buckets = histogram.get("buckets") or []
            non_zero_bins = [index for index, count in enumerate(buckets) if count]
            if len(non_zero_bins) > 2:
                raise ValidationError("Raster harus biner. Ditemukan lebih dari dua nilai kelas.")

            if not non_zero_bins:
                raise ValidationError("Raster tidak memiliki nilai piksel yang dapat dianalisis.")

            if any(value not in (0, 1) for value in non_zero_bins):
                raise ValidationError("Raster harus menggunakan nilai biner 0 dan 1.")

            upload.seek(0)
            return upload
        except subprocess.CalledProcessError:
            raise ValidationError("File tidak dapat dibaca oleh GDAL. Pastikan file adalah GeoTIFF yang valid.")
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    class Meta:
        model = RasterLayer
        fields = ("name", "file")


class MangroveSiteForm(forms.ModelForm):
    latitude = forms.FloatField()
    longitude = forms.FloatField()

    class Meta:
        model = MangroveSite
        fields = ("name", "species", "canopy_cover", "source", "latitude", "longitude")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.geometry:
            self.fields["latitude"].initial = self.instance.geometry.y
            self.fields["longitude"].initial = self.instance.geometry.x

    def clean_canopy_cover(self):
        value = self.cleaned_data.get("canopy_cover")
        if value is not None and not (0 <= value <= 100):
            raise ValidationError("Canopy cover harus berada pada rentang 0 sampai 100.")
        return value

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.geometry = Point(
            self.cleaned_data["longitude"],
            self.cleaned_data["latitude"],
            srid=4326,
        )
        if commit:
            instance.save()
        return instance
