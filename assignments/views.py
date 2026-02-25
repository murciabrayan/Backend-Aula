from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import PermissionDenied

from .models import Assignment, Submission
from .serializers import AssignmentSerializer, SubmissionSerializer
from notifications.models import Notification


# =========================
# 📚 ASSIGNMENTS
# =========================
class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Assignment.objects.all()

        course_id = self.request.query_params.get('course')
        if course_id:
            queryset = queryset.filter(curso_id=course_id)

        if user.role == 'TEACHER':
            queryset = queryset.filter(curso__docente=user)
        elif user.role == 'STUDENT':
            queryset = queryset.filter(curso__estudiantes=user)
        else:
            queryset = Assignment.objects.none()

        return queryset

    def perform_create(self, serializer):
        curso = serializer.validated_data.get('curso')
        if curso.docente != self.request.user:
            raise PermissionDenied(
                "Solo el docente asignado puede crear tareas para este curso."
            )
        serializer.save()


# =========================
# 📥 SUBMISSIONS
# =========================
class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = Submission.objects.all()
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
            queryset = queryset.filter(tarea__curso__docente=user)
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
        """
        Permite al docente calificar una entrega
        y genera una notificación al estudiante.
        """

        entrega = self.get_object()

        # 🔒 Verificar que sea el docente del curso
        if request.user != entrega.tarea.curso.docente:
            return Response(
                {'detail': 'No autorizado'},
                status=status.HTTP_403_FORBIDDEN
            )

        calificacion = request.data.get('calificacion')
        retroalimentacion = request.data.get('retroalimentacion', '')

        # ✅ Validar número
        try:
            calificacion = float(calificacion)
        except (TypeError, ValueError):
            return Response(
                {'detail': 'La calificación debe ser un número'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Validar rango
        if not (0.0 <= calificacion <= 5.0):
            return Response(
                {'detail': 'La calificación debe estar entre 0.0 y 5.0'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Redondear
        calificacion = round(calificacion, 2)

        # 💾 Guardar datos
        entrega.calificacion = calificacion
        entrega.retroalimentacion = retroalimentacion
        entrega.save()

        # 🔔 Crear notificación
        Notification.objects.create(
            usuario=entrega.estudiante,
            titulo="Nueva calificación",
            mensaje=(
                f"Tu tarea '{entrega.tarea.titulo}' "
                f"fue calificada con {calificacion}."
            )
        )

        return Response(
            {'detail': 'Calificación guardada correctamente.'},
            status=status.HTTP_200_OK
        )