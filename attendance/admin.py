from django.contrib import admin
from .models import Attendance


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "course",
        "date",
        "status",
        "is_justified",
        "justification_type",
    )
    list_filter = (
        "status",
        "is_justified",
        "justification_type",
        "course",
        "date",
    )
    search_fields = (
        "student__first_name",
        "student__last_name",
        "student__email",
        "course__nombre",
    )