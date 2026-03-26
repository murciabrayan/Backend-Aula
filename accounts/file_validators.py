from pathlib import Path


PDF_CONTENT_TYPES = {
    "application/pdf",
    "application/x-pdf",
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
IMAGE_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
}
MAX_IMAGE_SIZE_MB = 3


def validate_pdf_file(uploaded_file):
    if not uploaded_file:
        return uploaded_file

    extension = Path(uploaded_file.name or "").suffix.lower()
    content_type = getattr(uploaded_file, "content_type", "") or ""

    if extension != ".pdf" or (content_type and content_type not in PDF_CONTENT_TYPES):
        raise ValueError("Solo se permiten archivos PDF.")

    return uploaded_file


def validate_image_file(uploaded_file, *, max_size_mb=MAX_IMAGE_SIZE_MB):
    if not uploaded_file:
        return uploaded_file

    extension = Path(uploaded_file.name or "").suffix.lower()
    content_type = getattr(uploaded_file, "content_type", "") or ""
    file_size = getattr(uploaded_file, "size", 0) or 0
    max_size_bytes = int(max_size_mb * 1024 * 1024)

    if extension not in IMAGE_EXTENSIONS or (
        content_type and content_type not in IMAGE_CONTENT_TYPES
    ):
        raise ValueError("Solo se permiten imagenes JPG, JPEG o PNG.")

    if file_size > max_size_bytes:
        raise ValueError(
            f"La imagen supera el tamano maximo permitido de {int(max_size_mb)} MB."
        )

    return uploaded_file
