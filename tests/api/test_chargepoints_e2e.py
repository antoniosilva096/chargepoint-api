import pytest
from django.utils import timezone

from tests.factories import ChargePointFactory, ConnectorFactory

pytestmark = pytest.mark.django_db

BASE = "/api/v1/chargepoint/"


# ---------- CREATE ----------


def test_create_chargepoint_201(api):
    payload = {"name": "CP-001", "status": "ready"}
    res = api.post(BASE, payload, format="json")
    assert res.status_code == 201
    body = res.json()
    assert body["code"] == 201
    assert body["message"] == "Creado"
    assert body["errors"] is None
    assert body["data"]["name"] == "CP-001"
    assert body["data"]["status"] == "ready"
    assert body["data"]["connectors"] == []


def test_create_chargepoint_400_validation(api):
    payload = {"name": "   ", "status": "ready"}
    res = api.post(BASE, payload, format="json")
    assert res.status_code == 400
    body = res.json()
    assert body["code"] == 400
    assert "name" in body["errors"]


def test_create_chargepoint_400_unique(api):
    api.post(BASE, {"name": "CP-UNIQ", "status": "ready"}, format="json")
    res = api.post(BASE, {"name": "CP-UNIQ", "status": "ready"}, format="json")
    assert res.status_code == 400
    assert "name" in res.json()["errors"]


# ---------- LIST (paginación / filtros / búsqueda / ordenación) ----------


def test_list_pagination_structure_envelope(api):
    # crea 12 para forzar paginación (PAGE_SIZE=10)
    for i in range(12):
        ChargePointFactory(name=f"CP-{i:03d}")
    res = api.get(BASE)
    assert res.status_code == 200
    body = res.json()
    assert body["code"] == 200
    assert "data" in body and "results" in body["data"]
    assert len(body["data"]["results"]) <= 10
    assert body["data"]["count"] >= 12

    # page=2
    res2 = api.get(f"{BASE}?page=2")
    assert res2.status_code == 200
    assert len(res2.json()["data"]["results"]) >= 1


def test_list_filter_search_ordering(api):
    ChargePointFactory(name="AA-READY", status="ready")
    ChargePointFactory(name="ZZ-CHARG", status="charging")

    # filtro status
    res_f = api.get(f"{BASE}?status=ready")
    assert res_f.status_code == 200
    names_f = [x["name"] for x in res_f.json()["data"]["results"]]
    assert "AA-READY" in names_f and "ZZ-CHARG" not in names_f

    # búsqueda
    res_s = api.get(f"{BASE}?search=AA-REA")
    assert res_s.status_code == 200
    names_s = [x["name"] for x in res_s.json()["data"]["results"]]
    assert "AA-READY" in names_s

    # ordenación asc por name
    ChargePointFactory(name="MM-MID")
    res_o = api.get(f"{BASE}?ordering=name")
    assert res_o.status_code == 200
    names_o = [x["name"] for x in res_o.json()["data"]["results"]]
    assert names_o == sorted(names_o)


# ---------- RETRIEVE con conectores anidados (read-only) ----------


def test_retrieve_with_nested_connectors_read_only(api):
    cp = ChargePointFactory(name="CP-DET")
    ConnectorFactory(charge_point=cp, evse_number="EVSE-10")
    ConnectorFactory(charge_point=cp, evse_number="EVSE-11")

    res = api.get(f"{BASE}{cp.id}/")
    assert res.status_code == 200
    connectors = res.json()["data"]["connectors"]
    evses = {c["evse_number"] for c in connectors}
    assert evses == {"EVSE-10", "EVSE-11"}

    # Intento de escribir conectores desde CP (debe ignorar, es read-only)
    res_patch = api.patch(
        f"{BASE}{cp.id}/", {"connectors": [{"evse_number": "IGNORED"}]}, format="json"
    )
    assert res_patch.status_code == 200
    # sigue igual en lectura
    res2 = api.get(f"{BASE}{cp.id}/")
    assert {c["evse_number"] for c in res2.json()["data"]["connectors"]} == {"EVSE-10", "EVSE-11"}


# ---------- UPDATE (PATCH/PUT) ----------


def test_update_patch_status_200(api):
    cp = ChargePointFactory(name="CP-UP", status="ready")
    res = api.patch(f"{BASE}{cp.id}/", {"status": "charging"}, format="json")
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "charging"


def test_update_on_soft_deleted_returns_404(api):
    cp = ChargePointFactory(name="CP-DEL")
    # soft delete vía ORM para simular estado
    cp.deleted_at = timezone.now()
    cp.save(update_fields=["deleted_at"])

    res = api.patch(f"{BASE}{cp.id}/", {"status": "waiting"}, format="json")
    # Con el manager por defecto, debe ser 404
    assert res.status_code == 404
    body = res.json()
    assert body["code"] == 404
    assert body["data"] is None
    assert "detail" in body["errors"]


# ---------- DELETE (soft) ----------


def test_delete_soft_and_visibility(api):
    cp = ChargePointFactory(name="CP-SOFT")
    res = api.delete(f"{BASE}{cp.id}/")
    assert res.status_code == 204
    # 204 no tiene body
    assert not res.content

    # Detalle debe devolver 404
    res2 = api.get(f"{BASE}{cp.id}/")
    assert res2.status_code == 404

    # Listado no lo incluye
    res3 = api.get(BASE)
    ids = [x["id"] for x in res3.json()["data"]["results"]]
    assert cp.id not in ids


# ---------- ERROR ENVELOPE ----------


def test_error_envelope_404_detail(api):
    res = api.get(f"{BASE}999999/")
    assert res.status_code == 404
    body = res.json()
    assert set(body.keys()) == {"code", "message", "data", "errors"}
    assert body["data"] is None
    assert body["code"] == 404
    assert "detail" in body["errors"]
