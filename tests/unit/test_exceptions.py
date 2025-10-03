import pytest
from rest_framework.exceptions import NotFound, ValidationError

from config.exceptions import api_exception_handler

pytestmark = pytest.mark.django_db


def test_api_exception_handler_validation_error_shapes_envelope():
    exc = ValidationError({"name": ["Este campo es obligatorio."]})
    resp = api_exception_handler(exc, context={})
    assert resp.status_code == 400
    body = resp.data
    assert set(body.keys()) == {"code", "message", "data", "errors"}
    assert body["data"] is None
    assert "name" in body["errors"]


def test_api_exception_handler_not_found():
    exc = NotFound("No encontrado")
    resp = api_exception_handler(exc, context={})
    assert resp.status_code == 404
    assert resp.data["code"] == 404
    assert resp.data["errors"]["detail"] == "No encontrado"
