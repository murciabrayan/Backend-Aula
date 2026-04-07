from datetime import datetime

from django.utils.timezone import make_aware
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from assignments.models import Assignment
from courses.models import Course
from .models import CalendarEvent
from .serializers import CalendarEventSerializer
from .permissions import IsTeacherOrAdmin


class CalendarView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        events = []

        # =========================
        # CURSOS SEGÚN ROL
        # =========================
        if user.role == "STUDENT":
            courses = Course.objects.filter(estudiantes=user)
        elif user.role == "TEACHER":
            courses = Course.objects.filter(
                Q(director_curso=user) |
                Q(materias__docente=user)
            ).distinct()
        else:
            courses = Course.objects.all()

        # =========================
        # EVENTOS MANUALES
        # =========================
        calendar_events = CalendarEvent.objects.filter(
            curso__in=courses
        ).select_related("curso", "materia")

        for e in calendar_events:
            events.append({
                "id": f"event-{e.id}",
                "title": e.titulo,
                "start": e.fecha_inicio.isoformat(),
                "end": e.fecha_fin.isoformat() if e.fecha_fin else None,
                "className": "custom-event",
                "extendedProps": {
                    "tipo": e.tipo,
                    "curso": e.curso.nombre,
                    "materia": e.materia.nombre if e.materia else None,
                    "descripcion": e.descripcion,
                    "readonly": False,
                },
            })

        # =========================
        # TAREAS → EVENTOS
        # =========================
        assignments = Assignment.objects.filter(
            materia__curso__in=courses
        ).select_related("materia", "materia__curso")

        for a in assignments:
            start_date = make_aware(
                datetime.combine(a.fecha_entrega, datetime.min.time())
            )

            events.append({
                "id": f"task-{a.id}",
                "title": a.titulo,
                "start": start_date.isoformat(),
                "end": None,
                "allDay": True,
                "className": "task-event",
                "extendedProps": {
                    "tipo": "TASK",
                    "curso": a.materia.curso.nombre,
                    "materia": a.materia.nombre,
                    "descripcion": a.descripcion,
                    "readonly": True,
                },
            })

        return Response(events)


class CalendarEventViewSet(viewsets.ModelViewSet):
    queryset = CalendarEvent.objects.all()
    serializer_class = CalendarEventSerializer
    permission_classes = [IsAuthenticated, IsTeacherOrAdmin]

    def get_queryset(self):
        user = self.request.user

        # Docente: ve eventos de cursos donde es director o dicta al menos una materia
        if user.role == "TEACHER":
            return CalendarEvent.objects.filter(
                Q(curso__director_curso=user) |
                Q(curso__materias__docente=user)
            ).distinct()

        # Admin: ve todo
        return CalendarEvent.objects.all()

    def perform_create(self, serializer):
        user = self.request.user
        curso = serializer.validated_data.get("curso")

        # Docente solo puede crear eventos para cursos donde sea director o dicte una materia
        if user.role == "TEACHER":
            if not curso or not (
                curso.director_curso_id == user.id
                or curso.materias.filter(docente_id=user.id).exists()
            ):
                raise PermissionDenied("No puedes crear eventos para ese curso.")

        serializer.save(creado_por=user)
