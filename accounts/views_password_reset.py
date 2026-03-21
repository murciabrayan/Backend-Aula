import json

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.csrf import csrf_exempt

from .password_rules import validate_password_strength

User = get_user_model()


@csrf_exempt
def forgot_password(request):
    if request.method != "POST":
        return JsonResponse({"error": "Metodo no permitido"}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get("email")

        if not email:
            return JsonResponse({"error": "El correo es obligatorio"}, status=400)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({"error": "No existe un usuario con ese correo"}, status=404)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173").rstrip("/")
        reset_link = f"{frontend_url}/reset-password/{uid}/{token}"

        subject = "Restablecimiento de contrasena - Gimnasio Los Cerros"
        context = {
            "first_name": user.first_name or "Comunidad Gimnasio Los Cerros",
            "reset_link": reset_link,
            "support_email": settings.DEFAULT_FROM_EMAIL,
        }
        html_message = render_to_string("accounts/emails/password_reset.html", context)
        text_message = strip_tags(html_message)

        email_message = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email_message.attach_alternative(html_message, "text/html")
        email_message.send()

        return JsonResponse(
            {"message": "Correo de restablecimiento enviado correctamente."},
            status=200,
        )
    except Exception as exc:
        print("Error en forgot_password:", exc)
        return JsonResponse({"error": "Error interno del servidor"}, status=500)


@csrf_exempt
def reset_password(request, uidb64, token):
    if request.method != "POST":
        return JsonResponse({"error": "Metodo no permitido"}, status=405)

    try:
        data = json.loads(request.body)
        new_password = data.get("password")

        if not new_password:
            return JsonResponse({"error": "La nueva contrasena es obligatoria"}, status=400)

        try:
            validate_password_strength(new_password)
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400)

        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)

        if not default_token_generator.check_token(user, token):
            return JsonResponse({"error": "Token invalido o expirado"}, status=400)

        user.set_password(new_password)
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password"])

        return JsonResponse({"message": "Contrasena restablecida exitosamente."}, status=200)

    except Exception as exc:
        print("Error en reset_password:", exc)
        return JsonResponse({"error": "Error interno del servidor"}, status=500)
