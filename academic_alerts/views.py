from collections import defaultdict
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from courses.models import Course
from assignments.models import Assignment, Submission
from attendance.models import Attendance
from .models import AcademicAlert
from .serializers import (
    AcademicAlertSerializer,
    ResolveAcademicAlertSerializer,
)


LOW_GRADE_THRESHOLD = 3.0
LOW_GRADE_WARNING_THRESHOLD = 3.4

ABSENCE_WARNING_THRESHOLD = 3
ABSENCE_CRITICAL_THRESHOLD = 5

MISSING_ASSIGNMENTS_WARNING_THRESHOLD = 2
MISSING_ASSIGNMENTS_CRITICAL_THRESHOLD = 4


def avg_or_none(values):
    if not values:
        return None
    return round(sum(values) / len(values), 1)


def alert_level_for_grade(avg_value):
    if avg_value is None:
        return None
    if avg_value < LOW_GRADE_THRESHOLD:
        return "CRITICAL"
    if avg_value < LOW_GRADE_WARNING_THRESHOLD:
        return "WARNING"
    return None


def alert_level_for_absences(total_absences):
    if total_absences >= ABSENCE_CRITICAL_THRESHOLD:
        return "CRITICAL"
    if total_absences >= ABSENCE_WARNING_THRESHOLD:
        return "WARNING"
    return None


def alert_level_for_missing_assignments(total_missing):
    if total_missing >= MISSING_ASSIGNMENTS_CRITICAL_THRESHOLD:
        return "CRITICAL"
    if total_missing >= MISSING_ASSIGNMENTS_WARNING_THRESHOLD:
        return "WARNING"
    return None


def build_grade_alert_messages(student_name, avg_value, period):
    avg_text = f"{avg_value:.1f}" if avg_value is not None else "sin promedio"
    return {
        "title": f"Alerta por bajo rendimiento - Periodo {period}",
        "message_student": (
            f"Tu promedio actual en el periodo {period} es {avg_text}, "
            "por debajo del nivel esperado. Revisa tus calificaciones y busca apoyo con tu docente."
        ),
        "message_teacher": (
            f"El estudiante {student_name} presenta bajo rendimiento académico en el periodo {period}, "
            f"con promedio actual de {avg_text}. Se recomienda seguimiento."
        ),
        "message_admin": (
            f"Se detectó una alerta académica por bajo rendimiento para {student_name} "
            f"en el periodo {period}, con promedio de {avg_text}."
        ),
    }


def build_absence_alert_messages(student_name, total_absences, period):
    return {
        "title": f"Alerta por inasistencia - Periodo {period}",
        "message_student": (
            f"Registras {total_absences} ausencias no justificadas en el periodo {period}. "
            "Esto puede afectar tu proceso académico."
        ),
        "message_teacher": (
            f"El estudiante {student_name} acumula {total_absences} ausencias no justificadas "
            f"en el periodo {period}. Se recomienda acompañamiento."
        ),
        "message_admin": (
            f"Se detectó riesgo por inasistencia para {student_name}. "
            f"Actualmente registra {total_absences} ausencias no justificadas en el periodo {period}."
        ),
    }


def build_missing_alert_messages(student_name, total_missing, period):
    return {
        "title": f"Alerta por tareas no entregadas - Periodo {period}",
        "message_student": (
            f"Tienes {total_missing} actividades vencidas sin entregar en el periodo {period}. "
            "Debes ponerte al día lo antes posible."
        ),
        "message_teacher": (
            f"El estudiante {student_name} tiene {total_missing} actividades vencidas sin entregar "
            f"en el periodo {period}."
        ),
        "message_admin": (
            f"Se detectó incumplimiento académico para {student_name}, con "
            f"{total_missing} actividades vencidas sin entregar en el periodo {period}."
        ),
    }


def create_or_update_alert(
    *,
    student,
    course,
    period,
    alert_type,
    level,
    title,
    message_student,
    message_teacher,
    message_admin,
    metric_value,
    threshold_value,
    details,
):
    alert, created = AcademicAlert.objects.update_or_create(
        student=student,
        course=course,
        period=period,
        alert_type=alert_type,
        defaults={
            "level": level,
            "status": "ACTIVE",
            "title": title,
            "message_student": message_student,
            "message_teacher": message_teacher,
            "message_admin": message_admin,
            "metric_value": metric_value,
            "threshold_value": threshold_value,
            "details": details,
            "resolved_by": None,
            "resolution_notes": "",
            "resolved_at": None,
        },
    )
    return alert, created


