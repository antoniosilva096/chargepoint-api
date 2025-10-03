import pytest
from django.db import IntegrityError

from chargepoints.models import ChargePoint
from tests.factories import ChargePointFactory

pytestmark = pytest.mark.django_db


def test_instance_soft_delete_sets_deleted_at():
    cp = ChargePointFactory()
    assert cp.deleted_at is None
    cp.delete()
    cp.refresh_from_db()
    assert cp.deleted_at is not None


def test_manager_objects_excludes_soft_deleted():
    alive = ChargePointFactory()
    deleted = ChargePointFactory()
    deleted.delete()
    assert list(ChargePoint.objects.all()) == [alive]
    assert set(ChargePoint.all_objects.all()) == {alive, deleted}  # incluye eliminados


def test_hard_delete_removes_row():
    cp = ChargePointFactory()
    pk = cp.pk
    cp.hard_delete()
    assert not ChargePoint.all_objects.filter(pk=pk).exists()


@pytest.mark.django_db
def test_unique_name_enforced():
    ChargePointFactory(name="CP-UNIQ")
    with pytest.raises(IntegrityError):
        ChargePoint.objects.create(name="CP-UNIQ")  # viola unique=True
