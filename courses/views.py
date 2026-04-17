from django.db import transaction
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Course, Subject, Area
from .serializers import (
    CourseSerializer,
    SubjectSerializer,
    AreaSerializer,
    SubjectBulkAssignSerializer,
    SubjectCourseSyncSerializer,
)
from accounts.models import User
from accounts.permissions import IsAdminRoleOrReadOnly


def is_positive_int(value):
    try:
        return int(value) > 0
    except (TypeError, ValueError):
        return False


def resolve_area_for_course(source_area, course):
    if not source_area:
        return None

    existing_area = Area.objects.filter(
        curso=course,
        nombre__iexact=source_area.nombre,
    ).first()

    if existing_area:
        return existing_area

    return Area.objects.create(
        curso=course,
        nombre=source_area.nombre,
    )


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
        already_assigned = Course.objects.filter(estudiantes__in=users).exclude(pk=course.pk).distinct()

        if already_assigned.exists():
            assigned_students = users.filter(cursos__in=already_assigned).distinct()
            assigned_names = ", ".join(
                f"{student.first_name} {student.last_name}".strip()
                for student in assigned_students
            )
            return Response(
                {
                    'detail': (
                        'No se puede asignar un estudiante a dos cursos. '
                        f'Ya tienen curso asignado: {assigned_names}.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

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
            if not is_positive_int(course_id):
                return Area.objects.none()
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
        teaching_only = self.request.query_params.get("teaching_only")

        course_id = self.request.query_params.get('course')
        if course_id:
            if not is_positive_int(course_id):
                return Subject.objects.none()
            queryset = queryset.filter(curso__id=course_id)

        area_id = self.request.query_params.get('area')
        if area_id:
            if not is_positive_int(area_id):
                return Subject.objects.none()
            queryset = queryset.filter(area_id=area_id)

        if user.role == 'ADMIN':
            return queryset

        if user.role == 'TEACHER':
            if teaching_only and teaching_only.lower() in ["1", "true", "yes"]:
                return queryset.filter(docente=user).distinct()
            return queryset.filter(
                Q(docente=user) |
                Q(curso__director_curso=user)
            ).distinct()

        if user.role == 'STUDENT':
            return queryset.filter(curso__estudiantes=user)

        return Subject.objects.none()

    @action(detail=False, methods=["post"], url_path="bulk-assign")
    @transaction.atomic
    def bulk_assign(self, request):
        serializer = SubjectBulkAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        nombre = serializer.validated_data["nombre"].strip()
        area = serializer.validated_data.get("area")
        docente = serializer.validated_data.get("docente")
        cursos = serializer.validated_data["cursos"]

        created_subjects = []
        updated_subjects = []

        for course in cursos:
            subject = Subject.objects.filter(
                curso=course,
                nombre__iexact=nombre,
            ).first()

            if not subject:
                subject = Subject.objects.create(
                    curso=course,
                    nombre=nombre,
                    area=resolve_area_for_course(area, course),
                    docente=docente,
                )
                created_subjects.append(subject)
                continue

            resolved_area = resolve_area_for_course(area, course)
            if (
                subject.nombre != nombre
                or subject.docente_id != getattr(docente, "id", None)
                or subject.area_id != getattr(resolved_area, "id", None)
            ):
                subject.nombre = nombre
                subject.docente = docente
                subject.area = resolved_area
                subject.save(update_fields=["nombre", "docente", "area"])

            updated_subjects.append(subject)

        response_serializer = self.get_serializer(created_subjects + updated_subjects, many=True)
        return Response(
            {
                "detail": "Asignación masiva procesada correctamente.",
                "created_count": len(created_subjects),
                "updated_count": len(updated_subjects),
                "subjects": response_serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], url_path="sync-courses")
    @transaction.atomic
    def sync_courses(self, request):
        serializer = SubjectCourseSyncSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        base_subject = serializer.validated_data["subject"]
        nombre = serializer.validated_data["nombre"].strip()
        area = serializer.validated_data.get("area")
        docente = serializer.validated_data.get("docente")
        cursos = serializer.validated_data["cursos"]
        desired_course_ids = {course.id for course in cursos}

        linked_subjects = Subject.objects.filter(
            nombre__iexact=base_subject.nombre,
            docente_id=base_subject.docente_id,
        ).select_related("curso")

        if not linked_subjects.filter(id=base_subject.id).exists():
            linked_subjects = Subject.objects.filter(id=base_subject.id).select_related("curso")

        current_by_course = {subject.curso_id: subject for subject in linked_subjects}
        synced_subjects = []
        blocked_removals = []

        for course in cursos:
            subject = current_by_course.get(course.id)
            if not subject:
                subject = Subject.objects.filter(curso=course, nombre__iexact=nombre).first()

            if subject:
                changed_fields = []
                resolved_area = resolve_area_for_course(area, course)
                if subject.nombre != nombre:
                    subject.nombre = nombre
                    changed_fields.append("nombre")
                if subject.docente_id != getattr(docente, "id", None):
                    subject.docente = docente
                    changed_fields.append("docente")
                if subject.area_id != getattr(resolved_area, "id", None):
                    subject.area = resolved_area
                    changed_fields.append("area")
                if changed_fields:
                    subject.save(update_fields=changed_fields)
            else:
                subject = Subject.objects.create(
                    curso=course,
                    nombre=nombre,
                    area=resolve_area_for_course(area, course),
                    docente=docente,
                )

            synced_subjects.append(subject)

        for subject in linked_subjects:
            if subject.curso_id in desired_course_ids:
                continue

            if subject.tareas.exists() or subject.indicadores_asignados.exists():
                blocked_removals.append(
                    {
                        "subject_id": subject.id,
                        "course_id": subject.curso_id,
                        "course_name": subject.curso.nombre,
                    }
                )
                continue

            subject.delete()

        response_serializer = self.get_serializer(synced_subjects, many=True)
        return Response(
            {
                "detail": "Cursos de la materia sincronizados correctamente.",
                "blocked_removals": blocked_removals,
                "subjects": response_serializer.data,
            },
            status=status.HTTP_200_OK,
        )
