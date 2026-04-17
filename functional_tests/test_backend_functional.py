from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from courses.models import Course, Subject
from landing_content.models import LandingCalendarEntry, LandingNews
from notifications.models import Notification


User = get_user_model()


class FunctionalBase(APITestCase):
    def create_user(self, *, email, cedula, role, password="Clave123!", **extra):
        defaults = {
            "first_name": extra.pop("first_name", role.title()),
            "last_name": extra.pop("last_name", "Funcional"),
            "direccion": extra.pop("direccion", "Calle funcional"),
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


class AuthenticationFunctionalTests(FunctionalBase):
    def test_token_endpoint_rejects_invalid_credentials(self):
        self.create_user(email="admin@example.com", cedula="100", role="ADMIN")

        response = self.client.post(
            "/api/token/",
            {"email": "admin@example.com", "password": "Incorrecta123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertNotIn("access", response.data)


class ProfileFunctionalTests(FunctionalBase):
    def test_user_can_read_and_update_own_profile(self):
        user = self.create_user(email="profile@example.com", cedula="109", role="TEACHER")
        self.client.force_authenticate(user)

        get_response = self.client.get("/api/profile/")
        self.assertEqual(get_response.status_code, 200, get_response.data)
        self.assertEqual(get_response.data["email"], "profile@example.com")

        update_response = self.client.put(
            "/api/profile/",
            {
                "first_name": "Docente",
                "last_name": "Actualizado",
                "email": "profile@example.com",
                "direccion": "Calle actualizada",
                "rh": "A+",
                "especialidad": "Ciencias",
                "titulo": "Licenciado",
            },
            format="json",
        )
        self.assertEqual(update_response.status_code, 200, update_response.data)
        user.refresh_from_db()
        self.assertEqual(user.first_name, "Docente")
        self.assertEqual(user.direccion, "Calle actualizada")

    def test_user_can_change_password_with_current_password(self):
        user = self.create_user(
            email="password@example.com",
            cedula="110",
            role="STUDENT",
            password="Actual123!",
        )
        self.client.force_authenticate(user)

        response = self.client.post(
            "/api/change-password/",
            {"old_password": "Actual123!", "new_password": "Nueva123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 200, response.data)
        user.refresh_from_db()
        self.assertTrue(user.check_password("Nueva123!"))


class NotificationFunctionalTests(FunctionalBase):
    def test_user_can_list_mark_and_delete_own_notification(self):
        user = self.create_user(email="student@example.com", cedula="101", role="STUDENT")
        other_user = self.create_user(email="other@example.com", cedula="102", role="STUDENT")
        notification = Notification.objects.create(
            usuario=user,
            titulo="Aviso",
            mensaje="Mensaje funcional",
        )
        Notification.objects.create(
            usuario=other_user,
            titulo="Aviso privado",
            mensaje="No debe aparecer",
        )
        self.client.force_authenticate(user)

        list_response = self.client.get("/api/mis-notificaciones/")
        self.assertEqual(list_response.status_code, 200, list_response.data)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]["id"], notification.id)

        mark_response = self.client.post(f"/api/notificaciones/{notification.id}/leer/")
        self.assertEqual(mark_response.status_code, 200, mark_response.data)
        notification.refresh_from_db()
        self.assertTrue(notification.leida)

        delete_response = self.client.delete(f"/api/notificaciones/{notification.id}/")
        self.assertEqual(delete_response.status_code, 204)
        self.assertFalse(Notification.objects.filter(id=notification.id).exists())


class CourseFunctionalTests(FunctionalBase):
    def test_student_course_endpoint_returns_only_enrolled_courses(self):
        student = self.create_user(email="student@example.com", cedula="103", role="STUDENT")
        visible_course = Course.objects.create(nombre="Sexto A")
        hidden_course = Course.objects.create(nombre="Septimo A")
        visible_course.estudiantes.add(student)
        self.client.force_authenticate(student)

        response = self.client.get("/api/courses/")

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual([item["name"] for item in response.data], [visible_course.nombre])
        self.assertNotIn(hidden_course.nombre, [item["name"] for item in response.data])


class AssignmentFunctionalTests(FunctionalBase):
    def test_student_cannot_create_assignment(self):
        teacher = self.create_user(email="teacher@example.com", cedula="104", role="TEACHER")
        student = self.create_user(email="student2@example.com", cedula="105", role="STUDENT")
        course = Course.objects.create(nombre="Octavo A", director_curso=teacher)
        subject = Subject.objects.create(nombre="Lenguaje", curso=course, docente=teacher)
        self.client.force_authenticate(student)

        response = self.client.post(
            "/api/assignments/",
            {
                "materia": subject.id,
                "titulo": "Ensayo",
                "descripcion": "Escribir ensayo.",
                "fecha_entrega": "2026-04-30",
                "periodo": 1,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)


class CalendarFunctionalTests(FunctionalBase):
    def test_teacher_cannot_create_event_for_unrelated_course(self):
        teacher = self.create_user(email="teacher@example.com", cedula="106", role="TEACHER")
        other_teacher = self.create_user(email="other-teacher@example.com", cedula="107", role="TEACHER")
        course = Course.objects.create(nombre="Noveno A", director_curso=other_teacher)
        self.client.force_authenticate(teacher)

        response = self.client.post(
            "/api/calendar/events/",
            {
                "titulo": "Evento no autorizado",
                "descripcion": "No debe crearse.",
                "fecha_inicio": "2026-05-01T08:00:00-05:00",
                "fecha_fin": "2026-05-01T09:00:00-05:00",
                "tipo": "EVENT",
                "curso": course.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)


class PermissionLetterFunctionalTests(FunctionalBase):
    def test_admin_cannot_create_permission_letter_for_course_without_students(self):
        admin = self.create_user(email="admin@example.com", cedula="108", role="ADMIN")
        course = Course.objects.create(nombre="Decimo A")
        self.client.force_authenticate(admin)
        document = SimpleUploadedFile(
            "permiso.pdf",
            b"%PDF-1.4 permiso funcional",
            content_type="application/pdf",
        )

        response = self.client.post(
            "/api/permission-letters/",
            {
                "title": "Permiso sin estudiantes",
                "description": "No debe crearse si no hay estudiantes.",
                "course": course.id,
                "document": document,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)


class LandingFunctionalTests(FunctionalBase):
    def test_public_landing_content_returns_only_active_items(self):
        LandingNews.objects.create(
            title="Noticia activa",
            summary="Resumen activo",
            published_at="2026-04-16",
            display_order=1,
            is_active=True,
        )
        LandingNews.objects.create(
            title="Noticia inactiva",
            summary="Resumen inactivo",
            published_at="2026-04-16",
            display_order=2,
            is_active=False,
        )
        LandingCalendarEntry.objects.create(
            title="Reunion general",
            detail="Encuentro institucional",
            event_date="2026-04-20",
            is_active=True,
        )

        response = self.client.get("/api/landing/content/")

        self.assertEqual(response.status_code, 200, response.data)
        news_titles = [item["title"] for item in response.data["news"]]
        self.assertIn("Noticia activa", news_titles)
        self.assertNotIn("Noticia inactiva", news_titles)
        self.assertEqual(response.data["calendar_entries"][0]["title"], "Reunion general")

    def test_landing_contact_rejects_invalid_email(self):
        response = self.client.post(
            "/api/landing/contact/",
            {
                "name": "Acudiente",
                "email": "correo-invalido",
                "subject": "Informacion",
                "message": "Quiero recibir informacion.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)
