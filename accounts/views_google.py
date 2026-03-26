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
        full_name = idinfo.get("name", "")

        if not email:
            return Response({"error": "Email no disponible"}, status=400)

        first_name = ""
        last_name = ""
        if full_name:
            parts = full_name.split(" ", 1)
            first_name = parts[0]
            if len(parts) > 1:
                last_name = parts[1]

        user, _created = User.objects.get_or_create(
            email=email,
            defaults={
                "cedula": f"google_{email}",
                "first_name": first_name,
                "last_name": last_name,
                "role": "STUDENT",
                "is_active": True,
                "must_change_password": False,
            },
        )

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role,
                    "must_change_password": user.must_change_password,
                    "photo_url": user.get_photo_url(request),
                    "avatar_url": user.get_avatar_url(request),
                    "avatar_style": user.avatar_style,
                    "avatar_seed": user.get_avatar_seed(),
                },
            }
        )

    except ValueError:
        return Response({"error": "Token invalido"}, status=status.HTTP_400_BAD_REQUEST)