def resolve_missing_alerts(student, course, period, active_types):
    AcademicAlert.objects.filter(
        student=student,
        course=course,
        period=period,
        status="ACTIVE",
    ).exclude(alert_type__in=active_types).update(
        status="RESOLVED",
        resolved_at=timezone.now(),
    )


def calculate_student_average_for_period(student, course, period):
    assignments = Assignment.objects.filter(
        materia__curso=course,
        periodo=period,
    )

    submissions = Submission.objects.filter(
        estudiante=student,
        tarea__in=assignments,
        calificacion__isnull=False,
    ).select_related("tarea")

    subject_scores = defaultdict(list)
    for sub in submissions:
        if sub.calificacion is None:
            continue
        subject_scores[sub.tarea.materia_id].append(float(sub.calificacion))

    subject_averages = [
        avg_or_none(grades)
        for grades in subject_scores.values()
        if grades
    ]
    subject_averages = [value for value in subject_averages if value is not None]

    return avg_or_none(subject_averages), assignments.count(), submissions.count()


def calculate_student_absences_for_period(student, course, period):
    return Attendance.objects.filter(
        student=student,
        course=course,
        periodo=period,
        status="ABSENT",
        is_justified=False,
    ).count()


def calculate_missing_assignments_for_period(student, course, period):
    today = timezone.localdate()
    assignments = Assignment.objects.filter(
        materia__curso=course,
        periodo=period,
        fecha_entrega__isnull=False,
        fecha_entrega__lt=today,
    )

    submitted_task_ids = set(
        Submission.objects.filter(
            estudiante=student,
            tarea__in=assignments,
        ).values_list("tarea_id", flat=True)
    )

    missing_assignments = [task for task in assignments if task.id not in submitted_task_ids]
    return missing_assignments


@transaction.atomic
def generate_alerts_for_course(course, period):
    students = course.estudiantes.filter(role="STUDENT").order_by("first_name", "last_name")
    generated_alerts = []

    for student in students:
        student_name = f"{student.first_name} {student.last_name}".strip()
        active_types = []

        avg_value, total_assignments, total_graded = calculate_student_average_for_period(
            student, course, period
        )
        grade_level = alert_level_for_grade(avg_value)
        if grade_level:
            messages = build_grade_alert_messages(student_name, avg_value, period)
            alert, _ = create_or_update_alert(
                student=student,
                course=course,
                period=period,
                alert_type="LOW_GRADE",
                level=grade_level,
                title=messages["title"],
                message_student=messages["message_student"],
                message_teacher=messages["message_teacher"],
                message_admin=messages["message_admin"],
                metric_value=avg_value,
                threshold_value=LOW_GRADE_THRESHOLD,
                details={
                    "period": period,
                    "total_assignments": total_assignments,
                    "total_graded": total_graded,
                },
            )
            generated_alerts.append(alert)
            active_types.append("LOW_GRADE")

        total_absences = calculate_student_absences_for_period(student, course, period)
        absence_level = alert_level_for_absences(total_absences)
        if absence_level:
            messages = build_absence_alert_messages(student_name, total_absences, period)
            alert, _ = create_or_update_alert(
                student=student,
                course=course,
                period=period,
                alert_type="ABSENCE_RISK",
                level=absence_level,
                title=messages["title"],
                message_student=messages["message_student"],
                message_teacher=messages["message_teacher"],
                message_admin=messages["message_admin"],
                metric_value=float(total_absences),
                threshold_value=float(ABSENCE_WARNING_THRESHOLD),
                details={
                    "period": period,
                    "absences": total_absences,
                },
            )
            generated_alerts.append(alert)
            active_types.append("ABSENCE_RISK")

        missing_assignments = calculate_missing_assignments_for_period(student, course, period)
        total_missing = len(missing_assignments)
        missing_level = alert_level_for_missing_assignments(total_missing)
        if missing_level:
            messages = build_missing_alert_messages(student_name, total_missing, period)
            alert, _ = create_or_update_alert(
                student=student,
                course=course,
                period=period,
                alert_type="MISSING_ASSIGNMENTS",
                level=missing_level,
                title=messages["title"],
                message_student=messages["message_student"],
                message_teacher=messages["message_teacher"],
                message_admin=messages["message_admin"],
                metric_value=float(total_missing),
                threshold_value=float(MISSING_ASSIGNMENTS_WARNING_THRESHOLD),
                details={
                    "period": period,
                    "missing_assignments": [
                        {
                            "id": item.id,
                            "titulo": item.titulo,
                            "fecha_entrega": str(item.fecha_entrega) if item.fecha_entrega else None,
                            "materia": item.materia.nombre,
                        }
                        for item in missing_assignments
                    ],
                },
            )
            generated_alerts.append(alert)
            active_types.append("MISSING_ASSIGNMENTS")

        resolve_missing_alerts(student, course, period, active_types)

    return generated_alerts


class AcademicAlertViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AcademicAlert.objects.all().select_related("student", "course", "resolved_by")
    serializer_class = AcademicAlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = AcademicAlert.objects.all().select_related(
            "student",
            "course",
            "resolved_by",
        )

        period = self.request.query_params.get("period")
        if period:
            queryset = queryset.filter(period=period)

        course_id = self.request.query_params.get("course")
        if course_id:
            queryset = queryset.filter(course_id=course_id)

        alert_type = self.request.query_params.get("alert_type")
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)

        status_value = self.request.query_params.get("status")
        if status_value:
            queryset = queryset.filter(status=status_value)

        if user.role == "ADMIN":
            return queryset

        if user.role == "TEACHER":
            return queryset.filter(course__docente=user)

        if user.role == "STUDENT":
            return queryset.filter(student=user)

        return AcademicAlert.objects.none()

    @action(detail=False, methods=["post"], url_path="generate")
    def generate(self, request):
        user = request.user
        if user.role not in ["ADMIN", "TEACHER"]:
            return Response(
                {"detail": "No autorizado"},
                status=status.HTTP_403_FORBIDDEN,
            )

        course_id = request.data.get("course")
        period = request.data.get("period")

        if not course_id or not period:
            return Response(
                {"detail": "Debes enviar course y period."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        course = get_object_or_404(Course, pk=course_id)

        if user.role == "TEACHER" and course.docente_id != user.id:
            return Response(
                {"detail": "No autorizado para generar alertas de este curso."},
                status=status.HTTP_403_FORBIDDEN,
            )

        generated_alerts = generate_alerts_for_course(course, int(period))
        serializer = self.get_serializer(generated_alerts, many=True)

        return Response(
            {
                "detail": "Alertas generadas correctamente.",
                "count": len(generated_alerts),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], url_path="resolve")
    def resolve(self, request, pk=None):
        user = request.user
        if user.role not in ["ADMIN", "TEACHER"]:
            return Response(
                {"detail": "No autorizado"},
                status=status.HTTP_403_FORBIDDEN,
            )

        alert = self.get_object()

        if user.role == "TEACHER" and alert.course.docente_id != user.id:
            return Response(
                {"detail": "No autorizado para resolver esta alerta."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ResolveAcademicAlertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        alert.status = "RESOLVED"
        alert.resolved_by = user
        alert.resolution_notes = serializer.validated_data.get("resolution_notes", "")
        alert.resolved_at = timezone.now()
        alert.save()

        return Response(
            AcademicAlertSerializer(alert).data,
            status=status.HTTP_200_OK,
        )


class StudentAcademicSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role != "STUDENT":
            return Response(
                {"detail": "No autorizado"},
                status=status.HTTP_403_FORBIDDEN,
            )

        period = request.query_params.get("period")
        if not period:
            return Response(
                {"detail": "Debes enviar el periodo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        course = user.cursos.first()
        if not course:
            return Response(
                {"detail": "El estudiante no tiene curso asignado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        avg_value, total_assignments, total_graded = calculate_student_average_for_period(
            user, course, int(period)
        )
        total_absences = calculate_student_absences_for_period(user, course, int(period))
        missing_assignments = calculate_missing_assignments_for_period(user, course, int(period))

        return Response(
            {
                "student": {
                    "id": user.id,
                    "nombre": f"{user.first_name} {user.last_name}".strip(),
                },
                "course": {
                    "id": course.id,
                    "nombre": course.nombre,
                },
                "period": int(period),
                "summary": {
                    "average": avg_value,
                    "absences": total_absences,
                    "missing_assignments": len(missing_assignments),
                    "total_assignments": total_assignments,
                    "graded_assignments": total_graded,
                },
            },
            status=status.HTTP_200_OK,
        )
