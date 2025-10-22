from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings

# -------- MANAGER --------
class UserManager(BaseUserManager):
    def create_user(self, email, cedula, password=None, **extra_fields):
        if not email:
            raise ValueError('El correo es obligatorio')
        if not cedula:
            raise ValueError('La cédula es obligatoria')
        email = self.normalize_email(email)
        user = self.model(email=email, cedula=cedula, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, cedula, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, cedula, password, **extra_fields)

# -------- MODELO USER --------
class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('ADMIN', 'Administrador'),
        ('TEACHER', 'Docente'),
        ('STUDENT', 'Estudiante'),
    )

    email = models.EmailField(unique=True)             # usado para login
    cedula = models.CharField(max_length=20, unique=True)  # identificador único
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'          # login con email
    REQUIRED_FIELDS = ['cedula']      # campo obligatorio al crear usuario

    def __str__(self):
        return f'{self.email} - {self.cedula} - {self.get_role_display()}'


# -------- PROFILES --------
class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile"
    )
    grado = models.CharField(max_length=50)  # Ej: "10A", "11B"
    acudiente_nombre = models.CharField(max_length=150)
    acudiente_telefono = models.CharField(max_length=20)
    acudiente_email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"Estudiante: {self.user.email} - Grado {self.grado}"


class TeacherProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_profile"
    )
    especialidad = models.CharField(max_length=100)  # Ej: "Matemáticas"
    titulo = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Docente: {self.user.email} - {self.especialidad}"


class AdminProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="admin_profile"
    )
    cargo = models.CharField(max_length=100)  # Ej: "Coordinador", "Rector"

    def __str__(self):
        return f"Administrador: {self.user.email} - {self.cargo}"
