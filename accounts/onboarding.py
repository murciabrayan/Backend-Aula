import secrets
import string

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


SPECIAL_CHARS = "!@#$%&*_-"


def generate_temporary_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits + SPECIAL_CHARS

    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(char.isupper() for char in password)
            and any(char.islower() for char in password)
            and any(char.isdigit() for char in password)
            and any(char in SPECIAL_CHARS for char in password)
        ):
            return password


def send_welcome_credentials_email(user, temporary_password: str):
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173").rstrip("/")
    login_url = f"{frontend_url}/plataforma"

    subject = "Tu cuenta institucional fue creada"
    context = {
        "first_name": user.first_name or "Comunidad Gimnasio Los Cerros",
        "login_url": login_url,
        "email": user.email,
        "temporary_password": temporary_password,
        "support_email": settings.DEFAULT_FROM_EMAIL,
    }
    html_message = render_to_string("accounts/emails/welcome_credentials.html", context)
    text_message = strip_tags(html_message)

    email_message = EmailMultiAlternatives(
        subject=subject,
        body=text_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email_message.attach_alternative(html_message, "text/html")
    email_message.send()
