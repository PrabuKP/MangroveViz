from django.urls import path
from django.views.generic import TemplateView

from .views import (
    DataManagementView,
    HomeView,
    export_mangroves_geojson,
    export_rasters_csv,
    raster_status_api,
    raster_upload_api,
    viewer,
)

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("map/", viewer, name="viewer"),
    path("management/", DataManagementView.as_view(), name="management"),
    path("management/upload/", raster_upload_api, name="management-upload"),
    path("management/status/", raster_status_api, name="management-status"),
    path("management/export/rasters.csv", export_rasters_csv, name="export-rasters"),
    path("management/export/mangroves.geojson", export_mangroves_geojson, name="export-mangroves"),
    path("about/", TemplateView.as_view(template_name="mangroves/about.html"), name="about"),
    path("contact/", TemplateView.as_view(template_name="mangroves/contact.html"), name="contact"),
]
