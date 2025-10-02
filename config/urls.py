from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def healthz(_):
    return JsonResponse({"status": "ok"}, status=200)


def readyz(_):
    # Si quieres, aquí podrías chequear DB/Cache
    return JsonResponse({"status": "ready"}, status=200)


urlpatterns = [
    path("healthz/", healthz, name="healthz"),
    path("readyz/", readyz, name="readyz"),
    path("admin/", admin.site.urls),
    # Documentación OpenAPI
    path("api/schema/", include("api.schema_urls")),
    path("api/docs/", include("api.docs_urls")),
    # API versionada
    path("api/v1/", include(("api.v1.urls", "api_v1"), namespace="api_v1")),
]
