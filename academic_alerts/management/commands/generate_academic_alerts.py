from django.core.management.base import BaseCommand

from academic_alerts.views import (
    generate_alerts_for_course,
    trigger_scheduled_follow_up_requests,
)
from courses.models import Course


class Command(BaseCommand):
    help = "Genera alertas academicas automaticamente para los cursos y periodos indicados."

    def add_arguments(self, parser):
        parser.add_argument(
            "--course-id",
            type=int,
            help="Si se envia, genera alertas solo para ese curso.",
        )
        parser.add_argument(
            "--periods",
            nargs="+",
            type=int,
            default=[1, 2, 3, 4],
            help="Lista de periodos a procesar. Por defecto: 1 2 3 4.",
        )

    def handle(self, *args, **options):
        course_id = options.get("course_id")
        periods = sorted(set(options.get("periods") or [1, 2, 3, 4]))

        courses = Course.objects.all().order_by("nombre")
        if course_id:
            courses = courses.filter(pk=course_id)

        total_courses = 0
        total_runs = 0
        total_alerts = 0

        for course in courses:
            total_courses += 1
            for period in periods:
                generated_alerts = generate_alerts_for_course(course, period)
                total_runs += 1
                total_alerts += len(generated_alerts)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Curso '{course.nombre}' - periodo {period}: {len(generated_alerts)} alertas procesadas."
                    )
                )

        triggered_follow_ups = trigger_scheduled_follow_up_requests()

        self.stdout.write(
            self.style.SUCCESS(
                f"Proceso completado. Cursos: {total_courses}, ejecuciones: {total_runs}, alertas procesadas: {total_alerts}, seguimientos semanales activados: {triggered_follow_ups}."
            )
        )
