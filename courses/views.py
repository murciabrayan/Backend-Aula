# courses/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Course
from .serializers import CourseSerializer
from accounts.models import User

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    # 🔹 Asignar estudiantes a un curso
    @action(detail=True, methods=['post'], url_path='add-students')
    def add_students(self, request, pk=None):
        course = self.get_object()
        ids = request.data.get('students', [])
        if not isinstance(ids, list):
            return Response({'detail': 'students must be a list of ids'}, status=status.HTTP_400_BAD_REQUEST)
        users = User.objects.filter(id__in=ids, role='STUDENT')
        course.estudiantes.add(*users)
        return Response({'detail': 'students added'}, status=status.HTTP_200_OK)

    # 🔹 Remover un estudiante del curso
    @action(detail=True, methods=['post'], url_path='remove-student')
    def remove_student(self, request, pk=None):
        course = self.get_object()
        student_id = request.data.get('student')
        if student_id is None:
            return Response({'detail': 'student id required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(pk=student_id, role='STUDENT')
        except User.DoesNotExist:
            return Response({'detail': 'student not found'}, status=status.HTTP_404_NOT_FOUND)
        course.estudiantes.remove(user)
        return Response({'detail': 'student removed'}, status=status.HTTP_200_OK)

    # 🔹 Remover docente del curso
    @action(detail=True, methods=['post'], url_path='remove-teacher')
    def remove_teacher(self, request, pk=None):
        course = self.get_object()
        course.docente = None
        course.save()
        return Response({'detail': 'teacher removed'}, status=status.HTTP_200_OK)

    # 🔹 Obtener curso asignado al docente autenticado
    @action(detail=False, methods=['get'], url_path='teacher/course')
    def teacher_course(self, request):
        """
        Retorna el curso asignado al docente autenticado.
        Si tiene varios, devuelve el primero.
        """
        course = Course.objects.filter(docente=request.user).first()
        if not course:
            return Response(
                {"detail": "El docente no tiene un curso asignado."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = self.get_serializer(course)
        return Response(serializer.data, status=status.HTTP_200_OK)
