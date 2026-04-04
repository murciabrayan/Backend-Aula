import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from backend_project.email_utils import build_html_email

from .password_rules import validate_password_strength

User = get_user_model()

RESET_REQUEST_RESPONSE = {
    "message": "Si el correo existe en la plataforma, enviaremos instrucciones para restablecer la contraseña."
}


def _parse_request_body(request):
    if isinstance(request.data, dict):
        return request.data

    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return {}


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def forgot_password(request):
    data = _parse_request_body(request)
    email = (data.get("email") or "").strip()

    if not email:
        return Response(
            {"error": "El correo es obligatorio."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.filter(email=email).first()

        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173").rstrip("/")
            reset_link = f"{frontend_url}/reset-password/{uid}/{token}"

            subject = "Restablecimiento de contraseña - Gimnasio Los Cerros"
            context = {
                "first_name": user.first_name or "Comunidad Gimnasio Los Cerros",
                "reset_link": reset_link,
                "support_email": settings.DEFAULT_FROM_EMAIL,
            }
            email_message = build_html_email(
                subject=subject,
                to=[user.email],
                template_name="accounts/emails/password_reset.html",
                context=context,
                from_email=settings.DEFAULT_FROM_EMAIL,
            )
            email_message.send()

        return Response(RESET_REQUEST_RESPONSE, status=status.HTTP_200_OK)
    except Exception as exc:
        print("Error en forgot_password:", exc)
        return Response(
            {"error": "Error interno del servidor."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def reset_password(request, uidb64, token):
    data = _parse_request_body(request)
    new_password = data.get("password")

    if not new_password:
        return Response(
            {"error": "La nueva contraseña es obligatoria."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        validate_password_strength(new_password)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if not user or not default_token_generator.check_token(user, token):
        return Response(
            {"error": "Token inválido o expirado."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user.set_password(new_password)
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password"])
        return Response(
            {"message": "Contraseña restablecida exitosamente."},
            status=status.HTTP_200_OK,
        )
    except Exception as exc:
        print("Error en reset_password:", exc)
        return Response(
            {"error": "Error interno del servidor."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
