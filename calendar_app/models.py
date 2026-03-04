from django.db import models
from accounts.models import User
from courses.models import Course
from courses.models import Subject  

class CalendarEvent(models.Model):

    EVENT_TYPES = [
        ('EVENT', 'Evento'),
        ('EXAM', 'Evaluación'),
        ('ACTIVITY', 'Actividad'),
    ]

    titulo = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)

    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField(blank=True, null=True)

    tipo = models.CharField(max_length=20, choices=EVENT_TYPES)

    curso = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='calendar_events'
    )

    materia = models.ForeignKey(
        Subject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='calendar_events'
    )

    creado_por = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_calendar_events'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} - {self.curso.nombre}"