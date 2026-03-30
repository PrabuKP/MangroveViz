from django.contrib import admin
from .models import MangroveSite, RasterLayer

@admin.register(MangroveSite)
class MangroveSiteAdmin(admin.ModelAdmin):
    list_display  = ("id", "name", "species", "canopy_cover", "source", "created_at")
    search_fields = ("name", "species", "source")
    list_filter   = ("species",)
    date_hierarchy = "created_at"


@admin.register(RasterLayer)
class RasterLayerAdmin(admin.ModelAdmin):
    list_display = (
        "id", "name", "tiles_status",
        "epsg", "width", "height", "created_at",
    )
    search_fields = ("name",)
    readonly_fields = (
        "epsg", "width", "height",
        "minx", "miny", "maxx", "maxy",
        "reprojected_path", "tiles_status", "tiles_message", "tiles_dir",
    )
