from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APITestCase

from accounts.models import StudentProfile, TeacherProfile
from accounts.password_rules import PASSWORD_POLICY_MESSAGE, validate_password_strength
from accounts.serializers import UserSerializer


User = get_user_model()


class PasswordStrengthTests(TestCase):
    def test_accepts_password_matching_policy(self):
        validate_password_strength("Clave123!")

    def test_rejects_password_without_required_parts(self):
        invalid_passwords = ["short1!", "sinmayuscula1!", "SINNUMERO!", "SinEspecial1"]

        for password in invalid_passwords:
            with self.subTest(password=password):
                with self.assertRaisesMessage(ValueError, PASSWORD_POLICY_MESSAGE):
                    validate_password_strength(password)


class UserSerializerTests(TestCase):
    @patch("accounts.serializers.send_welcome_credentials_email")
    def test_creates_student_profile_for_student_user(self, mocked_email):
        serializer = UserSerializer(
            data={
                "email": "estudiante@example.com",
                "cedula": "100200300",
                "first_name": "Ana",
                "last_name": "Diaz",
                "direccion": "Calle 1",
                "rh": "o+",
                "role": "STUDENT",
                "grado": "Quinto",
                "acudiente_nombre": "Maria Diaz",
                "acudiente_cedula": "900800700",
                "acudiente_telefono": "3001234567",
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertTrue(user.must_change_password)
        self.assertEqual(user.rh, "O+")
        self.assertTrue(StudentProfile.objects.filter(user=user, grado="Quinto").exists())
        mocked_email.assert_called_once()

    @patch("accounts.serializers.send_welcome_credentials_email")
    def test_creates_teacher_profile_for_teacher_user(self, mocked_email):
        serializer = UserSerializer(
            data={
                "email": "docente@example.com",
                "cedula": "123456789",
                "first_name": "Luis",
                "last_name": "Perez",
                "direccion": "Calle 2",
                "rh": "A+",
                "role": "TEACHER",
                "especialidad": "Matematicas",
                "titulo": "Licenciado",
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        self.assertTrue(TeacherProfile.objects.filter(user=user, especialidad="Matematicas").exists())
        mocked_email.assert_called_once()

    def test_rejects_invalid_student_contact_data(self):
        serializer = UserSerializer(
            data={
                "email": "bad@example.com",
                "cedula": "ABC",
                "direccion": "",
                "rh": "ZZ",
                "role": "STUDENT",
                "acudiente_telefono": "123",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("cedula", serializer.errors)
        self.assertIn("direccion", serializer.errors)
        self.assertIn("rh", serializer.errors)
        self.assertIn("acudiente_telefono", serializer.errors)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AuthenticationApiTests(APITestCase):
    def test_login_returns_jwt_and_user_payload(self):
        User.objects.create_user(
            email="admin@example.com",
            cedula="999",
            password="Admin123!",
            role="ADMIN",
            first_name="Admin",
            last_name="Principal",
            direccion="Calle Admin",
            rh="O+",
        )

        response = self.client.post(
            "/api/token/",
            {"email": "admin@example.com", "password": "Admin123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["role"], "ADMIN")
