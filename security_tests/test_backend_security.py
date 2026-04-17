from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APITestCase

from courses.models import Course, Subject


User = get_user_model()


SQL_INJECTION_PAYLOADS = [
    "' OR '1'='1",
    "admin@gimnasioloscerros.com'--",
    "1 OR 1=1",
    '"; DROP TABLE accounts_user; --',
]


class SecurityBase(APITestCase):
    def create_user(self, *, email, cedula, role, password="Clave123!", **extra):
        defaults = {
            "first_name": extra.pop("first_name", role.title()),
            "last_name": extra.pop("last_name", "Seguridad"),
            "direccion": extra.pop("direccion", "Calle seguridad"),
            "rh": extra.pop("rh", "O+"),
        }
        defaults.update(extra)
        return User.objects.create_user(
            email=email,
            cedula=cedula,
            password=password,
            role=role,
            **defaults,
        )


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    SECURE_SSL_REDIRECT=False,
)
class AuthenticationSqlInjectionSecurityTests(SecurityBase):
    def test_login_rejects_sql_injection_payloads(self):
        self.create_user(
            email="admin@gimnasioloscerros.com",
            cedula="9001",
            role="ADMIN",
            password="Clave123!",
        )

        for payload in SQL_INJECTION_PAYLOADS:
            with self.subTest(payload=payload):
                response = self.client.post(
                    "/api/token/",
                    {"email": payload, "password": payload},
                    format="json",
                )

                self.assertEqual(response.status_code, 401)
                self.assertNotIn("access", response.data)
                self.assertEqual(User.objects.count(), 1)


@override_settings(SECURE_SSL_REDIRECT=False)
class AuthorizationSecurityTests(SecurityBase):
    def test_anonymous_user_cannot_list_users_with_injection_query(self):
        self.create_user(email="admin@example.com", cedula="9002", role="ADMIN")

        response = self.client.get("/api/users/?role=ADMIN' OR '1'='1")

        self.assertIn(response.status_code, [401, 403])
        self.assertNotContains(response, "admin@example.com", status_code=response.status_code)

    def test_student_cannot_access_users_with_injection_query(self):
        student = self.create_user(email="student@example.com", cedula="9003", role="STUDENT")
        self.create_user(email="admin@example.com", cedula="9004", role="ADMIN")
        self.client.force_authenticate(student)

        response = self.client.get("/api/users/?role=ADMIN' OR '1'='1")

        self.assertEqual(response.status_code, 403)
        self.assertNotContains(response, "admin@example.com", status_code=403)


@override_settings(SECURE_SSL_REDIRECT=False)
class QueryParameterInjectionSecurityTests(SecurityBase):
    def test_subject_filter_rejects_sql_injection_without_server_error(self):
        admin = self.create_user(email="admin@example.com", cedula="9005", role="ADMIN")
        teacher = self.create_user(email="teacher@example.com", cedula="9006", role="TEACHER")
        course = Course.objects.create(nombre="Sexto Seguridad", director_curso=teacher)
        Subject.objects.create(nombre="Matematicas", curso=course, docente=teacher)
        self.client.force_authenticate(admin)

        response = self.client.get("/api/subjects/?course=1 OR 1=1")

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data, [])

    def test_area_filter_rejects_sql_injection_without_server_error(self):
        admin = self.create_user(email="admin-area@example.com", cedula="9007", role="ADMIN")
        Course.objects.create(nombre="Septimo Seguridad")
        self.client.force_authenticate(admin)

        response = self.client.get("/api/areas/?course='; DROP TABLE courses_course; --")

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data, [])
        self.assertEqual(Course.objects.count(), 1)


@override_settings(SECURE_SSL_REDIRECT=False)
class PublicFormInjectionSecurityTests(SecurityBase):
    def test_landing_contact_rejects_injection_as_email_without_server_error(self):
        response = self.client.post(
            "/api/landing/contact/",
            {
                "name": "Atacante",
                "email": "' OR '1'='1",
                "subject": "Prueba seguridad",
                "message": '"; DROP TABLE landing_content_landingnews; --',
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)
