from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import PermissionDenied

from .models import Assignment, Submission
from .serializers import AssignmentSerializer, SubmissionSerializer
from notifications.models import Notification


# =========================
# 📘 ASSIGNMENTS
# =========================
class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()  # ✅ NECESARIO PARA EL ROUTER
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Assignment.objects.all()

        course_id = self.request.query_params.get('course')
        if course_id:
            queryset = queryset.filter(materia__curso_id=course_id)

        subject_id = self.request.query_params.get('subject')
        if subject_id:
            queryset = queryset.filter(materia_id=subject_id)

        if user.role == 'TEACHER':
            queryset = queryset.filter(
                materia__curso__docente=user
            )

        elif user.role == 'STUDENT':
            queryset = queryset.filter(
                materia__curso__estudiantes=user
            )

        else:
            queryset = Assignment.objects.none()

        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        materia = serializer.validated_data.get('materia')

        if user.role != 'TEACHER':
            raise PermissionDenied(
                "Solo los docentes pueden crear tareas."
            )

        if materia.curso.docente != user:
            raise PermissionDenied(
                "Solo el docente asignado al curso puede crear tareas en esta materia."
            )

        serializer.save()


# =========================
# 📥 SUBMISSIONS
# =========================
class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = Submission.objects.all()  # ✅ NECESARIO PARA EL ROUTER
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Submission.objects.all()

        assignment_id = self.request.query_params.get('assignment')
        if assignment_id:
            queryset = queryset.filter(tarea_id=assignment_id)

        if user.role == 'STUDENT':
            queryset = queryset.filter(estudiante=user)

        elif user.role == 'TEACHER':
            queryset = queryset.filter(
                tarea__materia__curso__docente=user
            )

        else:
            queryset = Submission.objects.none()

        return queryset

    def perform_create(self, serializer):
        user = self.request.user

        if user.role != 'STUDENT':
            raise PermissionDenied(
                "Solo los estudiantes pueden subir entregas."
            )

        serializer.save(estudiante=user)

    # =========================
    # ⭐ CALIFICAR ENTREGA
    # =========================
    @action(detail=True, methods=['post'])
    def calificar(self, request, pk=None):
        entrega = self.get_object()
        user = request.user

        if entrega.tarea.materia.curso.docente != user:
            return Response(
                {'detail': 'No autorizado'},
                status=status.HTTP_403_FORBIDDEN
            )

        calificacion = request.data.get('calificacion')
        retroalimentacion = request.data.get('retroalimentacion', '')

        try:
            calificacion = float(calificacion)
        except (TypeError, ValueError):
            return Response(
                {'detail': 'La calificación debe ser un número'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not (0.0 <= calificacion <= 5.0):
            return Response(
                {'detail': 'La calificación debe estar entre 0.0 y 5.0'},
                status=status.HTTP_400_BAD_REQUEST
            )

        entrega.calificacion = round(calificacion, 2)
        entrega.retroalimentacion = retroalimentacion
        entrega.save()

        Notification.objects.create(
            usuario=entrega.estudiante,
            titulo="Nueva calificación",
            mensaje=(
                f"Tu tarea '{entrega.tarea.titulo}' "
                f"fue calificada con {entrega.calificacion}."
            )
        )

        return Response(
            {'detail': 'Calificación guardada correctamente.'},
            status=status.HTTP_200_OK
        )