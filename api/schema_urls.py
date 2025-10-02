from django.urls import path
from drf_spectacular.views import SpectacularAPIView

urlpatterns = [
    path("", SpectacularAPIView.as_view(), name="schema"),
]
