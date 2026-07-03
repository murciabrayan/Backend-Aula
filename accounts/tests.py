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
        self.assertEqual(user.email, "estudiante-100200300@sin-correo.local")
        mocked_email.assert_not_called()

    @patch("accounts.serializers.send_welcome_credentials_email")
    def test_creates_student_without_grade_for_later_course_assignment(self, mocked_email):
        serializer = UserSerializer(
            data={
                "cedula": "300400500",
                "first_name": "Juan",
                "last_name": "Perez",
                "direccion": "Calle 5",
                "rh": "A+",
                "role": "STUDENT",
                "acudiente_nombre": "Fernando Perez",
                "acudiente_cedula": "1239874",
                "acudiente_telefono": "3123456789",
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()

        student_profile = StudentProfile.objects.get(user=user)
        self.assertEqual(student_profile.grado, "")
        self.assertEqual(user.email, "estudiante-300400500@sin-correo.local")
        mocked_email.assert_not_called()

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

    @patch("accounts.serializers.send_welcome_credentials_email")
    def test_partial_update_preserves_student_guardian_data(self, mocked_email):
        user = UserSerializer(
            data={
                "email": "perfil@example.com",
                "cedula": "111222333",
                "first_name": "Camila",
                "last_name": "Rios",
                "direccion": "Calle 3",
                "rh": "B+",
                "role": "STUDENT",
                "grado": "Sexto",
                "acudiente_nombre": "Laura Rios",
                "acudiente_cedula": "1234567890",
                "acudiente_telefono": "3211234567",
            }
        )
        self.assertTrue(user.is_valid(), user.errors)
        instance = user.save()

        serializer = UserSerializer(
            instance,
            data={"first_name": "Camila Maria"},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        student_profile = StudentProfile.objects.get(user=instance)
        self.assertEqual(student_profile.acudiente_nombre, "Laura Rios")
        self.assertEqual(student_profile.acudiente_cedula, "1234567890")
        self.assertEqual(student_profile.acudiente_telefono, "3211234567")
        mocked_email.assert_not_called()


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

    def test_student_can_login_with_cedula(self):
        User.objects.create_user(
            email="estudiante-login@example.com",
            cedula="1234567890",
            password="Clave123!",
            role="STUDENT",
            first_name="Sara",
            last_name="Lopez",
            direccion="Calle 9",
            rh="A+",
        )

        response = self.client.post(
            "/api/token/",
            {"email": "1234567890", "password": "Clave123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["user"]["role"], "STUDENT")
        self.assertEqual(response.data["user"]["login_identifier"], "1234567890")


class ProfileApiTests(APITestCase):
    def test_admin_can_reset_user_access_with_temporary_password(self):
        admin = User.objects.create_user(
            email="admin-reset@example.com",
            cedula="1010",
            password="Admin123!",
            role="ADMIN",
            first_name="Admin",
            last_name="Reset",
            direccion="Calle Admin",
            rh="O+",
        )
        student = User.objects.create_user(
            email="estudiante-reset@example.com",
            cedula="2020",
            password="Vieja123!",
            role="STUDENT",
            first_name="Luisa",
            last_name="Martinez",
            direccion="Calle 10",
            rh="A+",
            must_change_password=False,
        )

        self.client.force_authenticate(user=admin)
        response = self.client.post(f"/api/users/{student.id}/reset-access/", format="json")

        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn("credentials", response.data)
        self.assertEqual(response.data["credentials"]["login_identifier"], "2020")

        student.refresh_from_db()
        self.assertTrue(student.must_change_password)
        self.assertFalse(student.check_password("Vieja123!"))
        self.assertTrue(student.check_password(response.data["credentials"]["temporary_password"]))

    def test_avatar_update_preserves_student_guardian_data(self):
        user = User.objects.create_user(
            email="estudiante-avatar@example.com",
            cedula="555666777",
            password="Clave123!",
            role="STUDENT",
            first_name="Nicolas",
            last_name="Gomez",
            direccion="Calle 4",
            rh="A+",
        )
        StudentProfile.objects.create(
            user=user,
            grado="Septimo",
            acudiente_nombre="Diana Gomez",
            acudiente_cedula="9876543210",
            acudiente_telefono="3112223344",
            acudiente_email="diana@example.com",
        )

        self.client.force_authenticate(user=user)
        response = self.client.put(
            "/api/profile/",
            {
                "avatar_style": "personas",
                "avatar_seed": "nicolas-avatar",
                "clear_profile_photo": "true",
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 200, response.data)
        student_profile = StudentProfile.objects.get(user=user)
        self.assertEqual(student_profile.acudiente_nombre, "Diana Gomez")
        self.assertEqual(student_profile.acudiente_cedula, "9876543210")
        self.assertEqual(student_profile.acudiente_telefono, "3112223344")
        self.assertEqual(student_profile.acudiente_email, "diana@example.com")
