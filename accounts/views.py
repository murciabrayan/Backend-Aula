from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import StudentProfile, TeacherProfile, User, UserDocument
from .password_rules import validate_password_strength
from .serializers import (
    CustomTokenObtainPairSerializer,
    StudentProfileSerializer,
    TeacherProfileSerializer,
    UserDocumentSerializer,
    UserSerializer,
)

User = get_user_model()
token_generator = PasswordResetTokenGenerator()


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        queryset = User.objects.all()
        role = self.request.query_params.get("role")

        if role:
            queryset = queryset.filter(role__iexact=role)

        return queryset

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


class StudentProfileViewSet(viewsets.ModelViewSet):
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]


class TeacherProfileViewSet(viewsets.ModelViewSet):
    queryset = TeacherProfile.objects.all()
    serializer_class = TeacherProfileSerializer
    permission_classes = [permissions.IsAuthenticated]


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

        subject = "Restablecimiento de contrasena"
        message = (
            f"Hola {user.first_name or 'usuario'},\n\n"
            f"Para restablecer tu contrasena, haz clic en el siguiente enlace:\n"
            f"{reset_link}\n\n"
            f"Si tu no solicitaste este cambio, ignora este mensaje."
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
            {"error": "La contrasena es obligatoria."},
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
        user.save()
        return Response(
            {"message": "Contrasena restablecida exitosamente."},
            status=status.HTTP_200_OK,
        )

    return Response(
        {"error": "Enlace invalido o expirado."},
        status=status.HTTP_400_BAD_REQUEST,
    )
