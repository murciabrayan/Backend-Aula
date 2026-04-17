from collections import Counter

from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from accounts.models import User
from accounts.permissions import IsAdminRole
from courses.models import Course
from .models import Attendance, AttendanceEvent
from .serializers import AttendanceSerializer, BulkAttendanceSerializer


def build_attendance_snapshot(attendance):
    return {
        "status": attendance.status,
        "periodo": attendance.periodo,
        "is_justified": attendance.is_justified,
        "justification_type": attendance.justification_type,
        "teacher_notes": attendance.teacher_notes or "",
        "admin_notes": attendance.admin_notes or "",
        "has_attachment": bool(attendance.attachment),
    }


def build_attendance_changes(previous, current):
    changes = {}
    labels = {
        "status": "estado",
        "periodo": "periodo",
        "is_justified": "justificada",
        "justification_type": "tipo de justificación",
        "teacher_notes": "observación docente",
        "admin_notes": "observación administrativa",
        "has_attachment": "soporte",
    }

    for key, label in labels.items():
        previous_value = previous.get(key)
        current_value = current.get(key)
        if previous_value != current_value:
            changes[key] = {
                "label": label,
                "from": previous_value,
                "to": current_value,
            }

    return changes


def summarize_attendance_action(user, changes, created=False):
    actor_role = getattr(user, "role", "") if user else ""

    if actor_role == "ADMIN":
        if changes.get("is_justified") or changes.get("justification_type"):
            return "ADMIN_JUSTIFIED", "Coordinación registró o actualizó una justificación"
        if changes.get("has_attachment"):
            return "ADMIN_SUPPORT_ADDED", "Coordinación adjuntó un soporte"
        if created:
            return "ADMIN_CREATED", "Coordinación creó el registro de asistencia"
        return "ADMIN_UPDATED", "Coordinación corrigió el registro de asistencia"

    if created:
        return "TEACHER_CREATED", "El docente registró la asistencia inicial"
    return "TEACHER_UPDATED", "El docente actualizó la asistencia"


