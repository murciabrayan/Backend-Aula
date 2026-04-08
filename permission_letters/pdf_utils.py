from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from accounts.data_policy import DATA_POLICY_LETTERHEAD_CANDIDATES
from accounts.models import StudentProfile


PERMISSION_DOCUMENT_CATEGORY = "Permisos y autorizaciones"


def build_permission_response_pdf(*, recipient, status, signature_bytes=None):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4

    left = 2 * cm
    right = page_width - 2 * cm
    current_y = page_height - 2 * cm

    letterhead_path = next((path for path in DATA_POLICY_LETTERHEAD_CANDIDATES if path.exists()), None)
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
        current_y = page_height - 5.1 * cm
    else:
        logo_path = Path(settings.BASE_DIR) / "assets" / "boletin" / "logo_izquierdo.png"
        if logo_path.exists():
            pdf.drawImage(
                str(logo_path),
                left,
                current_y - 2.1 * cm,
                width=1.9 * cm,
                height=1.9 * cm,
                preserveAspectRatio=True,
                mask="auto",
            )
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(left + 2.3 * cm, current_y - 0.1 * cm, "GIMNASIO LOS CERROS")
        current_y -= 2.4 * cm

    status_label = "Aceptado" if status == "ACCEPTED" else "Rechazado"
    student_name = f"{recipient.student.first_name} {recipient.student.last_name}".strip() or recipient.student.email
    student_profile = StudentProfile.objects.filter(user=recipient.student).first()
    guardian_name = (student_profile.acudiente_nombre if student_profile else "") or "Acudiente registrado"
    guardian_document = (student_profile.acudiente_cedula if student_profile else "") or "Sin documento registrado"
    letter = recipient.permission_letter

    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawCentredString(page_width / 2, current_y, f"Respuesta de permiso: {status_label}")
    current_y -= 0.8 * cm
    pdf.setFont("Helvetica", 9.5)
    pdf.drawCentredString(page_width / 2, current_y, letter.title)
    current_y -= 0.7 * cm

    pdf.setStrokeColor(colors.black)
    pdf.line(left, current_y, right, current_y)
    current_y -= 1.0 * cm

    pdf.setFont("Helvetica", 10)
    paragraphs = [
        (
            f'El permiso institucional "{letter.title}" correspondiente al curso {letter.course.nombre} '
            f"fue respondido en estado {status_label.lower()} para el estudiante menor de edad "
            f"{student_name}, identificado con documento {recipient.student.cedula}."
        ),
        (
            f"La respuesta fue registrada por el acudiente {guardian_name} identificado con "
            f"documento {guardian_document}, quien actúa como firmante autorizado en "
            "representación del menor dentro de la plataforma institucional."
        ),
        (
            "Esta constancia fue generada automáticamente por la plataforma institucional y "
            "queda almacenada dentro del perfil del estudiante para fines de seguimiento administrativo."
        ),
    ]

    for paragraph in paragraphs:
        text_object = pdf.beginText(left, current_y)
        text_object.setLeading(15)
        for line in _wrap_text(pdf, paragraph, 10):
            text_object.textLine(line)
            current_y -= 0.52 * cm
        pdf.drawText(text_object)
        current_y -= 0.2 * cm

    current_y -= 0.2 * cm
    field_rows = [
        ("Permiso", letter.title),
        ("Curso", letter.course.nombre),
        ("Estudiante", student_name),
        ("Documento del estudiante", recipient.student.cedula),
        ("Acudiente firmante", guardian_name),
        ("Documento del acudiente", guardian_document),
        ("Estado", status_label),
        ("Fecha de respuesta", timezone.localtime(recipient.responded_at or timezone.now()).strftime("%Y-%m-%d %H:%M")),
    ]

    for label, value in field_rows:
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(left, current_y, f"{label}:")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(left + 4.8 * cm, current_y, str(value))
        current_y -= 0.65 * cm

    if status == "ACCEPTED" and signature_bytes:
        current_y -= 0.4 * cm
        pdf.setFont("Helvetica-Bold", 10.5)
        pdf.drawString(left, current_y, "Firma registrada del acudiente")
        current_y -= 0.3 * cm
        pdf.rect(left, current_y - 3.4 * cm, 8.5 * cm, 3.4 * cm)
        pdf.drawImage(
            ImageReader(BytesIO(signature_bytes)),
            left + 0.2 * cm,
            current_y - 3.2 * cm,
            width=8.1 * cm,
            height=3.0 * cm,
            preserveAspectRatio=True,
            mask="auto",
        )
        pdf.setFont("Helvetica", 8.5)
        pdf.drawString(
            left,
            current_y - 3.8 * cm,
            "La firma corresponde a la firma digital del acudiente almacenada en el perfil del estudiante.",
        )

    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    filename = f"permiso-{letter.id}-respuesta-{recipient.student.id}.pdf"
    return filename, buffer.getvalue()


def _wrap_text(pdf, text, font_size):
    words = text.split()
    if not words:
        return [""]

    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if pdf.stringWidth(candidate, "Helvetica", font_size) <= 16.4 * cm:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines
