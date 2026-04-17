from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from courses.models import Course, Subject


User = get_user_model()


class CourseApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email="admin@example.com",
            cedula="1",
            password="Admin123!",
            role="ADMIN",
            direccion="Calle 1",
            rh="O+",
        )
        self.teacher = User.objects.create_user(
            email="teacher@example.com",
            cedula="2",
            password="Teacher123!",
            role="TEACHER",
            direccion="Calle 2",
            rh="A+",
        )
        self.student = User.objects.create_user(
            email="student@example.com",
            cedula="3",
            password="Student123!",
            role="STUDENT",
            direccion="Calle 3",
            rh="B+",
        )

    def test_admin_can_create_course_and_add_students(self):
        self.client.force_authenticate(self.admin)

        create_response = self.client.post(
            "/api/courses/",
            {
                "name": "Sexto A",
                "description": "Curso de prueba",
                "teacher": self.teacher.id,
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, 201, create_response.data)

        course_id = create_response.data["id"]
        add_response = self.client.post(
            f"/api/courses/{course_id}/add-students/",
            {"students": [self.student.id]},
            format="json",
        )

        self.assertEqual(add_response.status_code, 200)
        self.assertTrue(Course.objects.get(id=course_id).estudiantes.filter(id=self.student.id).exists())

    def test_teacher_only_sees_related_subjects(self):
        other_teacher = User.objects.create_user(
            email="other@example.com",
            cedula="4",
            password="Teacher123!",
            role="TEACHER",
            direccion="Calle 4",
            rh="AB+",
        )
        visible_course = Course.objects.create(nombre="Septimo A", director_curso=self.teacher)
        hidden_course = Course.objects.create(nombre="Octavo A", director_curso=other_teacher)
        Subject.objects.create(nombre="Matematicas", curso=visible_course, docente=self.teacher)
        Subject.objects.create(nombre="Historia", curso=hidden_course, docente=other_teacher)

        self.client.force_authenticate(self.teacher)
        response = self.client.get("/api/subjects/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["nombre"] for item in response.data], ["Matematicas"])
