from django.core.files.base import ContentFile
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.decorators import api_view, parser_classes, permission_classes, throttle_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from accounts.models import UserDocument
from courses.models import Course
from notifications.models import Notification

from .models import PermissionLetter, PermissionLetterRecipient
from .pdf_utils import PERMISSION_DOCUMENT_CATEGORY, build_permission_response_pdf
from .serializers import PermissionLetterSerializer, StudentPermissionLetterSerializer


def _is_admin(user):
    return user.is_authenticated and user.role == "ADMIN"


def _get_student_signature_bytes(student):
    if not student.signature_image:
        return None
    try:
        student.signature_image.open("rb")
        return student.signature_image.read()
    finally:
        try:
            student.signature_image.close()
        except Exception:
            pass


@api_view(["GET", "POST"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@throttle_classes([])
def permission_letters_collection(request):
    if not _is_admin(request.user):
        return Response({"detail": "No autorizado."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        queryset = PermissionLetter.objects.select_related("course").prefetch_related("recipients__student")
        serializer = PermissionLetterSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)

    serializer = PermissionLetterSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)

    course = get_object_or_404(Course, pk=serializer.validated_data["course"].id)
    students = list(course.estudiantes.filter(role="STUDENT"))
    if not students:
        return Response(
            {"error": "El curso seleccionado no tiene estudiantes asignados."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        permission_letter = serializer.save(created_by=request.user)
        recipients = [
            PermissionLetterRecipient(permission_letter=permission_letter, student=student)
            for student in students
        ]
        PermissionLetterRecipient.objects.bulk_create(recipients)
        Notification.objects.bulk_create(
            [
                Notification(
                    usuario=student,
                    titulo=f"Nuevo permiso: {permission_letter.title}",
                    mensaje=(
                        f"Tienes un permiso pendiente del curso {course.nombre}. "
                        "Ingresa al modulo de permisos para que tu acudiente lo revise y lo responda."
                    ),
                )
                for student in students
            ]
        )

    response_serializer = PermissionLetterSerializer(permission_letter, context={"request": request})
    return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([])
def permission_letter_detail(request, pk):
    if not _is_admin(request.user):
        return Response({"detail": "No autorizado."}, status=status.HTTP_403_FORBIDDEN)

    permission_letter = get_object_or_404(
        PermissionLetter.objects.select_related("course").prefetch_related("recipients__student"),
        pk=pk,
    )
    serializer = PermissionLetterSerializer(permission_letter, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([])
def my_permission_letters(request):
    recipients = (
        PermissionLetterRecipient.objects.select_related("permission_letter__course")
        .filter(student=request.user)
        .order_by("-permission_letter__created_at")
    )
    serializer = StudentPermissionLetterSerializer(recipients, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([])
def respond_permission_letter(request, recipient_id):
    recipient = get_object_or_404(
        PermissionLetterRecipient.objects.select_related("permission_letter__course", "student"),
        pk=recipient_id,
        student=request.user,
    )

    if recipient.status != PermissionLetterRecipient.STATUS_PENDING:
        return Response(
            {"error": "Este permiso ya fue respondido anteriormente."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    action = str(request.data.get("action", "")).strip().upper()
    if action not in {"ACCEPT", "REJECT"}:
        return Response(
            {"error": "Debes indicar si aceptas o rechazas el permiso."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if action == "ACCEPT" and not request.user.has_saved_signature:
        return Response(
            {"error": "Primero debes registrar la firma del acudiente en el perfil para poder aceptar permisos."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    status_value = (
        PermissionLetterRecipient.STATUS_ACCEPTED
        if action == "ACCEPT"
        else PermissionLetterRecipient.STATUS_REJECTED
    )
    recipient.status = status_value
    recipient.responded_at = timezone.now()

    signature_bytes = _get_student_signature_bytes(request.user) if action == "ACCEPT" else None
    filename, pdf_bytes = build_permission_response_pdf(
        recipient=recipient,
        status=status_value,
        signature_bytes=signature_bytes,
    )

    if recipient.signed_document:
        recipient.signed_document.delete(save=False)
    recipient.signed_document.save(filename, ContentFile(pdf_bytes), save=False)

    document_title = f"{recipient.permission_letter.title} - {'Aceptado' if action == 'ACCEPT' else 'Rechazado'}"
    user_document = recipient.user_document or request.user.documents.filter(
        category=PERMISSION_DOCUMENT_CATEGORY,
        title=document_title,
    ).first()
    if user_document and user_document.file:
        user_document.file.delete(save=False)

    if user_document is None:
        user_document = UserDocument(user=request.user)

    user_document.title = document_title
    user_document.category = PERMISSION_DOCUMENT_CATEGORY
    user_document.file.save(filename, ContentFile(pdf_bytes), save=True)

    recipient.user_document = user_document
    recipient.save(update_fields=["status", "responded_at", "signed_document", "user_document"])

    if recipient.permission_letter.created_by:
        student_label = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.email
        Notification.objects.create(
            usuario=recipient.permission_letter.created_by,
            titulo=f"Respuesta de permiso: {recipient.permission_letter.title}",
            mensaje=(
                f"El acudiente del estudiante {student_label} ha "
                f"{'aceptado' if action == 'ACCEPT' else 'rechazado'} el permiso enviado."
            ),
        )

    serializer = StudentPermissionLetterSerializer(recipient, context={"request": request})
    return Response(
        {
            "message": "La respuesta del permiso fue registrada correctamente.",
            "item": serializer.data,
        },
        status=status.HTTP_200_OK,
    )
