from django.urls import include, path
from rest_framework.routers import SimpleRouter

from chargepoints.views import ChargePointViewSet

router = SimpleRouter(trailing_slash="/?")  # Permitir URLs con o sin barra final
router.register(r"chargepoint", ChargePointViewSet, basename="chargepoint")

urlpatterns = [path("", include(router.urls))]
