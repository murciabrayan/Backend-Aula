import os

from django.core.management.base import BaseCommand

from accounts.models import User


class Command(BaseCommand):
    help = "Crea o actualiza un usuario administrador desde variables de entorno."

    def handle(self, *args, **options):
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "").strip()
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "").strip()

        if not email or not password:
            self.stdout.write(
                self.style.WARNING(
                    "No se creo admin: faltan DJANGO_SUPERUSER_EMAIL o DJANGO_SUPERUSER_PASSWORD."
                )
            )
            return

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "cedula": os.getenv("DJANGO_SUPERUSER_CEDULA", "999001").strip() or "999001",
                "role": "ADMIN",
                "first_name": os.getenv("DJANGO_SUPERUSER_FIRST_NAME", "Admin").strip() or "Admin",
                "last_name": os.getenv("DJANGO_SUPERUSER_LAST_NAME", "Produccion").strip()
                or "Produccion",
                "direccion": os.getenv("DJANGO_SUPERUSER_DIRECCION", "Principal").strip()
                or "Principal",
                "rh": os.getenv("DJANGO_SUPERUSER_RH", "O+").strip() or "O+",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )

        user.role = "ADMIN"
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()

        action = "creado" if created else "actualizado"
        self.stdout.write(self.style.SUCCESS(f"Administrador {action}: {email}"))
