from __future__ import annotations

import random

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from faker import Faker

from chargepoints.models import ChargePoint, Connector


class Command(BaseCommand):
    help = (
        "Crea datos demo para ChargePoints/Connectors o limpia la base. "
        "Uso: --populate N [--connectors M] [--seed S] [--soft-delete-ratio R] | --clean [--force]"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--populate",
            type=int,
            help="Número de ChargePoints a crear (ej. 20).",
        )
        parser.add_argument(
            "--connectors",
            type=int,
            default=None,
            help="Conectores por ChargePoint. Si no se indica, se usa un número aleatorio 0..3.",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=None,
            help="Semilla (int) para datos reproducibles.",
        )
        parser.add_argument(
            "--soft-delete-ratio",
            type=float,
            default=0.0,
            help=(
                "Proporción (0..1) de ChargePoints recién creados "
                "que serán marcados como soft-deleted. Ej: 0.2"
            ),
        )
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Elimina TODOS los ChargePoints/Connectors (hard delete).",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Requerido para --clean: confirma el borrado completo.",
        )

    def handle(self, *args, **options):
        populate: int | None = options.get("populate")
        connectors_count: int | None = options.get("connectors")
        clean: bool = options.get("clean")
        seed: int | None = options.get("seed")
        ratio: float = float(options.get("soft_delete_ratio") or 0.0)
        force: bool = options.get("force")

        if not populate and not clean:
            raise CommandError("Debes indicar --populate N o --clean.")

        if seed is not None:
            random.seed(seed)
            faker = Faker()
            Faker.seed(seed)
        else:
            faker = Faker()

        if clean:
            self._clean_all(force=force)
            return

        if populate < 0:
            raise CommandError("--populate debe ser un entero >= 0.")
        if connectors_count is not None and connectors_count < 0:
            raise CommandError("--connectors debe ser >= 0.")
        if not (0.0 <= ratio <= 1.0):
            raise CommandError("--soft-delete-ratio debe estar entre 0.0 y 1.0.")

        # -------------------------
        # Crear datos
        # -------------------------
        created_cp_ids: list[int] = []
        created_cp = 0
        created_conn = 0

        self.stdout.write(self.style.WARNING("Iniciando población de datos demo..."))
        with transaction.atomic():
            for i in range(populate):
                name = f"CP-{i:03d}"  # determinista y legible
                status = random.choice(
                    [
                        ChargePoint.Status.READY,
                        ChargePoint.Status.CHARGING,
                        ChargePoint.Status.WAITING,
                        ChargePoint.Status.ERROR,
                    ]
                )
                cp = ChargePoint.objects.create(name=name, status=status)
                created_cp_ids.append(cp.id)
                created_cp += 1

                k = random.randint(0, 3) if connectors_count is None else connectors_count
                for j in range(k):
                    evse = f"EVSE-{i:03d}-{j:02d}-{faker.bothify(text='??##').upper()}"
                    Connector.objects.create(charge_point=cp, evse_number=evse)
                    created_conn += 1

        # -------------------------
        # Soft delete parcial (ratio)
        # -------------------------
        if created_cp_ids and ratio > 0.0:
            n = max(0, int(round(len(created_cp_ids) * ratio)))
            sample_ids = set(random.sample(created_cp_ids, k=n))
            now = timezone.now()

            with transaction.atomic():  # Idempotencia
                # Soft-delete chargepoints
                ChargePoint.all_objects.filter(id__in=sample_ids, deleted_at__isnull=True).update(
                    deleted_at=now
                )
                # Soft-delete connectors asociados
                Connector.all_objects.filter(
                    charge_point_id__in=sample_ids, deleted_at__isnull=True
                ).update(deleted_at=now)

            self.stdout.write(
                self.style.WARNING(
                    f"Marcados como soft-deleted {n} ChargePoints (ratio={ratio:.2f})."
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"OK: creados {created_cp} ChargePoints y {created_conn} Connectors."
            )
        )
        self.stdout.write(
            self.style.NOTICE(
                "Prueba en Swagger:\n"
                "  - GET /api/v1/chargepoint\n"
                "  - GET /api/v1/chargepoint/{id}\n"
                "  - Filtros: ?status=ready&search=CP&ordering=-created_at&page=1"
            )
        )

    @transaction.atomic
    def _clean_all(self, force: bool):
        if not force:
            self.stdout.write(
                self.style.ERROR("⚠️ Vas a borrar TODOS los ChargePoints/Connectors (hard delete).")
            )
            self.stdout.write(self.style.ERROR("Reejecuta con --clean --force para confirmar."))
            return

        self.stdout.write(
            self.style.WARNING("Eliminando TODOS los datos de ChargePoints y Connectors...")
        )

        Connector.all_objects.all().hard_delete()
        ChargePoint.all_objects.all().hard_delete()
        self.stdout.write(self.style.SUCCESS("OK: base limpia."))
