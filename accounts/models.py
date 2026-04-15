from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings
from urllib.parse import quote


# MANPROG_CAPTURA_ACCOUNTS_MODELS_INICIO: modelo de usuario personalizado y perfiles por rol.
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
    direccion = models.CharField(max_length=220, blank=True, default="")
    rh = models.CharField(max_length=5, blank=True, default="")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    avatar_style = models.CharField(max_length=60, blank=True, default="adventurer-neutral")
    avatar_seed = models.CharField(max_length=180, blank=True, default="")
    signature_image = models.ImageField(upload_to='signatures/', blank=True, null=True)
    signature_updated_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    google_account = models.BooleanField(default=False)
    must_change_password = models.BooleanField(default=False)
    data_policy_accepted_at = models.DateTimeField(blank=True, null=True)
    data_policy_acceptor_name = models.CharField(max_length=180, blank=True, default="")
    data_policy_acceptor_document = models.CharField(max_length=20, blank=True, default="")
    data_policy_version = models.CharField(max_length=20, blank=True, default="")

    objects = UserManager()

    USERNAME_FIELD = 'email'          # login con email
    REQUIRED_FIELDS = ['cedula']      # campo obligatorio al crear usuario

    def __str__(self):
        return f'{self.email} - {self.cedula} - {self.get_role_display()}'

    def get_avatar_seed(self):
        if self.avatar_seed:
            return self.avatar_seed
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.email or self.cedula

    def get_generated_avatar_url(self):
        style = self.avatar_style or "adventurer-neutral"
        seed = quote(self.get_avatar_seed())
        return f"https://api.dicebear.com/9.x/{style}/svg?seed={seed}&backgroundType=gradientLinear"

    def get_photo_url(self, request=None):
        if not self.profile_photo:
            return None
        try:
            return (
                request.build_absolute_uri(self.profile_photo.url)
                if request
                else self.profile_photo.url
            )
        except (AttributeError, OSError, ValueError, FileNotFoundError):
            return None

    def get_avatar_url(self, request=None):
        return self.get_photo_url(request) or self.get_generated_avatar_url()

    @property
    def has_accepted_data_policy(self):
        return bool(self.data_policy_accepted_at)

    @property
    def has_saved_signature(self):
        return bool(self.signature_image or self.data_policy_accepted_at)


# -------- PROFILES --------
class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile"
    )
    grado = models.CharField(max_length=50)  # Ej: "Quinto", "sexto"
    acudiente_nombre = models.CharField(max_length=150)
    acudiente_cedula = models.CharField(max_length=20, blank=True, default="")
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


class UserDocument(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    title = models.CharField(max_length=180)
    category = models.CharField(max_length=120, blank=True)
    file = models.FileField(upload_to="user_documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at", "title"]

    def __str__(self):
        return f"{self.title} - {self.user.email}"
# MANPROG_CAPTURA_ACCOUNTS_MODELS_FIN
