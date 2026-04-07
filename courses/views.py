from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Course, Subject, Area
from .serializers import CourseSerializer, SubjectSerializer, AreaSerializer
from accounts.models import User
from accounts.permissions import IsAdminRoleOrReadOnly


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAdminRoleOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        queryset = Course.objects.all().select_related(
            "docente",
            "director_curso",
        ).prefetch_related(
            "estudiantes",
            "materias",
            "materias__docente",
            "areas",
        )

        if user.role == "ADMIN":
            return queryset

        if user.role == "TEACHER":
            return queryset.filter(
                Q(director_curso=user) |
                Q(materias__docente=user)
            ).distinct()

        if user.role == "STUDENT":
            return queryset.filter(estudiantes=user)

        return Course.objects.none()

    @action(detail=True, methods=['post'], url_path='add-students')
    def add_students(self, request, pk=None):
        course = self.get_object()
        ids = request.data.get('students', [])

        if not isinstance(ids, list):
            return Response(
                {'detail': 'students must be a list of ids'},
                status=status.HTTP_400_BAD_REQUEST
            )

        users = User.objects.filter(id__in=ids, role='STUDENT')
        course.estudiantes.add(*users)

        return Response(
            {'detail': 'students added'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='remove-student')
    def remove_student(self, request, pk=None):
        course = self.get_object()
        student_id = request.data.get('student')

        if student_id is None:
            return Response(
                {'detail': 'student id required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(pk=student_id, role='STUDENT')
        except User.DoesNotExist:
            return Response(
                {'detail': 'student not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        course.estudiantes.remove(user)

        return Response(
            {'detail': 'student removed'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='remove-teacher')
    def remove_teacher(self, request, pk=None):
        course = self.get_object()
        course.director_curso = None
        course.docente = None
        course.save(update_fields=["director_curso", "docente"])

        return Response(
            {'detail': 'teacher removed'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'], url_path='teacher/course')
    def teacher_course(self, request):
        course = Course.objects.filter(
            director_curso=request.user
        ).first()

        if not course:
            return Response(
                {"detail": "El docente no tiene un curso dirigido asignado."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(course)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AreaViewSet(viewsets.ModelViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    permission_classes = [IsAdminRoleOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        queryset = Area.objects.all()

        course_id = self.request.query_params.get("course")
        if course_id:
            queryset = queryset.filter(curso_id=course_id)

        if user.role == "ADMIN":
            return queryset

        if user.role == "TEACHER":
            return queryset.filter(
                Q(curso__director_curso=user) |
                Q(curso__materias__docente=user)
            ).distinct()

        if user.role == "STUDENT":
            return queryset.filter(curso__estudiantes=user)

        return Area.objects.none()


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [IsAdminRoleOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        queryset = Subject.objects.all()

        course_id = self.request.query_params.get('course')
        if course_id:
            queryset = queryset.filter(curso__id=course_id)

        area_id = self.request.query_params.get('area')
        if area_id:
            queryset = queryset.filter(area_id=area_id)

        if user.role == 'ADMIN':
            return queryset

        if user.role == 'TEACHER':
            return queryset.filter(
                Q(docente=user) |
                Q(curso__director_curso=user)
            ).distinct()

        if user.role == 'STUDENT':
            return queryset.filter(curso__estudiantes=user)

        return Subject.objects.none()
