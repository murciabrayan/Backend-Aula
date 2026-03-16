from collections import Counter
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response

from accounts.models import User
from courses.models import Course
from .models import Attendance
from .serializers import (
    AttendanceSerializer,
    BulkAttendanceSerializer,
)


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all().select_related("student", "course")
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        user = self.request.user
        queryset = Attendance.objects.all().select_related("student", "course")

        date_value = self.request.query_params.get("date")
        if date_value:
            queryset = queryset.filter(date=date_value)

        course_id = self.request.query_params.get("course")
        if course_id:
            queryset = queryset.filter(course_id=course_id)

        student_id = self.request.query_params.get("student")
        if student_id:
            queryset = queryset.filter(student_id=student_id)

        status_value = self.request.query_params.get("status")
        if status_value:
            queryset = queryset.filter(status=status_value)

        periodo = self.request.query_params.get("periodo")
        if periodo:
            queryset = queryset.filter(periodo=periodo)

        if user.role == "ADMIN":
            return queryset

        if user.role == "TEACHER":
            return queryset.filter(course__docente=user)

        if user.role == "STUDENT":
            return queryset.filter(student=user)

        return Attendance.objects.none()

    def perform_create(self, serializer):
        serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=["get"], url_path="my-records")
    def my_records(self, request):
        if request.user.role != "STUDENT":
            return Response(
                {"detail": "No autorizado"},
                status=status.HTTP_403_FORBIDDEN
            )

        queryset = self.get_queryset().filter(student=request.user)
        serializer = self.get_serializer(
            queryset,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="teacher/course-day")
    def teacher_course_day(self, request):
        if request.user.role != "TEACHER":
            return Response(
                {"detail": "No autorizado"},
                status=status.HTTP_403_FORBIDDEN
            )

        date_value = request.query_params.get("date")
        if not date_value:
            return Response(
                {"detail": "La fecha es requerida en formato YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )

        course = Course.objects.filter(docente=request.user).first()
        if not course:
            return Response(
                {"detail": "El docente no tiene un curso asignado."},
                status=status.HTTP_404_NOT_FOUND
            )

        students = course.estudiantes.filter(role="STUDENT").order_by(
            "first_name",
            "last_name"
        )
        attendance_qs = Attendance.objects.filter(
            course=course,
            date=date_value
        ).select_related("student")

        attendance_map = {item.student_id: item for item in attendance_qs}

        result = []
        for student in students:
            attendance = attendance_map.get(student.id)
            result.append({
                "id": student.id,
                "student_name": f"{student.first_name} {student.last_name}".strip(),
                "attendance_id": attendance.id if attendance else None,
                "status": attendance.status if attendance else "PRESENT",
                "is_justified": attendance.is_justified if attendance else False,
                "justification_type": attendance.justification_type if attendance else "NONE",
                "notes": attendance.notes if attendance else "",
                "periodo": attendance.periodo if attendance else 1,
                "attachment_url": (
                    request.build_absolute_uri(attendance.attachment.url)
                    if attendance and attendance.attachment
                    else None
                ),
            })

        summary_counter = Counter(item["status"] for item in result)

        return Response(
            {
                "course": {
                    "id": course.id,
                    "nombre": course.nombre,
                },
                "date": date_value,
                "students": result,
                "summary": {
                    "present": summary_counter.get("PRESENT", 0),
                    "absent": summary_counter.get("ABSENT", 0),
                    "late": summary_counter.get("LATE", 0),
                    "total": len(result),
                },
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["post"], url_path="teacher/bulk-save")
    def teacher_bulk_save(self, request):
        if request.user.role != "TEACHER":
            return Response(
                {"detail": "No autorizado"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = BulkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        course = Course.objects.filter(docente=request.user).first()
        if not course:
            return Response(
                {"detail": "El docente no tiene un curso asignado."},
                status=status.HTTP_404_NOT_FOUND
            )

        date_value = serializer.validated_data["date"]
        periodo = serializer.validated_data["periodo"]
        records = serializer.validated_data["records"]

        allowed_student_ids = set(
            course.estudiantes.filter(role="STUDENT").values_list("id", flat=True)
        )

        saved_items = []

        for item in records:
            student_id = item["student"]

            if student_id not in allowed_student_ids:
                return Response(
                    {
                        "detail": f"El estudiante {student_id} no pertenece al curso del docente."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            student = get_object_or_404(User, pk=student_id, role="STUDENT")

            attendance, created = Attendance.objects.update_or_create(
                student=student,
                date=date_value,
                defaults={
                    "course": course,
                    "periodo": periodo,
                    "status": item["status"],
                    "notes": item.get("notes", ""),
                    "updated_by": request.user,
                },
            )

            if created and not attendance.created_by:
                attendance.created_by = request.user
                attendance.save(update_fields=["created_by"])

            saved_items.append(attendance)

        response_serializer = AttendanceSerializer(
            saved_items,
            many=True,
            context={"request": request},
        )
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="course-summary")
    def course_summary(self, request):
        user = request.user
        course_id = request.query_params.get("course")
        date_value = request.query_params.get("date")

        if not course_id or not date_value:
            return Response(
                {"detail": "Debes enviar course y date."},
                status=status.HTTP_400_BAD_REQUEST
            )

        course = get_object_or_404(Course, pk=course_id)

        if user.role == "TEACHER" and course.docente_id != user.id:
            return Response(
                {"detail": "No autorizado para este curso."},
                status=status.HTTP_403_FORBIDDEN
            )

        if user.role not in ["ADMIN", "TEACHER"]:
            return Response(
                {"detail": "No autorizado"},
                status=status.HTTP_403_FORBIDDEN
            )

        queryset = Attendance.objects.filter(course=course, date=date_value)
        counter = Counter(queryset.values_list("status", flat=True))

        return Response(
            {
                "course": {
                    "id": course.id,
                    "nombre": course.nombre,
                },
                "date": date_value,
                "present": counter.get("PRESENT", 0),
                "absent": counter.get("ABSENT", 0),
                "late": counter.get("LATE", 0),
                "justified": queryset.filter(is_justified=True).count(),
                "total": queryset.count(),
            },
            status=status.HTTP_200_OK
        )