def log_attendance_event(attendance, *, user, before_snapshot=None, created=False):
    current_snapshot = build_attendance_snapshot(attendance)
    previous_snapshot = before_snapshot or {}
    changes = build_attendance_changes(previous_snapshot, current_snapshot)

    if not created and not changes:
        return None

    action, summary = summarize_attendance_action(user, changes, created=created)

    actor_role = getattr(user, "role", "") if user else ""
    event_notes = (
        attendance.admin_notes
        if actor_role == "ADMIN"
        else attendance.teacher_notes
    ) or attendance.notes or ""

    return AttendanceEvent.objects.create(
        attendance=attendance,
        actor=user,
        actor_role=actor_role,
        action=action,
        summary=summary,
        notes=event_notes,
        details={"changes": changes},
    )


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all().select_related(
        "student",
        "course",
        "created_by",
        "updated_by",
    ).prefetch_related("events__actor")
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAdminRole()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        queryset = Attendance.objects.all().select_related(
            "student",
            "course",
            "created_by",
            "updated_by",
        ).prefetch_related("events__actor")

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
            return queryset.filter(
                course__director_curso=user
            )

        if user.role == "STUDENT":
            return queryset.filter(student=user)

        return Attendance.objects.none()

    def perform_create(self, serializer):
        attendance = serializer.save(
            created_by=self.request.user,
            updated_by=self.request.user,
        )
        attendance.notes = attendance.admin_notes or attendance.teacher_notes or attendance.notes
        attendance.save(update_fields=["notes"])
        log_attendance_event(attendance, user=self.request.user, created=True)

    def perform_update(self, serializer):
        before_snapshot = build_attendance_snapshot(serializer.instance)
        attendance = serializer.save(updated_by=self.request.user)
        attendance.notes = attendance.admin_notes or attendance.teacher_notes or attendance.notes
        attendance.save(update_fields=["notes"])
        log_attendance_event(
            attendance,
            user=self.request.user,
            before_snapshot=before_snapshot,
            created=False,
        )

    @action(detail=False, methods=["get"], url_path="my-records")
    def my_records(self, request):
        if request.user.role != "STUDENT":
            return Response({"detail": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        queryset = self.get_queryset().filter(student=request.user)
        serializer = self.get_serializer(queryset, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="teacher/course-day")
    def teacher_course_day(self, request):
        if request.user.role != "TEACHER":
            return Response({"detail": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        date_value = request.query_params.get("date")
        if not date_value:
            return Response(
                {"detail": "La fecha es requerida en formato YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        course = Course.objects.filter(
            director_curso=request.user
        ).first()
        if not course:
            return Response(
                {"detail": "El docente no tiene un curso como director asignado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        students = course.estudiantes.filter(role="STUDENT").order_by("first_name", "last_name")
        attendance_qs = Attendance.objects.filter(course=course, date=date_value).select_related(
            "student",
            "created_by",
            "updated_by",
        ).prefetch_related("events__actor")

        attendance_map = {item.student_id: item for item in attendance_qs}

        result = []
        for student in students:
            attendance = attendance_map.get(student.id)
            latest_admin_event = None
            latest_teacher_event = None

            if attendance:
                latest_admin_event = next(
                    (event for event in attendance.events.all() if event.actor_role == "ADMIN"),
                    None,
                )
                latest_teacher_event = next(
                    (event for event in attendance.events.all() if event.actor_role == "TEACHER"),
                    None,
                )

            result.append(
                {
                    "id": student.id,
                    "student_name": f"{student.first_name} {student.last_name}".strip(),
                    "attendance_id": attendance.id if attendance else None,
                    "status": attendance.status if attendance else "PRESENT",
                    "is_justified": attendance.is_justified if attendance else False,
                    "justification_type": attendance.justification_type if attendance else "NONE",
                    "notes": attendance.teacher_notes if attendance else "",
                    "teacher_notes": attendance.teacher_notes if attendance else "",
                    "admin_notes": attendance.admin_notes if attendance else "",
                    "periodo": attendance.periodo if attendance else 1,
                    "attachment_url": (
                        request.build_absolute_uri(attendance.attachment.url)
                        if attendance and attendance.attachment
                        else None
                    ),
                    "created_by_name": (
                        f"{attendance.created_by.first_name} {attendance.created_by.last_name}".strip()
                        if attendance and attendance.created_by
                        else None
                    ),
                    "updated_by_name": (
                        f"{attendance.updated_by.first_name} {attendance.updated_by.last_name}".strip()
                        if attendance and attendance.updated_by
                        else None
                    ),
                    "updated_by_role": attendance.updated_by.role if attendance and attendance.updated_by else None,
                    "latest_admin_event": (
                        {
                            "summary": latest_admin_event.summary,
                            "notes": latest_admin_event.notes,
                            "actor_name": f"{latest_admin_event.actor.first_name} {latest_admin_event.actor.last_name}".strip()
                            if latest_admin_event and latest_admin_event.actor
                            else None,
                            "created_at": latest_admin_event.created_at,
                            "details": latest_admin_event.details,
                        }
                        if latest_admin_event
                        else None
                    ),
                    "latest_teacher_event": (
                        {
                            "summary": latest_teacher_event.summary,
                            "notes": latest_teacher_event.notes,
                            "actor_name": f"{latest_teacher_event.actor.first_name} {latest_teacher_event.actor.last_name}".strip()
                            if latest_teacher_event and latest_teacher_event.actor
                            else None,
                            "created_at": latest_teacher_event.created_at,
                            "details": latest_teacher_event.details,
                        }
                        if latest_teacher_event
                        else None
                    ),
                }
            )

        summary_counter = Counter(item["status"] for item in result)

        return Response(
            {
                "course": {"id": course.id, "nombre": course.nombre},
                "date": date_value,
                "students": result,
                "summary": {
                    "present": summary_counter.get("PRESENT", 0),
                    "absent": summary_counter.get("ABSENT", 0),
                    "late": summary_counter.get("LATE", 0),
                    "total": len(result),
                },
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], url_path="teacher/bulk-save")
    def teacher_bulk_save(self, request):
        if request.user.role != "TEACHER":
            return Response({"detail": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        serializer = BulkAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        course = Course.objects.filter(
            director_curso=request.user
        ).first()
        if not course:
            return Response(
                {"detail": "El docente no tiene un curso como director asignado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        date_value = serializer.validated_data["date"]
        periodo = serializer.validated_data["periodo"]
        records = serializer.validated_data["records"]

        allowed_student_ids = set(course.estudiantes.filter(role="STUDENT").values_list("id", flat=True))
        saved_items = []

        for item in records:
            student_id = item["student"]

            if student_id not in allowed_student_ids:
                return Response(
                    {"detail": f"El estudiante {student_id} no pertenece al curso del docente."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            student = get_object_or_404(User, pk=student_id, role="STUDENT")
            existing = Attendance.objects.filter(student=student, date=date_value).first()
            before_snapshot = build_attendance_snapshot(existing) if existing else None

            attendance, created = Attendance.objects.update_or_create(
                student=student,
                date=date_value,
                defaults={
                    "course": course,
                    "periodo": periodo,
                    "status": item["status"],
                    "notes": item.get("notes", ""),
                    "teacher_notes": item.get("notes", ""),
                    "updated_by": request.user,
                },
            )

            if created and not attendance.created_by:
                attendance.created_by = request.user
                attendance.save(update_fields=["created_by"])

            log_attendance_event(
                attendance,
                user=request.user,
                before_snapshot=before_snapshot,
                created=created,
            )
            saved_items.append(attendance)

        response_serializer = AttendanceSerializer(saved_items, many=True, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="course-summary")
    def course_summary(self, request):
        user = request.user
        course_id = request.query_params.get("course")
        date_value = request.query_params.get("date")

        if not course_id or not date_value:
            return Response({"detail": "Debes enviar course y date."}, status=status.HTTP_400_BAD_REQUEST)

        course = get_object_or_404(Course, pk=course_id)

        if user.role == "TEACHER" and course.director_curso_id != user.id:
            return Response({"detail": "No autorizado para este curso."}, status=status.HTTP_403_FORBIDDEN)

        if user.role not in ["ADMIN", "TEACHER"]:
            return Response({"detail": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        queryset = Attendance.objects.filter(course=course, date=date_value)
        counter = Counter(queryset.values_list("status", flat=True))

        return Response(
            {
                "course": {"id": course.id, "nombre": course.nombre},
                "date": date_value,
                "present": counter.get("PRESENT", 0),
                "absent": counter.get("ABSENT", 0),
                "late": counter.get("LATE", 0),
                "justified": queryset.filter(is_justified=True).count(),
                "total": queryset.count(),
            },
            status=status.HTTP_200_OK,
        )
