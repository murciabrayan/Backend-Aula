from django.db import models
from django.conf import settings
from courses.models import Course

class Assignment(models.Model):
    """Tarea creada por un docente para un curso"""
    curso = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='tareas')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    fecha_entrega = models.DateField()
    archivo = models.FileField(upload_to='tareas_docente/', blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} ({self.curso.nombre})"


class Submission(models.Model):
    """Entrega de una tarea por parte del estudiante"""
    tarea = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='entregas')
    estudiante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'STUDENT'})
    archivo = models.FileField(upload_to='tareas_estudiantes/', blank=True, null=True)
    fecha_entrega = models.DateTimeField(auto_now_add=True)
    calificacion = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    retroalimentacion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.estudiante.username} - {self.tarea.titulo}"
