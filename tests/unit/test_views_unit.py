import pytest
from rest_framework import status
from rest_framework.test import APIRequestFactory

from chargepoints.views import ChargePointViewSet
from tests.factories import ChargePointFactory

pytestmark = pytest.mark.django_db


def test_list_view_unit():
    ChargePointFactory(name="CP-LIST")
    factory = APIRequestFactory()
    request = factory.get("/api/v1/chargepoint/")
    view = ChargePointViewSet.as_view({"get": "list"})
    response = view(request)
    assert response.status_code == status.HTTP_200_OK
    names = [item["name"] for item in response.data["data"]["results"]]
    assert "CP-LIST" in names


def test_retrieve_view_unit():
    cp = ChargePointFactory(name="CP-DET")
    factory = APIRequestFactory()
    request = factory.get(f"/api/v1/chargepoint/{cp.id}/")
    view = ChargePointViewSet.as_view({"get": "retrieve"})
    response = view(request, pk=cp.id)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["data"]["name"] == "CP-DET"


def test_update_conflict_or_404_if_deleted_unit():
    cp = ChargePointFactory()
    cp.delete()  # soft delete
    factory = APIRequestFactory()
    request = factory.patch(f"/api/v1/chargepoint/{cp.id}/", {"status": "waiting"}, format="json")
    view = ChargePointViewSet.as_view({"patch": "partial_update"})
    response = view(request, pk=cp.id)
    assert response.status_code in (404, 409)
