from pathlib import Path


PDF_CONTENT_TYPES = {
    "application/pdf",
    "application/x-pdf",
}


def validate_pdf_file(uploaded_file):
    if not uploaded_file:
        return uploaded_file

    extension = Path(uploaded_file.name or "").suffix.lower()
    content_type = getattr(uploaded_file, "content_type", "") or ""

    if extension != ".pdf" or (content_type and content_type not in PDF_CONTENT_TYPES):
        raise ValueError("Solo se permiten archivos PDF.")

    return uploaded_file
