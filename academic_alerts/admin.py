from django.contrib import admin
from .models import AcademicAlert


@admin.register(AcademicAlert)
class AcademicAlertAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "course",
        "period",
        "alert_type",
        "level",
        "status",
        "created_at",
    )
    list_filter = (
        "period",
        "alert_type",
        "level",
        "status",
        "course",
    )
    search_fields = (
        "student__first_name",
        "student__last_name",
        "student__email",
        "course__nombre",
        "title",
    )