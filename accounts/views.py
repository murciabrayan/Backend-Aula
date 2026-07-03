from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.http import HttpResponse
import logging
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView

from .excel_utils import (
    build_bulk_user_template_workbook,
    parse_bulk_user_workbook,
    validate_excel_file,
)
from .models import StudentProfile, TeacherProfile, User, UserDocument
from .permissions import IsAdminRole
from .onboarding import generate_temporary_password
from .password_rules import validate_password_strength
from .serializers import (
    CustomTokenObtainPairSerializer,
    StudentProfileSerializer,
    TeacherProfileSerializer,
    UserDocumentSerializer,
    UserSerializer,
    build_login_identifier,
)

User = get_user_model()
token_generator = PasswordResetTokenGenerator()
logger = logging.getLogger(__name__)


def _normalize_bulk_user_row(*, row, role):
    payload = {
        "email": (row.get("email") or "").strip(),
        "cedula": str(row.get("cedula") or "").strip(),
        "first_name": (row.get("first_name") or "").strip(),
        "last_name": (row.get("last_name") or "").strip(),
        "direccion": (row.get("direccion") or "").strip(),
        "rh": (row.get("rh") or "").strip().upper(),
        "role": role,
    }

    if role == "STUDENT":
        payload.update(
            {
                "acudiente_nombre": (row.get("acudiente_nombre") or "").strip(),
                "acudiente_cedula": str(row.get("acudiente_cedula") or "").strip(),
                "acudiente_telefono": str(row.get("acudiente_telefono") or "").strip(),
            }
        )
    elif role == "TEACHER":
        payload.update(
            {
                "especialidad": (row.get("especialidad") or "").strip(),
                "titulo": (row.get("titulo") or "").strip(),
            }
        )

    return payload


def _serialize_bulk_row_result(*, sheet_name, row_number, payload, serializer):
    full_name = f"{payload.get('first_name', '').strip()} {payload.get('last_name', '').strip()}".strip()
    display_identifier = payload.get("cedula") if payload.get("role") == "STUDENT" else payload.get("email")
    return {
        "sheet": sheet_name,
        "row": row_number,
        "role": payload.get("role"),
        "name": full_name or display_identifier or f"Fila {row_number}",
        "email": payload.get("email") or "",
        "cedula": payload.get("cedula") or "",
        "status": "valid" if serializer.is_valid() else "error",
        "data": payload,
        "errors": serializer.errors if serializer.errors else {},
    }


