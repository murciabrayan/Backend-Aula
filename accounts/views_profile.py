from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.decorators import parser_classes
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from .models import AdminProfile, StudentProfile, TeacherProfile

User = get_user_model()


@api_view(['GET', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def user_profile(request):
    user = request.user

    # ---------- OBTENER PERFIL ----------
    if request.method == 'GET':
        data = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "photo_url": user.get_photo_url(request),
            "avatar_url": user.get_avatar_url(request),
            "avatar_style": user.avatar_style,
            "avatar_seed": user.get_avatar_seed(),
        }

        if user.role == "STUDENT":
            student = StudentProfile.objects.filter(user=user).first()
            if student:
                data.update({
                    "grado": student.grado,
                    "acudiente_nombre": student.acudiente_nombre,
                    "acudiente_telefono": student.acudiente_telefono,
                    "acudiente_email": student.acudiente_email,
                })

        elif user.role == "TEACHER":
            teacher = TeacherProfile.objects.filter(user=user).first()
            if teacher:
                data.update({
                    "especialidad": teacher.especialidad,
                    "titulo": teacher.titulo,
                })

        elif user.role == "ADMIN":
            admin = AdminProfile.objects.filter(user=user).first()
            if admin:
                data.update({
                    "cargo": admin.cargo,
                })

        return Response(data)

    # ---------- ACTUALIZAR PERFIL ----------
    elif request.method == 'PUT':
        user.first_name = request.data.get("first_name", user.first_name)
        user.last_name = request.data.get("last_name", user.last_name)
        user.email = request.data.get("email", user.email)
        user.avatar_style = request.data.get("avatar_style", user.avatar_style or "adventurer-neutral")
        user.avatar_seed = request.data.get("avatar_seed", user.avatar_seed or "")

        if request.data.get("clear_profile_photo") == "true" and user.profile_photo:
            user.profile_photo.delete(save=False)
            user.profile_photo = None

        if "profile_photo" in request.FILES:
            user.profile_photo = request.FILES["profile_photo"]
        user.save()

        if user.role == "STUDENT":
            StudentProfile.objects.update_or_create(
                user=user,
                defaults={
                    "grado": request.data.get("grado", ""),
                    "acudiente_nombre": request.data.get("acudiente_nombre", ""),
                    "acudiente_telefono": request.data.get("acudiente_telefono", ""),
                    "acudiente_email": request.data.get("acudiente_email", ""),
                },
            )

        elif user.role == "TEACHER":
            TeacherProfile.objects.update_or_create(
                user=user,
                defaults={
                    "especialidad": request.data.get("especialidad", ""),
                    "titulo": request.data.get("titulo", ""),
                },
            )

        elif user.role == "ADMIN":
            AdminProfile.objects.update_or_create(
                user=user,
                defaults={
                    "cargo": request.data.get("cargo", ""),
                },
            )

        return Response({
            "message": "Perfil actualizado correctamente.",
            "profile": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "photo_url": user.get_photo_url(request),
                "avatar_url": user.get_avatar_url(request),
                "avatar_style": user.avatar_style,
                "avatar_seed": user.get_avatar_seed(),
            }
        })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    user = request.user
    old_password = request.data.get("old_password")
    new_password = request.data.get("new_password")

    if not old_password or not new_password:
        return Response({"error": "Debes ingresar ambas contraseñas."}, status=status.HTTP_400_BAD_REQUEST)

    if not check_password(old_password, user.password):
        return Response({"error": "La contraseña actual no es correcta."}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()
    return Response({"message": "Contraseña actualizada correctamente."})
