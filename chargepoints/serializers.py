from __future__ import annotations

from rest_framework import serializers

from .models import ChargePoint, Connector


class ConnectorNestedSerializer(serializers.ModelSerializer):
    """
    Serializer para la representación de conectores anidados en un ChargePoint.

    - Solo lectura: no permite crear ni actualizar conectores desde este contexto.
    - Pensado para respuesta (lectura). La escritura de conectores debe gestionarse
      a través de su propio endpoint.

    """

    class Meta:
        model = Connector
        fields = ["id", "evse_number", "deleted_at"]

        extra_kwargs = {
            "id": {"read_only": True},
            "evse_number": {"read_only": True},
            "deleted_at": {"read_only": True},
        }


class ChargePointSerializer(serializers.ModelSerializer):
    """
    Serializer principal para el modelo `ChargePoint`.
    Incluye una representación anidada y de solo lectura de los conectores asociados.

    """

    connectors = ConnectorNestedSerializer(many=True, read_only=True)

    class Meta:
        model = ChargePoint
        fields = ["id", "name", "status", "created_at", "connectors"]
        extra_kwargs = {
            "id": {"read_only": True},
            "created_at": {"read_only": True},
            "connectors": {"read_only": True},
        }

    def validate_name(self, value: str) -> str:
        """
        Valida y normaliza el campo `name`.

        Elimina espacios en blanco iniciales y finales, y asegura que el nombre no esté vacío
        tras la normalización.

        Parameters
        ----------
        value : str
            El valor recibido para el campo `name`.

        Returns
        -------
        str
            El valor limpio y validado.

        Raises
        ------
        serializers.ValidationError
            Si el valor está vacío tras eliminar los espacios.
        """

        value = (value or "").strip()
        if not value:
            raise serializers.ValidationError({"name": "El nombre no puede estar vacío."})
        return value


# ---------------------------------------------------------------------
# Solo para la documentacion de OpenAPI con drf-spectacular)
# Serializers de envelope para reflejar tu respuesta estándar:
#   { code, message, data, errors }
# ---------------------------------------------------------------------


class PaginationSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    next = serializers.CharField(allow_null=True)
    previous = serializers.CharField(allow_null=True)
    results = ChargePointSerializer(many=True)


class EnvelopeDetailSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = ChargePointSerializer()
    errors = serializers.DictField(allow_null=True)


class EnvelopeListSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = PaginationSerializer()
    errors = serializers.DictField(allow_null=True)
