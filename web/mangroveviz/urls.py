from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from mangroves.views import RegisterView


def healthz(request): 
    return HttpResponse("ok")

urlpatterns = [
    path("", include("mangroves.urls")),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="mangroves/login.html"), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/register/", RegisterView.as_view(), name="register"),
    path("admin/", admin.site.urls),
    path("api/", include("mangroves.api_urls")),
    path("healthz", healthz),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
