from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from rest_framework import viewsets, permissions, status
from .models import User, StudentProfile, TeacherProfile
from .serializers import UserSerializer, StudentProfileSerializer, TeacherProfileSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

# ---- Para recuperación de contraseña ----
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()
token_generator = PasswordResetTokenGenerator()


# ==============================
# LOGIN JWT PERSONALIZADO
# ==============================
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


# ==============================
# 👥 USERS CRUD (con roles)
# ==============================
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = User.objects.all()
        role = self.request.query_params.get('role')

        if role:
            queryset = queryset.filter(role__iexact=role)

        return queryset


# ==============================
# STUDENT PROFILE CRUD
# ==============================
class StudentProfileViewSet(viewsets.ModelViewSet):
    queryset = StudentProfile.objects.all()
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]


# ==============================
# TEACHER PROFILE CRUD
# ==============================
class TeacherProfileViewSet(viewsets.ModelViewSet):
    queryset = TeacherProfile.objects.all()
    serializer_class = TeacherProfileSerializer
    permission_classes = [permissions.IsAuthenticated]


# ==============================
#  RECUPERAR CONTRASEÑA (EMAIL)
# ==============================

# 1️ Enviar correo con enlace
@api_view(['POST'])
@permission_classes([])  # No requiere autenticación
def forgot_password(request):
    email = request.data.get('email')
    if not email:
        return Response({"error": "El correo es obligatorio."}, status=status.HTTP_400_BAD_REQUEST)

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
        return Response({"message": "Correo de restablecimiento enviado correctamente."}, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({"error": "No existe una cuenta con este correo."}, status=status.HTTP_404_NOT_FOUND)


# 2️Restablecer contraseña con token
@api_view(['POST'])
@permission_classes([])  # No requiere autenticación
def reset_password(request, uidb64, token):
    password = request.data.get('password')
    if not password:
        return Response({"error": "La contraseña es obligatoria."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and token_generator.check_token(user, token):
        user.set_password(password)
        user.save()
        return Response({"message": "Contraseña restablecida exitosamente."}, status=status.HTTP_200_OK)
    else:
        return Response({"error": "Enlace inválido o expirado."}, status=status.HTTP_400_BAD_REQUEST)
