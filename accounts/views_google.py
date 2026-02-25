from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status

from .models import User


@api_view(["POST"])
def google_login(request):
    token = request.data.get("token")

    if not token:
        return Response({"error": "Token requerido"}, status=400)

    try:
        # ✅ Verificar token con Google
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )

        email = idinfo.get("email")
        full_name = idinfo.get("name", "")

        if not email:
            return Response({"error": "Email no disponible"}, status=400)

        # 🔹 Separar nombre y apellido
        first_name = ""
        last_name = ""

        if full_name:
            parts = full_name.split(" ", 1)
            first_name = parts[0]
            if len(parts) > 1:
                last_name = parts[1]

        # ✅ BUSCAR O CREAR USUARIO (SIN DUPLICAR)
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "cedula": f"google_{email}",  # 👈 necesario porque es obligatorio
                "first_name": first_name,
                "last_name": last_name,
                "role": "STUDENT",  # 👈 AJUSTA si quieres otra lógica
                "is_active": True,
            },
        )

        # 🎟️ Generar JWT
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role,
                },
            }
        )

    except ValueError:
        return Response({"error": "Token inválido"}, status=status.HTTP_400_BAD_REQUEST)