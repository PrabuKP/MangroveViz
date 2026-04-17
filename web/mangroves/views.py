import csv
import json
import os
import shutil

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group, User
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now
from django.views import View
from django.views.generic import TemplateView
from rest_framework import filters, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_gis.filters import InBBoxFilter

from .forms import MangroveSiteForm, RasterUploadForm, RegisterForm
from .models import MangroveSite, RasterLayer
from .serializers import MangroveSiteSerializer, RasterLayerSerializer
from .utils import (
    VIEWER_GROUP,
    append_audit_log,
    assign_user_role,
    ensure_role_groups,
    get_next_raster_version,
    infer_model_name,
    read_audit_logs,
    summarize_raster_audit,
    user_is_admin,
    user_is_editor,
    user_role_label,
)


class RasterAccessPermission(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        if request.method == "DELETE":
            return user_is_admin(request.user)
        return user_is_editor(request.user)


def cleanup_raster_files(instance: RasterLayer) -> None:
    if instance.file and os.path.exists(instance.file.path):
        os.remove(instance.file.path)
    if instance.reprojected_path and os.path.exists(instance.reprojected_path):
        os.remove(instance.reprojected_path)
    if os.path.exists(instance.tile_dir_abs):
        shutil.rmtree(instance.tile_dir_abs)
    if os.path.exists(instance.area_cache_path):
        os.remove(instance.area_cache_path)


def _raster_cached_area(raster: RasterLayer) -> tuple[float | None, float | None]:
    src_path = raster.reprojected_path or os.path.abspath(os.path.join(settings.MEDIA_ROOT, raster.file.name))
    return raster._load_cached_areas(src_path) or (None, None)


def _dashboard_stats(rasters, users) -> dict:
    ready_count = sum(1 for raster in rasters if raster.tiles_status == "ok")
    processing_count = sum(1 for raster in rasters if raster.tiles_status in {"pending", "processing"})
    error_count = sum(1 for raster in rasters if raster.tiles_status == "error")
    total_mangrove_cached = 0.0
    cached_layers = 0
    for raster in rasters:
        mangrove_area, _ = _raster_cached_area(raster)
        if mangrove_area is not None:
            total_mangrove_cached += mangrove_area
            cached_layers += 1
    return {
        "raster_total": len(rasters),
        "raster_ready": ready_count,
        "raster_processing": processing_count,
        "raster_error": error_count,
        "mangrove_total": MangroveSite.objects.count(),
        "user_total": len(users),
        "viewer_total": sum(1 for user in users if user_role_label(user) == "viewer"),
        "editor_total": sum(1 for user in users if user_role_label(user) == "editor"),
        "admin_total": sum(1 for user in users if user_role_label(user) == "admin"),
        "cached_layers": cached_layers,
        "cached_mangrove_area_ha": total_mangrove_cached,
    }


def _mangrove_geojson_features(queryset) -> dict:
    features = []
    for site in queryset:
        features.append({
            "type": "Feature",
            "geometry": json.loads(site.geometry.geojson) if site.geometry else None,
            "properties": {
                "id": site.id,
                "name": site.name,
                "species": site.species,
                "canopy_cover": site.canopy_cover,
                "source": site.source,
                "created_at": site.created_at.isoformat() if site.created_at else None,
            },
        })
    return {"type": "FeatureCollection", "features": features}


class MangroveSiteViewSet(viewsets.ModelViewSet):
    queryset = MangroveSite.objects.all().order_by("-created_at")
    serializer_class = MangroveSiteSerializer
    filter_backends = [InBBoxFilter, filters.SearchFilter]
    bbox_filter_field = "geometry"
    search_fields = ["name", "species", "source"]
    permission_classes = [RasterAccessPermission]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"message": f"Mangrove site '{instance.name}' deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class RasterLayerViewSet(viewsets.ModelViewSet):
    queryset = RasterLayer.objects.all().order_by("-created_at")
    serializer_class = RasterLayerSerializer
    permission_classes = [RasterAccessPermission]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            cleanup_raster_files(instance)
        except Exception as e:
            print(f"Warning: Could not cleanup files for raster {instance.name}: {e}")
        self.perform_destroy(instance)
        return Response({"message": f"Raster layer '{instance.name}' and associated files deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


class HomeView(TemplateView):
    template_name = "mangroves/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["now"] = now()
        return ctx


class RegisterView(View):
    template_name = "mangroves/register.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("management")
        return render(request, self.template_name, {"form": RegisterForm()})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect("management")

        form = RegisterForm(request.POST)
        if form.is_valid():
            ensure_role_groups()
            user = form.save()
            viewer_group = Group.objects.get(name=VIEWER_GROUP)
            user.groups.add(viewer_group)
            login(request, user)
            messages.success(request, "Akun berhasil dibuat. Selamat datang di Mangrove Viewer.")
            return redirect("viewer")
        return render(request, self.template_name, {"form": form})


class DataManagementView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "mangroves/management.html"

    def test_func(self):
        return user_is_editor(self.request.user) or user_is_admin(self.request.user)

    def handle_no_permission(self):
        messages.error(self.request, "Halaman management hanya dapat diakses editor atau admin.")
        return redirect("viewer")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ensure_role_groups()
        rasters = list(RasterLayer.objects.all())
        vectors = list(MangroveSite.objects.all().order_by("-created_at"))
        users = list(User.objects.all().order_by("username"))
        audit_summary = summarize_raster_audit(rasters)

        for raster in rasters:
            raster.audit_info = audit_summary.get(raster.id, {})
            raster.cached_areas = _raster_cached_area(raster)

        edit_site = kwargs.get("edit_site")
        if edit_site is None:
            edit_site_id = self.request.GET.get("edit_site")
            if edit_site_id:
                edit_site = get_object_or_404(MangroveSite, pk=edit_site_id)

        for user in users:
            user.role_label = user_role_label(user)

        ctx["upload_form"] = kwargs.get("upload_form", RasterUploadForm())
        ctx["vector_form"] = kwargs.get("vector_form", MangroveSiteForm(instance=edit_site))
        ctx["edit_site"] = edit_site
        ctx["rasters"] = rasters
        ctx["vectors"] = vectors
        ctx["users"] = users
        ctx["stats"] = _dashboard_stats(rasters, users)
        ctx["user_role"] = user_role_label(self.request.user)
        ctx["recent_audits"] = read_audit_logs(limit=10)
        ctx["can_delete"] = user_is_admin(self.request.user)
        ctx["can_manage_users"] = user_is_admin(self.request.user)
        return ctx

    def _redirect_management(self):
        return redirect("management")

    def _render_management(self, **kwargs):
        return self.render_to_response(self.get_context_data(**kwargs))

    def _reject_editor_action(self, request, message_text):
        messages.error(request, message_text)
        return self._redirect_management()

    def _reject_admin_action(self, request, message_text):
        messages.error(request, message_text)
        return self._redirect_management()

    def _handle_upload_raster(self, request):
        if not user_is_editor(request.user):
            return self._reject_editor_action(request, "Anda tidak memiliki izin upload raster.")

        upload_form = RasterUploadForm(request.POST, request.FILES)
        if not upload_form.is_valid():
            return self._render_management(upload_form=upload_form)

        existing_names = list(RasterLayer.objects.values_list("name", flat=True))
        version = get_next_raster_version(upload_form.cleaned_data["name"], existing_names)
        raster = upload_form.save()
        append_audit_log({
            "action": "upload",
            "user": request.user.username,
            "role": user_role_label(request.user),
            "raster_id": raster.id,
            "raster_name": raster.name,
            "file_name": raster.source_label,
            "version": version,
            "previous_versions": [name for name in existing_names if name == raster.name],
        })
        messages.success(request, f"Raster '{raster.name}' berhasil diunggah. Proses metadata dan tiles sedang berjalan.")
        return self._redirect_management()

    def _handle_delete_raster(self, request):
        if not user_is_admin(request.user):
            return self._reject_admin_action(request, "Hanya admin yang dapat menghapus raster.")

        raster = get_object_or_404(RasterLayer, pk=request.POST.get("raster_id"))
        append_audit_log({
            "action": "delete",
            "user": request.user.username,
            "role": user_role_label(request.user),
            "raster_id": raster.id,
            "raster_name": raster.name,
            "file_name": raster.source_label,
            "version": getattr(raster, "audit_info", {}).get("version"),
        })
        try:
            cleanup_raster_files(raster)
        except Exception as e:
            messages.warning(request, f"Sebagian file raster '{raster.name}' tidak bisa dibersihkan: {e}")

        raster.delete()
        messages.success(request, f"Raster '{raster.name}' berhasil dihapus.")
        return self._redirect_management()

    def _handle_save_site(self, request):
        if not user_is_editor(request.user):
            return self._reject_editor_action(request, "Hanya editor atau admin yang dapat menyimpan data vektor.")

        site = None
        site_id = request.POST.get("site_id")
        if site_id:
            site = get_object_or_404(MangroveSite, pk=site_id)

        vector_form = MangroveSiteForm(request.POST, instance=site)
        if not vector_form.is_valid():
            return self._render_management(vector_form=vector_form, edit_site=site)

        site = vector_form.save()
        messages.success(request, f"Data vektor '{site.name}' berhasil disimpan.")
        return self._redirect_management()

    def _handle_delete_site(self, request):
        if not user_is_admin(request.user):
            return self._reject_admin_action(request, "Hanya admin yang dapat menghapus data vektor.")

        site = get_object_or_404(MangroveSite, pk=request.POST.get("site_id"))
        site_name = site.name
        site.delete()
        messages.success(request, f"Data vektor '{site_name}' berhasil dihapus.")
        return self._redirect_management()

    def _handle_update_user_role(self, request):
        if not user_is_admin(request.user):
            return self._reject_admin_action(request, "Hanya admin yang dapat mengubah role user.")

        target_user = get_object_or_404(User, pk=request.POST.get("user_id"))
        role = request.POST.get("role")
        if role not in {"viewer", "editor", "admin"}:
            return self._reject_admin_action(request, "Role tidak valid.")

        if request.user.pk == target_user.pk and role != "admin":
            return self._reject_admin_action(
                request,
                "Admin aktif tidak dapat menurunkan role dirinya sendiri dari halaman ini.",
            )

        assign_user_role(target_user, role)
        messages.success(request, f"Role user '{target_user.username}' berhasil diubah menjadi {role}.")
        return self._redirect_management()

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        handlers = {
            "upload_raster": self._handle_upload_raster,
            "delete_raster": self._handle_delete_raster,
            "save_site": self._handle_save_site,
            "delete_site": self._handle_delete_site,
            "update_user_role": self._handle_update_user_role,
        }
        handler = handlers.get(action)
        if handler is None:
            messages.error(request, "Aksi tidak dikenali.")
            return self._redirect_management()
        return handler(request)


@login_required
def viewer(request):
    return render(request, "mangroves/viewer.html", {"user_role": user_role_label(request.user)})


@login_required
def raster_upload_api(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed."}, status=405)
    if not user_is_editor(request.user):
        return JsonResponse({"detail": "Hanya editor atau admin yang dapat upload raster."}, status=403)

    form = RasterUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        errors = {field: [item["message"] for item in items] for field, items in form.errors.get_json_data().items()}
        return JsonResponse({"errors": errors}, status=400)

    existing_names = list(RasterLayer.objects.values_list("name", flat=True))
    version = get_next_raster_version(form.cleaned_data["name"], existing_names)
    raster = form.save()
    append_audit_log({
        "action": "upload",
        "user": request.user.username,
        "role": user_role_label(request.user),
        "raster_id": raster.id,
        "raster_name": raster.name,
        "file_name": raster.source_label,
        "version": version,
        "previous_versions": [name for name in existing_names if name == raster.name],
    })
    return JsonResponse({"id": raster.id, "name": raster.name, "status": raster.tiles_status, "message": raster.tiles_message})


@login_required
def raster_status_api(request):
    rasters = list(RasterLayer.objects.all())
    audit_summary = summarize_raster_audit(rasters)
    items = []
    for raster in rasters:
        audit = audit_summary.get(raster.id, {})
        items.append({
            "id": raster.id,
            "name": raster.name,
            "file_name": raster.source_label,
            "epsg": raster.epsg,
            "width": raster.width,
            "height": raster.height,
            "tiles_status": raster.tiles_status,
            "tiles_message": raster.tiles_message,
            "created_at": raster.created_at.isoformat() if raster.created_at else None,
            "version": audit.get("version"),
            "user": audit.get("user"),
            "timestamp": audit.get("timestamp"),
        })
    return JsonResponse({"items": items, "user_role": user_role_label(request.user), "can_delete": user_is_admin(request.user)})


@login_required
def export_rasters_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="rasters_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["id", "name", "file_name", "created_at", "epsg", "width", "height", "tiles_status", "model_name"])
    for raster in RasterLayer.objects.all():
        writer.writerow([
            raster.id,
            raster.name,
            raster.source_label,
            raster.created_at.isoformat() if raster.created_at else "",
            raster.epsg,
            raster.width,
            raster.height,
            raster.tiles_status,
            infer_model_name(raster.name, raster.source_label),
        ])
    return response


@login_required
def export_mangroves_geojson(request):
    return JsonResponse(_mangrove_geojson_features(MangroveSite.objects.all()))


@api_view(["GET"])
def health_check(request):
    return Response({"status": "healthy", "timestamp": now(), "service": "Mangrove Visualization API"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def raster_area_detail(request, pk):
    raster = get_object_or_404(RasterLayer, pk=pk)
    mangrove_area_ha, non_mangrove_area_ha = raster.compute_class_areas()
    return Response({
        "id": raster.id,
        "name": raster.name,
        "mangrove_area_ha": mangrove_area_ha,
        "non_mangrove_area_ha": non_mangrove_area_ha,
        "model_name": infer_model_name(raster.name, raster.source_label),
        "source_label": raster.source_label,
        "tiles_status": raster.tiles_status,
        "created_at": raster.created_at,
        "epsg": raster.epsg,
        "width": raster.width,
        "height": raster.height,
        "bbox": {"minx": raster.minx, "miny": raster.miny, "maxx": raster.maxx, "maxy": raster.maxy},
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def raster_roi_area_detail(request, pk):
    raster = get_object_or_404(RasterLayer, pk=pk)
    roi_geojson = request.data.get("geojson")
    if not roi_geojson:
        return Response({"detail": "GeoJSON polygon diperlukan."}, status=400)
    roi_feature = roi_geojson if roi_geojson.get("type") == "Feature" else {"type": "Feature", "properties": {}, "geometry": roi_geojson}
    mangrove_area_ha, non_mangrove_area_ha = raster.compute_class_areas_for_roi({"type": "FeatureCollection", "features": [roi_feature]})
    return Response({"id": raster.id, "name": raster.name, "mangrove_area_ha": mangrove_area_ha, "non_mangrove_area_ha": non_mangrove_area_ha})
