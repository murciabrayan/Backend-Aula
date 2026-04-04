from django.core.exceptions import PermissionDenied
from django.db import transaction
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from notifications.models import Notification

from .models import Assignment, Submission
from .serializers import (
    AssignmentSerializer,
    DirectActivityCreateSerializer,
    SubmissionSerializer,
)


class AssignmentViewSet(viewsets.ModelViewSet):
    queryset = Assignment.objects.all()
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated()]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        user = self.request.user
        queryset = Assignment.objects.all()

        course_id = self.request.query_params.get("course")
        if course_id:
            queryset = queryset.filter(materia__curso_id=course_id)

        subject_id = self.request.query_params.get("subject")
        if subject_id:
            queryset = queryset.filter(materia_id=subject_id)

        periodo = self.request.query_params.get("periodo")
        if periodo:
            queryset = queryset.filter(periodo=periodo)

        requires_submission = self.request.query_params.get("requires_submission")
        if requires_submission is not None:
            queryset = queryset.filter(
                requires_submission=requires_submission.lower() in ["1", "true", "yes"]
            )

        if user.role == "TEACHER":
            return queryset.filter(materia__curso__docente=user)

        if user.role == "STUDENT":
            return queryset.filter(materia__curso__estudiantes=user)

        return Assignment.objects.none()

    def _notify_new_assignment(self, assignment):
        students = list(
            assignment.materia.curso.estudiantes.filter(role="STUDENT", is_active=True)
        )
        if not students:
            return

        Notification.objects.bulk_create(
            [
                Notification(
                    usuario=student,
                    titulo=f"Nueva tarea en {assignment.materia.nombre}",
                    mensaje=(
                        f"Se publicó la tarea '{assignment.titulo}' para la materia "
                        f"{assignment.materia.nombre} del curso {assignment.materia.curso.nombre}."
                    ),
                )
                for student in students
            ]
        )

    def _sync_direct_activity_grades(self, assignment, grades, enrolled_students):
        existing_submissions = {
            submission.estudiante_id: submission
            for submission in Submission.objects.filter(tarea=assignment)
        }
        grade_student_ids = set()
        notifications_to_create = []

        for entry in grades:
            student = enrolled_students.get(entry["student_id"])
            if not student:
                raise PermissionDenied("Uno de los estudiantes no pertenece al curso seleccionado.")

            grade_student_ids.add(student.id)
            feedback = entry.get("retroalimentacion") or ""
            submission = existing_submissions.get(student.id)

            if submission:
                submission.calificacion = entry["calificacion"]
                submission.retroalimentacion = feedback
                submission.save(update_fields=["calificacion", "retroalimentacion"])
            else:
                Submission.objects.create(
                    tarea=assignment,
                    estudiante=student,
                    calificacion=entry["calificacion"],
                    retroalimentacion=feedback,
                )

            notifications_to_create.append(
                Notification(
                    usuario=student,
                    titulo=f"Nueva calificación en {assignment.materia.nombre}",
                    mensaje=(
                        f"Se registró la actividad '{assignment.titulo}' con una nota de "
                        f"{entry['calificacion']} en la materia {assignment.materia.nombre}."
                    ),
                )
            )

        missing_student_ids = set(existing_submissions) - grade_student_ids
        if missing_student_ids:
            Submission.objects.filter(
                tarea=assignment,
                estudiante_id__in=missing_student_ids,
            ).delete()

        if notifications_to_create:
            Notification.objects.bulk_create(notifications_to_create)

    def perform_create(self, serializer):
        user = self.request.user
        materia = serializer.validated_data.get("materia")

        if user.role != "TEACHER":
            raise PermissionDenied("Solo los docentes pueden crear tareas.")

        if materia.curso.docente != user:
            raise PermissionDenied(
                "Solo el docente asignado al curso puede crear tareas en esta materia."
            )

        assignment = serializer.save()
        self._notify_new_assignment(assignment)

    def perform_update(self, serializer):
        user = self.request.user
        materia = serializer.validated_data.get("materia", serializer.instance.materia)

        if user.role != "TEACHER":
            raise PermissionDenied("Solo los docentes pueden editar tareas.")

        if materia.curso.docente != user:
            raise PermissionDenied(
                "Solo el docente asignado al curso puede editar tareas en esta materia."
            )

        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user

        if user.role != "TEACHER":
            raise PermissionDenied("Solo los docentes pueden eliminar tareas.")

        if instance.materia.curso.docente != user:
            raise PermissionDenied(
                "Solo el docente asignado al curso puede eliminar tareas en esta materia."
            )

        instance.delete()

    @action(detail=False, methods=["post"], url_path="direct-activity")
    @transaction.atomic
    def direct_activity(self, request):
        user = request.user
        if user.role != "TEACHER":
            return Response(
                {"detail": "Solo los docentes pueden registrar actividades evaluables."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = DirectActivityCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        materia = serializer.validated_data["materia"]
        if materia.curso.docente_id != user.id:
            return Response(
                {
                    "detail": "Solo el docente asignado al curso puede registrar actividades en esta materia."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        assignment = Assignment.objects.create(
            materia=materia,
            titulo=serializer.validated_data["titulo"],
            descripcion=serializer.validated_data.get("descripcion", ""),
            fecha_entrega=serializer.validated_data["fecha_entrega"],
            periodo=int(serializer.validated_data["periodo"]),
            requires_submission=False,
        )

        enrolled_students = {
            student.id: student
            for student in materia.curso.estudiantes.filter(role="STUDENT", is_active=True)
        }
        self._sync_direct_activity_grades(
            assignment,
            serializer.validated_data.get("grades", []),
            enrolled_students,
        )

        return Response(AssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="direct-activity-update")
    @transaction.atomic
    def direct_activity_update(self, request, pk=None):
        user = request.user
        assignment = self.get_object()

        if user.role != "TEACHER":
            return Response(
                {"detail": "Solo los docentes pueden editar actividades evaluables."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if assignment.requires_submission:
            return Response(
                {"detail": "Solo las actividades sin entrega pueden editarse desde este flujo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if assignment.materia.curso.docente_id != user.id:
            return Response(
                {"detail": "Solo el docente asignado al curso puede editar esta actividad."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = DirectActivityCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        materia = serializer.validated_data["materia"]
        if materia.id != assignment.materia_id:
            return Response(
                {"detail": "La materia de la actividad evaluable no puede cambiarse."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        assignment.titulo = serializer.validated_data["titulo"]
        assignment.descripcion = serializer.validated_data.get("descripcion", "")
        assignment.fecha_entrega = serializer.validated_data["fecha_entrega"]
        assignment.periodo = int(serializer.validated_data["periodo"])
        assignment.save(update_fields=["titulo", "descripcion", "fecha_entrega", "periodo"])

        enrolled_students = {
            student.id: student
            for student in materia.curso.estudiantes.filter(role="STUDENT", is_active=True)
        }
        self._sync_direct_activity_grades(
            assignment,
            serializer.validated_data.get("grades", []),
            enrolled_students,
        )

        return Response(AssignmentSerializer(assignment).data, status=status.HTTP_200_OK)


class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy", "calificar"]:
            return [permissions.IsAuthenticated()]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        user = self.request.user
        queryset = Submission.objects.all()

        assignment_id = self.request.query_params.get("assignment")
        if assignment_id:
            queryset = queryset.filter(tarea_id=assignment_id)

        if user.role == "STUDENT":
            return queryset.filter(estudiante=user)

        if user.role == "TEACHER":
            return queryset.filter(tarea__materia__curso__docente=user)

        return queryset.none()

    def perform_create(self, serializer):
        user = self.request.user

        if user.role != "STUDENT":
            raise PermissionDenied("Solo los estudiantes pueden subir entregas.")

        serializer.save(estudiante=user)

    def perform_update(self, serializer):
        user = self.request.user
        entrega = serializer.instance

        if user.role != "STUDENT" or entrega.estudiante_id != user.id:
            raise PermissionDenied("Solo el estudiante propietario puede editar su entrega.")

        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user

        if user.role != "STUDENT" or instance.estudiante_id != user.id:
            raise PermissionDenied("Solo el estudiante propietario puede eliminar su entrega.")

        instance.delete()

    @action(detail=True, methods=["post"])
    def calificar(self, request, pk=None):
        entrega = self.get_object()
        user = request.user

        if entrega.tarea.materia.curso.docente != user:
            return Response({"detail": "No autorizado"}, status=status.HTTP_403_FORBIDDEN)

        calificacion = request.data.get("calificacion")
        retroalimentacion = request.data.get("retroalimentacion", "")

        try:
            calificacion = float(calificacion)
        except (TypeError, ValueError):
            return Response(
                {"detail": "La calificación debe ser un número"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (0.0 <= calificacion <= 5.0):
            return Response(
                {"detail": "La calificación debe estar entre 0.0 y 5.0"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        entrega.calificacion = round(calificacion, 2)
        entrega.retroalimentacion = retroalimentacion
        entrega.save()

        Notification.objects.create(
            usuario=entrega.estudiante,
            titulo="Nueva calificación",
            mensaje=(
                f"Tu tarea '{entrega.tarea.titulo}' fue calificada con {entrega.calificacion}."
            ),
        )

        return Response(
            {"detail": "Calificación guardada correctamente."},
            status=status.HTTP_200_OK,
        )
