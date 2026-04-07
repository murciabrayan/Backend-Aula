from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from .models import StudentProfile, UserDocument


DATA_POLICY_CATEGORY = "Tratamiento de datos personales"
DATA_POLICY_TITLE = "Autorizacion de tratamiento de datos personales"
DATA_POLICY_VERSION = "2026.1"
DATA_POLICY_LETTERHEAD_CANDIDATES = [
    Path(settings.BASE_DIR) / "assets" / "boletin" / "membrete_tratamiento_datos.png",
    Path(settings.BASE_DIR) / "assets" / "membrete tratamiento datos.png",
]

POLICY_PARAGRAPHS = [
    (
        "Yo, en calidad de titular o representante legal, autorizo de manera previa, "
        "expresa e informada al Gimnasio Los Cerros para recolectar, almacenar, usar, "
        "actualizar y custodiar los datos personales suministrados dentro de la plataforma institucional."
    ),
    (
        "Esta autorizacion comprende el tratamiento de informacion academica, administrativa, "
        "de contacto y soporte documental necesaria para la prestacion del servicio educativo, "
        "la comunicacion con la comunidad y el cumplimiento de obligaciones legales."
    ),
    (
        "Declaro que conozco que podre ejercer los derechos de consulta, actualizacion, "
        "rectificacion y supresion de datos personales a traves de los canales institucionales."
    ),
]


def get_data_policy_signer_for_user(user):
    if user.role == "STUDENT":
        student_profile = StudentProfile.objects.filter(user=user).first()
        signer_name = (student_profile.acudiente_nombre if student_profile else "") or ""
        signer_document = (student_profile.acudiente_cedula if student_profile else "") or ""
        signer_role = "Acudiente"
    else:
        signer_name = f"{user.first_name} {user.last_name}".strip() or user.email
        signer_document = user.cedula or ""
        signer_role = "Titular"

    return {
        "name": signer_name.strip(),
        "document": signer_document.strip(),
        "role": signer_role,
    }


def get_data_policy_payload_for_user(user):
    signer = get_data_policy_signer_for_user(user)
    return {
        "version": DATA_POLICY_VERSION,
        "title": DATA_POLICY_TITLE,
        "institution_name": "GIMNASIO LOS CERROS",
        "paragraphs": POLICY_PARAGRAPHS,
        "signer_name": signer["name"],
        "signer_document": signer["document"],
        "signer_role": signer["role"],
        "accepted": user.has_accepted_data_policy,
        "accepted_at": user.data_policy_accepted_at,
    }


def validate_signer_data(user):
    signer = get_data_policy_signer_for_user(user)
    if not signer["name"] or not signer["document"]:
        if user.role == "STUDENT":
            raise ValueError(
                "El estudiante no tiene completos los datos del acudiente para firmar la autorizacion."
            )
        raise ValueError("El usuario no tiene completos sus datos para firmar la autorizacion.")
    return signer


def build_data_policy_pdf(*, user, signer_name, signer_document, signature_bytes):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4

    left = 2 * cm
    right = page_width - 2 * cm
    top = page_height - 2 * cm
    current_y = top

    letterhead_path = next(
        (path for path in DATA_POLICY_LETTERHEAD_CANDIDATES if path.exists()),
        None,
    )

    if letterhead_path:
        pdf.drawImage(
            str(letterhead_path),
            0,
            0,
            width=page_width,
            height=page_height,
            preserveAspectRatio=False,
            mask="auto",
        )

    logo_path = Path(settings.BASE_DIR) / "assets" / "boletin" / "logo_izquierdo.png"
    if logo_path.exists() and not letterhead_path:
        pdf.drawImage(str(logo_path), left, current_y - 2.1 * cm, width=1.9 * cm, height=1.9 * cm, preserveAspectRatio=True, mask="auto")

    if letterhead_path:
        header_center_x = page_width / 2
        title_y = page_height - 5.0 * cm
        subtitle_y = title_y - 0.65 * cm
        version_y = subtitle_y - 0.5 * cm

        pdf.setFillColor(colors.black)
        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawCentredString(header_center_x, title_y, "Autorizacion para el tratamiento de datos personales")
        pdf.setFont("Helvetica", 9.5)
        pdf.drawCentredString(header_center_x, subtitle_y, "Declaracion institucional firmada electronicamente")
        pdf.drawCentredString(header_center_x, version_y, f"Version: {DATA_POLICY_VERSION}")
        current_y = version_y - 1.2 * cm
    else:
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(left + 2.3 * cm, current_y - 0.1 * cm, "GIMNASIO LOS CERROS")
        pdf.setFont("Helvetica", 9.5)
        pdf.drawString(left + 2.3 * cm, current_y - 0.7 * cm, "Autorizacion para el tratamiento de datos personales")
        pdf.drawString(left + 2.3 * cm, current_y - 1.2 * cm, f"Version: {DATA_POLICY_VERSION}")
        current_y -= 3.1 * cm

    pdf.setStrokeColor(colors.black)
    pdf.line(left, current_y, right, current_y)
    current_y -= 0.8 * cm

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(left, current_y, "Declaracion de autorizacion")
    current_y -= 0.8 * cm

    pdf.setFont("Helvetica", 10)
    for paragraph in POLICY_PARAGRAPHS:
        text_object = pdf.beginText(left, current_y)
        text_object.setLeading(14)
        for line in paragraph.split("\n"):
            for wrapped_line in _wrap_text(pdf, line):
                text_object.textLine(wrapped_line)
                current_y -= 0.5 * cm
        pdf.drawText(text_object)
        current_y -= 0.2 * cm

    current_y -= 0.3 * cm
    pdf.setFont("Helvetica-Bold", 10.5)
    pdf.drawString(left, current_y, "Datos del firmante")
    current_y -= 0.7 * cm

    field_rows = [
        ("Nombre", signer_name),
        ("Documento", signer_document),
        ("Calidad", "Acudiente" if user.role == "STUDENT" else "Titular"),
        ("Usuario asociado", f"{user.first_name} {user.last_name}".strip() or user.email),
        ("Fecha de aceptacion", timezone.localtime().strftime("%Y-%m-%d %H:%M")),
    ]

    pdf.setFont("Helvetica", 10)
    for label, value in field_rows:
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(left, current_y, f"{label}:")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(left + 3.7 * cm, current_y, value)
        current_y -= 0.6 * cm

    current_y -= 0.4 * cm
    pdf.setFont("Helvetica-Bold", 10.5)
    pdf.drawString(left, current_y, "Firma")
    current_y -= 0.3 * cm
    pdf.rect(left, current_y - 3.4 * cm, 8.5 * cm, 3.4 * cm)

    signature_reader = ImageReader(BytesIO(signature_bytes))
    pdf.drawImage(
        signature_reader,
        left + 0.2 * cm,
        current_y - 3.2 * cm,
        width=8.1 * cm,
        height=3.0 * cm,
        preserveAspectRatio=True,
        mask="auto",
    )

    pdf.setFont("Helvetica", 8.5)
    pdf.drawString(left, current_y - 3.8 * cm, "La firma corresponde a la aceptacion electronica del tratamiento de datos.")

    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    full_name = f"{user.first_name} {user.last_name}".strip() or user.email
    safe_name = (
        full_name.lower()
        .replace(" ", "-")
        .replace(".", "")
        .replace("@", "-")
    )
    filename = f"tratamiento-datos-{safe_name}.pdf"
    return filename, buffer.getvalue()


def _wrap_text(pdf, text):
    words = text.split()
    if not words:
        return [""]

    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if pdf.stringWidth(candidate, "Helvetica", 10) <= 16.5 * cm:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def store_signed_data_policy_document(*, user, signer_name, signer_document, signature_file):
    signature_bytes = signature_file.read()
    filename, pdf_bytes = build_data_policy_pdf(
        user=user,
        signer_name=signer_name,
        signer_document=signer_document,
        signature_bytes=signature_bytes,
    )

    document = user.documents.filter(category=DATA_POLICY_CATEGORY).first()
    if document:
        if document.file:
            document.file.delete(save=False)
        document.title = DATA_POLICY_TITLE
        document.category = DATA_POLICY_CATEGORY
        document.file.save(filename, ContentFile(pdf_bytes), save=True)
        return document

    return UserDocument.objects.create(
        user=user,
        title=DATA_POLICY_TITLE,
        category=DATA_POLICY_CATEGORY,
        file=ContentFile(pdf_bytes, name=filename),
    )


def save_user_signature_image(*, user, signature_file):
    signature_bytes = signature_file.read()
    extension = Path(signature_file.name or "").suffix.lower() or ".png"
    filename = f"firma-{user.id}{extension}"

    if user.signature_image:
        user.signature_image.delete(save=False)

    user.signature_image.save(filename, ContentFile(signature_bytes), save=False)
    user.signature_updated_at = timezone.now()
    user.save(update_fields=["signature_image", "signature_updated_at"])
