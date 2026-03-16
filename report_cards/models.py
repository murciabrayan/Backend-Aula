from django.db import models
from courses.models import Subject


class ReportCardConfig(models.Model):
    nombre_institucion = models.CharField(max_length=255)
    resolucion = models.CharField(max_length=255, blank=True)
    titulo_boletin = models.CharField(max_length=255, default="Boletín de calificaciones")
    anio_lectivo = models.CharField(max_length=20, blank=True)
    periodo_actual = models.CharField(max_length=50, blank=True)

    rector_nombre = models.CharField(max_length=255, blank=True)
    director_grupo_nombre = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Configuración de boletín"
        verbose_name_plural = "Configuración de boletín"

    def __str__(self):
        return self.nombre_institucion


class Indicator(models.Model):
    descripcion = models.TextField(unique=True)

    class Meta:
        verbose_name = "Indicador"
        verbose_name_plural = "Indicadores"
        ordering = ["descripcion"]

    def __str__(self):
        return self.descripcion[:80]


class SubjectIndicatorAssignment(models.Model):
    PERIOD_CHOICES = [
        (1, "Periodo 1"),
        (2, "Periodo 2"),
        (3, "Periodo 3"),
        (4, "Periodo 4"),
    ]

    materia = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="indicadores_asignados",
    )
    periodo = models.PositiveSmallIntegerField(choices=PERIOD_CHOICES)
    indicador = models.ForeignKey(
        Indicator,
        on_delete=models.CASCADE,
        related_name="asignaciones",
    )

    class Meta:
        verbose_name = "Asignación de indicador"
        verbose_name_plural = "Asignaciones de indicadores"
        unique_together = ("materia", "periodo", "indicador")
        ordering = ["materia__nombre", "periodo", "indicador__descripcion"]

    def __str__(self):
        return f"{self.materia.nombre} - P{self.periodo} - {self.indicador.descripcion[:40]}"