from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from assignments.models import Assignment
from assignments.serializers import (
    AssignmentSerializer,
    DirectActivityGradeEntrySerializer,
    SubmissionSerializer,
)
from courses.models import Course, Subject


class AssignmentFileValidationTests(TestCase):
    def setUp(self):
        self.course = Course.objects.create(nombre="Sexto A")
        self.subject = Subject.objects.create(nombre="Matematicas", curso=self.course)

    def _base_payload(self, uploaded_file):
        return {
            "materia": self.subject.id,
            "titulo": "Taller de fracciones",
            "descripcion": "Resolver los ejercicios propuestos.",
            "fecha_entrega": "2026-04-30",
            "periodo": 1,
            "archivo": uploaded_file,
        }

    def test_accepts_pdf_assignment_file(self):
        pdf_file = SimpleUploadedFile(
            "taller.pdf",
            b"%PDF-1.4 contenido de prueba",
            content_type="application/pdf",
        )
        serializer = AssignmentSerializer(data=self._base_payload(pdf_file))

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_rejects_non_pdf_assignment_file(self):
        text_file = SimpleUploadedFile(
            "taller.txt",
            b"contenido de prueba",
            content_type="text/plain",
        )
        serializer = AssignmentSerializer(data=self._base_payload(text_file))

        self.assertFalse(serializer.is_valid())
        self.assertIn("archivo", serializer.errors)


class SubmissionFileValidationTests(TestCase):
    def setUp(self):
        self.course = Course.objects.create(nombre="Sexto A")
        self.subject = Subject.objects.create(nombre="Matematicas", curso=self.course)
        self.assignment = Assignment.objects.create(
            materia=self.subject,
            titulo="Taller de fracciones",
            descripcion="Resolver los ejercicios propuestos.",
            fecha_entrega="2026-04-30",
            periodo=1,
        )

    def _base_payload(self, uploaded_file):
        return {
            "tarea": self.assignment.id,
            "archivo": uploaded_file,
        }

    def test_accepts_pdf_submission_file(self):
        pdf_file = SimpleUploadedFile(
            "entrega.pdf",
            b"%PDF-1.4 contenido de prueba",
            content_type="application/pdf",
        )
        serializer = SubmissionSerializer(data=self._base_payload(pdf_file))

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_rejects_non_pdf_submission_file(self):
        image_file = SimpleUploadedFile(
            "entrega.png",
            b"contenido de prueba",
            content_type="image/png",
        )
        serializer = SubmissionSerializer(data=self._base_payload(image_file))

        self.assertFalse(serializer.is_valid())
        self.assertIn("archivo", serializer.errors)


class DirectActivityGradeValidationTests(TestCase):
    def test_accepts_grade_inside_valid_range(self):
        serializer = DirectActivityGradeEntrySerializer(
            data={
                "student_id": 1,
                "calificacion": "4.5",
                "retroalimentacion": "Buen trabajo.",
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_rejects_grade_above_maximum(self):
        serializer = DirectActivityGradeEntrySerializer(
            data={
                "student_id": 1,
                "calificacion": "6.0",
                "retroalimentacion": "Nota fuera de rango.",
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("calificacion", serializer.errors)
