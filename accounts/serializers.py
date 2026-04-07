import logging

from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .file_validators import validate_image_file, validate_pdf_file
from .models import StudentProfile, TeacherProfile, User, UserDocument
from .onboarding import generate_temporary_password, send_welcome_credentials_email
from .password_rules import validate_password_strength

logger = logging.getLogger(__name__)
VALID_RH_VALUES = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['cedula'] = user.cedula
        token['role'] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        request = self.context.get("request")

        data["user"] = {
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
        return data


class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = [
            'id',
            'grado',
            'acudiente_nombre',
            'acudiente_cedula',
            'acudiente_telefono',
            'acudiente_email',
        ]


class TeacherProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherProfile
        fields = ['id', 'especialidad', 'titulo']


class UserDocumentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = UserDocument
        fields = ["id", "title", "category", "file", "file_url", "uploaded_at"]
        extra_kwargs = {"file": {"write_only": True}}

    def get_file_url(self, obj):
        request = self.context.get("request")
        try:
            return request.build_absolute_uri(obj.file.url) if request else obj.file.url
        except (AttributeError, OSError, ValueError, FileNotFoundError):
            return None

    def validate_file(self, value):
        try:
            return validate_pdf_file(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))


class UserSerializer(serializers.ModelSerializer):
    student_profile = StudentProfileSerializer(read_only=True)
    teacher_profile = TeacherProfileSerializer(read_only=True)
    documents = UserDocumentSerializer(read_only=True, many=True)
    photo_url = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    course_names = serializers.SerializerMethodField()

    grado = serializers.CharField(write_only=True, required=False, allow_blank=True)
    acudiente_nombre = serializers.CharField(write_only=True, required=False, allow_blank=True)
    acudiente_cedula = serializers.CharField(write_only=True, required=False, allow_blank=True)
    acudiente_telefono = serializers.CharField(write_only=True, required=False, allow_blank=True)
    acudiente_email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    especialidad = serializers.CharField(write_only=True, required=False, allow_blank=True)
    titulo = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    avatar_style = serializers.CharField(required=False, allow_blank=True)
    avatar_seed = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'cedula',
            'first_name',
            'last_name',
            'direccion',
            'rh',
            'role',
            'profile_photo',
            'photo_url',
            'avatar_url',
            'avatar_style',
            'avatar_seed',
            'is_active',
            'must_change_password',
            'password',
            'course_names',
            'student_profile',
            'teacher_profile',
            'documents',
            'grado',
            'acudiente_nombre',
            'acudiente_cedula',
            'acudiente_telefono',
            'acudiente_email',
            'especialidad',
            'titulo',
        ]
        extra_kwargs = {
            "profile_photo": {"required": False},
            "must_change_password": {"read_only": True},
        }

    def get_photo_url(self, obj):
        return obj.get_photo_url(self.context.get("request"))

    def get_avatar_url(self, obj):
        return obj.get_avatar_url(self.context.get("request"))

    def get_course_names(self, obj):
        if obj.role == "STUDENT":
            return list(obj.cursos.order_by("nombre").values_list("nombre", flat=True))
        if obj.role == "TEACHER":
            return list(obj.cursos_asignados.order_by("nombre").values_list("nombre", flat=True))
        return []

    def validate_password(self, value):
        if value:
            try:
                validate_password_strength(value)
            except ValueError as exc:
                raise serializers.ValidationError(str(exc))
        return value

    def validate_profile_photo(self, value):
        try:
            return validate_image_file(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))

    def validate_cedula(self, value):
        if value and not str(value).isdigit():
            raise serializers.ValidationError("La cedula solo puede contener numeros.")
        return value

    def validate_acudiente_telefono(self, value):
        if value and (not str(value).isdigit() or len(str(value)) != 10):
            raise serializers.ValidationError(
                "El telefono del acudiente debe tener exactamente 10 numeros."
            )
        return value

    def validate_acudiente_cedula(self, value):
        if value and not str(value).isdigit():
            raise serializers.ValidationError("La cedula del acudiente solo puede contener numeros.")
        return value

    def validate_direccion(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("La direccion es obligatoria.")
        return value.strip()

    def validate_rh(self, value):
        normalized_value = (value or "").strip().upper()
        if normalized_value not in VALID_RH_VALUES:
            raise serializers.ValidationError("Selecciona un RH valido.")
        return normalized_value

    def validate(self, attrs):
        email = attrs.get("email")
        if email and "@" not in email:
            raise serializers.ValidationError({"email": "Ingresa un correo valido con arroba."})
        return attrs

    def create(self, validated_data):
        role = validated_data.get('role')
        validated_data.pop('password', None)

        grado = validated_data.pop('grado', None)
        acudiente_nombre = validated_data.pop('acudiente_nombre', None)
        acudiente_cedula = validated_data.pop('acudiente_cedula', None)
        acudiente_telefono = validated_data.pop('acudiente_telefono', None)
        acudiente_email = validated_data.pop('acudiente_email', None)
        especialidad = validated_data.pop('especialidad', None)
        titulo = validated_data.pop('titulo', None)

        temporary_password = generate_temporary_password()

        with transaction.atomic():
            user = User.objects.create_user(
                password=temporary_password,
                must_change_password=True,
                **validated_data,
            )

            if role == "STUDENT":
                StudentProfile.objects.create(
                    user=user,
                    grado=grado or "",
                    acudiente_nombre=acudiente_nombre or "",
                    acudiente_cedula=acudiente_cedula or "",
                    acudiente_telefono=acudiente_telefono or "",
                    acudiente_email=acudiente_email or "",
                )
            elif role == "TEACHER":
                TeacherProfile.objects.create(
                    user=user,
                    especialidad=especialidad or "",
                    titulo=titulo or "",
                )

            try:
                send_welcome_credentials_email(user, temporary_password)
            except Exception as exc:
                logger.exception("No se pudo enviar el correo de bienvenida para %s", user.email)
                user._welcome_email_error = str(exc)

        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        role = validated_data.get('role', instance.role)

        grado = validated_data.pop('grado', None)
        acudiente_nombre = validated_data.pop('acudiente_nombre', None)
        acudiente_cedula = validated_data.pop('acudiente_cedula', None)
        acudiente_telefono = validated_data.pop('acudiente_telefono', None)
        acudiente_email = validated_data.pop('acudiente_email', None)
        especialidad = validated_data.pop('especialidad', None)
        titulo = validated_data.pop('titulo', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)
        instance.save()

        if role == "STUDENT":
            StudentProfile.objects.update_or_create(
                user=instance,
                defaults={
                    'grado': grado or "",
                    'acudiente_nombre': acudiente_nombre or "",
                    'acudiente_cedula': acudiente_cedula or "",
                    'acudiente_telefono': acudiente_telefono or "",
                    'acudiente_email': acudiente_email or "",
                }
            )
        elif role == "TEACHER":
            TeacherProfile.objects.update_or_create(
                user=instance,
                defaults={
                    'especialidad': especialidad or "",
                    'titulo': titulo or "",
                }
            )

        return instance
