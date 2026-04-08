from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class LandingNews(TimestampedModel):
    title = models.CharField(max_length=220)
    summary = models.TextField()
    published_at = models.DateField()
    image = models.ImageField(upload_to="landing/news/")
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "-published_at", "-created_at"]
        verbose_name = "Noticia de landing"
        verbose_name_plural = "Noticias de landing"

    def __str__(self):
        return self.title


class LandingGalleryItem(TimestampedModel):
    title = models.CharField(max_length=220)
    detail = models.CharField(max_length=280)
    image = models.ImageField(upload_to="landing/gallery/")
    event_date = models.DateField(null=True, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "-event_date", "-created_at"]
        verbose_name = "Evento de galeria"
        verbose_name_plural = "Eventos de galeria"

    def __str__(self):
        return self.title


class LandingDocument(TimestampedModel):
    title = models.CharField(max_length=220)
    description = models.TextField()
    file = models.FileField(upload_to="landing/documents/")
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["display_order", "title"]
        verbose_name = "Documento institucional"
        verbose_name_plural = "Documentos institucionales"

    def __str__(self):
        return self.title


class LandingCalendarEntry(TimestampedModel):
    title = models.CharField(max_length=220)
    detail = models.CharField(max_length=280, blank=True)
    event_date = models.DateField()
    event_time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=220, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["event_date", "display_order", "title"]
        verbose_name = "Evento de calendario"
        verbose_name_plural = "Eventos de calendario"

    def __str__(self):
        return f"{self.title} - {self.event_date}"
