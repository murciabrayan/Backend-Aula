import base64
from dataclasses import dataclass
from email.mime.image import MIMEImage
from pathlib import Path

import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


LOGO_CID = "gimnasio-los-cerros-logo"
LOGO_PATH = Path(__file__).resolve().parents[2] / "frontend" / "src" / "assets" / "logo.png"
RESEND_API_URL = "https://api.resend.com/emails"
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def _load_logo_data_uri():
    if not LOGO_PATH.exists():
        return None

    encoded = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    suffix = LOGO_PATH.suffix.lower().lstrip(".") or "png"
    mime_type = f"image/{'jpeg' if suffix == 'jpg' else suffix}"
    return f"data:{mime_type};base64,{encoded}"


@dataclass
class RenderedEmail:
    subject: str
    to: list[str]
    html_message: str
    text_message: str
    from_email: str

    def send(self):
        brevo_api_key = getattr(settings, "BREVO_API_KEY", "").strip()
        resend_api_key = getattr(settings, "RESEND_API_KEY", "").strip()

        if brevo_api_key:
            sender_value = getattr(settings, "BREVO_FROM_EMAIL", self.from_email).strip()
            sender_email = sender_value
            sender_name = None
            if "<" in sender_value and ">" in sender_value:
                sender_name = sender_value.split("<", 1)[0].strip().strip('"')
                sender_email = sender_value.split("<", 1)[1].split(">", 1)[0].strip()

            payload = {
                "sender": {
                    "email": sender_email,
                },
                "to": [{"email": email} for email in self.to],
                "subject": self.subject,
                "htmlContent": self.html_message,
                "textContent": self.text_message,
            }
            if sender_name:
                payload["sender"]["name"] = sender_name

            response = requests.post(
                BREVO_API_URL,
                headers={
                    "api-key": brevo_api_key,
                    "Content-Type": "application/json",
                    "accept": "application/json",
                },
                json=payload,
                timeout=getattr(settings, "EMAIL_TIMEOUT", 10),
            )
            if response.status_code >= 400:
                raise RuntimeError(f"Brevo {response.status_code}: {response.text}")
            return 1

        if resend_api_key:
            payload = {
                "from": getattr(settings, "RESEND_FROM_EMAIL", self.from_email),
                "to": self.to,
                "subject": self.subject,
                "html": self.html_message,
                "text": self.text_message,
            }
            response = requests.post(
                RESEND_API_URL,
                headers={
                    "Authorization": f"Bearer {resend_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=getattr(settings, "EMAIL_TIMEOUT", 10),
            )
            if response.status_code >= 400:
                raise RuntimeError(f"Resend {response.status_code}: {response.text}")
            return 1

        email_message = EmailMultiAlternatives(
            subject=self.subject,
            body=self.text_message,
            from_email=self.from_email,
            to=self.to,
        )
        email_message.attach_alternative(self.html_message, "text/html")

        if LOGO_PATH.exists():
            with LOGO_PATH.open("rb") as image_file:
                logo = MIMEImage(image_file.read())
            logo.add_header("Content-ID", f"<{LOGO_CID}>")
            logo.add_header("Content-Disposition", "inline", filename=LOGO_PATH.name)
            email_message.attach(logo)

        return email_message.send()


def build_html_email(*, subject, to, template_name, context, from_email=None):
    html_context = {
        **context,
        "logo_cid": LOGO_CID,
        "logo_src": _load_logo_data_uri(),
    }
    html_message = render_to_string(template_name, html_context)
    text_message = strip_tags(html_message)

    return RenderedEmail(
        subject=subject,
        to=to,
        html_message=html_message,
        text_message=text_message,
        from_email=from_email or settings.DEFAULT_FROM_EMAIL,
    )
