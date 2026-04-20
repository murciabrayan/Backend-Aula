from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from assignments.models import Assignment, Submission
from attendance.models import Attendance
from calendar_app.models import CalendarEvent
from courses.models import Course, Subject
from notifications.models import Notification
from permission_letters.models import PermissionLetter, PermissionLetterRecipient


User = get_user_model()


class AcceptanceBase(APITestCase):
    def create_user(self, *, email, cedula, role, password="Clave123!", **extra):
        defaults = {
            "first_name": extra.pop("first_name", role.title()),
            "last_name": extra.pop("last_name", "Prueba"),
            "direccion": extra.pop("direccion", "Calle 1"),
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

    def create_basic_academic_setup(self):
        admin = self.create_user(email="admin@example.com", cedula="1", role="ADMIN")
        teacher = self.create_user(email="teacher@example.com", cedula="2", role="TEACHER")
        student = self.create_user(email="student@example.com", cedula="3", role="STUDENT")
        course = Course.objects.create(nombre="Sexto A", director_curso=teacher, docente=teacher)
        course.estudiantes.add(student)
        subject = Subject.objects.create(nombre="Matematicas", curso=course, docente=teacher)
        return admin, teacher, student, course, subject


class AdminAcademicSetupAcceptanceTests(AcceptanceBase):
    def test_admin_creates_course_assigns_student_and_creates_subject(self):
        admin = self.create_user(email="admin@example.com", cedula="10", role="ADMIN")
        teacher = self.create_user(email="teacher@example.com", cedula="11", role="TEACHER")
        student = self.create_user(email="student@example.com", cedula="12", role="STUDENT")
        self.client.force_authenticate(admin)

        course_response = self.client.post(
            "/api/courses/",
            {
                "name": "Septimo A",
                "description": "Curso creado en aceptacion",
                "teacher": teacher.id,
            },
            format="json",
        )
        self.assertEqual(course_response.status_code, 201, course_response.data)

        course_id = course_response.data["id"]
        enroll_response = self.client.post(
            f"/api/courses/{course_id}/add-students/",
            {"students": [student.id]},
            format="json",
        )
        self.assertEqual(enroll_response.status_code, 200, enroll_response.data)

        subject_response = self.client.post(
            "/api/subjects/",
            {
                "nombre": "Ciencias",
                "curso": course_id,
                "teacher": teacher.id,
            },
            format="json",
        )
        self.assertEqual(subject_response.status_code, 201, subject_response.data)

        course = Course.objects.get(id=course_id)
        self.assertTrue(course.estudiantes.filter(id=student.id).exists())
        self.assertTrue(Subject.objects.filter(curso=course, nombre="Ciencias", docente=teacher).exists())


class AssignmentDeliveryAcceptanceTests(AcceptanceBase):
    def test_teacher_creates_assignment_student_submits_and_teacher_grades(self):
        _, teacher, student, _, subject = self.create_basic_academic_setup()

        self.client.force_authenticate(teacher)
        assignment_response = self.client.post(
            "/api/assignments/",
            {
                "materia": subject.id,
                "titulo": "Taller de fracciones",
                "descripcion": "Resolver ejercicios.",
                "fecha_entrega": "2026-04-30",
                "periodo": 1,
            },
            format="json",
        )
        self.assertEqual(assignment_response.status_code, 201, assignment_response.data)
        assignment_id = assignment_response.data["id"]
        self.assertTrue(Notification.objects.filter(usuario=student, titulo__contains="Nueva tarea").exists())

        self.client.force_authenticate(student)
        visible_assignments = self.client.get("/api/assignments/")
        self.assertEqual(visible_assignments.status_code, 200, visible_assignments.data)
        self.assertEqual(len(visible_assignments.data), 1)

        pdf_file = SimpleUploadedFile(
            "entrega.pdf",
            b"%PDF-1.4 entrega de aceptacion",
            content_type="application/pdf",
        )
        submission_response = self.client.post(
            "/api/submissions/",
            {"tarea": assignment_id, "archivo": pdf_file},
            format="multipart",
        )
        self.assertEqual(submission_response.status_code, 201, submission_response.data)
        submission_id = submission_response.data["id"]

        self.client.force_authenticate(teacher)
        grade_response = self.client.post(
            f"/api/submissions/{submission_id}/calificar/",
            {"calificacion": "4.5", "retroalimentacion": "Buen desarrollo."},
            format="json",
        )
        self.assertEqual(grade_response.status_code, 200, grade_response.data)

        submission = Submission.objects.get(id=submission_id)
        self.assertEqual(float(submission.calificacion), 4.5)
        self.assertEqual(submission.retroalimentacion, "Buen desarrollo.")
        self.assertTrue(Notification.objects.filter(usuario=student, titulo="Nueva calificación").exists())


class AttendanceAcceptanceTests(AcceptanceBase):
    def test_teacher_records_attendance_and_student_can_consult_it(self):
        _, teacher, student, course, _ = self.create_basic_academic_setup()
        self.client.force_authenticate(teacher)

        save_response = self.client.post(
            "/api/attendance/teacher/bulk-save/",
            {
                "date": "2026-04-16",
                "periodo": 1,
                "records": [
                    {
                        "student": student.id,
                        "status": "ABSENT",
                        "notes": "No asistio a clase.",
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(save_response.status_code, 200, save_response.data)

        summary_response = self.client.get(
            f"/api/attendance/course-summary/?course={course.id}&date=2026-04-16"
        )
        self.assertEqual(summary_response.status_code, 200, summary_response.data)
        self.assertEqual(summary_response.data["absent"], 1)

        self.client.force_authenticate(student)
        my_records_response = self.client.get("/api/attendance/my-records/")
        self.assertEqual(my_records_response.status_code, 200, my_records_response.data)
        self.assertEqual(my_records_response.data[0]["status"], "ABSENT")
        self.assertTrue(Attendance.objects.filter(student=student, date="2026-04-16").exists())


class CalendarAcceptanceTests(AcceptanceBase):
    def test_teacher_creates_calendar_event_and_student_sees_it(self):
        _, teacher, student, course, subject = self.create_basic_academic_setup()
        self.client.force_authenticate(teacher)

        event_response = self.client.post(
            "/api/calendar/events/",
            {
                "titulo": "Evaluacion de algebra",
                "descripcion": "Evaluacion programada.",
                "fecha_inicio": "2026-04-20T08:00:00-05:00",
                "fecha_fin": "2026-04-20T09:00:00-05:00",
                "tipo": "EXAM",
                "curso": course.id,
                "materia": subject.id,
            },
            format="json",
        )
        self.assertEqual(event_response.status_code, 201, event_response.data)
        self.assertTrue(CalendarEvent.objects.filter(titulo="Evaluacion de algebra").exists())

        self.client.force_authenticate(student)
        calendar_response = self.client.get("/api/calendar/")
        self.assertEqual(calendar_response.status_code, 200, calendar_response.data)
        titles = [item["title"] for item in calendar_response.data]
        self.assertIn("Evaluacion de algebra", titles)


class PermissionLetterAcceptanceTests(AcceptanceBase):
    def test_admin_sends_permission_letter_and_student_rejects_it(self):
        admin, _, student, course, _ = self.create_basic_academic_setup()
        self.client.force_authenticate(admin)

        document = SimpleUploadedFile(
            "permiso.pdf",
            b"%PDF-1.4 permiso de aceptacion",
            content_type="application/pdf",
        )
        create_response = self.client.post(
            "/api/permission-letters/",
            {
                "title": "Salida pedagogica",
                "description": "Permiso para salida pedagogica.",
                "course": course.id,
                "document": document,
            },
            format="multipart",
        )
        self.assertEqual(create_response.status_code, 201, create_response.data)
        recipient = PermissionLetterRecipient.objects.get(student=student)
        self.assertEqual(recipient.status, PermissionLetterRecipient.STATUS_PENDING)

        self.client.force_authenticate(student)
        list_response = self.client.get("/api/student/permission-letters/")
        self.assertEqual(list_response.status_code, 200, list_response.data)
        self.assertEqual(len(list_response.data), 1)

        reject_response = self.client.post(
            f"/api/student/permission-letters/{recipient.id}/respond/",
            {"action": "REJECT"},
            format="json",
        )
        self.assertEqual(reject_response.status_code, 200, reject_response.data)

        recipient.refresh_from_db()
        self.assertEqual(recipient.status, PermissionLetterRecipient.STATUS_REJECTED)
        self.assertIsNotNone(recipient.signed_document)
        self.assertTrue(Notification.objects.filter(usuario=admin, titulo__contains="Respuesta de permiso").exists())

    def test_admin_can_delete_permission_letter(self):
        admin, _, student, course, _ = self.create_basic_academic_setup()
        self.client.force_authenticate(admin)

        document = SimpleUploadedFile(
            "permiso.pdf",
            b"%PDF-1.4 permiso para eliminar",
            content_type="application/pdf",
        )
        create_response = self.client.post(
            "/api/permission-letters/",
            {
                "title": "Permiso temporal",
                "description": "Permiso creado para validar eliminacion.",
                "course": course.id,
                "document": document,
            },
            format="multipart",
        )
        self.assertEqual(create_response.status_code, 201, create_response.data)
        letter_id = create_response.data["id"]
        self.assertTrue(PermissionLetterRecipient.objects.filter(student=student).exists())

        delete_response = self.client.delete(f"/api/permission-letters/{letter_id}/")

        self.assertEqual(delete_response.status_code, 204)
        self.assertFalse(PermissionLetter.objects.filter(id=letter_id).exists())
        self.assertFalse(PermissionLetterRecipient.objects.filter(student=student).exists())
