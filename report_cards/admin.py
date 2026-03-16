from django.contrib import admin
from .models import (
    ReportCardConfig,
    Indicator,
    SubjectIndicatorAssignment,
)


@admin.register(ReportCardConfig)
class ReportCardConfigAdmin(admin.ModelAdmin):
    list_display = (
        "nombre_institucion",
        "anio_lectivo",
        "periodo_actual",
        "rector_nombre",
        "director_grupo_nombre",
    )


@admin.register(Indicator)
class IndicatorAdmin(admin.ModelAdmin):
    list_display = ("id", "descripcion_corta")
    search_fields = ("descripcion",)

    def descripcion_corta(self, obj):
        return obj.descripcion[:120]
    descripcion_corta.short_description = "Descripción"


@admin.register(SubjectIndicatorAssignment)
class SubjectIndicatorAssignmentAdmin(admin.ModelAdmin):
    list_display = ("materia", "periodo", "indicador")
    list_filter = ("periodo", "materia__curso")
    search_fields = ("materia__nombre", "indicador__descripcion")