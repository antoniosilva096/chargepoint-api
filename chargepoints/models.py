from __future__ import annotations

from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        return self.exclude(deleted_at__isnull=True)

    def delete(self):
        return super().update(deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()

    def all_with_deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db).all()

    def dead(self):
        return SoftDeleteQuerySet(self.model, using=self._db).dead()


class SoftDeleteModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["deleted_at"], name="%(class)s_del_idx"),
        ]

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    def hard_delete(self, using=None, keep_parents=False):
        return super().delete(using=using, keep_parents=keep_parents)


class ChargePoint(SoftDeleteModel):
    class Status(models.TextChoices):
        READY = "ready", "Ready"
        CHARGING = "charging", "Charging"
        WAITING = "waiting", "Waiting"
        ERROR = "error", "Error"

    name = models.CharField(max_length=32, unique=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.READY)

    class Meta:
        indexes = [
            models.Index(fields=["status"], name="chargepoint_status_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.name} [{self.status}]"


class Connector(SoftDeleteModel):
    evse_number = models.CharField(max_length=32, unique=True)
    charge_point = models.ForeignKey(
        ChargePoint,
        on_delete=models.CASCADE,
        related_name="connectors",
    )

    def __str__(self) -> str:
        return f"{self.evse_number} -> {self.charge_point.name}"
