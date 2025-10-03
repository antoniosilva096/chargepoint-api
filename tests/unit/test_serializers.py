import pytest

from chargepoints.serializers import ChargePointSerializer
from tests.factories import ChargePointFactory, ConnectorFactory

pytestmark = pytest.mark.django_db


def test_chargepoint_serializer_validates_name_strip():
    ser = ChargePointSerializer(data={"name": "   ", "status": "ready"})
    assert not ser.is_valid()
    assert "name" in ser.errors

    ser_ok = ChargePointSerializer(data={"name": " CP-001 ", "status": "ready"})
    assert ser_ok.is_valid(), ser_ok.errors
    assert ser_ok.validated_data["name"] == "CP-001"


def test_connectors_nested_is_read_only():
    ser = ChargePointSerializer(
        data={
            "name": "CP-RO",
            "status": "ready",
            "connectors": [{"evse_number": "SHOULD-IGNORE"}],
        }
    )
    assert ser.is_valid(), ser.errors
    # read-only: no entra en validated_data
    assert "connectors" not in ser.validated_data
    cp = ser.save()
    data = ChargePointSerializer(cp).data
    assert data["connectors"] == []


def test_nested_connectors_representation():
    cp = ChargePointFactory()
    ConnectorFactory(charge_point=cp, evse_number="EVSE-1")
    ConnectorFactory(charge_point=cp, evse_number="EVSE-2")
    data = ChargePointSerializer(cp).data
    evses = [c["evse_number"] for c in data["connectors"]]
    assert set(evses) == {"EVSE-1", "EVSE-2"}
