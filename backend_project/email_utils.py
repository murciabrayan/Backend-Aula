from email.mime.image import MIMEImage
from pathlib import Path

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


LOGO_CID = "gimnasio-los-cerros-logo"
LOGO_PATH = Path(__file__).resolve().parents[2] / "frontend" / "src" / "assets" / "logo.png"


def build_html_email(*, subject, to, template_name, context, from_email=None):
    html_context = {
        **context,
        "logo_cid": LOGO_CID,
    }
    html_message = render_to_string(template_name, html_context)
    text_message = strip_tags(html_message)

    email_message = EmailMultiAlternatives(
        subject=subject,
        body=text_message,
        from_email=from_email or settings.DEFAULT_FROM_EMAIL,
        to=to,
    )
    email_message.attach_alternative(html_message, "text/html")

    if LOGO_PATH.exists():
        with LOGO_PATH.open("rb") as image_file:
            logo = MIMEImage(image_file.read())
        logo.add_header("Content-ID", f"<{LOGO_CID}>")
        logo.add_header("Content-Disposition", "inline", filename=LOGO_PATH.name)
        email_message.attach(logo)

    return email_message
