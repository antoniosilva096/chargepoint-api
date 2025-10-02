from __future__ import annotations

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins, status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import ChargePoint
from .serializers import ChargePointSerializer


@extend_schema_view(
    list=extend_schema(
        operation_id="chargepoints.list",
        description=("Lista de ChargePoints activos"),
        tags=["chargepoints"],
        parameters=[
            OpenApiParameter(
                name="status",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="Filtra por estado (ready|charging|waiting|error)",
            ),
            OpenApiParameter(
                name="search",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="Búsqueda por nombre (icontains)",
            ),
            OpenApiParameter(
                name="ordering",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.STR,
                description="Campos de ordenación: name, created_at (usa '-' para descendente)",
            ),
            OpenApiParameter(
                name="page",
                location=OpenApiParameter.QUERY,
                type=OpenApiTypes.INT,
                description="Número de página (PageNumberPagination)",
            ),
        ],
        responses=ChargePointSerializer,
        examples=[
            OpenApiExample(
                "Ejemplo item:",
                value={
                    "id": 1,
                    "name": "CP-001",
                    "status": "ready",
                    "created_at": "2025-01-01T00:00:00Z",
                    "connectors": [],
                },
            )
        ],
    ),
    retrieve=extend_schema(
        operation_id="chargepoints.retrieve",
        description="Detalle de un ChargePoint.",
        tags=["chargepoints"],
        responses=ChargePointSerializer,
    ),
    create=extend_schema(
        operation_id="chargepoints.create",
        description="Crea un ChargePoint.",
        tags=["chargepoints"],
        request=ChargePointSerializer,
        responses=ChargePointSerializer,
    ),
    update=extend_schema(
        operation_id="chargepoints.update",
        description="Actualiza un ChargePoint (PUT/PATCH).",
        tags=["chargepoints"],
        request=ChargePointSerializer,
        responses=ChargePointSerializer,
    ),
    partial_update=extend_schema(
        operation_id="chargepoints.partial_update",
        description="Actualización parcial (PATCH).",
        tags=["chargepoints"],
        request=ChargePointSerializer,
        responses=ChargePointSerializer,
    ),
    destroy=extend_schema(
        operation_id="chargepoints.destroy",
        description="Soft delete (204 sin cuerpo).",
        tags=["chargepoints"],
        responses={204: None},
    ),
)
class ChargePointViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,  # PUT/PATCH
    mixins.DestroyModelMixin,  # DELETE (soft)
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    Endpoints:
      - POST   /api/v1/chargepoint
      - GET    /api/v1/chargepoint
      - GET    /api/v1/chargepoint/{id}
      - PUT    /api/v1/chargepoint/{id}
      - PATCH  /api/v1/chargepoint/{id}
      - DELETE /api/v1/chargepoint/{id}   (soft delete)
    """

    serializer_class = ChargePointSerializer
    permission_classes = [AllowAny]  # En prod IsAuthenticated / permisos

    # Filtros / búsqueda / ordenación
    filterset_fields = ["status"]
    search_fields = ["name"]
    ordering_fields = ["created_at", "name"]

    def get_queryset(self):
        qs = ChargePoint.objects.all()
        if self.action in {"list", "retrieve"}:
            qs = qs.prefetch_related("connectors")
        return qs

    # --------------------------
    # Envelope helpers
    # --------------------------
    def _ok(self, data, message: str = "OK", code: int = status.HTTP_200_OK) -> Response:
        return Response(
            {"code": code, "message": message, "data": data, "errors": None}, status=code
        )

    def _created(self, data, message: str = "Creado", headers: dict | None = None) -> Response:
        return Response(
            {"code": status.HTTP_201_CREATED, "message": message, "data": data, "errors": None},
            status=status.HTTP_201_CREATED,
            headers=headers or {},
        )

    def _no_content(self) -> Response:
        return Response(status=status.HTTP_204_NO_CONTENT)

    # --------------------------
    # CRUD
    # --------------------------
    def list(self, request, *args, **kwargs) -> Response:
        resp = super().list(request, *args, **kwargs)
        return self._ok(resp.data)

    def retrieve(self, request, *args, **kwargs) -> Response:
        instance = self.get_object()  # 404 si no existe o está soft-deleted
        data = self.get_serializer(instance).data
        return self._ok(data)

    def create(self, request, *args, **kwargs) -> Response:
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        self.perform_create(ser)
        headers = self.get_success_headers(ser.data)  # incluye Location
        return self._created(ser.data, headers=headers)

    def update(self, request, *args, **kwargs) -> Response:
        """PUT completo (PATCH delega aquí con partial=True)."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        ser = self.get_serializer(instance, data=request.data, partial=partial)
        ser.is_valid(raise_exception=True)
        self.perform_update(ser)
        return self._ok(ser.data, message="Actualizado")

    def partial_update(self, request, *args, **kwargs) -> Response:
        """PATCH parcial."""
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs) -> Response:
        """Soft delete: marca deleted_at y devuelve 204 sin body."""
        instance = self.get_object()
        instance.delete()
        return self._no_content()
