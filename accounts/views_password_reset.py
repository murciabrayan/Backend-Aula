from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json

User = get_user_model()


# Enviar correo de restablecimiento

@csrf_exempt
def forgot_password(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get("email")

        if not email:
            return JsonResponse({"error": "El correo es obligatorio"}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({"error": "No existe un usuario con ese correo"}, status=404)

        # Crear token de recuperación
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = f"http://localhost:5173/reset-password/{uid}/{token}/"

        # Enviar correo
        subject = "Restablecimiento de contraseña - Gimnasio Los Cerros"
        message = (
            f"Hola {user.first_name or ''},\n\n"
            f"Has solicitado restablecer tu contraseña.\n"
            f"Usa el siguiente enlace para hacerlo:\n\n{reset_link}\n\n"
            "Si no solicitaste este cambio, ignora este mensaje."
        )

        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

        return JsonResponse({"message": "Correo de restablecimiento enviado correctamente."}, status=200)

    except Exception as e:
        print("Error en forgot_password:", e)
        return JsonResponse({"error": "Error interno del servidor"}, status=500)


# -----------------------------
# Restablecer contraseña
# -----------------------------
@csrf_exempt
def reset_password(request, uidb64, token):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body)
        new_password = data.get("password")

        if not new_password:
            return JsonResponse({"error": "La nueva contraseña es obligatoria"}, status=400)

        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)

        # Verificar token
        if not default_token_generator.check_token(user, token):
            return JsonResponse({"error": "Token inválido o expirado"}, status=400)

        user.set_password(new_password)
        user.save()

        return JsonResponse({"message": "Contraseña restablecida exitosamente."}, status=200)

    except Exception as e:
        print("Error en reset_password:", e)
        return JsonResponse({"error": "Error interno del servidor"}, status=500)
