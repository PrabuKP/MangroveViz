from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MangroveSiteViewSet, RasterLayerViewSet, health_check, raster_area_detail, raster_roi_area_detail

router = DefaultRouter()
router.register(r"mangroves", MangroveSiteViewSet, basename="mangroves")
router.register(r"rasters", RasterLayerViewSet, basename="rasters")

urlpatterns = [
    path("", include(router.urls)),  # /api/mangroves/, /api/rasters/
    path("health/", health_check, name="health-check"),  # /api/health/
    path("rasters/<int:pk>/area/", raster_area_detail, name="raster-area-detail"),
    path("rasters/<int:pk>/roi-area/", raster_roi_area_detail, name="raster-roi-area-detail"),
]
