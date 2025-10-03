from __future__ import annotations

import factory
from factory import Faker, LazyAttribute, SubFactory
from factory.django import DjangoModelFactory

from chargepoints.models import ChargePoint, Connector


class ChargePointFactory(DjangoModelFactory):
    class Meta:
        model = ChargePoint

    name = factory.Sequence(lambda n: f"CP-{n:03d}")
    status = ChargePoint.Status.READY

    class Params:
        status_ready = factory.Trait(status=ChargePoint.Status.READY)
        status_charging = factory.Trait(status=ChargePoint.Status.CHARGING)
        status_waiting = factory.Trait(status=ChargePoint.Status.WAITING)
        status_error = factory.Trait(status=ChargePoint.Status.ERROR)

        soft_deleted = factory.Trait(
            deleted_at=LazyAttribute(lambda _: Faker("date_time_this_year").generate({}))
        )


class ConnectorFactory(DjangoModelFactory):
    class Meta:
        model = Connector

    charge_point = SubFactory(ChargePointFactory)
    evse_number = Faker("bothify", text="EVSE-####-????")

    class Params:
        soft_deleted = factory.Trait(
            deleted_at=LazyAttribute(lambda _: Faker("date_time_this_year").generate({}))
        )
