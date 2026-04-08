from rest_framework import permissions, status
from rest_framework.decorators import (
    api_view,
    parser_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from django.utils import timezone

from .data_policy import (
    DATA_POLICY_VERSION,
    get_data_policy_payload_for_user,
    save_user_signature_image,
    store_signed_data_policy_document,
    validate_signer_data,
)
from .file_validators import validate_image_file


def _build_user_payload(user, request=None):
    return {
        "id": user.id,
        "email": user.email,
        "cedula": user.cedula,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "direccion": user.direccion,
        "rh": user.rh,
        "role": user.role,
        "must_change_password": user.must_change_password,
        "has_accepted_data_policy": user.has_accepted_data_policy,
        "data_policy_accepted_at": user.data_policy_accepted_at,
        "has_saved_signature": user.has_saved_signature,
        "photo_url": user.get_photo_url(request),
        "avatar_url": user.get_avatar_url(request),
        "avatar_style": user.avatar_style,
        "avatar_seed": user.get_avatar_seed(),
    }


def _save_data_policy_signature(*, user, signature_file):
    signer = validate_signer_data(user)

    validated_signature = validate_image_file(signature_file)
    save_user_signature_image(user=user, signature_file=validated_signature)
    validated_signature.seek(0)
    document = store_signed_data_policy_document(
        user=user,
        signer_name=signer["name"],
        signer_document=signer["document"],
        signature_file=validated_signature,
    )

    user.data_policy_accepted_at = timezone.now()
    user.data_policy_acceptor_name = signer["name"]
    user.data_policy_acceptor_document = signer["document"]
    user.data_policy_version = DATA_POLICY_VERSION
    user.save(
        update_fields=[
            "data_policy_accepted_at",
            "data_policy_acceptor_name",
            "data_policy_acceptor_document",
            "data_policy_version",
        ]
    )

    return document


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([])
def data_policy_status(request):
    return Response(get_data_policy_payload_for_user(request.user), status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@throttle_classes([])
def accept_data_policy(request):
    user = request.user

    accepted = str(request.data.get("accept", "")).strip().lower() in {"1", "true", "yes", "on"}
    if not accepted:
        return Response(
            {"error": "Debes aceptar la política de tratamiento de datos para continuar."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    signature_file = request.FILES.get("signature_file")
    if not signature_file:
        return Response(
            {"error": "Debes adjuntar una firma o dibujarla antes de continuar."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        document = _save_data_policy_signature(user=user, signature_file=signature_file)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {
            "message": "La autorización de tratamiento de datos fue aceptada correctamente.",
            "user": _build_user_payload(user, request),
            "document": {
                "id": document.id,
                "title": document.title,
                "category": document.category,
                "file_url": request.build_absolute_uri(document.file.url) if document.file else None,
            },
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
@throttle_classes([])
def update_data_policy_signature(request):
    user = request.user

    if not user.has_accepted_data_policy:
        return Response(
            {"error": "Primero debes aceptar la política de tratamiento de datos."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    signature_file = request.FILES.get("signature_file")
    if not signature_file:
        return Response(
            {"error": "Debes adjuntar una nueva firma para actualizar el documento."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        document = _save_data_policy_signature(user=user, signature_file=signature_file)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {
            "message": "La firma del tratamiento de datos fue actualizada correctamente.",
            "user": _build_user_payload(user, request),
            "document": {
                "id": document.id,
                "title": document.title,
                "category": document.category,
                "file_url": request.build_absolute_uri(document.file.url) if document.file else None,
            },
        },
        status=status.HTTP_200_OK,
    )
