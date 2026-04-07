from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def copy_existing_course_teacher_to_new_fields(apps, schema_editor):
    Course = apps.get_model("courses", "Course")
    Subject = apps.get_model("courses", "Subject")

    for course in Course.objects.exclude(docente_id__isnull=True):
        if not course.director_curso_id:
            course.director_curso_id = course.docente_id
            course.save(update_fields=["director_curso"])

        Subject.objects.filter(curso_id=course.id, docente_id__isnull=True).update(
            docente_id=course.docente_id
        )


def reverse_copy_existing_course_teacher_to_new_fields(apps, schema_editor):
    Course = apps.get_model("courses", "Course")
    Subject = apps.get_model("courses", "Subject")

    for course in Course.objects.exclude(director_curso_id__isnull=True):
        if not course.docente_id:
            course.docente_id = course.director_curso_id
            course.save(update_fields=["docente"])

    Subject.objects.filter(docente_id__isnull=False).update(docente_id=None)


class Migration(migrations.Migration):
    dependencies = [
        ("courses", "0005_alter_subject_options_subject_area"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="director_curso",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"role": "TEACHER"},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="cursos_dirigidos",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="subject",
            name="docente",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"role": "TEACHER"},
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="materias_asignadas",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(
            copy_existing_course_teacher_to_new_fields,
            reverse_copy_existing_course_teacher_to_new_fields,
        ),
    ]
