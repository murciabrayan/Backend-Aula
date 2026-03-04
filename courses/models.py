from django.db import models
from django.conf import settings


class Course(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    docente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': 'TEACHER'},
        related_name='cursos_asignados'
    )

    estudiantes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        limit_choices_to={'role': 'STUDENT'},
        related_name='cursos'
    )

    def __str__(self):
        return self.nombre



class Subject(models.Model):
    """Asignatura dentro de un curso"""
    nombre = models.CharField(max_length=100)
    curso = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='materias'
    )

    class Meta:
        unique_together = ('nombre', 'curso')

    def __str__(self):
        return f"{self.nombre} - {self.curso.nombre}"