from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import MangroveSite, RasterLayer
from .utils import infer_model_name

class MangroveSiteSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = MangroveSite
        geo_field = "geometry"
        fields = ("id", "name", "species", "canopy_cover", "source", "created_at")

class RasterLayerSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    bbox = serializers.SerializerMethodField()
    model_name = serializers.SerializerMethodField()
    source_label = serializers.SerializerMethodField()

    class Meta:
        model = RasterLayer
        fields = (
            "id", "name", "url", "epsg", "width", "height",
            "minx", "miny", "maxx", "maxy", "bbox",
            "tiles_status", "tiles_message", "created_at",
            "file_name", "source_label", "model_name",
        )

    def get_url(self, obj):
        return obj.url

    def get_file_name(self, obj):
        return obj.source_label

    def get_source_label(self, obj):
        return obj.source_label

    def get_model_name(self, obj):
        return infer_model_name(obj.name, obj.source_label)

    def get_bbox(self, obj):
        return {
            "minx": obj.minx,
            "miny": obj.miny,
            "maxx": obj.maxx,
            "maxy": obj.maxy,
        }
