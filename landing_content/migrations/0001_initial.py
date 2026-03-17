from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="LandingCalendarEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=220)),
                ("detail", models.CharField(blank=True, max_length=280)),
                ("event_date", models.DateField()),
                ("display_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "Evento de calendario",
                "verbose_name_plural": "Eventos de calendario",
                "ordering": ["event_date", "display_order", "title"],
            },
        ),
        migrations.CreateModel(
            name="LandingDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=220)),
                ("description", models.TextField()),
                ("file", models.FileField(upload_to="landing/documents/")),
                ("display_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "Documento institucional",
                "verbose_name_plural": "Documentos institucionales",
                "ordering": ["display_order", "title"],
            },
        ),
        migrations.CreateModel(
            name="LandingGalleryItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=220)),
                ("detail", models.CharField(max_length=280)),
                ("image", models.ImageField(upload_to="landing/gallery/")),
                ("event_date", models.DateField(blank=True, null=True)),
                ("display_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "Evento de galeria",
                "verbose_name_plural": "Eventos de galeria",
                "ordering": ["display_order", "-event_date", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="LandingNews",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=220)),
                ("summary", models.TextField()),
                ("published_at", models.DateField()),
                ("image", models.ImageField(upload_to="landing/news/")),
                ("display_order", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "Noticia de landing",
                "verbose_name_plural": "Noticias de landing",
                "ordering": ["display_order", "-published_at", "-created_at"],
            },
        ),
    ]
