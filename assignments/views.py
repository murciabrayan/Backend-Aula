from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Assignment, Submission
from .serializers import AssignmentSerializer, SubmissionSerializer
from courses.models import Course

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
            raise PermissionError("Solo el docente asignado puede crear tareas para este curso.")
        serializer.save()


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
            raise PermissionError("Solo los estudiantes pueden subir entregas.")
        serializer.save(estudiante=user)

    @action(detail=True, methods=['post'])
    def calificar(self, request, pk=None):
        """Permite al docente calificar una entrega"""
        entrega = self.get_object()
        if request.user != entrega.tarea.curso.docente:
            return Response({'detail': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)

        calificacion = request.data.get('calificacion')
        retroalimentacion = request.data.get('retroalimentacion', '')

        try:
            calificacion = float(calificacion)
        except (TypeError, ValueError):
            return Response({'detail': 'La calificación debe ser un número'}, status=status.HTTP_400_BAD_REQUEST)

        entrega.calificacion = calificacion
        entrega.retroalimentacion = retroalimentacion
        entrega.save()

        return Response({'detail': 'Calificación y retroalimentación guardadas correctamente.'}, status=status.HTTP_200_OK)
