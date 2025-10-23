from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .models import User, StudentProfile, TeacherProfile


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


# -------------------------------
# SERIALIZADOR PRINCIPAL DE USUARIO
# -------------------------------
class UserSerializer(serializers.ModelSerializer):
    student_profile = StudentProfileSerializer(read_only=True)
    teacher_profile = TeacherProfileSerializer(read_only=True)

    # Campos adicionales para crear/editar desde el frontend
    grado = serializers.CharField(write_only=True, required=False, allow_blank=True)
    acudiente_nombre = serializers.CharField(write_only=True, required=False, allow_blank=True)
    acudiente_telefono = serializers.CharField(write_only=True, required=False, allow_blank=True)
    acudiente_email = serializers.EmailField(write_only=True, required=False, allow_blank=True)
    especialidad = serializers.CharField(write_only=True, required=False, allow_blank=True)
    titulo = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'cedula',
            'first_name',
            'last_name',
            'role',
            'is_active',
            'password',
            'student_profile',
            'teacher_profile',
            'grado',
            'acudiente_nombre',
            'acudiente_telefono',
            'acudiente_email',
            'especialidad',
            'titulo',
        ]

    # -------------------------------
    # CREACIÓN DE USUARIO + PERFIL
    # -------------------------------
    def create(self, validated_data):
        role = validated_data.get('role')
        password = validated_data.pop('password', None)

        # Datos de perfil
        grado = validated_data.pop('grado', None)
        acudiente_nombre = validated_data.pop('acudiente_nombre', None)
        acudiente_telefono = validated_data.pop('acudiente_telefono', None)
        acudiente_email = validated_data.pop('acudiente_email', None)
        especialidad = validated_data.pop('especialidad', None)
        titulo = validated_data.pop('titulo', None)

        # Crear usuario base
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

        # Extraer datos de perfil
        grado = validated_data.pop('grado', None)
        acudiente_nombre = validated_data.pop('acudiente_nombre', None)
        acudiente_telefono = validated_data.pop('acudiente_telefono', None)
        acudiente_email = validated_data.pop('acudiente_email', None)
        especialidad = validated_data.pop('especialidad', None)
        titulo = validated_data.pop('titulo', None)

        # Actualizar campos del usuario
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()

        # Actualizar o crear perfil según rol
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
