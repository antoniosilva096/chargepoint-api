from django.urls import include, path
from rest_framework.routers import SimpleRouter

from chargepoints.views import ChargePointViewSet

router = SimpleRouter(trailing_slash=False)
router.register(r"chargepoint", ChargePointViewSet, basename="chargepoint")

urlpatterns = [
    path("", include(router.urls)),
]
