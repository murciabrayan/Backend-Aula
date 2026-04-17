from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from attendance.models import Attendance
from attendance.serializers import AttendanceSerializer
from courses.models import Course


User = get_user_model()


class AttendanceSerializerTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            email="student@example.com",
            cedula="10",
            password="Student123!",
            role="STUDENT",
            direccion="Calle 10",
            rh="O+",
        )
        self.other_student = User.objects.create_user(
            email="other-student@example.com",
            cedula="11",
            password="Student123!",
            role="STUDENT",
            direccion="Calle 11",
            rh="A+",
        )
        self.course = Course.objects.create(nombre="Quinto A")
        self.course.estudiantes.add(self.student)

    def test_rejects_student_outside_course(self):
        serializer = AttendanceSerializer(
            data={
                "student": self.other_student.id,
                "course": self.course.id,
                "date": "2026-04-16",
                "periodo": 1,
                "status": "PRESENT",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("student", serializer.errors)

    def test_rejects_justified_present_attendance(self):
        serializer = AttendanceSerializer(
            data={
                "student": self.student.id,
                "course": self.course.id,
                "date": "2026-04-16",
                "periodo": 1,
                "status": "PRESENT",
                "is_justified": True,
                "justification_type": "MEDICAL",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("is_justified", serializer.errors)

    def test_rejects_duplicate_attendance_for_same_student_and_date(self):
        Attendance.objects.create(
            student=self.student,
            course=self.course,
            date=date(2026, 4, 16),
            periodo=1,
            status="ABSENT",
        )
        serializer = AttendanceSerializer(
            data={
                "student": self.student.id,
                "course": self.course.id,
                "date": "2026-04-16",
                "periodo": 1,
                "status": "LATE",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
