import pytest

from chargepoints.models import ChargePoint
from tests.factories import ChargePointFactory

pytestmark = pytest.mark.django_db


def test_bulk_soft_delete_on_queryset_marks_deleted_at():
    cp1 = ChargePointFactory()
    cp2 = ChargePointFactory()
    # delete() en QuerySet debe marcar deleted_at (no borrar físicamente)
    ChargePoint.objects.filter(id__in=[cp1.id, cp2.id]).delete()
    # manager oculta eliminados
    assert ChargePoint.objects.count() == 0
    # pero siguen existiendo en la BD
    assert ChargePoint.all_objects.count() == 2
