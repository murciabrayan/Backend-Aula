from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .models import User, StudentProfile, TeacherProfile, UserDocument
from .password_rules import validate_password_strength


# -------------------------------
# TOKEN PERSONALIZADO JWT
# -------------------------------
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
            "role": user.role,
            "photo_url": user.get_photo_url(request),
            "avatar_url": user.get_avatar_url(request),
            "avatar_style": user.avatar_style,
            "avatar_seed": user.get_avatar_seed(),
        }
        return data


# -------------------------------
# SERIALIZADORES DE PERFILES
# -------------------------------
class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = [
            'id',
            'grado',
            'acudiente_nombre',
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
            return (
                request.build_absolute_uri(obj.file.url)
                if request
                else obj.file.url
            )
        except (AttributeError, OSError, ValueError, FileNotFoundError):
            return None


# -------------------------------
# SERIALIZADOR PRINCIPAL DE USUARIO
# -------------------------------
class UserSerializer(serializers.ModelSerializer):
    student_profile = StudentProfileSerializer(read_only=True)
    teacher_profile = TeacherProfileSerializer(read_only=True)
    documents = UserDocumentSerializer(read_only=True, many=True)
    photo_url = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()

    # Campos adicionales
    grado = serializers.CharField(write_only=True, required=False, allow_blank=True)
    acudiente_nombre = serializers.CharField(write_only=True, required=False, allow_blank=True)
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
            'role',
            'profile_photo',
            'photo_url',
            'avatar_url',
            'avatar_style',
            'avatar_seed',
            'is_active',
            'password',
            'student_profile',
            'teacher_profile',
            'documents',
            'grado',
            'acudiente_nombre',
            'acudiente_telefono',
            'acudiente_email',
            'especialidad',
            'titulo',
        ]
        extra_kwargs = {"profile_photo": {"required": False}}

    def get_photo_url(self, obj):
        return obj.get_photo_url(self.context.get("request"))

    def get_avatar_url(self, obj):
        return obj.get_avatar_url(self.context.get("request"))

    def validate_password(self, value):
        if value:
            try:
                validate_password_strength(value)
            except ValueError as exc:
                raise serializers.ValidationError(str(exc))
        return value

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

    def validate(self, attrs):
        email = attrs.get("email")
        if email and "@" not in email:
            raise serializers.ValidationError({"email": "Ingresa un correo valido con arroba."})
        return attrs

    # -------------------------------
    # CREACIÓN DE USUARIO + PERFIL
    # -------------------------------
    def create(self, validated_data):
        role = validated_data.get('role')
        password = validated_data.pop('password', None)

        # Extraer los campos del perfil
        grado = validated_data.pop('grado', None)
        acudiente_nombre = validated_data.pop('acudiente_nombre', None)
        acudiente_telefono = validated_data.pop('acudiente_telefono', None)
        acudiente_email = validated_data.pop('acudiente_email', None)
        especialidad = validated_data.pop('especialidad', None)
        titulo = validated_data.pop('titulo', None)

        # Crear usuario base (asegurando nombres y apellidos)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
        user.save()

        # Crear perfil según el rol
        if role == "STUDENT":
            StudentProfile.objects.create(
                user=user,
                grado=grado or "",
                acudiente_nombre=acudiente_nombre or "",
                acudiente_telefono=acudiente_telefono or "",
                acudiente_email=acudiente_email or "",
            )
        elif role == "TEACHER":
            TeacherProfile.objects.create(
                user=user,
                especialidad=especialidad or "",
                titulo=titulo or "",
            )

        return user

    # -------------------------------
    # ACTUALIZACIÓN DE USUARIO + PERFIL
    # -------------------------------
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        role = validated_data.get('role', instance.role)

        grado = validated_data.pop('grado', None)
        acudiente_nombre = validated_data.pop('acudiente_nombre', None)
        acudiente_telefono = validated_data.pop('acudiente_telefono', None)
        acudiente_email = validated_data.pop('acudiente_email', None)
        especialidad = validated_data.pop('especialidad', None)
        titulo = validated_data.pop('titulo', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)
        instance.save()

        # Actualizar o crear perfil
        if role == "STUDENT":
            StudentProfile.objects.update_or_create(
                user=instance,
                defaults={
                    'grado': grado or "",
                    'acudiente_nombre': acudiente_nombre or "",
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
