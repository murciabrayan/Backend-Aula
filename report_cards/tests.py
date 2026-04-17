from django.test import TestCase

from courses.models import Course, Subject
from report_cards.models import Indicator
from report_cards.models import SubjectIndicatorAssignment
from report_cards.serializers import IndicatorSerializer, SubjectIndicatorAssignmentSerializer


class IndicatorSerializerTests(TestCase):
    def test_rejects_blank_description(self):
        serializer = IndicatorSerializer(data={"descripcion": "   "})

        self.assertFalse(serializer.is_valid())
        self.assertIn("descripcion", serializer.errors)

    def test_rejects_duplicate_description_ignoring_case(self):
        Indicator.objects.create(descripcion="Participa activamente en clase")
        serializer = IndicatorSerializer(
            data={"descripcion": "participa activamente en clase"}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("descripcion", serializer.errors)

    def test_accepts_valid_description_and_trims_spaces(self):
        serializer = IndicatorSerializer(
            data={"descripcion": "  Resuelve problemas con autonomia  "}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(
            serializer.validated_data["descripcion"],
            "Resuelve problemas con autonomia",
        )


class SubjectIndicatorAssignmentSerializerTests(TestCase):
    def setUp(self):
        self.course = Course.objects.create(nombre="Sexto A")
        self.subject = Subject.objects.create(nombre="Matematicas", curso=self.course)
        self.indicator = Indicator.objects.create(
            descripcion="Resuelve problemas con autonomia"
        )

    def test_accepts_indicator_assignment_for_subject_and_period(self):
        serializer = SubjectIndicatorAssignmentSerializer(
            data={
                "materia": self.subject.id,
                "periodo": 1,
                "indicador": self.indicator.id,
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_rejects_duplicate_indicator_assignment_for_subject_and_period(self):
        SubjectIndicatorAssignment.objects.create(
            materia=self.subject,
            periodo=1,
            indicador=self.indicator,
        )
        serializer = SubjectIndicatorAssignmentSerializer(
            data={
                "materia": self.subject.id,
                "periodo": 1,
                "indicador": self.indicator.id,
            }
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
