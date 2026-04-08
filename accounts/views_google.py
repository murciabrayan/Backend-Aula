import logging

from django.conf import settings
from google.auth.transport import requests
from google.oauth2 import id_token
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AnonRateThrottle])
def google_login(request):
    token = request.data.get("token")

    if not token:
        return Response({"error": "Token requerido"}, status=400)

    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )

        email = idinfo.get("email")
        email_verified = idinfo.get("email_verified", False)
        full_name = idinfo.get("name", "")

        if not email:
            return Response({"error": "Email no disponible"}, status=400)
        
        if not email_verified:
            return Response(
                {"error": "La cuenta de Google debe tener el correo verificado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        first_name = ""
        last_name = ""
        if full_name:
            parts = full_name.split(" ", 1)
            first_name = parts[0]
            if len(parts) > 1:
                last_name = parts[1]

        try:
            user = User.objects.get(email__iexact=email.strip())
        except User.DoesNotExist:
            return Response(
                {
                    "error": (
                        "No existe una cuenta institucional registrada con este correo. "
                        "Solicita al administrador la creación del usuario primero."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user.is_active:
            return Response(
                {"error": "Tu cuenta institucional está inactiva."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if user.must_change_password:
            return Response(
                {
                    "error": (
                        "Debes ingresar primero con la contraseña inicial enviada al correo "
                        "y crear tu contraseña personal antes de usar Google."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        updated_fields = []
        if not user.google_account:
            user.google_account = True
            updated_fields.append("google_account")
        if first_name and not user.first_name:
            user.first_name = first_name
            updated_fields.append("first_name")
        if last_name and not user.last_name:
            user.last_name = last_name
            updated_fields.append("last_name")

        if updated_fields:
            user.save(update_fields=updated_fields)

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "cedula": user.cedula,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "direccion": user.direccion,
                    "rh": user.rh,
                    "role": user.role,
                    "must_change_password": user.must_change_password,
                    "has_accepted_data_policy": user.has_accepted_data_policy,
                    "data_policy_accepted_at": user.data_policy_accepted_at,
                    "has_saved_signature": user.has_saved_signature,
                    "photo_url": user.get_photo_url(request),
                    "avatar_url": user.get_avatar_url(request),
                    "avatar_style": user.avatar_style,
                    "avatar_seed": user.get_avatar_seed(),
                },
            }
        )

    except ValueError:
        return Response({"error": "Token invalido"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        logger.exception("Error inesperado en login con Google")
        return Response(
            {"error": "Error interno al iniciar sesion con Google."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
