from django.contrib import admin, messages
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import ChargePoint, Connector


# ---------------------------
# Filtro para soft-delete
# ---------------------------
class SoftDeletedFilter(admin.SimpleListFilter):
    title = _("estado de borrado")
    parameter_name = "deleted"

    def lookups(self, request, model_admin):
        return (
            ("alive", _("Vivos")),
            ("deleted", _("Eliminados")),
            ("all", _("Todos")),
        )

    def queryset(self, request, queryset):
        val = self.value()
        if val == "alive":
            return queryset.filter(deleted_at__isnull=True)
        if val == "deleted":
            return queryset.filter(deleted_at__isnull=False)
        if val == "all":
            return queryset  # sin filtro
        # Por defecto, muestra vivos
        return queryset.filter(deleted_at__isnull=True)


# ---------------------------
# Admin base para modelos con soft-delete
# ---------------------------
class SoftDeleteAdminMixin:
    softdelete_actions = ("action_soft_delete", "action_restore", "action_hard_delete")

    @admin.action(description=_("Marcar como eliminado (soft delete)"))
    def action_soft_delete(self, request, queryset):
        updated = queryset.update(deleted_at=timezone.now())
        self.message_user(
            request, _(f"{updated} elemento(s) marcados como eliminados."), messages.SUCCESS
        )

    @admin.action(description=_("Restaurar elementos eliminados"))
    def action_restore(self, request, queryset):
        updated = queryset.update(deleted_at=None)
        self.message_user(request, _(f"{updated} elemento(s) restaurados."), messages.SUCCESS)

    @admin.action(description=_("Borrado físico (usar con cuidado)"))
    def action_hard_delete(self, request, queryset):
        count = 0
        for obj in queryset:
            obj.hard_delete()
            count += 1
        self.message_user(
            request, _(f"{count} elemento(s) borrados físicamente."), messages.WARNING
        )

    def get_queryset(self, request):
        """
        Usar el manager 'all_objects' si existe, para poder filtrar por eliminados.
        Si no, usar el queryset por defecto.
        """
        if hasattr(self.model, "all_objects"):
            return self.model.all_objects.all()
        return super().get_queryset(request)

    @staticmethod
    def _deleted_badge(obj):
        if getattr(obj, "deleted_at", None):
            return format_html('<span style="color:#b00020;">●</span> {}', _("Eliminado"))
        return format_html('<span style="color:#2e7d32;">●</span> {}', _("Vivo"))

    _deleted_badge.short_description = _("Estado")


# ---------------------------
# Inlines
# ---------------------------
class ConnectorInline(admin.TabularInline):
    model = Connector
    extra = 0
    fields = ("evse_number", "created_at", "deleted_at")
    readonly_fields = ("created_at", "deleted_at")
    show_change_link = True
    can_delete = False


# ---------------------------
# ChargePoint Admin
# ---------------------------
@admin.register(ChargePoint)
class ChargePointAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("id", "name", "status", "created_at", "deleted_at", "estado")
    list_filter = ("status", SoftDeletedFilter)
    search_fields = ("name",)
    readonly_fields = ("created_at", "deleted_at")
    date_hierarchy = "created_at"
    ordering = ("-created_at", "id")
    list_per_page = 25
    inlines = [ConnectorInline]
    actions = SoftDeleteAdminMixin.softdelete_actions

    def estado(self, obj):
        return self._deleted_badge(obj)

    estado.short_description = _("Estado")


# ---------------------------
# Connector Admin
# ---------------------------
@admin.register(Connector)
class ConnectorAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("id", "evse_number", "charge_point", "created_at", "deleted_at", "estado")
    list_filter = (SoftDeletedFilter,)
    search_fields = ("evse_number", "charge_point__name")
    readonly_fields = ("created_at", "deleted_at")
    date_hierarchy = "created_at"
    ordering = ("-created_at", "id")
    list_per_page = 25
    list_select_related = ("charge_point",)
    autocomplete_fields = ("charge_point",)
    actions = SoftDeleteAdminMixin.softdelete_actions

    def estado(self, obj):
        return self._deleted_badge(obj)

    estado.short_description = _("Estado")
