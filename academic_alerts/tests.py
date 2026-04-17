from datetime import datetime

from django.test import TestCase, override_settings
from django.utils import timezone

from academic_alerts.views import (
    alert_level_for_absences,
    alert_level_for_grade,
    alert_level_for_missing_assignments,
    avg_or_none,
    calculate_next_follow_up_due_at,
)


class AcademicAlertLevelTests(TestCase):
    def test_grade_alert_levels_follow_thresholds(self):
        self.assertEqual(alert_level_for_grade(2.9), "CRITICAL")
        self.assertEqual(alert_level_for_grade(3.2), "WARNING")
        self.assertIsNone(alert_level_for_grade(3.4))
        self.assertIsNone(alert_level_for_grade(None))

    def test_absence_alert_levels_follow_thresholds(self):
        self.assertIsNone(alert_level_for_absences(2))
        self.assertEqual(alert_level_for_absences(3), "WARNING")
        self.assertEqual(alert_level_for_absences(5), "CRITICAL")

    def test_missing_assignment_alert_levels_follow_thresholds(self):
        self.assertIsNone(alert_level_for_missing_assignments(1))
        self.assertEqual(alert_level_for_missing_assignments(2), "WARNING")
        self.assertEqual(alert_level_for_missing_assignments(4), "CRITICAL")


class AcademicAverageTests(TestCase):
    def test_returns_none_when_no_values_exist(self):
        self.assertIsNone(avg_or_none([]))

    def test_returns_average_rounded_to_one_decimal(self):
        self.assertEqual(avg_or_none([3.0, 4.0, 4.5]), 3.8)


class AcademicFollowUpDateTests(TestCase):
    @override_settings(TIME_ZONE="America/Bogota")
    def test_next_follow_up_due_date_is_seven_days_later_at_start_of_day(self):
        base_datetime = timezone.make_aware(datetime(2026, 4, 16, 15, 30))

        due_at = calculate_next_follow_up_due_at(base_datetime)
        local_due_at = timezone.localtime(due_at)

        self.assertEqual(local_due_at.date().isoformat(), "2026-04-23")
        self.assertEqual(local_due_at.time().isoformat(), "00:00:00")
