from rest_framework import permissions, status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password

from .file_validators import validate_image_file
from .models import AdminProfile, StudentProfile, TeacherProfile
from .password_rules import validate_password_strength
from .serializers import UserDocumentSerializer

User = get_user_model()


@api_view(["GET", "PUT"])
@permission_classes([permissions.IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def user_profile(request):
    user = request.user

    if request.method == "GET":
        data = {
            "id": user.id,
            "email": user.email,
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
            "documents": UserDocumentSerializer(
                user.documents.all(),
                many=True,
                context={"request": request},
            ).data,
        }

        if user.role == "STUDENT":
            student = StudentProfile.objects.filter(user=user).first()
            if student:
                data.update(
                    {
                        "grado": student.grado,
                        "acudiente_nombre": student.acudiente_nombre,
                        "acudiente_cedula": student.acudiente_cedula,
                        "acudiente_telefono": student.acudiente_telefono,
                        "acudiente_email": student.acudiente_email,
                    }
                )
        elif user.role == "TEACHER":
            teacher = TeacherProfile.objects.filter(user=user).first()
            if teacher:
                data.update(
                    {
                        "especialidad": teacher.especialidad,
                        "titulo": teacher.titulo,
                    }
                )
        elif user.role == "ADMIN":
            admin = AdminProfile.objects.filter(user=user).first()
            if admin:
                data.update({"cargo": admin.cargo})

        return Response(data)

    user.first_name = request.data.get("first_name", user.first_name)
    user.last_name = request.data.get("last_name", user.last_name)
    user.email = request.data.get("email", user.email)
    user.direccion = request.data.get("direccion", user.direccion)
    user.rh = request.data.get("rh", user.rh)
    user.avatar_style = request.data.get(
        "avatar_style", user.avatar_style or "adventurer-neutral"
    )
    user.avatar_seed = request.data.get("avatar_seed", user.avatar_seed or "")

    if request.data.get("clear_profile_photo") == "true" and user.profile_photo:
        user.profile_photo.delete(save=False)
        user.profile_photo = None

    if "profile_photo" in request.FILES:
        try:
            user.profile_photo = validate_image_file(request.FILES["profile_photo"])
        except ValueError as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    user.save()

    if user.role == "STUDENT":
        student, _ = StudentProfile.objects.get_or_create(
            user=user,
            defaults={
                "grado": "",
                "acudiente_nombre": "",
                "acudiente_cedula": "",
                "acudiente_telefono": "",
                "acudiente_email": "",
            },
        )
        defaults = {}
        for field in (
            "grado",
            "acudiente_nombre",
            "acudiente_cedula",
            "acudiente_telefono",
            "acudiente_email",
        ):
            if field in request.data:
                defaults[field] = request.data.get(field, "")
        if defaults:
            for field, value in defaults.items():
                setattr(student, field, value)
            student.save(update_fields=list(defaults.keys()))
    elif user.role == "TEACHER":
        teacher, _ = TeacherProfile.objects.get_or_create(
            user=user,
            defaults={"especialidad": "", "titulo": ""},
        )
        defaults = {}
        for field in ("especialidad", "titulo"):
            if field in request.data:
                defaults[field] = request.data.get(field, "")
        if defaults:
            for field, value in defaults.items():
                setattr(teacher, field, value)
            teacher.save(update_fields=list(defaults.keys()))
    elif user.role == "ADMIN":
        admin, _ = AdminProfile.objects.get_or_create(
            user=user,
            defaults={"cargo": ""},
        )
        if "cargo" in request.data:
            admin.cargo = request.data.get("cargo", "")
            admin.save(update_fields=["cargo"])

    return Response(
        {
            "message": "Perfil actualizado correctamente.",
            "profile": {
                "id": user.id,
                "email": user.email,
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
        }
    )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    user = request.user
    old_password = request.data.get("old_password")
    new_password = request.data.get("new_password")

    if not old_password or not new_password:
        return Response(
            {"error": "Debes ingresar ambas contraseñas."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not check_password(old_password, user.password):
        return Response(
            {"error": "La contraseña actual no es correcta."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        validate_password_strength(new_password)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.must_change_password = False
    user.save(update_fields=["password", "must_change_password"])
    return Response({"message": "Contraseña actualizada correctamente."})