def _build_credentials_payload(user, temporary_password=None):
    return {
        "full_name": f"{user.first_name} {user.last_name}".strip(),
        "role": user.role,
        "login_identifier": getattr(user, "_login_identifier", build_login_identifier(user)),
        "temporary_password": temporary_password or getattr(user, "_temporary_password", ""),
        "delivery_channel": getattr(user, "_credentials_delivery", "manual"),
    }


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [AnonRateThrottle]


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminRole]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        queryset = User.objects.all()
        role = self.request.query_params.get("role")

        if role:
            queryset = queryset.filter(role__iexact=role)

        return queryset

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except Exception as exc:
            logger.exception("Error al listar usuarios")
            return Response(
                {"detail": f"No se pudieron cargar los usuarios: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def create(self, request, *args, **kwargs):
        try:
            response = super().create(request, *args, **kwargs)
        except Exception as exc:
            logger.exception("Error al crear usuario")
            return Response(
                {"detail": f"No se pudo crear el usuario: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        created_user = getattr(self, "instance", None)
        temporary_password = getattr(created_user, "_temporary_password", None)
        if temporary_password:
            response.data["credentials"] = _build_credentials_payload(created_user, temporary_password)
        warning = getattr(created_user, "_welcome_email_error", None)
        if warning:
            response.data["warning"] = (
                "El usuario fue creado, pero no se pudo enviar el correo de bienvenida. "
                "Puedes compartir la clave temporal manualmente o revisar la configuracion SMTP."
            )
            response.data["warning_detail"] = warning
        return response

    def perform_create(self, serializer):
        self.instance = serializer.save()

    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser, FormParser])
    def documents(self, request, pk=None):
        user = self.get_object()
        serializer = UserDocumentSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @documents.mapping.get
    def list_documents(self, request, pk=None):
        user = self.get_object()
        serializer = UserDocumentSerializer(
            user.documents.all(), many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=["delete"], url_path=r"documents/(?P<document_id>[^/.]+)")
    def delete_document(self, request, pk=None, document_id=None):
        user = self.get_object()
        document = get_object_or_404(UserDocument, pk=document_id, user=user)
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="reset-access")
    def reset_access(self, request, pk=None):
        user = self.get_object()
        temporary_password = generate_temporary_password()
        user.set_password(temporary_password)
        user.must_change_password = True
        user.save(update_fields=["password", "must_change_password"])
        user._temporary_password = temporary_password
        user._login_identifier = build_login_identifier(user)
        user._credentials_delivery = "manual" if user.role == "STUDENT" else "email"

        return Response(
            {
                "message": "Se generaron nuevas credenciales temporales para el usuario.",
                "credentials": _build_credentials_payload(user, temporary_password),
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], url_path="bulk/template")
    def bulk_template(self, request):
        workbook_bytes = build_bulk_user_template_workbook()
        response = HttpResponse(
            workbook_bytes,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="plantilla-usuarios-masivos.xlsx"'
        return response

    @action(
        detail=False,
        methods=["post"],
        url_path="bulk/preview",
        parser_classes=[MultiPartParser, FormParser],
    )
    def bulk_preview(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response(
                {"error": "Debes adjuntar el archivo Excel para revisar los usuarios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validated_file = validate_excel_file(uploaded_file)
            workbook_data = parse_bulk_user_workbook(validated_file)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception("Error al previsualizar archivo de usuarios masivos")
            return Response(
                {"error": f"No se pudo leer el archivo Excel: {exc}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        rows = []
        sheet_definitions = [
            ("Estudiantes", "STUDENT"),
            ("Docentes", "TEACHER"),
        ]

        for sheet_name, role in sheet_definitions:
            for row_number, row in enumerate(workbook_data.get(sheet_name, []), start=2):
                payload = _normalize_bulk_user_row(row=row, role=role)
                serializer = self.get_serializer(data=payload, context={"request": request})
                rows.append(
                    _serialize_bulk_row_result(
                        sheet_name=sheet_name,
                        row_number=row_number,
                        payload=payload,
                        serializer=serializer,
                    )
                )

        valid_count = sum(1 for row in rows if row["status"] == "valid")
        error_count = sum(1 for row in rows if row["status"] == "error")

        return Response(
            {
                "message": "Previsualizacion generada.",
                "rows": rows,
                "total_count": len(rows),
                "valid_count": valid_count,
                "error_count": error_count,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=["post"],
        url_path="bulk/import",
        parser_classes=[MultiPartParser, FormParser],
    )
    def bulk_import(self, request):
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            return Response(
                {"error": "Debes adjuntar el archivo Excel para importar usuarios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validated_file = validate_excel_file(uploaded_file)
            workbook_data = parse_bulk_user_workbook(validated_file)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.exception("Error al leer archivo de usuarios masivos")
            return Response(
                {"error": f"No se pudo leer el archivo Excel: {exc}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created = []
        errors = []
        warnings = []
        sheet_definitions = [
            ("Estudiantes", "STUDENT"),
            ("Docentes", "TEACHER"),
        ]

        for sheet_name, role in sheet_definitions:
            for row_number, row in enumerate(workbook_data.get(sheet_name, []), start=2):
                payload = _normalize_bulk_user_row(row=row, role=role)
                serializer = self.get_serializer(data=payload, context={"request": request})

                if not serializer.is_valid():
                    errors.append(
                        {
                            "sheet": sheet_name,
                            "row": row_number,
                            "name": f"{payload.get('first_name', '').strip()} {payload.get('last_name', '').strip()}".strip()
                            or payload.get("cedula")
                            or payload.get("email")
                            or f"Fila {row_number}",
                            "email": payload.get("email") or "",
                            "errors": serializer.errors,
                        }
                    )
                    continue

                try:
                    user = serializer.save()
                except Exception as exc:
                    logger.exception("Error al crear usuario masivo")
                    errors.append(
                        {
                            "sheet": sheet_name,
                            "row": row_number,
                            "errors": {"detail": [str(exc)]},
                        }
                    )
                    continue

                created.append(
                    {
                        "id": user.id,
                        "email": user.email,
                        "role": user.role,
                        "name": f"{user.first_name} {user.last_name}".strip(),
                        "credentials": _build_credentials_payload(user),
                    }
                )

                warning = getattr(user, "_welcome_email_error", None)
                if warning:
                    warnings.append(
                        {
                            "sheet": sheet_name,
                            "row": row_number,
                            "email": user.email,
                            "warning": warning,
                        }
                    )

        return Response(
            {
                "message": "Importacion masiva procesada.",
                "created_count": len(created),
                "error_count": len(errors),
                "warning_count": len(warnings),
                "created": created,
                "errors": errors,
                "warnings": warnings,
            },
            status=status.HTTP_200_OK,
        )


class StudentProfileViewSet(viewsets.ModelViewSet):
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAdminRole]


class TeacherProfileViewSet(viewsets.ModelViewSet):
    queryset = TeacherProfile.objects.all()
    serializer_class = TeacherProfileSerializer
    permission_classes = [IsAdminRole]


@api_view(["POST"])
@permission_classes([])
def forgot_password(request):
    email = request.data.get("email")
    if not email:
        return Response(
            {"error": "El correo es obligatorio."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.get(email=email)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)
        reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"

        subject = "Restablecimiento de contraseña"
        message = (
            f"Hola {user.first_name or 'usuario'},\n\n"
            f"Para restablecer tu contraseña, haz clic en el siguiente enlace:\n"
            f"{reset_link}\n\n"
            f"Si tú no solicitaste este cambio, ignora este mensaje."
        )

        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
        return Response(
            {"message": "Correo de restablecimiento enviado correctamente."},
            status=status.HTTP_200_OK,
        )
    except User.DoesNotExist:
        return Response(
            {"error": "No existe una cuenta con este correo."},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["POST"])
@permission_classes([])
def reset_password(request, uidb64, token):
    password = request.data.get("password")
    if not password:
        return Response(
            {"error": "La contraseña es obligatoria."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        validate_password_strength(password)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and token_generator.check_token(user, token):
        user.set_password(password)
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password"])
        return Response(
            {"message": "Contraseña restablecida exitosamente."},
            status=status.HTTP_200_OK,
        )

    return Response(
        {"error": "Enlace inválido o expirado."},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def complete_initial_password(request):
    user = request.user
    new_password = request.data.get("new_password")

    if not user.must_change_password:
        return Response(
            {"error": "Tu cuenta no tiene un cambio inicial pendiente."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not new_password:
        return Response(
            {"error": "Debes ingresar una nueva contraseña."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        validate_password_strength(new_password)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.must_change_password = False
    user.save(update_fields=["password", "must_change_password"])

    return Response(
        {
            "message": "Contraseña actualizada correctamente.",
            "user": {
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
            },
        },
        status=status.HTTP_200_OK,
    )
