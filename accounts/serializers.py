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


def build_login_identifier(user):
    return user.cedula if user.role == "STUDENT" else user.email


def build_placeholder_student_email(cedula: str) -> str:
    normalized_cedula = "".join(char for char in str(cedula or "") if char.isdigit()) or "sin-cedula"
    base_email = f"estudiante-{normalized_cedula}@sin-correo.local"
    candidate = base_email
    counter = 2

    while User.objects.filter(email__iexact=candidate).exists():
        candidate = f"estudiante-{normalized_cedula}-{counter}@sin-correo.local"
        counter += 1

    return candidate


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['cedula'] = user.cedula
        token['role'] = user.role
        return token

    def validate(self, attrs):
        identifier = (attrs.get(self.username_field) or "").strip()
        if identifier and "@" not in identifier:
            student_user = User.objects.filter(role="STUDENT", cedula=identifier).first()
            if student_user:
                attrs[self.username_field] = student_user.email

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
            "login_identifier": build_login_identifier(user),
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
            'acudiente_parentesco',
            'acudiente2_nombre',
            'acudiente2_cedula',
            'acudiente2_telefono',
            'acudiente2_email',
            'acudiente2_parentesco',
        ]


class TeacherProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeacherProfile
        fields = ['id', 'especialidad', 'titulo', 'telefono']


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
    email = serializers.EmailField(required=False, allow_blank=True)
    student_profile = StudentProfileSerializer(read_only=True)
    teacher_profile = TeacherProfileSerializer(read_only=True)
    documents = UserDocumentSerializer(read_only=True, many=True)
    photo_url = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    course_names = serializers.SerializerMethodField()
    login_identifier = serializers.SerializerMethodField()

    grado = serializers.CharField(write_only=True, required=False, allow_blank=True)
    acudiente_nombre = serializers.CharField(write_only=True, required=False, allow_blank=True)
    acudiente_cedula = serializers.CharField(write_only=True, required=False, allow_blank=True)
    acudiente_telefono = serializers.CharField(write_only=True, required=False, allow_blank=True)
    acudiente_email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    acudiente_parentesco = serializers.CharField(write_only=True, required=False, allow_blank=True)
    acudiente2_nombre = serializers.CharField(write_only=True, required=False, allow_blank=True)
    acudiente2_cedula = serializers.CharField(write_only=True, required=False, allow_blank=True)
    acudiente2_telefono = serializers.CharField(write_only=True, required=False, allow_blank=True)
    acudiente2_email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    acudiente2_parentesco = serializers.CharField(write_only=True, required=False, allow_blank=True)
    especialidad = serializers.CharField(write_only=True, required=False, allow_blank=True)
    titulo = serializers.CharField(write_only=True, required=False, allow_blank=True)
    telefono = serializers.CharField(write_only=True, required=False, allow_blank=True)
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
            'login_identifier',
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
            'acudiente_parentesco',
            'acudiente2_nombre',
            'acudiente2_cedula',
            'acudiente2_telefono',
            'acudiente2_email',
            'acudiente2_parentesco',
            'especialidad',
            'titulo',
            'telefono',
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

    def get_login_identifier(self, obj):
        return build_login_identifier(obj)

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

    def validate_acudiente_parentesco(self, value):
        return self._validate_parentesco(value)

    def validate_acudiente2_telefono(self, value):
        if value and (not str(value).isdigit() or len(str(value)) != 10):
            raise serializers.ValidationError(
                "El telefono del segundo acudiente debe tener exactamente 10 numeros."
            )
        return value

    def validate_acudiente2_cedula(self, value):
        if value and not str(value).isdigit():
            raise serializers.ValidationError(
                "La cedula del segundo acudiente solo puede contener numeros."
            )
        return value

    def validate_acudiente2_parentesco(self, value):
        return self._validate_parentesco(value)

    @staticmethod
    def _validate_parentesco(value):
        if not value:
            return value
        valid_codes = {code for code, _label in StudentProfile.PARENTESCO_CHOICES}
        normalized = str(value).strip().upper()
        if normalized not in valid_codes:
            raise serializers.ValidationError("Selecciona un parentesco valido.")
        return normalized

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
        role = attrs.get("role", getattr(self.instance, "role", None))
        current_email = getattr(self.instance, "email", "")

        if role != "STUDENT":
            effective_email = str(email or current_email or "").strip()
            if not effective_email:
                raise serializers.ValidationError({"email": "El correo es obligatorio para este usuario."})
            if "@" not in effective_email:
                raise serializers.ValidationError({"email": "Ingresa un correo valido con arroba."})

        if role == "STUDENT":
            student_profile = getattr(self.instance, "student_profile", None)

            def effective(field):
                value = attrs.get(field)
                if value is None and student_profile is not None:
                    value = getattr(student_profile, field, "")
                return str(value or "").strip()

            errors = {}
            is_create = self.instance is None

            # Acudiente 1: obligatorio.
            required_fields = {
                "acudiente_nombre": "El nombre del acudiente es obligatorio.",
                "acudiente_cedula": "La cedula del acudiente es obligatoria.",
                "acudiente_telefono": "El telefono del acudiente es obligatorio.",
            }
            # El parentesco solo se exige al registrar (no romper registros previos
            # ni actualizaciones parciales de estudiantes ya existentes).
            if is_create:
                required_fields["acudiente_parentesco"] = "Selecciona el parentesco del acudiente."
            for field, message in required_fields.items():
                if not effective(field):
                    errors[field] = message

            # Acudiente 2: opcional. Si llenan cualquiera de sus datos,
            # se exigen nombre, cedula, telefono y parentesco.
            acudiente2_fields = [
                "acudiente2_nombre",
                "acudiente2_cedula",
                "acudiente2_telefono",
                "acudiente2_email",
                "acudiente2_parentesco",
            ]
            has_any_acudiente2 = any(effective(field) for field in acudiente2_fields)
            if has_any_acudiente2:
                acudiente2_required = {
                    "acudiente2_nombre": "El nombre del segundo acudiente es obligatorio.",
                    "acudiente2_cedula": "La cedula del segundo acudiente es obligatoria.",
                    "acudiente2_telefono": "El telefono del segundo acudiente es obligatorio.",
                    "acudiente2_parentesco": "Selecciona el parentesco del segundo acudiente.",
                }
                for field, message in acudiente2_required.items():
                    if not effective(field):
                        errors[field] = message

            if errors:
                raise serializers.ValidationError(errors)

        return attrs

    def create(self, validated_data):
        role = validated_data.get('role')
        validated_data.pop('password', None)

        grado = validated_data.pop('grado', None)
        acudiente_nombre = validated_data.pop('acudiente_nombre', None)
        acudiente_cedula = validated_data.pop('acudiente_cedula', None)
        acudiente_telefono = validated_data.pop('acudiente_telefono', None)
        acudiente_email = validated_data.pop('acudiente_email', None)
        acudiente_parentesco = validated_data.pop('acudiente_parentesco', None)
        acudiente2_nombre = validated_data.pop('acudiente2_nombre', None)
        acudiente2_cedula = validated_data.pop('acudiente2_cedula', None)
        acudiente2_telefono = validated_data.pop('acudiente2_telefono', None)
        acudiente2_email = validated_data.pop('acudiente2_email', None)
        acudiente2_parentesco = validated_data.pop('acudiente2_parentesco', None)
        especialidad = validated_data.pop('especialidad', None)
        titulo = validated_data.pop('titulo', None)
        telefono = validated_data.pop('telefono', None)

        if role == "STUDENT" and not str(validated_data.get("email") or "").strip():
            validated_data["email"] = build_placeholder_student_email(validated_data.get("cedula"))

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
                    acudiente_parentesco=acudiente_parentesco or "",
                    acudiente2_nombre=acudiente2_nombre or "",
                    acudiente2_cedula=acudiente2_cedula or "",
                    acudiente2_telefono=acudiente2_telefono or "",
                    acudiente2_email=acudiente2_email or "",
                    acudiente2_parentesco=acudiente2_parentesco or "",
                )
            elif role == "TEACHER":
                TeacherProfile.objects.create(
                    user=user,
                    especialidad=especialidad or "",
                    titulo=titulo or "",
                    telefono=telefono or "",
                )

            if role != "STUDENT":
                try:
                    send_welcome_credentials_email(user, temporary_password)
                except Exception as exc:
                    logger.exception("No se pudo enviar el correo de bienvenida para %s", user.email)
                    user._welcome_email_error = str(exc)

        user._temporary_password = temporary_password
        user._login_identifier = build_login_identifier(user)
        user._credentials_delivery = "manual" if role == "STUDENT" else "email"

        return user

    def update(self, instance, validated_data):
        missing = object()
        password = validated_data.pop('password', None)
        role = validated_data.get('role', instance.role)

        grado = validated_data.pop('grado', missing)
        acudiente_nombre = validated_data.pop('acudiente_nombre', missing)
        acudiente_cedula = validated_data.pop('acudiente_cedula', missing)
        acudiente_telefono = validated_data.pop('acudiente_telefono', missing)
        acudiente_email = validated_data.pop('acudiente_email', missing)
        acudiente_parentesco = validated_data.pop('acudiente_parentesco', missing)
        acudiente2_nombre = validated_data.pop('acudiente2_nombre', missing)
        acudiente2_cedula = validated_data.pop('acudiente2_cedula', missing)
        acudiente2_telefono = validated_data.pop('acudiente2_telefono', missing)
        acudiente2_email = validated_data.pop('acudiente2_email', missing)
        acudiente2_parentesco = validated_data.pop('acudiente2_parentesco', missing)
        especialidad = validated_data.pop('especialidad', missing)
        titulo = validated_data.pop('titulo', missing)
        telefono = validated_data.pop('telefono', missing)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)
        instance.save()

        if role == "STUDENT":
            student, _ = StudentProfile.objects.get_or_create(
                user=instance,
                defaults={
                    'grado': "",
                    'acudiente_nombre': "",
                    'acudiente_cedula': "",
                    'acudiente_telefono': "",
                    'acudiente_email': "",
                },
            )
            profile_updates = {}
            profile_values = {
                'grado': grado,
                'acudiente_nombre': acudiente_nombre,
                'acudiente_cedula': acudiente_cedula,
                'acudiente_telefono': acudiente_telefono,
                'acudiente_email': acudiente_email,
                'acudiente_parentesco': acudiente_parentesco,
                'acudiente2_nombre': acudiente2_nombre,
                'acudiente2_cedula': acudiente2_cedula,
                'acudiente2_telefono': acudiente2_telefono,
                'acudiente2_email': acudiente2_email,
                'acudiente2_parentesco': acudiente2_parentesco,
            }
            for field, value in profile_values.items():
                if value is not missing:
                    profile_updates[field] = value or ""
            if profile_updates:
                for field, value in profile_updates.items():
                    setattr(student, field, value)
                student.save(update_fields=list(profile_updates.keys()))
        elif role == "TEACHER":
            teacher, _ = TeacherProfile.objects.get_or_create(
                user=instance,
                defaults={
                    'especialidad': "",
                    'titulo': "",
                },
            )
            profile_updates = {}
            if especialidad is not missing:
                profile_updates['especialidad'] = especialidad or ""
            if titulo is not missing:
                profile_updates['titulo'] = titulo or ""
            if telefono is not missing:
                profile_updates['telefono'] = telefono or ""
            if profile_updates:
                for field, value in profile_updates.items():
                    setattr(teacher, field, value)
                teacher.save(update_fields=list(profile_updates.keys()))

        return instance
